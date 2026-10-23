"""Each product's description: the text the search compares a need against.

- ``written`` (free): descriptions written ahead, read from JSON-lines files, one
  {"id", "text", "by", "prompt"} a line. Ours (datos/catalogo/descripciones.jsonl) were written
  by subagents in Claude Code, looking at each product's photo with prompts/describe_product_v3.md
  (the first furniture with v2, the same format), not through the API.
- ``fields`` (free): the product's own fields (name, type, colors, materials, description): the
  seller's words, uneven from one store to the next; a baseline.
- ``anthropic_vision`` / ``openai_chat_vision``: an LLM (llm.py) looks at the product's photos
  and writes the description with that same prompt, in one fixed format for every store.

A product is described once; index.py keeps the description in the cache.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from amoblai.catalog.loader import Product
from amoblai.config import Config
from amoblai.furnish.llm import LLM, image_block, make_llm, text_block
from amoblai.prompts import PromptTemplate, load_prompt


@dataclass
class Description:
    text: str
    model: str
    cost_usd: float
    cost_source: str  # "api" | "estimate" | "none"
    # "status": "completed", or why the model stopped early (then the text may be cut short).
    meta: dict = field(default_factory=dict)


class Describer(Protocol):
    name: str
    paid: bool
    account: str | None  # the API account it spends from (budget.accounts); None when free

    def key(self) -> dict:
        """Everything besides the product that changes the description."""
        ...

    def estimate_cost(self, product: Product) -> float: ...

    def describe(self, product: Product) -> Description: ...


class FieldsDescriber:
    paid = False
    account = None

    def __init__(self, name: str = "fields"):
        self.name = name

    def key(self) -> dict:
        return {"kind": "fields", "version": 1}

    def estimate_cost(self, product: Product) -> float:
        return 0.0

    def describe(self, product: Product) -> Description:
        i = product.info
        lines = [f"Type: {i['category'].replace('_', ' ')}", f"Name: {i['name']}"]
        if i.get("colors"):
            lines.append("Colors: " + ", ".join(i["colors"]))
        if i.get("materials"):
            lines.append("Materials: " + ", ".join(i["materials"]))
        if i.get("description"):
            lines.append(i["description"])
        return Description("\n".join(lines) + "\n", "fields", 0.0, "none", {"status": "completed"})


class WrittenDescriber:
    """In one file or several (one per source). A product missing from them gets no description
    (it is left out of the index, and said)."""

    paid = False
    account = None

    def __init__(self, paths: Path | list[Path], name: str = "written"):
        self.name = name
        self.paths = [paths] if isinstance(paths, Path) else list(paths)
        raw = b"".join(p.read_bytes() for p in self.paths)
        self.sha = hashlib.sha256(raw).hexdigest()[:12]
        rows = [json.loads(x) for x in raw.decode().splitlines() if x.strip()]
        self.rows = {r["id"]: r for r in rows}

    def key(self) -> dict:
        return {"kind": "written", "file": ",".join(p.name for p in self.paths), "sha": self.sha}

    def estimate_cost(self, product: Product) -> float:
        return 0.0

    def describe(self, product: Product) -> Description:
        r = self.rows.get(product.id)
        if r is None:
            names = ", ".join(p.name for p in self.paths)
            return Description("", "none", 0.0, "none", {"status": f"not in {names}"})
        meta = {"status": "completed", "prompt": r.get("prompt")}
        return Description(r["text"].strip() + "\n", r.get("by", "written"), 0.0, "none", meta)


class VisionDescriber:
    """The product's photos (the primary first), then the prompt with its name, type and size."""

    paid = True

    def __init__(self, llm: LLM, prompt: PromptTemplate, params: dict, name: str):
        self.name = name
        self.llm = llm
        self.account = llm.account
        self.prompt = prompt
        self.max_photos = int(params.get("max_photos", 4))
        self.photo_max_side = int(params.get("photo_max_side", 1024))

    def key(self) -> dict:
        return {
            "kind": "vision",
            "llm": self.llm.key(),
            "max_photos": self.max_photos,
            "photo_max_side": self.photo_max_side,
            "prompt": self.prompt.version,
            "prompt_sha": self.prompt.sha,
        }

    def estimate_cost(self, product: Product) -> float:
        return self.llm.estimate_cost()

    def content(self, product: Product) -> list[dict]:
        photos = product.photos()[: self.max_photos]
        return [image_block(p, self.photo_max_side) for p in photos] + [
            text_block(self.prompt.render(product.info))
        ]

    def describe(self, product: Product) -> Description:
        a = self.llm.ask(self.content(product))
        meta = {**a.meta, "photos": a.meta.get("images")}
        return Description(a.text + "\n", a.model, a.cost_usd, a.cost_source, meta)


def get_describer(name: str, cfg: Config) -> Describer:
    params = dict(cfg.rag.describers.get(name, {}))
    if not params:
        raise ValueError(
            f"rag: no describer {name!r} in rag.describers; known: {sorted(cfg.rag.describers)}"
        )
    kind = params.pop("kind", name)
    if kind == "fields":
        return FieldsDescriber(name)
    if kind == "written":
        files = params["file"] if isinstance(params["file"], list) else [params["file"]]
        return WrittenDescriber([cfg.path(f) for f in files], name)
    if kind.endswith("_vision"):
        llm = make_llm({**params, "kind": kind.removesuffix("_vision")}, name)
        return VisionDescriber(llm, load_prompt(cfg.rag.describe_prompt, cfg.root), params, name)
    raise ValueError(f"rag: describer {name!r} has an unknown kind {kind!r}")
