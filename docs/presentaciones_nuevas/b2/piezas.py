"""Las piezas visuales: fotos embebidas, el esquema del flujo (la columna vertebral de la charla),
las etiquetas de producto, los tickets y los gráficos."""

from __future__ import annotations

import base64
import hashlib
import io
import math
import re

from PIL import Image

from datos import ITEMS, ROOT, esc, f2

# =============================================================================================
# Fotos: cada una se embebe una sola vez, como clase CSS con background-image
# =============================================================================================


class Imagenes:
    def __init__(self):
        self.css: dict[str, str] = {}
        self.bytes = 0

    def reg(self, clave: str, src, w: int, h: int | None = None, modo: str = "cover", q: int = 80,
            recorte=None, fondo=(255, 255, 255)) -> str:
        cls = "im-" + re.sub(r"[^a-z0-9]+", "-", clave.lower()).strip("-")
        if cls in self.css:
            return cls
        im = src if isinstance(src, Image.Image) else Image.open(src if str(src).startswith("/") else ROOT / src)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, fondo)
            bg.paste(im, mask=im.split()[-1])
            im = bg
        im = im.convert("RGB")
        if recorte:
            im = im.crop(recorte)
        if modo == "cover" and h:
            sw, sh = im.size
            r = max(w / sw, h / sh)
            im = im.resize((round(sw * r), round(sh * r)), Image.LANCZOS)
            x0 = (im.width - w) // 2
            y0 = (im.height - h) // 2
            im = im.crop((x0, y0, x0 + w, y0 + h))
        else:
            im.thumbnail((w, h or w), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        b = buf.getvalue()
        self.bytes += len(b)
        self.css[cls] = f".{cls}{{background-image:url(data:image/jpeg;base64,{base64.b64encode(b).decode()})}}"
        return cls

    def style(self) -> str:
        return "\n".join(self.css.values())


IM = Imagenes()


def foto(clave, src, w, h, extra="", estilo="", q=80, recorte=None, enc=1.25, modo="cover") -> str:
    """Un div w×h con la foto recortada a ese tamaño; se codifica a enc× para que se vea nítida
    cuando el escenario se escala a una pantalla más grande."""
    cls = IM.reg(clave, src, round(w * enc), round(h * enc), modo=modo, q=q, recorte=recorte)
    return f'<div class="foto {cls} {extra}" style="width:{w}px;height:{h}px;{estilo}"></div>'


def prod_cls(pid: str, lado: int = 300) -> str:
    return IM.reg("p-" + pid, ITEMS[pid]["photos"][0], lado, None, modo="fit", q=80)


def producto(pid: str, w: int, extra="", estilo="") -> str:
    if pid not in ITEMS:
        return ""
    return (f'<div class="prod {prod_cls(pid)} {extra}" style="width:{w}px;height:{w}px;padding:{max(2, round(w * .06))}px;'
            f'{estilo}"></div>')


# =============================================================================================
# Íconos del esquema (trazo, 36×36)
# =============================================================================================

ICONOS = {
    "foto": '<rect x="3" y="10" width="30" height="21" rx="3"/><path d="M12 10l2.5-4h7L24 10"/><circle cx="18" cy="20.5" r="5.5"/>',
    "plan": '<rect x="7" y="6" width="22" height="27" rx="2.5"/><path d="M13 6V3.5h10V6M12.5 15h11M12.5 21h11M12.5 27h6"/>',
    "busqueda": '<circle cx="15" cy="15" r="9.5"/><path d="M22 22l9.5 9.5"/>',
    "eleccion": '<rect x="2.5" y="9" width="9" height="19" rx="1.5"/><rect x="13.5" y="6" width="10" height="25" rx="1.5"/><rect x="25.5" y="9" width="8" height="19" rx="1.5"/><path d="M15.8 18.5l2.4 2.8 3.6-5"/>',
    "escena": '<path d="M3 31V6h30v25"/><path d="M1 31h34"/><rect x="7" y="19" width="10" height="12"/><rect x="21" y="14" width="8" height="17"/>',
    "imagen": '<rect x="3" y="6" width="30" height="24" rx="2.5"/><path d="M3 25l9-9 7 7 4-4 10 10"/><circle cx="25" cy="13" r="2.6"/>',
    "control": '<rect x="2.5" y="6" width="20" height="16" rx="2"/><rect x="13.5" y="14" width="20" height="16" rx="2"/><path d="M19 22.5l3 3 6-6.5"/>',
    "catalogo": '<rect x="4" y="4" width="12" height="12" rx="1.5"/><rect x="20" y="4" width="12" height="12" rx="1.5"/><rect x="4" y="20" width="12" height="12" rx="1.5"/><rect x="20" y="20" width="12" height="12" rx="1.5"/>',
    "descripcion": '<rect x="5" y="4" width="26" height="29" rx="2.5"/><path d="M10 11h16M10 16h16M10 21h16M10 26h9"/>',
    "indice": '<ellipse cx="18" cy="8" rx="12" ry="4.5"/><path d="M6 8v19c0 2.5 5.4 4.5 12 4.5s12-2 12-4.5V8M6 17.5c0 2.5 5.4 4.5 12 4.5s12-2 12-4.5"/>',
    "salida": '<path d="M8 3h20v30l-3.3-2.2L21.3 33 18 30.8 14.7 33 11.3 30.8 8 33z"/><path d="M12.5 10h11M12.5 16h11M12.5 22h7"/>',
    "lidar": '<rect x="10" y="3" width="16" height="30" rx="3"/><circle cx="18" cy="9" r="2.4"/><path d="M3 14a14 14 0 0 1 0 8M33 14a14 14 0 0 0 0 8"/>',
    "cubo": '<path d="M18 3l13 7v16l-13 7-13-7V10z"/><path d="M5 10l13 7 13-7M18 17v16"/>',
}


def icono(nombre: str, cls: str = "ico") -> str:
    return f'<svg class="{cls}" viewBox="0 0 36 36" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{ICONOS[nombre]}</g></svg>'


# =============================================================================================
# El esquema del flujo
# =============================================================================================
#
#   indexing (corre una vez):   Catálogo → Descripción → Índice
#                                                          ↓
#   consulta (por pedido):      Foto + pedido → Plan → Búsqueda
#                                 ⇣                       ↓
#                               Imagen ← Escena ←  Elección
#                                 ↓ ↺                     ⇣
#                               Control →   Lista + imagen
#
NW, NH = 272, 122
COL = [28, 368, 708]
FILA = {"i": 64, "1": 300, "2": 510, "3": 720}

NODOS = [
    # clave, ícono, nombre, sub1, sub2, col, fila, ancho
    ("catalogo", "catalogo", "Catálogo", "productos con foto", "IKEA y Amazon (ABO)", 0, "i", NW),
    ("descripcion", "descripcion", "Descripción", "un VLM mira cada foto", "y escribe 8 líneas", 1, "i", NW),
    ("indice", "indice", "Índice", "Qwen3-Embedding", "ChromaDB (HNSW)", 2, "i", NW),
    ("foto", "foto", "Foto + pedido", "el ambiente vacío", "y el pedido en texto", 0, "1", NW),
    ("plan", "plan", "Plan", "Claude Opus: piezas,", "medidas y consulta", 1, "1", NW),
    ("busqueda", "busqueda", "Búsqueda", "filtros duros", "k candidatos por pieza", 2, "1", NW),
    ("imagen", "imagen", "Imagen", "Nano Banana 2", "edita la foto", 0, "2", NW),
    ("escena", "escena", "Escena", "foto, productos y", "medidas, para la imagen", 1, "2", NW),
    ("eleccion", "eleccion", "Elección", "Claude mira las fotos", "y elige uno por pieza", 2, "2", NW),
    ("control", "control", "Control", "SIFT: ¿es el mismo", "cuarto?", 0, "3", NW),
    ("salida", "salida", "Lista + imagen", "la lista de compra", "y el ambiente amoblado", 1, "3", COL[2] + NW - COL[1]),
]
POS = {k: (COL[c], FILA[f], w) for k, _i, _n, _a, _b, c, f, w in NODOS}

# Lo que cambia en cada etapa con medidas reales (pasos a futuro): paso en que aparece y las dos líneas
FUT_SUB = {"foto": (1, "+ escaneo con LiDAR:", "medidas reales del cuarto"),
           "catalogo": (2, "+ medidas de cada", "producto: su caja a escala"),
           "escena": (3, "+ cajas 3D a escala,", "ubicadas (a o b)"),
           "imagen": (4, "llena cada caja:", "tamaño y lugar reales")}

# A qué etapa toca cada experimento (para los pines y los focos)
ETAPA_EXP = {1: ["descripcion"], 2: ["indice"], 3: ["busqueda"], 4: ["indice"], 5: ["indice"], 6: ["indice", "plan"],
             7: ["eleccion"], 8: ["busqueda", "eleccion"], 9: ["catalogo"], 10: ["catalogo"], 11: ["busqueda"],
             12: ["escena", "imagen", "control"], 13: ["imagen"]}


def _pines_por_nodo(pines):
    por = {}
    for n in pines:
        k = ETAPA_EXP[n][0] if n not in (8, 12) else {8: "eleccion", 12: "imagen"}[n]
        if n == 6:
            k = "indice"
        por.setdefault(k, []).append(n)
    return por


def flujo(pines=(), cls="", fut=False, pin_paso=None, etiquetas_fin=None, on=()) -> str:
    """El esquema completo. pines: números de experimento que se marcan sobre su etapa.
    pin_paso: dict n -> paso en que aparece el pin. etiquetas_fin: dict clave -> texto (configuración final).
    on: etapas encendidas de entrada (sin depender de los pasos)."""
    on = set(on)
    if on:
        cls += " foco"
    o = ['<svg class="flujo ' + cls + '" viewBox="-44 0 1068 868" role="img" aria-label="El flujo de amoblai: el indexing '
         'corre una vez (catálogo, descripción, índice) y la consulta corre por pedido (foto y pedido, plan, búsqueda, '
         'elección, escena, imagen y control).">']
    # regiones
    o.append('<g data-k="indexing"><rect class="reg reg-i" x="0" y="14" width="1008" height="196" rx="10"/>'
             '<text class="reg-t" x="20" y="44">indexing · corre una vez</text></g>')
    o.append('<g data-k="consulta"><rect class="reg" x="0" y="248" width="1008" height="612" rx="10"/>'
             '<text class="reg-t" x="20" y="278">consulta · corre por pedido</text></g>')
    # flechas
    cy = lambda f: FILA[f] + NH / 2  # noqa: E731
    x_mid = lambda c: COL[c] + NW / 2  # noqa: E731
    fl = [
        f'M{COL[0] + NW} {cy("i")}H{COL[1] - 6}', f'M{COL[1] + NW} {cy("i")}H{COL[2] - 6}',
        f'M{x_mid(2)} {FILA["i"] + NH}V{FILA["1"] - 6}',
        f'M{COL[0] + NW} {cy("1")}H{COL[1] - 6}', f'M{COL[1] + NW} {cy("1")}H{COL[2] - 6}',
        f'M{x_mid(2)} {FILA["1"] + NH}V{FILA["2"] - 6}',
        f'M{COL[2]} {cy("2")}H{COL[1] + NW + 6}', f'M{COL[1]} {cy("2")}H{COL[0] + NW + 6}',
        f'M{x_mid(0) + 34} {FILA["2"] + NH}V{FILA["3"] - 6}',
        f'M{COL[0] + NW} {cy("3")}H{COL[1] - 6}',
    ]
    o.append('<g class="lineas">' + "".join(f'<path class="fl" d="{d}" marker-end="url(#pf)"/>' for d in fl))
    # la foto también va a la imagen; la lista sale de la elección; el control puede pedir otro intento
    o.append(f'<path class="fl fl-d" d="M{x_mid(0) - 60} {FILA["1"] + NH}V{FILA["2"] - 6}" marker-end="url(#pf)"/>')
    o.append(f'<text class="fl-t" x="{x_mid(0) - 48}" y="{FILA["1"] + NH + 50}">la foto</text>')
    o.append(f'<path class="fl fl-d" d="M{x_mid(2)} {FILA["2"] + NH}V{FILA["3"] - 6}" marker-end="url(#pf)"/>')
    o.append(f'<text class="fl-t" x="{x_mid(2) + 12}" y="{FILA["2"] + NH + 50}">la lista</text>')
    o.append(f'<text class="fl-t" x="{x_mid(2) + 12}" y="{FILA["1"] + NH + 50}">k candidatos</text>')
    lx = COL[0] - 18
    o.append(f'<path class="fl" d="M{COL[0]} {cy("3") + 18}H{lx + 6}Q{lx - 14} {cy("3") + 18} {lx - 14} {cy("3") - 2}'
             f'V{cy("2") + 20}Q{lx - 14} {cy("2")} {lx + 6} {cy("2")}H{COL[0] - 6}" marker-end="url(#pf)"/>')
    o.append(f'<text class="fl-t" x="{lx - 26}" y="{(cy("2") + cy("3")) / 2}" text-anchor="middle" '
             f'transform="rotate(-90 {lx - 26} {(cy("2") + cy("3")) / 2})">otro intento</text>')
    o.append('</g>')
    # nodos
    fin = etiquetas_fin or {}
    for k, ic_, nom, a, b, c, f, w in NODOS:
        x, y = COL[c], FILA[f]
        subs = (f'<text class="sub" x="{x + 20}" y="{y + 84}">{a}</text>'
                + ("" if k in fin else f'<text class="sub" x="{x + 20}" y="{y + 105}">{b}</text>'))
        if fut and k in FUT_SUB:
            pa, fa, fb = FUT_SUB[k]
            subs = (f'<g data-hasta="{pa}">{subs}</g><g class="fut-sub" data-paso="{pa}">'
                    f'<rect x="{x - 7}" y="{y - 7}" width="{w + 14}" height="{NH + 14}" rx="13"/>'
                    f'<text x="{x + 20}" y="{y + 84}">{fa}</text><text x="{x + 20}" y="{y + 105}">{fb}</text></g>')
        o.append(f'<g class="nodo{" on" if k in on else ""}" data-k="{k}"><rect class="caja" x="{x}" y="{y}" width="{w}" height="{NH}" rx="9"/>'
                 f'<use href="#i-{ic_}" class="ico" x="{x + 18}" y="{y + 18}" width="34" height="34"/>'
                 f'<text class="nom" x="{x + 64}" y="{y + 45}">{nom}</text>{subs}</g>')
    # etiquetas de la configuración final
    if etiquetas_fin:
        for k, txt in etiquetas_fin.items():
            x, y, w = POS[k]
            o.append(f'<g class="cfg" data-k="{k}"><rect x="{x + 8}" y="{y + NH - 16}" width="{w - 16}" height="34" rx="5"/>'
                     f'<text x="{x + w / 2}" y="{y + NH + 7}" text-anchor="middle">{txt}</text></g>')
    # pines de experimentos
    for k, ns in _pines_por_nodo(pines).items():
        x, y, w = POS[k]
        for i, n in enumerate(ns):
            px, py = x + w - 24 - i * 42, y
            pa = f' data-paso="{pin_paso[n]}"' if pin_paso and n in pin_paso else ""
            o.append(f'<g class="pin"{pa}><circle cx="{px}" cy="{py}" r="18"/><text x="{px}" y="{py + 7}" text-anchor="middle">{n}</text></g>')
    o.append("</svg>")
    return "".join(o)


def defs_svg() -> str:
    """Íconos y puntas de flecha, una sola vez en el documento."""
    sims = "".join(f'<symbol id="i-{k}" viewBox="0 0 36 36"><g fill="none" stroke="currentColor" stroke-width="2.4" '
                   f'stroke-linecap="round" stroke-linejoin="round">{v}</g></symbol>' for k, v in ICONOS.items())
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
            '<marker id="pf" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">'
            '<path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker>'
            '<marker id="pf-t" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
            '<path d="M0 0L10 5L0 10z" fill="currentColor"/></marker>'
            f'{sims}</defs></svg>')


