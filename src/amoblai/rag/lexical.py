"""Lexical search (BM25) and its fusion with the dense search (hybrid search).

The descriptions and the queries are written in the same eight lines and vocabulary, so matching
words carries a lot: BM25 alone ranks about as well as the embedder, and the two together rank
better than either (evaluation/retrieval.py, `embedder: bm25` and `hybrid`).

- `BM25`: Okapi BM25 over the words of each description (`embed.words`: lowercase, no accents, no
  stopwords). The query's words count once each.
- `fuse`: the dense and the lexical scores of the products that pass the filters, as one score.
  `sum`: each score standardized over those products (z-score), then `alpha` dense + (1 - alpha)
  lexical. `rrf`: reciprocal rank fusion, 1 / (60 + rank) in each ranking, added.
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np

from amoblai.rag.embed import words


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


def fuse(
    dense: np.ndarray,
    lexical: np.ndarray,
    allowed: np.ndarray,
    how: str = "sum",
    alpha: float = 0.5,
    rrf_k: int = 60,
) -> np.ndarray:
    """One score per product from its dense and lexical scores (one query); -inf where the
    filters don't allow it."""
    out = np.full(dense.shape, -np.inf)
    if not allowed.any():
        return out
    a, b = dense[allowed].astype(float), lexical[allowed].astype(float)
    if how == "sum":

        def z(x: np.ndarray) -> np.ndarray:
            return (x - x.mean()) / max(float(x.std()), 1e-9)

        out[allowed] = alpha * z(a) + (1 - alpha) * z(b)
    elif how == "rrf":

        def reciprocal(x: np.ndarray) -> np.ndarray:
            rank = np.empty(len(x))
            rank[np.argsort(-x, kind="stable")] = np.arange(1, len(x) + 1)
            return 1.0 / (rrf_k + rank)

        out[allowed] = reciprocal(a) + reciprocal(b)
    else:
        raise ValueError(f"hybrid {how!r}: sum or rrf")
    return out
