"""Del dataset IKEA al catálogo de roomrag (un producto por línea, JSON-lines).

Entran los productos del alcance de la v1 (sofá, sillón, silla, mesa, alfombra; mapeo en
`configs/categories.yaml`) que tienen foto. Para cada uno:

- `category`: el tipo grueso de roomrag (`sofa`, `chair`, `table`, `rug`); el sillón es una
  `chair` con kind `armchair`, como en roomrag/kinds.py.
- `kind`: el tipo fino. Acá va uno por defecto según el `type` de IKEA; el definitivo lo asigna
  el subagente que describe el producto mirando la foto (`catalogo/kinds.yaml`), que pisa este.
- `dimensions_cm`: solo cuando no es ambiguo. Con tres medidas, en muebles IKEA da ancho x
  profundidad x alto; en mesas y alfombras con dos, ancho x largo (va como ancho y profundidad).
  Una sola medida (un diámetro, un alto) no se interpreta: sin medidas los filtros de tamaño
  dejan pasar el producto.
- `colors` y `description`: el texto del vendedor, para la línea de base `describer: fields`.
"""

from __future__ import annotations

import json
from pathlib import Path

from amoblai.categories import OTHER, CategoryMap
from amoblai.data.catalog import Catalog, Product

# Categoría del alcance (configs/categories.yaml) -> tipo grueso de roomrag.
ROOMRAG_CATEGORY = {
    "sofa": "sofa",
    "armchair": "chair",
    "chair": "chair",
    "table": "table",
    "rug": "rug",
}

# Kind por defecto según el `type` de IKEA; el resto toma el de su categoría.
DEFAULT_KIND_BY_TYPE = {
    "Three-seat sofa-bed": "sofa bed",
    "Two-seat sofa-bed": "sofa bed",
    "3-seat sofa with bed": "sofa bed",
    "Coffee table": "coffee table",
    "Storage table": "coffee table",
    "Side table": "side table",
    "Side table on castors": "side table",
    "Nest of tables, set of 2": "side table",
    "Tray table": "side table",
    "Console table": "console table",
}
DEFAULT_KIND_BY_CATEGORY = {
    "sofa": "sofa",
    "armchair": "armchair",
    "chair": "dining chair",
    "table": "dining table",
    "rug": "rug",
}


def dimensions(product: Product) -> dict[str, float] | None:
    d = product.dims_cm
    if len(d) == 3 and product.category in ("sofa", "armchair", "chair", "table"):
        return {"width": d[0], "depth": d[1], "height": d[2]}
    if len(d) == 2 and product.category in ("table", "rug"):
        return {"width": d[0], "depth": d[1]}
    return None


def default_kind(product: Product) -> str:
    return DEFAULT_KIND_BY_TYPE.get(product.type, DEFAULT_KIND_BY_CATEGORY[product.category])


def to_item(product: Product, raw_prefix: str) -> dict:
    """Un producto en el formato de roomrag/catalog.py (fotos relativas a la raíz del repo)."""
    return {
        "id": product.sku,
        "name": product.name,
        "category": ROOMRAG_CATEGORY[product.category],
        "kind": default_kind(product),
        "dimensions_cm": dimensions(product),
        "photos": [f"{raw_prefix}/{p}" for p in product.image_paths],
        "type_ikea": product.type,
        "category_tp": product.category,
        "size_raw": product.size_raw,
        "colors": [c.strip() for c in (product.color or "").split(",") if c.strip()],
        "description": product.description,
    }


def build_items(catalog: Catalog, raw_prefix: str) -> list[dict]:
    products = sorted(
        (p for p in catalog.products.values() if p.category != OTHER and p.image_paths),
        key=lambda p: (p.category, p.sku),
    )
    return [to_item(p, raw_prefix) for p in products]


def write_items(items: list[dict], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items))
    return path


def build_catalog_items(raw_dir: Path, categories_file: Path, out: Path) -> list[dict]:
    """Lee el dataset, aplica el mapeo de categorías y escribe el JSON-lines de roomrag."""
    from amoblai.data.ikea import IkeaDataset

    dataset = IkeaDataset.load(raw_dir)
    catalog = Catalog.from_dataset(dataset, CategoryMap.load(categories_file))
    items = build_items(catalog, Path(raw_dir).as_posix())
    write_items(items, out)
    return items


def load_corrections(path: Path) -> dict[str, dict]:
    import yaml

    path = Path(path)
    return (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}


def write_catalog_files(
    items_path: Path,
    descriptions_dir: Path,
    descriptions_out: Path,
    kinds_out: Path,
    corrections_path: Path,
    catalog_yaml: Path,
) -> dict[str, int]:
    """Junta las descripciones de los subagentes, aplica las correcciones a mano y escribe el
    YAML del catálogo que lee roomrag (items, kinds y tipos corregidos). Una corrección con
    `excluir: true` saca el producto de los items (su foto no lo muestra)."""
    import yaml

    from amoblai.descripciones import merge

    n, _ = merge(sorted(Path(descriptions_dir).glob("lote_*.jsonl")), descriptions_out, kinds_out)
    corrections = load_corrections(corrections_path)
    excluded = {str(pid) for pid, fix in corrections.items() if fix.get("excluir")}
    if excluded:
        items = [json.loads(line) for line in Path(items_path).read_text().splitlines()]
        write_items([it for it in items if it["id"] not in excluded], items_path)
    kinds = yaml.safe_load(kinds_out.read_text()) or {}
    for pid, fix in corrections.items():
        if "kind" in fix:
            kinds[str(pid)] = fix["kind"]
    header = (
        "# Kind de cada producto (roomrag/kinds.py): lo asignó el subagente que lo describió\n"
        "# mirando la foto, con las correcciones de catalogo/correcciones.yaml.\n"
        "# Lo genera `amoblai catalogo`: no editar a mano.\n"
    )
    kinds_out.write_text(header + yaml.safe_dump(kinds, allow_unicode=True, sort_keys=True))
    catalog = {
        "name": "ikea",
        "items": [Path(items_path).as_posix()],
        "kinds_file": Path(kinds_out).as_posix(),
        "categories": {
            str(pid): fix["category"] for pid, fix in corrections.items() if "category" in fix
        },
    }
    header = (
        "# Catálogo de roomrag para el TP: los productos IKEA del alcance (roomrag/catalog.py).\n"
        "# Lo genera `amoblai catalogo` desde el dataset y catalogo/correcciones.yaml.\n"
    )
    catalog_yaml.write_text(header + yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False))
    return {
        "descriptions": n,
        "kinds": len(kinds),
        "corrections": len(corrections),
        "excluded": len(excluded),
    }
