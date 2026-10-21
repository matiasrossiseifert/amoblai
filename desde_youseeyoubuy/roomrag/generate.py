"""The image model that puts the chosen products in the room: the room photo first, then the
products' photos, and the prompt the scene step wrote.

- ``manual`` (free): writes the images, the prompt and instructions to <run>/manual/, for a
  person to paste into ChatGPT or Gemini; the result dropped there as result.png (or .jpg) is
  picked up when the flow runs again.
- any other generator: ``kind: "package.module:Class"``, built as Class(params, cfg); it has
  the attributes and methods of `Generator`. YouSeeYouBuy plugs its image-model providers
  (OpenAI, Gemini through fal) this way.
"""

from __future__ import annotations

import importlib
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .config import Config


@dataclass
class Generated:
    image: Path | None  # None: not there yet
    model: str
    cost_usd: float
    cost_source: str  # "api" | "estimate" | "none"
    meta: dict = field(default_factory=dict)


class Generator(Protocol):
    name: str
    paid: bool
    account: str | None  # the API account it spends from (budget.accounts)

    def estimate_cost(self, images: list[Path]) -> float: ...

    def generate(self, prompt: str, images: list[Path], out: Path) -> Generated:
        """Writes out/final.png (or another name) and returns it."""
        ...


INSTRUCTIONS = """Pegá en ChatGPT o Gemini las imágenes de esta carpeta en orden (1_room primero)
y el texto de prompt.txt. Guardá la imagen que devuelva acá como result.png (o .jpg) y corré el
flujo de nuevo: sigue desde este paso.
"""


class ManualGenerator:
    paid = False
    account = None

    def __init__(self, params: dict, cfg: Config, name: str = "manual"):
        self.name = name

    def estimate_cost(self, images: list[Path]) -> float:
        return 0.0

    def generate(self, prompt: str, images: list[Path], out: Path) -> Generated:
        job = out / "manual"
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            if (job / f"result{ext}").exists():
                dst = out / f"final{ext}"
                shutil.copy(job / f"result{ext}", dst)
                return Generated(dst, "manual", 0.0, "none")
        job.mkdir(parents=True, exist_ok=True)
        for i, src in enumerate(images, 1):
            name = "room" if i == 1 else f"product_{i - 1}"
            shutil.copy(src, job / f"{i}_{name}{Path(src).suffix.lower()}")
        (job / "prompt.txt").write_text(prompt + "\n")
        (job / "LEEME.txt").write_text(INSTRUCTIONS)
        return Generated(None, "manual", 0.0, "none", {"job": str(job)})


def load_attr(spec: str):
    """'package.module:name' -> that object."""
    module, _, attr = spec.partition(":")
    if not attr:
        raise ValueError(f"{spec!r}: expected 'package.module:name'")
    return getattr(importlib.import_module(module), attr)


def get_generator(name: str, cfg: Config) -> Generator:
    params = dict(cfg.furnish.generators.get(name, {}))
    if not params:
        raise ValueError(
            f"furnish: no generator {name!r} in furnish.generators; "
            f"known: {sorted(cfg.furnish.generators)}"
        )
    kind = params.pop("kind", name)
    cls = ManualGenerator if kind == "manual" else load_attr(kind)
    return cls(params, cfg, name)
