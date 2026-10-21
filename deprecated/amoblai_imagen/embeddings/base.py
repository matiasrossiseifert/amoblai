"""Interfaz de los modelos de embeddings de imagen."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import numpy as np
from PIL import Image


@runtime_checkable
class Embedder(Protocol):
    name: str  # alias corto, p. ej. "dinov2"
    model_id: str  # id en Hugging Face

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """Devuelve un array (n, d) float32 con filas L2-normalizadas."""
        ...


def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    return (x / np.maximum(norms, eps)).astype(np.float32)
