"""Catálogo de productos: la ficha completa, guardada una vez por SKU.

El vector store guarda un vector por imagen con metadata mínima (SKU, categoría,
medidas). La ficha completa vive acá y se recupera por SKU, que funciona como
la clave entre ambos.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel

from amoblai.categories import OTHER, CategoryMap
from amoblai.data.ikea import IkeaDataset

_DIMS = re.compile(r"^\s*(\d+(?:\.\d+)?)(?:\s*x\s*(\d+(?:\.\d+)?))?(?:\s*x\s*(\d+(?:\.\d+)?))?\s*$")
_UNITS_TO_CM = {"cm": 1.0, "mm": 0.1, "m": 100.0}


def parse_size(size: str) -> list[float]:
    """Extrae las medidas en cm de `size` (texto libre del dataset).

    Toma la primera variante cuando hay varias ("150x200,50x80 cm" → [150, 200]).
    No interpreta qué dimensión es cuál: IKEA usa ancho x profundidad x alto en
    muebles, pero en alfombras son ancho x largo y una sola cifra puede ser un
    diámetro. Devuelve [] si no hay medidas lineales (litros, "Standard King"...).
    """
    text = (size or "").strip().lower()
    for unit, factor in _UNITS_TO_CM.items():
        if text.endswith(f" {unit}"):
            body = text[: -len(unit)].strip()
            match = _DIMS.match(body.split(",")[0])
            if not match:
                return []
            return [round(float(g) * factor, 1) for g in match.groups() if g is not None]
    return []


class Product(BaseModel):
    sku: str
    name: str
    type: str
    category: str
    color: str | None = None
    size_raw: str | None = None
    dims_cm: list[float] = []
    description: str | None = None
    image_paths: list[str] = []  # relativas a la raíz del dataset
    # El dataset no trae precio ni link; quedan para cuando haya scraping (FUTURO.md).
    price: float | None = None
    url: str | None = None

    def card(self) -> dict[str, object]:
        """Ficha para la lista de compra (precio y link solo si existen)."""
        card: dict[str, object] = {
            "sku": self.sku,
            "nombre": self.name,
            "tipo": self.type,
            "categoria": self.category,
            "color": self.color,
            "medidas": self.size_raw,
            "medidas_cm": self.dims_cm or None,
        }
        if self.price is not None:
            card["precio"] = self.price
        if self.url:
            card["link"] = self.url
        return card


class Catalog:
    def __init__(self, products: dict[str, Product], raw_dir: Path):
        self.products = products
        self.raw_dir = Path(raw_dir)

    @classmethod
    def from_dataset(cls, dataset: IkeaDataset, categories: CategoryMap) -> Catalog:
        products = {
            sku: Product(
                sku=sku,
                name=p.name,
                type=p.type,
                category=categories.category_of_type(p.type),
                color=p.color or None,
                size_raw=p.size or None,
                dims_cm=parse_size(p.size),
                description=p.description or None,
                image_paths=[path.as_posix() for path in p.image_paths],
            )
            for sku, p in dataset.products.items()
        }
        return cls(products, dataset.root)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {sku: p.model_dump(mode="json") for sku, p in sorted(self.products.items())}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    @classmethod
    def load(cls, path: Path, raw_dir: Path, categories: CategoryMap | None = None) -> Catalog:
        """Carga la ficha; con `categories`, reaplica el mapeo (por si se editó el YAML)."""
        data = json.loads(Path(path).read_text())
        catalog = cls({sku: Product.model_validate(v) for sku, v in data.items()}, raw_dir)
        if categories is not None:
            for product in catalog.products.values():
                product.category = categories.category_of_type(product.type)
        return catalog

    def __len__(self) -> int:
        return len(self.products)

    def __contains__(self, sku: str) -> bool:
        return sku in self.products

    def get(self, sku: str) -> Product:
        return self.products[sku]

    def in_category(self, category: str) -> list[Product]:
        return [p for p in self.products.values() if p.category == category]

    def in_scope(self) -> list[Product]:
        return [p for p in self.products.values() if p.category != OTHER]

    def image_path(self, sku: str, index: int = 0) -> Path:
        return self.raw_dir / self.products[sku].image_paths[index]
