"""La planta del flujo: el pipeline dibujado como la planta de una casa. Cada fase es un ambiente y
se pasa de uno al otro por una puerta, en fila (una enfilada). Los tres ambientes del indexing son
un pabellón aparte, que se construye una vez; el índice llega a la búsqueda por una pasarela.

Tres versiones del mismo dibujo:
- `tira()`: la planta grande, arriba de cada lámina del recorrido, con el ambiente actual encendido
  y el recorrido hecho en naranja; también la del mapa de experimentos.
- `llave()`: la planta de llave del cajetín (el pie), chiquita, para las láminas de experimento.
- `llamada()`: el círculo de detalle partido (experimento arriba, lámina abajo).
"""

from __future__ import annotations

from base import esc

FASES = [
    (1, "Catálogo"), (2, "Descripción"), (3, "Índice"),
    (4, "Foto + pedido"), (5, "Plan"), (6, "Búsqueda"), (7, "Elección"),
    (8, "Escena"), (9, "Imagen"), (10, "Control"), (11, "Lista + imagen"),
]
NOMBRE = dict(FASES)
OFFLINE = (1, 2, 3)

# la tira grande, en px de lámina (1776 de ancho)
W, G, H = 1776.0, 70.0, 84.0
TE, TP = 8.0, 4.0          # espesor del muro exterior y de los tabiques
YP0, YP1 = 48.0, 76.0      # el vano de las puertas (abajo, para no tapar el nombre)
YC = 62.0                  # la línea de circulación
YPAS = H + 24.0            # la pasarela del índice


def _geo(w_total: float, g: float):
    """x0, x1 de cada ambiente: tres en el pabellón, el patio, ocho en la casa."""
    w = (w_total - g) / 11
    out = {}
    for n, _ in FASES:
        x0 = (n - 1) * w if n <= 3 else 3 * w + g + (n - 4) * w
        out[n] = (x0, x0 + w)
    return out, w


def _c(r):
    return (r[0] + r[1]) / 2


def _rect(x0, y0, x1, y1, cls):
    return f'<rect class="{cls}" x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}"/>'


def _muros(R, te, tp, h, vanos_ext, vano_tab, abajo_vanos):
    """Los muros de los dos edificios: segmentos de rectángulo (el vano es lo que falta).
    vanos_ext: {('izq'|'der', edificio): (y0, y1)}; abajo_vanos: {n: (x0, x1)} en el muro de abajo."""
    o = []
    for ed, (a, b) in (("pab", (1, 3)), ("casa", (4, 11))):
        x0, x1 = R[a][0], R[b][1]
        # arriba entero
        o.append(_rect(x0, 0, x1, te, "muro"))
        # abajo, con los vanos de la pasarela
        cortes = sorted(v for n, v in abajo_vanos.items() if a <= n <= b)
        xa = x0
        for c0, c1 in cortes:
            o.append(_rect(xa, h - te, c0, h, "muro"))
            xa = c1
        o.append(_rect(xa, h - te, x1, h, "muro"))
        # costados, con la entrada (casa, izquierda) y la salida (casa, derecha)
        for lado, xx in (("izq", x0), ("der", x1 - te)):
            v = vanos_ext.get((lado, ed))
            if v:
                o.append(_rect(xx, te, xx + te, v[0], "muro"))
                o.append(_rect(xx, v[1], xx + te, h - te, "muro"))
            else:
                o.append(_rect(xx, te, xx + te, h - te, "muro"))
        # tabiques entre ambientes, con su puerta
        for n in range(a, b):
            xb = R[n][1]
            if vano_tab:
                o.append(_rect(xb - tp / 2, te, xb + tp / 2, vano_tab[0], "tab"))
                o.append(_rect(xb - tp / 2, vano_tab[1], xb + tp / 2, h - te, "tab"))
            else:
                o.append(_rect(xb - tp / 2, te, xb + tp / 2, h - te, "tab"))
    return "".join(o)


