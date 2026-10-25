"""¿Sigue siendo el ambiente del usuario? La foto original contra la imagen generada.

SSIM fuera de las cajas de los muebles nuevos y SIFT + RANSAC entre las dos fotos: qué fracción
de los puntos de la original se reencuentra en la final con una homografía y cuánto se movieron.
Lo usan el paso generate (furnish.room_check: reintenta si el modelo de imagen cambió el cuarto)
y las métricas de la imagen (evaluation/image.py).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from PIL import Image

SIDE = 800  # ancho al que se comparan la foto original y la final


def preservation(before: Image.Image, after: Image.Image, boxes: list[Sequence[float]]) -> dict:
    """¿Es el mismo ambiente? SSIM fuera de las cajas (las cajas en coordenadas de `after`) y
    SIFT + RANSAC entre las dos fotos."""
    from skimage.feature import SIFT, match_descriptors
    from skimage.measure import ransac
    from skimage.metrics import structural_similarity
    from skimage.transform import ProjectiveTransform

    w = SIDE
    h = round(before.height * SIDE / before.width)
    b = np.asarray(before.convert("L").resize((w, h)), float) / 255
    a = np.asarray(after.convert("L").resize((w, h)), float) / 255
    ssim, smap = structural_similarity(b, a, data_range=1.0, full=True)
    sx, sy = w / after.width, h / after.height
    free = np.ones((h, w), bool)
    for x0, y0, x1, y1 in boxes:
        pad = 0.03 * w
        free[
            max(0, int(y0 * sy - pad)) : min(h, int(y1 * sy + pad)),
            max(0, int(x0 * sx - pad)) : min(w, int(x1 * sx + pad)),
        ] = False
    out: dict[str, Any] = {
        "ssim": round(float(ssim), 4),
        "ssim_fuera_de_los_muebles": round(float(smap[free].mean()), 4) if free.any() else None,
        "fraccion_fuera_de_los_muebles": round(float(free.mean()), 4),
    }
    sift_b, sift_a = SIFT(), SIFT()
    try:
        sift_b.detect_and_extract(b)
        sift_a.detect_and_extract(a)
    except RuntimeError:  # una imagen lisa: SIFT no encuentra puntos
        return {
            **out,
            "sift_puntos_original": 0,
            "sift_matches": 0,
            "sift_inliers": 0,
            "sift_reencontrados": 0.0,
        }
    matches = match_descriptors(
        sift_b.descriptors, sift_a.descriptors, max_ratio=0.8, cross_check=True
    )
    out["sift_puntos_original"] = len(sift_b.keypoints)
    out["sift_matches"] = len(matches)
    if len(matches) >= 8:
        src = sift_b.keypoints[matches[:, 0]][:, ::-1]  # (fila, col) -> (x, y)
        dst = sift_a.keypoints[matches[:, 1]][:, ::-1]
        _, inliers = ransac(
            (src, dst),
            ProjectiveTransform,
            min_samples=4,
            residual_threshold=3,
            max_trials=2000,
            rng=0,
        )
        n_in = int(inliers.sum()) if inliers is not None else 0
        out["sift_inliers"] = n_in
        out["sift_reencontrados"] = round(n_in / max(1, len(sift_b.keypoints)), 4)
        if n_in:
            moved = np.linalg.norm(dst[inliers] - src[inliers], axis=1)
            out["sift_desplazamiento_mediano"] = round(float(np.median(moved)) / w, 4)
    return out
