"""Evaluación del retrieval por texto con el ground truth del dataset IKEA.

Para cada foto de ambiente (65 livings y comedores con productos anotados del catálogo), las
consultas de `evaluacion/ikea/consultas.json`: una por mueble del alcance que se ve, en las
ocho líneas del catálogo y con su kind (las escribieron subagentes mirando la foto, sin ver el
catálogo ni las anotaciones). Cada consulta pasa por la búsqueda de roomrag (filtros duros,
después los vecinos más cercanos por coseno) y se mira el ranking:

- **relevantes de una consulta**: los SKUs anotados en ese ambiente de la misma categoría del TP
  (sofá, sillón, silla, mesa, alfombra: configs/categories.yaml) que su kind. Es la misma
  definición que la v0 (retrieval por imagen), así que las dos se comparan con el mismo ground
  truth. Las anotaciones no dicen dónde está cada producto: la métrica es permisiva.
- hit rate@k y MRR@10 sobre las consultas con al menos un relevante; recall@k por ítem anotado;
  baseline aleatorio sobre lo que deja pasar el filtro; IC 95% por bootstrap de ambientes.

Un método es un embedder, el texto de cada producto que se embebe y el filtro:
- texto `description` (nuestras ocho líneas), `seller` (el texto del vendedor) o
  `name+description` (el nombre comercial adelante);
- filtro `kind` (el kind de la consulta), `type` (solo el tipo grueso) o `none`.
"""

from __future__ import annotations

import itertools
import json
import platform
import subprocess
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from roomrag.budget import ledger_for
from roomrag.catalog import load_catalog
from roomrag.config import Config
from roomrag.embed import get_embedder
from roomrag.evaluate import TEXTS
from roomrag.filters import Filters
from roomrag.index import Index, build_index, vectors_cached
from roomrag.kinds import KINDS

from amoblai.consultas import load_queries
from amoblai.metricas import (
    bootstrap_ci,
    first_relevant_rank,
    hit_at_k,
    random_hit_at_k,
    random_mrr,
    reciprocal_rank,
)

KS = (1, 3, 5, 10)

# kind de roomrag -> categoría del TP (la de la v0 y de configs/categories.yaml).
KIND_TO_TP = {
    "sofa": "sofa",
    "sofa bed": "sofa",
    "armchair": "armchair",
    "dining chair": "chair",
    "desk chair": "chair",
    "dining table": "table",
    "coffee table": "table",
    "side table": "table",
    "nightstand": "table",
    "console table": "table",
    "desk": "table",
    "rug": "rug",
}


@dataclass(frozen=True)
class Method:
    embedder: str
    text: str = "description"
    filter: str = "kind"  # kind | type | none

    @property
    def name(self) -> str:
        return f"{self.embedder}|{self.text}|filtro-{self.filter}"


def default_methods(embedders: list[str]) -> list[Method]:
    """La grilla de la ablación: embedder × texto × filtro, más el nombre comercial."""
    grid = [
        Method(e, t, f)
        for e, t, f in itertools.product(
            embedders, ("description", "seller"), ("kind", "type", "none")
        )
    ]
    grid += [Method(e, "name+description", "kind") for e in embedders if e != "hashing"]
    return grid


@dataclass
class Search:
    room_id: str
    piece: int
    kind: str
    query: str
    relevant: list[str]  # mismo tipo que el kind
    relevant_any: list[str]  # cualquier producto anotado del catálogo


def load_searches(queries_path: Path, raw_dir: Path, catalog_ids: dict[str, str]) -> list[Search]:
    """Consultas con sus relevantes, a partir del ground truth del dataset.

    `catalog_ids`: {SKU: categoría del TP} de los productos del catálogo."""
    from amoblai.data.ikea import IkeaDataset

    ds = IkeaDataset.load(raw_dir)
    searches = []
    for room_id, rec in load_queries(queries_path).items():
        gt = sorted(s for s in ds.rooms[room_id].skus if s in catalog_ids)
        for i, p in enumerate(rec["pieces"]):
            kind = p["kinds"][0]
            group = KIND_TO_TP[kind]
            searches.append(
                Search(room_id, i, kind, p["query"], [s for s in gt if catalog_ids[s] == group], gt)
            )
    return searches


def filters_for(method: Method, kind: str) -> Filters:
    if method.filter == "kind":
        return Filters(kinds=[kind])
    if method.filter == "type":
        return Filters(categories=[KINDS[kind]])
    return Filters()


