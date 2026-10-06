"""Vector store: ChromaDB persistente con índice HNSW y espacio coseno explícito.

El espacio por defecto de Chroma es L2. Acá se configura `cosine` explícitamente
y además los embeddings llegan L2-normalizados, así que distancia coseno y L2
ordenan igual. Chroma devuelve distancia coseno (1 - cos); se convierte a
similitud para el umbral.

Hay una colección por combinación de modelo de embeddings y preprocesamiento:
cambiar cualquiera de los dos crea otra colección en vez de mezclar vectores
incompatibles.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Hit:
    id: str
    sku: str
    score: float  # similitud coseno
    metadata: dict[str, Any]


def collection_name_for(embedder_name: str, model_id: str, preprocess_hash: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", f"{embedder_name}-{model_id}").strip("-").lower()
    return f"catalog_{slug}_{preprocess_hash}"[:120]


class ChromaVectorStore:
    def __init__(self, path: Path, collection_name: str):
        import chromadb

        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.path), settings=chromadb.Settings(anonymized_telemetry=False)
        )
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            collection_name,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )

    def count(self) -> int:
        return self.collection.count()

    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        found: set[str] = set()
        for start in range(0, len(ids), 500):
            found.update(self.collection.get(ids=list(ids[start : start + 500]), include=[])["ids"])
        return found

    def upsert(
        self, ids: Sequence[str], embeddings: np.ndarray, metadatas: Sequence[dict[str, Any]]
    ) -> None:
        self.collection.upsert(
            ids=list(ids), embeddings=embeddings.astype(np.float32), metadatas=list(metadatas)
        )

    def query(
        self, embeddings: np.ndarray, k: int, where: dict[str, Any] | None = None
    ) -> list[list[Hit]]:
        """ANN (HNSW) por similitud coseno, con metadata filtering opcional."""
        if len(embeddings) == 0:
            return []
        res = self.collection.query(
            query_embeddings=embeddings.astype(np.float32),
            n_results=k,
            where=where,
            include=["metadatas", "distances"],
        )
        results: list[list[Hit]] = []
        for ids, dists, metas in zip(res["ids"], res["distances"], res["metadatas"], strict=True):
            results.append(
                [
                    Hit(id=i, sku=str(m["sku"]), score=1.0 - float(d), metadata=dict(m))
                    for i, d, m in zip(ids, dists, metas, strict=True)
                ]
            )
        return results

    def get_embeddings(self, ids: Sequence[str]) -> dict[str, np.ndarray]:
        res = self.collection.get(ids=list(ids), include=["embeddings"])
        return {
            i: np.asarray(e, dtype=np.float32)
            for i, e in zip(res["ids"], res["embeddings"], strict=True)
        }
