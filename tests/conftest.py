"""Fixtures: un dataset IKEA sintético y componentes falsos (sin red ni modelos)."""

from __future__ import annotations

import pickle
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from amoblai.categories import CategoryMap
from amoblai.components import RetrievalComponents
from amoblai.config import AppConfig, load_config
from amoblai.data.catalog import Catalog
from amoblai.data.ikea import IkeaDataset
from amoblai.embeddings.base import l2_normalize
from amoblai.indexing.indexer import build_index, collection_name
from amoblai.indexing.splitter import split_catalog
from amoblai.retrieval.reranker import NoopReranker
from amoblai.retrieval.retriever import Retriever
from amoblai.vectorstore.chroma import ChromaVectorStore
from amoblai.vision.background import NoBackgroundRemoval
from amoblai.vision.boxes import Box
from amoblai.vision.detection import Detection

ROOT = Path(__file__).resolve().parents[1]

# SKU → (type, color RGB). Los colores son la "identidad visual" para el embedder falso.
PRODUCTS = {
    "100.000.01": ("Three-seat sofa", (200, 30, 30)),
    "100.000.02": ("Two-seat sofa", (30, 30, 200)),
    "100.000.03": ("Chair", (30, 160, 30)),
    "100.000.04": ("Chair", (230, 200, 40)),
    "100.000.05": ("Coffee table", (120, 70, 20)),
    "100.000.06": ("Rug, flatwoven", (150, 150, 230)),
    "100.000.07": ("Table lamp", (250, 250, 120)),
    "100.000.08": ("Armchair", (240, 120, 200)),
}
ROOM_ID = "ikea-living-test__1-s4.jpg"
ROOM_BOXES = {
    "100.000.01": Box(20, 120, 180, 220),
    "100.000.03": Box(220, 100, 280, 220),
    "100.000.05": Box(120, 230, 230, 290),
}


