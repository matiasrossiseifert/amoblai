"""Webapp paso a paso para probar sin API keys: el sistema da los prompts, vos generás.

    uv run --group apps python apps/paso_a_paso.py      (http://127.0.0.1:7863)

1. Subís la foto del ambiente vacío y escribís el pedido → te da el prompt (y la
   imagen) para generar la imagen 1 en ChatGPT o Gemini.
2. Subís la imagen 1 → detecta los muebles, busca los productos en el catálogo y
   te da el prompt (y las imágenes, en orden) para generar la imagen final.
3. Subís la imagen final → lista de compra y, si querés, las métricas.

Usa el pipeline real con el editor manual: cada imagen que subís queda en la
caché (resultados/generaciones/manual/) y en la carpeta de la corrida, con la
app que usaste.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import gradio as gr

from amoblai.embeddings.registry import PRESETS
from amoblai.infra.images import load_image
from amoblai.infra.runs import RunContext
from amoblai.pipeline.query import PipelineResult
from common import (
    SHOPPING_HEADERS,
    allowed_paths,
    empty_rooms,
    get_pipeline,
    image_or_none,
    make_config,
    manual_inputs,
    read_json,
    save_manual_result,
    setup,
    shopping_rows,
)

STAGE_TITLES = {
    "generator1": "Paso 1 de 2 · Imagen 1: el ambiente amoblado con muebles genéricos",
    "generator2": "Paso 2 de 2 · Imagen final: cada mueble reemplazado por el producto real",
}
APP_HINTS = {
    "chatgpt": "Abrí https://chatgpt.com, adjuntá las imágenes **en este orden**, pegá el prompt y pedí la imagen.",
    "gemini": "Abrí https://gemini.google.com, adjuntá las imágenes **en este orden**, pegá el prompt y pedí la imagen.",
}


def _overrides(
    app: str, embedder: str, background: str, threshold: str, gen2_base: str, gen2_mode: str
) -> list[str]:
    return [
        "generation.generator1.provider=manual",
        "generation.generator2.provider=manual",
        f"generation.generator1.manual_app={app}",
        f"generation.generator2.manual_app={app}",
        f"embedding.name={embedder}",
        f"background.method={background}",
        f"retrieval.threshold={threshold.strip() or 'auto'}",
        f"generation.gen2_base={gen2_base}",
        f"generation.gen2_mode={gen2_mode}",
    ]


def _products(run_dir: Path) -> tuple[list[list[Any]], list[tuple[str, str]]]:
    """Muebles detectados en la imagen 1 con el producto elegido (o descartado)."""
    cfg = make_config()
    raw = Path(cfg.paths.raw_dir)
    summary = read_json(run_dir / "resultado.json") or {}
    rows, gallery = [], []
    for item in summary.get("items", []):
        best = item["candidates"][0] if item["candidates"] else None
        chosen = item.get("chosen_sku")
        rows.append(
            [
                item["index"],
                item["category"],
                chosen or "— (descartado)",
                best["name"] if best else "",
                round(best["score"], 3) if best else None,
                item.get("threshold"),
            ]
        )
        if chosen and best:
            gallery.append(
                (
                    str(raw / best["image_path"]),
                    f"{item['index']} · {item['category']} · {chosen} · {best['name']}",
                )
            )
    return rows, gallery


def _step_number(run_dir: Path, result: PipelineResult, gen2_mode: str) -> str:
    """En modo un mueble por llamada, indica cuál mueble toca."""
    if result.pending is None or result.pending.stage != "generator2" or gen2_mode != "per_item":
        return ""
    done = len(list((run_dir / "05_pasos").glob("*.jpg"))) if (run_dir / "05_pasos").exists() else 0
    return f" — mueble {done + 1} de {len(result.accepted)}"


def _advance(state: dict[str, Any], with_metrics: bool = False) -> tuple:
    cfg = make_config(state["overrides"])
    run = RunContext.reopen(Path(state["run_dir"]), cfg)
    pipeline = get_pipeline(cfg)
    result = pipeline.run(load_image(run.dir / "entrada_ambiente.png"), state["prompt"], run=run)
    metrics: dict[str, Any] = {"status": result.status, "timings_s": result.timings}
    if with_metrics and result.status == "ok":
        from amoblai.eval.e2e_eval import evaluate_result

        metrics |= evaluate_result(result, pipeline)
    run.finish(metrics)

    rows, products = _products(run.dir)
    image1 = image_or_none(run.dir / "01_imagen1.jpg")
    detections = image_or_none(run.dir / "02_detecciones.jpg")
    if result.status == "pending_manual" and result.pending is not None:
        state["workdir"] = str(result.pending.workdir)
        images, prompt, _ = manual_inputs(result.pending.workdir)
        to_upload = [(p, n) for p, n in images if Path(p).name.startswith("entrada_")]
        zone = result.pending.workdir / "zona_a_editar.png"
        title = STAGE_TITLES.get(result.pending.stage, result.pending.stage) + _step_number(
            run.dir, result, cfg.generation.gen2_mode
        )
        app = cfg.generation.generator1.manual_app
        hint = APP_HINTS.get(app, "")
        if result.pending.stage == "generator2":
            hint += (
                "\n\nLa imagen 1 es el ambiente y las siguientes son las fotos de los productos, en el orden del prompt."
                " `zona_a_editar.png` es solo de referencia (no la subas): si la app deja seleccionar una región, marcá esa."
            )
        step_md = f"## {title}\n{hint}\n\nCorrida: `{run.run_id}`"
        return (
            state,
            step_md,
            prompt,
            to_upload,
            [p for p, _ in to_upload],
            gr.Image(value=image_or_none(zone), visible=zone.exists()),
            gr.Group(visible=True),
            None,
            image1,
            detections,
            rows,
            products,
            None,
            [],
            None,
            None,
        )
    state.pop("workdir", None)
    if result.status == "no_furniture":
        done_md = (
            "## No se eligió ningún producto\nNingún mueble de la imagen 1 superó el umbral de similitud. "
            "Probá con otra imagen 1, otro embedder o un umbral más bajo (Opciones)."
        )
    else:
        done_md = (
            f"## ✅ Listo\n{len(result.accepted)} productos del catálogo. Corrida: `{run.run_id}`"
        )
    shopping = result.shopping_list
    shown_metrics = (
        {k: v for k, v in metrics.items() if k not in ("reid",)} if with_metrics else None
    )
    return (
        state,
        done_md,
        "",
        [],
        [],
        gr.Image(value=None, visible=False),
        gr.Group(visible=False),
        None,
        image1,
        detections,
        rows,
        products,
        result.final,
        shopping_rows(shopping),
        str(run.dir / "lista_compra.json"),
        shown_metrics,
    )


def start(room, room_choice, request, app, embedder, background, threshold, gen2_base, gen2_mode):
    if room is None and room_choice:
        room = load_image(room_choice)
    if room is None:
        raise gr.Error("Subí la foto del ambiente vacío (o elegí una de la lista).")
    overrides = _overrides(app, embedder, background, threshold, gen2_base, gen2_mode)
    cfg = make_config(overrides)
    run = RunContext(cfg, "app", name="paso-a-paso")
    run.save_image("entrada_ambiente.png", room)  # sin pérdida: permite reanudar
    state = {"run_dir": str(run.dir), "prompt": request or "", "overrides": overrides}
    return _advance(state)


def submit(uploaded, app_used, with_metrics, state):
    if not state or "workdir" not in state:
        raise gr.Error("No hay ningún paso esperando una imagen. Empezá con el botón 1.")
    if uploaded is None:
        raise gr.Error("Subí la imagen que generaste.")
    save_manual_result(Path(state["workdir"]), uploaded, app_used)
    return _advance(state, with_metrics)


def _warm_up() -> None:
    """Carga los modelos en segundo plano para que el primer paso sea inmediato."""
    base = make_config()
    try:
        get_pipeline(
            make_config(
                _overrides(
                    "chatgpt",
                    base.embedding.name,
                    base.background.method,
                    "auto",
                    base.generation.gen2_base,
                    base.generation.gen2_mode,
                )
            )
        )
    except Exception as exc:
        print(f"Precarga fallida (se reintenta al usar la app): {exc}")


def build() -> gr.Blocks:
    cfg = make_config()
    with gr.Blocks(analytics_enabled=False, title="amoblai · paso a paso") as demo:
        gr.Markdown(
            "# amoblai · paso a paso (sin API keys)\n"
            "El sistema arma los prompts; vos generás las imágenes en ChatGPT o Gemini y las subís acá."
        )
        state = gr.State({})
        with gr.Row():
            with gr.Column():
                room = gr.Image(label="Ambiente vacío", type="pil", sources=["upload", "clipboard"])
                room_choice = gr.Dropdown(
                    choices=empty_rooms(cfg), value=None, label="…o elegí uno de ambientes_vacios/"
                )
            with gr.Column():
                request = gr.Textbox(
                    label="Pedido",
                    lines=4,
                    placeholder="Living nórdico: sofá gris claro, mesa ratona de madera y una alfombra beige",
                )
                app = gr.Radio(
                    ["chatgpt", "gemini"],
                    value="chatgpt",
                    label="¿Dónde vas a generar las imágenes?",
                )
                with gr.Accordion("Opciones", open=False):
                    gr.Markdown(
                        "Mejor configuración medida en la ablación: **siglip2** con fondo **none** (ver docs/EXPERIMENTOS.md)."
                    )
                    with gr.Row():
                        embedder = gr.Dropdown(
                            sorted(PRESETS), value=cfg.embedding.name, label="Embedder"
                        )
                        background = gr.Dropdown(
                            ["none", "sam", "rembg"],
                            value=cfg.background.method,
                            label="Quitar fondo de los recortes",
                        )
                        threshold = gr.Textbox(value="auto", label="Umbral (auto, número o null)")
                    with gr.Row():
                        gen2_base = gr.Radio(
                            ["image1", "original"],
                            value=cfg.generation.gen2_base,
                            label="La imagen final parte de…",
                        )
                        gen2_mode = gr.Radio(
                            ["single", "per_item"],
                            value=cfg.generation.gen2_mode,
                            label="Generación final",
                        )
                go = gr.Button("1 · Darme el prompt de la imagen 1", variant="primary")

        step_md = gr.Markdown("## Empezá subiendo la foto y el pedido")
        with gr.Row():
            with gr.Column(scale=3):
                prompt = gr.Textbox(
                    label="Prompt para copiar", lines=12, buttons=["copy"], interactive=False
                )
            with gr.Column(scale=2):
                to_upload = gr.Gallery(
                    label="Imágenes para adjuntar (en este orden)",
                    columns=3,
                    height=260,
                    buttons=["download", "download_all", "fullscreen"],
                )
                files = gr.File(label="Descargar", file_count="multiple", interactive=False)
                zone = gr.Image(
                    label="Zona a editar (referencia, no se sube)",
                    visible=False,
                    height=200,
                    interactive=False,
                )
        with gr.Group(visible=False) as upload_box, gr.Row():
            uploaded = gr.Image(
                label="Subí acá la imagen que generaste",
                type="pil",
                sources=["upload", "clipboard"],
            )
            with gr.Column():
                app_used = gr.Radio(
                    ["chatgpt", "gemini"], value="chatgpt", label="¿Con qué app la generaste?"
                )
                with_metrics = gr.Checkbox(
                    value=False,
                    label="Al terminar, calcular métricas (re-identificación, SSIM, cobertura)",
                )
                send = gr.Button("2 · Listo, siguiente paso", variant="primary")

        gr.Markdown("## Lo que va armando el sistema")
        with gr.Row():
            image1 = gr.Image(label="Imagen 1", interactive=False, height=280)
            detections = gr.Image(label="Muebles detectados", interactive=False, height=280)
            final = gr.Image(label="Imagen final", interactive=False, height=280)
        with gr.Row():
            products_table = gr.Dataframe(
                headers=[
                    "#",
                    "Categoría",
                    "SKU elegido",
                    "Producto más parecido",
                    "Similitud",
                    "Umbral",
                ],
                label="Retrieval: un mueble por fila",
                interactive=False,
            )
            products = gr.Gallery(label="Productos elegidos del catálogo", columns=4, height=260)
        with gr.Row():
            shopping = gr.Dataframe(
                headers=SHOPPING_HEADERS, label="Lista de compra", interactive=False
            )
            shopping_file = gr.File(label="Lista de compra (JSON)", interactive=False)
        metrics = gr.JSON(label="Métricas de punta a punta")

        outputs = [
            state,
            step_md,
            prompt,
            to_upload,
            files,
            zone,
            upload_box,
            uploaded,
            image1,
            detections,
            products_table,
            products,
            final,
            shopping,
            shopping_file,
            metrics,
        ]
        go.click(
            start,
            [
                room,
                room_choice,
                request,
                app,
                embedder,
                background,
                threshold,
                gen2_base,
                gen2_mode,
            ],
            outputs,
        )
        send.click(submit, [uploaded, app_used, with_metrics, state], outputs)
        app.change(lambda a: a, app, app_used)
    return demo


if __name__ == "__main__":
    setup()
    threading.Thread(target=_warm_up, daemon=True).start()
    build().launch(server_port=7863, allowed_paths=allowed_paths(make_config()))
