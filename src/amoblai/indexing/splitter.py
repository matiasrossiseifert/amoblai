"""Splitting: cada producto se divide en una entrada (y un vector) por imagen.

Es el equivalente visual del text splitting: la unidad que se embebe y se
recupera es una foto de producto, no el producto entero. Todas las entradas de
un producto comparten el SKU, que apunta a la ficha completa del catálogo
(patrón multi-vector / parent document). Hoy casi todos los SKUs tienen una sola
foto, pero el esquema ya soporta varias vistas por producto.
"""

from __future__ import annotations

from dataclasses import dataclass

from amoblai.categories import OTHER
from amoblai.data.catalog import Catalog, Product

MetadataValue = str | int | float | bool


@dataclass(frozen=True)
class IndexEntry:
    id: str
    sku: str
    image_path: str  # relativa a la raíz del dataset
    metadata: dict[str, MetadataValue]


def product_metadata(product: Product, image_index: int) -> dict[str, MetadataValue]:
    """Metadata mínima por vector. Chroma no admite None, así que se omiten las claves vacías."""
    meta: dict[str, MetadataValue] = {
        "sku": product.sku,
        "category": product.category,
        "raw_type": product.type,
        "name": product.name,
        "image_index": image_index,
        "image_path": product.image_paths[image_index],
    }
    if product.size_raw:
        meta["size_raw"] = product.size_raw
    for i, value in enumerate(product.dims_cm[:3], start=1):
        meta[f"dim{i}_cm"] = value
    if product.color:
        meta["color"] = product.color
    return meta


def split_product(product: Product) -> list[IndexEntry]:
    return [
        IndexEntry(
            id=f"{product.sku}#{i}",
            sku=product.sku,
            image_path=path,
            metadata=product_metadata(product, i),
        )
        for i, path in enumerate(product.image_paths)
    ]


def split_catalog(catalog: Catalog, scope_only: bool = False) -> list[IndexEntry]:
    entries: list[IndexEntry] = []
    for product in catalog.products.values():
        if scope_only and product.category == OTHER:
            continue
        entries.extend(split_product(product))
    return entries
