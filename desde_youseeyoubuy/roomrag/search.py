"""The search: the hard filters first, then the descriptions nearest to the query.

- mode ``rag``: at most ``top_k`` products, best first (about 3 that make sense, not necessarily
  of one style).
- mode ``whole_catalog``: every product that passes the filters, unranked. It is the
  alternative to compare against: the whole catalog goes to the model that chooses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .budget import ledger_for
from .config import Config
from .embed import get_embedder
from .filters import Filters
from .index import Index, vectors_cached


@dataclass
class Hit:
    id: str
    name: str
    category: str
    dimensions_cm: dict | None
    source: str  # its folder or JSON-lines file, relative to the root
    photos: list[str]  # relative to the root
    description: str
    score: float | None  # cosine similarity to the query; None in whole_catalog mode
    kind: str | None = None  # kinds.py


def _hit(item: dict, score: float | None) -> Hit:
    return Hit(**{k: item.get(k) for k in Hit.__dataclass_fields__ if k != "score"}, score=score)


def search(index: Index, query: str, filters: Filters, cfg: Config) -> list[Hit]:
    allowed = np.array([filters.allows(it) for it in index.items], bool)
    if cfg.rag.mode == "whole_catalog":
        return [_hit(it, None) for it, ok in zip(index.items, allowed, strict=True) if ok]
    embedder = get_embedder(index.meta["embedder"]["name"], cfg)
    if embedder.key() != index.meta["embedder"]["key"]:
        raise ValueError(
            f"the index at {index.path} was built with another {embedder.name!r} setup; "
            "rebuild it (build_index)"
        )
    q, _ = vectors_cached([query], embedder, cfg, ledger_for(cfg.budget, embedder.account))
    return [_hit(index.items[i], s) for i, s in index.nearest(q[0], cfg.rag.top_k, allowed)]
