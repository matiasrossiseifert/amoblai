"""Gráficos en SVG. Cada gráfico tiene un esqueleto (ejes, nombres de las variantes) que aparece
con «qué hicimos» y los resultados (barras, curvas, valores) que aparecen recién en su paso: primero
el plano vacío, después los muebles."""

from __future__ import annotations

import math

from base import esc, f

C = {"main": "#2453D6", "alt": "#9AA4AF", "muted": "#C9CFD5", "ink": "#13202C", "good": "#3F8F5A",
     "cota": "#E2462F", "hilo": "#D5DADD", "t3": "#7E8A98"}


def _svg(w, h, body, cls="graf"):
    return f'<svg class="{cls}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">{body}</svg>'


def _d(n):
    return f' data-desde="{n}"' if n is not None else ""


def hbars(rows, width=1000, label_w=380, row_h=96, bar_h=30, x_max=1.0, ticks=None, refs=None,
          val_d=3, top=40, right=120, fmt=None, tick_fmt=None, esq=1, res=2, sub_dy=26):
    """rows: dict(label, value, ci=(lo, hi)|None, kind='main'|'alt'|'muted'|'ink'|'good', sub=str)."""
    ticks = ticks if ticks is not None else [0, .2, .4, .6, .8, 1.0]
    fmt = fmt or (lambda v: f(v, val_d))
    tick_fmt = tick_fmt or (lambda t: f(t, 1))
    x0, x1 = label_w, width - right
    X = lambda v: x0 + (x1 - x0) * v / x_max
    h = top + row_h * len(rows) + 10
    sk, rs = [], []
    for t in ticks:
        sk.append(f'<line class="eje" x1="{X(t):.1f}" y1="{top - 10}" x2="{X(t):.1f}" y2="{h - 6}" stroke-dasharray="{"" if t == 0 else "2 6"}"/>'
                  f'<text class="tick" x="{X(t):.1f}" y="{top - 18}" text-anchor="middle">{tick_fmt(t)}</text>')
    for i, r in enumerate(rows):
        yc = top + row_h * i + row_h / 2
        ly = yc + (0 if not r.get("sub") else -8)
        sk.append(f'<text class="lab" x="0" y="{ly + 8:.1f}">{esc(r["label"])}</text>')
        if r.get("sub"):
            sk.append(f'<text class="sub" x="0" y="{ly + 8 + sub_dy:.1f}">{esc(r["sub"])}</text>')
        sk.append(f'<rect class="riel" x="{x0}" y="{yc - bar_h / 2:.1f}" width="{x1 - x0}" height="{bar_h}"/>')
        v = r["value"]
        k = r.get("kind", "alt")
        rs.append(f'<rect class="bar {k}" x="{x0}" y="{yc - bar_h / 2:.1f}" width="{max(0, X(v) - x0):.1f}" height="{bar_h}"/>')
        end = X(v)
        if r.get("ci"):
            lo, hi = r["ci"]
            a, b = X(lo), X(hi)
            rs.append(f'<g class="ic"><rect x="{a:.1f}" y="{yc - bar_h / 2 - 9:.1f}" width="{b - a:.1f}" height="{bar_h + 18}"/>'
                      f'<line x1="{a:.1f}" y1="{yc:.1f}" x2="{b:.1f}" y2="{yc:.1f}"/>'
                      f'<line x1="{a:.1f}" y1="{yc - 11:.1f}" x2="{a:.1f}" y2="{yc + 11:.1f}"/>'
                      f'<line x1="{b:.1f}" y1="{yc - 11:.1f}" x2="{b:.1f}" y2="{yc + 11:.1f}"/></g>')
            end = max(end, b)
        rs.append(f'<text class="val{" main" if k == "main" else ""}" x="{end + 14:.1f}" y="{yc + 8:.1f}">{fmt(v)}</text>')
    for v, lab in refs or []:
        sk.append(f'<g class="ref"><line x1="{X(v):.1f}" y1="{top - 4}" x2="{X(v):.1f}" y2="{h - 6}"/>'
                  f'<text x="{X(v) + 6:.1f}" y="{h + 14}">{esc(lab)}</text></g>')
    body = f'<g{_d(esq)}>{"".join(sk)}</g><g class="res{"" if res is not None else " visible"}"{_d(res)}>{"".join(rs)}</g>'
    return _svg(width, h + 22, body)


