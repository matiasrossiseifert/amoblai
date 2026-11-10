"""Experimento de réplica: ¿el modelo de imagen reproduce un ambiente real si sabe exactamente qué
productos van? Y, como prueba de una idea a futuro, ¿lo hace mejor si además le marcamos dónde?

En los ambientes vacíos reales no hay con qué comparar la imagen: nadie sabe cómo "debería"
quedar. Un ambiente IKEA del ground truth sí lo tiene: la foto real, con sus productos anotados.
El experimento la vacía con el modelo de imagen, la vuelve a amoblar con esos mismos productos
(la lista ya decidida: acá no se prueba el retrieval sino el generador) y compara con la foto real:

- **sin_cajas**: el paso de imagen del flujo tal cual (scene_prompt_libre_v4): la foto vacía, las
  fotos de los productos y el pedido.
- **con_cajas**: lo mismo, con un rectángulo numerado por producto dibujado en la foto vacía, donde
  está ese mueble en la foto real (scene_prompt_cajas_v1): el producto tiene que llenar su caja.

Las cajas de la foto real las encuentran Grounding DINO y DINOv3 (evaluation/image.py, gratis): la
detección de cada categoría que más se parece a la foto del producto. Por imagen generada, con
los mismos modelos: dónde quedó cada producto (IoU de su caja con la de la foto real y distancia
entre los centros), si es el producto de la foto (coseno DINOv3 con su foto), cuánto se parece a la
foto real en conjunto (SSIM y coseno DINOv3 de la imagen entera) y si el cuarto sigue siendo el de
la foto vacía (SIFT, como el control del flujo).

Lo pago son las imágenes (la vaciada y las de cada variante); todo queda en la carpeta de salida
y lo que ya está no se vuelve a pagar.
"""

from __future__ import annotations

import json
import math
import shutil
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from amoblai.catalog.loader import Product
from amoblai.config import Config
from amoblai.evaluation import image as ev
from amoblai.furnish.generate import get_generator
from amoblai.furnish.room import preservation
from amoblai.infra.budget import check_spend, ledger_for
from amoblai.prompts import load_prompt

# Las categorías del detector que son muebles: lo que no debería quedar en la foto vaciada.
FURNITURE = {
    "sofa", "armchair", "chair", "ottoman", "stool", "bench", "table", "desk", "cabinet",
    "shelf", "dresser", "rug", "lamp",
}  # fmt: skip
COLORS = [
    (230, 57, 70), (29, 120, 230), (40, 160, 70), (245, 150, 0), (150, 60, 180),
    (0, 160, 160), (210, 80, 30), (90, 90, 90),
]  # fmt: skip
IOU_OK = 0.5


# cajas -----------------------------------------------------------------------------------------


def rel(box: Sequence[float], w: int, h: int) -> list[float]:
    """Una caja en píxeles -> en fracciones del ancho y del alto (para comparar imágenes de
    distinto tamaño)."""
    return [round(box[0] / w, 4), round(box[1] / h, 4), round(box[2] / w, 4), round(box[3] / h, 4)]


def to_px(r: Sequence[float], w: int, h: int) -> tuple[float, float, float, float]:
    return (r[0] * w, r[1] * h, r[2] * w, r[3] * h)


