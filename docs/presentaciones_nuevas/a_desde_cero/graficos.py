"""Gráficos en SVG inline, con el lenguaje de un plano: líneas finas, cotas con remates, rótulos
en monoespaciada. Todos reciben números ya leídos de los archivos (datos_deck.py)."""

from __future__ import annotations

import math

COL = {
    "main": "#B0502A",  # terracota: lo elegido
    "main2": "#D9825E",
    "alt": "#7E858C",  # grafito: alternativas
    "alt2": "#B9BDC0",
    "good": "#56785D",  # salvia
    "ink": "#2B211B",
    "ink2": "#5D4F45",
    "ink3": "#8B7C70",
    "hair": "#D9CEBF",
    "hair2": "#C4B6A3",
    "paper": "#FBF8F2",
    "ocre": "#C68F2B",
}


def f(x: float, d: int = 3) -> str:
    """Decimal con coma: 0,535 (mismo redondeo que EXPERIMENTOS.md)."""
    if x is None:
        return "—"
    return f"{x:.{d}f}".replace(".", ",")


def pct(x: float, d: int = 0) -> str:
    return f(100 * x, d) + "%"


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def svg(w: int, h: int, body: str, cls: str = "chart", extra: str = "") -> str:
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'xmlns="http://www.w3.org/2000/svg" {extra}>{body}</svg>')


def cota(x1, x2, y, color=COL["ink2"], tick=9, sw=1.6, cls=""):
    """Una cota de plano: línea con remates a 45°."""
    t = tick / 2
    return (f'<g class="{cls}" stroke="{color}" stroke-width="{sw}" fill="none">'
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'
            f'<line x1="{x1 - t}" y1="{y + t}" x2="{x1 + t}" y2="{y - t}"/>'
            f'<line x1="{x2 - t}" y1="{y + t}" x2="{x2 + t}" y2="{y - t}"/></g>')


def hbars(rows, width=1000, label_w=380, row_h=66, bar_h=18, x_max=1.0, ticks=None,
          refs=None, val_d=3, top=46, right_pad=110, axis_label=None, step_attr=None, fmt=None,
          tick_fmt=None):
    """Barras horizontales con intervalo como cota.

    rows: dict(label, value, ci=(lo, hi)|None, kind='main'|'alt'|'muted'|'good', sub=str, step=int)
    refs: [(valor, rótulo)] líneas de referencia verticales (p. ej. el azar)."""
    ticks = ticks if ticks is not None else [0, 0.25, 0.5, 0.75, 1.0]
    plot_w = width - label_w - right_pad
    h = top + row_h * len(rows) + 18
    X = lambda v: label_w + plot_w * (v / x_max)
    out = []
    for t in ticks:
        x = X(t)
        out.append(f'<line x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{h - 8}" stroke="{COL["hair"]}" stroke-width="1"/>')
        tl = tick_fmt(t) if tick_fmt else (f(t, 2) if t not in (0, 1) else int(t))
        out.append(f'<text class="c-tick" x="{x:.1f}" y="{top - 20}" text-anchor="middle">{tl}</text>')
    if axis_label:
        out.append(f'<text class="c-tick" x="{label_w - 14}" y="{top - 20}" text-anchor="end">{esc(axis_label)}</text>')
    for v, lab in (refs or []):
        x = X(v)
        out.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{h - 8}" stroke="{COL["ink3"]}" stroke-width="1.4" stroke-dasharray="4 5"/>')
        out.append(f'<text class="c-note" x="{x + 8:.1f}" y="{h - 12}">{esc(lab)}</text>')
    for i, r in enumerate(rows):
        y0 = top + i * row_h
        cy = y0 + row_h / 2
        kind = r.get("kind", "alt")
        color = {"main": COL["main"], "alt": COL["alt"], "muted": COL["alt2"], "good": COL["good"],
                 "ink": COL["ink2"]}[kind]
        st = f' data-step="{r["step"]}"' if r.get("step") is not None else ""
        g = [f'<g{st}>']
        lab_cls = "c-lab b" if kind == "main" else "c-lab"
        if r.get("sub"):
            g.append(f'<text class="{lab_cls}" x="0" y="{cy - 4:.1f}">{esc(r["label"])}</text>')
            g.append(f'<text class="c-sub" x="0" y="{cy + 21:.1f}">{esc(r["sub"])}</text>')
        else:
            g.append(f'<text class="{lab_cls}" x="0" y="{cy + 8:.1f}">{esc(r["label"])}</text>')
        g.append(f'<line x1="{X(0):.1f}" y1="{cy:.1f}" x2="{X(x_max):.1f}" y2="{cy:.1f}" stroke="{COL["hair2"]}" stroke-width="1"/>')
        v = r["value"]
        g.append(f'<rect x="{X(0):.1f}" y="{cy - bar_h / 2:.1f}" width="{max(2, X(v) - X(0)):.1f}" height="{bar_h}" fill="{color}"/>')
        end = X(v)
        if r.get("ci"):
            lo, hi = r["ci"]
            g.append(cota(X(lo), X(hi), cy, color=COL["ink"], tick=14, sw=1.8))
            end = max(end, X(hi))
        vcls = "c-val m" if kind == "main" else "c-val"
        g.append(f'<text class="{vcls}" x="{end + 14:.1f}" y="{cy + 8:.1f}">{fmt(v) if fmt else f(v, val_d)}</text>')
        g.append("</g>")
        out.append("".join(g))
    return svg(width, h, "".join(out))