def _flecha(x, y, d, cls, s=7.0):
    """Punta de flecha en (x, y) mirando a d: 'e' (derecha), 'n' (arriba), 's' (abajo)."""
    if d == "e":
        p = f"{x:.1f},{y:.1f} {x - s * 1.5:.1f},{y - s:.1f} {x - s * 1.5:.1f},{y + s:.1f}"
    elif d == "n":
        p = f"{x:.1f},{y:.1f} {x - s:.1f},{y + s * 1.5:.1f} {x + s:.1f},{y + s * 1.5:.1f}"
    else:
        p = f"{x:.1f},{y:.1f} {x - s:.1f},{y - s * 1.5:.1f} {x + s:.1f},{y - s * 1.5:.1f}"
    return f'<polygon class="{cls}" points="{p}"/>'


def tira(actual: int | None = None, *, vistas=None, marcas=None, extra: str = "", top_pad=34.0,
         bottom_pad=50.0, attrs: str = "", cls: str = "") -> str:
    """La planta grande. actual: el ambiente encendido; vistas: los ya recorridos (por defecto,
    todos los anteriores al actual). marcas: {n: texto} chico en la esquina del ambiente."""
    R, w = _geo(W, G)
    if vistas is None:
        vistas = set(range(1, actual)) if actual else set()
    vistas = set(vistas)
    marcas = marcas or {}
    hecho = set(vistas) | ({actual} if actual else set())

    def est(n):
        return "act" if n == actual else ("vis" if n in vistas else "fut")

    o = []
    # pisos
    for n, nom in FASES:
        x0, x1 = R[n]
        o.append(f'<g class="loc {est(n)}" data-f="{n}">' + _rect(x0, 0, x1, H, "piso") + "</g>")
    # circulación: entre ambientes contiguos, la entrada, la salida, la pasarela y el reintento
    seg = []

    def linea(pts, ok, flechas):
        c = "circ hecho" if ok else "circ"
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        s = f'<path class="{c}" d="{d}"/>'
        s += "".join(_flecha(x, y, dd, "fle hecho" if ok else "fle") for x, y, dd in flechas)
        seg.append(s)

    for a, b in [(1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11)]:
        ok = a in hecho and b in hecho
        linea([(_c(R[a]), YC), (_c(R[b]), YC)], ok, [(R[a][1] + 13, YC, "e")])
    ent_x = R[4][0] - G * 0.62
    linea([(ent_x, YC), (_c(R[4]), YC)], 4 in hecho, [(R[4][0] + 13, YC, "e")])
    linea([(_c(R[11]), YC), (R[11][1] + 30, YC)], 11 in hecho, [(R[11][1] + 30, YC, "e")])
    linea([(_c(R[3]), YC + 4), (_c(R[3]), YPAS), (_c(R[6]), YPAS), (_c(R[6]), YC + 4)],
          3 in hecho and 6 in hecho, [(_c(R[6]), H - 2, "n")])
    # reintento: de Control vuelve a Imagen, por arriba
    x9, x10 = _c(R[9]) + 14, _c(R[10]) - 14
    ok = 10 in hecho
    seg.append(f'<path class="{"circ hecho" if ok else "circ"} rei" d="M{x10:.1f},{-2:.1f} C{x10:.1f},{-30:.1f} {x9:.1f},{-30:.1f} {x9:.1f},{-6:.1f}"/>'
               + _flecha(x9, 2, "s", "fle hecho" if ok else "fle", 6))
    o.append('<g class="circs">' + "".join(seg) + "</g>")
    # muros
    o.append(_muros(R, TE, TP, H, {("izq", "casa"): (YP0, YP1), ("der", "casa"): (YP0, YP1)}, (YP0, YP1),
                    {3: (_c(R[3]) - 14, _c(R[3]) + 14), 6: (_c(R[6]) - 14, _c(R[6]) + 14)}))
    # puertas: hoja y arco, abriendo hacia el ambiente siguiente
    pu = []
    for a in [1, 2, 4, 5, 6, 7, 8, 9, 10]:
        xb = R[a][1] + TP / 2
        r = YP1 - YP0
        pu.append(f'<path class="{"pta act" if a + 1 == actual else "pta"}" d="M{xb:.1f},{YP1:.1f} L{xb + r:.1f},{YP1:.1f} M{xb:.1f},{YP0:.1f} A{r:.1f},{r:.1f} 0 0 1 {xb + r:.1f},{YP1:.1f}"/>')
    o.append('<g class="ptas">' + "".join(pu) + "</g>")
    # número y nombre de cada ambiente
    for n, nom in FASES:
        x0, x1 = R[n]
        cx = (x0 + x1) / 2
        mk = ""
        if n in marcas:
            mk = f'<text class="mk" x="{x1 - TE - 6:.1f}" y="{TE + 17:.1f}">{esc(marcas[n])}</text>'
        o.append(f'<g class="rot {est(n)}" data-f="{n}"><circle class="num" cx="{cx:.1f}" cy="20" r="12"/>'
                 f'<text class="numt" x="{cx:.1f}" y="24.6">{n}</text>'
                 f'<text class="nom" x="{cx:.1f}" y="48">{esc(nom)}</text>{mk}</g>')
    # rótulos de las alas y de la pasarela
    o.append(f'<text class="ala" x="{R[1][0]:.1f}" y="-12">una vez · offline</text>'
             f'<text class="ala" x="{R[4][0]:.1f}" y="-12">en cada pedido</text>'
             f'<text class="ala r" x="{(x9 + x10) / 2:.1f}" y="-30" text-anchor="middle">otro intento</text>'
             f'<text class="pasl" x="{(_c(R[3]) + _c(R[6])) / 2:.1f}" y="{YPAS + 22:.1f}" text-anchor="middle">el índice</text>')
    o.append(extra)
    vb = f"-6 {-top_pad:.0f} {W + 46:.0f} {H + top_pad + bottom_pad:.0f}"
    return f'<svg class="pl {cls}" viewBox="{vb}" xmlns="http://www.w3.org/2000/svg" {attrs}>' + "".join(o) + "</svg>"


