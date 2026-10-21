"""The indexing pipeline: each product's description and its vector, into the vector database.
`build_index` writes it to <cache_dir>/rag/:

  descriptions/<key>.json   one product's description. The key covers the describer (model,
                            prompt) and the product (its record, photos): a product is
                            described again only when one of them changes.
  vectors/<key>.npy         one text's vector, keyed by the embedder and the text (queries too).
  index/<catalog>-<describer>-<embedder>/
    chroma/                 ChromaDB: one record per product (vector, description, the
                            metadata of the filters), HNSW index in cosine space (store.py)
    items.jsonl             one product a line: id, source, name, category, kind,
                            dimensions_cm, photos (relative to the root), description
    index.json              what built it, when, and what that build cost
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from amoblai.catalog.loader import Product, load_catalog
from amoblai.config import Config
from amoblai.infra.budget import Ledger, check_spend, ledger_for
from amoblai.infra.http import ProviderError
from amoblai.rag.describe import Describer, get_describer
from amoblai.rag.embed import Embedder, get_embedder
from amoblai.rag.store import ChromaStore

# 2: items have a kind; 3: `source`, photos under the root; 4: the vectors in ChromaDB
INDEX_SCHEMA = "amoblai.index/4"


class NoFullDescription(ProviderError):
    """The model stopped before a full description (cut short, refused): paid, not kept."""


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:24]


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _rel(path: Path, root: Path) -> str:
    path, root = path.resolve(), root.resolve()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


@dataclass
class Index:
    path: Path
    meta: dict
    items: list[dict]
    vectors: np.ndarray  # (n, d), rows of length 1, in the order of `items`
    store: ChromaStore | None = None

    @classmethod
    def load(cls, path: Path) -> Index:
        if not (path / "index.json").exists():
            raise FileNotFoundError(f"no index at {path}: build it first (build_index)")
        meta = json.loads((path / "index.json").read_text())
        items = [json.loads(x) for x in (path / "items.jsonl").read_text().splitlines() if x]
        store = ChromaStore(path / "chroma")
        return cls(path, meta, items, store.vectors([it["id"] for it in items]), store)

    def nearest(
        self, query: np.ndarray, k: int, allowed: np.ndarray | None = None
    ) -> list[tuple[int, float]]:
        """Exact search: the k items nearest to `query` by cosine, best first, among the
        allowed ones (every vector, numpy). The baseline the vector database is compared to."""
        scores = self.vectors @ query
        if allowed is not None:
            scores = np.where(allowed, scores, -np.inf)
        order = np.argsort(-scores, kind="stable")[:k]
        return [(int(i), float(scores[i])) for i in order if np.isfinite(scores[i])]

    def query(self, query: np.ndarray, k: int, where: dict | None) -> list[tuple[int, float]]:
        """The vector database: the k items nearest to `query` (HNSW, cosine) among those the
        filters let through (`where`), best first."""
        row = {it["id"]: i for i, it in enumerate(self.items)}
        return [(row[pid], s) for pid, s in self.store.query(query, k, where)]


def catalog_sha(catalog) -> str:
    """What the filters read from the catalog: a changed type or kind means a stale index."""
    return _sha([(p.id, p.category, p.kind, p.info["dimensions_cm"]) for p in catalog.products])


def catalog_of(cfg: Config):
    return load_catalog(cfg.rag.catalog, cfg.root)


def index_is_current(cfg: Config) -> bool:
    f = index_path(cfg) / "index.json"
    if not f.exists():
        return False
    meta = json.loads(f.read_text())
    return meta.get("schema") == INDEX_SCHEMA and meta.get("catalog_sha") == catalog_sha(
        catalog_of(cfg)
    )


def index_path(cfg: Config) -> Path:
    name = catalog_of(cfg).name
    return Path(cfg.cache_dir) / "rag" / "index" / f"{name}-{cfg.rag.describer}-{cfg.rag.embedder}"


def open_index(cfg: Config) -> Index:
    return Index.load(index_path(cfg))


def describe_cached(
    product: Product, describer: Describer, cfg: Config, ledger: Ledger
) -> tuple[str, float]:
    """(description, what it cost now: 0 when it came from the cache)."""
    key_src = {
        "describer": describer.key(),
        "product": {k: v for k, v in product.info.items() if k != "photos"},
        "photos": [_file_sha(f) for f in product.photos()],
    }
    f = Path(cfg.cache_dir) / "rag" / "descriptions" / f"{_sha(key_src)}.json"
    if f.exists():
        return json.loads(f.read_text())["text"], 0.0
    check_spend(
        ledger,
        describer.estimate_cost(product),
        paid=describer.paid,
        allow_paid=cfg.budget.allow_paid,
        what=f"rag describer {describer.name}",
    )
    d = describer.describe(product)
    if describer.paid:
        ledger.record(
            step="rag.describe",
            provider=describer.name,
            model=d.model,
            product=product.id,
            cost_usd=d.cost_usd,
            cost_source=d.cost_source,
            cached=False,
        )
    status = d.meta.get("status", "completed")
    if status != "completed" or not d.text.strip():
        raise NoFullDescription(
            f"{describer.name}: no full description for {product.id} (status {status}, "
            f"{d.meta.get('incomplete_details') or d.meta.get('stop_reason')}); "
            f"${d.cost_usd:.4f} spent"
        )
    f.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "product": product.id,
        "text": d.text,
        "model": d.model,
        "cost_usd": d.cost_usd,
        "cost_source": d.cost_source,
        "meta": d.meta,
        "key_src": key_src,
    }
    f.write_text(json.dumps(rec, indent=2, default=str))
    return d.text, d.cost_usd


def vectors_cached(
    texts: list[str], embedder: Embedder, cfg: Config, ledger: Ledger
) -> tuple[np.ndarray, float]:
    """(n, d) vectors for `texts`, and what the new ones cost now."""
    root = Path(cfg.cache_dir) / "rag" / "vectors"
    files = [root / f"{_sha({'embedder': embedder.key(), 'text': t})}.npy" for t in texts]
    missing = [i for i, f in enumerate(files) if not f.exists()]
    cost = 0.0
    if missing:
        batch = [texts[i] for i in missing]
        check_spend(
            ledger,
            embedder.estimate_cost(batch),
            paid=embedder.paid,
            allow_paid=cfg.budget.allow_paid or "rag.embed" in cfg.budget.allow_paid_steps,
            what=f"rag embedder {embedder.name}",
        )
        e = embedder.embed(batch)
        if embedder.paid:
            ledger.record(
                step="rag.embed",
                provider=embedder.name,
                model=e.model,
                texts=len(batch),
                cost_usd=e.cost_usd,
                cost_source=e.cost_source,
                cached=False,
            )
        root.mkdir(parents=True, exist_ok=True)
        for i, v in zip(missing, e.vectors, strict=True):
            np.save(files[i], v)
        cost = e.cost_usd
    return np.stack([np.load(f) for f in files]), cost


def build_index(cfg: Config, log: Callable[[str], None] = print) -> Index:
    """Describe and embed every product of the catalog (only what the cache doesn't have).

    `rag.workers` products are described at once. A product the model doesn't describe in full
    is left out of the index (and said); any other error, the budget and the paid gate stop the
    whole build. With
    several workers the cap can be passed by at most that many calls already on their way."""
    catalog = catalog_of(cfg)
    if not catalog.products:
        raise ValueError(f"{cfg.rag.catalog}: the catalog has no products")
    describer = get_describer(cfg.rag.describer, cfg)
    embedder = get_embedder(cfg.rag.embedder, cfg)
    ledger = ledger_for(cfg.budget, describer.account)

    def one(p: Product) -> tuple[str, float] | None:
        try:
            return describe_cached(p, describer, cfg, ledger)
        except NoFullDescription as e:
            log(f"left out: {e}")
            return None

    with ThreadPoolExecutor(max(1, cfg.rag.workers)) as pool:
        texts = list(pool.map(one, catalog.products))
    items, cost, left_out = [], 0.0, 0
    for p, got in zip(catalog.products, texts, strict=True):
        if got is None:
            left_out += 1
            continue
        text, c = got
        cost += c
        if c:
            log(f"described {p.id} (${c:.4f})")
        items.append(
            {
                "id": p.id,
                "source": _rel(p.source, Path(cfg.root)),
                "name": p.info["name"],
                "category": p.category,
                "kind": p.kind,
                "dimensions_cm": p.info.get("dimensions_cm"),
                "photos": [_rel(f, Path(cfg.root)) for f in p.photos()],
                "description": text,
            }
        )
    if not items:
        raise ProviderError(f"{describer.name}: no product described; nothing to index")
    vectors, c = vectors_cached(
        [it["description"] for it in items], embedder, cfg, ledger_for(cfg.budget, embedder.account)
    )
    cost += c
    out = index_path(cfg)
    out.mkdir(parents=True, exist_ok=True)
    (out / "items.jsonl").write_text("".join(json.dumps(it) + "\n" for it in items))
    store = ChromaStore(out / "chroma")
    store.create(items, vectors, cfg.rag.hnsw)
    (out / "vectors.npy").unlink(missing_ok=True)  # el índice de antes de ChromaDB
    meta = {
        "schema": INDEX_SCHEMA,
        "catalog": catalog.name,
        "catalog_file": str(cfg.rag.catalog),
        "catalog_sha": catalog_sha(catalog),
        "describer": {"name": describer.name, "key": describer.key()},
        "embedder": {"name": embedder.name, "key": embedder.key()},
        "vector_store": {"kind": "chromadb", "space": "cosine", "hnsw": cfg.rag.hnsw},
        "products": len(items),
        "left_out": left_out,
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cost_usd": round(cost, 6),
    }
    (out / "index.json").write_text(json.dumps(meta, indent=2))
    return Index(out, meta, items, vectors, store)