def heatmap(row_labels, col_labels, values, width=1000, label_w=330, cell_h=62, top=56,
            vmin=0.0, vmax=0.7, best=None, groups=None):
    """values[i][j] (None = no se corrió). best=(i, j) se marca con borde."""
    n_c = len(col_labels)
    cell_w = (width - label_w) / n_c
    h = top + cell_h * len(row_labels) + (18 * len(groups) if groups else 0) + 6
    out = []
    for j, c in enumerate(col_labels):
        out.append(f'<text class="c-sub b" x="{label_w + cell_w * (j + .5):.1f}" y="{top - 18}" text-anchor="middle">{esc(c)}</text>')
    lo = (0xF4, 0xEE, 0xE4)
    hi = (0xB0, 0x50, 0x2A)
    y = top
    for i, rl in enumerate(row_labels):
        if groups and i in groups:
            y += 18 if i else 0
        out.append(f'<text class="c-lab" x="0" y="{y + cell_h / 2 + 8:.1f}">{esc(rl)}</text>')
        for j in range(n_c):
            v = values[i][j]
            x = label_w + j * cell_w
            if v is None:
                out.append(f'<rect x="{x + 3:.1f}" y="{y + 3:.1f}" width="{cell_w - 6:.1f}" height="{cell_h - 6}" fill="none" stroke="{COL["hair"]}" stroke-dasharray="3 5"/>')
                out.append(f'<text class="c-tick" x="{x + cell_w / 2:.1f}" y="{y + cell_h / 2 + 6:.1f}" text-anchor="middle">no se corrió</text>')
                continue
            t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
            rgb = tuple(int(lo[k] + (hi[k] - lo[k]) * t) for k in range(3))
            fill = "#%02x%02x%02x" % rgb
            txt = "#FFFFFF" if t > 0.55 else COL["ink"]
            out.append(f'<rect x="{x + 3:.1f}" y="{y + 3:.1f}" width="{cell_w - 6:.1f}" height="{cell_h - 6}" fill="{fill}"/>')
            out.append(f'<text class="c-val" style="fill:{txt}" x="{x + cell_w / 2:.1f}" y="{y + cell_h / 2 + 8:.1f}" text-anchor="middle">{f(v)}</text>')
            if best == (i, j):
                out.append(f'<rect x="{x + 1:.1f}" y="{y + 1:.1f}" width="{cell_w - 2:.1f}" height="{cell_h - 2}" fill="none" stroke="{COL["ink"]}" stroke-width="3"/>')
        y += cell_h
    return svg(width, int(y + 8), "".join(out))