def alto_tira(ancho_px: float, top_pad=34.0, bottom_pad=50.0) -> float:
    return ancho_px * (H + top_pad + bottom_pad) / (W + 46)


def centro(n: int) -> float:
    R, _ = _geo(W, G)
    return _c(R[n])


def x0(n: int) -> float:
    R, _ = _geo(W, G)
    return R[n][0]


# ---------------------------------------------------------------- la planta de llave (pie)

def llave() -> str:
    """Chiquita, sin nombres ni puertas: los números y los muros. El JS enciende los ambientes de
    cada lámina (data-planta)."""
    w_t, g, h = 330.0, 16.0, 30.0
    R, w = _geo(w_t, g)
    o = []
    for n, _ in FASES:
        x0_, x1_ = R[n]
        o.append(f'<g class="loc" data-f="{n}">' + _rect(x0_, 0, x1_, h, "piso")
                 + f'<text class="numt" x="{(x0_ + x1_) / 2:.1f}" y="{h / 2 + 4.2:.1f}">{n}</text></g>')
    o.append(_muros(R, 2.4, 1.2, h, {}, None, {}))
    c3, c6 = _c(R[3]), _c(R[6])
    o.append(f'<path class="pas" d="M{c3:.1f},{h:.1f} L{c3:.1f},{h + 6:.1f} L{c6:.1f},{h + 6:.1f} L{c6:.1f},{h:.1f}"/>')
    return f'<svg class="pl llave" viewBox="-2 -2 {w_t + 4:.0f} {h + 10:.0f}" xmlns="http://www.w3.org/2000/svg">' + "".join(o) + "</svg>"


# ---------------------------------------------------------------- una planta chica (desafíos)

