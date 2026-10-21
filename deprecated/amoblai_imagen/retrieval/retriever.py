"""Retrieval: recorte → embedding → búsqueda ANN con metadata filtering → umbral.

Cada recorte se embebe con el mismo modelo que el catálogo y se buscan sus
vecinos más cercanos por similitud coseno en el índice HNSW. Con
`category_filter` la búsqueda se restringe a la categoría detectada (metadata
filtering); sin filtro se busca en todo el catálogo indexado. Si la mejor
similitud no supera el umbral, el mueble se descarta.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from amoblai_imagen.config import RetrievalConfig
from amoblai_imagen.embeddings.base import Embedder
from amoblai_imagen.infra.tracing import traced
from amoblai_imagen.vectorstore.chroma import ChromaVectorStore, Hit
from amoblai_imagen.vision.crops import QueryCrop

log = logging.getLogger(__name__)


@dataclass
class Candidate:
    sku: str
    score: float
    rank: int  # 1 = más similar
    category: str
    name: str
    image_path: str

    @classmethod
    def from_hit(cls, hit: Hit, rank: int) -> Candidate:
        m = hit.metadata
        return cls(
            sku=hit.sku,
            score=round(hit.score, 6),
            rank=rank,
            category=str(m.get("category", "")),
            name=str(m.get("name", "")),
            image_path=str(m.get("image_path", "")),
        )


@dataclass
class RetrievalResult:
    crop_index: int
    category: str  # categoría detectada
    candidates: list[Candidate]
    threshold: float | None
    reranked: bool = False
    chosen_sku: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def best_score(self) -> float | None:
        return self.candidates[0].score if self.candidates else None

    @property
    def accepted(self) -> bool:
        return self.chosen_sku is not None

    def ranked_skus(self) -> list[str]:
        """SKUs en orden, sin repetir (un SKU puede tener varias imágenes indexadas)."""
        seen: list[str] = []
        for c in self.candidates:
            if c.sku not in seen:
                seen.append(c.sku)
        return seen


def load_threshold(thresholds_file: Path, collection: str) -> float | None:
    path = Path(thresholds_file)
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text()) or {}
    entry = data.get(collection)
    return float(entry["threshold"]) if entry else None


def resolve_threshold(cfg: RetrievalConfig, thresholds_file: Path, key: str) -> float | None:
    """Umbral fijo de la config, o el calibrado para `key` (colección + fondo) si es "auto"."""
    if cfg.threshold == "auto":
        value = load_threshold(thresholds_file, key)
        if value is None:
            log.warning(
                "No hay umbral calibrado para %s: no se descarta ningún mueble. "
                "Calibrar con `amoblai eval retriever --calibrate`.",
                key,
            )
        return value
    return cfg.threshold


class Retriever:
    def __init__(
        self,
        embedder: Embedder,
        store: ChromaVectorStore,
        top_k: int = 10,
        category_filter: bool = True,
        threshold: float | None = None,
        scope: list[str] | None = None,
    ):
        self.embedder = embedder
        self.store = store
        self.top_k = top_k
        self.category_filter = category_filter
        self.threshold = threshold
        self.scope = scope

    def _where(self, category: str) -> dict[str, Any] | None:
        if self.category_filter:
            return {"category": category}
        return None

    @traced("retrieval", run_type="retriever")
    def search(self, crops: list[QueryCrop]) -> list[RetrievalResult]:
        if not crops:
            return []
        vectors = self.embedder.embed_images([c.query for c in crops])
        results = []
        for crop, vec in zip(crops, vectors, strict=True):
            hits = self.store.query(vec[None, :], self.top_k, self._where(crop.detection.category))[
                0
            ]
            candidates = [Candidate.from_hit(h, rank) for rank, h in enumerate(hits, start=1)]
            result = RetrievalResult(
                crop.index, crop.detection.category, candidates, self.threshold
            )
            best = result.best_score
            if best is not None and (self.threshold is None or best >= self.threshold):
                result.chosen_sku = candidates[0].sku
            results.append(result)
        return results
