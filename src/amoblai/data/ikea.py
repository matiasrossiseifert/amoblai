"""Data loading del dataset IKEA (Tautkute et al., 2017).

Particularidades verificadas del dataset que este módulo resuelve:

- Las rutas de las anotaciones no coinciden con las carpetas reales (por ejemplo
  `images/mirror/X.jpg` cuando el archivo está en `images/objects/X.jpg`), así
  que todo se une por el SKU que sale del nombre de archivo.
- Hay SKUs en dos carpetas: si los archivos son idénticos se deduplican; si son
  distintos, el producto queda con dos imágenes (dos entradas en el índice).
- `room_to_items.p` trae nombres de tipo, no SKUs: el ground truth de cada
  ambiente sale de invertir `item_to_room.p`.
- `images/clock/` no son productos del catálogo y se ignora.
- Solo una parte de los ambientes anotados existe en disco.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from amoblai.data.safe_pickle import load_pickle

log = logging.getLogger(__name__)

ROOMS_DIR = "room_scenes"
_IGNORED_DIRS = {ROOMS_DIR, "clock"}
_DESC_PREFIX = "View more product information"


@dataclass(frozen=True)
class RawProduct:
    sku: str
    name: str
    type: str
    color: str
    size: str
    description: str
    image_paths: tuple[Path, ...]  # relativas a la raíz del dataset


@dataclass(frozen=True)
class RoomScene:
    room_id: str  # nombre de archivo
    path: Path  # relativa a la raíz del dataset
    room_type: str | None
    skus: frozenset[str]  # SKUs anotados (todas las categorías)


@dataclass
class IkeaDataset:
    root: Path
    products: dict[str, RawProduct]
    rooms: dict[str, RoomScene]
    stats: dict[str, int] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> IkeaDataset:
        root = Path(root)
        text = root / "text_data"
        products_raw: dict[str, dict] = load_pickle(text / "products_dict.p")
        img_to_desc: dict[str, dict] = load_pickle(text / "img_to_desc.p")
        room_types: dict[str, str] = load_pickle(text / "categories_dict.p")
        item_to_room: dict[str, list[str]] = load_pickle(text / "item_to_room.p")

        images, dup_identical = _index_product_images(root)
        products: dict[str, RawProduct] = {}
        for sku, info in products_raw.items():
            sku = str(sku)
            products[sku] = RawProduct(
                sku=sku,
                name=str(info.get("name", "")).strip(),
                type=str(info.get("type", "")).strip(),
                color=str(info.get("color", "")).strip(),
                size=str(info.get("size", "")).strip(),
                description=_clean_description(sku, info.get("desc", ""), img_to_desc),
                image_paths=tuple(images.get(sku, ())),
            )

        gt: dict[str, set[str]] = defaultdict(set)
        for item_path, room_paths in item_to_room.items():
            sku = PurePosixPath(item_path).stem
            for room_path in room_paths:
                gt[PurePosixPath(room_path).name].add(sku)

        rooms: dict[str, RoomScene] = {}
        for path in sorted((root / "images" / ROOMS_DIR).glob("*.jpg")):
            rooms[path.name] = RoomScene(
                room_id=path.name,
                path=path.relative_to(root),
                room_type=room_types.get(path.name),
                skus=frozenset(s for s in gt.get(path.name, ()) if s in products),
            )

        stats = {
            "products": len(products),
            "products_with_image": sum(1 for p in products.values() if p.image_paths),
            "product_images": sum(len(p.image_paths) for p in products.values()),
            "duplicate_identical_images": dup_identical,
            "rooms_on_disk": len(rooms),
            "rooms_annotated": len(gt),
        }
        log.info("Dataset IKEA cargado: %s", stats)
        return cls(root=root, products=products, rooms=rooms, stats=stats)

    def rooms_of_type(self, room_types: list[str]) -> list[RoomScene]:
        wanted = set(room_types)
        return [r for r in self.rooms.values() if r.room_type in wanted]


def _index_product_images(root: Path) -> tuple[dict[str, list[Path]], int]:
    """SKU → rutas de imágenes distintas, y cuántas copias idénticas se descartaron."""
    by_sku: dict[str, list[Path]] = defaultdict(list)
    for path in sorted((root / "images").rglob("*.jpg")):
        if path.parent.name in _IGNORED_DIRS:
            continue
        by_sku[path.stem].append(path)
    result: dict[str, list[Path]] = {}
    dropped = 0
    for sku, paths in by_sku.items():
        seen: set[str] = set()
        unique: list[Path] = []
        for p in paths:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            if digest in seen:
                dropped += 1
                continue
            seen.add(digest)
            unique.append(p.relative_to(root))
        result[sku] = unique
    return result, dropped


def _clean_description(sku: str, raw: object, img_to_desc: dict[str, dict]) -> str:
    clean = img_to_desc.get(f"/static/images/{sku}.jpg", {}).get("desc")
    text = str(clean if clean else raw or "").strip()
    if text.startswith(_DESC_PREFIX):
        text = text[len(_DESC_PREFIX) :].strip()
    return text
