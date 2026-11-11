"""Recorta las fuentes instaladas a woff2 (solo latín y los signos que usa la presentación) en
_trabajo/cache/fuentes/, de donde build.py las embebe. build.py lo llama solo si faltan.

    cd /home/fer/tp-llm && uv run python docs/presentaciones_nuevas/a2/fuentes.py

- Ubuntu Sans (variable, ancho y peso): títulos condensados y texto.
- Ubuntu Sans Italic (variable): los pedidos y los porqués, que son citas.
- Go Mono: rótulos, cotas y datos.
"""

from __future__ import annotations

from pathlib import Path

from fontTools import subset

HERE = Path(__file__).resolve().parent
OUT = HERE / "_trabajo" / "cache" / "fuentes"

F = {
    "sans": "/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf",
    "sans-i": "/usr/share/fonts/truetype/ubuntu/UbuntuSans-Italic[wdth,wght].ttf",
    "mono": "/usr/share/fonts/fonts-go/Go-Mono.ttf",
    "mono-b": "/usr/share/fonts/fonts-go/Go-Mono-Bold.ttf",
}

UNICODES = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x180))
    + list(range(0x2010, 0x2050)) + list(range(0x2070, 0x20A0)) + list(range(0x2190, 0x2200))
    + list(range(0x2200, 0x2300)) + [0x2713, 0x2717, 0x25CF, 0x25CB, 0x25B8, 0x25B2, 0x25BC, 0x3BC,
                                     0x3C3, 0x394, 0x2502, 0x2500, 0x221A, 0x2264, 0x2265, 0x2248]
)


def build(force: bool = False) -> dict[str, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, src in F.items():
        dst = OUT / f"{name}.woff2"
        out[name] = dst
        if dst.exists() and not force:
            continue
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt", "tnum", "lnum", "pnum", "case", "ss01"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        font = subset.load_font(src, opts)
        sub = subset.Subsetter(opts)
        sub.populate(unicodes=UNICODES)
        sub.subset(font)
        subset.save_font(font, str(dst), opts)
        print(name, dst.stat().st_size)
    return out


if __name__ == "__main__":
    build(force=True)
