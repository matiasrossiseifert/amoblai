"""Webapp de prueba del flujo de amoblado: cada paso, a medida que se hace.

    uv run --group apps python apps/amoblar.py      (http://127.0.0.1:7860)

1. plan (Claude): cómo lee el ambiente y qué piezas hacen falta, con su consulta.
2. retrieve (RAG): los candidatos del catálogo (IKEA + Amazon Berkeley Objects) de cada pieza.
3. choose (Claude): la combinación elegida y por qué.
4. scene (Claude): el prompt para el modelo de imagen.
5. generate: la imagen final por API (Nano Banana 2 en fal) o a mano (te da las imágenes en
   orden y el prompt para pegar en ChatGPT o Gemini, y subís el resultado).

Las llamadas pagas solo salen si se tilda la casilla, dentro de los topes de
datos/configs/amoblai.yaml. La app no tiene lógica propia: corre el flujo de amoblai y muestra
la carpeta de la corrida.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from PIL import Image

from amoblai import paths
from amoblai.config import deep_merge, load_config
from amoblai.furnish.flow import run_flow
from amoblai.infra.budget import Ledger

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / paths.CONFIG
LLM_STEPS = ["furnish.plan", "furnish.choose", "furnish.scene"]
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


def config(generator: str, use_claude: bool, pay_image: bool):
    over: dict = {"furnish": {"generator": generator}}
    if use_claude:
        over = deep_merge(over, {"budget": {"allow_paid_steps": LLM_STEPS}})
    if pay_image:
        over = deep_merge(over, {"budget": {"allow_paid": True}})
    return load_config(CONFIG, over)


def read(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def spend_text(cfg) -> str:
    parts = []
    for account, cap in cfg.budget.accounts.items():
        spent = Ledger(cfg.budget.ledger, cap, account).spent()
        parts.append(f"{account}: US$ {spent:.3f} de {cap:.2f}")
    return "Gastado: " + " · ".join(parts)


def render(out: Path, cfg, log: list[str]) -> tuple:
    plan, found = read(out / "1_searches.json"), read(out / "2_candidates.json")
    choice, scene, image = (
        read(out / "3_choice.json"),
        read(out / "4_scene.json"),
        read(out / "5_image.json"),
    )
    md = [f"Corrida: `{out.relative_to(ROOT)}`"]
    pieces_rows = []
    if plan:
        a = plan["answer"]
        md.append(f"**Cómo leyó el ambiente:** {a.get('room', '')}")
        for p in a["pieces"]:
            limits = ", ".join(
                f"{k[4:-3]} ≤ {v} cm" for k, v in p.items() if k.startswith("max_") and v
            )
            pieces_rows.append(
                [
                    p["piece"],
                    ", ".join(p.get("kinds") or []),
                    limits,
                    p.get("why", ""),
                    p.get("query", ""),
                ]
            )
        if plan.get("unknown_kinds"):
            md.append(f"Kinds desconocidos descartados: {plan['unknown_kinds']}")
    sheets = sorted(str(p) for p in out.glob("2_candidates*.jpg"))
    if found and found.get("empty"):
        md.append(f"**Sin nada en el catálogo para:** {found['empty']}")
    shopping = []
    if choice:
        md.append(f"**Por qué esta combinación:** {choice['answer'].get('why', '')}")
        for f, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
            if not c.get("quantity", 1):
                continue  # el LLM la dejó afuera
            # los datos del elegido salen de sus candidatos: sirve para cualquier catálogo
            it = next((h for h in f["candidates"] if h["id"] == c["id"]), {})
            dims = it.get("dimensions_cm") or {}
            size = " × ".join(f"{dims[a]:g}" for a in ("width", "depth", "height") if dims.get(a))
            shopping.append(
                [
                    f["piece"],
                    f"{c['id']} x{c.get('quantity', 1)}",
                    it.get("name", ""),
                    it.get("kind") or it.get("category", ""),
                    f"{size} cm" if size else "—",
                    c.get("why", ""),
                ]
            )
    prompt = scene["answer"]["prompt"] if scene else ""
    final = next((str(p) for p in out.glob("final.*")), None)
    manual = out / "manual"
    # el flujo no guarda 5_image.json mientras la imagen manual espera: se ve por la carpeta.
    waiting = final is None and (
        (manual / "prompt.txt").exists() or bool(image and image.get("pending"))
    )
    manual_imgs = sorted(str(p) for p in manual.glob("[0-9]_*")) if waiting else []
    if waiting:
        md.append(
            "**Imagen final pendiente:** adjuntá las imágenes en orden en ChatGPT o Gemini, pegá el prompt y subí el resultado abajo."
        )
    md.append(spend_text(cfg))
    if log:
        md.append("```\n" + "\n".join(log[-12:]) + "\n```")
    return (
        "\n\n".join(md),
        pieces_rows,
        sheets,
        shopping,
        prompt,
        final,
        gr.Group(visible=waiting),
        manual_imgs,
    )


def go(photo, view, request, generator, use_claude, pay_image, state):
    if photo is None or not (request or "").strip():
        raise gr.Error("Subí la foto del ambiente y escribí el pedido.")
    out = ROOT / paths.RUNS / f"app-{time.strftime('%Y%m%d-%H%M%S')}"
    out.mkdir(parents=True)
    src = out / "entrada.jpg"
    Image.fromarray(photo).convert("RGB").save(src, quality=95)
    state = {"out": str(out), "photo": str(src), "request": request.strip(), "views": []}
    if view is not None:
        Image.fromarray(view).convert("RGB").save(out / "entrada_2.jpg", quality=95)
        state["views"] = [str(out / "entrada_2.jpg")]
    return advance(state, generator, use_claude, pay_image)


def advance(state, generator, use_claude, pay_image):
    cfg = config(generator, use_claude, pay_image)
    out, log = Path(state["out"]), []
    try:
        run_flow(
            state["photo"], state["request"], cfg, out, log=log.append, views=state.get("views", [])
        )
    except Exception as e:
        log.append(f"ERROR: {type(e).__name__}: {e}")
    return (*render(out, cfg, log), state)


def continue_run(generator, use_claude, pay_image, state):
    """Sigue la corrida actual (por ejemplo, después de tildar una casilla de pago)."""
    if not state:
        raise gr.Error("Todavía no hay una corrida: empezá con 'Amoblar'.")
    return advance(state, generator, use_claude, pay_image)


def upload_result(result, generator, use_claude, pay_image, state):
    if not state or result is None:
        raise gr.Error("Primero corré el flujo y subí la imagen generada.")
    manual = Path(state["out"]) / "manual"
    Image.fromarray(result).convert("RGB").save(manual / "result.png")
    return advance(state, generator, use_claude, pay_image)


def build() -> gr.Blocks:
    with gr.Blocks(title="amoblai", analytics_enabled=False) as demo:
        gr.Markdown(
            "# amoblai\nFoto de un ambiente + pedido → productos reales del catálogo (IKEA + Amazon Berkeley Objects), y el ambiente con ellos."
        )
        state = gr.State({})
        with gr.Row():
            photo = gr.Image(
                label="Foto del ambiente (la que se amobla)",
                type="numpy",
                sources=["upload", "clipboard"],
            )
            view = gr.Image(
                label="Otra foto del mismo ambiente (opcional, solo para entender el espacio)",
                type="numpy",
                sources=["upload", "clipboard"],
            )
            with gr.Column():
                request = gr.Textbox(
                    label="Pedido",
                    lines=3,
                    placeholder="un living nórdico, cálido, con un sofá y una alfombra",
                )
                generator = gr.Radio(
                    ["manual", "nano_banana_2"], value="manual", label="Imagen final"
                )
                use_claude = gr.Checkbox(
                    value=False,
                    label="Usar Claude para plan, choose y scene (pago, dentro del tope)",
                )
                pay_image = gr.Checkbox(
                    value=False, label="Generar la imagen por API (pago; incluye lo de arriba)"
                )
                with gr.Row():
                    run_btn = gr.Button("Amoblar (nueva corrida)", variant="primary")
                    cont_btn = gr.Button("Seguir esta corrida")
        status = gr.Markdown()
        pieces = gr.Dataframe(
            headers=["pieza", "kinds", "límites", "por qué", "consulta"],
            label="1 · Plan",
            wrap=True,
        )
        sheets = gr.Gallery(label="2 · Candidatos del catálogo por pieza", columns=1, height=420)
        shopping = gr.Dataframe(
            headers=["pieza", "SKU", "nombre", "kind", "medidas", "por qué"],
            label="3 · Elegidos (lista de compra)",
            wrap=True,
        )
        prompt = gr.Textbox(label="4 · Prompt para el modelo de imagen", lines=8, buttons=["copy"])
        final = gr.Image(label="5 · Ambiente amoblado", interactive=False)
        with gr.Group(visible=False) as manual_box:
            manual_imgs = gr.Gallery(
                label="Imágenes para adjuntar, en este orden",
                columns=5,
                height=220,
                buttons=["download", "download_all"],
            )
            result = gr.Image(label="Subí la imagen que generaste", type="numpy")
            send = gr.Button("Listo, seguir")
        outs = [status, pieces, sheets, shopping, prompt, final, manual_box, manual_imgs, state]
        run_btn.click(go, [photo, view, request, generator, use_claude, pay_image, state], outs)
        cont_btn.click(continue_run, [generator, use_claude, pay_image, state], outs)
        send.click(upload_result, [result, generator, use_claude, pay_image, state], outs)
    return demo


if __name__ == "__main__":
    os.chdir(ROOT)
    load_dotenv(ROOT / ".env", override=False)
    build().launch(server_port=7860, allowed_paths=[str(ROOT / paths.DATOS)])
