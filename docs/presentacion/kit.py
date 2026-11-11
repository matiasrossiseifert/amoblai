"""Piezas de la presentación: gráficos SVG desde los resultados, imágenes embebidas, el mapa de
las once fases (el recorrido, que se va encendiendo) con los pines de los experimentos, y los
extractos de los prompts (copiados del archivo real: si un extracto no está, falla)."""

from __future__ import annotations

import base64
import html
import io
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]

INK = "var(--ink)"
MUTED = "var(--muted)"
ACCENT = "var(--accent)"
BAR = "var(--bar)"
GRID = "var(--grid)"
GOOD = "var(--good)"


def esc(s: object) -> str:
    return html.escape(str(s))


def img(path: str | Path, max_side: int = 1400, quality: int = 80, cls: str = "", alt: str = "") -> str:
    p = Path(path)
    p = p if p.is_absolute() else ROOT / p
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=quality, optimize=True)
    data = base64.b64encode(buf.getvalue()).decode()
    return f'<img class="{cls}" alt="{esc(alt)}" src="data:image/jpeg;base64,{data}">'


def num(x: float, d: int = 2) -> str:
    """0,533 (coma decimal)."""
    return f"{x:.{d}f}".replace(".", ",")


def hbars(
    rows: list[dict],
    xmax: float = 1.0,
    width: int = 560,
    row_h: int = 34,
    label_w: int = 210,
    digits: int = 2,
    unit: str = "",
) -> str:
    """Barras horizontales: [{label, value, ci: (lo, hi)?, hl: bool, note?}]."""
    pad_r = 64
    plot_w = width - label_w - pad_r
    h = row_h * len(rows) + 10
    out = [f'<svg class="chart" viewBox="0 0 {width} {h}" width="{width}" height="{h}" role="img">']
    for t in (0.25, 0.5, 0.75, 1.0):
        if t * xmax <= xmax:
            x = label_w + plot_w * t
            out.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h - 6}" stroke="{GRID}" stroke-width="1"/>')
    for i, r in enumerate(rows):
        y = 6 + i * row_h
        v = r["value"]
        w = max(1.5, plot_w * v / xmax)
        color = ACCENT if r.get("hl") else BAR
        weight = 650 if r.get("hl") else 450
        out.append(
            f'<text x="{label_w - 10}" y="{y + row_h / 2 + 1}" text-anchor="end" '
            f'dominant-baseline="middle" font-size="14" font-weight="{weight}" fill="{INK}">{esc(r["label"])}</text>'
        )
        out.append(f'<rect x="{label_w}" y="{y + 5}" width="{w}" height="{row_h - 12}" rx="3" fill="{color}"/>')
        if r.get("ci"):
            lo, hi = r["ci"]
            x1, x2 = label_w + plot_w * lo / xmax, label_w + plot_w * hi / xmax
            ym = y + row_h / 2 - 1
            out.append(f'<line x1="{x1}" y1="{ym}" x2="{x2}" y2="{ym}" stroke="{INK}" stroke-width="1.4" opacity=".55"/>')
            for x in (x1, x2):
                out.append(f'<line x1="{x}" y1="{ym - 5}" x2="{x}" y2="{ym + 5}" stroke="{INK}" stroke-width="1.4" opacity=".55"/>')
        tx = label_w + max(w, plot_w * (r["ci"][1] / xmax) if r.get("ci") else w) + 8
        out.append(
            f'<text x="{tx}" y="{y + row_h / 2 + 1}" dominant-baseline="middle" font-size="14" '
            f'font-weight="{weight}" fill="{INK}">{num(v, digits)}{unit}</text>'
        )
    out.append("</svg>")
    return "".join(out)


