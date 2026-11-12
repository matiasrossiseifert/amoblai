"""El espacio de embeddings del catálogo (clase 8: "¿cómo podemos visualizar los embeddings?").

- **separabilidad**, por embedder: de cada producto, ¿su vecino más cercano (coseno, sin contarse
  a sí mismo) es de su mismo kind? ¿y de su mismo tipo? Y el silhouette por kind (coseno). Mide
  si el espacio agrupa lo que el usuario distingue, antes de cualquier consulta.
- **UMAP** de las descripciones con Qwen3 (el embedder del sistema), coloreadas por tipo, con dos
  consultas proyectadas y sus diez vecinos: una del dominio (un sillón visto en un ambiente) y una
  de afuera (como en la demo de la clase: lo que trae queda disperso, y su mejor coseno es bajo).

Escribe `datos/resultados/evaluacion_espacio/espacio.json` y `datos/resultados/reporte/umap.png`.
Todo local: los vectores salen de la caché de la evaluación.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from amoblai import paths
from amoblai.config import Config

OUT = paths.RESULTS / "evaluacion_espacio" / "espacio.json"
EMBEDDERS = ("hashing", "bge", "qwen3")
IN_DOMAIN = (
    "Type: armchair, wingback reading chair\n"
    "Use: reading, relaxing; living room, reading corner\n"
    "Style: Scandinavian, classic\n"
    "Materials: light grey woven fabric, solid wood legs\n"
    "Colors: light grey, natural wood\n"
    "Shape: high back with side wings, rolled arms, loose seat cushion, four tapered legs\n"
    "Feel: cozy, calm, inviting\n"
    "Goes with: white walls, light wood floors, wool throws; Scandinavian living rooms"
)
OUT_OF_DOMAIN = "What is retrieval-augmented generation and how is it evaluated?"


def _vectors(cfg: Config, embedder: str, texts: list[str]) -> np.ndarray:
    from amoblai.infra.budget import ledger_for
    from amoblai.rag.embed import get_embedder
    from amoblai.rag.index import vectors_cached

    emb = get_embedder(embedder, cfg)
    return vectors_cached(texts, emb, cfg, ledger_for(cfg.budget, emb.account))[0]


def separability(vectors: np.ndarray, kinds: list[str], types: list[str]) -> dict[str, float]:
    """Vecino más cercano (sin el propio) del mismo kind y del mismo tipo; silhouette por kind."""
    from sklearn.metrics import silhouette_score

    sims = vectors @ vectors.T
    np.fill_diagonal(sims, -np.inf)
    nearest = sims.argmax(axis=1)
    kinds_a, types_a = np.array(kinds), np.array(types)
    counts = {k: kinds.count(k) for k in set(kinds)}
    keep = np.array([counts[k] > 1 for k in kinds])
    return {
        "vecino_mismo_kind": round(float((kinds_a[nearest] == kinds_a).mean()), 4),
        "vecino_mismo_tipo": round(float((types_a[nearest] == types_a).mean()), 4),
        "silhouette_kind": round(
            float(silhouette_score(vectors[keep], kinds_a[keep], metric="cosine")), 4
        ),
    }


def analyze(cfg: Config, out: Path = OUT, figure: Path = paths.REPORT / "umap.png") -> dict:
    from amoblai.rag.index import ensure_index

    index = ensure_index(cfg)
    items = index.items
    texts = [it["description"] for it in items]
    kinds = [it.get("kind") or "" for it in items]
    types = [it["category"] for it in items]
    result: dict[str, Any] = {"productos": len(items), "separabilidad": {}}
    for e in EMBEDDERS:
        result["separabilidad"][e] = separability(_vectors(cfg, e, texts), kinds, types)
    docs = _vectors(cfg, "qwen3", texts)
    queries = _vectors(cfg, "qwen3", [IN_DOMAIN, OUT_OF_DOMAIN])
    result["consultas"] = {}
    for name, q in zip(("del_dominio", "fuera_del_dominio"), queries, strict=True):
        sims = docs @ q
        top = np.argsort(-sims)[:10]
        result["consultas"][name] = {
            "mejor_coseno": round(float(sims[top[0]]), 4),
            "coseno_10": round(float(sims[top[-1]]), 4),
            "kinds_top10": [kinds[i] for i in top],
        }
    _plot(docs, queries, types, figure)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return result


def _plot(docs: np.ndarray, queries: np.ndarray, types: list[str], path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import umap

    reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric="cosine", random_state=0)
    xy = reducer.fit_transform(docs)
    qxy = reducer.transform(queries)
    palette = plt.get_cmap("tab20")
    cats = sorted(set(types))
    fig, ax = plt.subplots(figsize=(8, 6.2), facecolor="#fcfcfb")
    for i, c in enumerate(cats):
        m = np.array([t == c for t in types])
        ax.scatter(xy[m, 0], xy[m, 1], s=7, color=palette(i % 20), label=c, alpha=0.8)
    for (label, marker), q, qp in zip(
        (("consulta: sillón de lectura", "X"), ("consulta fuera del dominio", "P")),
        queries,
        qxy,
        strict=True,
    ):
        top = np.argsort(-(docs @ q))[:10]
        ax.scatter(
            xy[top, 0], xy[top, 1], s=40, facecolors="none", edgecolors="#0b0b0b", linewidths=0.9
        )
        ax.scatter([qp[0]], [qp[1]], s=150, marker=marker, color="#0b0b0b", label=label)
    ax.set_title(
        "Catálogo en el espacio de Qwen3-Embedding (UMAP, coseno); círculos: top-10",
        loc="left",
        fontsize=10,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.legend(
        fontsize=7,
        frameon=False,
        ncols=2,
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        markerscale=1.5,
    )
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, facecolor="#fcfcfb")
    plt.close(fig)
