"""What a product is for, finer than its type: the search's first filter (a desk chair is not an
armchair). Each kind belongs to one type (a product's `category`); the catalog says each
product's kind (catalog.py) and the plan step names the kinds that would serve
(prompts/search_query_v2.md). Another catalog may need other kinds: edit this table."""

from __future__ import annotations

KINDS: dict[str, str] = {
    "desk chair": "chair",  # office, task, executive, guest; swivel or not
    "dining chair": "chair",  # upright, for a table; with or without arms
    "armchair": "chair",  # lounge, accent, club, wingback, barrel, recliner, rocker, glider
    "sofa": "sofa",
    "sofa bed": "sofa",
    "dining table": "table",
    "coffee table": "table",
    "side table": "table",  # end, accent, nesting
    "nightstand": "table",
    "console table": "table",
    "desk": "desk",
    "bed": "bed",
    "bookcase": "shelf",
    "wall shelf": "shelf",
    "sideboard": "cabinet",
    "TV stand": "cabinet",
    "storage cabinet": "cabinet",
    "file cabinet": "cabinet",
    "wardrobe": "cabinet",
    "dresser": "dresser",
    "ottoman": "ottoman",
    "bar stool": "stool",
    "low stool": "stool",
    "bench": "bench",
    "rug": "rug",  # area rugs, runners, hides (IKEA has them; the plan may ask for one)
}


def kinds_text() -> str:
    """The kinds grouped by type, one type a line, for the prompts."""
    by_type: dict[str, list[str]] = {}
    for k, t in KINDS.items():
        by_type.setdefault(t, []).append(k)
    return "\n".join(f"- {t}: {', '.join(ks)}" for t, ks in by_type.items())
