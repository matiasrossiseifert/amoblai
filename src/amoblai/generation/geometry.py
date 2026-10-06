"""Geometría de la generación: tamaños admitidos, máscaras y compositing.

- Los modelos de imagen admiten ciertos tamaños. `fit_size` elige el tamaño de
  salida y `FitTransform` lleva la imagen a ese tamaño y la devuelve a la
  geometría original, para que las cajas detectadas en la imagen 1 sigan
  coincidiendo con la foto original.
- Las máscaras marcan dónde puede editar el generador n.º 2 (cajas dilatadas).
- `composite` (postprocesamiento opcional) pega solo lo de adentro de la
  máscara sobre la base, con borde suavizado: garantiza que el resto del
  ambiente quede intacto.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageFilter

from amoblai.vision.boxes import Box

FIXED_SIZES = [(1024, 1024), (1536, 1024), (1024, 1536)]
GEMINI_ASPECTS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]


def free_size(width: int, height: int, max_side: int = 1536, multiple: int = 16) -> tuple[int, int]:
    """Tamaño múltiplo de `multiple` con el mismo aspecto (gpt-image-2 admite tamaños libres).

    Limita la proporción a 3:1 como pide la API.
    """
    ratio = min(max(width / height, 1 / 3), 3.0)
    if ratio >= 1:
        w, h = max_side, max_side / ratio
    else:
        w, h = max_side * ratio, max_side
    return (
        max(multiple, round(w / multiple) * multiple),
        max(multiple, round(h / multiple) * multiple),
    )


def closest_fixed_size(
    width: int, height: int, sizes: list[tuple[int, int]] = FIXED_SIZES
) -> tuple[int, int]:
    ratio = width / height
    return min(sizes, key=lambda s: abs(np.log(s[0] / s[1]) - np.log(ratio)))


def closest_aspect(width: int, height: int, aspects: list[str] = GEMINI_ASPECTS) -> str:
    ratio = width / height

    def value(a: str) -> float:
        w, h = a.split(":")
        return int(w) / int(h)

    return min(aspects, key=lambda a: abs(np.log(value(a)) - np.log(ratio)))


@dataclass(frozen=True)
class FitTransform:
    """Letterbox: escala para entrar en `target` y rellena el resto (bandas)."""

    source: tuple[int, int]
    target: tuple[int, int]

    @property
    def scale(self) -> float:
        return min(self.target[0] / self.source[0], self.target[1] / self.source[1])

    @property
    def inner(self) -> tuple[int, int, int, int]:
        """Rectángulo (x0, y0, x1, y1) del contenido dentro del lienzo destino."""
        w = round(self.source[0] * self.scale)
        h = round(self.source[1] * self.scale)
        x0 = (self.target[0] - w) // 2
        y0 = (self.target[1] - h) // 2
        return (x0, y0, x0 + w, y0 + h)

    def apply(self, img: Image.Image, fill: int | tuple[int, ...] = (255, 255, 255)) -> Image.Image:
        x0, y0, x1, y1 = self.inner
        canvas = Image.new(img.mode, self.target, fill if img.mode != "L" else 0)
        canvas.paste(img.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), (x0, y0))
        return canvas

    def invert(self, img: Image.Image) -> Image.Image:
        """Recorta las bandas de una salida del tamaño `target` y vuelve a `source`."""
        if img.size != self.target:
            img = img.resize(self.target, Image.Resampling.LANCZOS)
        return img.crop(self.inner).resize(self.source, Image.Resampling.LANCZOS)


def boxes_mask(size: tuple[int, int], boxes: list[Box], dilation: float = 0.0) -> np.ndarray:
    """Máscara booleana (H, W) con las cajas dilatadas `dilation` veces su lado mayor."""
    w, h = size
    mask = np.zeros((h, w), dtype=bool)
    for box in boxes:
        x0, y0, x1, y1 = box.expand(dilation, w, h).to_int()
        mask[y0:y1, x0:x1] = True
    return mask


def openai_mask(mask: np.ndarray) -> Image.Image:
    """Máscara en el formato de la API de OpenAI: RGBA, transparente donde se edita."""
    h, w = mask.shape
    rgba = np.full((h, w, 4), 255, dtype=np.uint8)
    rgba[mask, 3] = 0
    return Image.fromarray(rgba, mode="RGBA")


def composite(
    base: Image.Image, generated: Image.Image, mask: np.ndarray, feather_px: int = 12
) -> Image.Image:
    """Toma `generated` dentro de la máscara y `base` afuera, con transición suave."""
    if generated.size != base.size:
        generated = generated.resize(base.size, Image.Resampling.LANCZOS)
    alpha = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")
    if feather_px > 0:
        alpha = alpha.filter(ImageFilter.GaussianBlur(feather_px))
    return Image.composite(generated.convert("RGB"), base.convert("RGB"), alpha)
