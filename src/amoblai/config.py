"""The configuration: one YAML file (datos/configs/amoblai.yaml; it may `extends:` another),
every field below, and `--set a.b=value` overrides. Paths to inputs (catalog, photos, prompts,
written descriptions) are relative to `root`; `cache_dir`, `runs_dir` and `budget.ledger` to the
working directory.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class _Cfg(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RagConfig(_Cfg):
    """The catalog search."""

    catalog: str = "catalog.yaml"  # catalog.py: which products, and where
    workers: int = 1  # products described at once when the index is built (paid describers)
    # "rag": the hard filters, then the top_k descriptions nearest to the query. "whole_catalog":
    # every product that passes the filters, unranked (the alternative to compare against).
    mode: Literal["rag", "whole_catalog"] = "rag"
    top_k: int = 3
    # Keys of `describers` and `embedders` (describe.py, embed.py).
    describer: str = "written"
    describe_prompt: str = "describe_product_v3.md"
    embedder: str = "hashing"
    describers: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {"fields": {"kind": "fields"}}
    )
    embedders: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {"hashing": {"kind": "hashing", "dim": 1024}}
    )
    # Where the vectors are searched (store.py): "chroma", ChromaDB with an HNSW index in cosine
    # space and the filters as its `where`; "exact", every vector with numpy, the baseline.
    vector_store: Literal["chroma", "exact"] = "chroma"
    hnsw: dict[str, Any] = Field(default_factory=dict)  # ChromaDB's: ef_search, max_neighbors...


class FurnishConfig(_Cfg):
    """From a room photo and a request to the room with the products (flow.py)."""

    # The steps, in order: names from flow.STEPS, or "package.module:function" for a step of
    # one's own. Each writes its own file in the run folder.
    steps: list[str] = Field(
        default_factory=lambda: ["plan", "retrieve", "choose", "scene", "generate"]
    )
    # The LLM that reads the photos and writes (llm.py): kind anthropic | openai_chat, model,
    # its prices (`models`), effort...
    llm: dict[str, Any] = Field(default_factory=dict)
    max_pieces: int | None = None  # pieces of the plan carried on (most important first); None: all
    candidates: int = 3  # products the search brings for each piece
    # The plan's most-it-can-measure comes from a photo: the search allows this much more.
    size_slack: float = 0.15
    photo_max_side: int = 1024  # photos sent to the LLM
    query_prompt: str = "search_query_v4.md"
    choose_prompt: str = "choose_combination_v1.md"
    scene_prompt: str = "scene_prompt_v1.md"
    # False: the scene prompt is the template filled in (scene_prompt_libre_*: the image model
    # arranges the products itself), with no LLM call.
    scene_llm: bool = True
    # The image model that puts the chosen products in the room (generate.py).
    generator: str = "manual"
    generators: dict[str, dict[str, Any]] = Field(
        default_factory=lambda: {"manual": {"kind": "manual"}}
    )


class EvaluationConfig(_Cfg):
    """The retrieval evaluation (evaluation/retrieval.py) beyond the search itself."""

    # Post-retrieval ablation: a vision LLM reorders the search's `rerank_top` candidates.
    rerank_top: int = 10
    rerank_prompt: str = "rerank_candidates_v1.md"
    rerankers: dict[str, dict[str, Any]] = Field(default_factory=dict)  # name -> LLM (llm.py)


class BudgetConfig(_Cfg):
    # Hard cap on total paid spend recorded in the ledger, for every API account without a cap
    # of its own.
    max_usd_total: float = 10.0
    # API accounts with a cap of their own, spent apart from max_usd_total (e.g. anthropic).
    accounts: dict[str, float] = Field(default_factory=dict)
    # Steps whose paid calls need no allow_paid, within the caps (e.g. "rag.embed").
    allow_paid_steps: list[str] = Field(default_factory=list)
    ledger: str = "cache/spend_ledger.jsonl"
    # Paid APIs are refused unless this is true (an approved run: --set budget.allow_paid=true).
    allow_paid: bool = False


class Config(_Cfg):
    extends: str | None = None
    name: str = "amoblai"
    root: str = "."
    cache_dir: str = "cache"
    runs_dir: str = "runs"
    rag: RagConfig = RagConfig()
    furnish: FurnishConfig = FurnishConfig()
    evaluation: EvaluationConfig = EvaluationConfig()
    budget: BudgetConfig = BudgetConfig()

    def path(self, p: str | Path) -> Path:
        """An input path: as it is if absolute, else under `root`."""
        p = Path(p)
        return p if p.is_absolute() else Path(self.root) / p


def deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_raw(path: str | Path, _seen: tuple[Path, ...] = ()) -> dict:
    path = Path(path).resolve()
    if path in _seen:
        raise ValueError(f"config extends cycle: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    parent = data.get("extends")
    if parent:
        base = load_raw(path.parent / parent, (*_seen, path))
        data = deep_merge(base, {k: v for k, v in data.items() if k != "extends"})
    return data


def load_config(
    path: str | Path | None = None, overrides: dict | None = None, model: type[Config] = Config
) -> Config:
    raw = load_raw(path) if path else {}
    if overrides:
        raw = deep_merge(raw, overrides)
    raw.pop("extends", None)
    return model.model_validate(raw)


def parse_override(expr: str) -> dict:
    """'rag.top_k=5' -> {'rag': {'top_k': 5}} (value parsed as YAML)."""
    key, _, value = expr.partition("=")
    if not key or not _:
        raise ValueError(f"override must look like a.b.c=value, got {expr!r}")
    node: dict = {}
    cur = node
    parts = key.strip().split(".")
    for p in parts[:-1]:
        cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = yaml.safe_load(value)
    return node
