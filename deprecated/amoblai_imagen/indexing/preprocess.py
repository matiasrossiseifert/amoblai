"""Preprocesamiento simétrico de imágenes de catálogo y de recortes.

Las fotos del catálogo son productos sobre fondo blanco. Para que la consulta
(un recorte de un ambiente) y los documentos del índice sean comparables, las
dos pasan por el mismo proceso: RGB, fondo blanco y padding a cuadrado. El
padding evita que el center-crop de los procesadores de CLIP/SigLIP/DINO le
corte los extremos a un mueble alargado (por ejemplo, los brazos de un sofá).
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from amoblai_imagen.config import PreprocessConfig
from amoblai_imagen.infra.images import to_rgb


def pad_to_square(
    img: Image.Image, color: tuple[int, int, int] = (255, 255, 255), margin: float = 0.0
) -> Image.Image:
    """Centra la imagen en un lienzo cuadrado de `color`, con `margin` (fracción del lado)."""
    w, h = img.size
    side = round(max(w, h) * (1.0 + 2.0 * margin))
    canvas = Image.new("RGB", (side, side), color)
    canvas.paste(to_rgb(img, color), ((side - w) // 2, (side - h) // 2))
    return canvas


def apply_mask(
    img: Image.Image, mask: np.ndarray, color: tuple[int, int, int] = (255, 255, 255)
) -> Image.Image:
    """Pinta de `color` todo lo que queda fuera de la máscara (fondo quitado)."""
    rgb = np.asarray(to_rgb(img)).copy()
    rgb[~mask.astype(bool)] = color
    return Image.fromarray(rgb)


def prepare_for_embedding(img: Image.Image, cfg: PreprocessConfig) -> Image.Image:
    img = to_rgb(img, cfg.background_color)
    if cfg.pad_to_square:
        img = pad_to_square(img, cfg.background_color, cfg.pad_margin)
    return img
