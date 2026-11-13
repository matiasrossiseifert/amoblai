"""Lo común: el registro de láminas, formatos de números y las piezas de cada lámina (llamada,
encabezado de experimento, frase de cierre, fichas de producto)."""

from __future__ import annotations

import json
import re

import img

SL: list[dict] = []

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

# capítulos: número, nombre (para el pie) y la pieza que suma a la habitación
CAPS = {
    0: ("00 · El producto", []),
    1: ("01 · El recorrido", ["alfombra"]),
    2: ("02 · Cómo medimos", ["sofa"]),
    3: ("03 · El buscador", ["tv"]),
    4: ("04 · La lista", ["mesa"]),
    5: ("05 · De trámite", ["lampara"]),
    6: ("06 · Ejercicio 4", ["cortinas", "planta"]),
    7: ("07 · Cierre", ["almohadones"]),
    9: ("Anexo", []),
}


def piezas_hasta(cap: int) -> list[str]:
    out = []
    for c in range(0, min(cap, 7) + 1):
        out += CAPS[c][1]
    return out


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def f(x, d: int = 3) -> str:
    """Decimal con coma: 0,535."""
    if x is None:
        return "—"
    return f"{x:.{d}f}".replace(".", ",")


def pct(x, d: int = 0) -> str:
    return f(100 * x, d) + "%"


def usd(x, d: int = 2) -> str:
    return "US$" + f(x, d)


def miles(n: int) -> str:
    """1.502 (punto de miles)."""
    return f"{n:,}".replace(",", ".")


def sg(x: float, d: int = 3) -> str:
    """+0,075 o −0,005: con signo."""
    return ("−" if x < 0 else "+") + f(abs(x), d)


def ic(lo: float, hi: float, d: int = 3) -> str:
    """[0,041; 0,111]; con signos cuando no es todo positivo: [−0,015; +0,006]."""
    return f"[{f(lo, d)}; {f(hi, d)}]" if lo >= 0 else f"[{sg(lo, d)}; {sg(hi, d)}]"


def dif(v: dict, k: str = "hit@1", d: int = 3, flip: bool = False) -> str:
    """Una diferencia pareada con su IC 95%: +0,075 [0,041; 0,111]. `flip`: al revés (b − a)."""
    x, (lo, hi) = v[k], v[f"{k}_ic95"]
    if flip:
        x, lo, hi = -x, -hi, -lo
    return f"{sg(x, d)} {ic(lo, hi, d)}"


def nb(s: str) -> str:
    """Sin cortes de línea adentro (una diferencia con su intervalo)."""
    return f'<span class="nb">{s}</span>'


def media_desvio(xs: list[float]) -> str:
    import statistics

    return f"{f(statistics.mean(xs), 3)} ± {f(statistics.stdev(xs), 3)}"


def ci95(m: dict, k: str = "hit@1") -> tuple:
    return tuple(m[f"{k}_ic95"])


def add(body: str, *, titulo: str, cap: int, t: int, notas: list[str], cls: str = "",
        fases: str | None = None, capas: dict | None = None, anexo: str | None = None,
        seccion: str | None = None, planta: list[int] | None = None) -> None:
    """planta: los ambientes del flujo que esta lámina toca (se encienden en la planta de llave del
    cajetín)."""
    SL.append(dict(body=body, titulo=titulo, cap=cap, t=t, notas=notas, cls=cls, fases=fases,
                   capas=capas, anexo=anexo, seccion=seccion or CAPS[cap][0], planta=planta))


def section_html(i: int, s: dict, n_total: int) -> str:
    a = [f'class="slide {s["cls"]}"', f'data-titulo="{esc(s["titulo"])}"', f'data-seccion="{esc(s["seccion"])}"',
         f'data-cap="{s["cap"]}"']
    if s["fases"]:
        a.append(f'data-fases="{s["fases"]}"')
    if s["capas"]:
        a.append(f"data-capas='{json.dumps(s['capas'])}'")
    if s["anexo"]:
        a.append(f'data-anexo="{s["anexo"]}"')
    if s.get("planta"):
        a.append(f'data-planta="{" ".join(map(str, s["planta"]))}"')
    return f'<section {" ".join(a)}>{s["body"]}</section>'


# ---------------------------------------------------------------- piezas

def llamada(num: str, texto: str) -> str:
    return f'<div class="llamada"><i>{esc(num)}</i><s></s><span>{texto}</span></div>'