def line_chart(series, xs, width=980, height=520, ymin=0.0, ymax=1.0, yticks=None, xlabels=None,
               left=86, bottom=64, top=30, right=40, marks=None, bands=None, gap=None, xlab=None,
               ylab=None, labels_at_end=True):
    """series: [dict(name, ys, color, dash=False, ci=[(lo,hi)]|None, width=3)]
    marks: [(x, texto)] líneas verticales destacadas. gap: (i_serie_alta, i_serie_baja) sombrea."""
    yticks = yticks or [ymin + (ymax - ymin) * k / 4 for k in range(5)]
    pw, ph = width - left - right, height - top - bottom
    xi = {x: i for i, x in enumerate(xs)}
    X = lambda x: left + pw * xi[x] / (len(xs) - 1)
    Y = lambda y: top + ph * (1 - (y - ymin) / (ymax - ymin))
    out = []
    for t in yticks:
        out.append(f'<line x1="{left}" y1="{Y(t):.1f}" x2="{width - right}" y2="{Y(t):.1f}" stroke="{COL["hair"]}"/>')
        out.append(f'<text class="c-tick" x="{left - 14}" y="{Y(t) + 6:.1f}" text-anchor="end">{f(t, 2)}</text>')
    for i, x in enumerate(xs):
        lab = xlabels[i] if xlabels else str(x)
        out.append(f'<line x1="{X(x):.1f}" y1="{top + ph}" x2="{X(x):.1f}" y2="{top + ph + 8}" stroke="{COL["ink3"]}"/>')
        out.append(f'<text class="c-tick" x="{X(x):.1f}" y="{top + ph + 32}" text-anchor="middle">{esc(lab)}</text>')
    if xlab:
        out.append(f'<text class="c-sub" x="{left + pw / 2:.1f}" y="{height - 4}" text-anchor="middle">{esc(xlab)}</text>')
    if ylab:
        out.append(f'<text class="c-sub" x="{left}" y="{top - 10}" >{esc(ylab)}</text>')
    if gap:
        a, b = series[gap[0]]["ys"], series[gap[1]]["ys"]
        pts = [f"{X(x):.1f},{Y(a[i]):.1f}" for i, x in enumerate(xs)]
        pts += [f"{X(x):.1f},{Y(b[i]):.1f}" for i, x in reversed(list(enumerate(xs)))]
        out.append(f'<polygon points="{" ".join(pts)}" fill="{COL["main"]}" fill-opacity=".08"/>')
    for x, txt in (marks or []):
        out.append(f'<line x1="{X(x):.1f}" y1="{top}" x2="{X(x):.1f}" y2="{top + ph}" stroke="{COL["ink2"]}" stroke-width="1.4" stroke-dasharray="5 5"/>')
        out.append(f'<text class="c-note" x="{X(x) + 8:.1f}" y="{top + 18}">{esc(txt)}</text>')
    for s in series:
        if s.get("ci"):
            up = [f"{X(x):.1f},{Y(s['ci'][i][1]):.1f}" for i, x in enumerate(xs)]
            dn = [f"{X(x):.1f},{Y(s['ci'][i][0]):.1f}" for i, x in reversed(list(enumerate(xs)))]
            out.append(f'<polygon points="{" ".join(up + dn)}" fill="{s["color"]}" fill-opacity=".14"/>')
        pts = " ".join(f"{X(x):.1f},{Y(s['ys'][i]):.1f}" for i, x in enumerate(xs))
        dash = ' stroke-dasharray="8 7"' if s.get("dash") else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{s["color"]}" stroke-width="{s.get("width", 3.2)}"{dash}/>')
        for i, x in enumerate(xs):
            r = 6 if s.get("dots", True) else 0
            if r:
                out.append(f'<circle cx="{X(x):.1f}" cy="{Y(s["ys"][i]):.1f}" r="{r}" fill="{COL["paper"]}" stroke="{s["color"]}" stroke-width="2.6"/>')
        if labels_at_end and s.get("name"):
            yl = Y(s["ys"][-1]) + s.get("dy", 0)
            out.append(f'<text class="c-lab" style="fill:{s["color"]}" x="{X(xs[-1]) + 14:.1f}" y="{yl + 7:.1f}">{esc(s["name"])}</text>')
    for (x, y, txt, anchor, dy) in (bands or []):
        out.append(f'<text class="c-val" x="{X(x):.1f}" y="{Y(y) + dy:.1f}" text-anchor="{anchor}">{esc(txt)}</text>')
    return svg(width, height, "".join(out))


def dumbbell(rows, width=980, label_w=250, row_h=52, top=46, right=90, x_max=1.0):
    """rows: dict(label, a, b, n). a = antes (grafito), b = después (terracota)."""
    pw = width - label_w - right
    h = top + row_h * len(rows) + 10
    X = lambda v: label_w + pw * v / x_max
    out = []
    for t in (0, .25, .5, .75, 1):
        out.append(f'<line x1="{X(t):.1f}" y1="{top - 10}" x2="{X(t):.1f}" y2="{h - 6}" stroke="{COL["hair"]}"/>')
        out.append(f'<text class="c-tick" x="{X(t):.1f}" y="{top - 20}" text-anchor="middle">{f(t, 2) if t not in (0, 1) else int(t)}</text>')
    for i, r in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        out.append(f'<text class="c-lab" x="0" y="{cy + 8:.1f}">{esc(r["label"])}<tspan class="c-sub" dx="10">{r["n"]}</tspan></text>')
        a, b = r["a"], r["b"]
        out.append(f'<line x1="{X(min(a, b)):.1f}" y1="{cy:.1f}" x2="{X(max(a, b)):.1f}" y2="{cy:.1f}" stroke="{COL["main2"]}" stroke-width="5"/>')
        out.append(f'<circle cx="{X(a):.1f}" cy="{cy:.1f}" r="9" fill="{COL["paper"]}" stroke="{COL["alt"]}" stroke-width="3"/>')
        out.append(f'<circle cx="{X(b):.1f}" cy="{cy:.1f}" r="9" fill="{COL["main"]}"/>')
        out.append(f'<text class="c-val m" x="{X(max(a, b)) + 18:.1f}" y="{cy + 8:.1f}">{f(b, 2)}</text>')
    return svg(width, h, "".join(out))


