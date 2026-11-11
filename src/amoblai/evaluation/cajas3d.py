"""Cajas 3D de los muebles de una foto: el volumen que ocupa cada uno en el cuarto, para dibujarlo
en perspectiva (experimento de réplica, variante con_cajas_3d).

Un rectángulo en la foto no dice dónde está el mueble en el piso ni cuánto ocupa hacia el fondo; un
prisma apoyado en el piso, orientado como el cuarto, sí. Todo sale de la foto, gratis y local:

1. Profundidad métrica y distancia focal con Depth Pro (Apple, monocular): cada píxel pasa a un
   punto 3D en metros.
2. Una máscara por mueble con SAM, a partir de su caja 2D y, si el experimento los da, puntos de
   ayuda (de las tres que da, la más grande entre las de confianza parecida). A cada una se le
   restan las más chicas que se le superponen: al sofá el puf, a la alfombra lo que tiene encima.
3. El piso: un plano (RANSAC) sobre la alfombra (o, si no hay, lo que no es mueble en el tercio de
   abajo). La pared: el plano vertical más grande entre lo que no es mueble en la mitad de arriba.
   Con eso, los ejes del cuarto: a lo largo de la pared, hacia afuera de ella y hacia arriba.
4. Por mueble, sus puntos en esos ejes (sin los pegados al piso, que suelen ser alfombra o sombra):
   la caja va de los percentiles 5 a 95 en el piso y del piso al percentil 95 en altura (lo de
   atrás no se ve: la caja es lo que se ve del mueble). La alfombra es una caja chata de 3 cm.

Las cajas se proyectan con la misma cámara y se guardan como 8 esquinas en fracciones del ancho y
del alto: se dibujan igual sobre la foto vaciada, que tiene el mismo encuadre.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Las aristas y caras de una caja con las esquinas 0-3 abajo y 4-7 arriba, en el mismo orden.
EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4),
         (0, 4), (1, 5), (2, 6), (3, 7)]  # fmt: skip
FACES = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
PCT = 5  # percentiles de la caja: 5 a 95
NEAR_FLOOR = 0.08  # m: los puntos más bajos no cuentan para la caja (alfombra, sombra)
RUG_HEIGHT = 0.03  # m


# geometría pura (testeable) -------------------------------------------------------------------


def fit_plane(pts: np.ndarray, thr: float, iters: int = 2000, seed: int = 0):
    """RANSAC + ajuste por mínimos cuadrados: (normal unitaria, d) con n·p + d = 0, y la fracción de
    puntos que lo apoyan."""
    rng = np.random.default_rng(seed)
    best, best_n = None, 0
    for _ in range(iters):
        s = pts[rng.choice(len(pts), 3, replace=False)]
        n = np.cross(s[1] - s[0], s[2] - s[0])
        norm = np.linalg.norm(n)
        if norm < 1e-9:
            continue
        n = n / norm
        inl = np.abs(pts @ n + (-n @ s[0])) < thr
        if inl.sum() > best_n:
            best, best_n = inl, int(inl.sum())
    q = pts[best]
    c = q.mean(0)
    n = np.linalg.svd(q - c, full_matrices=False)[2][-1]
    return n, float(-n @ c), best_n / len(pts)


def box_corners(origin, axes, b: dict[str, Sequence[float]]) -> np.ndarray:
    """Las 8 esquinas (cámara, metros) de una caja dada en los ejes del cuarto: `along` (a lo
    largo de la pared), `out` (hacia afuera de la pared) y `h` (altura), cada uno [min, max]."""
    a_along, a_out, a_up = axes
    out = []
    for h in b["h"]:
        for al, ou in ((b["along"][0], b["out"][0]), (b["along"][1], b["out"][0]),
                       (b["along"][1], b["out"][1]), (b["along"][0], b["out"][1])):  # fmt: skip
            out.append(origin + al * a_along + ou * a_out + h * a_up)
    return np.array(out)


def project(pts: np.ndarray, f: float, cx: float, cy: float) -> np.ndarray:
    return np.stack([f * pts[:, 0] / pts[:, 2] + cx, f * pts[:, 1] / pts[:, 2] + cy], -1)


def visible_corners(corners: np.ndarray) -> set[int]:
    """Las esquinas de las caras que miran a la cámara (en el origen): las aristas entre dos de
    ellas se dibujan llenas, las demás finas."""
    c = corners.mean(0)
    vis: set[int] = set()
    for face in FACES:
        fc = corners[face].mean(0)
        if (fc - c) @ (-fc) > 0:
            vis.update(face)
    return vis


def draw_boxes3d(img: Image.Image, boxes: Sequence[tuple[int, dict]], colors) -> Image.Image:
    """La foto con cada caja 3D en alambre: aristas visibles gruesas, ocultas finas, y el número
    del producto en la esquina de arriba más a la izquierda."""
    out = img.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    w, h = out.size
    lw = max(3, round(w / 256))
    size = max(18, round(w / 38))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        font = ImageFont.load_default()
    for k, (n, box) in enumerate(boxes):
        color = colors[k % len(colors)]
        px = np.array(box["esquinas"]) * [w, h]
        vis = set(box["visibles"])
        for a, b in EDGES:
            full = a in vis and b in vis
            d.line([tuple(px[a]), tuple(px[b])], fill=color, width=lw if full else max(1, lw // 2))
        top = px[4:]
        x, y = top[int(np.argmin(top[:, 1] + 0.3 * top[:, 0]))]
        x, y = min(max(x, 0), w - size), min(max(y, size + 2 * lw), h)
        tag = str(n)
        tw = d.textlength(tag, font=font)
        d.rectangle((x, y - size - 2 * lw, x + tw + 2 * lw + 6, y), fill=color)
        d.text((x + lw + 3, y - size - lw), tag, fill=(255, 255, 255), font=font)
    return out


# lo que corre modelos ----------------------------------------------------------------------------


def _depth(photo: Path, cache: Path) -> tuple[np.ndarray, float]:
    key = hashlib.sha1(photo.read_bytes()).hexdigest()[:16]
    f = cache / f"depthpro_{key}.npz"
    if f.exists():
        z = np.load(f)
        return z["depth"].astype(np.float64), float(z["focal"])
    import torch
    from transformers import DepthProForDepthEstimation, DepthProImageProcessor

    img = Image.open(photo).convert("RGB")
    proc = DepthProImageProcessor.from_pretrained("apple/DepthPro-hf")
    model = DepthProForDepthEstimation.from_pretrained("apple/DepthPro-hf").eval()
    with torch.no_grad():
        out = model(**proc(images=img, return_tensors="pt"))
    post = proc.post_process_depth_estimation(out, target_sizes=[(img.height, img.width)])[0]
    depth, focal = post["predicted_depth"].float().numpy(), float(post["focal_length"])
    cache.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, depth=depth.astype(np.float16), focal=focal)
    return depth.astype(np.float64), focal


def _masks(
    photo: Path, boxes: dict[str, Sequence[float]], points: dict[str, dict] | None = None
) -> dict[str, np.ndarray]:
    import torch
    from scipy import ndimage
    from transformers import SamModel, SamProcessor

    img = Image.open(photo).convert("RGB")
    w, h = img.size
    sp = SamProcessor.from_pretrained("facebook/sam-vit-base")
    sm = SamModel.from_pretrained("facebook/sam-vit-base").eval()
    emb, masks = None, {}
    for pid, (x0, y0, x1, y1) in boxes.items():
        extra: dict[str, Any] = {}
        pts = (points or {}).get(pid)
        if pts:  # puntos de ayuda (relativos): adentro del mueble y afuera
            xy = [[x * w, y * h] for x, y in pts.get("adentro", []) + pts.get("afuera", [])]
            labels = [1] * len(pts.get("adentro", [])) + [0] * len(pts.get("afuera", []))
            extra = {"input_points": [[xy]], "input_labels": [[labels]]}
        inp = sp(
            img, input_boxes=[[[x0 * w, y0 * h, x1 * w, y1 * h]]], return_tensors="pt", **extra
        )
        with torch.no_grad():
            if emb is None:
                emb = sm.get_image_embeddings(inp["pixel_values"])
            o = sm(
                image_embeddings=emb,
                input_boxes=inp["input_boxes"],
                input_points=inp.get("input_points"),
                input_labels=inp.get("input_labels"),
                multimask_output=True,
            )
        ms = sp.image_processor.post_process_masks(
            o.pred_masks, inp["original_sizes"], inp["reshaped_input_sizes"]
        )[0][0].numpy()
        scores = o.iou_scores[0, 0].numpy()
        ok = [i for i in range(len(ms)) if scores[i] >= scores.max() - 0.1]
        masks[pid] = ms[max(ok, key=lambda i: ms[i].sum())]
    # a cada máscara se le restan las más chicas que se le superponen
    out = {}
    for pid, m in masks.items():
        m = m.copy()
        for other, mo in masks.items():
            if other != pid and mo.sum() < masks[pid].sum() and (mo & m).any():
                m &= ~ndimage.binary_dilation(mo, iterations=4)
        out[pid] = m
    return out


def estimate(
    photo: Path,
    boxes: dict[str, Sequence[float]],
    rug: str | None,
    cache: Path,
    points: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """Las cajas 3D de los productos de `boxes` (cajas 2D relativas) en la foto. `rug`: el id de
    la alfombra, si hay (es la mejor muestra del piso y su caja es chata). `points`: por producto,
    puntos relativos `adentro` y `afuera` para ayudar a SAM cuando la caja sola no alcanza."""
    from scipy import ndimage

    depth, f = _depth(photo, cache)
    masks = _masks(photo, boxes, points)
    hgt, wid = depth.shape
    cx, cy = wid / 2, hgt / 2
    v, u = np.mgrid[0:hgt, 0:wid]
    pts = np.stack([(u - cx) / f * depth, (v - cy) / f * depth, depth], -1)
    furniture = np.zeros((hgt, wid), bool)
    for m in masks.values():
        furniture |= m
    free = ~ndimage.binary_dilation(furniture, iterations=8)

    # el piso: la alfombra (lejos de lo que tiene encima) o, si no hay, lo libre del tercio de abajo
    if rug:
        others = furniture & ~masks[rug]
        floor_px = ndimage.binary_erosion(masks[rug], iterations=6) & ~ndimage.binary_dilation(
            others, iterations=8
        )
    else:
        floor_px = free.copy()
        floor_px[: int(hgt * 2 / 3)] = False
    n, d, floor_fit = fit_plane(pts[floor_px][::3], thr=0.02)
    if n[1] > 0:  # hacia arriba (la y de la cámara apunta hacia abajo)
        n, d = -n, -d
    # la pared: el plano casi vertical más grande entre lo que no es mueble en la mitad de arriba
    upper = free.copy()
    upper[hgt // 2 :] = False
    cand = pts[upper][::2]
    wall_n, wall_d, wall_fit = fit_plane(cand, thr=0.03)
    for _ in range(3):  # si salió algo inclinado, se saca y se prueba de nuevo
        if abs(wall_n @ n) < 0.1:
            break
        cand = cand[np.abs(cand @ wall_n + wall_d) >= 0.03]
        wall_n, wall_d, wall_fit = fit_plane(cand, thr=0.03)
    a_out = wall_n - (wall_n @ n) * n
    a_out /= np.linalg.norm(a_out)
    if a_out[2] > 0:  # hacia la cámara
        a_out = -a_out
    a_along = np.cross(n, a_out)
    origin = -d * n  # el punto del piso más cercano a la cámara
    axes = (a_along, a_out, n)

    def room(p: np.ndarray) -> np.ndarray:
        q = p - origin
        return np.stack([q @ a_along, q @ a_out, q @ n], -1)

    result: dict[str, Any] = {}
    for pid, m in masks.items():
        m = ndimage.binary_erosion(m, iterations=4 if m.mean() > 0.02 else 1)
        q = room(pts[m])
        if pid != rug:
            q = q[q[:, 2] > NEAR_FLOOR]
        lo, hi = np.percentile(q, PCT, 0), np.percentile(q, 100 - PCT, 0)
        b = {"along": [lo[0], hi[0]], "out": [lo[1], hi[1]], "h": [0.0, hi[2]]}
        if pid == rug:
            b["h"] = [0.0, RUG_HEIGHT]
        b = {k: [round(float(x), 3) for x in vals] for k, vals in b.items()}
        corners = box_corners(origin, axes, b)
        px = project(corners, f, cx, cy) / [wid, hgt]
        result[pid] = {
            "ejes_m": b,
            "medidas_m": {k: round(b[k][1] - b[k][0], 2) for k in b},
            "esquinas": px.round(4).tolist(),
            "visibles": sorted(visible_corners(corners)),
            "mascara_px": int(masks[pid].sum()),
        }
    return {
        "camara": {"focal_px": round(f, 1), "ancho": wid, "alto": hgt},
        "piso": {"normal": n.round(4).tolist(), "altura_camara_m": round(abs(d), 3),
                 "ajuste": round(floor_fit, 3)},
        "pared": {"normal": a_out.round(4).tolist(), "ajuste": round(wall_fit, 3),
                  "angulo_con_el_piso": round(float(np.degrees(np.arccos(abs(wall_n @ n)))), 1)},
        "cajas": result,
    }  # fmt: skip


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
