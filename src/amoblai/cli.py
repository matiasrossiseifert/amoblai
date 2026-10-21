"""Puntos de entrada de la línea de comandos: `uv run amoblai --help`.

El flujo es el de roomrag (desde_youseeyoubuy/roomrag): plan → retrieve → choose → scene →
generate. Acá está lo propio del TP: el catálogo IKEA, la evaluación y los generadores.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="amoblai: amoblado virtual con RAG sobre el catálogo IKEA.", no_args_is_help=True
)
data_app = typer.Typer(help="Dataset IKEA.", no_args_is_help=True)
app.add_typer(data_app, name="data")
console = Console()

CONFIG = Path("configs/amoblai.yaml")
RAW = Path("data/raw/ikea")
ITEMS = Path("data/processed/items_roomrag.jsonl")

ConfigOpt = Annotated[Path, typer.Option("--config", "-c", help="Config de roomrag.")]
SetOpt = Annotated[
    list[str] | None, typer.Option("--set", "-s", help="Override: seccion.campo=valor (repetible).")
]


def load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(".env", override=False)


def cfg_for(config: Path, overrides: list[str] | None = None, paid: bool = False):
    from roomrag.config import deep_merge, load_config, parse_override

    over: dict = {}
    for expr in overrides or []:
        over = deep_merge(over, parse_override(expr))
    if paid:
        over = deep_merge(over, {"budget": {"allow_paid": True}})
    return load_config(config, over)


@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False) -> None:
    load_env()
    logging.basicConfig(level=logging.DEBUG if verbose else logging.WARNING, format="%(message)s")


@data_app.command("download")
def data_download(force: Annotated[bool, typer.Option(help="Volver a descargar.")] = False) -> None:
    """Descarga el dataset IKEA (fijado a un commit) en data/raw/ikea."""
    from amoblai.data.download import download_dataset

    download_dataset(RAW, force=force)
    console.print(f"Dataset en {RAW}")


@app.command()
def catalogo(
    lotes: Annotated[
        int, typer.Option(help="Además, armar lotes de N productos para los subagentes (0 = no).")
    ] = 0,
) -> None:
    """Arma el catálogo de roomrag: productos del alcance, descripciones, kinds y correcciones."""
    from amoblai.catalogo_ikea import build_catalog_items, write_catalog_files

    items = build_catalog_items(RAW, Path("configs/categories.yaml"), ITEMS)
    console.print(f"{len(items)} productos del alcance en {ITEMS}")
    if lotes:
        from amoblai.descripciones import make_batches

        paths = make_batches(items, Path("data/processed/describir"), lotes, Path("."))
        console.print(f"{len(paths)} lotes para describir en data/processed/describir/")
    if any(Path("catalogo/descripciones").glob("lote_*.jsonl")):
        stats = write_catalog_files(
            ITEMS,
            Path("catalogo/descripciones"),
            Path("catalogo/descripciones.jsonl"),
            Path("catalogo/kinds.yaml"),
            Path("catalogo/correcciones.yaml"),
            Path("catalogo/ikea.yaml"),
        )
        console.print(f"catalogo/ikea.yaml: {stats}")


@app.command()
def indice(config: ConfigOpt = CONFIG, overrides: SetOpt = None) -> None:
    """Indexing pipeline de roomrag: descripciones → embeddings (en caché)."""
    from roomrag.index import build_index

    idx = build_index(cfg_for(config, overrides), log=console.print)
    console.print(
        f"{idx.meta['products']} productos ({idx.meta['left_out']} sin descripción): {idx.path}"
    )


@app.command()
def buscar(
    consulta: Annotated[
        str, typer.Argument(help="Texto (idealmente en las ocho líneas del catálogo).")
    ],
    kind: Annotated[str | None, typer.Option(help="Filtrar por kind (roomrag/kinds.py).")] = None,
    k: Annotated[int, typer.Option(help="Cuántos traer.")] = 5,
    config: ConfigOpt = CONFIG,
    overrides: SetOpt = None,
) -> None:
    """Prueba el índice: los productos más cercanos a una consulta."""
    from roomrag.filters import Filters
    from roomrag.index import build_index, index_is_current, open_index
    from roomrag.search import search

    cfg = cfg_for(config, overrides)
    if not index_is_current(cfg):
        build_index(cfg, log=lambda _: None)
    cfg.rag.top_k = k
    for h in search(open_index(cfg), consulta, Filters(kinds=[kind] if kind else []), cfg):
        console.print(f"{h.score or 0:.3f}  {h.id}  {h.kind or h.category:<14} {h.name}")


@app.command()
def amoblar(
    foto: Annotated[Path, typer.Argument(help="Foto del ambiente.")],
    pedido: Annotated[str, typer.Argument(help="Lo que pide el usuario, en texto libre.")],
    generador: Annotated[str, typer.Option(help="manual | nano_banana_2 | openai")] = "manual",
    pagar: Annotated[
        bool, typer.Option("--pagar", help="Habilitar las llamadas pagas (dentro de los topes).")
    ] = False,
    nombre: Annotated[
        str | None, typer.Option(help="Nombre de la corrida (default: nombre de la foto).")
    ] = None,
    config: ConfigOpt = CONFIG,
    overrides: SetOpt = None,
) -> None:
    """El flujo completo (plan → retrieve → choose → scene → generate); se retoma donde quedó."""
    from roomrag.flow import run_flow

    cfg = cfg_for(config, [*(overrides or []), f"furnish.generator={generador}"], paid=pagar)
    out = Path(cfg.runs_dir) / (nombre or foto.stem)
    run_flow(foto, pedido, cfg, out, log=console.print)
    console.print(f"Corrida: {out}")


@app.command()
def evaluar(
    embedders: Annotated[
        str, typer.Option(help="Embedders separados por coma.")
    ] = "hashing,bge,qwen3",
    nombre: Annotated[str, typer.Option(help="Nombre de la corrida.")] = "ablacion-texto",
    config: ConfigOpt = CONFIG,
) -> None:
    """Retrieval por texto sobre los 65 ambientes IKEA: hit@k, MRR, recall (ablación)."""
    from amoblai.evaluacion import default_methods, run_eval

    cfg = cfg_for(config)
    methods = default_methods([e.strip() for e in embedders.split(",") if e.strip()])
    run = run_eval(
        cfg,
        Path("evaluacion/ikea/consultas.json"),
        RAW,
        Path("resultados/evaluacion"),
        methods,
        nombre,
    )
    data = json.loads((run / "metricas.json").read_text())
    table = Table("método", "consultas", "hit@1", "hit@10", "MRR@10", "recall ítem@10")
    for name, m in data.items():
        table.add_row(
            name,
            str(m["answerable"]),
            f"{m['hit@1']:.3f}",
            f"{m['hit@10']:.3f}",
            f"{m['mrr@10']:.3f}",
            str(m["recall_item@10"]),
        )
    console.print(table)
    console.print(f"Corrida: {run}")


@app.command()
def reporte() -> None:
    """Tablas y gráficos de las evaluaciones (incluye la v0 por imagen para comparar)."""
    from amoblai.reporte import build_report

    for k, p in build_report(Path("resultados/evaluacion"), Path("resultados/reporte")).items():
        console.print(f"{k}: {p}")


@app.command()
def gastos(config: ConfigOpt = CONFIG) -> None:
    """Lo gastado por cuenta (resultados/gastos.jsonl) contra sus topes."""
    from roomrag.budget import Ledger

    cfg = cfg_for(config)
    table = Table("cuenta", "gastado (US$)", "tope (US$)")
    for account, cap in {**cfg.budget.accounts, "(resto)": cfg.budget.max_usd_total}.items():
        pool = None if account == "(resto)" else account
        table.add_row(account, f"{Ledger(cfg.budget.ledger, cap, pool).spent():.4f}", f"{cap:.2f}")
    console.print(table)


if __name__ == "__main__":  # pragma: no cover
    app()
