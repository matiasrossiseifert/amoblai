"""The search: the hard filters first, then the descriptions nearest to the query. With
`rag.vector_store: chroma` ChromaDB does both (the filters as its `where`, then HNSW); with
`exact`, numpy over every vector, the baseline.

- mode ``rag``: at most ``top_k`` products, best first (about 3 that make sense, not necessarily
  of one style).
- mode ``whole_catalog``: every product that passes the filters, unranked. It is the
  alternative to compare against: the whole catalog goes to the model that chooses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from amoblai.config import Config
from amoblai.infra.budget import ledger_for
from amoblai.rag.embed import get_embedder
from amoblai.rag.filters import Filters
from amoblai.rag.index import Index, vectors_cached


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


def as_hit(item: dict, score: float | None) -> Hit:
    return Hit(**{k: item.get(k) for k in Hit.__dataclass_fields__ if k != "score"}, score=score)


def search(index: Index, query: str, filters: Filters, cfg: Config) -> list[Hit]:
    allowed = np.array([filters.allows(it) for it in index.items], bool)
    if cfg.rag.mode == "whole_catalog":
        return [as_hit(it, None) for it, ok in zip(index.items, allowed, strict=True) if ok]
    embedder = get_embedder(index.meta["embedder"]["name"], cfg)
    if embedder.key() != index.meta["embedder"]["key"]:
        raise ValueError(
            f"the index at {index.path} was built with another {embedder.name!r} setup; "
            "rebuild it (build_index)"
        )
    q, _ = vectors_cached([query], embedder, cfg, ledger_for(cfg.budget, embedder.account))
    if cfg.rag.vector_store == "exact":
        found = index.nearest(q[0], cfg.rag.top_k, allowed)
    else:
        found = index.query(q[0], cfg.rag.top_k, filters.where())
    return [as_hit(index.items[i], s) for i, s in found]
