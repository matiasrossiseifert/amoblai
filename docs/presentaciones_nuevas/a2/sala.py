"""La habitación: un living dibujado en axonometría (dimétrica), en centímetros.

Es la columna vertebral de la presentación. Empieza vacía y se va amoblando con los mismos
productos que eligió amoblai para el living de la portada (sofá, alfombra, mesa ratona, mueble de
TV, lámpara de pie, almohadones, planta y cortinas). Las etapas del flujo se dibujan como capas
sobre ella y, en los pasos a futuro, aparecen las cajas 3D con las medidas del catálogo.

Las medidas del cuarto NO son datos: el dibujo no lleva números en sus cotas (solo «?» o
rótulos). Los únicos números de medidas que aparecen salen de la metadata del catálogo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

W, D, H = 430.0, 540.0, 262.0  # proporciones del dibujo (no son medidas del departamento)
T = 14.0  # espesor de muro


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


@dataclass
class Proj:
    """Dimétrica: x a la derecha bajando ax°, y a la izquierda bajando ay° y escalado sy."""
    s: float = 1.0
    ox: float = 0.0
    oy: float = 0.0
    ax: float = 14.0
    ay: float = 40.0
    sy: float = 0.72

    def __post_init__(self):
        a, b = math.radians(self.ax), math.radians(self.ay)
        self.cx, self.sx_ = math.cos(a), math.sin(a)
        self.cy, self.sy_ = math.cos(b) * self.sy, math.sin(b) * self.sy
        # dirección de la vista (lo que se proyecta a un mismo punto), apunta al observador
        dx = self.cy / self.cx
        self.view = (dx, 1.0, dx * self.sx_ + self.sy_)

    def p(self, x, y, z):
        return (self.ox + self.s * (x * self.cx - y * self.cy),
                self.oy + self.s * (x * self.sx_ + y * self.sy_ - z))

    def depth(self, x, y, z):
        v = self.view
        return x * v[0] + y * v[1] + z * v[2]


def pts(P: Proj, ps) -> str:
    return " ".join(f"{a:.1f},{b:.1f}" for a, b in (P.p(*q) for q in ps))


# ---------------------------------------------------------------- primitivas

@dataclass
class Box:
    x0: float
    y0: float
    z0: float
    x1: float
    y1: float
    z1: float
    k: str = ""            # pieza a la que pertenece (para resaltar)
    cls: str = ""          # clases extra
    front: list = field(default_factory=list)  # líneas extra sobre la cara +y: [(x, z0, x, z1)…]
    side: list = field(default_factory=list)   # líneas extra sobre la cara +x: [(y, z0, y, z1)…]
    top: list = field(default_factory=list)    # líneas extra sobre la tapa: [(x0,y0,x1,y1)…]
    hide: str = ""         # caras que no se dibujan: 'x', 'y', 't'

    def bbox(self):
        return self.x0, self.y0, self.z0, self.x1, self.y1, self.z1

    def svg(self, P: Proj) -> str:
        x0, y0, z0, x1, y1, z1 = self.bbox()
        o = []
        if "y" not in self.hide:  # cara que mira al observador (+y)
            o.append(f'<polygon class="fy" points="{pts(P, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)])}"/>')
            for a, b, c, d in self.front:
                (p1, p2) = P.p(a, y1, b), P.p(c, y1, d)
                o.append(f'<line class="det" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}"/>')
        if "x" not in self.hide:  # cara +x
            o.append(f'<polygon class="fx" points="{pts(P, [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)])}"/>')
            for a, b, c, d in self.side:
                (p1, p2) = P.p(x1, a, b), P.p(x1, c, d)
                o.append(f'<line class="det" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}"/>')
        if "t" not in self.hide:
            o.append(f'<polygon class="ft" points="{pts(P, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])}"/>')
            for a, b, c, d in self.top:
                (p1, p2) = P.p(a, b, z1), P.p(c, d, z1)
                o.append(f'<line class="det" x1="{p1[0]:.1f}" y1="{p1[1]:.1f}" x2="{p2[0]:.1f}" y2="{p2[1]:.1f}"/>')
        return "".join(o)


@dataclass
class Cyl:
    cx: float
    cy: float
    z0: float
    z1: float
    r: float
    r1: float | None = None  # radio arriba (tronco de cono)
    k: str = ""
    cls: str = ""
    n: int = 28

    def bbox(self):
        r = max(self.r, self.r1 or self.r)
        return self.cx - r, self.cy - r, self.z0, self.cx + r, self.cy + r, self.z1

    def svg(self, P: Proj) -> str:
        r0, r1 = self.r, (self.r1 if self.r1 is not None else self.r)
        ang = [2 * math.pi * i / self.n for i in range(self.n)]
        bot = [(self.cx + r0 * math.cos(a), self.cy + r0 * math.sin(a), self.z0) for a in ang]
        top = [(self.cx + r1 * math.cos(a), self.cy + r1 * math.sin(a), self.z1) for a in ang]
        # silueta: en pantalla, la envolvente de la tapa y la base
        v = P.view
        vis = [math.cos(a) * v[0] + math.sin(a) * v[1] > 0 for a in ang]
        # el tramo visible del costado, de un borde de la silueta al otro
        idx = [i for i in range(self.n) if vis[i]]
        start = next(i for i in range(self.n) if vis[i] and not vis[i - 1])
        seq = [(start + j) % self.n for j in range(len(idx))]
        side = [bot[i] for i in seq] + [top[i] for i in reversed(seq)]
        return (f'<polygon class="fx" points="{pts(P, side)}"/>'
                f'<polygon class="ft" points="{pts(P, top)}"/>')


@dataclass
class Raw:
    """SVG ya proyectado (hojas, arcos…), con una caja para ordenar."""
    bb: tuple
    fn: object
    k: str = ""
    cls: str = ""

    def bbox(self):
        return self.bb

    def svg(self, P: Proj) -> str:
        return self.fn(P)


def _overlap(a, b) -> bool:
    return a[0] < b[3] and b[0] < a[3] and a[1] < b[4] and b[1] < a[4] and a[2] < b[5] and b[2] < a[5]


def order(prims, P: Proj):
    """Pintor: A antes que B si A queda detrás (separados en x, y o z hacia el observador)."""
    n = len(prims)
    bbs = [p.bbox() for p in prims]
    before = [set() for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a, b = bbs[i], bbs[j]
            if a[3] <= b[0] + 1e-6 or a[4] <= b[1] + 1e-6 or a[5] <= b[2] + 1e-6:
                # i está detrás de j en algún eje: solo importa si en el otro sentido no pasa lo mismo
                if not (b[3] <= a[0] + 1e-6 or b[4] <= a[1] + 1e-6 or b[5] <= a[2] + 1e-6):
                    before[j].add(i)
    dk = [P.depth((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2) for b in bbs]
    done, out = set(), []
    remaining = sorted(range(n), key=lambda i: dk[i])
    while remaining:
        for i in remaining:
            if before[i] <= done:
                break
        else:
            i = remaining[0]
        remaining.remove(i)
        done.add(i)
        out.append(prims[i])
    return out


# ---------------------------------------------------------------- los muebles del living
# Cada pieza: lista de primitivas. Las medidas son del dibujo; las del catálogo van aparte.

def sofa():
    k = "sofa"
    x0, x1, ya, yb = 2, 98, 150, 382
    arm = 26
    o = [Box(x0, ya, 0, x1, yb, 14, k, "zocalo"),
         Box(x0, ya + arm, 14, x1, yb - arm, 40, k),
         Box(x0, ya, 40, 26, yb, 84, k),
         Box(x0, ya, 14, x1, ya + arm, 64, k, front=[]),
         Box(x0, yb - arm, 14, x1, yb, 64, k)]
    mid = (ya + arm + yb - arm) / 2
    o += [Box(26, ya + arm, 40, x1 - 3, mid - 1, 50, k), Box(26, mid + 1, 40, x1 - 3, yb - arm, 50, k)]
    return o


def almohadones():
    k = "almohadones"
    return [Box(27, 186, 50, 40, 232, 92, k, "verde"), Box(27, 300, 50, 40, 346, 92, k, "verde")]


def alfombra():
    k = "alfombra"
    x0, y0, x1, y1 = 122, 150, 300, 398
    lines = [(x0 + 8, y0 + 8, x1 - 8, y0 + 8), (x1 - 8, y0 + 8, x1 - 8, y1 - 8),
             (x1 - 8, y1 - 8, x0 + 8, y1 - 8), (x0 + 8, y1 - 8, x0 + 8, y0 + 8)]
    return [Box(x0, y0, 0, x1, y1, 2.5, k, "lana", top=lines)]


def mesa_ratona():
    k = "mesa"
    x0, y0, x1, y1 = 172, 238, 248, 314
    o = [Box(x0, y0, 40, x1, y1, 45, k)]
    for (a, b) in ((x0 + 6, y0 + 6), (x1 - 10, y0 + 6), (x0 + 6, y1 - 10), (x1 - 10, y1 - 10)):
        o.append(Box(a, b, 0, a + 4, b + 4, 40, k, "pata"))
    return o


def mueble_tv():
    k = "tv"
    x0, x1, y0, y1 = W - 44, W - 2, 176, 356
    o = [Box(x0, y0, 12, x1, y1, 52, k, front=[(x0 + 21, 14, x0 + 21, 50)])]
    for (a, b) in ((x0 + 4, y0 + 4), (x0 + 4, y1 - 8), (x1 - 8, y0 + 4), (x1 - 8, y1 - 8)):
        o.append(Box(a, b, 0, a + 4, b + 4, 12, k, "pata"))
    return o


def lampara():
    k = "lampara"
    cx, cy = 52, 102
    return [Cyl(cx, cy, 0, 3, 16, k=k),
            Box(cx - 1.6, cy - 1.6, 3, cx + 1.6, cy + 1.6, 140, k, "pata"),
            Box(cx - 20, cy - 14, 140, cx + 20, cy + 14, 182, k, "pantalla")]


def planta():
    k = "planta"
    cx, cy = W - 42, 44

    def hojas(P):
        bx, by = P.p(cx, cy, 44)
        s = P.s
        o = []
        fr = [(-52, -150, -94, -86), (-20, -178, -40, -120), (14, -186, 30, -128), (44, -160, 92, -104),
              (-70, -110, -118, -56), (70, -120, 120, -70), (-6, -150, -2, -96), (30, -96, 64, -40),
              (-36, -92, -70, -36)]
        for (qx, qy, ex, ey) in fr:
            o.append(f'<path class="hoja" d="M{bx:.1f},{by:.1f} Q{bx + qx * s * .55:.1f},{by + qy * s * .55:.1f} '
                     f'{bx + ex * s * .62:.1f},{by + ey * s * .62:.1f}"/>')
            # foliolos: trazos cortos a lo largo de cada fronda
            for t in (0.45, 0.6, 0.75, 0.9):
                mx = (1 - t) ** 2 * bx + 2 * (1 - t) * t * (bx + qx * s * .55) + t * t * (bx + ex * s * .62)
                my = (1 - t) ** 2 * by + 2 * (1 - t) * t * (by + qy * s * .55) + t * t * (by + ey * s * .62)
                L = 13 * s * (1.1 - t * .5)
                o.append(f'<path class="hoja f" d="M{mx - L * .6:.1f},{my - L * .2:.1f} L{mx:.1f},{my:.1f} '
                         f'L{mx + L * .6:.1f},{my - L * .3:.1f}"/>')
        return "".join(o)

    return [Cyl(cx, cy, 0, 44, 20, 24, k=k, cls="maceta"),
            Raw((cx - 60, cy - 60, 44, cx + 60, cy + 60, 210), hojas, k)]


def cortinas():
    k = "cortinas"
    o = []
    for (a, b) in ((86, 132), (322, 368)):
        folds = [(a + (b - a) * t / 6, 2, a + (b - a) * t / 6, 238) for t in range(1, 6)]
        o.append(Box(a, 5, 0, b, 15, 242, k, "tela", front=folds))
    o.append(Box(78, 7, 242, 376, 11, 246, k, "pata"))
    return o


PIEZAS = {
    "alfombra": alfombra, "sofa": sofa, "mesa": mesa_ratona, "tv": mueble_tv, "lampara": lampara,
    "almohadones": almohadones, "planta": planta, "cortinas": cortinas,
}
ORDEN = ["alfombra", "sofa", "tv", "mesa", "lampara", "cortinas", "planta", "almohadones"]
NOMBRE = {"alfombra": "alfombra", "sofa": "sofá", "mesa": "mesa ratona", "tv": "mueble de TV",
          "lampara": "lámpara de pie", "almohadones": "almohadones", "planta": "planta",
          "cortinas": "cortinas"}
# dónde anclar el rótulo de cada pieza (punto 3D)
ANCLA = {"alfombra": (211, 398, 2), "sofa": (50, 382, 64), "mesa": (210, 314, 45), "tv": (W - 2, 356, 52),
         "lampara": (52, 116, 182), "almohadones": (34, 232, 92), "planta": (W - 42, 44, 150),
         "cortinas": (345, 15, 200)}
# caja envolvente de cada pieza (para fantasmas, cajas 3D y resaltados)
CAJA = {"alfombra": (122, 150, 0, 300, 398, 2.5), "sofa": (2, 150, 0, 98, 382, 84),
        "mesa": (172, 238, 0, 248, 314, 45), "tv": (W - 44, 176, 0, W - 2, 356, 52),
        "lampara": (32, 88, 0, 72, 116, 182), "almohadones": (27, 186, 50, 40, 346, 92),
        "planta": (W - 66, 20, 0, W - 18, 68, 190), "cortinas": (86, 5, 0, 368, 15, 246)}


# ---------------------------------------------------------------- la cáscara

def cascara(P: Proj, *, interrogantes=False, cotas=True, rotulos_cota=("ancho", "fondo", "alto"),
            grilla=True) -> str:
    """Los dos muros del fondo (con espesor y corte), el piso, la ventana-balcón y el pie de los
    otros dos muros, cortados a ras del piso como en una planta."""
    o = ['<g class="cascara">']
    # piso
    o.append(f'<polygon class="piso" points="{pts(P, [(0, 0, 0), (W, 0, 0), (W, D, 0), (0, D, 0)])}"/>')
    if grilla:
        g = []
        step = 45
        for i in range(1, int(W // step) + 1):
            x = i * step
            if x < W - 2:
                a, b = P.p(x, 0, 0), P.p(x, D, 0)
                g.append(f"M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}")
        for j in range(1, int(D // step) + 1):
            y = j * step
            if y < D - 2:
                a, b = P.p(0, y, 0), P.p(W, y, 0)
                g.append(f"M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}")
        o.append(f'<path class="grilla" d="{"".join(g)}"/>')
    # pie de los muros cortados (derecho y del frente), con rayado
    o.append(f'<polygon class="corte" points="{pts(P, [(W, -T, 0), (W + T, -T, 0), (W + T, D + T, 0), (W, D + T, 0), (W, D, 0), (W, 0, 0)])}"/>')
    o.append(f'<polygon class="corte" points="{pts(P, [(-T, D, 0), (W, D, 0), (W, D + T, 0), (-T, D + T, 0)])}"/>')
    # muro izquierdo (x = 0): cara interior, canto superior cortado y canto del frente
    o.append(f'<polygon class="muro" points="{pts(P, [(0, 0, 0), (0, D, 0), (0, D, H), (0, 0, H)])}"/>')
    o.append(f'<polygon class="corte" points="{pts(P, [(-T, -T, H), (0, 0, H), (0, D, H), (-T, D, H)])}"/>')
    o.append(f'<polygon class="canto" points="{pts(P, [(-T, D, 0), (0, D, 0), (0, D, H), (-T, D, H)])}"/>')
    # muro del fondo (y = 0), con la abertura del balcón
    wx0, wx1, wz1 = 128, 326, 232
    o.append(f'<path class="muro" fill-rule="evenodd" d="M{pts(P, [(0, 0, 0), (W, 0, 0), (W, 0, H), (0, 0, H)]).replace(" ", "L")}Z '
             f'M{pts(P, [(wx0, 0, 0), (wx1, 0, 0), (wx1, 0, wz1), (wx0, 0, wz1)]).replace(" ", "L")}Z"/>')
    o.append(f'<polygon class="corte" points="{pts(P, [(0, -T, H), (W + T, -T, H), (W, 0, H), (0, 0, H)])}"/>')
    o.append(f'<polygon class="canto" points="{pts(P, [(W, -T, 0), (W + T, -T, 0), (W + T, -T, H), (W, -T, H)])}"/>')
    # la abertura: jambas y dintel con espesor, y el vidrio del fondo
    o.append(f'<polygon class="vano" points="{pts(P, [(wx0, -T, 0), (wx1, -T, 0), (wx1, -T, wz1), (wx0, -T, wz1)])}"/>')
    o.append(f'<polygon class="jamba" points="{pts(P, [(wx0, 0, 0), (wx0, -T, 0), (wx0, -T, wz1), (wx0, 0, wz1)])}"/>')
    o.append(f'<polygon class="jamba" points="{pts(P, [(wx0, 0, wz1), (wx1, 0, wz1), (wx1, -T, wz1), (wx0, -T, wz1)])}"/>')
    # marcos del ventanal corredizo (dos hojas)
    mid = (wx0 + wx1) / 2
    fr = 5
    for (a, b) in ((wx0, mid + 4), (mid - 4, wx1)):
        o.append(f'<path class="marco" fill-rule="evenodd" d="M{pts(P, [(a, -T + 3, 0), (b, -T + 3, 0), (b, -T + 3, wz1), (a, -T + 3, wz1)]).replace(" ", "L")}Z '
                 f'M{pts(P, [(a + fr, -T + 3, fr), (b - fr, -T + 3, fr), (b - fr, -T + 3, wz1 - fr), (a + fr, -T + 3, wz1 - fr)]).replace(" ", "L")}Z"/>')
    # baranda del balcón, del otro lado del vidrio
    by = -T - 2
    for z in (96, 100):
        a, b = P.p(wx0 + 6, by, z), P.p(wx1 - 6, by, z)
        o.append(f'<line class="baranda" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    for i in range(1, 12):
        x = wx0 + (wx1 - wx0) * i / 12
        a, b = P.p(x, by, 8), P.p(x, by, 96)
        o.append(f'<line class="baranda f" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    # zócalo
    for (p1, p2) in (((0, 0, 7), (wx0, 0, 7)), ((wx1, 0, 7), (W, 0, 7)), ((0, 0, 7), (0, D, 7))):
        a, b = P.p(*p1), P.p(*p2)
        o.append(f'<line class="zoc" x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
    # equipo de aire sobre el ventanal (está en la foto)
    o.append('<g class="aire">' + Box(236, 0, 222, 318, 20, 250, "", "aire").svg(P) + "</g>")
    if cotas:
        o.append(cotas_cuarto(P, rotulos_cota, interrogantes))
    o.append("</g>")
    return "".join(o)


def cota(P: Proj, a, b, off, texto="", cls="cota", lado=1, rot=True, fs=15) -> str:
    """Cota 3D: de a a b, desplazada off (vector 3D), con líneas de referencia y remates a 45°."""
    A = (a[0] + off[0], a[1] + off[1], a[2] + off[2])
    B = (b[0] + off[0], b[1] + off[1], b[2] + off[2])
    pa, pb = P.p(*A), P.p(*B)
    ra, rb = P.p(*a), P.p(*b)
    ang = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
    o = [f'<g class="{cls}">']
    # líneas de referencia
    for (r, q) in ((ra, pa), (rb, pb)):
        ux, uy = q[0] - r[0], q[1] - r[1]
        L = math.hypot(ux, uy) or 1
        o.append(f'<line class="ref" x1="{r[0] + ux / L * 4:.1f}" y1="{r[1] + uy / L * 4:.1f}" '
                 f'x2="{q[0] + ux / L * 6:.1f}" y2="{q[1] + uy / L * 6:.1f}"/>')
    o.append(f'<line x1="{pa[0]:.1f}" y1="{pa[1]:.1f}" x2="{pb[0]:.1f}" y2="{pb[1]:.1f}"/>')
    # remates a 45° respecto de la línea
    t = math.radians(ang + 45)
    for q in (pa, pb):
        dx, dy = 6 * math.cos(t), 6 * math.sin(t)
        o.append(f'<line class="tick" x1="{q[0] - dx:.1f}" y1="{q[1] - dy:.1f}" x2="{q[0] + dx:.1f}" y2="{q[1] + dy:.1f}"/>')
    if texto:
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        a2 = ang
        if a2 > 90:
            a2 -= 180
        if a2 < -90:
            a2 += 180
        nx, ny = math.sin(math.radians(a2)), -math.cos(math.radians(a2))
        tx, ty = mx + nx * 9 * lado, my + ny * 9 * lado
        tr = f' transform="rotate({a2:.1f} {tx:.1f} {ty:.1f})"' if rot else ""
        o.append(f'<text class="ct" x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" font-size="{fs}"{tr}>{esc(texto)}</text>')
    o.append("</g>")
    return "".join(o)


def cotas_cuarto(P: Proj, rot=("ancho", "fondo", "alto"), q=False) -> str:
    t = (lambda s: s + " = ?") if q else (lambda s: s)
    o = [cota(P, (0, D + T, 0), (W + T, D + T, 0), (0, 46, 0), t(rot[0]), lado=-1),
         cota(P, (W + T, 0, 0), (W + T, D + T, 0), (46, 0, 0), t(rot[1]), lado=-1),
         cota(P, (-T, D + T, 0), (-T, D + T, H), (-38, 0, 0), t(rot[2]), lado=1)]
    return "".join(o)


# ---------------------------------------------------------------- escenas

def prims_de(piezas):
    out = []
    for k in piezas:
        out += PIEZAS[k]()
    return out


def muebles(P: Proj, piezas, nuevas=(), apagadas=(), cls_extra=None) -> str:
    """Dibuja las piezas ordenadas; las 'nuevas' se resaltan, las 'apagadas' se atenúan."""
    prims = prims_de(piezas)
    o = []
    for p in order(prims, P):
        c = ["m", p.cls]
        if p.k in nuevas:
            c.append("nuevo")
        if p.k in apagadas:
            c.append("apagado")
        if cls_extra and p.k in cls_extra:
            c.append(cls_extra[p.k])
        o.append(f'<g class="{" ".join(x for x in c if x)}" data-k="{p.k}">{p.svg(P)}</g>')
    return "".join(o)


def caja_alambre(P: Proj, bb, cls="fantasma", k="") -> str:
    """Una caja de alambre: aristas visibles enteras, ocultas punteadas."""
    x0, y0, z0, x1, y1, z1 = bb
    V = {(i, j, l): P.p((x0, x1)[i], (y0, y1)[j], (z0, z1)[l]) for i in (0, 1) for j in (0, 1) for l in (0, 1)}
    edges = []
    for i in (0, 1):
        for j in (0, 1):
            edges.append(((i, j, 0), (i, j, 1)))
    for i in (0, 1):
        for l in (0, 1):
            edges.append(((i, 0, l), (i, 1, l)))
    for j in (0, 1):
        for l in (0, 1):
            edges.append(((0, j, l), (1, j, l)))
    hidden_v = (0, 0, 0)  # el vértice del fondo-abajo queda oculto
    o = [f'<g class="{cls}" data-k="{k}">']
    o.append(f'<polygon class="cf" points="{" ".join(f"{V[v][0]:.1f},{V[v][1]:.1f}" for v in [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)])}"/>')
    o.append(f'<polygon class="cf2" points="{" ".join(f"{V[v][0]:.1f},{V[v][1]:.1f}" for v in [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)])}"/>')
    o.append(f'<polygon class="ct2" points="{" ".join(f"{V[v][0]:.1f},{V[v][1]:.1f}" for v in [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)])}"/>')
    for a, b in edges:
        hid = hidden_v in (a, b)
        o.append(f'<line class="{"oc" if hid else "ar"}" x1="{V[a][0]:.1f}" y1="{V[a][1]:.1f}" x2="{V[b][0]:.1f}" y2="{V[b][1]:.1f}"/>')
    o.append("</g>")
    return "".join(o)


def rotulo(P: Proj, k: str, texto: str, dx: float, dy: float, cls="rot", sub="", anchor=None, num=None, pt=None) -> str:
    """Rótulo con línea de llamada desde el ancla de la pieza (o desde pt, un punto 3D)."""
    ax, ay = P.p(*(pt or ANCLA[k]))
    tx, ty = ax + dx, ay + dy
    an = anchor or ("start" if dx >= 0 else "end")
    pad = 8 if an == "start" else -8
    o = [f'<g class="{cls}" data-k="{k}">',
         f'<circle class="pto" cx="{ax:.1f}" cy="{ay:.1f}" r="3.6"/>',
         f'<path class="lin" d="M{ax:.1f},{ay:.1f} L{tx:.1f},{ty:.1f} L{tx + pad * 2.2:.1f},{ty:.1f}"/>']
    x = tx + pad * 3
    if num is not None:
        o.append(f'<circle class="num" cx="{x + (14 if an == "start" else -14):.1f}" cy="{ty:.1f}" r="15"/>'
                 f'<text class="numt" x="{x + (14 if an == "start" else -14):.1f}" y="{ty + 5.5:.1f}" text-anchor="middle">{num}</text>')
        x += 36 if an == "start" else -36
    o.append(f'<text class="rt" x="{x:.1f}" y="{ty + 6:.1f}" text-anchor="{an}">{esc(texto)}</text>')
    if sub:
        o.append(f'<text class="rs" x="{x:.1f}" y="{ty + 30:.1f}" text-anchor="{an}">{esc(sub)}</text>')
    o.append("</g>")
    return "".join(o)


def viewbox(P: Proj, pad=(40, 40, 40, 40), m=60):
    """Caja de la cáscara proyectada (m: margen para las cotas)."""
    corners = [(x, y, z) for x in (-T - m, W + T + m) for y in (-T, D + T + m) for z in (0, H)]
    xs, ys = zip(*(P.p(*c) for c in corners))
    return min(xs) - pad[3], min(ys) - pad[0], max(xs) - min(xs) + pad[1] + pad[3], max(ys) - min(ys) + pad[0] + pad[2]


def sala(piezas=(), nuevas=(), apagadas=(), *, cls="sala", extra="", extra_bajo="", cotas=True,
         interrogantes=False, rotulos_cota=("ancho", "fondo", "alto"), P: Proj | None = None,
         vb=None, grilla=True, attrs="") -> str:
    P = P or Proj()
    x, y, w, h = vb or viewbox(P)
    return (f'<svg class="{cls}" viewBox="{x:.0f} {y:.0f} {w:.0f} {h:.0f}" xmlns="http://www.w3.org/2000/svg" {attrs}>'
            + cascara(P, interrogantes=interrogantes, cotas=cotas, rotulos_cota=rotulos_cota, grilla=grilla)
            + extra_bajo + muebles(P, piezas, nuevas, apagadas) + extra + "</svg>")


def abrir(P: Proj, vb=None, cls="sala", attrs="") -> str:
    x, y, w, h = vb or viewbox(P)
    return f'<svg class="{cls}" viewBox="{x:.0f} {y:.0f} {w:.0f} {h:.0f}" xmlns="http://www.w3.org/2000/svg" {attrs}>'


class Encuadre:
    """Convierte un punto 3D del cuarto en píxeles de la lámina, para poner HTML encima del dibujo
    (el svg ocupa `ancho` px de ancho, con su esquina en left, top)."""

    def __init__(self, P: Proj, left: float, top: float, ancho: float, vb=None):
        self.P, self.left, self.top = P, left, top
        self.vb = vb or viewbox(P)
        self.k = ancho / self.vb[2]
        self.alto = self.vb[3] * self.k

    def __call__(self, x, y, z):
        sx, sy = self.P.p(x, y, z)
        return self.left + (sx - self.vb[0]) * self.k, self.top + (sy - self.vb[1]) * self.k

    def svg_px(self, sx, sy):
        return self.left + (sx - self.vb[0]) * self.k, self.top + (sy - self.vb[1]) * self.k


def mini(cap_piezas, nuevas=()) -> str:
    """La habitación en miniatura, para el cajetín del pie."""
    P = Proj()
    x, y, w, h = viewbox(P, pad=(10, 10, 10, 10))
    return (f'<svg class="sala mini" viewBox="{x:.0f} {y + 40:.0f} {w:.0f} {h - 80:.0f}" xmlns="http://www.w3.org/2000/svg">'
            + cascara(P, cotas=False, grilla=False) + muebles(P, cap_piezas, nuevas) + "</svg>")
