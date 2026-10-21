"""Fixtures: un dataset IKEA sintético y el catálogo armado con él (sin red)."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from amoblai.config import Config, RagConfig

ROOT = Path(__file__).resolve().parents[1]
ROOM_ID = "ikea-living-test__1-s4.jpg"

# SKU -> (type, color, size, texto de las ocho líneas)
PRODUCTS = {
    "100.000.01": (
        "Three-seat sofa",
        (200, 30, 30),
        "200x90x80 cm",
        "Type: three-seat sofa\nUse: lounging; living room\nStyle: modern\nMaterials: red fabric, wooden legs\nColors: bright red\nShape: boxy, low arms, long seat\nFeel: bold, cozy\nGoes with: white walls; modern living rooms",
    ),
    "100.000.02": (
        "Two-seat sofa",
        (30, 30, 200),
        "",
        "Type: two-seat sofa\nUse: lounging; small living room\nStyle: minimalist\nMaterials: blue velvet\nColors: deep blue\nShape: compact, rounded arms\nFeel: calm, soft\nGoes with: grey walls; minimalist rooms",
    ),
    "100.000.03": (
        "Chair",
        (30, 160, 30),
        "",
        "Type: dining chair, slatted back\nUse: dining; dining room\nStyle: Scandinavian\nMaterials: green painted beech\nColors: forest green\nShape: slatted back, four legs\nFeel: fresh, light\nGoes with: light wood tables; Scandinavian rooms",
    ),
    "100.000.04": (
        "Easy chair",
        (230, 200, 40),
        "",
        "Type: armchair, rattan lounge\nUse: reading; living room\nStyle: bohemian\nMaterials: rattan\nColors: honey yellow\nShape: round tub back, low seat\nFeel: relaxed, warm\nGoes with: plants, jute; bohemian rooms",
    ),
    "100.000.05": (
        "Coffee table",
        (120, 70, 20),
        "90x55x45 cm",
        "Type: coffee table, oak\nUse: serving; living room\nStyle: rustic\nMaterials: solid oak\nColors: warm brown wood\nShape: rectangular top, thick legs\nFeel: sturdy, warm\nGoes with: leather sofas; rustic rooms",
    ),
    "100.000.06": (
        "Rug, flatwoven",
        (150, 150, 230),
        "133x195 cm",
        "Type: rug, flatwoven stripes\nUse: covering floors; living room\nStyle: coastal\nMaterials: cotton\nColors: light blue, white\nShape: rectangular, thin\nFeel: airy, fresh\nGoes with: white sofas; coastal rooms",
    ),
    "100.000.07": ("Table lamp", (250, 250, 120), "", ""),  # fuera del alcance
    "100.000.08": (
        "Table",
        (80, 80, 80),
        "120x60x75 cm",
        "Type: desk, simple top on trestles\nUse: working at a desk; home office\nStyle: minimalist\nMaterials: grey laminate\nColors: grey\nShape: flat top, trestle legs\nFeel: plain, practical\nGoes with: white walls; home offices",
    ),
}
IN_ROOM = ("100.000.01", "100.000.03", "100.000.05", "100.000.06")


def _solid(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    ImageDraw.Draw(img).rectangle([12, 12, size - 12, size - 12], fill=color)
    return img


@pytest.fixture
def dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "ikea"
    text = root / "text_data"
    text.mkdir(parents=True)
    products, img_to_desc = {}, {}
    for i, (sku, (ptype, color, size, _)) in enumerate(PRODUCTS.items()):
        folder = "couch" if "sofa" in ptype.lower() else "objects"
        path = root / "images" / folder / f"{sku}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        _solid(color).save(path, quality=95)
        products[sku] = {
            "name": f"PROD{i}",
            "type": ptype,
            "color": "Red,oak",
            "size": size,
            "img": f"images/mirror/{sku}.jpg",  # ruta anotada distinta de la real, como en IKEA
            "desc": "View more product information A product.",
        }
        img_to_desc[f"/static/images/{sku}.jpg"] = {"desc": "A product.", "name": f"PROD{i}"}
    rooms = root / "images" / "room_scenes"
    rooms.mkdir(parents=True)
    Image.new("RGB", (320, 240), (180, 180, 170)).save(rooms / ROOM_ID)
    item_to_room = {f"images/couch/{s}.jpg": [f"images/room_scenes/{ROOM_ID}"] for s in IN_ROOM}
    pickles = {
        "products_dict.p": products,
        "img_to_desc.p": img_to_desc,
        "categories_dict.p": {ROOM_ID: "Living Room"},
        "item_to_room.p": item_to_room,
        "room_to_items.p": {},
        "categories_images_dict.p": {},
    }
    for name, obj in pickles.items():
        (text / name).write_bytes(pickle.dumps(obj, protocol=2))
    return root


@pytest.fixture
def catalog_dir(tmp_path: Path, dataset_root: Path) -> Path:
    """El catálogo armado como lo arma `amoblai catalogo`, con descripciones falsas."""
    from amoblai.catalog.ikea import build_catalog_items, write_catalog_files

    out = tmp_path / "catalogo"
    items = build_catalog_items(
        dataset_root, ROOT / "datos" / "configs" / "categories.yaml", out / "items.jsonl"
    )
    lots = out / "descripciones"
    lots.mkdir(parents=True)
    with (lots / "lote_01.jsonl").open("w") as fh:
        for it in items:
            text = PRODUCTS[it["id"]][3]
            fh.write(
                json.dumps(
                    {
                        "id": it["id"],
                        "kind": it["kind"],
                        "text": text,
                        "by": "test",
                        "prompt": "describe_product_v2@test",
                    }
                )
                + "\n"
            )
    (out / "correcciones.yaml").write_text(
        '"100.000.08": {category: desk, kind: desk, motivo: "es un escritorio"}\n'
    )
    write_catalog_files(
        out / "items.jsonl",
        lots,
        out / "descripciones.jsonl",
        out / "kinds.yaml",
        out / "correcciones.yaml",
        out / "ikea.yaml",
    )
    return out


CLAUDE = {
    "kind": "anthropic",
    "model": "claude-opus-5-5",
    "effort": "medium",
    "models": {
        "claude-opus-5-5": {"usd_per_m": {"input": 4.0, "output": 20.0}, "estimate_usd": 0.15}
    },
}


@pytest.fixture
def cfg(tmp_path: Path, catalog_dir: Path) -> Config:
    return Config(
        root=str(tmp_path),
        cache_dir=str(tmp_path / "cache"),
        runs_dir=str(tmp_path / "runs"),
        rag=RagConfig(
            catalog=str(catalog_dir / "ikea.yaml"),
            describer="written",
            describers={
                "written": {"kind": "written", "file": str(catalog_dir / "descripciones.jsonl")},
                "fields": {"kind": "fields"},
            },
            embedder="hashing",
            embedders={"hashing": {"kind": "hashing", "dim": 1024}},
        ),
        furnish={
            "llm": CLAUDE,
            "generator": "manual",
            "generators": {
                "manual": {"kind": "manual"},
                "nano_banana_2": {
                    "kind": "amoblai.furnish.image_models:FalNanoBanana",
                    "usd_per_image": {"1K": 0.08},
                    "poll_s": 0,
                },
            },
        },
        budget={
            "max_usd_total": 0.0,
            "accounts": {"anthropic": 1.0, "fal": 0.10},
            "ledger": str(tmp_path / "gastos.jsonl"),
        },
    )
