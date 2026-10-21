"""Embeddings de imagen con modelos locales de Hugging Face (CLIP, SigLIP 2, DINOv2, DINOv3).

- CLIP y SigLIP: `get_image_features` (embedding proyectado al espacio imagen-texto).
- DINOv2 y DINOv3: `pooler_output`, el token CLS normalizado (embedding autosupervisado,
  más sensible a forma y textura que a semántica).

Las imágenes llegan ya cuadradas (ver indexing/preprocess.py); acá solo se
escalan al tamaño de entrada del modelo, sin center-crop.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import numpy as np
from PIL import Image

from amoblai_imagen.embeddings.base import l2_normalize
from amoblai_imagen.infra.device import default_dtype, resolve_device

log = logging.getLogger(__name__)

_PROJECTED_TYPES = {"clip", "siglip", "siglip2"}


class HFImageEmbedder:
    def __init__(self, name: str, model_id: str, device: str = "auto", batch_size: int = 16):
        import torch
        from transformers import AutoConfig, AutoImageProcessor, AutoModel

        self.name = name
        self.model_id = model_id
        self.batch_size = batch_size
        self.device = resolve_device(device)
        self.dtype = default_dtype(self.device)
        config = AutoConfig.from_pretrained(model_id)
        self.model_type = config.model_type
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id, dtype=self.dtype).to(self.device).eval()
        self.input_size = _input_size(self.processor)
        self._torch = torch
        log.info(
            "Embedder %s (%s) en %s, entrada %dpx", name, model_id, self.device, self.input_size
        )

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        if not images:
            return np.zeros((0, 0), dtype=np.float32)
        chunks = []
        for start in range(0, len(images), self.batch_size):
            batch = [
                img.convert("RGB").resize(
                    (self.input_size, self.input_size), Image.Resampling.BICUBIC
                )
                for img in images[start : start + self.batch_size]
            ]
            chunks.append(self._embed_batch(batch))
        return l2_normalize(np.concatenate(chunks, axis=0))

    def _embed_batch(self, batch: list[Image.Image]) -> np.ndarray:
        inputs = self.processor(
            images=batch, return_tensors="pt", do_resize=False, do_center_crop=False
        )
        pixel_values = inputs["pixel_values"].to(self.device, dtype=self.dtype)
        with self._torch.inference_mode():
            if self.model_type in _PROJECTED_TYPES:
                out = self.model.get_image_features(pixel_values=pixel_values)
            else:
                out = self.model(pixel_values=pixel_values)
            feats = out if isinstance(out, self._torch.Tensor) else out.pooler_output
        return feats.float().cpu().numpy()


def _input_size(processor) -> int:
    """Lado de entrada del modelo según su procesador (crop_size o size)."""
    for attr in ("crop_size", "size"):
        size = getattr(processor, attr, None)
        if size is None:
            continue
        get = size.get if isinstance(size, dict) else lambda k, s=size: getattr(s, k, None)
        for key in ("height", "shortest_edge"):
            value = get(key)
            if value:
                return int(value)
    return 224
