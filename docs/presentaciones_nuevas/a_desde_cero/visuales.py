"""Dos figuras que se calculan acá, gratis y en local, con el mismo método que usa el repo
(src/amoblai/furnish/room.py): los puntos SIFT reencontrados entre la foto original y la generada,
y la máscara de lo que mide el SSIM (todo lo que queda fuera de las cajas de los muebles)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from componentes import CACHE, REPO

SIDE = 800


def _key(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def sift_pair(before: Path, after: Path, gap: int = 24) -> tuple[Path, dict]:
    """Original y generada lado a lado, con una línea por cada punto SIFT que RANSAC acepta."""
    before, after = REPO / before, REPO / after
    out = CACHE / f"sift_{_key(before, after, before.stat().st_mtime, after.stat().st_mtime)}.png"
    info_f = out.with_suffix(".txt")
    if out.exists() and info_f.exists():
        n_in, n_kp = (int(x) for x in info_f.read_text().split())
        return out, {"inliers": n_in, "puntos": n_kp}
    from skimage.feature import SIFT, match_descriptors
    from skimage.measure import ransac
    from skimage.transform import ProjectiveTransform

    bi, ai = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    w = SIDE
    h = round(bi.height * SIDE / bi.width)
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
    canvas = Image.new("RGB", (2 * w + gap, h), (251, 248, 242))
    canvas.paste(bi, (0, 0))
    canvas.paste(ai, (w + gap, 0))
    # se aclaran las fotos para que se vean las líneas
    veil = Image.new("RGBA", canvas.size, (251, 248, 242, 70))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), veil)
    d = ImageDraw.Draw(canvas)
    for (x0, y0), (x1, y1) in zip(src[inl], dst[inl], strict=True):
        d.line([(x0, y0), (x1 + w + gap, y1)], fill=(176, 80, 42, 200), width=2)
        for x, y in ((x0, y0), (x1 + w + gap, y1)):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 255, 255, 255), fill=(176, 80, 42, 255), width=1)
    canvas.convert("RGB").save(out)
    info_f.write_text(f"{int(inl.sum())} {len(sb.keypoints)}")
    return out, {"inliers": int(inl.sum()), "puntos": len(sb.keypoints)}


def ssim_mask(after: Path, boxes: list, pad: float = 0.03) -> Path:
    """La imagen generada con las cajas de los muebles tapadas: el SSIM se mide en el resto."""
    after = REPO / after
    out = CACHE / f"mask_{_key(after, after.stat().st_mtime, boxes, pad)}.png"
    if out.exists():
        return out
    im = Image.open(after).convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    p = pad * im.width
    for x0, y0, x1, y1 in boxes:
        r = [max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p)]
        d.rectangle(r, fill=(43, 33, 27, 165))
        for k in range(int(r[0]) - int(r[3] - r[1]), int(r[2]), 18):  # rayado
            d.line([(k, r[3]), (k + (r[3] - r[1]), r[1])], fill=(217, 130, 94, 150), width=2)
        d.rectangle(r, outline=(217, 130, 94, 255), width=3)
    # el rayado no se sale de cada caja: se recorta con una máscara
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in boxes:
        md.rectangle([max(0, x0 - p), max(0, y0 - p), min(im.width, x1 + p), min(im.height, y1 + p)], fill=255)
    ov.putalpha(Image.fromarray(np.minimum(np.asarray(ov.split()[3]), np.asarray(mask))))
    Image.alpha_composite(im, ov).convert("RGB").save(out)
    return out