def rank(cfg: Config, index: Index, method: Method, searches: list[Search], k: int) -> list[dict]:
    """El top-k de cada búsqueda con un método (los vectores se cachean)."""
    catalog = {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    embedder = get_embedder(method.embedder, cfg)
    ledger = ledger_for(cfg.budget, embedder.account)
    texts = [TEXTS[method.text](it, catalog[it["id"]]) for it in index.items]
    docs, _ = vectors_cached(texts, embedder, cfg, ledger)
    queries, _ = vectors_cached([s.query for s in searches], embedder, cfg, ledger)
    ranked = Index(index.path, index.meta, index.items, docs)
    rows = []
    for s, q in zip(searches, queries, strict=True):
        f = filters_for(method, s.kind)
        allowed = np.array([f.allows(it) for it in index.items], bool)
        hits = ranked.nearest(q, k, allowed)
        ids = [index.items[i]["id"] for i, _ in hits]
        rows.append(
            {
                **asdict(s),
                "method": method.name,
                "ranked": ids,
                "scores": [round(sc, 4) for _, sc in hits],
                "universe": int(allowed.sum()),
                "universe_relevant": sum(
                    1
                    for it, ok in zip(index.items, allowed, strict=True)
                    if ok and it["id"] in s.relevant
                ),
                "rank": first_relevant_rank(ids, s.relevant),
                "rank_any": first_relevant_rank(ids, s.relevant_any),
            }
        )
    return rows


def metrics(rows: list[dict], n_boot: int = 1000, seed: int = 0) -> dict[str, Any]:
    answerable = [r for r in rows if r["relevant"]]
    groups = [r["room_id"] for r in answerable]
    out: dict[str, Any] = {"searches": len(rows), "answerable": len(answerable)}
    for k in KS:
        vals = [hit_at_k(r["rank"], k) for r in answerable]
        out[f"hit@{k}"] = round(float(np.mean(vals)), 4)
        out[f"hit@{k}_ic95"] = [round(v, 4) for v in bootstrap_ci(vals, groups, n_boot, seed)]
    rr = [reciprocal_rank(r["rank"], max(KS)) for r in answerable]
    out["mrr@10"] = round(float(np.mean(rr)), 4)
    out["mrr@10_ic95"] = [round(v, 4) for v in bootstrap_ci(rr, groups, n_boot, seed)]
    out["literal_hit@10"] = round(
        float(np.mean([hit_at_k(r["rank_any"], 10) for r in rows if r["relevant_any"]])), 4
    )
    out["azar_hit@1"] = round(
        float(
            np.mean([random_hit_at_k(r["universe"], r["universe_relevant"], 1) for r in answerable])
        ),
        4,
    )
    out["azar_hit@10"] = round(
        float(
            np.mean(
                [random_hit_at_k(r["universe"], r["universe_relevant"], 10) for r in answerable]
            )
        ),
        4,
    )
    out["azar_mrr@10"] = round(
        float(np.mean([random_mrr(r["universe"], r["universe_relevant"], 10) for r in answerable])),
        4,
    )
    # Recall por ítem: cada SKU anotado (del tipo de alguna consulta del ambiente), ¿alguna
    # consulta del ambiente lo trajo en el top-k?
    best: dict[tuple[str, str], int | None] = {}
    for r in rows:
        for sku in r["relevant"]:
            pos = r["ranked"].index(sku) + 1 if sku in r["ranked"] else None
            key = (r["room_id"], sku)
            prev = best.get(key)
            best[key] = pos if prev is None else (prev if pos is None else min(prev, pos))
    item_groups = [room for room, _ in best]
    for k in (1, 10):
        vals = [hit_at_k(v, k) for v in best.values()]
        out[f"recall_item@{k}"] = round(float(np.mean(vals)), 4) if vals else None
        if vals:
            out[f"recall_item@{k}_ic95"] = [
                round(v, 4) for v in bootstrap_ci(vals, item_groups, n_boot, seed)
            ]
    by_kind: dict[str, list[float]] = defaultdict(list)
    for r in answerable:
        by_kind[KIND_TO_TP[r["kind"]]].append(hit_at_k(r["rank"], 1))
    out["hit@1_por_categoria"] = {
        t: round(float(np.mean(v)), 4) for t, v in sorted(by_kind.items())
    }
    out["consultas_por_categoria"] = dict(Counter(KIND_TO_TP[r["kind"]] for r in answerable))
    return out


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def run_eval(
    cfg: Config,
    queries_path: Path,
    raw_dir: Path,
    out_root: Path,
    methods: list[Method],
    name: str = "texto",
    n_boot: int = 1000,
) -> Path:
    """Corre todos los métodos y guarda una carpeta con config, métricas y rankings."""
    index = build_index(cfg, log=lambda _: None)  # las descripciones: el describer `written`
    catalog_ids = {
        p.id: p.info["category_tp"] for p in load_catalog(cfg.rag.catalog, cfg.root).products
    }
    searches = load_searches(queries_path, raw_dir, catalog_ids)
    run_dir = Path(out_root) / f"{time.strftime('%Y%m%d-%H%M%S')}_{name}"
    run_dir.mkdir(parents=True)
    results: dict[str, Any] = {}
    with (run_dir / "rankings.jsonl").open("w") as fh:
        for m in methods:
            t0 = time.perf_counter()
            rows = rank(cfg, index, m, searches, max(KS))
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            results[m.name] = {
                "method": asdict(m),
                **metrics(rows, n_boot),
                "segundos": round(time.perf_counter() - t0, 1),
            }
    meta = {
        "name": name,
        "queries": str(queries_path),
        "queries_meta": json.loads(Path(queries_path).read_text()).get("_meta"),
        "rooms": len({s.room_id for s in searches}),
        "catalog": cfg.rag.catalog,
        "index": index.meta,
        "embedders": {e: cfg.rag.embedders[e] for e in sorted({m.embedder for m in methods})},
        "git_commit": git_commit(),
        "python": platform.python_version(),
    }
    (run_dir / "corrida.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str)
    )
    (run_dir / "metricas.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    return run_dir
