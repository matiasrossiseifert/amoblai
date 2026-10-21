"""Tests con modelos reales de Hugging Face (lentos, requieren red): `uv run pytest -m models`."""

import os

import numpy as np
import pytest
from PIL import Image, ImageDraw

from amoblai_imagen.config import BackgroundConfig, DetectionConfig, EmbeddingConfig, load_env
from amoblai_imagen.embeddings.registry import build_embedder
from amoblai_imagen.vision.background import build_background_remover
from amoblai_imagen.vision.boxes import Box
from amoblai_imagen.vision.detection import build_detector

pytestmark = pytest.mark.models


@pytest.mark.parametrize("name", ["dinov3", "dinov2", "clip", "siglip2"])
def test_embedders_return_normalized_vectors(name):
    if name == "dinov3":
        load_env()
        if not os.environ.get("HF_TOKEN"):
            pytest.skip("DINOv3 es gated: requiere HF_TOKEN")
    emb = build_embedder(EmbeddingConfig(name=name, batch_size=2), device="auto")
    imgs = [Image.new("RGB", (64, 64), c) for c in ("red", "blue", "green")]
    vecs = emb.embed_images(imgs)
    assert vecs.shape[0] == 3
    assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-4)


@pytest.mark.parametrize("provider", ["grounding_dino", "owlv2"])
def test_detectors_run(provider):
    det = build_detector(DetectionConfig(provider=provider), {"chair": "chair", "table": "table"})
    out = det.detect(Image.new("RGB", (320, 240), "white"))
    assert isinstance(out, list)


def test_sam_mask_inside_box():
    img = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(img).ellipse([60, 60, 140, 140], fill="black")
    remover = build_background_remover(BackgroundConfig(method="sam"))
    (mask,) = remover.masks(img, [Box(50, 50, 150, 150)])
    assert mask is not None and mask[100, 100] and not mask[10, 10]
