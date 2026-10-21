"""The catalog search test: several ways of searching, over the same requests, graded.

    <eval_dir>/cases.yaml       requests the way users write them, and the room each is for
    <eval_dir>/queries.json     the searches each request became (the plan step's prompt):
                                {case: {"pieces": [{piece, categories, kinds, max_*_cm, query}]}}
    <eval_dir>/judgments.jsonl  {"case", "piece", "product", "grade", "by"}: how well a product
                                does for that piece, graded from its photo, not from our text.
                                2 good, 1 acceptable, 0 wrong.

A method is an embedder, the text of each product it embeds, and whether the hard filters
apply. `score` gives each method's ok@k, good@k, first_ok and nDCG@k; `pool` the products the
methods brought that nobody has graded yet, to grade them. (YouSeeYouBuy: evals/rag/, D-063.)
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from .budget import ledger_for
from .catalog import Product
from .config import Config
from .describe import FieldsDescriber
from .embed import get_embedder
from .filters import Filters
from .index import Index, build_index, catalog_of, vectors_cached


def _drop(text: str, labels: tuple[str, ...]) -> str:
    return "".join(ln + "\n" for ln in text.splitlines() if not ln.startswith(labels))


TEXTS: dict[str, Callable[[dict, Product], str]] = {
    # our eight lines
    "description": lambda it, p: it["description"],
    # the store's name before them (brand, sizes, marketing words)
    "name+description": lambda it, p: f"Name: {it['name']}\n{it['description']}",
    # without the mood and the "goes with" lines
    "description-core": lambda it, p: _drop(it["description"], ("Feel:", "Goes with:")),
    # the seller's text instead of ours: name, colors, materials, bullet points
    "seller": lambda it, p: FieldsDescriber().describe(p).text,
}


@dataclass
class Method:
    embedder: str
    text: str = "description"
    filters: bool = True


METHODS = {
    "hashing": Method("hashing"),
    "bge": Method("bge"),
    "bge+name": Method("bge", "name+description"),
    "bge-core": Method("bge", "description-core"),
    "bge-seller": Method("bge", "seller"),
    "bge-nofilter": Method("bge", filters=False),
    "qwen3": Method("qwen3"),
    "openai": Method("openai"),  # paid: text-embedding-3-large
}


@dataclass
class Search:
    case: str
    piece: int
    spec: dict  # one piece of queries.json

    def filters(self) -> Filters:
        s = self.spec
        return Filters(
            categories=s.get("categories") or [],
            kinds=s.get("kinds") or [],
            max_width_cm=s.get("max_width_cm"),
            max_depth_cm=s.get("max_depth_cm"),
            max_height_cm=s.get("max_height_cm"),
        )


def load_searches(eval_dir: Path) -> tuple[dict, list[Search]]:
    cases = {c["id"]: c for c in yaml.safe_load((eval_dir / "cases.yaml").read_text())["cases"]}
    queries = json.loads((eval_dir / "queries.json").read_text())
    searches = [
        Search(case, i, spec)
        for case in cases
        for i, spec in enumerate(queries.get(case, {}).get("pieces", []))
    ]
    return cases, searches


def load_judgments(eval_dir: Path) -> dict[tuple[str, int, str], int]:
    f = eval_dir / "judgments.jsonl"
    if not f.exists():
        return {}
    rows = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    return {(r["case"], int(r["piece"]), r["product"]): int(r["grade"]) for r in rows}


def run(cfg: Config, methods: list[str], searches: list[Search], k: int) -> dict[str, list]:
    """{method: [the ids of the top k, one list per search]}."""
    index = build_index(cfg, log=lambda _: None)  # the catalog and its descriptions
    products = {p.id: p for p in catalog_of(cfg).products}
    out = {}
    for name in methods:
        m = METHODS[name]
        embedder = get_embedder(m.embedder, cfg)
        ledger = ledger_for(cfg.budget, embedder.account)
        texts = [TEXTS[m.text](it, products[it["id"]]) for it in index.items]
        docs, _ = vectors_cached(texts, embedder, cfg, ledger)
        queries, _ = vectors_cached([s.spec["query"] for s in searches], embedder, cfg, ledger)
        ranked = Index(index.path, index.meta, index.items, docs)
        out[name] = []
        for s, q in zip(searches, queries, strict=True):
            f = s.filters() if m.filters else Filters()
            allowed = np.array([f.allows(it) for it in index.items], bool)
            out[name].append([index.items[i]["id"] for i, _ in ranked.nearest(q, k, allowed)])
    return out


def ndcg(grades: list[int], ideal: list[int], k: int) -> float:
    def dcg(g):
        return sum((2**x - 1) / np.log2(i + 2) for i, x in enumerate(g[:k]))

    best = dcg(sorted(ideal, reverse=True))
    return dcg(grades) / best if best > 0 else 0.0


def score(results: dict, searches: list[Search], judged: dict, k: int) -> dict[str, dict]:
    """Per method: `ok@k` the share of the top k that is good or acceptable, `good@k` the share
    that is good, `first_ok` how often the first is good or acceptable, `ndcg@k` against every
    product graded for that search, `ungraded` the results nobody graded (counted as wrong)."""
    table = {}
    for name, lists in results.items():
        ok = good = first = nd = 0.0
        ungraded = 0
        for s, ids in zip(searches, lists, strict=True):
            g = []
            for pid in ids:
                key = (s.case, s.piece, pid)
                ungraded += key not in judged
                g.append(judged.get(key, 0))
            g += [0] * (k - len(g))  # fewer than k passed the filters
            ok += sum(x >= 1 for x in g) / k
            good += sum(x == 2 for x in g) / k
            first += g[0] >= 1
            ideal = [v for (c, i, _), v in judged.items() if (c, i) == (s.case, s.piece)]
            nd += ndcg(g, ideal, k)
        n = len(searches)
        table[name] = {
            f"ok@{k}": round(ok / n, 3),
            f"good@{k}": round(good / n, 3),
            "first_ok": round(first / n, 3),
            f"ndcg@{k}": round(nd / n, 3),
            "ungraded": ungraded,
        }
    return table


def pool(
    results: dict, searches: list[Search], cases: dict, judged: dict, index: Index, root: Path
) -> list:
    """What the methods brought that nobody graded: one row per (search, product)."""
    items = {it["id"]: it for it in index.items}
    rows, seen = [], set()
    for lists in results.values():
        for s, ids in zip(searches, lists, strict=True):
            for pid in ids:
                key = (s.case, s.piece, pid)
                if key in judged or key in seen:
                    continue
                seen.add(key)
                it = items[pid]
                limits = {d: s.spec.get(f"max_{d}_cm") for d in ("width", "depth", "height")}
                rows.append(
                    {
                        "case": s.case,
                        "piece": s.piece,
                        "request": cases[s.case]["request"],
                        "room": cases[s.case]["room"],
                        "needed": s.spec["piece"],
                        "types": s.spec.get("categories"),
                        "limits_cm": {d: v for d, v in limits.items() if v},
                        "product": pid,
                        "name": it["name"],
                        "dimensions_cm": it["dimensions_cm"],
                        "photo": str(root / it["photos"][0]),
                    }
                )
    return rows
