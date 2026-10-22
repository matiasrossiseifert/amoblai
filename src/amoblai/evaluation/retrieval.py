"""Evaluación del retrieval por texto con el ground truth del dataset IKEA.

Para cada foto de ambiente (65 livings y comedores con productos anotados del catálogo), las
consultas de `datos/evaluacion_ikea/consultas.json`: una por mueble del alcance que se ve, en
las ocho líneas del catálogo y con su kind (las escribieron subagentes mirando la foto, sin ver
el catálogo ni las anotaciones). Cada consulta pasa por la búsqueda (filtros duros, después los
vecinos más cercanos por coseno) y se mira el ranking:

- **relevantes de una consulta**: los SKUs anotados en ese ambiente de la misma categoría del TP
  (sofá, sillón, silla, mesa, alfombra: datos/configs/categories.yaml) que su kind. Es la misma
  definición que la v0 (retrieval por imagen), así que las dos se comparan con el mismo ground
  truth. Las anotaciones no dicen dónde está cada producto: la métrica es permisiva.
- hit rate@k y MRR@10 sobre las consultas con al menos un relevante; recall@k por ítem anotado;
  baseline aleatorio sobre lo que deja pasar el filtro; IC 95% por bootstrap de ambientes.

Un método (las ablaciones de datos/configs/ablaciones/*.yaml) combina:
- `embedder`: hashing, bge, qwen3 (rag.embedders);
- `text`, lo que se embebe de cada producto: `description` (nuestras ocho líneas), `seller` (el
  texto del vendedor) o `name+description` (el nombre comercial adelante);
- `filter`: `kind` (el kind de la consulta), `type` (solo el tipo grueso) o `none`;
- `store`, la base vectorial: `chroma` (ChromaDB, HNSW, los filtros como `where`) o `exact`
  (numpy sobre todos los vectores);
- `query`, el query rewriting: `full` (las ocho líneas, como las escribe el plan), `type` (solo
  la línea Type) o `kind` (solo el nombre del kind: sin reescribir);
- `rerank`: un VLM reordena los `evaluation.rerank_top` primeros mirando las fotos (pago).
"""

from __future__ import annotations

import hashlib
import itertools
import json
import platform
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from amoblai.catalog.kinds import KINDS
from amoblai.catalog.loader import Product, load_catalog
from amoblai.config import Config
from amoblai.evaluation.metrics import (
    bootstrap_ci,
    first_relevant_rank,
    hit_at_k,
    random_hit_at_k,
    random_mrr,
    reciprocal_rank,
)
from amoblai.evaluation.queries import load_queries
from amoblai.furnish.llm import image_block, text_block
from amoblai.furnish.steps import ask, photo, size_text, type_line
from amoblai.infra.budget import ledger_for
from amoblai.infra.http import ProviderError
from amoblai.prompts import load_prompt
from amoblai.rag.describe import FieldsDescriber
from amoblai.rag.embed import get_embedder
from amoblai.rag.filters import Filters
from amoblai.rag.index import Index, build_index, vectors_cached
from amoblai.rag.search import as_hit
from amoblai.rag.store import ChromaStore

KS = (1, 3, 5, 10)

# Lo que se embebe de cada producto (item del índice, producto del catálogo).
TEXTS: dict[str, Callable[[dict, Product], str]] = {
    "description": lambda it, p: it["description"],  # nuestras ocho líneas
    "name+description": lambda it, p: f"Name: {it['name']}\n{it['description']}",
    "seller": lambda it, p: FieldsDescriber().describe(p).text,  # nombre, colores, texto
}

# kind (catalog/kinds.py) -> categoría del TP (la de la v0 y de datos/configs/categories.yaml).
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
    store: str = "chroma"  # chroma | exact
    query: str = "full"  # full | type | kind
    rerank: str | None = None  # un reranker de evaluation.rerankers

    @property
    def name(self) -> str:
        name = f"{self.embedder}|{self.text}|filtro-{self.filter}"
        if self.store != "chroma":
            name += f"|{self.store}"
        if self.query != "full":
            name += f"|consulta-{self.query}"
        if self.rerank:
            name += f"|rerank-{self.rerank}"
        return name

    @property
    def paid(self) -> bool:
        return self.rerank is not None


def load_ablation(path: Path) -> tuple[str, list[Method]]:
    """(nombre, métodos) de una ablación: la grilla (producto cartesiano de `grid`) más los
    métodos sueltos de `methods`; los campos que faltan toman el default de Method."""
    spec = yaml.safe_load(Path(path).read_text()) or {}
    grid = spec.get("grid") or {}
    methods = (
        [
            Method(**dict(zip(grid, combo, strict=True)))
            for combo in itertools.product(*grid.values())
        ]
        if grid
        else []
    )
    methods += [Method(**m) for m in spec.get("methods") or []]
    return spec.get("name") or Path(path).stem, list(dict.fromkeys(methods))


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
    from amoblai.dataset.ikea import IkeaDataset

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


# El query rewriting: la consulta como la escribe el plan, o menos.
QUERIES: dict[str, Callable[[Search], str]] = {
    "full": lambda s: s.query,  # las ocho líneas
    "type": lambda s: s.query.splitlines()[0],  # solo "Type: ..."
    "kind": lambda s: s.kind,  # solo el nombre del kind, sin reescribir
}


