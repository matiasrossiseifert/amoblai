"""Webapp de flujo completo: muestra cada etapa del pipeline y de la evaluación.

    uv run --group apps python apps/flujo.py      (http://127.0.0.1:7861)

- Correr: el pipeline con cualquier configuración (embedder, fondo, filtro, umbral,
  generadores, entrada y modo del generador n.º 2, dry-run, imagen 1 dada).
- Ver corrida: imagen original, imagen 1, detecciones, recortes (crudo y consulta),
  top-k de IKEA con su similitud, el elegido, máscara, pasos del generador n.º 2,
  imagen final, lista de compra, uso, costo y tiempos.
- Evaluación del retriever: métricas de una corrida y, por ambiente, cada recorte
  con sus candidatos marcando los SKUs anotados.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr
import yaml

from amoblai.embeddings.registry import PRESETS
from amoblai.infra.images import load_image
from amoblai.infra.runs import RunContext
from amoblai.pipeline.query import CATEGORY_COLORS
from amoblai.vision.boxes import Box
from common import (
    PROVIDERS,
    get_pipeline,
    ikea_rooms,
    image_or_none,
    make_config,
    manual_inputs,
    read_json,
    read_jsonl,
    runs,
    save_manual_result,
    setup,
)

STAGE_IMAGES = [
    ("00_original.jpg", "Original (tamaño de trabajo)"),
    ("01_imagen1.jpg", "Imagen 1 (generador n.º 1)"),
    ("02_detecciones.jpg", "Detecciones"),
    ("06_final.jpg", "Imagen final"),
]


# ------------------------------------------------------------------ correr


def _overrides(values: dict[str, Any]) -> list[str]:
    ov = [
        f"embedding.name={values['embedder']}",
        f"background.method={values['background']}",
        f"retrieval.category_filter={str(values['category_filter']).lower()}",
        f"retrieval.top_k={int(values['top_k'])}",
        f"retrieval.threshold={values['threshold'] or 'auto'}",
        f"generation.generator1.provider={values['gen1']}",
        f"generation.generator2.provider={values['gen2']}",
        f"generation.generator1.quality={values['quality']}",
        f"generation.generator2.quality={values['quality']}",
        f"generation.gen2_base={values['gen2_base']}",
        f"generation.gen2_mode={values['gen2_mode']}",
        f"generation.composite={str(values['composite']).lower()}",
        f"budget.dry_run={str(values['dry_run']).lower()}",
    ]
    return ov


def _execute(state: dict[str, Any]) -> tuple:
    cfg = make_config(state["overrides"])
    run = RunContext.reopen(Path(state["run_dir"]), cfg)
    room = load_image(run.dir / "entrada_ambiente.png")
    image1 = (
        load_image(run.dir / "entrada_imagen1.png")
        if (run.dir / "entrada_imagen1.png").exists()
        else None
    )
    result = get_pipeline(cfg).run(room, state["prompt"], run=run, image1=image1)
    run.finish({"status": result.status, "timings_s": result.timings})
    if result.status == "pending_manual" and result.pending is not None:
        state["workdir"] = str(result.pending.workdir)
        images, prompt, instr = manual_inputs(result.pending.workdir)
        msg = f"⏸ Paso manual pendiente en `{result.pending.workdir}`"
        return state, str(run.dir), msg, gr.Group(visible=True), images, prompt, instr
    return (
        state,
        str(run.dir),
        f"Corrida `{run.run_id}`: **{result.status}**",
        gr.Group(visible=False),
        [],
        "",
        "",
    )


def start(room, room_choice, image1, image1_choice, prompt, *knobs):
    keys = [
        "embedder",
        "background",
        "category_filter",
        "top_k",
        "threshold",
        "gen1",
        "gen2",
        "quality",
        "gen2_base",
        "gen2_mode",
        "composite",
        "dry_run",
    ]
    values = dict(zip(keys, knobs, strict=True))
    if room is None and room_choice:
        room = load_image(room_choice)
    if image1 is None and image1_choice:
        image1 = load_image(image1_choice)
    if room is None and image1 is not None:
        room = image1  # para probar solo detección + retrieval con una foto amoblada
    if room is None:
        raise gr.Error("Subí una foto (o elegí una) para empezar.")
    overrides = _overrides(values)
    cfg = make_config(overrides)
    run = RunContext(cfg, "app", name="flujo")
    run.save_image("entrada_ambiente.png", room)
    if image1 is not None:
        run.save_image("entrada_imagen1.png", image1)
    state = {"run_dir": str(run.dir), "prompt": prompt or "", "overrides": overrides}
    return _execute(state)


def resume(uploaded, app_used, state):
    if not state or "workdir" not in state:
        raise gr.Error("No hay un paso manual pendiente.")
    if uploaded is None:
        raise gr.Error("Subí la imagen generada.")
    save_manual_result(Path(state["workdir"]), uploaded, app_used)
    return _execute(state)


# ------------------------------------------------------------- ver corrida


def pipeline_runs(results_dir: Path) -> list[str]:
    return sorted((str(p.parent) for p in Path(results_dir).rglob("resultado.json")), reverse=True)


def _candidate_gallery(raw_dir: Path, item: dict[str, Any]) -> list[tuple[str, str]]:
    out = []
    for c in item["candidates"]:
        mark = " ✅ elegido" if c["sku"] == item.get("chosen_sku") else ""
        caption = f"#{c['rank']} {c['sku']} · {c['name']} · {c['score']:.3f}{mark}"
        out.append((str(raw_dir / c["image_path"]), caption))
    return out


def render_run(run_dir: str | None) -> None:
    if not run_dir:
        gr.Markdown("Elegí una corrida.")
        return
    d = Path(run_dir)
    cfg = make_config()
    raw_dir = Path(cfg.paths.raw_dir)
    summary = read_json(d / "resultado.json") or {}
    run_root = (
        d
        if (d / "config.yaml").exists()
        else next(p for p in d.parents if (p / "config.yaml").exists())
    )
    # Una sub-corrida (un ambiente de una eval e2e) tiene sus propias métricas y uso.
    run_cfg = read_json(d / "metrics.json") or read_json(run_root / "metrics.json") or {}
    conf = yaml.safe_load((run_root / "config.yaml").read_text())
    g = conf["generation"]
    gr.Markdown(
        f"### {d.name} — estado: **{summary.get('status')}**\n"
        f"**Pedido:** {summary.get('prompt') or '(vacío)'}  \n"
        f"**Embedder:** {conf['embedding']['name']} · **fondo:** {conf['background']['method']} · "
        f"**filtro por categoría:** {conf['retrieval']['category_filter']} · **top-k:** {conf['retrieval']['top_k']} · "
        f"**umbral:** {conf['retrieval']['threshold']}  \n"
        f"**Generador 1:** {g['generator1']['provider']}:{g['generator1']['model']} · "
        f"**Generador 2:** {g['generator2']['provider']}:{g['generator2']['model']} ({g['generator2']['quality']}) · "
        f"**entrada gen. 2:** {summary.get('gen2_base')} · **modo:** {summary.get('gen2_mode')} · "
        f"**compositing:** {g['composite']} · **imagen 1:** {summary.get('image1_source')}  \n"
        f"**Tiempos (s):** {summary.get('timings_s')}"
    )
    with gr.Row():
        for name, label in STAGE_IMAGES:
            gr.Image(value=image_or_none(d / name), label=label, interactive=False, height=260)
    with gr.Accordion("Prompts de los generadores", open=False):
        for name in ("prompt.txt", "01_prompt_generador1.txt", "05_prompt_generador2.txt"):
            if (d / name).exists():
                gr.Textbox(value=(d / name).read_text(), label=name, lines=6)
    gr.Markdown("## Detección → recorte → retrieval")
    for item in summary.get("items", []):
        idx, cat = item["index"], item["category"]
        decision = (
            f"✅ elegido **{item['chosen_sku']}**"
            if item.get("chosen_sku")
            else f"❌ descartado (mejor similitud {item['candidates'][0]['score']:.3f} < umbral {item.get('threshold')})"
            if item["candidates"]
            else "❌ sin candidatos"
        )
        gr.Markdown(
            f"**Mueble {idx} · {cat}** (detector: '{item['det_label']}' {item['det_score']:.2f}, "
            f"fondo quitado: {item['background_removed']}) — {decision}"
        )
        with gr.Row():
            gr.Image(
                value=image_or_none(d / "03_recortes" / f"{idx:02d}_{cat}_crudo.jpg"),
                label="Recorte crudo",
                height=200,
                interactive=False,
                scale=1,
            )
            gr.Image(
                value=image_or_none(d / "03_recortes" / f"{idx:02d}_{cat}_consulta.jpg"),
                label="Consulta (fondo blanco)",
                height=200,
                interactive=False,
                scale=1,
            )
            gr.Gallery(
                value=_candidate_gallery(raw_dir, item),
                label="Top-k del catálogo IKEA",
                columns=5,
                height=230,
                scale=4,
            )
    gr.Markdown("## Generación (generador n.º 2)")
    with gr.Row():
        gr.Image(
            value=image_or_none(d / "05_mascara.png"),
            label="Máscara (zonas editables)",
            height=260,
            interactive=False,
        )
        steps = sorted((d / "05_pasos").glob("*.jpg")) if (d / "05_pasos").exists() else []
        gr.Gallery(
            value=[(str(p), p.stem) for p in steps],
            label="Pasos (modo un mueble por llamada)",
            columns=4,
            height=260,
        )
    gr.Markdown("## Salida, uso y costos")
    with gr.Row():
        gr.JSON(value=read_json(d / "lista_compra.json"), label="Lista de compra")
        usage = read_jsonl(d / "usage.jsonl") or read_jsonl(run_root / "usage.jsonl")
        gr.Dataframe(
            value=[
                [
                    u["stage"],
                    u["provider"],
                    u["model"],
                    u["cached"],
                    u["dry_run"],
                    u["manual"],
                    u["latency_s"],
                    u["cost_usd"],
                ]
                for u in usage
            ],
            headers=[
                "etapa",
                "proveedor",
                "modelo",
                "caché",
                "dry-run",
                "manual",
                "latencia s",
                "USD",
            ],
            label="Uso por llamada",
        )
    if run_cfg:
        gr.JSON(
            value={k: v for k, v in run_cfg.items() if k != "reid"}, label="Métricas de la corrida"
        )


# ---------------------------------------------------- evaluación retriever


def render_eval(run_dir: str | None, room_id: str | None) -> None:
    if not run_dir:
        gr.Markdown("Elegí una corrida de evaluación del retriever.")
        return
    d = Path(run_dir)
    metrics = read_json(d / "metrics.json") or {}
    ret, items = metrics.get("retrieval", {}), metrics.get("items", {})
    rnd = metrics.get("random_baseline", {})
    gr.Markdown(
        f"### {d.name}\n"
        f"Setup: `{metrics.get('setup')}` · ambientes: {metrics.get('rooms')} · recortes con respuesta: "
        f"{ret.get('n')} de {metrics.get('crops_total')}\n\n"
        "| | hit@1 | hit@5 | hit@10 | MRR@10 |\n|---|---|---|---|---|\n"
        f"| retriever | {ret.get('hit@1')} | {ret.get('hit@5')} | {ret.get('hit@10')} | {ret.get('mrr@10')} |\n"
        f"| azar | {rnd.get('hit@1')} | {rnd.get('hit@5')} | {rnd.get('hit@10')} | {rnd.get('mrr@10')} |\n\n"
        f"Recall por ítem@10: {items.get('recall@10')} · umbral calibrado: {metrics.get('threshold_calibration', {}).get('threshold')}"
    )
    if not room_id:
        return
    cfg = make_config()
    raw_dir = Path(cfg.paths.raw_dir)
    records = [r for r in read_jsonl(d / "recortes.jsonl") if r["room_id"] == room_id]
    room_path = raw_dir / "images" / "room_scenes" / room_id
    if room_path.exists():
        from PIL import ImageDraw

        img = load_image(room_path)
        draw = ImageDraw.Draw(img)
        for r in records:
            box = Box.from_list(r["box"])
            draw.rectangle(
                box.to_int(), outline=CATEGORY_COLORS.get(r["category"], (255, 200, 0)), width=4
            )
            draw.text(
                (box.x0 + 4, box.y0 + 4), f"{r['crop_index']} {r['category']}", fill=(255, 255, 255)
            )
        relevant = sorted({s for r in records for s in r["relevant_any"]})
        with gr.Row():
            gr.Image(value=img, label=room_id, height=360, interactive=False, scale=2)
            gr.Gallery(
                value=[(str(raw_dir / p), s) for s in relevant for p in _sku_images(cfg, s)],
                label="SKUs anotados en el ambiente (ground truth)",
                columns=4,
                height=360,
                scale=3,
            )
    for r in records:
        ok = "✅" if r["rank"] == 1 else ("🟡" if r["rank"] else "❌")
        gr.Markdown(
            f"{ok} **Recorte {r['crop_index']} · {r['category']}** (detector '{r['det_label']}' {r['det_score']}) — "
            f"rank del primer relevante: {r['rank']} · {'con' if r['answerable'] else 'sin'} respuesta posible"
        )
        with gr.Row():
            # Rutas relativas a resultados/ (almacén compartido de recortes).
            crop = Path(cfg.paths.results_dir) / r["crop_path"] if r.get("crop_path") else None
            gr.Image(
                value=image_or_none(crop) if crop else None,
                label="Consulta",
                height=180,
                interactive=False,
                scale=1,
            )
            gallery = []
            for rank, (sku, score) in enumerate(
                zip(r["ranked_skus"], r["scores"], strict=False), start=1
            ):
                mark = " ✓ anotado" if sku in r["relevant"] else ""
                for p in _sku_images(cfg, sku)[:1]:
                    gallery.append((str(raw_dir / p), f"#{rank} {sku} · {score:.3f}{mark}"))
            gr.Gallery(value=gallery, label="Top-k", columns=5, height=210, scale=5)


_CATALOG: dict[str, Any] = {}


def _sku_images(cfg, sku: str) -> list[str]:
    if "catalog" not in _CATALOG:
        from amoblai.indexing.indexer import load_or_build_catalog

        _CATALOG["catalog"] = load_or_build_catalog(cfg)
    catalog = _CATALOG["catalog"]
    return catalog.get(sku).image_paths if sku in catalog else []


def eval_rooms(run_dir: str | None):
    if not run_dir:
        return gr.Dropdown(choices=[], value=None)
    rooms = sorted({r["room_id"] for r in read_jsonl(Path(run_dir) / "recortes.jsonl")})
    return gr.Dropdown(choices=rooms, value=rooms[0] if rooms else None)


# ------------------------------------------------------------------- app


def build() -> gr.Blocks:
    cfg = make_config()
    with gr.Blocks(
        analytics_enabled=False, title="amoblai · flujo completo", fill_width=True
    ) as demo:
        gr.Markdown("# amoblai · flujo completo del pipeline")
        state = gr.State({})
        selected = gr.State(None)
        with gr.Tab("Correr"):
            with gr.Row():
                with gr.Column():
                    room = gr.Image(label="Ambiente vacío", type="pil")
                    room_choice = gr.Dropdown(
                        choices=[
                            str(p)
                            for p in Path(cfg.paths.empty_rooms_dir).glob("*.*")
                            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
                        ],
                        label="…o de ambientes_vacios/",
                    )
                    prompt = gr.Textbox(label="Pedido", lines=3)
                with gr.Column():
                    image1 = gr.Image(
                        label="Imagen 1 dada (opcional: saltea el generador n.º 1)", type="pil"
                    )
                    image1_choice = gr.Dropdown(
                        choices=ikea_rooms(cfg),
                        label="…o una foto de IKEA (living/comedor) como imagen 1",
                    )
            with gr.Accordion("Configuración", open=True):
                with gr.Row():
                    embedder = gr.Dropdown(
                        sorted(PRESETS), value=cfg.embedding.name, label="Embedder"
                    )
                    background = gr.Dropdown(
                        ["sam", "none", "rembg"], value=cfg.background.method, label="Quitar fondo"
                    )
                    category_filter = gr.Checkbox(
                        value=cfg.retrieval.category_filter, label="Filtro por categoría"
                    )
                    top_k = gr.Slider(1, 20, value=cfg.retrieval.top_k, step=1, label="top-k")
                    threshold = gr.Textbox(value="auto", label="Umbral (auto, número o null)")
                with gr.Row():
                    gen1 = gr.Dropdown(PROVIDERS, value="dry_run", label="Generador 1")
                    gen2 = gr.Dropdown(PROVIDERS, value="dry_run", label="Generador 2")
                    quality = gr.Dropdown(["low", "medium", "high"], value="low", label="Calidad")
                    gen2_base = gr.Radio(
                        ["image1", "original"],
                        value=cfg.generation.gen2_base,
                        label="Entrada gen. 2",
                    )
                    gen2_mode = gr.Radio(
                        ["single", "per_item"], value=cfg.generation.gen2_mode, label="Modo gen. 2"
                    )
                    composite = gr.Checkbox(value=cfg.generation.composite, label="Compositing")
                    dry_run = gr.Checkbox(value=False, label="Dry-run global (no gasta)")
            go = gr.Button("Correr pipeline", variant="primary")
            status = gr.Markdown()
            with gr.Group(visible=False) as manual_box:
                with gr.Row():
                    manual_gallery = gr.Gallery(
                        label="Entradas para el paso manual", columns=4, height=240
                    )
                    with gr.Column():
                        manual_prompt = gr.Textbox(label="Prompt", lines=8, buttons=["copy"])
                        manual_instr = gr.Markdown()
                with gr.Row():
                    uploaded = gr.Image(label="Resultado generado a mano", type="pil")
                    app_used = gr.Radio(["chatgpt", "gemini"], value="chatgpt", label="App usada")
                    cont = gr.Button("Continuar")
            knobs = [
                embedder,
                background,
                category_filter,
                top_k,
                threshold,
                gen1,
                gen2,
                quality,
                gen2_base,
                gen2_mode,
                composite,
                dry_run,
            ]
            outs = [
                state,
                selected,
                status,
                manual_box,
                manual_gallery,
                manual_prompt,
                manual_instr,
            ]
            go.click(start, [room, room_choice, image1, image1_choice, prompt, *knobs], outs)
            cont.click(resume, [uploaded, app_used, state], outs)

            @gr.render(inputs=selected)
            def _show_new(run_dir):
                if run_dir:
                    render_run(run_dir)

        with gr.Tab("Ver corrida"):
            refresh = gr.Button("Actualizar lista")
            run_pick = gr.Dropdown(
                choices=pipeline_runs(cfg.paths.results_dir),
                label="Corrida (incluye ambientes de evaluaciones e2e)",
            )
            refresh.click(
                lambda: gr.Dropdown(choices=pipeline_runs(cfg.paths.results_dir)), None, run_pick
            )

            @gr.render(inputs=run_pick)
            def _show(run_dir):
                render_run(run_dir)

        with gr.Tab("Evaluación del retriever"):
            eval_pick = gr.Dropdown(choices=runs(cfg, "retriever"), label="Corrida de evaluación")
            room_pick = gr.Dropdown(choices=[], label="Ambiente")
            eval_pick.change(eval_rooms, eval_pick, room_pick)

            @gr.render(inputs=[eval_pick, room_pick])
            def _show_eval(run_dir, room_id):
                render_eval(run_dir, room_id)

    return demo


if __name__ == "__main__":
    setup()
    cfg = make_config()
    from common import allowed_paths

    build().launch(server_port=7861, allowed_paths=allowed_paths(cfg))
