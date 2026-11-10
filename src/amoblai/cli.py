"""Puntos de entrada de la línea de comandos: `uv run amoblai --help`.

    data download   el dataset IKEA                catalogo   el catálogo que se indexa
    indice          indexing pipeline (ChromaDB)   buscar     probar la búsqueda
    amoblar         el flujo: plan → retrieve → choose → scene → generate
    corridas        la página para mirar cada corrida (datos/resultados/amoblar/index.html)
    evaluar         una ablación del retrieval     reporte    tablas y gráficos
    evaluar-imagen  la imagen generada (fidelidad, ambiente, pedido)
    evaluar-respuesta  RAGAS sobre el porqué de la lista (faithfulness, answer relevance)
    evaluar-espacio  el espacio de embeddings: separabilidad por kind y UMAP
    evaluar-graduada  relevancia graduada (2/1/0) del top-3, con un juez
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


# El ground truth del retrieval es de IKEA: las evaluaciones que lo usan corren siempre sobre el
# catálogo de IKEA, aunque el flujo use otro (rag.catalog). Así los números siguen comparables.
IKEA_GT = ["rag.catalog=datos/catalogo/ikea.yaml", "rag.describer=written"]


def cfg_ikea(config: Path, overrides: list[str] | None = None, paid: bool = False):
    return cfg_for(config, [*IKEA_GT, *(overrides or [])], paid)


def cfg_of_run(config: Path, run: Path):
    """La configuración con el catálogo de una corrida: el de IKEA si eligió solo productos de
    IKEA (las corridas viejas), el combinado si eligió alguno de ABO."""
    choice = json.loads((run / "3_choice.json").read_text())
    ids = [c.get("id", "") for c in choice.get("answer", {}).get("choices", [])]
    if any(i.startswith("abo-") for i in ids):
        return cfg_for(
            config, ["rag.catalog=datos/catalogo/todos.yaml", "rag.describer=written_todos"]
        )
    return cfg_ikea(config)


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


@data_app.command("ambientes")
def data_ambientes() -> None:
    """Baja las fotos públicas de ambientes vacíos (datos/ambientes_vacios/publicas.yaml: de
    dónde es cada una, su autor y su licencia). No se commitean."""
    import httpx
    import yaml
    from PIL import Image, ImageOps

    fotos = yaml.safe_load((paths.EMPTY_ROOMS / "publicas.yaml").read_text())["fotos"]
    headers = {"User-Agent": "amoblai-tp/0.1 (university project)"}
    n = 0
    for f in fotos:
        dst = Path(f["archivo"])
        if dst.exists():
            continue
        r = httpx.get(f["url_descarga"], headers=headers, follow_redirects=True, timeout=120)
        r.raise_for_status()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(r.content)
        with Image.open(dst) as im:  # los originales de Commons: a 2400 px, como las copias locales
            if max(im.size) > 2400:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.thumbnail((2400, 2400), Image.LANCZOS)
                im.save(dst, quality=92)
        n += 1
    console.print(f"{n} fotos bajadas ({len(fotos)} en publicas.yaml)")


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


@app.command("catalogo-abo")
def catalogo_abo(
    describir: Annotated[
        bool, typer.Option("--describir", help="Escribir las descripciones que falten (pago).")
    ] = False,
    pagar: Annotated[bool, typer.Option("--pagar", help="Habilitar las llamadas pagas.")] = False,
    config: ConfigOpt = paths.CONFIG,
) -> None:
    """El catálogo alternativo, Amazon Berkeley Objects: baja la metadata y las fotos, elige los
    productos (uno por modelo, con tope por kind) y, con --describir --pagar, escribe sus
    descripciones con Claude (catalog/describe_api.py; lo que está en la caché no se paga)."""
    import yaml

    from amoblai.catalog import abo
    from amoblai.catalog.kinds import KINDS

    load_env()
    abo.download_metadata(paths.ABO / "metadata")
    items = abo.select(paths.ABO / "metadata")
    console.print(f"{len(items)} productos elegidos; bajando las fotos que falten...")
    abo.download_images(items, Path("."))
    items = abo.drop_shared_photos(items, Path("."))
    if describir:
        from amoblai.catalog.describe_api import describe

        cfg = cfg_for(config, paid=pagar)
        llm = {**cfg.evaluation.rerankers["opus"], "effort": "low"}
        console.print(describe(cfg, items, paths.ABO_CATALOG, llm))
    kinds = yaml.safe_load((paths.ABO_CATALOG / "kinds.yaml").read_text()) or {}
    for it in items:  # the describer's kind, and the type that goes with it
        if it["id"] in kinds:
            it["kind"], it["category"] = kinds[it["id"]], KINDS[kinds[it["id"]]]
    abo.write_items(items, paths.ABO_ITEMS)
    console.print(f"{paths.ABO_ITEMS}: {len(items)} productos, {len(kinds)} con descripción")


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
def corridas() -> None:
    """Arma datos/resultados/amoblar/index.html: cada corrida paso a paso (pedido, plan,
    candidatos, elección, prompt de la imagen, imagen, métricas y costo). Se abre del disco."""
    from amoblai.furnish.viewer import build

    console.print(f"file://{build(paths.RUNS).resolve()}")


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
    replica: Annotated[
        str | None,
        typer.Option(
            help="Otra escritura de las consultas (r2, r3: datos/evaluacion_ikea/replicas/), "
            "para medir cuánto varía el resultado con quien las escribe."
        ),
    ] = None,
    config: ConfigOpt = paths.CONFIG,
    overrides: SetOpt = None,
) -> None:
    """Retrieval por texto sobre los ambientes IKEA: hit@k, MRR, recall, por método."""
    from amoblai.evaluation.retrieval import estimate_reranks, load_ablation, run_eval

    name, methods = load_ablation(ablacion)
    queries = paths.EVAL_QUERIES
    if replica:
        queries, name = paths.REPLICAS / f"consultas_{replica}.json", f"{name}-{replica}"
    if estimar or (any(m.paid for m in methods) and not pagar):
        cost = estimate_reranks(cfg_ikea(config, overrides), queries, paths.RAW, methods)
        for method, (n, usd) in cost.items():
            console.print(f"{method}: {n} llamadas sin caché, unos US${usd}")
        if not estimar:
            raise typer.BadParameter(f"{ablacion} tiene métodos pagos: correr con --pagar")
        return
    run = run_eval(
        cfg_ikea(config, overrides, paid=pagar),
        queries,
        paths.RAW,
        paths.EVAL_RUNS,
        methods,
        name,
        replica=replica,
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


@app.command("evaluar-imagen")
def evaluar_imagen(
    corridas: Annotated[
        list[Path] | None,
        typer.Argument(
            help="Corridas de datos/resultados/amoblar/ (default: las que tienen imagen)."
        ),
    ] = None,
    referencia: Annotated[
        bool,
        typer.Option(
            "--referencia",
            help="Además, la vara: la misma identificación con las fotos reales de IKEA.",
        ),
    ] = False,
    config: ConfigOpt = paths.CONFIG,
) -> None:
    """La imagen generada, gratis y local: ¿muestra los productos de la lista (fidelidad), sin
    inventar otros, en el mismo ambiente (SSIM, SIFT) y con lo que se pidió (SigLIP 2)?"""
    from amoblai.evaluation.image import Models, evaluate_run, reference

    cfg = cfg_ikea(config)
    models = Models(Path(cfg.cache_dir) / "imagen")
    if referencia:
        ref = reference(cfg, paths.EVAL_QUERIES, paths.RAW, paths.IMAGE_REFERENCE, models)
        console.print(
            f"Fotos reales IKEA: {ref['recortes']} recortes, hit@1 {ref['hit@1']}, "
            f"MRR@10 {ref['mrr@10']}, coseno {ref['coseno_medio']} → {paths.IMAGE_REFERENCE}"
        )
    runs = corridas or [
        d
        for d in sorted(paths.RUNS.glob("*"))
        if (d / "5_image.json").exists()
        and not json.loads((d / "5_image.json").read_text()).get("pending")
    ]
    table = Table(
        "corrida",
        "presencia",
        "identificados@1",
        "coseno",
        "inventadas",
        "SSIM fuera",
        "SIFT",
        "pedido Δ",
    )
    for run in runs:
        r = evaluate_run(cfg_of_run(config, run), run, models)
        f, a, q = r["fidelidad"], r["ambiente"], r["pedido_imagen"]
        table.add_row(
            run.name,
            f"{f['detectados']}/{f['productos']}",
            str(f["identificados@1"]),
            str(f["coseno_medio"]),
            str(len(r["inventadas"])),
            str(a["ssim_fuera_de_los_muebles"]),
            str(a.get("sift_reencontrados")),
            f"{q['delta']:+.3f} (puesto {q['puesto_entre_contrastes']})",
        )
    console.print(table)


@app.command("evaluar-respuesta")
def evaluar_respuesta(
    corridas: Annotated[
        list[Path] | None,
        typer.Argument(help="Corridas de datos/resultados/amoblar/ (default: las que eligieron)."),
    ] = None,
    juez: Annotated[
        str,
        typer.Option(
            help="archivo: un subagente de Claude Code lee la tarea y escribe la respuesta "
            "(gratis); opus: Claude por la API (pago, con --pagar)."
        ),
    ] = "archivo",
    pagar: Annotated[bool, typer.Option("--pagar", help="Habilitar el juez pago.")] = False,
    config: ConfigOpt = paths.CONFIG,
) -> None:
    """RAGAS del lado del generador sobre la respuesta en texto (el porqué de cada producto):
    faithfulness (sus afirmaciones se infieren de lo que vio el sistema) y answer relevance (los
    pedidos que un juez infiere de la respuesta, contra el original)."""
    from amoblai.evaluation.answer import JUDGE_DIR, JUDGES, judge_with_claude, score, write_tasks

    if juez not in ("archivo", "opus"):
        raise typer.BadParameter("--juez: archivo u opus")
    if juez == "opus" and not pagar:
        raise typer.BadParameter("el juez opus es pago: correr con --pagar")
    cfg = cfg_for(config, paid=pagar)
    runs = corridas or [d for d in sorted(paths.RUNS.glob("*")) if (d / "3_choice.json").exists()]
    for run in runs:
        missing = [n for n in JUDGES if not (JUDGE_DIR / run.name / f"{n}.json").exists()]
        if missing and juez == "opus":
            for name in missing:
                judge_with_claude(cfg, run, name)
        elif missing:
            for task in write_tasks(cfg, run):
                if task.stem in missing:
                    console.print(f"{run.name}: falta el juez {task.stem}, tarea en {task}")
        r = score(cfg, run)
        if r:
            fid = r.get("fidelidad", {})
            rel = r.get("relevancia", {})
            console.print(
                f"{run.name}: faithfulness {fid.get('faithfulness')} "
                f"({fid.get('afirmaciones')} afirmaciones), answer relevance "
                f"{rel.get('answer_relevance')} (vara {rel.get('vara_contrastes')})"
            )


@app.command("evaluar-punta-a-punta")
def evaluar_punta_a_punta(
    experimento: Annotated[
        Path, typer.Argument(help="El experimento (datos/configs/punta_a_punta/*.yaml).")
    ],
    pagar: Annotated[bool, typer.Option("--pagar", help="Habilitar las llamadas pagas.")] = False,
    config: ConfigOpt = paths.CONFIG,
) -> None:
    """Variantes del flujo (plan → retrieve → choose) sobre ambientes reales vacíos y un juez
    que compara sus listas de a pares, en los dos órdenes (evaluation/endtoend.py). Lo que ya
    está (corridas, respuestas del juez) no se vuelve a pagar."""
    import yaml

    from amoblai.evaluation import endtoend as e2e

    load_env()
    exp = yaml.safe_load(experimento.read_text())
    rooms = e2e.load_rooms(Path(exp["ambientes"]))
    if exp.get("solo"):  # un subconjunto de los ambientes, por slug
        rooms = [r for r in rooms if r["slug"] in set(exp["solo"])]
    root = Path(exp["salida"])
    first = exp.get("plan_de")
    order = sorted(exp["variantes"], key=lambda v: v != first)  # la del plan, primero
    for name in order:
        over = [f"{k}={v}" for k, v in (exp["variantes"][name] or {}).items()]
        cfg = cfg_for(config, over, paid=pagar)
        from amoblai.rag.index import build_index, index_is_current

        if not index_is_current(cfg):
            build_index(cfg, log=console.print)
        plan_from = root / first if first and name != first else None
        e2e.run_variant(cfg, rooms, root / name, plan_from=plan_from, log=console.print)
    cfg = cfg_for(config, paid=pagar)
    llm = dict(cfg.evaluation.rerankers["opus"])
    for a, b in exp.get("comparaciones") or []:
        res = e2e.compare(cfg, llm, rooms, root, a, b)
        out = root / f"juez_{a}_vs_{b}{exp.get('sufijo', '')}.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
        t = Table(title=f"{a} vs {b} ({res['ambientes']} ambientes, {res['empates']} empates)")
        for col in ("variante", "gana", "útil", "aceptable", "pedido", "ambiente", "conjunto"):
            t.add_column(col)
        for v, s in res["resumen"].items():
            t.add_row(
                v,
                str(s["gana"]),
                f"{s['util']:.2f}",
                f"{s['aceptable']:.2f}",
                f"{s['request']:.2f}",
                f"{s['room']:.2f}",
                f"{s['together']:.2f}",
            )
        console.print(t)
        console.print(
            f"acuerdo entre órdenes {res['acuerdo_entre_ordenes']:.2f}; "
            f"votos a la posición A {res['votos_por_posicion_A']:.2f}; "
            f"US${res['costo_usd']:.2f}: {out}"
        )


@app.command("evaluar-espacio")
def evaluar_espacio(config: ConfigOpt = paths.CONFIG) -> None:
    """El espacio de embeddings del catálogo: ¿el vecino más cercano es del mismo kind? (por
    embedder) y la UMAP con una consulta del dominio y una de afuera. Gratis, local."""
    from amoblai.evaluation.space import OUT, analyze

    r = analyze(cfg_ikea(config))
    for e, m in r["separabilidad"].items():
        console.print(f"{e}: {m}")
    for name, q in r["consultas"].items():
        console.print(f"{name}: mejor coseno {q['mejor_coseno']}, top-10 {q['kinds_top10']}")
    console.print(f"→ {OUT}")


@app.command("evaluar-graduada")
def evaluar_graduada(
    armar: Annotated[
        int, typer.Option(help="Armar los lotes para los jueces con N consultas (0 = puntuar).")
    ] = 0,
    metodo: Annotated[str, typer.Option(help="El método de la ablación.")] = (
        "qwen3|description|filtro-type"
    ),
) -> None:
    """Relevancia graduada del top-3 (2 el mismo, 1 alternativa aceptable, 0 no sirve): el
    context precision de RAGAS con el juez etiquetando, el NDCG graduado y el acuerdo del juez con
    el ground truth. Los jueces son subagentes (gratis): primero --armar, después puntuar."""
    from amoblai.evaluation.graded import ANSWERS, BATCHES, make_batches, score
    from amoblai.evaluation.report import latest_runs

    if armar:
        run = [r for r in latest_runs(paths.EVAL_RUNS) if r.name.endswith("_ablacion-retrieval")]
        batches = make_batches(cfg_ikea(paths.CONFIG), run[-1], metodo, n=armar)
        console.print(f"{len(batches)} lotes en {BATCHES}/ (respuestas en {ANSWERS}/)")
        return
    meta = json.loads((BATCHES / "meta.json").read_text())
    r = score(paths.EVAL_RUNS / meta["run"], meta["method"])
    out = paths.RESULTS / "evaluacion_graduada" / "graduada.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1))
    console.print(json.dumps(r, ensure_ascii=False, indent=1))


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
