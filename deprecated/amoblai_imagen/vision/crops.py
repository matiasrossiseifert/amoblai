"""Recorte de cada mueble detectado para usarlo como consulta del retriever.

Pasos: recorte con margen → (opcional) fondo blanco fuera de la máscara →
padding a cuadrado sobre blanco, igual que las imágenes del catálogo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from amoblai_imagen.config import BackgroundConfig, PreprocessConfig
from amoblai_imagen.indexing.preprocess import apply_mask, prepare_for_embedding
from amoblai_imagen.vision.background import BackgroundRemover
from amoblai_imagen.vision.detection import Detection


@dataclass
class QueryCrop:
    index: int
    detection: Detection
    raw: Image.Image  # recorte tal cual sale del ambiente
    query: Image.Image  # recorte preprocesado que se embebe
    background_removed: bool


def make_crop(
    image: Image.Image,
    detection: Detection,
    mask: np.ndarray | None,
    bg_cfg: BackgroundConfig,
    pre_cfg: PreprocessConfig,
    index: int = 0,
) -> QueryCrop:
    w, h = image.size
    x0, y0, x1, y1 = detection.box.expand(bg_cfg.crop_margin, w, h).to_int()
    raw = image.crop((x0, y0, x1, y1))
    source = apply_mask(image, mask, pre_cfg.background_color) if mask is not None else image
    query = prepare_for_embedding(source.crop((x0, y0, x1, y1)), pre_cfg)
    return QueryCrop(index, detection, raw, query, background_removed=mask is not None)


def make_crops(
    image: Image.Image,
    detections: list[Detection],
    remover: BackgroundRemover,
    bg_cfg: BackgroundConfig,
    pre_cfg: PreprocessConfig,
) -> list[QueryCrop]:
    """Recortes de todas las detecciones; las categorías en `skip_categories` conservan el fondo."""
    to_mask = [i for i, d in enumerate(detections) if d.category not in bg_cfg.skip_categories]
    masks: list[np.ndarray | None] = [None] * len(detections)
    for i, m in zip(
        to_mask, remover.masks(image, [detections[i].box for i in to_mask]), strict=True
    ):
        masks[i] = m
    return [
        make_crop(image, det, masks[i], bg_cfg, pre_cfg, index=i)
        for i, det in enumerate(detections)
    ]
