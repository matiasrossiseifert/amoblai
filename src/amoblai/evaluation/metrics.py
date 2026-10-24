"""Métricas de retrieval (hit rate@k, MRR, context precision, NDCG, recall), baseline aleatorio,
intervalos bootstrap y la calibración del score (AUROC, umbral)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from math import comb, log2

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


def context_precision_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Context precision@K de RAGAS (clase 11): Σ_k (Precision@k · v_k) / relevantes en el top K,
    con v_k = 1 si el k-ésimo es relevante. 0 si no hay ninguno en el top K."""
    rel = set(relevant)
    found, total = 0, 0.0
    for i, item in enumerate(ranked[:k], start=1):
        if item in rel:
            found += 1
            total += found / i
    return total / found if found else 0.0


def ndcg_at_k(ranked: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """NDCG@k con relevancia binaria: DCG del ranking sobre el DCG del ranking ideal (todos los
    relevantes primero)."""
    rel = set(relevant)
    dcg = sum(1 / log2(i + 1) for i, item in enumerate(ranked[:k], start=1) if item in rel)
    ideal = sum(1 / log2(i + 1) for i in range(1, min(len(rel), k) + 1))
    return dcg / ideal if ideal else 0.0


def auroc(scores: Sequence[float], positive: Sequence[bool]) -> float:
    """Área bajo la curva ROC (Mann-Whitney): la probabilidad de que un positivo al azar tenga más
    score que un negativo al azar (los empates cuentan medio). NaN si falta una de las clases."""
    pos = np.asarray([s for s, p in zip(scores, positive, strict=True) if p], float)
    neg = np.asarray([s for s, p in zip(scores, positive, strict=True) if not p], float)
    if not len(pos) or not len(neg):
        return float("nan")
    greater = (pos[:, None] > neg[None, :]).sum()
    ties = (pos[:, None] == neg[None, :]).sum()
    return float((greater + 0.5 * ties) / (len(pos) * len(neg)))


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