def heatmap(row_labels, col_labels, values, width=1000, label_w=330, cell_h=66, top=60, vmin=0.0,
            vmax=1.0, best=None, gaps=(), esq=1, res=2, sub=None):
    n_c = len(col_labels)
    cw = (width - label_w) / n_c
    y = top
    ys = []
    for i in range(len(row_labels)):
        if i in gaps:
            y += 22
        ys.append(y)
        y += cell_h
    h = y + 6
    sk, rs = [], []
    for j, c in enumerate(col_labels):
        sk.append(f'<text class="tick" x="{label_w + cw * j + cw / 2:.1f}" y="{top - 16}" text-anchor="middle" style="font-size:18px">{esc(c)}</text>')
    for i, lab in enumerate(row_labels):
        yy = ys[i]
        sk.append(f'<text class="lab" x="0" y="{yy + cell_h / 2 + 9:.1f}">{esc(lab)}</text>')
        for j in range(n_c):
            sk.append(f'<rect x="{label_w + cw * j + 3:.1f}" y="{yy + 3:.1f}" width="{cw - 6:.1f}" height="{cell_h - 6}" fill="none" stroke="#D5DADD" stroke-dasharray="3 4"/>')
            v = values[i][j]
            tt = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
            # de papel a cobalto
            r = round(236 + (36 - 236) * tt)
            g = round(237 + (83 - 237) * tt)
            b = round(232 + (214 - 232) * tt)
            col = "#fff" if tt > 0.52 else "#13202C"
            hb = best == (i, j)
            rs.append(f'<rect x="{label_w + cw * j + 3:.1f}" y="{yy + 3:.1f}" width="{cw - 6:.1f}" height="{cell_h - 6}" fill="rgb({r},{g},{b})"'
                      + (' stroke="#FF9A3D" stroke-width="5"' if hb else "") + "/>"
                      f'<text x="{label_w + cw * j + cw / 2:.1f}" y="{yy + cell_h / 2 + 9:.1f}" text-anchor="middle" '
                      f'style="font:700 25px var(--mono);fill:{col}">{f(v)}</text>')
    body = f'<g{_d(esq)}>{"".join(sk)}</g><g class="res{"" if res is not None else " visible"}"{_d(res)}>{"".join(rs)}</g>'
    return _svg(width, h, body)


def line_chart(series, xs, width=1000, height=500, ymin=0.0, ymax=1.0, yticks=None, xlab="",
               left=70, right=130, top=30, bottom=74, marks=None, ylab=None, esq=1, res=2, fmt_y=None):
    """series: dict(name, ys, kind='main'|'alt', ci=[(lo,hi)…]|None, dash=bool, label=str)."""
    yticks = yticks or [ymin, (ymin + ymax) / 2, ymax]
    fmt_y = fmt_y or (lambda t: f(t, 1))
    x0, x1, y0, y1 = left, width - right, height - bottom, top
    n = len(xs)
    X = lambda i: x0 + (x1 - x0) * i / (n - 1)
    Y = lambda v: y0 - (y0 - y1) * (v - ymin) / (ymax - ymin)
    sk, rs = [], []
    for t in yticks:
        sk.append(f'<line class="eje" x1="{x0}" y1="{Y(t):.1f}" x2="{x1}" y2="{Y(t):.1f}" stroke-dasharray="2 6"/>'
                  f'<text class="tick" x="{x0 - 14}" y="{Y(t) + 5:.1f}" text-anchor="end">{fmt_y(t)}</text>')
    for i, xv in enumerate(xs):
        sk.append(f'<line class="eje" x1="{X(i):.1f}" y1="{y0}" x2="{X(i):.1f}" y2="{y0 + 8}"/>'
                  f'<text class="tick" x="{X(i):.1f}" y="{y0 + 32}" text-anchor="middle">{xv}</text>')
    sk.append(f'<line class="eje" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" style="stroke:#13202C"/>')
    if xlab:
        sk.append(f'<text class="sub" x="{(x0 + x1) / 2:.1f}" y="{height - 6}" text-anchor="middle" style="font-size:18px">{esc(xlab)}</text>')
    for xv, lab in marks or []:
        if xv in xs:
            i = xs.index(xv)
            sk.append(f'<line x1="{X(i):.1f}" y1="{y1 - 6}" x2="{X(i):.1f}" y2="{y0}" stroke="#13202C" stroke-width="1.2" stroke-dasharray="4 5"/>'
                      f'<text class="sub" x="{X(i):.1f}" y="{y1 - 12}" text-anchor="middle" style="fill:#13202C;font-size:17px">{esc(lab)}</text>')
    for s in series:
        col = C[s.get("kind", "main")]
        if s.get("ci"):
            up = " ".join(f"{X(i):.1f},{Y(hi):.1f}" for i, (lo, hi) in enumerate(s["ci"]))
            dn = " ".join(f"{X(i):.1f},{Y(lo):.1f}" for i, (lo, hi) in reversed(list(enumerate(s["ci"]))))
            rs.append(f'<polygon points="{up} {dn}" fill="{col}" opacity=".14"/>')
        d = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s["ys"]))
        dash = ' stroke-dasharray="9 8"' if s.get("dash") else ""
        rs.append(f'<path class="linea{"" if s.get("dash") else " trazo"}" d="{d}" stroke="{col}"{dash} pathLength="1"/>' if not s.get("dash")
                  else f'<path class="linea" d="{d}" stroke="{col}"{dash}/>')
        for i, v in enumerate(s["ys"]):
            rs.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{6 if not s.get("dash") else 4.5}" fill="{col if not s.get("dash") else "#fff"}" stroke="{col}" stroke-width="2.4"/>')
        if s.get("label"):
            rs.append(f'<text x="{X(n - 1) + 16:.1f}" y="{Y(s["ys"][-1]) + 7:.1f}" style="font:700 21px var(--mono);fill:{col}">{esc(s["label"])}</text>')
    body = f'<g{_d(esq)}>{"".join(sk)}</g><g class="res{"" if res is not None else " visible"}"{_d(res)}>{"".join(rs)}</g>'
    return _svg(width, height, body)