def enfilada(amb, w: float = 1500.0, h: float = 78.0, cls: str = "") -> str:
    """Una fila de ambientes con sus puertas, para comparar dos plantas chicas. amb: [(nombre,
    sub)]. Con cls="ante" es un anteproyecto: muros punteados, sin recorrido hecho."""
    n = len(amb)
    cw = w / n
    te, tp = 6.0, 3.0
    yp0, yp1 = h - 30.0, h - 9.0
    yc = (yp0 + yp1) / 2
    ante = "ante" in cls
    o = [_rect(i * cw, 0, (i + 1) * cw, h, "piso") for i in range(n)]
    o.append(f'<path class="circ{"" if ante else " hecho"}" d="M-20,{yc:.1f} L{w + 16:.1f},{yc:.1f}"/>'
             + _flecha(w + 24, yc, "e", "fle" if ante else "fle hecho"))
    o.append(_rect(0, 0, w, te, "muro") + _rect(0, h - te, w, h, "muro"))
    for xx in (0, w - te):
        o.append(_rect(xx, te, xx + te, yp0, "muro") + _rect(xx, yp1, xx + te, h - te, "muro"))
    r = yp1 - yp0
    for i in range(1, n):
        xb = i * cw
        o.append(_rect(xb - tp / 2, te, xb + tp / 2, yp0, "tab") + _rect(xb - tp / 2, yp1, xb + tp / 2, h - te, "tab"))
        o.append(f'<path class="pta" d="M{xb + tp / 2:.1f},{yp1:.1f} L{xb + tp / 2 + r:.1f},{yp1:.1f} '
                 f'M{xb + tp / 2:.1f},{yp0:.1f} A{r:.1f},{r:.1f} 0 0 1 {xb + tp / 2 + r:.1f},{yp1:.1f}"/>')
    for i, (nom, sub) in enumerate(amb):
        cx = i * cw + cw / 2
        o.append(f'<text class="nom" x="{cx:.1f}" y="{27 if sub else 32}">{esc(nom)}</text>')
        if sub:
            o.append(f'<text class="subn" x="{cx:.1f}" y="44">{esc(sub)}</text>')
    return (f'<svg class="pl enf {cls}" viewBox="-24 -3 {w + 56:.0f} {h + 6:.0f}" xmlns="http://www.w3.org/2000/svg">'
            + "".join(o) + "</svg>")


# ---------------------------------------------------------------- la llamada de detalle

def llamada(cx, cy, exp, lam, tipo="si", r=22.0, ir=None) -> str:
    """El círculo de detalle partido: arriba el experimento, abajo la lámina donde está."""
    d = f' data-ir="{ir}"' if ir is not None else ""
    return (f'<g class="ll {tipo}"{d}><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
            f'<line x1="{cx - r:.1f}" y1="{cy:.1f}" x2="{cx + r:.1f}" y2="{cy:.1f}"/>'
            f'<text class="le" x="{cx:.1f}" y="{cy - 5.5:.1f}">{esc(exp)}</text>'
            f'<text class="ln" x="{cx:.1f}" y="{cy + 15.5:.1f}">{esc(lam)}</text></g>')


