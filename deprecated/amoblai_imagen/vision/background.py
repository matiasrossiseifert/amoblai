"""Eliminación del fondo de los recortes.

El catálogo son fotos de producto sobre blanco; los recortes salen de un
ambiente con piso, paredes y otros muebles. Quitarles el fondo achica la brecha
de dominio entre consulta y documentos (es una de las ablaciones).

- `sam` (default): SAM con la caja del detector como prompt. Un recorte de un
  living suele tener varios objetos destacados (almohadones, lámparas, otra
  silla) y un modelo de "objeto saliente" puede elegir el equivocado; con la
  caja como prompt la segmentación apunta al mueble detectado.
- `rembg`: segmentación de objeto saliente sobre el recorte (alternativa, extra `rembg`).
- `none`: el recorte conserva su contexto.
"""

from __future__ import annotations

import logging
from typing import Protocol

import numpy as np
from PIL import Image
from scipy import ndimage

from amoblai_imagen.config import BackgroundConfig, stable_hash
from amoblai_imagen.infra.cache import ArtifactCache
from amoblai_imagen.infra.device import resolve_device
from amoblai_imagen.infra.images import image_digest
from amoblai_imagen.vision.boxes import Box

log = logging.getLogger(__name__)


class BackgroundRemover(Protocol):
    def masks(self, image: Image.Image, boxes: list[Box]) -> list[np.ndarray | None]:
        """Una máscara booleana (H, W) del tamaño de la imagen por caja, o None si no aplica."""
        ...


class NoBackgroundRemoval:
    def masks(self, image: Image.Image, boxes: list[Box]) -> list[np.ndarray | None]:
        return [None for _ in boxes]


def clean_mask(mask: np.ndarray, box: Box, margin: float = 0.02) -> np.ndarray:
    """Restringe la máscara a la caja (con margen), rellena huecos y deja la componente mayor."""
    h, w = mask.shape
    x0, y0, x1, y1 = box.expand(margin, w, h).to_int()
    limited = np.zeros_like(mask, dtype=bool)
    limited[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    labels, n = ndimage.label(limited)
    if n > 1:
        sizes = ndimage.sum(limited, labels, range(1, n + 1))
        limited = labels == (int(np.argmax(sizes)) + 1)
    return ndimage.binary_fill_holes(limited)


class SamBoxRemover:
    def __init__(self, model_id: str, device: str = "auto"):
        import torch
        from transformers import SamModel, SamProcessor

        self.device = resolve_device(device)
        self.processor = SamProcessor.from_pretrained(model_id)
        self.model = SamModel.from_pretrained(model_id).to(self.device).eval()
        self._torch = torch

    def masks(self, image: Image.Image, boxes: list[Box]) -> list[np.ndarray | None]:
        if not boxes:
            return []
        inputs = self.processor(
            images=image, input_boxes=[[b.as_list() for b in boxes]], return_tensors="pt"
        ).to(self.device)
        with self._torch.inference_mode():
            outputs = self.model(**inputs, multimask_output=True)
        masks = self.processor.image_processor.post_process_masks(
            outputs.pred_masks.cpu(),
            inputs["original_sizes"].cpu(),
            inputs["reshaped_input_sizes"].cpu(),
        )[0]  # (n_cajas, 3, H, W)
        scores = outputs.iou_scores[0].cpu()  # (n_cajas, 3)
        result: list[np.ndarray | None] = []
        for i, box in enumerate(boxes):
            best = int(scores[i].argmax())
            result.append(clean_mask(masks[i, best].numpy().astype(bool), box))
        return result


class RembgRemover:
    def __init__(self, model_name: str):
        try:
            from rembg import new_session, remove
        except ImportError as exc:  # pragma: no cover
            raise ImportError("background.method=rembg requiere `uv sync --extra rembg`") from exc
        self._remove = remove
        self.session = new_session(model_name)

    def masks(self, image: Image.Image, boxes: list[Box]) -> list[np.ndarray | None]:
        w, h = image.size
        result: list[np.ndarray | None] = []
        for box in boxes:
            x0, y0, x1, y1 = box.clip(w, h).to_int()
            crop_mask = self._remove(
                image.crop((x0, y0, x1, y1)), session=self.session, only_mask=True
            )
            full = np.zeros((h, w), dtype=bool)
            full[y0:y1, x0:x1] = np.asarray(crop_mask.convert("L")) > 127
            result.append(clean_mask(full, box))
        return result


class CachedRemover:
    def __init__(self, remover: BackgroundRemover, cfg: BackgroundConfig, cache: ArtifactCache):
        self.remover = remover
        self.cache = cache
        self.config_key = stable_hash(
            {"method": cfg.method, "sam": cfg.sam_model_id, "rembg": cfg.rembg_model}
        )

    def masks(self, image: Image.Image, boxes: list[Box]) -> list[np.ndarray | None]:
        if not boxes:
            return []
        key = self.cache.key(
            {
                "image": image_digest(image),
                "boxes": [b.as_list() for b in boxes],
                "cfg": self.config_key,
            }
        )
        cached = self.cache.get_array(key, "masks.npz")
        if cached is not None:
            h, w = image.size[1], image.size[0]
            bits = np.unpackbits(cached["packed"], axis=1)[:, : h * w]
            return [row.reshape(h, w).astype(bool) for row in bits]
        masks = self.remover.masks(image, boxes)
        if all(m is not None for m in masks):
            stacked = np.stack([m.reshape(-1) for m in masks if m is not None])
            self.cache.put_array(key, {"packed": np.packbits(stacked, axis=1)}, "masks.npz")
        return masks


def build_background_remover(
    cfg: BackgroundConfig, device: str = "auto", cache: ArtifactCache | None = None
) -> BackgroundRemover:
    remover: BackgroundRemover
    if cfg.method == "none":
        return NoBackgroundRemoval()
    if cfg.method == "sam":
        remover = SamBoxRemover(cfg.sam_model_id, device)
    elif cfg.method == "rembg":
        remover = RembgRemover(cfg.rembg_model)
    else:  # pragma: no cover
        raise ValueError(cfg.method)
    return CachedRemover(remover, cfg, cache) if cache is not None else remover