def cab(num: str, rot: str, titulo: str, bajada: str | None = None, cls: str = "") -> str:
    b = f'<p class="bajada">{bajada}</p>' if bajada else ""
    return f'<header class="cab {cls}">{llamada(num, rot)}<h2 class="t">{titulo}</h2>{b}</header>'


def remate(html: str, desde: int | None = None, cls: str = "") -> str:
    d = f' data-desde="{desde}"' if desde is not None else ""
    return f'<p class="remate {cls}"{d}>{html}</p>'


PASOS = ["por qué", "qué hicimos", "resultados", "decisión"]


def pasos_x() -> str:
    return '<div class="pasos-x">' + "".join(f"<span>{p}</span>" for p in PASOS) + "</div>"


def bloque(titulo: str, html: str, desde: int | None = None, cls: str = "") -> str:
    d = f' data-desde="{desde}"' if desde is not None else ""
    return f'<div class="bloque {cls}"{d}><div class="bt">{titulo}</div>{html}</div>'


def exp(num, cap, titulo, por_que, que_hicimos, resultados, decision, *, t, notas, ancho=False,
        rot=None, extra="", planta=None, k_dec="decisión", cls=""):
    """Lámina de experimento: por qué → qué hicimos → resultados → decisión, en ese orden.
    'resultados' es el HTML del lado derecho; lo que deba aparecer recién en el paso 2 lo marca
    quien lo arma (data-desde="2"), y el esqueleto (ejes, nombres) puede aparecer en el paso 1."""
    body = (f'<div class="cuerpo"><div class="xcab">{llamada(num, rot or CAPS[cap][0][5:])}{pasos_x()}</div>'
            f'<h2 class="t xt">{titulo}</h2></div>'
            f'<div class="xg{" ancho" if ancho else ""}"><div class="xl">'
            + bloque("por qué", por_que)
            + bloque("qué hicimos", que_hicimos, desde=1)
            + f'</div><div class="xr">{resultados}</div></div>'
            + (f'<div class="decision" data-desde="3"><div class="k">{k_dec}</div><p>{decision}</p></div>' if decision else "")
            + extra)
    add(body, titulo=f"{num} · " + re.sub("<[^>]+>", "", titulo), cap=cap, t=t, notas=notas, planta=planta, cls=cls)


# ---------------------------------------------------------------- productos

def item(D, pid: str) -> dict:
    """El producto del catálogo (IKEA o ABO)."""
    return D["abo_items"][pid] if pid.startswith("abo-") else D["items"][pid]


def descripcion(D, pid: str) -> str:
    return D["abo_desc"][pid] if pid.startswith("abo-") else D["desc"][pid]


def catalogo(pid: str) -> str:
    return "ABO" if pid.startswith("abo-") else "IKEA"


def kind_es(D, pid: str) -> str:
    k = item(D, pid).get("kind") or ""
    return KIND_ES.get(k, k)


def foto_producto(D, pid: str) -> str:
    return item(D, pid)["photos"][0]


def medidas(D, pid: str) -> str:
    dims = item(D, pid).get("dimensions_cm") or {}
    vals = [dims.get(k) for k in ("width", "depth", "height") if dims.get(k)]
    if not vals:
        return "sin medidas"
    return " × ".join(f"{v:.0f}" for v in vals) + " cm"


def ficha(D, pid, size=150, *, titulo=None, sub=None, cant=None, pos=None, hi=False, tag=None,
          notas=None, cap=True, cls="") -> str:
    u = img.uri(foto_producto(D, pid), int(size * 1.6), int(size * 1.6), q=80, fit="contain")
    extra = ""
    if pos is not None:
        extra += f'<span class="pos">{pos}</span>'
    if cant and cant > 1:
        extra += f'<span class="cant">×{cant}</span>'
    if tag:
        extra += f'<span class="tag">{esc(tag)}</span>'
    nt = ""
    if notas is not None:
        nt = '<div class="notas">' + "".join(f'<i class="g{v}"></i>' for v in notas) + "</div>"
    c = ""
    if cap:
        c = f'<figcaption><b>{esc(titulo or "")}</b>{f"<span>{esc(sub)}</span>" if sub else ""}</figcaption>'
    return (f'<figure class="ficha{" hi" if hi else ""} {cls}" style="--fs:{size}px">'
            f'<div class="fi"><img src="{u}" alt="">{extra}</div>{nt}{c}</figure>')


def md(s: str) -> str:
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\[paso\]", r'<span class="np">▸ paso</span>', s)
    return s
