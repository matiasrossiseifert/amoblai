"""Piezas de la presentación: gráficos SVG desde los resultados, imágenes embebidas y el
diagrama de la arquitectura (que se resalta según qué toca cada experimento)."""

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


# La arquitectura ------------------------------------------------------------------------------
# Cajas del flujo (x, y, w, h, título, detalle) en un lienzo de 1180 x 300. `hl`: las que toca
# el experimento; `off`: las que esa versión no tiene.

ARCH = {
    # indexing pipeline (offline)
    "catalogo": (10, 18, 150, 64, "Catálogo", "productos + fotos"),
    "describe": (190, 18, 170, 64, "VLM describe", "8 líneas por producto"),
    "embed": (390, 18, 160, 64, "Embeddings", "Qwen3 0.6B"),
    "vdb": (580, 18, 160, 64, "ChromaDB", "HNSW · coseno"),
    # query pipeline
    "input": (10, 180, 150, 76, "Foto + pedido", "ambiente vacío"),
    "plan": (190, 180, 150, 76, "plan", "Claude: piezas, kinds, consulta ideal"),
    "retrieve": (370, 180, 150, 76, "retrieve", "filtros + top-k"),
    "rerank": (550, 180, 130, 76, "rerank", "VLM sobre top-10"),
    "choose": (710, 180, 150, 76, "choose", "Claude ve fotos: combinación y cantidades"),
    "scene": (890, 180, 120, 76, "scene", "prompt de la imagen"),
    "generate": (1040, 180, 130, 76, "generate", "Nano Banana 2 + control SIFT"),
}
EDGES = [
    ("catalogo", "describe"), ("describe", "embed"), ("embed", "vdb"),
    ("input", "plan"), ("plan", "retrieve"), ("retrieve", "rerank"), ("rerank", "choose"),
    ("choose", "scene"), ("scene", "generate"),
]


def arch(hl: set[str] | tuple = (), off: set[str] | tuple = (), notes: dict | None = None, width: int = 1180) -> str:
    hl, off, notes = set(hl), set(off), notes or {}
    out = [f'<svg class="arch" viewBox="0 0 1180 300" width="{width}" role="img">']
    out.append('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--muted)"/></marker></defs>')
    out.append(f'<text x="10" y="11" font-size="12" letter-spacing=".04em" fill="{MUTED}">INDEXING (OFFLINE)</text>')
    out.append(f'<text x="10" y="172" font-size="12" letter-spacing=".04em" fill="{MUTED}">CONSULTA (POR PEDIDO)</text>')

    def mid(k: str, side: str) -> tuple[float, float]:
        x, y, w, h, *_ = ARCH[k]
        return (x + w, y + h / 2) if side == "r" else (x, y + h / 2)

    edges = list(EDGES)
    if "rerank" in off:
        edges = [e for e in edges if "rerank" not in e] + [("retrieve", "choose")]
    for a, b in edges:
        (x1, y1), (x2, y2) = mid(a, "r"), mid(b, "l")
        out.append(f'<line x1="{x1 + 2}" y1="{y1}" x2="{x2 - 4}" y2="{y2}" stroke="var(--muted)" stroke-width="1.6" marker-end="url(#ah)"/>')
    # la base vectorial alimenta al retrieve
    vx, vy, vw, vh, *_ = ARCH["vdb"]
    rx, ry, rw, rh, *_ = ARCH["retrieve"]
    out.append(f'<path d="M{vx + vw / 2},{vy + vh} C{vx + vw / 2},{vy + vh + 50} {rx + rw / 2},{ry - 50} {rx + rw / 2},{ry - 4}" fill="none" stroke="var(--muted)" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ah)"/>')
    for k, (x, y, w, h, title, sub) in ARCH.items():
        if k in off:
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="none" stroke="var(--grid)" stroke-dasharray="5 4"/>')
            out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 4}" text-anchor="middle" font-size="13" fill="var(--grid)">{esc(title)}</text>')
            continue
        on = k in hl
        fill = "var(--accent)" if on else "var(--card)"
        tc = "#fff" if on else INK
        sc = "rgba(255,255,255,.85)" if on else MUTED
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{"var(--accent)" if on else "var(--line)"}" stroke-width="1.4"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + 26}" text-anchor="middle" font-size="15.5" font-weight="650" fill="{tc}">{esc(title)}</text>')
        sub = notes.get(k, sub)
        # el detalle en una o dos líneas
        words, line1, line2 = sub.split(), "", ""
        for wd in words:
            if len(line1) + len(wd) < (w / 7.4):
                line1 = f"{line1} {wd}".strip()
            else:
                line2 = f"{line2} {wd}".strip()
        out.append(f'<text x="{x + w / 2}" y="{y + 45}" text-anchor="middle" font-size="12" fill="{sc}">{esc(line1)}</text>')
        if line2:
            out.append(f'<text x="{x + w / 2}" y="{y + 60}" text-anchor="middle" font-size="12" fill="{sc}">{esc(line2)}</text>')
    out.append("</svg>")
    return "".join(out)


CHAIN = [
    ("catalogo", "catálogo"), ("describe", "VLM describe"), ("embed", "embeddings"), ("vdb", "ChromaDB"),
    None,
    ("plan", "plan"), ("retrieve", "retrieve"), ("rerank", "rerank"), ("choose", "choose"),
    ("scene", "scene"), ("generate", "generate"),
]


def chain(hl: set[str] | tuple = (), off: set[str] | tuple = ()) -> str:
    """La arquitectura en una tira: qué pasos toca el experimento."""
    hl, off = set(hl), set(off)
    parts = []
    for c in CHAIN:
        if c is None:
            parts.append('<span class="sep">│</span>')
            continue
        k, label = c
        cls = "on" if k in hl else ("off" if k in off else "")
        parts.append(f'<span class="st {cls}">{esc(label)}</span>')
    return '<div class="chain">' + '<span class="ar">›</span>'.join(parts).replace('<span class="ar">›</span><span class="sep">│</span><span class="ar">›</span>', '<span class="sep">│</span>') + "</div>"