# =============================================================================================
# Etiquetas y tickets
# =============================================================================================

def kick(cod: str, txt: str) -> str:
    return f'<p class="kick"><b>{cod}</b>{txt}</p>'


def codigo_barras(semilla: str, w: int = 150, h: int = 40) -> str:
    """Un código de barras decorativo, determinista a partir del texto."""
    hsh = hashlib.sha256(semilla.encode()).digest()
    x, o = 0.0, []
    i = 0
    while x < w - 4:
        bw = 1.2 + (hsh[i % len(hsh)] % 4) * 0.9
        gap = 1.4 + (hsh[(i * 7 + 3) % len(hsh)] % 3) * 0.9
        o.append(f'<rect x="{x:.1f}" y="0" width="{bw:.1f}" height="{h}"/>')
        x += bw + gap
        i += 1
    return f'<svg class="barras-cod" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true">{"".join(o)}</svg>'


def talon(clave: str, valor: str, texto: str, paso: int | None = None, cls: str = "", rotulo: str = "configuración") -> str:
    """La decisión de un experimento: un talón de ticket con la línea de configuración que deja
    (clave = valor) y, a la derecha, la decisión en una frase."""
    pa = f' data-paso="{paso}"' if paso is not None else ""
    return (f'<div class="talon {cls}"{pa}><div class="talon-cod"><span>{rotulo}</span><i>{clave} =</i><b>{valor}</b>'
            f'{codigo_barras(clave + valor, 150, 24)}</div><p class="talon-txt"><span>{texto}</span></p></div>')


