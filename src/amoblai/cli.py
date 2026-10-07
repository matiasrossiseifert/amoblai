"""Puntos de entrada de la línea de comandos: `uv run amoblai --help`."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.logging import RichHandler

from amoblai.config import AppConfig, load_config, load_env

app = typer.Typer(
    help="amoblai: amoblado virtual con RAG sobre un catálogo real de muebles.",
    no_args_is_help=True,
)
data_app = typer.Typer(help="Descarga e inspección del dataset IKEA.", no_args_is_help=True)
eval_app = typer.Typer(help="Evaluación del retriever y de punta a punta.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(eval_app, name="eval")
console = Console()

ConfigOpt = Annotated[
    Path | None,
    typer.Option("--config", "-c", help="YAML de configuración (default: configs/base.yaml)."),
]
SetOpt = Annotated[
    list[str] | None,
    typer.Option("--set", "-s", help="Override puntual: seccion.campo=valor (repetible)."),
]
NameOpt = Annotated[str | None, typer.Option("--name", "-n", help="Nombre de la corrida.")]


@app.callback()
def main(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False) -> None:
    load_env()
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False, rich_tracebacks=True)],
    )
    for noisy in ("httpx", "httpcore", "urllib3", "chromadb", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _config(config: Path | None, overrides: list[str] | None, name: str | None = None) -> AppConfig:
    extra = list(overrides or [])
    if name:
        extra.append(f"name={name}")
    return load_config(config, extra)


@data_app.command("download")
def data_download(
    config: ConfigOpt = None,
    force: Annotated[bool, typer.Option(help="Volver a descargar aunque ya exista.")] = False,
) -> None:
    """Descarga el dataset IKEA (fijado a un commit) en data/raw/ikea."""
    from amoblai.data.download import download_dataset

    cfg = _config(config, None)
    download_dataset(cfg.paths.raw_dir, cfg.dataset.repo, cfg.dataset.commit, force=force)


@data_app.command("info")
def data_info(config: ConfigOpt = None) -> None:
    """Resumen del dataset: productos, imágenes, ambientes por tipo."""
    from collections import Counter

    from amoblai.data.ikea import IkeaDataset

    cfg = _config(config, None)
    ds = IkeaDataset.load(cfg.paths.raw_dir)
    console.print(ds.stats)
    console.print(
        "Ambientes en disco por tipo:", dict(Counter(r.room_type for r in ds.rooms.values()))
    )


@app.command()
def categories(config: ConfigOpt = None) -> None:
    """Escribe resultados/mapeo_categorias.md con el mapeo type → categoría y sus conteos."""
    from amoblai.categories import CategoryMap
    from amoblai.indexing.indexer import load_or_build_catalog

    cfg = _config(config, None)
    catalog = load_or_build_catalog(cfg)  # reaplica el mapeo vigente
    report = CategoryMap.load(cfg.paths.categories_file).mapping_report(
        p.type for p in catalog.products.values()
    )
    out = Path(cfg.paths.results_dir) / "mapeo_categorias.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    console.print(f"Mapeo escrito en {out}")


@app.command()
def index(
    config: ConfigOpt = None,
    overrides: SetOpt = None,
    rebuild_catalog: Annotated[
        bool, typer.Option(help="Regenerar data/processed/catalog.json.")
    ] = False,
) -> None:
    """Indexing pipeline: catálogo → preprocesamiento → splitting → embeddings → ChromaDB."""
    from amoblai.components import get_embedder
    from amoblai.indexing.indexer import index_catalog

    cfg = _config(config, overrides)
    stats = index_catalog(cfg, get_embedder(cfg), rebuild_catalog=rebuild_catalog)
    console.print(stats)


@app.command()
def run(
    room: Annotated[Path, typer.Argument(help="Foto del ambiente vacío.")],
    prompt: Annotated[
        str, typer.Option("--prompt", "-p", help="Pedido del usuario (estilo, colores, muebles).")
    ] = "",
    image1: Annotated[
        Path | None,
        typer.Option(help="Usar esta imagen como imagen 1 (saltea el generador n.º 1)."),
    ] = None,
    config: ConfigOpt = None,
    overrides: SetOpt = None,
    name: NameOpt = None,
    evaluate: Annotated[
        bool, typer.Option("--eval", help="Calcular también las métricas de punta a punta.")
    ] = False,
) -> None:
    """Amobla un ambiente: imagen final + lista de compra (guardadas en resultados/corridas/)."""
    from amoblai.infra.images import load_image
    from amoblai.infra.runs import RunContext
    from amoblai.pipeline.query import FurnishPipeline

    cfg = _config(config, overrides, name)
    pipeline = FurnishPipeline.from_config(cfg)
    ctx = RunContext(cfg, "run", name=name or room.stem)
    result = pipeline.run(
        load_image(room), prompt, run=ctx, image1=load_image(image1) if image1 else None
    )
    metrics: dict = {"status": result.status, "timings_s": result.timings}
    if evaluate and result.final is not None:
        from amoblai.eval.e2e_eval import evaluate_result

        metrics |= evaluate_result(result, pipeline)
    ctx.finish(metrics)
    console.print_json(json.dumps(result.shopping_list, ensure_ascii=False))
    if result.pending:
        console.print(
            f"[yellow]Paso manual pendiente:[/] {result.pending.workdir}\n"
            "Volvé a correr el mismo comando cuando esté el resultado."
        )
    console.print(f"Corrida: {ctx.dir}")


@eval_app.command("retriever")
def eval_retriever(
    config: ConfigOpt = None,
    overrides: SetOpt = None,
    name: NameOpt = None,
    calibrate: Annotated[
        bool, typer.Option(help="Guardar el umbral calibrado en configs/umbrales.yaml.")
    ] = False,
    strict: Annotated[
        bool,
        typer.Option(help="Correr también la evaluación estricta (anotaciones/estricto.jsonl)."),
    ] = False,
) -> None:
    """Hit rate@k, MRR y recall sobre los livings y comedores de IKEA."""
    from amoblai.components import build_retrieval_components
    from amoblai.eval.retriever_eval import run_retriever_eval
    from amoblai.eval.strict_eval import run_strict_eval
    from amoblai.infra.runs import RunContext

    cfg = _config(config, overrides, name)
    ctx = RunContext(cfg, "retriever", name=name)
    comps = build_retrieval_components(cfg, use_threshold=False)
    metrics = run_retriever_eval(cfg, ctx, comps, calibrate=calibrate)
    if strict:
        metrics |= run_strict_eval(cfg, ctx, comps)
    ctx.finish(metrics)
    console.print_json(
        json.dumps(
            {
                k: metrics[k]
                for k in ("retrieval", "items", "random_baseline", "threshold_calibration")
                if k in metrics
            }
        )
    )
    console.print(f"Corrida: {ctx.dir}")


@eval_app.command("strict")
def eval_strict(config: ConfigOpt = None, overrides: SetOpt = None, name: NameOpt = None) -> None:
    """Evaluación estricta con los recortes etiquetados a mano (SKU exacto)."""
    from amoblai.eval.strict_eval import run_strict_eval
    from amoblai.infra.runs import RunContext

    cfg = _config(config, overrides, name)
    ctx = RunContext(cfg, "strict", name=name)
    metrics = run_strict_eval(cfg, ctx)
    ctx.finish(metrics)
    console.print_json(json.dumps(metrics))


@eval_app.command("e2e")
def eval_e2e(
    config: ConfigOpt = None,
    overrides: SetOpt = None,
    name: NameOpt = None,
    rooms: Annotated[
        Path | None, typer.Option(help="Carpeta de ambientes vacíos (default: ambientes_vacios/).")
    ] = None,
    limit: Annotated[
        int | None, typer.Option(help="Procesar solo los primeros N ambientes.")
    ] = None,
) -> None:
    """Re-identificación, preservación (SSIM), cobertura, costo y latencia en ambientes vacíos."""
    from amoblai.eval.e2e_eval import run_e2e_eval
    from amoblai.infra.runs import RunContext

    cfg = _config(config, overrides, name)
    ctx = RunContext(cfg, "e2e", name=name)
    metrics = run_e2e_eval(cfg, ctx, rooms, limit)
    ctx.finish(metrics)
    console.print_json(
        json.dumps({k: v for k, v in metrics.items() if k != "per_room"}, default=str)
    )
    console.print(f"Corrida: {ctx.dir}")


@app.command()
def ablation(
    plan: Annotated[Path, typer.Argument(help="Plan de ablación (configs/ablaciones/*.yaml).")],
    only: Annotated[
        list[str] | None, typer.Option(help="Correr solo estos pasos (por nombre).")
    ] = None,
) -> None:
    """Corre todas las configuraciones de un plan de ablación del retriever."""
    from amoblai.eval.ablation import run_ablation

    for d in run_ablation(plan, only):
        console.print(f"✓ {d}")


@app.command()
def report(
    config: ConfigOpt = None,
    out: Annotated[
        Path | None, typer.Option(help="Carpeta de salida (default: resultados/reporte).")
    ] = None,
) -> None:
    """Tablas y gráficos comparativos de todas las corridas."""
    from amoblai.report.report import build_report

    cfg = _config(config, None)
    written = build_report(cfg.paths.runs_dir, out or Path(cfg.paths.results_dir) / "reporte")
    for k, p in written.items():
        console.print(f"{k}: {p}")


if __name__ == "__main__":  # pragma: no cover
    app()
