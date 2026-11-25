"""Arma los ejemplos de la landing (web/ejemplos.json y web/img/) con corridas reales de la
configuración final de amoblai. Se corre una vez; traducir los textos cuesta unos centavos.

    uv run --group apps python apps/web/preparar_ejemplos.py
"""

from __future__ import annotations

import json
import shutil
from urllib.parse import unquote

import server as s
from PIL import Image, ImageOps

SRC = s.TP / "datos" / "resultados" / "amoblar"
EXAMPLES = [  # (carpeta de la corrida, nombre corto)
    ("final-experimento-lectura", "rincon-de-lectura"),
    ("final-publica-living-bohemio", "living-bohemio"),
    ("final-publica-living-japandi", "living-japandi"),
    ("final-publica-loft-industrial", "loft-industrial"),
    ("final-alvear-escritorio", "escritorio-ventanal"),
    ("final-publica-comedor-clasico-moderno", "comedor-abierto"),
    ("final-caballito-living", "living-balcon"),
]
IMG = s.WEB / "img"
WORK = s.CACHE / "ejemplos"


def save(src, dst, width: int, quality: int = 84) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((width, width * 4))
    im.save(dst, "JPEG", quality=quality, optimize=True, progressive=True)
    return "/static/" + dst.relative_to(s.WEB).as_posix()


def product_photo(url: str | None) -> str | None:
    """De /archivo?p=... a una copia chica en web/img/productos/."""
    if not url:
        return None
    rel = unquote(url.split("p=", 1)[1].split("&", 1)[0])
    name = rel.replace("/", "_").removeprefix("datos_dataset_")
    return save(s.TP / rel, IMG / "productos" / name, 480, 82)


def main() -> None:
    out = {"ejemplos": []}
    for folder, slug in EXAMPLES:
        src = SRC / folder
        work = WORK / slug
        work.mkdir(parents=True, exist_ok=True)
        for f in ("1_searches.json", "2_candidates.json", "3_choice.json", "5_image.json", "request.json"):
            shutil.copy(src / f, work / f)
        s.translate(work, work / "traduccion.json")  # en la caché: la carpeta de la corrida no se toca
        tr = s.read(work / "traduccion.json")
        lista = s.products(work, tr)
        for it in lista:
            it["foto"] = product_photo(it["foto"])
        img = s.read(work / "5_image.json") or {}
        out["ejemplos"].append(
            {
                "id": slug,
                "corrida": folder,  # para la vista por dentro: /dev/terminal-<corrida>
                "pedido": s.read(src / "request.json")["request"],
                "estado": "listo",
                "antes": save(src / "room.jpg", IMG / f"{slug}-antes.jpg", 1600),
                "despues": save(src / "final.png", IMG / f"{slug}-despues.jpg", 1600),
                "alineada": bool((img.get("room_check") or {}).get("ok")),
                "ambiente": (tr or {}).get("ambiente"),
                "resumen": (tr or {}).get("resumen"),
                "piezas": s.pieces(work),
                "lista": lista,
                "faltan": (tr or {}).get("faltan") or [],
            }
        )
        print(slug, len(lista), "productos", "traducido" if tr else "SIN traducir")
    # cómo busca: los candidatos del sillón (o el sofá) del ejemplo principal, con el elegido marcado
    first = SRC / EXAMPLES[0][0]
    found, choice = s.read(first / "2_candidates.json"), s.read(first / "3_choice.json")
    for piece, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
        kinds = piece["spec"].get("kinds") or []
        if "armchair" in kinds or "sofa" in kinds:
            out["candidatos"] = {
                "pieza": s.KIND_ES[kinds[0]],
                "fotos": [product_photo(s.tp_url(h["photos"][0])) for h in piece["candidates"]],
                "elegido": [h["id"] for h in piece["candidates"]].index(c["id"]),
            }
            break
    (s.WEB / "ejemplos.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
