"""Los gráficos de presentacion_simple.html, con matplotlib: barras con su IC 95% (bootstrap de
ambientes, como todo el trabajo), diferencias pareadas con su intervalo y, de punta a punta, los
productos útiles de cada lado con el marcador del juez. Cada figura sale como PNG embebido; se
muestra a 100 px por pulgada, así el tamaño de letra es el mismo en todas las láminas."""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datos import TRAB, f2, f3, p_signos
from matplotlib import font_manager as fm
from matplotlib.ticker import FuncFormatter

from amoblai.evaluation.metrics import bootstrap_ci

for _p in sorted((TRAB / "fuentes" / "ttf").glob("*.ttf")):  # Ubuntu Sans, la letra del deck, en estático
    fm.fontManager.addfont(str(_p))

AZUL, GRIS, GRIS_O = "#2A4BDB", "#A7B0C2", "#4A5060"
TINTA, TINTA2, TINTA3, HILO = "#16181D", "#4A5060", "#858B98", "#DCDFE5"
N_BOOT = 2000

plt.rcParams.update({
    "font.family": "Ubuntu Sans Graficos", "font.size": 16, "axes.titlesize": 18, "axes.titleweight": "medium",
    "axes.titlelocation": "left", "axes.titlepad": 40, "axes.labelsize": 15, "xtick.labelsize": 15, "ytick.labelsize": 14,
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": TINTA2, "axes.linewidth": 1.0,
    "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2, "text.color": TINTA,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": HILO, "grid.linewidth": 1.0, "axes.axisbelow": True,
    "legend.frameon": False, "legend.fontsize": 15, "figure.dpi": 100, "savefig.dpi": 150, "axes.unicode_minus": True,
})
ERR = dict(fmt="none", ecolor=TINTA, elinewidth=1.6, capsize=7, capthick=1.6, zorder=3)


def coma(nd: int) -> FuncFormatter:
    return FuncFormatter(lambda v, _: f"{v:.{nd}f}".replace(".", ",").replace("-", "−"))


def figura(w: float, h: float = 7.6, **kw):
    """Una figura de w × h pulgadas (se muestra a 100 px por pulgada)."""
    return plt.subplots(figsize=(w, h), layout="constrained", **kw)