def center_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Entre los centros de dos cajas relativas, en fracción de la diagonal de la imagen."""
    dx = (a[0] + a[2] - b[0] - b[2]) / 2
    dy = (a[1] + a[3] - b[1] - b[3]) / 2
    return math.hypot(dx, dy) / math.sqrt(2)


def draw_boxes(img: Image.Image, boxes: Sequence[tuple[int, Sequence[float]]]) -> Image.Image:
    """La foto con un rectángulo de color por producto y su número (el de su imagen en el
    pedido al modelo) en un recuadro lleno en la esquina."""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    lw = max(3, round(out.width / 220))
    size = max(18, round(out.width / 32))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    for k, (n, r) in enumerate(boxes):
        color = COLORS[k % len(COLORS)]
        x0, y0, x1, y1 = to_px(r, out.width, out.height)
        x1, y1 = min(x1, out.width - 1), min(y1, out.height - 1)
        d.rectangle((x0, y0, x1, y1), outline=color, width=lw)
        tag = str(n)
        tw = d.textlength(tag, font=font)
        d.rectangle((x0, y0, x0 + tw + 2 * lw + 6, y0 + size + 2 * lw), fill=color)
        d.text((x0 + lw + 3, y0 + lw), tag, fill=(255, 255, 255), font=font)
    return out


# productos -------------------------------------------------------------------------------------


def descriptions(cfg: Config) -> dict[str, str]:
    spec = cfg.rag.describers.get(cfg.rag.describer, {})
    files = spec.get("file") or []
    out: dict[str, str] = {}
    for f in [files] if isinstance(files, str) else files:
        for line in (Path(cfg.root) / f).read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["id"]] = rec["text"]
    return out


def product_lines(products: Sequence[Product], texts: dict[str, str]) -> str:
    """Como el paso scene del flujo sin LLM: 'image N: <línea Type>, <medidas>'."""
    words = (("width", "wide"), ("depth", "deep"), ("height", "high"))
    lines = []
    for i, p in enumerate(products):
        first = (texts.get(p.id) or "").splitlines()[:1]
        kind = first[0].removeprefix("Type:").strip() if first else (p.kind or p.category)
        d = p.info.get("dimensions_cm") or {}
        size = ", ".join(f"{d[a]:.0f} cm {w}" for a, w in words if d.get(a)) or "size unknown"
        lines.append(f"image {i + 2}: {kind}, {size}")
    return "\n".join(lines)


def locate(
    models: ev.Models, image_path: Path, products: Sequence[Product], photo_vecs: dict
) -> dict[str, dict]:
    """Dónde está cada producto en una imagen: la detección de su categoría (o familia) que más
    se parece a su foto (ev.assign). Por producto: su caja relativa, la frase del detector y el
    coseno DINOv3 del recorte con su foto; sin detección, no aparece."""
    img = Image.open(image_path).convert("RGB")
    dets = [
        d for d in models.detect(image_path, ev.detector_labels()) if d.score >= ev.BOX_THRESHOLD
    ]
    if not dets:
        return {}
    vecs = models.embed([ev.crop(img, d.box) for d in dets])

    def sim(p: Product, d: ev.Det) -> float:
        return float(vecs[dets.index(d)] @ photo_vecs[p.id])

    picked = ev.assign(list(products), dets, sim)
    return {
        pid: {
            "caja": rel(dets[i].box, img.width, img.height),
            "detector": dets[i].label,
            "score": round(dets[i].score, 3),
            "coseno": round(float(vecs[i] @ photo_vecs[pid]), 4),
        }
        for pid, i in picked.items()
    }


def furniture_left(models: ev.Models, image_path: Path) -> list[str]:
    """Los muebles que el detector todavía ve (para la foto vaciada: tendría que ser ninguno)."""
    dets = models.detect(image_path, ev.detector_labels())
    return sorted(d.label for d in dets if d.score >= ev.BOX_THRESHOLD and d.category in FURNITURE)


# las imágenes pagas ----------------------------------------------------------------------------


def paid_image(cfg: Config, prompt: str, images: list[Path], dst: Path, what: str) -> dict:
    """Una imagen del generador del flujo (furnish.generator), con el tope de su cuenta."""
    gen = get_generator(cfg.furnish.generator, cfg)
    ledger = ledger_for(cfg.budget, gen.account)
    check_spend(
        ledger,
        gen.estimate_cost(images),
        paid=gen.paid,
        allow_paid=cfg.budget.allow_paid,
        what=what,
    )
    with tempfile.TemporaryDirectory() as tmp:
        g = gen.generate(prompt, images, Path(tmp))
        if gen.paid:
            ledger.record(
                step=what, provider=gen.name, model=g.model, cost_usd=g.cost_usd,
                cost_source=g.cost_source, cached=False,
            )  # fmt: skip
        if g.image is None:
            raise RuntimeError(f"{what}: el generador {gen.name!r} no devolvió imagen")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(g.image, dst)
    return {"model": g.model, "cost_usd": g.cost_usd, "meta": g.meta}


def pending(exp: dict, out: Path) -> int:
    """Cuántas imágenes pagas faltan (la vaciada cuenta por sus intentos posibles)."""
    n = 0 if (out / "vacio.png").exists() else int(exp.get("intentos_vaciar", 2))
    for v in exp["variantes"]:
        n += sum(not (out / v / f"{k}.png").exists() for k in range(1, exp["repeticiones"] + 1))
    return n


# métricas --------------------------------------------------------------------------------------


def measure(
    models: ev.Models,
    path: Path,
    original: Path,
    empty: Path,
    products: Sequence[Product],
    boxes: dict[str, list[float]],
    photo_vecs: dict,
) -> dict[str, Any]:
    from skimage.metrics import structural_similarity

    found = locate(models, path, products, photo_vecs)
    rows, ious = [], []
    for p in products:
        f = found.get(p.id)
        row: dict[str, Any] = {"id": p.id, "kind": p.kind, "detectado": f is not None}
        if f:
            iou = ev.iou(f["caja"], boxes[p.id])
            row.update(
                caja=f["caja"], iou=round(iou, 4), coseno=f["coseno"],
                centro=round(center_distance(f["caja"], boxes[p.id]), 4),
            )  # fmt: skip
        ious.append(row.get("iou", 0.0))
        rows.append(row)
    img = Image.open(path).convert("RGB")
    orig = Image.open(original).convert("RGB")
    g = np.asarray(img.convert("L").resize(orig.size), float) / 255
    o = np.asarray(orig.convert("L"), float) / 255
    whole = models.embed([orig, img])
    kept = preservation(
        Image.open(empty),
        img,
        [to_px(r["caja"], img.width, img.height) for r in rows if "caja" in r],
    )
    det = [r for r in rows if r["detectado"]]
    return {
        "productos": rows,
        "detectados": len(det),
        "iou_medio": round(float(np.mean(ious)), 4),  # los no detectados cuentan 0
        "en_su_lugar": sum(i >= IOU_OK for i in ious),  # IoU >= 0,5 con su caja real
        "centro_medio": round(float(np.mean([r["centro"] for r in det])), 4) if det else None,
        "coseno_producto": round(float(np.mean([r["coseno"] for r in det])), 4) if det else None,
        "ssim_con_la_real": round(float(structural_similarity(o, g, data_range=1.0)), 4),
        "dino_con_la_real": round(float(whole[0] @ whole[1]), 4),
        "ambiente": {k: kept.get(k) for k in ("sift_inliers", "sift_desplazamiento_mediano")},
    }


def summarize(rows: list[dict]) -> dict[str, Any]:
    """Por variante: la media de cada métrica y los valores de cada repetición."""
    keys = (
        "iou_medio", "en_su_lugar", "detectados", "centro_medio", "coseno_producto",
        "ssim_con_la_real", "dino_con_la_real",
    )  # fmt: skip
    out: dict[str, Any] = {}
    for k in keys:
        vals = [r[k] for r in rows if r.get(k) is not None]
        out[k] = {
            "media": round(float(np.mean(vals)), 4) if vals else None,
            "valores": vals,
        }
    return out


def overlay(img: Image.Image, real: dict[str, list[float]], found: dict[str, list[float]]) -> Image:
    """La imagen con la caja real de cada producto (fina, blanca) y dónde quedó (de color)."""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    lw = max(2, round(out.width / 400))
    for k, (pid, r) in enumerate(real.items()):
        d.rectangle(to_px(r, out.width, out.height), outline=(255, 255, 255), width=lw)
        if pid in found:
            d.rectangle(to_px(found[pid], out.width, out.height), outline=COLORS[k], width=2 * lw)
    return out


# el experimento --------------------------------------------------------------------------------


def run(
    cfg: Config, exp: dict, log: Callable[[str], None] = print, paid: bool = True
) -> dict[str, Any] | None:
    """Todo el experimento. `paid` False: solo lo gratis (las cajas, y las métricas de lo que ya
    está); devuelve None si todavía no hay foto vaciada."""
    out = Path(exp["salida"])
    out.mkdir(parents=True, exist_ok=True)
    original = Path(exp["foto"])
    catalog = ev._catalog(cfg)
    products = [catalog[i] for i in exp["productos"]]
    models = ev.Models(Path(cfg.cache_dir) / "imagen")
    photo_vecs = dict(
        zip(
            [p.id for p in products],
            models.photo_vectors([p.photos()[0] for p in products]),
            strict=True,
        )
    )
    state_f = out / "estado.json"
    state = json.loads(state_f.read_text()) if state_f.exists() else {"imagenes": {}}

    def save_state() -> None:
        state_f.write_text(json.dumps(state, ensure_ascii=False, indent=1))

    # 1. las cajas de la foto real (o las que fija el experimento)
    found = locate(models, original, products, photo_vecs)
    fixed = exp.get("cajas") or {}
    boxes = {p.id: fixed.get(p.id) or (found.get(p.id) or {}).get("caja") for p in products}
    missing = [pid for pid, b in boxes.items() if not b]
    if missing:
        raise ValueError(f"replica: sin caja en la foto real para {missing}; fijalas en `cajas`")
    (out / "cajas.json").write_text(json.dumps(
        {"cajas": boxes, "deteccion": found, "fijadas": sorted(fixed)}, ensure_ascii=False, indent=1
    ))  # fmt: skip
    orig_img = Image.open(original).convert("RGB")
    draw_boxes(orig_img, [(i + 2, boxes[p.id]) for i, p in enumerate(products)]).save(
        out / "real_con_cajas.jpg", quality=90
    )

    # 2. la foto vaciada. El control SIFT del flujo no sirve acá: casi todos los puntos de la
    # foto real están en los muebles y cuadros que se sacan (quedan unos pocos en las paredes).
    # Vale el intento que no deja muebles y conserva el cuarto donde no había muebles (SSIM fuera
    # de las cajas >= `ssim_vaciado`); si ninguno, el que menos muebles deja y más conserva.
    empty = out / "vacio.png"

    def check(dst: Path) -> dict:
        im = Image.open(dst)
        m = preservation(orig_img, im, [to_px(b, *im.size) for b in boxes.values()])
        left = furniture_left(models, dst)
        ssim = m.get("ssim_fuera_de_los_muebles") or 0.0
        return {"imagen": dst.name, "ok": not left and ssim >= exp.get("ssim_vaciado", 0.4),
                "quedan": left, "ssim_fuera_de_los_muebles": ssim,
                "sift_inliers": m.get("sift_inliers")}  # fmt: skip

    tries = [check(f) for f in sorted(out.glob("vacio_intento_*.png"))]
    if not any(t["ok"] for t in tries) and not empty.exists():
        if not paid:
            log("falta la foto vaciada (paga): nada más que medir")
            return None
        prompt = load_prompt(exp["prompt_vaciar"], cfg.root)
        for n in range(len(tries) + 1, int(exp.get("intentos_vaciar", 2)) + 1):
            dst = out / f"vacio_intento_{n}.png"
            log(f"vaciando la foto real (intento {n})")
            state["imagenes"][dst.name] = paid_image(
                cfg, prompt.fill(), [original], dst, "eval.replica.vaciar"
            )
            save_state()
            tries.append(check(dst))
            if tries[-1]["ok"]:
                break
    if tries:
        best = next((t for t in tries if t["ok"]), None) or min(
            tries, key=lambda t: (len(t["quedan"]), -t["ssim_fuera_de_los_muebles"])
        )
        if not empty.exists() or state.get("vaciado", {}).get("elegido") != best["imagen"]:
            shutil.copyfile(out / best["imagen"], empty)
        state["vaciado"] = {"intentos": tries, "elegido": best["imagen"]}
        save_state()
    empty_img = Image.open(empty).convert("RGB")
    with_boxes = out / "vacio_con_cajas.png"
    draw_boxes(empty_img, [(i + 2, boxes[p.id]) for i, p in enumerate(products)]).save(with_boxes)

    # 3. las variantes, `repeticiones` imágenes cada una
    lines = product_lines(products, descriptions(cfg))
    photos = [p.photos()[0] for p in products]
    for name, v in exp["variantes"].items():
        tmpl = load_prompt(v["prompt"], cfg.root)
        prompt = tmpl.fill(request=exp["pedido"], products=lines, last=len(products) + 1)
        (out / name).mkdir(exist_ok=True)
        (out / name / "prompt.txt").write_text(prompt + "\n")
        room = with_boxes if v.get("cajas") else empty
        for k in range(1, exp["repeticiones"] + 1):
            dst = out / name / f"{k}.png"
            if not dst.exists() and paid:
                log(f"{name}: imagen {k}")
                state["imagenes"][f"{name}/{k}.png"] = paid_image(
                    cfg, prompt, [room, *photos], dst, f"eval.replica.{name}"
                )
                save_state()

    # 4. las métricas (gratis)
    result: dict[str, Any] = {
        "foto": str(original),
        "productos": [
            {"id": p.id, "kind": p.kind, "imagen": i + 2} for i, p in enumerate(products)
        ],
        "pedido": exp["pedido"],
        "vaciado": state.get("vaciado"),
        "observaciones": exp.get("observaciones") or {},
        "vacio": {"quedan": furniture_left(models, empty)},
        "variantes": {},
        "costo_usd": round(sum(x["cost_usd"] for x in state["imagenes"].values()), 4),
    }
    for name in exp["variantes"]:
        rows = []
        for k in range(1, exp["repeticiones"] + 1):
            p = out / name / f"{k}.png"
            if not p.exists():
                continue
            m = measure(models, p, original, empty, products, boxes, photo_vecs)
            rows.append({"imagen": f"{name}/{k}.png", **m})
            got = {r["id"]: r["caja"] for r in m["productos"] if "caja" in r}
            overlay(Image.open(p), boxes, got).save(out / name / f"{k}_cajas.jpg", quality=88)
        result["variantes"][name] = {"resumen": summarize(rows), "imagenes": rows}
    (out / "resultados.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result
