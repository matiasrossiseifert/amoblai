"""The search: the hard filters first, then the descriptions nearest to the query. With
`rag.vector_store: chroma` ChromaDB does both (the filters as its `where`, then HNSW); with
`exact`, numpy over every vector, the baseline.

- mode ``rag``: at most ``top_k`` products, best first (about 3 that make sense, not necessarily
  of one style).
- mode ``whole_catalog``: every product that passes the filters, unranked. It is the
  alternative to compare against: the whole catalog goes to the model that chooses.
- mode ``random``: ``top_k`` products that pass the filters, at random (the same ones for the
  same query). The baseline without retrieval: what the ranking adds, end to end.

With ``rag.hybrid`` (hybrid.py) the cosine is one score of several: the lexical one (``bm25``) and
the product's photo against the query (an image-and-text model of ``rag.embedders``) are fused
with it over the products that pass the filters, and the best ``top_k`` of that are the answer.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from amoblai.config import Config
from amoblai.infra.budget import ledger_for
from amoblai.rag.embed import get_embedder
from amoblai.rag.filters import Filters
from amoblai.rag.hybrid import BM25, ImageTextEmbedder, fuse, visual_query
from amoblai.rag.index import Index, vectors_cached

_SCORERS: dict[tuple[str, str], object] = {}  # (index, scorer) -> what it needs, built once


@dataclass
class Hit:
    id: str
    name: str
    category: str
    dimensions_cm: dict | None
    source: str  # its folder or JSON-lines file, relative to the root
    photos: list[str]  # relative to the root
    description: str
    score: float | None  # cosine to the query (rag.hybrid: the fused score); None: whole_catalog
    kind: str | None = None  # kinds.py


def as_hit(item: dict, score: float | None) -> Hit:
    return Hit(**{k: item.get(k) for k in Hit.__dataclass_fields__ if k != "score"}, score=score)


def other_scores(index: Index, name: str, query: str, cfg: Config) -> np.ndarray:
    """One score per product of the index from another scorer: `bm25` over the descriptions, or
    an image-and-text model (rag.embedders, kind image_text) between the query as a short phrase
    and each product's photo."""
    key = (str(index.path), name)
    if name == "bm25":
        if key not in _SCORERS:
            _SCORERS[key] = BM25([it["description"] for it in index.items])
        return _SCORERS[key].scores([query])[0]
    params = cfg.rag.embedders.get(name) or {}
    if params.get("kind") != "image_text":
        raise ValueError(f"rag.hybrid: {name!r} is not bm25 nor an image_text embedder")
    if key not in _SCORERS:
        model = ImageTextEmbedder(params, name, Path(cfg.cache_dir))
        photos = [cfg.path(it["photos"][0]) for it in index.items]
        _SCORERS[key] = (model, model.embed_images(photos))
    model, photos = _SCORERS[key]
    return photos @ model.embed_texts([visual_query(query)])[0]


def search(index: Index, query: str, filters: Filters, cfg: Config) -> list[Hit]:
    allowed = np.array([filters.allows(it) for it in index.items], bool)
    if cfg.rag.mode == "whole_catalog":
        return [as_hit(it, None) for it, ok in zip(index.items, allowed, strict=True) if ok]
    if cfg.rag.mode == "random":
        seed = int(hashlib.sha256(query.encode()).hexdigest()[:8], 16)
        passed = np.flatnonzero(allowed)
        size = min(cfg.rag.top_k, len(passed))
        picked = np.random.default_rng(seed).choice(passed, size=size, replace=False)
        return [as_hit(index.items[i], None) for i in picked]
    embedder = get_embedder(index.meta["embedder"]["name"], cfg)
    if embedder.key() != index.meta["embedder"]["key"]:
        raise ValueError(
            f"the index at {index.path} was built with another {embedder.name!r} setup; "
            "rebuild it (build_index)"
        )
    q, _ = vectors_cached([query], embedder, cfg, ledger_for(cfg.budget, embedder.account))
    if cfg.rag.hybrid:
        scores = [index.vectors @ q[0]]
        scores += [other_scores(index, name, query, cfg) for name in cfg.rag.hybrid]
        fused = fuse(scores, allowed, cfg.rag.fusion)
        best = np.argsort(-fused, kind="stable")[: cfg.rag.top_k]
        return [as_hit(index.items[i], float(fused[i])) for i in best if np.isfinite(fused[i])]
    if cfg.rag.vector_store == "exact":
        found = index.nearest(q[0], cfg.rag.top_k, allowed)
    else:
        found = index.query(q[0], cfg.rag.top_k, filters.where())
    return [as_hit(index.items[i], s) for i, s in found]