def lines(
    series: list[dict],
    xs: list[float],
    ymin: float = 0.0,
    ymax: float = 1.0,
    width: int = 560,
    height: int = 300,
    xlabel: str = "",
    ylabel: str = "",
    xticks: list | None = None,
    xlog: bool = False,
    digits: int = 2,
    marks: list[dict] | None = None,
) -> str:
    """Curvas: [{name, ys, hl, dash?, labels: {x: texto}}]; `marks`: líneas verticales {x, text}."""
    import math

    L, R, T, B = 52, 18, 14, 44
    pw, ph = width - L - R, height - T - B

    def X(x: float) -> float:
        if xlog:
            a, b = math.log2(xs[0]), math.log2(xs[-1])
            return L + pw * (math.log2(x) - a) / (b - a)
        return L + pw * (x - xs[0]) / (xs[-1] - xs[0])

    def Y(y: float) -> float:
        return T + ph * (1 - (y - ymin) / (ymax - ymin))

    out = [f'<svg class="chart" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img">']
    steps = 4
    for i in range(steps + 1):
        yv = ymin + (ymax - ymin) * i / steps
        out.append(f'<line x1="{L}" y1="{Y(yv)}" x2="{width - R}" y2="{Y(yv)}" stroke="{GRID}"/>')
        out.append(f'<text x="{L - 8}" y="{Y(yv)}" text-anchor="end" dominant-baseline="middle" font-size="12" fill="{MUTED}">{num(yv, digits)}</text>')
    for x in xticks or xs:
        out.append(f'<text x="{X(x)}" y="{height - B + 18}" text-anchor="middle" font-size="12" fill="{MUTED}">{esc(x)}</text>')
    if xlabel:
        out.append(f'<text x="{L + pw / 2}" y="{height - 6}" text-anchor="middle" font-size="12.5" fill="{MUTED}">{esc(xlabel)}</text>')
    if ylabel:
        out.append(f'<text x="14" y="{T + ph / 2}" text-anchor="middle" font-size="12.5" fill="{MUTED}" transform="rotate(-90 14 {T + ph / 2})">{esc(ylabel)}</text>')
    for m in marks or []:
        out.append(f'<line x1="{X(m["x"])}" y1="{T}" x2="{X(m["x"])}" y2="{T + ph}" stroke="{ACCENT}" stroke-dasharray="4 4" opacity=".7"/>')
        out.append(f'<text x="{X(m["x"]) + 6}" y="{T + 12}" font-size="12" fill="{ACCENT}">{esc(m["text"])}</text>')
    for s in series:
        color = ACCENT if s.get("hl") else (s.get("color") or BAR)
        sw = 3 if s.get("hl") else 2.2
        pts = " ".join(f"{X(x)},{Y(y)}" for x, y in zip(xs, s["ys"], strict=True) if y is not None)
        dash = ' stroke-dasharray="6 5"' if s.get("dash") else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}"{dash} stroke-linejoin="round"/>')
        for x, y in zip(xs, s["ys"], strict=True):
            if y is None:
                continue
            out.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{3.6 if s.get("hl") else 3}" fill="{color}"/>')
            lab = (s.get("labels") or {}).get(x)
            if lab:
                out.append(f'<text x="{X(x)}" y="{Y(y) - 10}" text-anchor="middle" font-size="12.5" font-weight="600" fill="{color}">{esc(lab)}</text>')
        if s.get("name"):
            lx, ly = X(xs[-1]), Y(s["ys"][-1])
            out.append(f'<text x="{lx - 4}" y="{ly + (16 if s.get("below") else -10)}" text-anchor="end" font-size="12.5" font-weight="600" fill="{color}">{esc(s["name"])}</text>')
    out.append("</svg>")
    return "".join(out)