def etq(pid: str, w: int, extra: str = "", nombre: str | None = None, estilo: str = "") -> str:
    """Etiqueta colgante de producto: foto, número de artículo y nombre."""
    if pid not in ITEMS:
        return ""
    nom = nombre if nombre is not None else ITEMS[pid].get("name", "")
    return (f'<div class="etq {extra}" style="width:{w}px;{estilo}">{producto(pid, w - 28)}'
            f'<span class="art">art. {pid}</span><span class="nom">{esc(nom)}</span></div>')


def consulta(q: str, n: int = 8, cls: str = "") -> str:
    """Una consulta o descripción de 8 líneas, como ficha impresa (rótulo: valor)."""
    filas = []
    for l in q.strip().splitlines()[:n]:
        if ":" in l:
            a, b = l.split(":", 1)
            filas.append(f'<div><dt>{esc(a.strip())}</dt><dd>{esc(b.strip())}</dd></div>')
    return f'<dl class="ficha {cls}">{"".join(filas)}</dl>'


def ranking(r: dict, n: int, w: int, marca: str = "el anotado") -> str:
    out = []
    for pos, pid in enumerate(r["ranked"][:n], start=1):
        ok = pid in r["relevant"]
        out.append(f'<div class="rk{" ok" if ok else ""}"><span class="rk-n">{pos}</span>{producto(pid, w)}'
                   f'{f"<span class=rk-ok>{marca}</span>" if ok else ""}</div>')
    return f'<div class="rk-fila">{"".join(out)}</div>'


