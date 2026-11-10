"""Lo común a todas las láminas: la lista de láminas, encabezados, el paso a paso de los
experimentos, formato de números y traducciones de los kinds."""

from __future__ import annotations

import re

from graficos import esc, f, pct  # noqa: F401  (se reexportan)

SL: list[dict] = []

STEP_NAMES = ["Por qué", "Qué hicimos", "Resultados", "Decisión"]

KIND_ES = {
    "sofa": "sofá", "sofa bed": "sofá cama", "armchair": "sillón", "rug": "alfombra",
    "coffee table": "mesa ratona", "side table": "mesa auxiliar", "TV stand": "mueble de TV",
    "floor lamp": "lámpara de pie", "table lamp": "lámpara de mesa", "pendant lamp": "lámpara colgante",
    "ceiling lamp": "lámpara de techo", "wall lamp": "aplique", "desk lamp": "lámpara de escritorio",
    "cushion": "almohadón", "plant": "planta", "plant pot": "maceta", "curtains": "cortinas",
    "dining table": "mesa de comedor", "dining chair": "silla", "desk chair": "silla de escritorio",
    "sideboard": "aparador", "bookcase": "biblioteca", "wall shelf": "estante", "desk": "escritorio",
    "storage cabinet": "mueble de guardado", "display cabinet": "vitrina", "mirror": "espejo",
    "ottoman": "puf", "low stool": "banqueta", "bar stool": "banqueta alta", "bench": "banco",
    "vase": "florero", "throw": "manta", "picture frame": "portarretrato", "wall art": "cuadro",
    "console table": "consola", "dresser": "cómoda", "basket": "canasto", "candle holder": "candelabro",
    "wall clock": "reloj", "file cabinet": "cajonera",
}

CAT_ES = {"rug": "alfombras", "deco": "deco", "lamp": "lámparas", "table": "mesas", "chair": "sillas",
          "cabinet": "guardado", "sofa": "sofás", "armchair": "sillones", "shelf": "estantes"}


def usd(x: float, d: int = 2) -> str:
    return "US$" + f(x, d)


def add(body: str, *, sec: str, title: str, t: int, notes: list[str], cls: str = "",
        phases: str | None = None, po: int = 0) -> None:
    SL.append(dict(body=body, sec=sec, title=title, t=t, notes=notes, cls=cls, phases=phases, po=po))


def stepper() -> str:
    parts = []
    for i, n in enumerate(STEP_NAMES):
        if i:
            parts.append('<span class="bar"></span>')
        parts.append(f'<span class="s"><i>{i + 1}</i>{n}</span>')
    return '<div class="steps">' + "".join(parts) + "</div>"


def hd(eb: str, title: str, lead: str | None = None) -> str:
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return (f'<header class="hd"><div><div class="eb"><i class="sw"></i>{eb}</div>'
            f'<h2 class="t">{title}</h2>{lead_html}</div></header>')


def hdx(num: str, sec: str, title: str) -> str:
    """Encabezado de un experimento: rótulo y paso a paso arriba, la pregunta abajo."""
    return (f'<header class="hd x"><div class="hrow"><div class="eb"><i class="sw"></i>{num}'
            f'<span class="dim">· {sec}</span></div>{stepper()}</div><h2 class="t">{title}</h2></header>')


def blk(label: str, html: str, step: int | None = None, cls: str = "") -> str:
    st = f' data-step="{step}"' if step is not None else ""
    return f'<div class="blk {cls}"{st}><div class="lbl">{label}</div>{html}</div>'


def exp(num, sec, title, why, what, res, dec, *, t, notes, wide=False, res_cls=""):
    """Lámina de experimento: por qué → qué hicimos → resultados → decisión, en ese orden. Los
    resultados no se ven hasta el paso 2 (en su lugar hay un recuadro rayado)."""
    body = hdx(num, sec, title)
    body += f'<div class="xg{" wide" if wide else ""}"><div class="xl">'
    body += blk("Por qué", why)
    body += blk("Qué hicimos", what, step=1)
    body += "</div>"
    body += ('<div class="res"><div class="ph" data-until="2"><span>los resultados, cuando '
             'esté claro qué medimos</span></div>'
             f'<div class="rin {res_cls}" data-step="2">{res}</div></div></div>')
    if dec:
        body += f'<div class="dec" data-step="3"><div class="k">Decisión</div><p>{dec}</p></div>'
    add(body, sec=sec, title=f"{num} · " + re.sub("<[^>]+>", "", title), t=t, notes=notes)


def md_to_html(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[(paso|clic)\]", r'<span class="nstep">▸ \1</span>', s)
    return s