# El recorrido: las once fases -----------------------------------------------------------------
FASES = [
    ("catalogo", "Catálogo", "IKEA 819 + ABO 683"),
    ("descripcion", "Descripción", "un VLM escribe 8 líneas"),
    ("indice", "Índice", "Qwen3-Embedding + ChromaDB"),
    ("entrada", "Foto + pedido", "el ambiente vacío y el texto"),
    ("plan", "Plan", "Opus: piezas y una consulta por pieza"),
    ("busqueda", "Búsqueda", "filtro por kind + coseno: 5"),
    ("eleccion", "Elección", "Opus mira las fotos y elige"),
    ("escena", "Escena", "plantilla estricta, sin LLM"),
    ("imagen", "Imagen", "Nano Banana 2 edita la foto"),
    ("control", "Control", "SIFT: ¿el mismo cuarto?"),
    ("salida", "Lista + imagen", "la lista de compra y la foto"),
]
FKEYS = [k for k, *_ in FASES]
FNAME = {k: n for k, n, _ in FASES}
OFFLINE = 3  # las tres primeras fases se hacen una vez, offline

# Qué experimento decidió cada fase: los pines del mapa y del minimapa de cada experimento.
PINES: dict[str, list[int]] = {
    "catalogo": [9, 10],
    "descripcion": [1],
    "indice": [2, 4, 5, 6],
    "plan": [6],
    "busqueda": [3, 8, 11],
    "eleccion": [7],
    "escena": [12],
    "control": [12],
}


def pin(cx: float, tip: float, r: float = 10, n: int | None = None, stroke: str = "var(--paper)") -> str:
    """Un pin de mapa (una gota) con la punta en (cx, tip) y el número del experimento."""
    d = 1.75 * r
    cy = tip - d
    tx, ty = 0.8207 * r, 0.5714 * r  # donde las rectas desde la punta tocan el círculo
    out = (
        f'<path d="M{cx:.1f},{tip:.1f} L{cx - tx:.1f},{cy + ty:.1f} A{r},{r} 0 1 1 {cx + tx:.1f},{cy + ty:.1f} Z" '
        f'fill="{ACCENT}" stroke="{stroke}" stroke-width="1.5"/>'
    )
    if n is not None:
        out += (
            f'<text x="{cx:.1f}" y="{cy + 0.6:.1f}" text-anchor="middle" dominant-baseline="central" '
            f'font-size="{r * 1.12:.1f}" font-weight="700" fill="#fff">{n}</text>'
        )
    return out


def pin_inline(n: int, size: int = 24) -> str:
    """El mismo pin, suelto en el texto (qué experimento decidió esto)."""
    r = size * 0.36
    w = 2 * r + 4
    return (
        f'<svg class="pini" width="{w:.0f}" height="{size}" viewBox="0 0 {w:.1f} {size}" role="img" '
        f'aria-label="experimento {n}">{pin(w / 2, size - 1, r, n, stroke="none")}</svg>'
    )


def arrowhead(x: float, y: float, fx: float, fy: float, size: float = 7, color: str = MUTED) -> str:
    """Una punta de flecha en (x, y) que llega desde (fx, fy)."""
    import math

    a = math.atan2(y - fy, x - fx)
    c, s = math.cos(a), math.sin(a)
    p1 = (x - size * c + size * 0.5 * s, y - size * s - size * 0.5 * c)
    p2 = (x - size * c - size * 0.5 * s, y - size * s + size * 0.5 * c)
    return f'<path d="M{x:.1f},{y:.1f} L{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} Z" fill="{color}"/>'


def _route_x(width: float) -> list[float]:
    m = 52
    s = (width - 2 * m) / 10.5
    return [m + i * s if i < OFFLINE else m + (i + 0.5) * s for i in range(len(FASES))]


