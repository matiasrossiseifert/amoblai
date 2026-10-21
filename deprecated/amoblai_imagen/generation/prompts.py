"""Prompts de los generadores. Van en inglés (los modelos responden mejor); el
pedido del usuario se pasa tal cual, en el idioma en que lo escribió."""

from __future__ import annotations

from dataclasses import dataclass

from amoblai_imagen.vision.boxes import Box, box_percent, describe_location

GENERATOR1 = """\
Furnish this photo of an empty room.

Hard constraints:
- Keep the exact same camera viewpoint, framing, walls, floor, ceiling, windows, doors, \
lighting and every architectural detail. Do not crop, zoom, rotate or extend the image.
- Add ONLY furniture from these categories: {categories}. Do not add anything else: \
no lamps, plants, shelves, cushions on the floor, curtains, artwork, decorations or people.
- Each piece must be realistic, generic (no visible brand), fully visible and clearly \
separated from the others, with correct scale and perspective for the room.
- A rug, if any, must lie flat on the floor.

User request (follow it within the constraints above): {user_prompt}
"""

GENERATOR2_SINGLE_IMAGE1 = """\
Image 1 is a photo of a furnished room. The other images are product photos from a \
furniture catalog, on a white background.

Replace each piece of furniture listed below with the exact catalog product shown in the \
indicated image. Reproduce the product faithfully (shape, proportions, color, material, \
legs, details), keeping the position, orientation and size of the piece it replaces, and \
the room's perspective, lighting and shadows.
Leave everything else in image 1 unchanged: same walls, floor, windows and framing.

{items}
"""

GENERATOR2_SINGLE_ORIGINAL = """\
Image 1 is a photo of an empty room. The other images are product photos from a \
furniture catalog, on a white background.

Place each catalog product listed below inside the room, in the indicated region. \
Reproduce each product faithfully (shape, proportions, color, material, legs, details), \
with realistic scale, perspective, lighting and contact shadows.
Leave everything else unchanged: same walls, floor, windows and framing. Do not add any \
other objects.

{items}
"""

GENERATOR2_ITEM_IMAGE1 = """\
Image 1 is a photo of a room. Image 2 is a product photo from a furniture catalog, on a \
white background.

Replace the {category} in the {location} of image 1 (region {region}) with the exact \
product shown in image 2: {product}. Reproduce it faithfully (shape, proportions, color, \
material, legs, details), keeping the position, orientation and size of the piece it \
replaces, and the room's perspective, lighting and shadows. Leave everything else unchanged.
"""

GENERATOR2_ITEM_ORIGINAL = """\
Image 1 is a photo of a room. Image 2 is a product photo from a furniture catalog, on a \
white background.

Place the exact product shown in image 2 ({product}) in the {location} of image 1 \
(region {region}), as a {category}. Reproduce it faithfully (shape, proportions, color, \
material, legs, details), with realistic scale, perspective, lighting and contact shadows. \
Leave everything else unchanged and do not add other objects.
"""

CATEGORY_EN = {
    "sofa": "sofa",
    "armchair": "armchair",
    "chair": "chair",
    "table": "table",
    "rug": "rug",
}


@dataclass
class PlacedProduct:
    category: str
    box: Box
    sku: str
    name: str
    type: str
    size: str | None


def product_text(p: PlacedProduct) -> str:
    text = f"IKEA {p.name} ({p.type.lower()}"
    return text + (f", {p.size})" if p.size else ")")


def generator1_prompt(user_prompt: str, categories: list[str]) -> str:
    cats = ", ".join(CATEGORY_EN.get(c, c) for c in categories)
    return GENERATOR1.format(categories=cats, user_prompt=user_prompt.strip() or "(none)")


def unique_skus(items: list[PlacedProduct]) -> list[str]:
    """SKUs distintos en orden de aparición: cada producto se adjunta una sola vez."""
    return list(dict.fromkeys(p.sku for p in items))


def generator2_single_prompt(items: list[PlacedProduct], size: tuple[int, int], base: str) -> str:
    """Un renglón por mueble; si varios usan el mismo producto, apuntan a la misma imagen."""
    w, h = size
    image_of = {sku: i for i, sku in enumerate(unique_skus(items), start=2)}
    lines = []
    for p in items:
        i = image_of[p.sku]
        lines.append(
            f"- The {CATEGORY_EN.get(p.category, p.category)} in the "
            f"{describe_location(p.box, w, h)} (region {box_percent(p.box, w, h)}) -> "
            f"product in image {i}: {product_text(p)}."
        )
    template = GENERATOR2_SINGLE_IMAGE1 if base == "image1" else GENERATOR2_SINGLE_ORIGINAL
    return template.format(items="\n".join(lines))


def generator2_item_prompt(item: PlacedProduct, size: tuple[int, int], base: str) -> str:
    w, h = size
    template = GENERATOR2_ITEM_IMAGE1 if base == "image1" else GENERATOR2_ITEM_ORIGINAL
    return template.format(
        category=CATEGORY_EN.get(item.category, item.category),
        location=describe_location(item.box, w, h),
        region=box_percent(item.box, w, h),
        product=product_text(item),
    )