def dumbbell(rows, width=900, label_w=210, row_h=60, top=44, right=80, x_max=1.0, esq=None, res=None):
    """rows: dict(label, a, b, n). a → b."""
    x0, x1 = label_w, width - right
    X = lambda v: x0 + (x1 - x0) * v / x_max
    h = top + row_h * len(rows) + 8
    o = []
    for t in (0, .25, .5, .75, 1):
        o.append(f'<line class="eje" x1="{X(t):.1f}" y1="{top - 10}" x2="{X(t):.1f}" y2="{h}" stroke-dasharray="{"" if t == 0 else "2 6"}"/>'
                 f'<text class="tick" x="{X(t):.1f}" y="{top - 18}" text-anchor="middle">{f(t, 2)}</text>')
    for i, r in enumerate(rows):
        yc = top + row_h * i + row_h / 2
        o.append(f'<text class="lab" x="0" y="{yc + 8:.1f}">{esc(r["label"])}</text>'
                 f'<text class="sub" x="{label_w - 16}" y="{yc + 6:.1f}" text-anchor="end">{r["n"]}</text>')
        a, b = X(r["a"]), X(r["b"])
        o.append(f'<line x1="{a:.1f}" y1="{yc:.1f}" x2="{b:.1f}" y2="{yc:.1f}" stroke="#2453D6" stroke-width="5" opacity=".35"/>'
                 f'<circle cx="{a:.1f}" cy="{yc:.1f}" r="9" fill="#fff" stroke="#9AA4AF" stroke-width="3"/>'
                 f'<circle cx="{b:.1f}" cy="{yc:.1f}" r="10" fill="#2453D6"/>'
                 f'<text x="{b + 18:.1f}" y="{yc + 7:.1f}" style="font:700 19px var(--mono);fill:#2453D6">{f(r["b"], 2)}</text>')
    return _svg(width, h, "".join(o))


