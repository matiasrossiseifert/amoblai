"""Imágenes embebidas (JPEG en base64, con caché) y dos figuras que se calculan acá, gratis y en
local, con el mismo método que usa el repo (src/amoblai/furnish/room.py): los puntos SIFT
reencontrados entre la foto original y la generada, y la máscara de lo que mide el SSIM."""

from __future__ import annotations

import base64
import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CACHE = HERE / "_trabajo" / "cache" / "img"
CACHE.mkdir(parents=True, exist_ok=True)

STATS = {"bytes": 0, "n": 0}


def _abs(path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO / path


def uri(path, w: int, h: int | None = None, q: int = 78, fit: str = "cover", bg=(255, 255, 255)) -> str:
    """fit='cover' recorta al centro; 'contain' encaja sobre fondo; sin h, solo ancho."""
    path = _abs(path)
    key = hashlib.sha1(f"{path}|{path.stat().st_mtime}|{w}|{h}|{q}|{fit}|{bg}".encode()).hexdigest()[:16]
    cached = CACHE / f"{key}.b64"
    if cached.exists():
        b64 = cached.read_text()
    else:
        im = Image.open(path).convert("RGB")
        if h is None:
            r = w / im.width
            im = im.resize((w, max(1, round(im.height * r))), Image.LANCZOS)
        elif fit == "cover":
            r = max(w / im.width, h / im.height)
            im = im.resize((max(w, round(im.width * r)), max(h, round(im.height * r))), Image.LANCZOS)
            x0, y0 = (im.width - w) // 2, (im.height - h) // 2
            im = im.crop((x0, y0, x0 + w, y0 + h))
        else:
            r = min(w / im.width, h / im.height)
            im2 = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
            im = Image.new("RGB", (w, h), bg)
            im.paste(im2, ((w - im2.width) // 2, (h - im2.height) // 2))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        cached.write_text(b64)
    STATS["bytes"] += len(b64)
    STATS["n"] += 1
    return "data:image/jpeg;base64," + b64


def crop(path, box, w: int, h: int, q: int = 80, pad: float = 0.04) -> str:
    """Un recorte (x0, y0, x1, y1) en píxeles, encajado en w × h sobre blanco."""
    path = _abs(path)
    key = hashlib.sha1(f"crop|{path}|{path.stat().st_mtime}|{box}|{w}|{h}|{q}".encode()).hexdigest()[:16]
    cached = CACHE / f"{key}.b64"
    if cached.exists():
        b64 = cached.read_text()
    else:
        im = Image.open(path).convert("RGB")
        x0, y0, x1, y1 = box
        dx, dy = (x1 - x0) * pad, (y1 - y0) * pad
        im = im.crop((max(0, x0 - dx), max(0, y0 - dy), min(im.width, x1 + dx), min(im.height, y1 + dy)))
        r = min(w / im.width, h / im.height)
        im2 = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
        im = Image.new("RGB", (w, h), (255, 255, 255))
        im.paste(im2, ((w - im2.width) // 2, (h - im2.height) // 2))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        cached.write_text(b64)
    STATS["bytes"] += len(b64)
    STATS["n"] += 1
    return "data:image/jpeg;base64," + b64


def _key(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


INK = (19, 32, 44)
COB = (36, 83, 214)


def sift_pair(before, after, side: int = 800, gap: int = 24):
    """Original y generada lado a lado, con una línea por cada punto SIFT que RANSAC acepta."""
    before, after = _abs(before), _abs(after)
    out = CACHE / f"sift_{_key(before, after, before.stat().st_mtime, after.stat().st_mtime, 'a2')}.png"
    info_f = out.with_suffix(".txt")
    if out.exists() and info_f.exists():
        n_in, n_kp = (int(x) for x in info_f.read_text().split())
        return out, {"inliers": n_in, "puntos": n_kp}
    from skimage.feature import SIFT, match_descriptors
    from skimage.measure import ransac
    from skimage.transform import ProjectiveTransform

    bi, ai = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    w = side
    h = round(bi.height * side / bi.width)
    bi, ai = bi.resize((w, h)), ai.resize((w, h))
    b = np.asarray(bi.convert("L"), float) / 255
    a = np.asarray(ai.convert("L"), float) / 255
    sb, sa = SIFT(), SIFT()
    sb.detect_and_extract(b)
    sa.detect_and_extract(a)
    m = match_descriptors(sb.descriptors, sa.descriptors, max_ratio=0.8, cross_check=True)
    src = sb.keypoints[m[:, 0]][:, ::-1]
    dst = sa.keypoints[m[:, 1]][:, ::-1]
    _, inl = ransac((src, dst), ProjectiveTransform, min_samples=4, residual_threshold=3,
                    max_trials=2000, rng=0)
    inl = inl if inl is not None else np.zeros(len(src), bool)
    canvas = Image.new("RGB", (2 * w + gap, h), (244, 244, 240))
    canvas.paste(bi, (0, 0))
    canvas.paste(ai, (w + gap, 0))
    veil = Image.new("RGBA", canvas.size, (244, 244, 240, 90))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), veil)
    d = ImageDraw.Draw(canvas)
    for (x0, y0), (x1, y1) in zip(src[inl], dst[inl], strict=True):
        d.line([(x0, y0), (x1 + w + gap, y1)], fill=COB + (190,), width=2)
        for x, y in ((x0, y0), (x1 + w + gap, y1)):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 255, 255, 255), fill=COB + (255,), width=1)
    canvas.convert("RGB").save(out)
    info_f.write_text(f"{int(inl.sum())} {len(sb.keypoints)}")
    return out, {"inliers": int(inl.sum()), "puntos": len(sb.keypoints)}


def ssim_mask(after, boxes: list, pad: float = 0.03) -> Path:
    """La imagen generada con las cajas de los muebles tapadas: el SSIM se mide en el resto."""
    after = _abs(after)
    out = CACHE / f"mask_{_key(after, after.stat().st_mtime, boxes, pad, 'a2')}.png"
    if out.exists():
        return out
    im = Image.open(after).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    p = pad * im.width
    rects = []
    for x0, y0, x1, y1 in boxes:
        r = [max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p)]
        rects.append(r)
        d.rectangle(r, fill=INK + (150,))
        for k in range(int(r[0]) - int(r[3] - r[1]), int(r[2]), 16):
            d.line([(k, r[3]), (k + (r[3] - r[1]), r[1])], fill=(255, 255, 255, 120), width=2)
        d.rectangle(r, outline=(255, 255, 255, 255), width=3)
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for r in rects:
        md.rectangle(r, fill=255)
    ov.putalpha(Image.fromarray(np.minimum(np.asarray(ov.split()[3]), np.asarray(mask))))
    Image.alpha_composite(im, ov).convert("RGB").save(out)
    return out
