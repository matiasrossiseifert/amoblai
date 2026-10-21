"""Utilidades de imágenes compartidas por todo el pipeline."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def load_image(path: Path | str) -> Image.Image:
    """Abre una imagen aplicando la rotación EXIF y la convierte a RGB."""
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        return to_rgb(img)


def to_rgb(img: Image.Image, background: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Convierte a RGB; la transparencia se aplana sobre `background`."""
    if img.mode == "RGB":
        return img.copy()
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, background)
        canvas.paste(rgba, mask=rgba.getchannel("A"))
        return canvas
    return img.convert("RGB")


def image_digest(img: Image.Image) -> str:
    """Hash del contenido en píxeles (no depende del formato del archivo)."""
    h = hashlib.sha256()
    h.update(f"{img.mode}{img.size}".encode())
    h.update(img.tobytes())
    return h.hexdigest()


def to_png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def from_bytes(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as img:
        img.load()
        return img.copy()


def resize_max_side(img: Image.Image, max_side: int, multiple: int = 1) -> Image.Image:
    """Escala para que el lado mayor sea `max_side` (sin agrandar) y redondea a `multiple`."""
    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    nw = max(multiple, round(w * scale / multiple) * multiple)
    nh = max(multiple, round(h * scale / multiple) * multiple)
    if (nw, nh) == (w, h):
        return img.copy()
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def save_image(img: Image.Image, path: Path, quality: int = 90) -> Path:
    """Guarda PNG o JPEG según la extensión (JPEG para miniaturas livianas en git)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() in (".jpg", ".jpeg"):
        to_rgb(img).save(path, quality=quality, optimize=True)
    else:
        img.save(path)
    return path


def thumbnail(img: Image.Image, max_side: int = 384) -> Image.Image:
    out = img.copy()
    out.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return out


def mask_to_image(mask: np.ndarray) -> Image.Image:
    return Image.fromarray((mask.astype(np.uint8) * 255), mode="L")


def image_to_mask(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L")) > 127
