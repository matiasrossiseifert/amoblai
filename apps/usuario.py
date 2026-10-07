"""Webapp de usuario: foto del ambiente vacío + pedido → foto amoblada + lista de compra.

    uv run --group apps python apps/usuario.py      (http://127.0.0.1:7860)

Si el generador es "manual", la app muestra las imágenes y el prompt para
generar a mano en ChatGPT o Gemini, y un lugar para subir el resultado.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr

from amoblai.infra.images import load_image
from amoblai.infra.runs import RunContext
from amoblai.pipeline.query import PipelineResult
from common import (
    PROVIDERS,
    SHOPPING_HEADERS,
    empty_rooms,
    get_pipeline,
    make_config,
    manual_inputs,
    save_manual_result,
    setup,
    shopping_rows,
)


def _overrides(provider: str, quality: str) -> list[str]:
    return [
        f"generation.generator1.provider={provider}",
        f"generation.generator2.provider={provider}",
        f"generation.generator1.quality={quality}",
        f"generation.generator2.quality={quality}",
    ]


def _run(state: dict[str, Any]) -> tuple:
    cfg = make_config(state["overrides"])
    run = RunContext.reopen(Path(state["run_dir"]), cfg)
    room = load_image(run.dir / "entrada_ambiente.png")
    result = get_pipeline(cfg).run(room, state["prompt"], run=run)
    run.finish({"status": result.status, "timings_s": result.timings})
    return _render(result, run, state)


def _render(result: PipelineResult, run: RunContext, state: dict[str, Any]) -> tuple:
    shopping_path = run.dir / "lista_compra.json"
    rows = shopping_rows(result.shopping_list)
    if result.status == "pending_manual" and result.pending is not None:
        images, prompt, instructions = manual_inputs(result.pending.workdir)
        state["workdir"] = str(result.pending.workdir)
        status = f"⏸ **Paso manual pendiente** ({run.run_id}). Generá la imagen y subila abajo."
        return (
            None,
            rows,
            None,
            status,
            gr.Group(visible=True),
            images,
            prompt,
            instructions,
            state,
        )
    msg = {
        "ok": f"✅ Listo: {len(result.accepted)} productos del catálogo ({run.run_id}).",
        "no_furniture": "No se encontraron muebles del catálogo por encima del umbral.",
    }.get(result.status, result.status)
    no_found = result.shopping_list.get("no_encontrados", [])
    if no_found:
        msg += f" Descartados por baja similitud: {len(no_found)}."
    final = result.final
    return (final, rows, str(shopping_path), msg, gr.Group(visible=False), [], "", "", state)


def furnish(room, room_choice, prompt, provider, quality):
    if room is None and room_choice:
        room = load_image(room_choice)
    if room is None:
        raise gr.Error("Subí una foto del ambiente vacío o elegí una de la lista.")
    overrides = _overrides(provider, quality)
    cfg = make_config(overrides)
    run = RunContext(cfg, "app", name="usuario")
    run.save_image("entrada_ambiente.png", room)  # sin pérdida: permite reanudar
    state = {"run_dir": str(run.dir), "prompt": prompt or "", "overrides": overrides}
    return _run(state)


def continue_manual(uploaded, app_used, state):
    if not state or "workdir" not in state:
        raise gr.Error("No hay ningún paso manual pendiente.")
    if uploaded is None:
        raise gr.Error("Subí la imagen que generaste.")
    save_manual_result(Path(state["workdir"]), uploaded, app_used)
    return _run(state)


def build() -> gr.Blocks:
    cfg = make_config()
    with gr.Blocks(analytics_enabled=False, title="amoblai") as demo:
        gr.Markdown("# amoblai\nSubí una foto de un ambiente vacío y contá cómo lo querés amoblar.")
        state = gr.State({})
        with gr.Row():
            with gr.Column():
                room = gr.Image(label="Ambiente vacío", type="pil", sources=["upload", "clipboard"])
                room_choice = gr.Dropdown(
                    choices=empty_rooms(cfg), label="…o elegí uno de ambientes_vacios/", value=None
                )
                prompt = gr.Textbox(
                    label="Pedido",
                    lines=3,
                    placeholder="Living nórdico, sofá gris claro, mesa ratona de madera y una alfombra clara",
                )
                with gr.Row():
                    provider = gr.Dropdown(
                        PROVIDERS,
                        value=cfg.generation.generator1.provider,
                        label="Generador de imagen",
                    )
                    quality = gr.Dropdown(
                        ["low", "medium", "high"],
                        value=cfg.generation.generator1.quality,
                        label="Calidad",
                    )
                go = gr.Button("Amoblar", variant="primary")
            with gr.Column():
                status = gr.Markdown()
                final = gr.Image(label="Ambiente amoblado", type="pil", interactive=False)
                table = gr.Dataframe(
                    headers=SHOPPING_HEADERS, label="Lista de compra", interactive=False
                )
                json_file = gr.File(label="Lista de compra (JSON)", interactive=False)
        with gr.Group(visible=False) as manual_box:
            gr.Markdown("## Paso manual")
            with gr.Row():
                manual_gallery = gr.Gallery(
                    label="Imágenes para subir (en este orden)", columns=4, height=260
                )
                with gr.Column():
                    manual_prompt = gr.Textbox(label="Prompt (copialo)", lines=8, buttons=["copy"])
                    manual_instr = gr.Markdown()
            with gr.Row():
                uploaded = gr.Image(label="Resultado generado a mano", type="pil")
                with gr.Column():
                    app_used = gr.Radio(
                        ["chatgpt", "gemini"], value="chatgpt", label="¿Con qué app lo generaste?"
                    )
                    cont = gr.Button("Continuar", variant="primary")
        outputs = [
            final,
            table,
            json_file,
            status,
            manual_box,
            manual_gallery,
            manual_prompt,
            manual_instr,
            state,
        ]
        go.click(furnish, [room, room_choice, prompt, provider, quality], outputs)
        cont.click(continue_manual, [uploaded, app_used, state], outputs)
    return demo


if __name__ == "__main__":
    setup()
    cfg = make_config()
    build().launch(server_port=7860, allowed_paths=[str(Path(cfg.paths.results_dir).resolve())])