def hist(values, lo, hi, point, width=960, height=520, bins=34, left=20, bottom=70, top=30):
    vmin, vmax = min(values), max(values)
    pad = (vmax - vmin) * 0.06
    vmin, vmax = vmin - pad, vmax + pad
    edges = [vmin + (vmax - vmin) * i / bins for i in range(bins + 1)]
    counts = [0] * bins
    for v in values:
        k = min(bins - 1, int((v - vmin) / (vmax - vmin) * bins))
        counts[k] += 1
    cmax = max(counts)
    x0, x1, y0 = left, width - 20, height - bottom
    X = lambda v: x0 + (x1 - x0) * (v - vmin) / (vmax - vmin)
    bw = (x1 - x0) / bins
    o = []
    for i, c in enumerate(counts):
        mid = (edges[i] + edges[i + 1]) / 2
        inside = lo <= mid <= hi
        hh = (y0 - top) * c / cmax
        o.append(f'<rect x="{X(edges[i]) + 1.5:.1f}" y="{y0 - hh:.1f}" width="{bw - 3:.1f}" height="{hh:.1f}" fill="{"#2453D6" if inside else "#C9CFD5"}"/>')
    o.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#13202C" stroke-width="1.4"/>')
    # el intervalo, como una cota debajo del eje
    a, b = X(lo), X(hi)
    yy = y0 + 30
    o.append(f'<g stroke="#E2462F" stroke-width="1.6"><line x1="{a:.1f}" y1="{yy}" x2="{b:.1f}" y2="{yy}"/>'
             f'<line x1="{a - 6:.1f}" y1="{yy + 6}" x2="{a + 6:.1f}" y2="{yy - 6}"/><line x1="{b - 6:.1f}" y1="{yy + 6}" x2="{b + 6:.1f}" y2="{yy - 6}"/>'
             f'<line x1="{a:.1f}" y1="{y0 + 4}" x2="{a:.1f}" y2="{yy + 10}" stroke-width="1"/><line x1="{b:.1f}" y1="{y0 + 4}" x2="{b:.1f}" y2="{yy + 10}" stroke-width="1"/></g>'
             f'<text x="{a - 10:.1f}" y="{yy + 7}" text-anchor="end" style="font:700 20px var(--mono);fill:#E2462F">{f(lo)}</text>'
             f'<text x="{b + 10:.1f}" y="{yy + 7}" style="font:700 20px var(--mono);fill:#E2462F">{f(hi)}</text>'
             f'<text x="{(a + b) / 2:.1f}" y="{yy + 30}" text-anchor="middle" style="font:400 17px var(--mono);fill:#E2462F">95% de las muestras</text>')
    px = X(point)
    o.append(f'<line x1="{px:.1f}" y1="{top - 10}" x2="{px:.1f}" y2="{y0}" stroke="#13202C" stroke-width="2"/>'
             f'<text x="{px + 10:.1f}" y="{top + 6}" style="font:700 20px var(--mono);fill:#13202C">medido {f(point)}</text>')
    return _svg(width, height, "".join(o))


def dots_repro(rows, width=980, label_w=330, row_h=96, top=50, right=190, xmin=0.44, xmax=0.60, ticks=None,
               tick_d=2, esq=1, res=2):
    ticks = ticks or [xmin, xmax]
    x0, x1 = label_w, width - right
    X = lambda v: x0 + (x1 - x0) * (v - xmin) / (xmax - xmin)
    h = top + row_h * len(rows) + 8
    sk, rs = [], []
    for t in ticks:
        sk.append(f'<line class="eje" x1="{X(t):.1f}" y1="{top - 10}" x2="{X(t):.1f}" y2="{h}" stroke-dasharray="2 6"/>'
                  f'<text class="tick" x="{X(t):.1f}" y="{top - 18}" text-anchor="middle">{f(t, tick_d)}</text>')
    for i, r in enumerate(rows):
        yc = top + row_h * i + row_h / 2
        main = i == 0
        col = "#2453D6" if main else "#7E8A98"
        sk.append(f'<text class="lab" x="0" y="{yc + 8:.1f}">{esc(r["label"])}</text>'
                  f'<line x1="{x0}" y1="{yc:.1f}" x2="{x1}" y2="{yc:.1f}" stroke="#D5DADD"/>')
        a, b = X(r["mean"] - r["sd"]), X(r["mean"] + r["sd"])
        rs.append(f'<rect x="{a:.1f}" y="{yc - 16:.1f}" width="{b - a:.1f}" height="32" fill="{col}" opacity=".14"/>'
                  f'<line x1="{X(r["mean"]):.1f}" y1="{yc - 20:.1f}" x2="{X(r["mean"]):.1f}" y2="{yc + 20:.1f}" stroke="{col}" stroke-width="2.4"/>')
        for v in r["h"]:
            rs.append(f'<circle cx="{X(v):.1f}" cy="{yc:.1f}" r="9" fill="{col}" stroke="#fff" stroke-width="2"/>')
        rs.append(f'<text x="{x1 + 18}" y="{yc + 7:.1f}" style="font:700 21px var(--mono);fill:{col}">{f(r["mean"])} ± {f(r["sd"])}</text>')
    body = f'<g{_d(esq)}>{"".join(sk)}</g><g class="res{"" if res is not None else " visible"}"{_d(res)}>{"".join(rs)}</g>'
    return _svg(width, h, body)
