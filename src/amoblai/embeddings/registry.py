"""Presets de modelos de embeddings y construcción a partir de la config."""

from __future__ import annotations

from amoblai.config import EmbeddingConfig
from amoblai.embeddings.base import Embedder

# Variantes "base" (~86-100M parámetros en la torre de imagen): entran cómodas en 8 GB de VRAM.
PRESETS: dict[str, str] = {
    "dinov2": "facebook/dinov2-base",
    # Gated en Hugging Face: requiere aceptar la licencia y HF_TOKEN en .env.
    "dinov3": "facebook/dinov3-vitb16-pretrain-lvd1689m",
    "clip": "openai/clip-vit-base-patch32",
    "siglip2": "google/siglip2-base-patch16-224",
}


def model_id_for(cfg: EmbeddingConfig) -> str:
    if cfg.model_id:
        return cfg.model_id
    if cfg.name not in PRESETS:
        raise ValueError(f"Embedder desconocido {cfg.name!r}; presets: {sorted(PRESETS)}")
    return PRESETS[cfg.name]


def build_embedder(cfg: EmbeddingConfig, device: str = "auto") -> Embedder:
    from amoblai.embeddings.hf import HFImageEmbedder

    return HFImageEmbedder(cfg.name, model_id_for(cfg), device=device, batch_size=cfg.batch_size)