def _candidate(answer: str, ids: list[str]) -> str | None:
    """Un id de la respuesta: el id tal cual, o el número de imagen ("image 3", "3")."""
    answer = str(answer).strip()
    if answer in ids:
        return answer
    n = answer.lower().removeprefix("image").strip(" .")
    return ids[int(n) - 1] if n.isdigit() and 1 <= int(n) <= len(ids) else None


def rerank(cfg: Config, reranker: str, query: str, items: list[dict]) -> list[str]:
    """Los ids de `items` reordenados por el VLM `reranker` mirando sus fotos (pago; la
    respuesta queda en caché: la misma consulta con los mismos candidatos no se paga dos veces)."""
    params = cfg.evaluation.rerankers[reranker]
    tmpl = load_prompt(cfg.evaluation.rerank_prompt, cfg.root)
    hits = [as_hit(it, None) for it in items]
    lines = [
        f"image {n}. {h.id}: {h.kind or h.category}, {type_line(h)}, {size_text(h)}"
        for n, h in enumerate(hits, 1)
    ]
    text = tmpl.fill(query=query, n=len(hits), candidates="\n".join(lines))
    key = {"llm": params, "prompt": tmpl.version, "text": text}
    sha = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
    f = Path(cfg.cache_dir) / "rerank" / f"{sha}.json"
    if f.exists():
        return json.loads(f.read_text())["ranking"]
    content = [image_block(photo(cfg, h), cfg.furnish.photo_max_side) for h in hits]
    a, data = ask(cfg, "eval.rerank", [*content, text_block(text)], params)
    ids = [h.id for h in hits]
    got = [i for i in dict.fromkeys(_candidate(x, ids) for x in data.get("ranking") or []) if i]
    if not got:
        raise ProviderError(f"eval.rerank: no ranking in the answer: {a.text[:200]!r}")
    ranking = got + [i for i in ids if i not in got]
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"ranking": ranking, "model": a.model, "cost_usd": a.cost_usd}))
    return ranking


def rank(
    cfg: Config,
    index: Index,
    method: Method,
    searches: list[Search],
    k: int,
    workers: int = 8,
) -> list[dict]:
    """El top-k de cada búsqueda con un método (los vectores se cachean; con `store: chroma`,
    una colección de ChromaDB en memoria con los vectores de ese embedder y ese texto)."""
    catalog = {p.id: p for p in load_catalog(cfg.rag.catalog, cfg.root).products}
    embedder = get_embedder(method.embedder, cfg)
    ledger = ledger_for(cfg.budget, embedder.account)
    texts = [TEXTS[method.text](it, catalog[it["id"]]) for it in index.items]
    docs, _ = vectors_cached(texts, embedder, cfg, ledger)
    queries, _ = vectors_cached([QUERIES[method.query](s) for s in searches], embedder, cfg, ledger)
    ranked = Index(index.path, index.meta, index.items, docs)
    if method.store == "chroma":
        ranked.store = ChromaStore(None, f"eval-{method.embedder}-{method.text}")
        ranked.store.create(index.items, docs, cfg.rag.hnsw)
    rows = []
    for s, q in zip(searches, queries, strict=True):
        f = filters_for(method, s.kind)
        allowed = np.array([f.allows(it) for it in index.items], bool)
        if method.store == "exact":
            hits = ranked.nearest(q, k, allowed)
        else:
            hits = ranked.query(q, k, f.where())
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
            }
        )
    if method.rerank:
        by_id = {it["id"]: it for it in index.items}
        top = cfg.evaluation.rerank_top

        def one(row: dict) -> list[str]:
            if not row["relevant"]:  # no entra en las métricas: no se paga
                return row["ranked"]
            head = rerank(cfg, method.rerank, row["query"], [by_id[i] for i in row["ranked"][:top]])
            return head + row["ranked"][top:]

        with ThreadPoolExecutor(max(1, workers)) as pool:
            for row, new in zip(rows, pool.map(one, rows), strict=True):
                score = dict(zip(row["ranked"], row["scores"], strict=True))
                row["ranked"], row["scores"] = new, [score[i] for i in new]
    for row in rows:
        row["rank"] = first_relevant_rank(row["ranked"], row["relevant"])
        row["rank_any"] = first_relevant_rank(row["ranked"], row["relevant_any"])
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
    started = time.strftime("%Y%m%d-%H%M%S")
    results: dict[str, Any] = {}
    rankings: list[dict] = []
    for m in methods:  # todo antes de escribir: una corrida que falla no deja nada a medias
        t0 = time.perf_counter()
        rows = rank(cfg, index, m, searches, max(KS))
        rankings += rows
        results[m.name] = {
            "method": asdict(m),
            **metrics(rows, n_boot),
            "segundos": round(time.perf_counter() - t0, 1),
        }
    run_dir = Path(out_root) / f"{started}_{name}"
    run_dir.mkdir(parents=True)
    (run_dir / "rankings.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rankings)
    )
    meta = {
        "name": name,
        "queries": str(queries_path),
        "queries_meta": json.loads(Path(queries_path).read_text()).get("_meta"),
        "rooms": len({s.room_id for s in searches}),
        "catalog": cfg.rag.catalog,
        "index": index.meta,
        "embedders": {e: cfg.rag.embedders[e] for e in sorted({m.embedder for m in methods})},
        "hnsw": cfg.rag.hnsw,
        "rerankers": {
            r: cfg.evaluation.rerankers[r] for r in sorted({m.rerank for m in methods if m.rerank})
        },
        "git_commit": git_commit(),
        "python": platform.python_version(),
    }
    (run_dir / "corrida.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str)
    )
    (run_dir / "metricas.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    return run_dir
