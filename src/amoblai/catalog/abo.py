"""A second catalog to compare with IKEA's: Amazon Berkeley Objects (ABO; Collins et al., CVPR
2022; CC BY-NC 4.0). Real Amazon listings (2019-2020) with the seller's text, measurements for
most of them and photos at up to 2000 px; the IKEA dataset's photos are 500 px and its seats
have no measurements.

`build` reads ABO's listing metadata (downloaded to `datos/dataset/abo/`, never committed),
keeps the US English listings of the kinds of products IKEA's catalog has, one per model (a
sofa comes in ten colors; one is enough to compare), with a large enough photo, up to a cap per
kind, and writes them in the catalog's JSON-lines format (catalog/loader.py). The kind it gives
each product is a first guess from the listing's type and name: the describer looks at the
photo and fixes it (catalog/describe_api.py), and the products it says are out of scope leave.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import logging
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from PIL import Image

from amoblai.catalog.kinds import KINDS

log = logging.getLogger(__name__)

BUCKET = "https://amazon-berkeley-objects.s3.amazonaws.com"
LISTINGS = [f"listings/metadata/listings_{c}.json.gz" for c in "0123456789abcdef"]
IMAGES = "images/metadata/images.csv.gz"
MIN_SIDE = 800  # the photo's long side, in px

# (kind, ABO product types, words of which one must be in the name, words that rule it out).
# The first rule that matches wins, so the narrow ones go first. "" matches any name.
RULES: list[tuple[str, set[str], list[str], list[str]]] = [
    ("sofa bed", {"SOFA"}, ["sleeper", "sofa bed", "futon", "convertible"], []),
    ("desk chair", {"CHAIR"}, ["office", "desk chair", "task", "executive", "gaming"], []),
    ("bar stool", {"STOOL_SEATING", "CHAIR"}, ["bar stool", "counter stool", "barstool"], []),
    ("dining chair", {"CHAIR"}, ["dining", "side chair", "kitchen chair"], []),
    (
        "armchair",
        {"CHAIR", "SOFA"},
        [
            "accent",
            "armchair",
            "arm chair",
            "lounge",
            "club",
            "recliner",
            "rocking",
            "wingback",
            "barrel",
            "slipper chair",
            "swivel chair",
            "chaise",
        ],
        ["sectional", "loveseat"],
    ),
    ("sofa", {"SOFA"}, [""], ["chair"]),
    ("coffee table", {"TABLE", "HOME_FURNITURE_AND_DECOR"}, ["coffee table", "cocktail table"], []),
    (
        "console table",
        {"TABLE", "HOME_FURNITURE_AND_DECOR"},
        ["console table", "sofa table", "entryway table", "hall table"],
        [],
    ),
    (
        "nightstand",
        {"TABLE", "HOME_FURNITURE_AND_DECOR", "CABINET"},
        ["nightstand", "night stand", "bedside"],
        [],
    ),
    (
        "side table",
        {"TABLE", "HOME_FURNITURE_AND_DECOR"},
        ["side table", "end table", "accent table", "nesting table", "c-table", "drink table"],
        [],
    ),
    ("dining table", {"TABLE"}, ["dining", "kitchen table", "pedestal table"], []),
    ("desk", {"DESK", "TABLE", "HOME_FURNITURE_AND_DECOR"}, ["desk"], ["lamp", "organizer"]),
    ("rug", {"RUG"}, [""], ["pad", "mat ", "doormat", "bath"]),
    ("floor lamp", {"LAMP", "HOME_LIGHTING_AND_LAMPS"}, ["floor lamp", "floor"], []),
    ("desk lamp", {"LAMP", "HOME_LIGHTING_AND_LAMPS"}, ["desk lamp", "task lamp", "architect"], []),
    ("table lamp", {"LAMP", "HOME_LIGHTING_AND_LAMPS"}, ["table lamp", "lamp"], ["bulb"]),
    ("pendant lamp", {"LIGHT_FIXTURE", "LAMP"}, ["pendant", "chandelier"], []),
    ("ceiling lamp", {"LIGHT_FIXTURE"}, ["flush mount", "flushmount", "ceiling"], []),
    ("wall lamp", {"LIGHT_FIXTURE", "LAMP"}, ["sconce", "wall light", "wall lamp"], []),
    ("bench", {"BENCH", "HOME_FURNITURE_AND_DECOR", "OTTOMAN"}, ["bench"], []),
    ("ottoman", {"OTTOMAN"}, [""], ["bench"]),
    ("low stool", {"STOOL_SEATING"}, [""], []),
    (
        "TV stand",
        {"CABINET", "HOME_FURNITURE_AND_DECOR", "TABLE"},
        ["tv stand", "tv console", "media console", "entertainment center", "media cabinet"],
        [],
    ),
    ("sideboard", {"CABINET", "HOME_FURNITURE_AND_DECOR"}, ["sideboard", "buffet", "credenza"], []),
    (
        "dresser",
        {"DRESSER", "HOME_FURNITURE_AND_DECOR", "CABINET"},
        ["dresser", "chest of drawers", "drawer chest"],
        [],
    ),
    (
        "display cabinet",
        {"CABINET", "HOME_FURNITURE_AND_DECOR"},
        ["curio", "display cabinet", "glass door"],
        [],
    ),
    (
        "storage cabinet",
        {"CABINET", "HOME_FURNITURE_AND_DECOR"},
        ["cabinet", "armoire", "cupboard"],
        ["bathroom", "medicine", "file"],
    ),
    (
        "wall shelf",
        {"SHELF", "HOME_FURNITURE_AND_DECOR", "HOME"},
        ["wall shelf", "floating shelf", "wall-mounted shelf", "wall mounted"],
        [],
    ),
    (
        "bookcase",
        {"SHELF", "HOME_FURNITURE_AND_DECOR"},
        ["bookcase", "bookshelf", "shelving unit", "etagere", "ladder shelf", "shelf"],
        [],
    ),
    (
        "cushion",
        {"PILLOW", "HOME_BED_AND_BATH", "HOME", "HOME_FURNITURE_AND_DECOR"},
        ["throw pillow", "decorative pillow", "pillow cover", "cushion", "lumbar pillow"],
        ["bed pillow", "sleep", "memory foam", "seat cushion", "chair pad"],
    ),
    (
        "throw",
        {"HOME_BED_AND_BATH", "HOME", "BLANKET", "HOME_FURNITURE_AND_DECOR"},
        ["throw blanket", "throw"],
        ["pillow"],
    ),
    (
        "curtains",
        {"HOME", "HOME_BED_AND_BATH", "CURTAIN", "HOME_FURNITURE_AND_DECOR"},
        ["curtain", "drape", "window panel"],
        ["shower", "rod"],
    ),
    ("wall art", {"WALL_ART"}, [""], ["decal", "sticker"]),
    (
        "mirror",
        {"HOME", "HOME_FURNITURE_AND_DECOR", "MIRROR", "HOME_MIRROR"},
        ["mirror"],
        ["makeup", "car"],
    ),
    (
        "plant pot",
        {"PLANTER", "HOME", "HOME_FURNITURE_AND_DECOR"},
        ["planter", "plant pot", "flower pot"],
        [],
    ),
    ("vase", {"HOME", "HOME_FURNITURE_AND_DECOR", "VASE"}, ["vase"], []),
    (
        "basket",
        {"HOME", "HOME_FURNITURE_AND_DECOR", "BASKET", "STORAGE_BASKET"},
        ["basket"],
        ["laundry hamper", "bike"],
    ),
    (
        "candle holder",
        {"HOME", "HOME_FURNITURE_AND_DECOR", "CANDLE_HOLDER"},
        ["candle holder", "candlestick", "lantern", "candle"],
        [],
    ),
    ("wall clock", {"HOME", "CLOCK", "HOME_FURNITURE_AND_DECOR"}, ["wall clock"], []),
    (
        "plant",
        {"HOME", "ARTIFICIAL_PLANT", "HOME_FURNITURE_AND_DECOR", "PLANT"},
        ["artificial plant", "faux plant", "artificial tree", "faux tree", "fake plant"],
        [],
    ),
]

# What is not for a living or dining room, whatever its type says.
NEVER = re.compile(
    r"\b(outdoor|patio|garden|kid'?s|kids|children'?s|toddler|baby|nursery|dog|cat|pet|car|"
    r"replacement|slipcover|cover set|furniture cover|bathroom|shower|office supplies|"
    r"hardware|bulb|bulbs|part|parts|kit)\b",
    re.I,
)

# How many of each kind: about the size of IKEA's catalog (819 products), a few more of what
# a living or dining room is made of (IKEA has 31 sofas and 24 armchairs).
CAPS: dict[str, int] = {
    "sofa": 45,
    "sofa bed": 8,
    "armchair": 45,
    "dining chair": 40,
    "desk chair": 14,
    "coffee table": 30,
    "side table": 30,
    "nightstand": 8,
    "dining table": 30,
    "console table": 10,
    "desk": 18,
    "rug": 90,
    "floor lamp": 20,
    "table lamp": 25,
    "desk lamp": 10,
    "pendant lamp": 25,
    "ceiling lamp": 8,
    "wall lamp": 12,
    "bench": 14,
    "ottoman": 20,
    "bar stool": 6,
    "low stool": 10,
    "TV stand": 12,
    "sideboard": 8,
    "dresser": 25,
    "display cabinet": 6,
    "storage cabinet": 18,
    "wall shelf": 20,
    "bookcase": 30,
    "cushion": 50,
    "throw": 15,
    "curtains": 15,
    "wall art": 25,
    "mirror": 28,
    "plant pot": 25,
    "vase": 15,
    "basket": 20,
    "candle holder": 10,
    "wall clock": 10,
    "plant": 6,
}

COLORS = re.compile(
    r"\b(black|white|grey|gray|beige|blue|navy|green|red|pink|yellow|orange|brown|tan|cream|"
    r"ivory|gold|silver|brass|bronze|copper|natural|walnut|oak|espresso|charcoal|teal|"
    r"turquoise|purple|multi|multicolor|light|dark|velvet|linen|leather|fabric)\b",
    re.I,
)


def _en(values: list[dict] | None) -> str | None:
    for v in values or []:
        if str(v.get("language_tag", "")).startswith("en"):
            return str(v.get("value", "")).strip()
    return None


def guess_kind(product_type: str, name: str) -> str | None:
    low = f" {name.lower()} "
    if NEVER.search(low):
        return None
    for kind, types, words, nots in RULES:
        if (
            product_type in types
            and any(w in low for w in words)
            and not any(n in low for n in nots)
        ):
            return kind
    return None


def family(brand: str, name: str) -> str:
    """One key per model: the name without colors, sizes and numbers (variants differ in those)."""
    low = re.sub(r"[\d\"'”″]+(\s*(in|inch|inches|cm|ft|x))?", " ", name.lower())
    low = COLORS.sub(" ", low.split(",")[0])
    return f"{brand.lower()}|{' '.join(re.sub(r'[^a-z ]', ' ', low).split()[:7])}"


def dimensions(listing: dict) -> dict[str, float] | None:
    """Width (the longer side on the floor), depth and height in cm; None if it has none."""
    d = listing.get("item_dimensions") or {}

    def cm(key: str) -> float | None:
        v = (d.get(key) or {}).get("normalized_value") or d.get(key) or {}
        if not v.get("value"):
            return None
        unit = str(v.get("unit", "inches")).lower()
        f = {"inches": 2.54, "centimeters": 1.0, "feet": 30.48, "millimeters": 0.1}.get(unit)
        return round(float(v["value"]) * f, 1) if f else None

    a, b, h = cm("length"), cm("width"), cm("height")
    floor = sorted(x for x in (a, b) if x)
    if not floor and not h:
        return None
    out = {}
    if floor:
        out["width"] = floor[-1]
        if len(floor) == 2:
            out["depth"] = floor[0]
    if h:
        out["height"] = h
    return out


def download_metadata(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for rel in [*LISTINGS, IMAGES]:
        f = dest / Path(rel).name
        if f.exists():
            continue
        log.info("Descargando %s", rel)
        r = httpx.get(f"{BUCKET}/{rel}", timeout=300, follow_redirects=True)
        r.raise_for_status()
        f.write_bytes(r.content)


def _rank(item_id: str) -> str:
    return hashlib.sha256(item_id.encode()).hexdigest()  # a fixed shuffle


def select(meta_dir: Path, caps: dict[str, int] = CAPS) -> list[dict]:
    """The catalog's products from the listing metadata: one per model, up to `caps`."""
    sizes: dict[str, tuple[int, int, str]] = {}
    with gzip.open(meta_dir / Path(IMAGES).name, "rt") as fh:
        for row in csv.DictReader(fh):
            sizes[row["image_id"]] = (int(row["width"]), int(row["height"]), row["path"])
    by_kind: dict[str, dict[str, dict]] = defaultdict(dict)
    for rel in LISTINGS:
        with gzip.open(meta_dir / Path(rel).name, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("country") != "US":
                    continue
                name = _en(r.get("item_name"))
                ptype = (r.get("product_type") or [{}])[0].get("value", "")
                img = sizes.get(r.get("main_image_id", ""))
                if not name or not img or max(img[0], img[1]) < MIN_SIDE:
                    continue
                kind = guess_kind(ptype, name)
                if kind is None or kind not in caps:
                    continue
                brand = _en(r.get("brand")) or ""
                key = family(brand, name)
                dims = dimensions(r)
                item = {
                    "id": f"abo-{r['item_id']}",
                    "name": name,
                    "category": KINDS[kind],
                    "kind": kind,
                    "dimensions_cm": dims,
                    "photos": [f"datos/dataset/abo/images/{r['item_id']}.jpg"],
                    "brand": brand,
                    "product_type": ptype,
                    "colors": [c for c in [_en(r.get("color"))] if c],
                    "materials": [m for m in [_en(r.get("material"))] if m],
                    "style": _en(r.get("style")),
                    "description": " ".join(
                        str(b.get("value", "")).strip()
                        for b in r.get("bullet_point") or []
                        if str(b.get("language_tag", "")).startswith("en")
                    )[:1500],
                    "image_path": img[2],
                    "image_px": [img[0], img[1]],
                }
                old = by_kind[kind].get(key)
                # one per model: the one with measurements, then a fixed pick
                if old is None or (bool(dims), _rank(item["id"])) > (
                    bool(old["dimensions_cm"]),
                    _rank(old["id"]),
                ):
                    by_kind[kind][key] = item
    out = []
    for kind, cap in caps.items():
        models = sorted(by_kind[kind].values(), key=lambda x: _rank(x["id"]))
        out += models[:cap]
    log.info("ABO: %s", dict(Counter(x["kind"] for x in out)))
    return out


def download_images(items: list[dict], root: Path, max_side: int = 1024, workers: int = 16) -> int:
    """The main photo of each product, at most `max_side` px (what the LLM and the image model
    get anyway). Returns how many it downloaded."""

    def one(it: dict) -> int:
        dst = root / it["photos"][0]
        if dst.exists():
            return 0
        r = httpx.get(f"{BUCKET}/images/original/{it['image_path']}", timeout=120)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, quality=92)
        return 1

    with ThreadPoolExecutor(workers) as pool:
        return sum(pool.map(one, items))


def write_items(items: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items))


def drop_shared_photos(items: list[dict], root: Path) -> list[dict]:
    """Without the products whose photo isn't theirs: a photo three or more products share is a
    placeholder ("image coming soon") or a swatch; of two that share one, the first stays."""
    by_photo: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        by_photo[hashlib.md5((root / it["photos"][0]).read_bytes()).hexdigest()].append(it)
    keep = {g[0]["id"] for g in by_photo.values() if len(g) <= 2}
    return [it for it in items if it["id"] in keep]
