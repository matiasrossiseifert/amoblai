"""Herramienta mínima de etiquetado del set estricto (recorte → SKU exacto).

    uv run --group apps python apps/etiquetado.py      (http://127.0.0.1:7862)

Para cada ambiente de IKEA (livings y comedores) muestra los muebles que
encontró el detector. Para el recorte elegido muestra primero los SKUs anotados
en ese ambiente y después TODO el catálogo de la categoría en orden fijo: no se
muestran los candidatos de ningún embedder, así el set no queda sesgado a favor
de un modelo. Las etiquetas se agregan a anotaciones/estricto.jsonl.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import gradio as gr
from PIL import ImageDraw

from amoblai_imagen.categories import CategoryMap
from amoblai_imagen.data.ikea import IkeaDataset
from amoblai_imagen.eval.strict_eval import (
    NOT_FURNITURE,
    NOT_IN_CATALOG,
    StrictLabel,
    append_label,
    load_labels,
)
from amoblai_imagen.indexing.indexer import load_or_build_catalog
from amoblai_imagen.infra.cache import ArtifactCache
from amoblai_imagen.infra.images import load_image
from amoblai_imagen.vision.boxes import Box
from amoblai_imagen.vision.detection import build_detector
from common import allowed_paths, make_config, setup

_CTX: dict[str, Any] = {}


def ctx() -> dict[str, Any]:
    if not _CTX:
        cfg = make_config()
        cats = CategoryMap.load(cfg.paths.categories_file)
        catalog = load_or_build_catalog(cfg)
        ds = IkeaDataset.load(cfg.paths.raw_dir)
        rooms = [
            r
            for r in ds.rooms_of_type(cfg.dataset.eval_room_types)
            if any(s in catalog and catalog.get(s).category in cats.scope for s in r.skus)
        ]
        detector = build_detector(
            cfg.detection,
            cats.label_to_category,
            cfg.device,
            ArtifactCache(cfg.paths.cache_dir, "detecciones"),
        )
        _CTX.update(
            cfg=cfg,
            cats=cats,
            catalog=catalog,
            rooms={r.room_id: r for r in rooms},
            detector=detector,
        )
    return _CTX


def _labels_by_room() -> dict[str, list[StrictLabel]]:
    out: dict[str, list[StrictLabel]] = {}
    for lb in load_labels(ctx()["cfg"].paths.labels_file):
        out.setdefault(lb.room_id, []).append(lb)
    return out


def _progress() -> str:
    labels = load_labels(ctx()["cfg"].paths.labels_file)
    by_room = _labels_by_room()
    return f"Etiquetas: **{len(labels)}** en {len(by_room)} de {len(ctx()['rooms'])} ambientes."


def load_room(room_id: str | None):
    if not room_id:
        return None, gr.Radio(choices=[]), [], {}
    c = ctx()
    room = c["rooms"][room_id]
    image = load_image(Path(c["cfg"].paths.raw_dir) / room.path)
    dets = c["detector"].detect(image)
    done = {tuple(lb.box): lb for lb in _labels_by_room().get(room_id, [])}
    drawn = image.copy()
    draw = ImageDraw.Draw(drawn)
    choices = []
    for i, d in enumerate(dets):
        label = done.get(tuple(d.box.as_list()))
        color = (40, 170, 90) if label else (230, 60, 60)
        draw.rectangle(d.box.to_int(), outline=color, width=4)
        draw.text((d.box.x0 + 4, d.box.y0 + 4), str(i), fill=(255, 255, 255))
        tag = f" → {label.sku}" if label else ""
        choices.append((f"{i} · {d.category} ({d.score:.2f}){tag}", i))
    state = {"room_id": room_id, "dets": [d.to_dict() for d in dets]}
    return drawn, gr.Radio(choices=choices, value=0 if choices else None), [], state


def candidates(state: dict[str, Any], det_index: int | None, category: str | None):
    if not state or det_index is None:
        return None, [], gr.Dropdown(), {}
    c = ctx()
    det = state["dets"][int(det_index)]
    cat = category or det["category"]
    room = c["rooms"][state["room_id"]]
    image = load_image(Path(c["cfg"].paths.raw_dir) / room.path)
    crop = image.crop(Box.from_list(det["box"]).expand(0.04, *image.size).to_int())
    in_room = sorted(
        s for s in room.skus if s in c["catalog"] and c["catalog"].get(s).category == cat
    )
    rest = sorted(
        p.sku for p in c["catalog"].in_category(cat) if p.sku not in in_room and p.image_paths
    )
    skus = in_room + rest
    raw = Path(c["cfg"].paths.raw_dir)
    gallery = [
        (
            str(raw / c["catalog"].get(s).image_paths[0]),
            f"{'★ anotado · ' if s in in_room else ''}{s} · {c['catalog'].get(s).name}",
        )
        for s in skus
    ]
    sel = {"skus": skus, "det": det, "category": cat, "room_id": state["room_id"]}
    return crop, gallery, gr.Dropdown(value=cat), sel


def on_select(sel: dict[str, Any], evt: gr.SelectData):
    sel = dict(sel)
    sel["sku"] = sel["skus"][evt.index]
    return sel, f"Seleccionado: **{sel['sku']}**"


def save(sel: dict[str, Any], labeler: str, special: str | None = None):
    if not sel or "det" not in sel:
        raise gr.Error("Elegí un recorte.")
    sku = special or sel.get("sku")
    if not sku:
        raise gr.Error("Elegí un producto de la galería (o usá los botones de 'no está').")
    label = StrictLabel(
        room_id=sel["room_id"],
        box=sel["det"]["box"],
        category=sel["category"],
        sku=sku,
        labeler=labeler or "",
    )
    append_label(ctx()["cfg"].paths.labels_file, label)
    return f"Guardado: {sel['room_id']} · {sel['category']} → **{sku}**", _progress()


def next_unlabeled() -> str | None:
    done = _labels_by_room()
    for room_id in sorted(ctx()["rooms"]):
        if room_id not in done:
            return room_id
    return None


def build() -> gr.Blocks:
    c = ctx()
    with gr.Blocks(analytics_enabled=False, title="amoblai · etiquetado") as demo:
        gr.Markdown(
            "# Etiquetado del set estricto\nRecorte del detector → SKU exacto del catálogo."
        )
        progress = gr.Markdown(_progress())
        state, sel = gr.State({}), gr.State({})
        with gr.Row():
            room_pick = gr.Dropdown(choices=sorted(c["rooms"]), label="Ambiente", scale=4)
            next_btn = gr.Button("Siguiente sin etiquetar", scale=1)
            labeler = gr.Textbox(label="Quién etiqueta", scale=1)
        with gr.Row():
            room_img = gr.Image(
                label="Detecciones (verde = etiquetada)", interactive=False, height=420, scale=3
            )
            with gr.Column(scale=2):
                det_pick = gr.Radio(choices=[], label="Recorte")
                category = gr.Dropdown(
                    choices=c["cats"].scope, label="Categoría (corregir si el detector se equivocó)"
                )
                crop_img = gr.Image(label="Recorte", interactive=False, height=220)
        gallery = gr.Gallery(
            label="Catálogo de la categoría (★ = anotado en este ambiente)",
            columns=8,
            height=420,
            allow_preview=False,
        )
        chosen = gr.Markdown()
        with gr.Row():
            save_btn = gr.Button("Guardar etiqueta", variant="primary")
            not_in = gr.Button("No está en el catálogo")
            not_furn = gr.Button("No es un mueble / detección errónea")
        room_pick.change(load_room, room_pick, [room_img, det_pick, gallery, state])
        next_btn.click(next_unlabeled, None, room_pick)
        det_pick.change(
            lambda s, i: candidates(s, i, None),
            [state, det_pick],
            [crop_img, gallery, category, sel],
        )
        category.input(candidates, [state, det_pick, category], [crop_img, gallery, category, sel])
        gallery.select(on_select, sel, [sel, chosen])
        save_btn.click(lambda s, w: save(s, w), [sel, labeler], [chosen, progress])
        not_in.click(lambda s, w: save(s, w, NOT_IN_CATALOG), [sel, labeler], [chosen, progress])
        not_furn.click(lambda s, w: save(s, w, NOT_FURNITURE), [sel, labeler], [chosen, progress])
    return demo


if __name__ == "__main__":
    setup()
    build().launch(server_port=7862, allowed_paths=allowed_paths(make_config()))
