"""Versioned prompt templates (`prompts/*.md`): the catalog descriptions, the furnishing steps.

A template file starts with a small front matter block:

    ---
    version: search_query_v2
    ---
    <prompt text with {placeholders}>

`load_prompt` finds a template by path (absolute, or relative to the config's root) or by the
name of one of this package's own templates (src/amoblai/prompts/).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

PROMPTS = Path(__file__).parent


@dataclass
class PromptTemplate:
    path: Path
    version: str
    text: str

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:12]

    @classmethod
    def load(cls, path: str | Path) -> PromptTemplate:
        p = Path(path)
        raw = p.read_text()
        meta: dict = {}
        body = raw
        if raw.startswith("---"):
            _, fm, body = raw.split("---", 2)
            meta = yaml.safe_load(fm) or {}
        return cls(p, str(meta.get("version", p.stem)), body.strip() + "\n")

    def fill(self, **values) -> str:
        """The text with these {placeholders} replaced; any other brace stays as it is (the
        prompts show JSON examples)."""
        text = self.text
        for k, v in values.items():
            text = text.replace("{" + k + "}", str(v))
        return text.strip()

    def render(self, product: dict) -> str:
        """A product's fields into the description prompt: {name}, {category}, {colors},
        {materials}, {width_cm}, {depth_cm}, {height_cm}."""
        dims = product.get("dimensions_cm") or {}

        def join(xs) -> str:
            return ", ".join(x for x in xs if x) if xs else "as in the reference photos"

        return self.text.format(
            name=product.get("name", "the product"),
            category=str(product.get("category", "furniture")).replace("_", " "),
            colors=join(product.get("colors")),
            materials=join(product.get("materials")),
            width_cm=round(float(dims.get("width") or 0)),
            depth_cm=round(float(dims.get("depth") or 0)),
            height_cm=round(float(dims.get("height") or 0)),
        ).strip()


def load_prompt(path: str | Path, root: str | Path = ".") -> PromptTemplate:
    p = Path(path)
    for candidate in [p] if p.is_absolute() else [Path(root) / p, PROMPTS / p]:
        if candidate.is_file():
            return PromptTemplate.load(candidate)
    raise FileNotFoundError(f"prompt {path!r}: not under {root} nor in {PROMPTS}")