def route(cur: str | None = None, lit=(), pins: dict | None = None, width: int = 1160) -> str:
    """El mapa del recorrido en una tira. Con `cur` (las láminas del recorrido): la fase actual
    encendida y las anteriores marcadas como vistas. Sin `cur` (el minimapa de un experimento):
    las fases `lit` encendidas, cada una con el pin de `pins`."""
    mini = cur is None
    lit, pins = set(lit), pins or {}
    xs = _route_x(width)
    ci = FKEYS.index(cur) if cur else -1
    cy = 32 if mini else 44
    h = cy + (22 if mini else 33)
    out = [
        f'<svg class="route{" mini" if mini else ""}" viewBox="0 0 {width} {h}" width="{width}" height="{h}" role="img">'
    ]

    def state(i: int) -> str:
        if mini:
            return "on" if FKEYS[i] in lit else "off"
        return "cur" if i == ci else ("seen" if i < ci else "next")

    if not mini:
        out.append(f'<text x="{xs[0] - 14}" y="11" font-size="11" font-weight="600" letter-spacing=".08em" fill="{MUTED}">UNA VEZ · OFFLINE</text>')
        out.append(f'<text x="{xs[-1] + 44}" y="11" text-anchor="end" font-size="11" font-weight="600" letter-spacing=".08em" fill="{MUTED}">POR CADA PEDIDO</text>')
    for a in range(len(FASES) - 1):
        if a == OFFLINE - 1:
            continue  # entre el índice y la foto no hay vía: son dos pipelines
        on = not mini and state(a) in ("seen", "cur") and state(a + 1) in ("seen", "cur")
        out.append(
            f'<line x1="{xs[a]:.1f}" y1="{cy}" x2="{xs[a + 1]:.1f}" y2="{cy}" '
            f'stroke="{ACCENT if on else "var(--line)"}" stroke-width="{2.6 if on else 1.6}"/>'
        )
    if not mini:
        # el índice alimenta a la búsqueda; el control vuelve a la imagen
        x3, x6 = xs[2], xs[5]
        p = (x3 + 10, cy - 9, x3 + 70, cy - 42, x6 - 70, cy - 42, x6 - 9, cy - 11)
        out.append(f'<path d="M{p[0]:.1f},{p[1]} C{p[2]:.1f},{p[3]} {p[4]:.1f},{p[5]} {p[6]:.1f},{p[7]}" fill="none" stroke="{MUTED}" stroke-width="1.3" stroke-dasharray="4 4"/>')
        out.append(arrowhead(p[6], p[7], p[4], p[5], 6.5))
        out.append(f'<text x="{(x3 + x6) / 2:.1f}" y="{cy - 36}" text-anchor="middle" font-size="10.5" fill="{MUTED}">consulta el índice</text>')
        x9, x10 = xs[8], xs[9]
        q = (x10 - 9, cy - 10, x10 - 28, cy - 34, x9 + 28, cy - 34, x9 + 9, cy - 11)
        out.append(f'<path d="M{q[0]:.1f},{q[1]} C{q[2]:.1f},{q[3]} {q[4]:.1f},{q[5]} {q[6]:.1f},{q[7]}" fill="none" stroke="{MUTED}" stroke-width="1.3"/>')
        out.append(arrowhead(q[6], q[7], q[4], q[5], 6.5))
        out.append(f'<text x="{(x9 + x10) / 2:.1f}" y="{cy - 32}" text-anchor="middle" font-size="10.5" fill="{MUTED}">reintenta</text>')
    for i, (k, name, _) in enumerate(FASES):
        x, st = xs[i], state(i)
        if mini:
            on = st == "on"
            out.append(f'<circle cx="{x:.1f}" cy="{cy}" r="{6 if on else 4.5}" fill="{ACCENT if on else "var(--paper)"}" stroke="{ACCENT if on else "var(--line)"}" stroke-width="1.5"/>')
            out.append(f'<text x="{x:.1f}" y="{cy + 19}" text-anchor="middle" font-size="11.5" font-weight="{650 if on else 450}" fill="{ACCENT if on else MUTED}">{esc(name)}</text>')
            if on:
                ns = pins.get(k, [])
                for j, n in enumerate(ns):
                    out.append(pin(x + (j - (len(ns) - 1) / 2) * 19, cy - 8, 8, n))
            continue
        if st == "cur":
            out.append(f'<circle cx="{x:.1f}" cy="{cy}" r="19" fill="var(--accent-soft)"/>')
            out.append(f'<circle cx="{x:.1f}" cy="{cy}" r="13.5" fill="{ACCENT}"/>')
            out.append(f'<text x="{x:.1f}" y="{cy + 0.5}" text-anchor="middle" dominant-baseline="central" font-size="13" font-weight="700" fill="#fff">{i + 1}</text>')
            out.append(f'<text x="{x:.1f}" y="{cy + 31}" text-anchor="middle" font-size="13.5" font-weight="700" fill="{ACCENT}">{esc(name)}</text>')
        else:
            seen = st == "seen"
            out.append(f'<circle cx="{x:.1f}" cy="{cy}" r="10.5" fill="{"var(--accent-soft)" if seen else "var(--paper)"}" stroke="{ACCENT if seen else "var(--line)"}" stroke-width="1.4"/>')
            out.append(f'<text x="{x:.1f}" y="{cy + 0.5}" text-anchor="middle" dominant-baseline="central" font-size="11" font-weight="{650 if seen else 500}" fill="{ACCENT if seen else MUTED}">{i + 1}</text>')
            out.append(f'<text x="{x:.1f}" y="{cy + 30}" text-anchor="middle" font-size="12.5" font-weight="{550 if seen else 450}" fill="{INK if seen else MUTED}">{esc(name)}</text>')
    out.append("</svg>")
    return "".join(out)


