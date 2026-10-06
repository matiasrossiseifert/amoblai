"""Selección de dispositivo: GPU (fp16) si hay CUDA, si no CPU (fp32)."""

from __future__ import annotations

import functools
import logging

log = logging.getLogger(__name__)


@functools.cache
def resolve_device(preference: str = "auto") -> str:
    import torch

    if preference != "auto":
        return preference
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    log.info("Sin GPU disponible: se usa CPU")
    return "cpu"


def default_dtype(device: str):
    import torch

    return torch.float16 if device.startswith("cuda") else torch.float32
