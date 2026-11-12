"""Hybrid search: the dense search over the descriptions, plus other ways of scoring a product for
the same query, fused into one ranking.

- `BM25`: lexical. Okapi BM25 over the words of each description (`embed.words`: lowercase, no
  accents, no stopwords); the query's words count once each. The descriptions and the queries
  are written in the same eight lines and vocabulary, so matching words carries a lot.
- `ImageTextEmbedder`: visual. A CLIP-like model (SigLIP 2, CLIP) puts the product's photo and
  the query's text in one space: the index "sees" the product instead of reading its description.
  The text tower reads few tokens (64 in SigLIP 2), so the query goes in as one short phrase
  (`visual_query`: what it is, materials, colors, shape).
- `fuse`: the scores of the products that pass the filters, as one score. `sum`: each score
  standardized over those products (z-score), then averaged. `rrf`: reciprocal rank fusion,
  1 / (60 + rank) in each ranking, added.

Measured in evaluation/retrieval.py (`embedder: bm25 | siglip2 | clip`, `fusion`,
datos/configs/ablaciones/hibrido.yaml); the flow uses it with `rag.hybrid` (search.py).
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from amoblai.rag.embed import unit_rows, words

VISUAL_LINES = ("Type", "Materials", "Colors", "Shape")


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        tokens = [words(d) for d in docs]
        n = len(tokens)
        df = Counter(w for doc in tokens for w in set(doc))
        self.vocab = {w: i for i, w in enumerate(df)}
        tf = np.zeros((n, len(self.vocab)), np.float32)
        for i, doc in enumerate(tokens):
            for w, c in Counter(doc).items():
                tf[i, self.vocab[w]] = c
        length = np.array([len(doc) for doc in tokens], np.float32)
        mean = float(length.mean()) if n else 1.0
        idf = np.array([math.log(1 + (n - c + 0.5) / (c + 0.5)) for c in df.values()], np.float32)
        norm = k1 * (1 - b + b * length[:, None] / max(mean, 1e-9))
        self.weights = idf * tf * (k1 + 1) / (tf + norm)  # (docs, vocab)

    def scores(self, queries: list[str]) -> np.ndarray:
        """(queries, docs): the BM25 score of each document for each query."""
        out = np.zeros((len(queries), self.weights.shape[0]), np.float32)
        for i, q in enumerate(queries):
            cols = [self.vocab[w] for w in set(words(q)) if w in self.vocab]
            if cols:
                out[i] = self.weights[:, cols].sum(1)
        return out


def visual_query(query: str) -> str:
    """The query as one short phrase for a CLIP-like text tower: what the lines Type, Materials,
    Colors and Shape say, without their labels. A query that is not in lines goes as it is."""
    lines = {}
    for line in query.splitlines():
        label, _, body = line.partition(":")
        if body.strip():
            lines.setdefault(label.strip(), body.strip())
    parts = [lines[k] for k in VISUAL_LINES if k in lines]
    return "; ".join(parts) if parts else " ".join(query.split())


class ImageTextEmbedder:
    """`model`: a CLIP-like checkpoint of transformers (get_image_features, get_text_features).
    The photos' vectors are cached, one file per photo and model."""

    def __init__(self, params: dict, name: str, cache_dir: Path):
        self.name = name
        self.model_id = str(params["model"])
        self.max_length = int(params.get("max_length", 64))
        self.batch = int(params.get("batch", 32))
        self.cache = Path(cache_dir) / "rag" / "vectores_foto" / name
        self._loaded = None

    def key(self) -> dict:
        return {"kind": "image_text", "model": self.model_id, "max_length": self.max_length}

    def _load(self):
        if self._loaded is None:
            from transformers import AutoModel, AutoProcessor

            self._loaded = (
                AutoProcessor.from_pretrained(self.model_id),
                AutoModel.from_pretrained(self.model_id).eval(),
            )
        return self._loaded

    @staticmethod
    def _rows(out) -> np.ndarray:
        x = out if hasattr(out, "numpy") else out.pooler_output
        return unit_rows(x.float().numpy())

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        import torch

        proc, model = self._load()
        rows = []
        with torch.inference_mode():
            for i in range(0, len(texts), 64):
                enc = proc(
                    text=texts[i : i + 64],
                    padding="max_length",
                    max_length=self.max_length,
                    truncation=True,
                    return_tensors="pt",
                )
                rows.append(self._rows(model.get_text_features(**enc)))
        return np.concatenate(rows)

    def embed_images(self, photos: Sequence[Path]) -> np.ndarray:
        """One vector per photo, in order (only the photos the cache doesn't have are read by
        the model)."""
        files = []
        for p in photos:
            sha = hashlib.sha256(self.model_id.encode() + Path(p).read_bytes()).hexdigest()[:24]
            files.append(self.cache / f"{sha}.npy")
        todo = [i for i, f in enumerate(files) if not f.exists()]
        if todo:
            import torch
            from PIL import Image

            proc, model = self._load()
            self.cache.mkdir(parents=True, exist_ok=True)
            with torch.inference_mode():
                for start in range(0, len(todo), self.batch):
                    part = todo[start : start + self.batch]
                    images = [Image.open(photos[i]).convert("RGB") for i in part]
                    enc = proc(images=images, return_tensors="pt")
                    for i, v in zip(part, self._rows(model.get_image_features(**enc)), strict=True):
                        np.save(files[i], v)
        return np.stack([np.load(f) for f in files])


def fuse(
    scores: Sequence[np.ndarray], allowed: np.ndarray, how: str = "sum", rrf_k: int = 60
) -> np.ndarray:
    """One score per product from several (each an array over the products, for one query);
    -inf where the filters don't allow the product."""
    out = np.full(allowed.shape, -np.inf)
    if not allowed.any():
        return out
    parts = [np.asarray(s, float)[allowed] for s in scores]
    if how == "sum":
        out[allowed] = np.mean([(x - x.mean()) / max(float(x.std()), 1e-9) for x in parts], axis=0)
    elif how == "rrf":
        total = np.zeros(int(allowed.sum()))
        for x in parts:
            rank = np.empty(len(x))
            rank[np.argsort(-x, kind="stable")] = np.arange(1, len(x) + 1)
            total += 1.0 / (rrf_k + rank)
        out[allowed] = total
    else:
        raise ValueError(f"fusion {how!r}: sum or rrf")
    return out