def _wrap(text: str, n: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > n:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


def pipeline(pins: bool = False, width: int = 1160) -> str:
    """Las once fases como cajas: arriba lo que se hace una vez (offline), abajo lo de cada
    pedido; el índice baja a la búsqueda. Con `pins`, sobre cada caja los experimentos que la
    decidieron (PINES)."""
    bw, step, bh = 131, 147, 80
    y1, y2 = 34, 170
    H = 300
    pos = {}
    for i, (k, *_r) in enumerate(FASES):
        pos[k] = (i * step, y1) if i < OFFLINE else ((i - OFFLINE) * step, y2)
    out = [f'<svg class="pipe" viewBox="0 0 1160 {H}" width="{width}" role="img">']
    out.append(f'<text x="{3 * step + 4}" y="{y1 + 30}" font-size="11.5" font-weight="600" letter-spacing=".08em" fill="{MUTED}">UNA VEZ · OFFLINE</text>')
    out.append(f'<text x="{3 * step + 4}" y="{y1 + 50}" font-size="13" fill="{MUTED}">se arma una vez y queda en caché</text>')
    out.append(f'<text x="0" y="{y2 - 14}" font-size="11.5" font-weight="600" letter-spacing=".08em" fill="{MUTED}">POR CADA PEDIDO</text>')

    def arrow(x1, y1_, x2, y2_, dash=False):
        d = ' stroke-dasharray="5 4"' if dash else ""
        return (f'<line x1="{x1}" y1="{y1_}" x2="{x2}" y2="{y2_}" stroke="{MUTED}" stroke-width="1.5"{d}/>'
                + arrowhead(x2, y2_, x1, y1_))

    for i in range(len(FASES) - 1):
        if i == OFFLINE - 1:
            continue
        (xa, ya), (xb, yb) = pos[FKEYS[i]], pos[FKEYS[i + 1]]
        out.append(arrow(xa + bw + 3, ya + bh / 2, xb - 3, yb + bh / 2))
    xi, yi = pos["indice"]
    out.append(arrow(xi + 36, yi + bh + 3, xi + 36, y2 - 4, dash=True))
    out.append(f'<text x="{xi + 44}" y="{(yi + bh + y2) / 2 + 4}" font-size="11.5" fill="{MUTED}">el índice</text>')
    # el control vuelve a la imagen (hasta 3 intentos); la lista sale de la elección
    (xg, _), (xc, _) = pos["imagen"], pos["control"]
    yb = y2 + bh
    a0, a1 = xc + bw / 2, xg + bw / 2
    out.append(f'<path d="M{a0},{yb + 3} C{a0},{yb + 30} {a1},{yb + 30} {a1},{yb + 6}" fill="none" stroke="{MUTED}" stroke-width="1.4"/>')
    out.append(arrowhead(a1, yb + 4, a1, yb + 20))
    out.append(f'<text x="{(a0 + a1) / 2}" y="{yb + 40}" text-anchor="middle" font-size="11.5" fill="{MUTED}">reintenta, hasta 3</text>')
    (xe, _), (xs_, _) = pos["eleccion"], pos["salida"]
    l0, l1, ly = xe + bw / 2, xs_ + bw / 2, H - 6
    out.append(f'<path d="M{l0},{yb + 3} L{l0},{ly} L{l1},{ly} L{l1},{yb + 6}" fill="none" stroke="{MUTED}" stroke-width="1.4" stroke-dasharray="5 4"/>')
    out.append(arrowhead(l1, yb + 4, l1, yb + 20))
    out.append(f'<text x="{l0 + 8}" y="{ly - 6}" font-size="11.5" fill="{MUTED}">la lista</text>')
    for i, (k, name, sub) in enumerate(FASES):
        x, y = pos[k]
        ns = PINES.get(k, []) if pins else []
        out.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="11" fill="var(--card)" stroke="{ACCENT if ns else "var(--line)"}" stroke-width="{1.6 if ns else 1.2}"/>')
        out.append(f'<text x="{x + 10}" y="{y + 17}" font-size="10.5" font-weight="650" letter-spacing=".06em" fill="{ACCENT if ns else MUTED}">FASE {i + 1}</text>')
        out.append(f'<text x="{x + 10}" y="{y + 36}" font-size="14" font-weight="650" fill="{INK}">{esc(name)}</text>')
        for j, ln in enumerate(_wrap(sub, 19)[:2]):
            out.append(f'<text x="{x + 10}" y="{y + 54 + j * 14}" font-size="11" fill="{MUTED}">{esc(ln)}</text>')
        for j, n in enumerate(reversed(ns)):
            out.append(pin(x + bw - 14 - j * 23, y + 7, 10, n))
    out.append("</svg>")
    return "".join(out)


# Los prompts: extractos copiados del archivo ----------------------------------------------------
PROMPTS = ROOT / "src" / "amoblai" / "prompts"


def prompt_body(name: str) -> str:
    """El texto que se manda (sin el front matter)."""
    t = (PROMPTS / name).read_text()
    return t.split("---", 2)[2] if t.startswith("---") else t


def excerpt_html(source: str, parts: list[str]) -> str:
    """Los pedazos de `source` tal cual (si alguno no está, falla), unidos con […]. [[…]]
    resalta y {variable} va en color."""
    import re

    out = []
    for part in parts:
        plain = part.replace("[[", "").replace("]]", "")
        assert plain in source, f"el extracto no está en el prompt: {plain[:70]!r}"
        h = esc(part).replace("[[", "<mark>").replace("]]", "</mark>")
        out.append(re.sub(r"\{(\w+)\}", r'<span class="v">{\1}</span>', h))
    return '\n<span class="cut">[…]</span>\n'.join(out)


def prompt_card(name: str, parts: list[str], note: str = "extracto · se manda en inglés", source: str | None = None, cls: str = "") -> str:
    src = source if source is not None else prompt_body(name)
    return (
        f'<div class="prompt {cls}"><div class="ph"><b>{esc(name)}</b><span>{esc(note)}</span></div>'
        f"<pre>{excerpt_html(src, parts)}</pre></div>"
    )


def versions(rows: list[tuple[str, str, bool]], title: str = "Cómo lo fuimos reescribiendo") -> str:
    """Las versiones de un prompt: (versión, qué cambió y por qué, si es la que se usa)."""
    items = "".join(
        f'<div class="vr{" now" if now else ""}"><span class="vt">{esc(tag)}</span><span>{txt}</span></div>'
        for tag, txt, now in rows
    )
    head = f'<div class="lab">{title}</div>' if title else ""
    return f'<div class="vers">{head}{items}</div>'
