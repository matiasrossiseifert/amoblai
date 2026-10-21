"""Métricas de retrieval (hit rate@k, MRR, recall), baseline aleatorio e intervalos bootstrap."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import comb

import numpy as np


def first_relevant_rank(ranked: Sequence[str], relevant: Iterable[str]) -> int | None:
    """Posición (desde 1) del primer elemento relevante, o None si no aparece."""
    rel = set(relevant)
    for i, item in enumerate(ranked, start=1):
        if item in rel:
            return i
    return None


def hit_at_k(rank: int | None, k: int) -> float:
    return 1.0 if rank is not None and rank <= k else 0.0


def reciprocal_rank(rank: int | None, k: int | None = None) -> float:
    """1/rank del primer relevante (0 si no aparece o si queda después de k)."""
    if rank is None or (k is not None and rank > k):
        return 0.0
    return 1.0 / rank


def random_hit_at_k(n_items: int, n_relevant: int, k: int) -> float:
    """P(al menos un relevante en el top-k) si el ranking fuera una permutación al azar."""
    if n_items <= 0 or n_relevant <= 0:
        return 0.0
    k = min(k, n_items)
    return 1.0 - comb(n_items - n_relevant, k) / comb(n_items, k)


def random_mrr(n_items: int, n_relevant: int, k: int | None = None) -> float:
    """E[1/rank del primer relevante] para un ranking al azar (truncado en k)."""
    if n_items <= 0 or n_relevant <= 0:
        return 0.0
    last = n_items - n_relevant + 1
    if k is not None:
        last = min(last, k)
    total = comb(n_items, n_relevant)
    return sum(comb(n_items - i, n_relevant - 1) / total / i for i in range(1, last + 1))


def bootstrap_ci(
    values: Sequence[float],
    groups: Sequence[str],
    n_samples: int = 1000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """IC del promedio con bootstrap por grupos (ambientes).

    Los recortes de un mismo ambiente no son independientes, así que se
    remuestrean ambientes completos y no recortes sueltos.
    """
    if not values:
        return (float("nan"), float("nan"))
    vals = np.asarray(values, dtype=float)
    uniq = sorted(set(groups))
    index = {g: np.flatnonzero(np.asarray(groups) == g) for g in uniq}
    rng = np.random.default_rng(seed)
    means = np.empty(n_samples)
    for s in range(n_samples):
        picked = rng.choice(len(uniq), size=len(uniq), replace=True)
        idx = np.concatenate([index[uniq[i]] for i in picked])
        means[s] = vals[idx].mean()
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return (float(lo), float(hi))


def best_f1_threshold(scores: Sequence[float], correct: Sequence[bool]) -> dict[str, float]:
    """Umbral de similitud que maximiza F1 de "aceptar ⇔ el top-1 es correcto"."""
    pairs = sorted(zip(scores, correct, strict=True), key=lambda p: -p[0])
    total_pos = sum(1 for _, c in pairs if c)
    if not pairs or total_pos == 0:
        return {"threshold": float("nan"), "f1": 0.0, "precision": 0.0, "recall": 0.0}
    best = {"threshold": pairs[0][0], "f1": -1.0, "precision": 0.0, "recall": 0.0}
    tp = fp = 0
    for i, (score, ok) in enumerate(pairs):
        tp += int(ok)
        fp += int(not ok)
        if i + 1 < len(pairs) and pairs[i + 1][0] == score:
            continue  # evaluar solo al final de cada grupo de scores iguales
        precision = tp / (tp + fp)
        recall = tp / total_pos
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if f1 > best["f1"]:
            best = {"threshold": float(score), "f1": f1, "precision": precision, "recall": recall}
    return best