def hist(values, lo, hi, point, width=900, height=420, bins=34, xmin=None, xmax=None, left=30,
         bottom=58, top=40):
    xmin = xmin if xmin is not None else min(values)
    xmax = xmax if xmax is not None else max(values)
    counts = [0] * bins
    for v in values:
        k = int((v - xmin) / (xmax - xmin) * bins)
        counts[min(bins - 1, max(0, k))] += 1
    pw, ph = width - 2 * left, height - top - bottom
    cmax = max(counts)
    X = lambda v: left + pw * (v - xmin) / (xmax - xmin)
    out = []
    bw = pw / bins
    for k, c in enumerate(counts):
        x0 = left + k * bw
        mid = xmin + (k + .5) * (xmax - xmin) / bins
        inside = lo <= mid <= hi
        hh = ph * c / cmax
        out.append(f'<rect x="{x0 + 1:.1f}" y="{top + ph - hh:.1f}" width="{bw - 2:.1f}" height="{hh:.1f}" fill="{COL["main"] if inside else COL["alt2"]}" fill-opacity="{0.85 if inside else 1}"/>')
    out.append(f'<line x1="{left}" y1="{top + ph}" x2="{width - left}" y2="{top + ph}" stroke="{COL["ink3"]}"/>')
    nt = 5
    for k in range(nt + 1):
        v = xmin + (xmax - xmin) * k / nt
        out.append(f'<line x1="{X(v):.1f}" y1="{top + ph}" x2="{X(v):.1f}" y2="{top + ph + 8}" stroke="{COL["ink3"]}"/>')
        out.append(f'<text class="c-tick" x="{X(v):.1f}" y="{top + ph + 32}" text-anchor="middle">{f(v, 2)}</text>')
    out.append(cota(X(lo), X(hi), top - 14, color=COL["ink"], tick=14, sw=1.8))
    out.append(f'<text class="c-val" x="{X(lo) - 10:.1f}" y="{top - 6}" text-anchor="end">{f(lo)}</text>')
    out.append(f'<text class="c-val" x="{X(hi) + 10:.1f}" y="{top - 6}">{f(hi)}</text>')
    out.append(f'<line x1="{X(point):.1f}" y1="{top}" x2="{X(point):.1f}" y2="{top + ph}" stroke="{COL["ink"]}" stroke-width="2.4"/>')
    return svg(width, height, "".join(out))


def dots_repro(rows, width=980, label_w=330, row_h=70, top=50, right=150, xmin=0.0, xmax=0.7,
               ticks=None, tick_d=1):
    pw = width - label_w - right
    h = top + row_h * len(rows) + 10
    X = lambda v: label_w + pw * (v - xmin) / (xmax - xmin)
    out = []
    for t in (ticks or [xmin + (xmax - xmin) * k / 7 for k in range(8)]):
        out.append(f'<line x1="{X(t):.1f}" y1="{top - 10}" x2="{X(t):.1f}" y2="{h - 6}" stroke="{COL["hair"]}"/>')
        out.append(f'<text class="c-tick" x="{X(t):.1f}" y="{top - 20}" text-anchor="middle">{f(t, tick_d)}</text>')
    for i, r in enumerate(rows):
        cy = top + i * row_h + row_h / 2
        main = i == 0
        out.append(f'<text class="c-lab{" b" if main else ""}" x="0" y="{cy + 8:.1f}">{esc(r["label"])}</text>')
        m, sd = r["mean"], r["sd"]
        out.append(cota(X(min(r["h"])), X(max(r["h"])), cy, color=COL["ink2"], tick=12, sw=1.5))
        for j, v in enumerate(r["h"]):
            out.append(f'<circle cx="{X(v):.1f}" cy="{cy:.1f}" r="9" fill="{COL["main"] if main else COL["alt"]}" fill-opacity=".9" stroke="{COL["paper"]}" stroke-width="2"/>')
        out.append(f'<text class="c-val{" m" if main else ""}" x="{X(max(r["h"])) + 20:.1f}" y="{cy + 8:.1f}">{f(m)} ± {f(sd)}</text>')
    return svg(width, h, "".join(out))


def stacked(parts, width=1500, height=150, total_label=None):
    """parts: [(rótulo, valor, color)] en una barra horizontal con rótulos debajo."""
    tot = sum(p[1] for p in parts)
    x = 0.0
    out = []
    bar_y, bar_h = 10, 54
    for i, (lab, v, col) in enumerate(parts):
        w = width * v / tot
        out.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(1, w - 3):.1f}" height="{bar_h}" fill="{col}"/>')
        if w > 120:
            out.append(f'<text class="c-val" style="fill:#fff" x="{x + 12:.1f}" y="{bar_y + 35}">US${f(v, 1)}</text>')
        x += w
    return svg(width, height, "".join(out))