def _solid(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    img = Image.new("RGB", (size, size), (255, 255, 255))
    ImageDraw.Draw(img).rectangle([12, 12, size - 12, size - 12], fill=color)
    return img


def make_room_image() -> Image.Image:
    img = Image.new("RGB", (320, 320), (180, 180, 170))
    draw = ImageDraw.Draw(img)
    for sku, box in ROOM_BOXES.items():
        draw.rectangle(box.to_int(), fill=PRODUCTS[sku][1])
    return img


@pytest.fixture
def dataset_root(tmp_path: Path) -> Path:
    root = tmp_path / "ikea"
    text = root / "text_data"
    text.mkdir(parents=True)
    products = {}
    img_to_desc = {}
    for i, (sku, (ptype, color)) in enumerate(PRODUCTS.items()):
        folder = "couch" if "sofa" in ptype.lower() else "objects"
        path = root / "images" / folder / f"{sku}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        _solid(color).save(path, quality=95)
        # Ruta anotada distinta de la real, como en el dataset original.
        products[sku] = {
            "name": f"PROD{i}",
            "type": ptype,
            "color": "red",
            "size": "200x90x80 cm" if i % 2 == 0 else "",
            "img": f"images/mirror/{sku}.jpg",
            "desc": "View more product information Un producto.",
        }
        img_to_desc[f"/static/images/{sku}.jpg"] = {"desc": "Un producto.", "name": f"PROD{i}"}
    # Copia idéntica en otra carpeta (debe deduplicarse) y carpeta clock (se ignora).
    dup = root / "images" / "chair" / "100.000.03.jpg"
    dup.parent.mkdir(parents=True, exist_ok=True)
    dup.write_bytes((root / "images" / "objects" / "100.000.03.jpg").read_bytes())
    (root / "images" / "clock").mkdir(parents=True)
    _solid((0, 0, 0)).save(root / "images" / "clock" / "img1.jpg")
    rooms_dir = root / "images" / "room_scenes"
    rooms_dir.mkdir(parents=True)
    make_room_image().save(rooms_dir / ROOM_ID, quality=95)
    item_to_room = {f"images/couch/{s}.jpg": [f"images/room_scenes/{ROOM_ID}"] for s in ROOM_BOXES}
    item_to_room["images/objects/100.000.06.jpg"] = ["images/room_scenes/otro.jpg"]
    pickles = {
        "products_dict.p": products,
        "img_to_desc.p": img_to_desc,
        "categories_dict.p": {ROOM_ID: "Living Room"},
        "item_to_room.p": item_to_room,
        "room_to_items.p": {f"images/room_scenes/{ROOM_ID}": ["three-seat sofa", "chair"]},
        "categories_images_dict.p": {s: v["type"] for s, v in products.items()},
    }
    for name, obj in pickles.items():
        (text / name).write_bytes(pickle.dumps(obj, protocol=2))
    return root


@pytest.fixture
def cfg(tmp_path: Path, dataset_root: Path) -> AppConfig:
    return load_config(
        ROOT / "configs" / "base.yaml",
        [
            f"paths.raw_dir={dataset_root}",
            f"paths.catalog_file={tmp_path / 'catalog.json'}",
            f"paths.chroma_dir={tmp_path / 'chroma'}",
            f"paths.cache_dir={tmp_path / 'cache'}",
            f"paths.results_dir={tmp_path / 'resultados'}",
            f"paths.runs_dir={tmp_path / 'resultados' / 'corridas'}",
            f"paths.generations_dir={tmp_path / 'resultados' / 'generaciones'}",
            f"paths.spend_ledger={tmp_path / 'resultados' / 'gastos.jsonl'}",
            f"paths.labels_file={tmp_path / 'anotaciones' / 'estricto.jsonl'}",
            f"paths.thresholds_file={tmp_path / 'umbrales.yaml'}",
            f"paths.categories_file={ROOT / 'configs' / 'categories.yaml'}",
            f"paths.pricing_file={ROOT / 'configs' / 'pricing.yaml'}",
            "device=cpu",
            "background.method=none",
            "eval.bootstrap_samples=50",
            "budget.max_usd_total=null",
        ],
    )


class FakeEmbedder:
    """Embedding = color medio de la zona no blanca (suficiente para los productos sintéticos)."""

    name = "fake"
    model_id = "fake/color"

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        rows = []
        for img in images:
            arr = np.asarray(img.convert("RGB"), dtype=np.float32)
            fg = arr[(arr < 245).any(axis=2)]
            mean = fg.mean(axis=0) if len(fg) else np.full(3, 255.0)
            rows.append(np.concatenate([mean / 255.0 - 0.5, [0.05]]))
        return l2_normalize(np.asarray(rows, dtype=np.float32))


class FakeDetector:
    """Devuelve las cajas que se le indiquen (o las del ambiente sintético)."""

    def __init__(self, detections: list[Detection] | None = None):
        self.detections = detections
        self.calls = 0

    def detect(self, image: Image.Image) -> list[Detection]:
        self.calls += 1
        if self.detections is not None:
            return self.detections
        cats = {"100.000.01": "sofa", "100.000.03": "chair", "100.000.05": "table"}
        return [Detection(box, cats[sku], cats[sku], 0.9) for sku, box in ROOM_BOXES.items()]


@pytest.fixture
def catalog(cfg: AppConfig) -> Catalog:
    ds = IkeaDataset.load(cfg.paths.raw_dir)
    cat = Catalog.from_dataset(ds, CategoryMap.load(cfg.paths.categories_file))
    cat.save(cfg.paths.catalog_file)
    return cat


@pytest.fixture
def components(cfg: AppConfig, catalog: Catalog) -> RetrievalComponents:
    cfg.embedding.name = "fake"
    cfg.embedding.model_id = "fake/color"
    embedder = FakeEmbedder()
    store = ChromaVectorStore(cfg.paths.chroma_dir, collection_name(cfg))
    build_index(split_catalog(catalog), embedder, store, cfg)
    categories = CategoryMap.load(cfg.paths.categories_file)
    retriever = Retriever(embedder, store, top_k=5, category_filter=True, threshold=None)
    return RetrievalComponents(
        cfg,
        categories,
        catalog,
        FakeDetector(),
        NoBackgroundRemoval(),
        embedder,
        store,
        retriever,
        NoopReranker(),
    )
