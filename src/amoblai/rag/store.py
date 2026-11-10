"""The vector database: ChromaDB, one collection per index, with an HNSW index in cosine space.

Each product is one record: its id, its vector (embed.py makes it: Chroma embeds nothing), its
description as the document, and the metadata the hard filters read (filters.py): its type,
its kind and its size. Chroma stores no None: a missing kind goes as "" and a missing size as
-1, which passes any "at most" limit, as in `Filters.allows`.

Chroma returns the cosine distance (1 - cos); `query` gives back the similarity.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Any

import numpy as np

# crear clientes de ChromaDB desde varios hilos a la vez falla (los bindings de Rust)
_CLIENT_LOCK = threading.Lock()

AXES = ("width", "depth", "height")
MISSING = -1.0  # a size the catalog doesn't have
BATCH = 1000


def metadata_for(item: dict) -> dict[str, Any]:
    """What the filters read from a product, as Chroma metadata."""
    dims = item.get("dimensions_cm") or {}
    sizes = {a: float(dims[a]) if dims.get(a) is not None else MISSING for a in AXES}
    return {"category": item["category"], "kind": item.get("kind") or "", **sizes}


def collection_name(text: str) -> str:
    """A valid collection name: 3 to 512 of [a-zA-Z0-9._-], starting and ending alphanumeric."""
    name = re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-._")
    return (name or "products").ljust(3, "0")[:512]


class ChromaStore:
    """A collection on disk (`path`) or in memory (no path: the evaluation's, per method)."""

    def __init__(self, path: Path | None, name: str = "products"):
        import chromadb

        settings = chromadb.Settings(anonymized_telemetry=False)
        if path is None:
            self.client = chromadb.EphemeralClient(settings=settings)
        else:
            Path(path).mkdir(parents=True, exist_ok=True)
            with _CLIENT_LOCK:
                self.client = chromadb.PersistentClient(path=str(path), settings=settings)
        self.name = collection_name(name)

    def create(self, items: list[dict], vectors: np.ndarray, hnsw: dict | None = None) -> None:
        """The collection anew: one record per item, in this order."""
        if self.name in {c.name for c in self.client.list_collections()}:
            self.client.delete_collection(self.name)
        col = self.client.create_collection(
            self.name,
            configuration={"hnsw": {"space": "cosine", **(hnsw or {})}},
            embedding_function=None,
        )
        for start in range(0, len(items), BATCH):
            part = items[start : start + BATCH]
            col.add(
                ids=[it["id"] for it in part],
                embeddings=vectors[start : start + BATCH].astype(np.float32),
                metadatas=[metadata_for(it) for it in part],
                documents=[it.get("description") or "" for it in part],
            )

    @property
    def collection(self):
        return self.client.get_collection(self.name, embedding_function=None)

    def count(self) -> int:
        return self.collection.count()

    def vectors(self, ids: list[str]) -> np.ndarray:
        """The stored vectors of `ids`, in that order."""
        got = self.collection.get(ids=ids, include=["embeddings"])
        by_id = dict(zip(got["ids"], got["embeddings"], strict=True))
        return np.stack([np.asarray(by_id[i], dtype=np.float32) for i in ids])

    def query(
        self, vector: np.ndarray, k: int, where: dict | None = None
    ) -> list[tuple[str, float]]:
        """The k records nearest to `vector` (HNSW) among those `where` lets through, best
        first, with their cosine similarity."""
        res = self.collection.query(
            query_embeddings=[np.asarray(vector, dtype=np.float32)],
            n_results=k,
            where=where,
            include=["distances"],
        )
        return [
            (i, 1.0 - float(d)) for i, d in zip(res["ids"][0], res["distances"][0], strict=True)
        ]