def minimapa(n: int) -> str:
    """El esquema en chico, sin texto, con la etapa del experimento encendida (arriba a la derecha)."""
    return f'<div class="minimapa sin-texto" title="la etapa del flujo">{flujo(pines=[n], on=ETAPA_EXP[n], cls="mini")}</div>'


# =============================================================================================
# Gráficos (HTML y SVG, con el mismo estilo)
# =============================================================================================

def barras(filas, xmax=1.0, ticks=(0, 0.25, 0.5, 0.75, 1.0), paso=1, gana_paso=2, fmt=f2, titulo="", cls="",
           tick_fmt=None) -> str:
    """Barras horizontales. filas: dicts con letra, et, sub, v, ic, gana (bool), vtxt.
    Las barras se llenan en `paso` y la elegida se marca en `gana_paso`."""
    tf = tick_fmt or (lambda t: "0" if t == 0 else ("1" if t == 1 else fmt(t)))
    ejes = "".join(f'<span style="left:{t / xmax * 100:.2f}%">{tf(t)}</span>' for t in ticks)
    grilla = "".join(f'<i style="left:{t / xmax * 100:.2f}%"></i>' for t in ticks)
    out = [f'<div class="graf-b {cls}">']
    if titulo:
        out.append(f'<div class="gb-tit">{titulo}</div>')
    out.append(f'<div class="gb-fila gb-eje"><span></span><span class="gb-pista">{ejes}</span><span></span></div>')
    for f in filas:
        v = f["v"] / xmax * 100
        icx = ""
        if f.get("ic"):
            lo, hi = f["ic"]
            icx = f'<b class="gb-ic" style="left:{lo / xmax * 100:.2f}%;width:{(hi - lo) / xmax * 100:.2f}%"></b>'
        g = f' data-gana="{gana_paso}"' if f.get("gana") else ""
        letra = f'<em class="gb-l">{f["letra"]}</em>' if f.get("letra") else ""
        sub = f'<small>{f["sub"]}</small>' if f.get("sub") else ""
        out.append(f'<div class="gb-fila"{g}><span class="gb-et">{letra}<span>{f["et"]}{sub}</span></span>'
                   f'<span class="gb-pista">{grilla}<b class="gb-lleno" data-paso="{paso}" style="--v:{v:.2f}%"></b>'
                   f'<span class="gb-ics" data-paso="{paso}">{icx}</span></span>'
                   f'<span class="gb-val" data-paso="{paso}">{f.get("vtxt", fmt(f["v"]))}</span></div>')
    out.append("</div>")
    return "".join(out)