def png(fig) -> tuple[str, int, int]:
    """La figura en PNG (base64) y su tamaño en px de la lámina."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    w, h = fig.get_size_inches()
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode(), round(w * 100), round(h * 100)


def titulo(ax, t1: str, t2: str = "") -> None:
    """El título del panel, y abajo, en gris, el dato que lo resume."""
    ax.set_title(t1, pad=40 if t2 else 14)
    if t2:
        ax.text(0, 1.02, t2, transform=ax.transAxes, color=TINTA2, fontsize=15, va="bottom", ha="left")


def ci(xs: list[float], grupos: list[str]) -> tuple[float, float]:
    return bootstrap_ci(xs, grupos, n_samples=N_BOOT)


def barras_v(ax, etiquetas, vals, ics, azul=(), fmt=f3, ylim=(0, 1), nd=2, ancho=0.62, ylabel="", hatch=()):
    """Barras verticales con su IC (ics[i] = (lo, hi) o None) y el valor arriba."""
    span = ylim[1] - ylim[0]
    for i, (v, ic) in enumerate(zip(vals, ics, strict=True)):
        az = i in azul
        ax.bar(i, v, width=ancho, color="white" if i in hatch else (AZUL if az else GRIS), zorder=2,
               edgecolor=GRIS_O if i in hatch else "none", hatch="//" if i in hatch else None, linewidth=1.2)
        top = v
        if ic:
            ax.errorbar(i, v, yerr=[[v - ic[0]], [ic[1] - v]], **ERR)
            top = ic[1]
        ax.text(i, top + 0.018 * span, fmt(v), ha="center", va="bottom", fontsize=15,
                color=AZUL if az else TINTA, fontweight="bold" if az else "normal")
    ax.set_xticks(range(len(vals)), etiquetas)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.set_xlim(-0.6, len(vals) - 0.4)
    ax.set_ylim(*ylim)
    ax.yaxis.set_major_formatter(coma(nd))
    if ylabel:
        ax.set_ylabel(ylabel)


def barras_h(ax, etiquetas, vals, ics, azul=(), fmt=f3, xlim=(0, 1), nd=2, notas=None, xlabel=""):
    """Barras horizontales (la primera arriba) con su IC y el valor a la derecha."""
    span = xlim[1] - xlim[0]
    for i, (v, ic) in enumerate(zip(vals, ics, strict=True)):
        az = i in azul
        ax.barh(i, v, height=0.62, color=AZUL if az else GRIS, zorder=2)
        tip = v
        if ic:
            ax.errorbar(v, i, xerr=[[v - ic[0]], [ic[1] - v]], **{**ERR, "capsize": 5})
            tip = ic[1]
        ax.text(tip + 0.012 * span, i, fmt(v), va="center", ha="left", fontsize=15,
                color=AZUL if az else TINTA, fontweight="bold" if az else "normal")
        if notas and notas[i]:
            ax.text(1.0, i, notas[i], transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=14, color=TINTA2)
    ax.set_yticks(range(len(vals)), etiquetas)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=8)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_formatter(coma(nd))
    if xlabel:
        ax.set_xlabel(xlabel)


def forest(ax, etiquetas, difs, ics, azul=(), xlim=None, nd=3, xlabel="diferencia pareada, con su IC 95%"):
    """Diferencias pareadas: el punto y su intervalo, con el cero marcado."""
    for i, (d, (lo, hi)) in enumerate(zip(difs, ics, strict=True)):
        c = AZUL if i in azul else (TINTA if lo > 0 or hi < 0 else TINTA3)
        ax.plot([lo, hi], [i, i], color=c, lw=2.2, zorder=3)
        ax.plot([lo, lo], [i - 0.14, i + 0.14], color=c, lw=2.2, zorder=3)
        ax.plot([hi, hi], [i - 0.14, i + 0.14], color=c, lw=2.2, zorder=3)
        ax.plot(d, i, "o", ms=10, color=c, zorder=4)
        ax.text(hi, i - 0.22, "  " + (("−" if d < 0 else "+") + f"{abs(d):.{nd}f}".replace(".", ",")),
                va="bottom", ha="left", fontsize=14, color=c, fontweight="bold" if i in azul else "normal")
    ax.axvline(0, color=TINTA2, lw=1.2, zorder=2)
    ax.set_yticks(range(len(difs)), etiquetas)
    ax.invert_yaxis()
    ax.tick_params(axis="y", length=0, pad=8)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    if xlim:
        ax.set_xlim(*xlim)
    ax.xaxis.set_major_formatter(coma(2))
    ax.set_xlabel(xlabel)


# =============================================================================================
# De punta a punta: los productos útiles de cada lado (los que el juez califica 2, en los dos
# órdenes) con su IC por bootstrap de ambientes, y el marcador
# =============================================================================================
def util_ci(j: dict, lado: str) -> tuple[float, tuple[float, float]]:
    xs, gs = [], []
    for r in j["rows"]:
        for p in r["puntajes"][lado]:
            xs += [float(g == 2) for g in p["grades"]]
            gs += [r["slug"]] * len(p["grades"])
    return sum(xs) / len(xs), ci(xs, gs)


def _emp(n: int) -> str:
    return f"{n} empate{'s' if n != 1 else ''}"


def panel_juez(ax, j: dict, lados: list[tuple[str, str, bool]], t1: str = "", corto: bool = False):
    """lados: (clave del lado en el juez, etiqueta, azul) en el orden en que se muestran."""
    vals, ics, gana = [], [], []
    for k, _, _ in lados:
        v, ic = util_ci(j, k)
        vals.append(v)
        ics.append(ic)
        gana.append(j["a"] if k == j["lado_a"] else j["b"])
    p = p_signos(j["a"], j["b"])
    barras_v(ax, [e for _, e, _ in lados], vals, ics, azul=[i for i, x in enumerate(lados) if x[2]], fmt=f2,
             ylabel="productos útiles (nota 2 del juez)", ancho=0.55)
    titulo(ax, t1 or f"{j['n']} ambientes vacíos · juez de listas",
           f"{'ganados' if corto else 'ambientes ganados'}: {gana[0]} a {gana[1]} · {_emp(j['emp'])} · "
           f"{'p < 0,01' if p < 0.005 else f'p = {f2(p)}'}")
