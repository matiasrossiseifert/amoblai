"""Puntos de entrada de la línea de comandos: `uv run amoblai --help`.

    data download   el dataset IKEA                catalogo   el catálogo que se indexa
    indice          indexing pipeline (ChromaDB)   buscar     probar la búsqueda
    amoblar         el flujo: plan → retrieve → choose → scene → generate
    evaluar         una ablación del retrieval     reporte    tablas y gráficos
    gastos          lo gastado contra los topes

Las rutas están en paths.py (todo en datos/).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from amoblai import paths

app = typer.Typer(
    help="amoblai: amoblado virtual con RAG sobre el catálogo IKEA.", no_args_is_help=True
)
data_app = typer.Typer(help="Dataset IKEA.", no_args_is_help=True)
app.add_typer(data_app, name="data")
console = Console()

ConfigOpt = Annotated[Path, typer.Option("--config", "-c", help="La config (YAML).")]
SetOpt = Annotated[
    list[str] | None, typer.Option("--set", "-s", help="Override: seccion.campo=valor (repetible).")
]


def load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(".env", override=False)


def cfg_for(config: Path, overrides: list[str] | None = None, paid: bool = False):
    from amoblai.config import deep_merge, load_config, parse_override

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
    """Descarga el dataset IKEA (fijado a un commit) en datos/dataset/ikea."""
    from amoblai.dataset.download import download_dataset

    download_dataset(paths.RAW, force=force)
    console.print(f"Dataset en {paths.RAW}")


@app.command()
def catalogo(
    lotes: Annotated[
        int,
        typer.Option(
            help="Además, armar lotes de N productos sin descripción para los subagentes (0 = no)."
        ),
    ] = 0,
) -> None:
    """Arma el catálogo que se indexa: productos, descripciones, kinds y correcciones."""
    from amoblai.catalog.ikea import build_catalog_items, write_catalog_files

    items = build_catalog_items(paths.RAW, paths.CATEGORIES, paths.ITEMS)
    console.print(f"{len(items)} productos del alcance en {paths.ITEMS}")
    if lotes:
        from amoblai.catalog.descriptions import described, make_batches

        written = sorted(paths.DESCRIPTION_BATCHES.glob("lote_*.jsonl"))
        done = described(written)
        todo = [it for it in items if it["id"] not in done]
        out = paths.PROCESSED / "describir"
        batches = make_batches(todo, out, lotes, Path("."), first=len(written) + 1)
        console.print(f"{len(todo)} sin descripción: {len(batches)} lotes en {out}/")
    if any(paths.DESCRIPTION_BATCHES.glob("lote_*.jsonl")):
        stats = write_catalog_files(
            paths.ITEMS,
            paths.DESCRIPTION_BATCHES,
            paths.DESCRIPTIONS,
            paths.KINDS_FILE,
            paths.CORRECTIONS,
            paths.CATALOG_YAML,
        )
        console.print(f"{paths.CATALOG_YAML}: {stats}")


@app.command()
def indice(config: ConfigOpt = paths.CONFIG, overrides: SetOpt = None) -> None:
    """Indexing pipeline: descripciones → embeddings → ChromaDB (lo que ya está, de la caché)."""
    from amoblai.rag.index import build_index

    idx = build_index(cfg_for(config, overrides), log=console.print)
    console.print(
        f"{idx.meta['products']} productos ({idx.meta['left_out']} sin descripción): {idx.path}"
    )


@app.command()
def buscar(
    consulta: Annotated[
        str, typer.Argument(help="Texto (idealmente en las ocho líneas del catálogo).")
    ],
    kind: Annotated[str | None, typer.Option(help="Filtrar por kind (catalog/kinds.py).")] = None,
    k: Annotated[int, typer.Option(help="Cuántos traer.")] = 5,
    config: ConfigOpt = paths.CONFIG,
    overrides: SetOpt = None,
) -> None:
    """Prueba el índice: los productos más cercanos a una consulta."""
    from amoblai.rag.filters import Filters
    from amoblai.rag.index import build_index, index_is_current, open_index
    from amoblai.rag.search import search

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
    vista: Annotated[
        list[Path] | None,
        typer.Option(help="Otra foto del mismo ambiente, solo para entenderlo (repetible)."),
    ] = None,
    config: ConfigOpt = paths.CONFIG,
    overrides: SetOpt = None,
) -> None:
    """El flujo completo (plan → retrieve → choose → scene → generate); se retoma donde quedó.

    Las --vista van a Claude junto con la foto; el modelo de imagen amobla solo la foto."""
    from amoblai.furnish.flow import run_flow

    cfg = cfg_for(config, [*(overrides or []), f"furnish.generator={generador}"], paid=pagar)
    out = Path(cfg.runs_dir) / (nombre or foto.stem)
    run_flow(foto, pedido, cfg, out, log=console.print, views=vista or [])
    console.print(f"Corrida: {out}")


@app.command()
def evaluar(
    ablacion: Annotated[
        Path, typer.Option(help="La ablación: métodos a comparar (datos/configs/ablaciones/).")
    ] = paths.ABLATIONS / "retrieval.yaml",
    pagar: Annotated[
        bool, typer.Option("--pagar", help="Habilitar los métodos pagos (reranking con un VLM).")
    ] = False,
    estimar: Annotated[
        bool,
        typer.Option(
            "--estimar", help="Solo contar las llamadas pagas que faltan en la caché y su costo."
        ),
    ] = False,
    config: ConfigOpt = paths.CONFIG,
) -> None:
    """Retrieval por texto sobre los ambientes IKEA: hit@k, MRR, recall, por método."""
    from amoblai.evaluation.retrieval import estimate_reranks, load_ablation, run_eval

    name, methods = load_ablation(ablacion)
    if estimar or (any(m.paid for m in methods) and not pagar):
        cost = estimate_reranks(cfg_for(config), paths.EVAL_QUERIES, paths.RAW, methods)
        for method, (n, usd) in cost.items():
            console.print(f"{method}: {n} llamadas sin caché, unos US${usd}")
        if not estimar:
            raise typer.BadParameter(f"{ablacion} tiene métodos pagos: correr con --pagar")
        return
    run = run_eval(
        cfg_for(config, paid=pagar), paths.EVAL_QUERIES, paths.RAW, paths.EVAL_RUNS, methods, name
    )
    data = json.loads((run / "metricas.json").read_text())
    table = Table("método", "consultas", "hit@1", "hit@10", "MRR@10", "recall ítem@10")
    for method, m in data.items():
        table.add_row(
            method,
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
    from amoblai.evaluation.report import build_report

    for k, p in build_report(paths.EVAL_RUNS, paths.REPORT).items():
        console.print(f"{k}: {p}")


@app.command()
def gastos(config: ConfigOpt = paths.CONFIG) -> None:
    """Lo gastado por cuenta (datos/resultados/gastos.jsonl) contra sus topes."""
    from amoblai.infra.budget import Ledger

    cfg = cfg_for(config)
    table = Table("cuenta", "gastado (US$)", "tope (US$)")
    for account, cap in {**cfg.budget.accounts, "(resto)": cfg.budget.max_usd_total}.items():
        pool = None if account == "(resto)" else account
        table.add_row(account, f"{Ledger(cfg.budget.ledger, cap, pool).spent():.4f}", f"{cap:.2f}")
    console.print(table)


if __name__ == "__main__":  # pragma: no cover
    app()