def lineas_svg(xs, series, ancho, alto, ymin, ymax, yticks, xlab="", xfmt=str, ml=80, mr=40, mt=30, mb=90,
               marcas=(), banda=None, logx=False, paso=1, gana_paso=2, yfmt=f2) -> str:
    """series: dicts con ys, clase ('sol'|'punt'), et, et_dy. marcas: (x, y, texto, dx, dy, ancla, gana)."""
    W = ancho - ml - mr
    H = alto - mt - mb
    lx = [math.log2(x) if logx else x for x in xs]
    x_min, x_max = min(lx), max(lx)
    sx = lambda v: ml + W * ((math.log2(v) if logx else v) - x_min) / (x_max - x_min)  # noqa: E731
    sy = lambda v: mt + H * (1 - (v - ymin) / (ymax - ymin))  # noqa: E731
    o = [f'<svg class="graf-l" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}">']
    for t in yticks:
        o.append(f'<line x1="{ml}" y1="{sy(t):.1f}" x2="{ml + W}" y2="{sy(t):.1f}" class="gl-grilla"/>'
                 f'<text x="{ml - 16}" y="{sy(t) + 7:.1f}" class="gl-eje" text-anchor="end">{yfmt(t)}</text>')
    yb = mt + H + 18
    for x in xs:
        o.append(f'<line x1="{sx(x):.1f}" y1="{mt}" x2="{sx(x):.1f}" y2="{mt + H}" class="gl-grilla v"/>'
                 f'<text x="{sx(x):.1f}" y="{yb + 24}" class="gl-eje" text-anchor="middle">{xfmt(x)}</text>')
    if xlab:
        o.append(f'<text x="{ml + W}" y="{yb + 62}" class="gl-xlab" text-anchor="end">{xlab}</text>')
    if banda:
        lo, hi = banda
        pts = [f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs, hi)] + [f"{sx(x):.1f},{sy(v):.1f}" for x, v in reversed(list(zip(xs, lo)))]
        o.append(f'<polygon points="{" ".join(pts)}" class="gl-banda" data-paso="{paso}"/>')
    for s in series:
        pts = " ".join(f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs, s["ys"]))
        cl = s.get("clase", "sol")
        o.append(f'<g class="gl-serie {cl}" data-paso="{s.get("paso", paso)}"><polyline points="{pts}" pathLength="1"/>')
        for x, v in zip(xs, s["ys"]):
            o.append(f'<circle cx="{sx(x):.1f}" cy="{sy(v):.1f}" r="{6 if cl == "sol" else 4.5}"/>')
        if s.get("et"):
            o.append(f'<text x="{sx(xs[-1]) + 16:.1f}" y="{sy(s["ys"][-1]) + 7 + s.get("et_dy", 0):.1f}" class="gl-et">{s["et"]}</text>')
        o.append("</g>")
    for x, v, t, dx, dy, anc, gana in marcas:
        g = f' data-gana="{gana_paso}"' if gana else ""
        o.append(f'<g class="gl-marca" data-paso="{paso}"{g}><circle cx="{sx(x):.1f}" cy="{sy(v):.1f}" r="11"/>'
                 f'<text x="{sx(x) + dx:.1f}" y="{sy(v) + dy:.1f}" text-anchor="{anc}">{t}</text></g>')
    o.append("</svg>")
    return "".join(o)


def letra(l: str) -> str:
    return f'<em class="letra">{l}</em>'


def variantes_html(vs, paso=None) -> str:
    pa = f' data-paso="{paso}"' if paso is not None else ""
    filas = "".join(f'<li>{letra(l)}<div><b>{esc(t)}</b><span>{d}</span></div></li>' for l, t, d in vs)
    return f'<ul class="variantes"{pa}>{filas}</ul>'
