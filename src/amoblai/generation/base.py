"""Interfaz de los editores de imagen (generadores n.º 1 y n.º 2).

Contrato de `ImageEditor.edit`: la imagen devuelta tiene siempre el mismo tamaño
que la imagen base (`request.images[0]`). Cada proveedor se encarga de adaptar
el tamaño a lo que admite su API y de volver a la geometría original.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from PIL import Image

from amoblai.infra.usage import UsageRecord


@dataclass
class EditRequest:
    stage: str  # "generator1" | "generator2"
    prompt: str
    images: list[Image.Image]  # images[0] es la base; el resto, referencias (fotos de producto)
    image_labels: list[str]  # descripción de cada imagen, para el editor manual
    mask: np.ndarray | None = None  # True = zona editable (solo afecta a la base)
    cache_key: str = ""  # lo completa el servicio con caché

    @property
    def base(self) -> Image.Image:
        return self.images[0]


@dataclass
class EditResult:
    image: Image.Image
    usage: UsageRecord
    meta: dict[str, Any] = field(default_factory=dict)


class ImageEditor(Protocol):
    provider: str
    model: str

    def edit(self, request: EditRequest) -> EditResult: ...

    def estimate_usd(self, request: EditRequest) -> float: ...


class ManualStepPendingError(Exception):
    """El editor manual preparó la carpeta de trabajo y espera el resultado."""

    def __init__(self, workdir: Path, instructions: str):
        super().__init__(f"Paso manual pendiente en {workdir}")
        self.workdir = workdir
        self.instructions = instructions
