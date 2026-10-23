"""What a product is for, finer than its type: the search's first filter (a desk chair is not an
armchair). Each kind belongs to one type (a product's `category`); the catalog says each
product's kind (catalog.py) and the plan step names the kinds that would serve
(prompts/search_query_v3.md). Another catalog may need other kinds: edit this table."""

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
    "bookcase": "shelf",  # freestanding, open or with a few doors: bookcases, shelving units
    "wall shelf": "shelf",  # shelves and ledges hung on the wall
    "sideboard": "cabinet",
    "TV stand": "cabinet",
    "display cabinet": "cabinet",  # glass doors
    "storage cabinet": "cabinet",
    "file cabinet": "cabinet",  # drawer units for a desk
    "wardrobe": "cabinet",
    "dresser": "dresser",  # chests of drawers
    "ottoman": "ottoman",  # footstools and poufs
    "bar stool": "stool",
    "low stool": "stool",
    "bench": "bench",
    "rug": "rug",  # area rugs, runners, hides (IKEA has them; the plan may ask for one)
    "pendant lamp": "lamp",  # hangs from the ceiling
    "ceiling lamp": "lamp",  # mounted flush on the ceiling
    "floor lamp": "lamp",
    "table lamp": "lamp",
    "desk lamp": "lamp",  # work lamps, adjustable arm or head
    "wall lamp": "lamp",  # sconces, clamp spotlights
    "cushion": "deco",  # throw pillows and their covers
    "throw": "deco",  # blankets for a sofa or a bed
    "curtains": "deco",
    "vase": "deco",
    "plant pot": "deco",  # pots and planters
    "plant": "deco",  # potted plants, real or artificial
    "picture frame": "deco",
    "wall art": "deco",  # prints and pictures
    "mirror": "deco",
    "wall clock": "deco",
    "basket": "deco",
    "candle holder": "deco",  # candlesticks, lanterns, candles
}


def kinds_text() -> str:
    """The kinds grouped by type, one type a line, for the prompts."""
    by_type: dict[str, list[str]] = {}
    for k, t in KINDS.items():
        by_type.setdefault(t, []).append(k)
    return "\n".join(f"- {t}: {', '.join(ks)}" for t, ks in by_type.items())
