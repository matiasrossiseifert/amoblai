"""Which products the catalog has. A catalog file (YAML) lists them in any of these ways:

    name: main
    items:                      # JSON-lines files, one product a line (below)
      - data/ikea/items.jsonl
    products:                   # product folders, one by one (each with a product.json)
      - data/products/chair-1
    product_dirs:               # every subfolder with a product.json
      - data/catalog/abo
    catalogs:                   # every product of these catalogs too
      - other.yaml
    categories:                 # optional: a product's type, where its record has it wrong
      abo-B0857JLP6K: stool
    kinds_file: kinds.yaml      # optional: {id: kind} (kinds.py)

A product, as a JSON line or a product.json:

    {"id": "...", "name": "...", "category": "chair", "kind": "desk chair",
     "dimensions_cm": {"width": 60, "depth": 55, "height": 90},
     "photos": ["photos/00.jpg", ...], ...any other field (colors, materials, price, url)}

`kind` and `dimensions_cm` are optional (without a size, the size filters let it through). In a
product.json, photos are relative to its folder and may be {"file", "is_primary"} objects (the
primary goes first); in a JSON-lines file, relative to the config's root. Every other path is
relative to the root too.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .kinds import KINDS

REQUIRED = ("id", "name", "category", "photos")


@dataclass
class Product:
    source: Path  # its folder (product.json) or its JSON-lines file
    info: dict  # the record, photos as absolute paths, the primary first

    @property
    def id(self) -> str:
        return self.info["id"]

    @property
    def category(self) -> str:
        return self.info["category"]

    @property
    def kind(self) -> str | None:
        return self.info.get("kind")

    def photos(self) -> list[Path]:
        return [Path(p) for p in self.info["photos"]]


@dataclass
class Catalog:
    name: str
    products: list[Product]


def _record(info: dict, base: Path, where: Path) -> dict:
    missing = [k for k in REQUIRED if not info.get(k)]
    if missing:
        raise ValueError(f"{where}: product {info.get('id')!r} has no {missing}")
    photos = sorted(
        info["photos"], key=lambda p: not (isinstance(p, dict) and p.get("is_primary", False))
    )
    files = [p["file"] if isinstance(p, dict) else p for p in photos]
    return {**info, "photos": [str(base / f) for f in files]}


def load_product(folder: Path) -> Product:
    info = json.loads((folder / "product.json").read_text())
    return Product(folder, _record(info, folder, folder / "product.json"))


def load_items(path: Path, root: Path) -> list[Product]:
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    return [Product(path, _record(r, root, path)) for r in rows]


def load_catalog(path: str | Path, root: str | Path = ".") -> Catalog:
    root = Path(root)

    def at(p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else root / p

    path = at(path)
    data = yaml.safe_load(path.read_text())
    folders = [at(x) for x in data.get("products") or []]
    for d in data.get("product_dirs") or []:
        folders += sorted(f.parent for f in at(d).glob("*/product.json"))
    products = [load_product(x) for x in folders]
    for f in data.get("items") or []:
        products += load_items(at(f), root)
    for sub in data.get("catalogs") or []:
        products += load_catalog(sub, root).products
    fixes = data.get("categories") or {}
    for p in products:
        if p.id in fixes:
            p.info = {**p.info, "category": fixes[p.id]}
    unknown = sorted(set(fixes) - {p.id for p in products})
    if unknown:
        raise ValueError(f"{path}: categories for products it doesn't have: {unknown}")
    if data.get("kinds_file"):
        kinds = yaml.safe_load(at(data["kinds_file"]).read_text()) or {}
        for p in products:
            if p.id in kinds:
                p.info = {**p.info, "kind": kinds[p.id]}
    bad = sorted({p.kind for p in products if p.kind is not None} - set(KINDS))
    if bad:
        raise ValueError(f"{path}: kinds not in kinds.py: {bad}")
    ids = [p.id for p in products]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise ValueError(f"{path}: the same product twice: {dup}")
    return Catalog(str(data.get("name", path.stem)), products)
