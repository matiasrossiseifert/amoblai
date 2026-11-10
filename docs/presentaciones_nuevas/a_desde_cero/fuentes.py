"""Recorta las fuentes locales a woff2 (solo los caracteres que usa la presentación) en
_trabajo/cache/, de donde build.py las embebe. Se corre una vez:

    cd /home/fer/tp-llm && uv run python docs/presentaciones_nuevas/a_desde_cero/fuentes.py
"""

from pathlib import Path

from fontTools import subset

HERE = Path(__file__).resolve().parent
OUT = HERE / "_trabajo" / "cache"
OUT.mkdir(parents=True, exist_ok=True)

F = {
    "serif-r": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Regular.ttf",
    "serif-i": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Italic.ttf",
    "serif-b": "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Bold.ttf",
    "texto-i": "/usr/share/fonts/truetype/paratype/PTF56F.ttf",  # PT Serif Italic: citas en cuerpo de texto
    "sans-r": "/usr/share/fonts/opentype/cabin/Cabin-Regular.otf",
    "sans-i": "/usr/share/fonts/opentype/cabin/Cabin-Italic.otf",
    "sans-m": "/usr/share/fonts/opentype/cabin/Cabin-Medium.otf",
    "sans-sb": "/usr/share/fonts/opentype/cabin/Cabin-SemiBold.otf",
    "sans-b": "/usr/share/fonts/opentype/cabin/Cabin-Bold.otf",
    "mono": "/usr/share/fonts/truetype/ubuntu/UbuntuSansMono[wght].ttf",
}

UNICODES = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x180))  # Latin-1 y Latin Extended-A
    + list(range(0x2010, 0x2050)) + list(range(0x2070, 0x20A0)) + list(range(0x2190, 0x2200))
    + list(range(0x2200, 0x2300)) + [0x2713, 0x2717, 0x25CF, 0x25CB, 0x25B8, 0x3BC, 0x3C3, 0x394, 0x2502]
)

for name, src in F.items():
    if not Path(src).exists():
        print("falta", src)
        continue
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga", "calt", "tnum", "lnum", "pnum", "onum"]
    opts.name_IDs = []
    opts.notdef_outline = True
    font = subset.load_font(src, opts)
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    subset.save_font(font, str(OUT / f"{name}.woff2"), opts)
    print(name, (OUT / f"{name}.woff2").stat().st_size)