CSS_P = r"""
/* ---------- la planta del flujo */
.pl{display:block;overflow:visible}
.pl .piso{fill:var(--hoja)}
.pl .loc.vis .piso{fill:#E2E9FB}
.pl .loc.act .piso{fill:var(--cobalto)}
.pl .muro{fill:url(#rayado);stroke:var(--tinta);stroke-width:1.1}
.pl .tab{fill:var(--tinta);stroke:none}
.pl .pta{fill:none;stroke:var(--tinta-3);stroke-width:1}
.pl .pta.act{stroke:rgba(255,255,255,.75)}
.pl .circ{fill:none;stroke:var(--hilo-2);stroke-width:1.6;stroke-dasharray:5 5}
.pl .circ.hecho{stroke:var(--naranja);stroke-width:3;stroke-dasharray:none}
.pl .fle{fill:var(--hilo-2)}.pl .fle.hecho{fill:var(--naranja)}
.pl .num{fill:var(--hoja);stroke:var(--hilo-2);stroke-width:1.3}
.pl .numt{font:700 13px var(--mono);fill:var(--tinta-3);text-anchor:middle}
.pl .nom{font:600 20px var(--sans);font-stretch:82%;fill:var(--tinta-2);text-anchor:middle}
.pl .mk{font:700 12.5px var(--mono);fill:var(--naranja);text-anchor:end;letter-spacing:.03em}
.pl .rot.vis .num{stroke:var(--cobalto)}.pl .rot.vis .numt{fill:var(--cobalto)}.pl .rot.vis .nom{fill:var(--tinta)}
.pl .rot.act .num{fill:#fff;stroke:#fff}.pl .rot.act .numt{fill:var(--cobalto)}.pl .rot.act .nom{fill:#fff}
.pl .rot.act .mk{fill:#fff}
.pl .ala{font:400 15px var(--mono);fill:var(--tinta-3)}
.pl .ala.r{font-size:13px}
.pl .pasl{font:400 13px var(--mono);fill:var(--tinta-3)}
.pl .pas{fill:none;stroke:var(--tinta-3);stroke-width:1}
/* llamadas de detalle (mapa de experimentos) */
.pl .ll circle{fill:#fff;stroke:var(--cobalto);stroke-width:2}
.pl .ll line{stroke:var(--cobalto);stroke-width:1.4}
.pl .ll .le{font:700 14.5px var(--mono);fill:var(--cobalto);text-anchor:middle}
.pl .ll .ln{font:400 13px var(--mono);fill:var(--tinta-2);text-anchor:middle}
.pl .ll.prueba circle,.pl .ll.tram circle{stroke:var(--tinta-2);stroke-dasharray:4 3}.pl .ll.prueba line,.pl .ll.tram line{stroke:var(--tinta-2)}
.pl .ll.prueba .le,.pl .ll.tram .le{fill:var(--tinta)}
.pl .ll.pend circle{stroke:var(--cota);stroke-dasharray:4 3}.pl .ll.pend line{stroke:var(--cota)}.pl .ll.pend .le{fill:var(--cota)}
.pl [data-ir]{cursor:pointer}
.pl .guia{fill:none;stroke:var(--tinta-2);stroke-width:1.2}
.pl .guia-p{fill:var(--tinta-2)}
.pl .lt{font:600 17px var(--sans);font-stretch:82%;fill:var(--tinta)}
.pl .ld{font:400 13px var(--mono);fill:var(--cobalto)}
.pl .ll.prueba~.ld,.pl .ld.prueba,.pl .ld.tram{fill:var(--tinta-2)}
.pl .ld.pend{fill:var(--cota)}
/* el cuadro de locales (lámina de la planta) */
.pl .cl{font:400 16px var(--mono);fill:var(--tinta-2)}
.pl .cl b,.pl .clb{font-weight:700;fill:var(--tinta)}
.pl .clc{font:700 15px var(--mono);fill:var(--cobalto)}
.pl .clc.g{fill:var(--tinta-3);font-weight:400}
/* la planta de llave, en el cajetín */
#pie .p-planta{width:380px;justify-content:center;padding:0 18px}
#pie .p-planta.vacia{display:none}
#pie .p-planta svg{width:344px;height:46px}
.pl.llave .piso{fill:var(--papel)}
.pl.llave .loc.act .piso{fill:var(--cobalto)}
.pl.llave .numt{font:700 11px var(--mono);fill:var(--tinta-3)}
.pl.llave .loc.act .numt{fill:#fff}
.pl.llave .muro{fill:var(--tinta);stroke:none}
#pie.sobre-plano .pl.llave .piso{fill:var(--plano-3)}
#pie.sobre-plano .pl.llave .muro,#pie.sobre-plano .pl.llave .tab{fill:var(--trazo)}
#pie.sobre-plano .pl.llave .numt{fill:var(--trazo)}
#pie.sobre-plano .pl.llave .loc.act .piso{fill:var(--naranja)}
#pie.sobre-plano .pl.llave .loc.act .numt{fill:var(--plano)}
#pie.sobre-plano .pl.llave .pas{stroke:var(--trazo)}
/* una planta chica (desafíos) */
.pl.enf .nom{font:600 20px var(--sans);font-stretch:84%;fill:var(--tinta);text-anchor:middle}
.pl.enf .subn{font:400 13.5px var(--mono);fill:var(--tinta-3);text-anchor:middle}
.pl.enf.ante .muro{fill:var(--papel);stroke:var(--tinta-3);stroke-dasharray:5 4}
.pl.enf.ante .tab{fill:var(--tinta-3)}
.pl.enf.ante .piso{fill:var(--papel)}
.pl.enf.ante .nom{fill:var(--tinta-2)}
/* el banco de prueba, en el mapa */
.pl .banco{fill:none;stroke:var(--tinta-2);stroke-width:1.2;stroke-dasharray:6 5}
.pl .bk{font:700 15px var(--mono);fill:var(--tinta)}
.pl .bs{font:400 13px var(--mono);fill:var(--tinta-3)}
"""
