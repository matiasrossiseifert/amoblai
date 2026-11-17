"""presentacion_simple.html (SIMPLE=1 en build.py): una sola lámina por experimento, con el título y
los gráficos de matplotlib (graficos_simple.py), con sus barras de error. Lo demás es igual a la
presentación principal: laminas.py reemplaza las láminas de los experimentos por estas.

Cuando un experimento se repitió de punta a punta en los 11 ambientes vacíos, ese panel va a la
derecha, con los productos útiles de cada lado y el marcador del juez. Los números salen de los
mismos módulos que la principal (laminas_exp.py, laminas_extra.py, datos.py)."""

from __future__ import annotations

import json
import statistics

import datos as Dt
import laminas_exp as X
import laminas_extra as E
from datos import (
    CAM,
    CURVA,
    D21,
    DOC,
    EMB,
    GRAD,
    HIB,
    IMG_LLM,
    IMG_PL,
    J_AZAR,
    J_CTX,
    N_ANS,
    RLOC,
    TRAB,
    UTIL1,
    V1,
    V2,
    VT,
    F,
    K,
    dif,
    f2,
    f3,
    ic_txt,
    media_desvio,
    sg,
    usd,
)
from graficos_simple import (
    AZUL,
    ERR,
    GRIS,
    TINTA,
    TINTA2,
    TINTA3,
    barras_h,
    barras_v,
    ci,
    coma,
    figura,
    forest,
    panel_juez,
    png,
    titulo,
)
from piezas import kick
from registro import lam

CSS = """
.simple .sf{position:absolute;left:96px;right:96px;top:196px;bottom:108px;display:flex;align-items:center;justify-content:center}
.simple .sf img{display:block}
.simple .sf-pie{position:absolute;left:96px;right:96px;bottom:68px;margin:0;font:400 17px/1.3 var(--mono);color:var(--tinta-3)}
"""

IC = "barras de error: IC 95%, bootstrap de ambientes"
AZ = "en azul, lo que queda en el flujo"
IDS: list[str] = []


def lamina(n, tema: str, fig, notas: str, pie: str = f"{IC} · {AZ}", sid: str = "") -> None:
    b64, w, h = png(fig)
    sobre = X.SOBRE.get(n) if n not in (1, 2, None) else None
    etapa = X.ETAPA_TXT.get(n, "")
    cod, sid = (f"E{n}", f"s{n}") if n is not None else ("E", sid)
    lam(sid, f"Exp. {n}: {tema}" if n is not None else tema, f"Experimentos · {n}" if n is not None else "Experimentos", f'''
{kick(cod, f"experimento {n} · {etapa}" if n is not None else "experimentos")}
<h2 class="t chico">{tema}</h2>
<div class="sf"><img src="data:image/png;base64,{b64}" style="width:{w}px;height:{h}px" alt="{tema}"></div>
<p class="sf-pie">{f"sobre {sobre} · " if sobre else ""}{pie}</p>''', notas, 0, clase="clara simple")
    IDS.append(sid)


def _et(s: str) -> str:
    """Etiqueta en dos líneas, cortada en el medio."""
    w = s.split()
    if len(w) < 2:
        return s
    mejor = min(range(1, len(w)), key=lambda i: abs(len(" ".join(w[:i])) - len(" ".join(w[i:]))))
    return " ".join(w[:mejor]) + "\n" + " ".join(w[mejor:])


def _ics(rs, k="hit@1"):
    return [r[k + "_ic95"] for r in rs]


def _vs(rs, k="hit@1"):
    return [r[k] for r in rs]


# =============================================================================================
# 1 · Qué se indexa
# =============================================================================================
_n1, _n2, _d1, _j1 = X._n1, X._n2, X._d_idx, E._j1
fig, (a, b) = figura(17.2, ncols=2, gridspec_kw=dict(width_ratios=[1.3, 1]))
for k, met in enumerate(("hit@1", "hit@5")):
    for s, (r, lbl, az) in enumerate(((_n1, "Texto del vendedor", False), (_n2, "Descripción desde la foto", True))):
        x, v, (lo, hi) = k + (s - 0.5) * 0.36, r[met], r[met + "_ic95"]
        a.bar(x, v, width=0.34, color=AZUL if az else GRIS, label=lbl if k == 0 else None, zorder=2)
        a.errorbar(x, v, yerr=[[v - lo], [hi - v]], **ERR)
        a.text(x, hi + 0.015, f2(v), ha="center", va="bottom", fontsize=15, color=AZUL if az else TINTA,
               fontweight="bold" if az else "normal")
a.set_xticks([0, 1], ["hit@1", "hit@5"])
a.tick_params(axis="x", length=0, pad=8)
a.set_ylim(0, 0.8)
a.yaxis.set_major_formatter(coma(2))
a.legend(loc="upper left")
titulo(a, f"Set de IKEA · {N_ANS} consultas", f"hit@1, pareado: {sg(_d1['hit@1'], 2)} {ic_txt(*_d1['hit@1_ic95'], nd=2)}")
panel_juez(b, _j1, [("vendedor", "Texto del vendedor", False), ("hibrida", "Descripción", True)])
lamina(1, "Qué se indexa", fig,
       "El texto de IKEA es marketing, y la gente pide estilo, color y materiales, que están en la foto. Comparamos indexar el "
       "texto del vendedor contra la descripción de ocho líneas hecha mirando la foto, con todo lo demás fijo. En el set de "
       f"IKEA, hit@1 pasa de {f2(_n1['hit@1'])} a {f2(_n2['hit@1'])}, casi el triple, y hit@5 de {f2(_n1['hit@5'])} a "
       f"{f2(_n2['hit@5'])}; la diferencia pareada, {sg(_d1['hit@1'], 2)}, está lejos del cero. De punta a punta, en los once "
       f"ambientes, el juez elige la descripción {_j1['a']} a {_j1['b']}, con {_j1['emp']} empate, p igual a "
       f"{f2(E._p['vendedor'])}, y los productos útiles caen de {f2(_j1['util_a'])} a {f2(_j1['util_b'])} con el texto del "
       "vendedor. Decisión: se indexa la descripción. Es lo que más pesa de todo el trabajo.")

# =============================================================================================
# 2 · Cómo se escribe la consulta
# =============================================================================================
_qs = [X._q_full, X._q_piece, X._q_type, X._q_kind]
_j2 = E._j2
fig, (a, b) = figura(17.2, ncols=2, gridspec_kw=dict(width_ratios=[1.3, 1]))
barras_v(a, ["La ficha\n(8 líneas)", "La frase\nnatural", "Solo la\nlínea Type", "Solo\nel kind"], _vs(_qs), _ics(_qs), azul=[0],
         ylim=(0, 0.8), ylabel="hit@1")
titulo(a, f"Set de IKEA · {N_ANS} consultas", f"ficha − frase, pareado: {sg(X.D_CONSULTA, 2)} {ic_txt(-X._hi_q, -X._lo_q, nd=2)}")
panel_juez(b, _j2, [("hibrida", "La ficha", True), ("frase", "La frase natural", False)])
lamina(2, "Cómo se escribe la consulta", fig,
       "El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo, una ficha. Es la técnica de "
       "Advanced RAG del flujo, query expansion, y la medimos contra no reescribir: la frase con que el redactor nombró la pieza. "
       f"La ficha da {f3(X._q_full['hit@1'])} y la frase {f3(X._q_piece['hit@1'])}: {sg(X.D_CONSULTA, 2)}, lejos del cero; solo "
       f"la línea Type o solo el kind quedan muy abajo. De punta a punta, {_j2['a']} a {_j2['b']} para la ficha, con "
       f"{_j2['emp']} empate: no alcanza la significancia, p igual a {f2(E._p['frase'])}, pero va para el mismo lado. "
       "Texto y foto fallan distinto, y eso es un argumento para la híbrida. Decisión: el plan sigue escribiendo la ficha.")

# =============================================================================================
# 3 · Búsqueda léxica, por foto e híbrida
# =============================================================================================
_H3 = [(V1, "Densa: Qwen3"), (X.HK["lexica"], "Léxica: BM25"), (X.HK["foto"], "Por foto: SigLIP 2"),
       (X.HK["clip"], "Por foto: CLIP ViT-B/32"), (X.HK["densa+lexica"], "Densa + léxica"), (X.HK["densa+foto"], "Densa + foto"),
       (X.HK["lexica+foto"], "Léxica + foto"), (V2, "Densa + léxica + foto")]
_r3 = [HIB[k] for k, _ in _H3]
fig, (a, b) = figura(17.2, ncols=2, gridspec_kw=dict(width_ratios=[1.25, 1]))
barras_h(a, [e for _, e in _H3], _vs(_r3), _ics(_r3), azul=[7], xlim=(0, 0.8), xlabel="hit@1")
titulo(a, f"Set de IKEA · {N_ANS} consultas", "solos rinden parecido")
forest(b, [""] * 7, [r["vs_base"]["hit@1"] for r in _r3[1:]], [r["vs_base"]["hit@1_ic95"] for r in _r3[1:]], azul=[6],
       xlim=(-0.26, 0.15), xlabel="hit@1 menos la densa, pareado")
b.set_ylim(7.5, -1.5)
b.text(0, -1, "   la base", va="center", ha="left", fontsize=14, color=TINTA2)
b.plot(0, -1, "o", ms=10, color=TINTA2)
b.set_yticks([])
titulo(b, "Contra la densa", f"las tres juntas: {dif(D21)}")
lamina(3, "Búsqueda léxica, por foto e híbrida", fig,
       "¿Hace falta el embedder, o alcanza con contar palabras? ¿Y embeber la foto del producto, en vez de describirla? Tres "
       "buscadores con el filtro por kind: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, y sus "
       f"fusiones. Solos rinden parecido: {f3(HIB[V1]['hit@1'])}, {f3(HIB[X.HK['lexica']]['hit@1'])} y "
       f"{f3(HIB[X.HK['foto']]['hit@1'])}; CLIP, un modelo por foto más viejo, queda muy abajo. Pero se equivocan en cosas distintas: a la derecha, la diferencia pareada contra la "
       f"densa. Las tres juntas dan {f3(HIB[V2]['hit@1'])}, {sg(D21['hit@1'])}, con un intervalo que no toca el cero. "
       "Decisión: la búsqueda pasa a ser híbrida. Es la versión 2, el Ejercicio 4.")

# =============================================================================================
# El camino incremental
# =============================================================================================
fig, ax = figura(17.2)
_ap = [("Un VLM elige entre los 5 primeros", CURVA["por_k"]["5"]["acierto_eleccion"], CURVA["por_k"]["5"]["ic95"]),
       ("Un VLM reordena los 10 primeros", X._r_opus["hit@1"], X._r_opus["hit@1_ic95"])]
_xs, _ets = [], []
for i, (key, et, _) in enumerate(X.PASOS):
    r = CAM[key]
    v, (lo, hi) = r["hit@1"], r["hit@1_ic95"]
    az = key == V2
    ax.bar(i, v, width=0.62, color=AZUL if az else GRIS, zorder=2)
    ax.errorbar(i, v, yerr=[[v - lo], [hi - v]], **ERR)
    ax.text(i, hi + 0.012, f2(v), ha="center", va="bottom", fontsize=15, color=AZUL if az else TINTA,
            fontweight="bold" if az else "normal")
    if "vs_anterior" in r:
        d = r["vs_anterior"]
        sube = d["hit@1_ic95"][0] > 0
        ax.text(i, hi + 0.06, sg(d["hit@1"], 2), ha="center", va="bottom", fontsize=14,
                color=TINTA if sube else TINTA3, fontweight="bold" if sube else "normal")
    _xs.append(i)
    _ets.append("\n".join(X._lineas(et, 16)))
for j, (et, v, (lo, hi)) in enumerate(_ap):
    x = len(X.PASOS) + 0.5 + j
    ax.bar(x, v, width=0.62, color="white", edgecolor=TINTA2, hatch="//", linewidth=1.2, zorder=2)
    ax.errorbar(x, v, yerr=[[v - lo], [hi - v]], **ERR)
    ax.text(x, hi + 0.012, f3(v), ha="center", va="bottom", fontsize=15)
    _xs.append(x)
    _ets.append("\n".join(X._lineas(et, 16)))
ax.axvline(len(X.PASOS) - 0.05, color=TINTA3, lw=1.2, ls="--")
ax.text(len(X.PASOS) + 1, 0.86, "aparte: técnicas aisladas,\nno pasos del flujo", ha="center", va="top", fontsize=14, color=TINTA2)
ax.set_xticks(_xs, _ets)
ax.tick_params(axis="x", length=0, pad=8)
ax.set_ylim(0, 0.88)
ax.set_ylabel("hit@1")
ax.yaxis.set_major_formatter(coma(1))
titulo(ax, f"Set de IKEA · {N_ANS} consultas · un cambio por paso",
       "arriba, la diferencia pareada con el paso anterior: en negro, si su IC 95% no toca el cero")
_r_opus = X._r_opus
lamina(None, "El camino incremental", fig,
       f"La ablación incremental: un cambio por paso, con su intervalo, sobre las {N_ANS} consultas. Del RAG naive, "
       f"{f2(_n1['hit@1'])}, la descripción lo lleva a {f2(_n2['hit@1'])} y la consulta como ficha a "
       f"{f2(CAM[X.K_FICHA]['hit@1'])}: esos dos pasos son los que más pesan. El filtro por kind no suma acá; con él, es la "
       f"versión 1. La léxica y la foto llegan a {f2(CAM[V2]['hit@1'])}: la versión 2. A la derecha, rayados, un VLM eligiendo o "
       f"reordenando, {f3(_r_opus['hit@1'])}: técnicas aisladas, no escalones del flujo.", pie=f"{IC} · {AZ}: la versión 2",
       sid="s-camino")

# =============================================================================================
# 4 · ¿Error, o una variante?
# =============================================================================================
# El juez calificó 75 consultas con anotado y 75 sin anotado; se repondera a todas. El IC del
# promedio reponderado sale de los de cada estrato (aproximación normal, estratos independientes).
_w = Dt._w_ans
_se = [(GRAD["consultas"][s]["util1_ic95"][1] - GRAD["consultas"][s]["util1_ic95"][0]) / 3.92 for s in ("con anotado", "sin anotado")]
_se_u = ((_w * _se[0]) ** 2 + ((1 - _w) * _se[1]) ** 2) ** 0.5
_e_q = X._e_q
fig, ax = figura(9.4)
barras_v(ax, ["El producto\nexacto", "El mismo\nmodelo", "Sirve,\nsegún un juez"],
         [_e_q["hit@1"], _e_q["familia_hit@1"], UTIL1],
         [_e_q["hit@1_ic95"], _e_q["familia_hit@1_ic95"], (UTIL1 - 1.96 * _se_u, UTIL1 + 1.96 * _se_u)], fmt=f2,
         ylabel="el primer candidato es correcto", ancho=0.58)
titulo(ax, "Set de IKEA · el primer candidato", f"1 de cada {round(1 / X._frac_var)} «errores» es el mismo modelo en otro color")
lamina(4, "¿Error, o una variante?", fig,
       "hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. Tres niveles de correcto "
       f"para el primer candidato: el exacto, {f2(_e_q['hit@1'])}; el mismo modelo, {f2(_e_q['familia_hit@1'])}; y uno que sirve "
       f"según un juez, {f2(UTIL1)}. Una de cada {round(1 / X._frac_var)} veces que el primero falla es otra variante del mismo mueble. Al juez lo probamos con las anotaciones: al producto anotado le dice que sirve el "
       f"{round(100 * Dt.G_ANOT2)} por ciento de las veces; a los otros candidatos, el {round(100 * Dt.G_OTROS2)}. Conclusión: "
       "el exacto subestima el nivel, no el orden; sirve para comparar.", pie=IC)

# =============================================================================================
# 5 · Elegir con un VLM, y cuántos candidatos
# =============================================================================================
_r0, _do, _j5 = X._r0, X._d_opus, E._j5
fig, (a, b, c) = figura(17.2, ncols=3, gridspec_kw=dict(width_ratios=[0.78, 1.3, 0.9]))
barras_v(a, ["Solo la\nbúsqueda", "Un VLM\nreordena"], [_r0["hit@1"], _r_opus["hit@1"]], [_r0["hit@1_ic95"], _r_opus["hit@1_ic95"]],
         ylim=(0, 0.8), ylabel="hit@1", ancho=0.58)
titulo(a, "Reordenar el top-10", f"pareado: {dif(_do, nd=2)}")
_ic5 = [CURVA["por_k"][str(k)]["ic95"] for k in X._ks]
b.plot(X._ks, X._tech, ls="--", color=TINTA3, lw=2, marker="o", ms=6, label="techo: el correcto está entre los k (hit@k)")
b.errorbar(X._ks, X._ele, yerr=[[v - lo for v, (lo, _) in zip(X._ele, _ic5, strict=True)],
                                [hi - v for v, (_, hi) in zip(X._ele, _ic5, strict=True)]],
           color=TINTA2, lw=2, marker="o", ms=8, capsize=5, capthick=1.4, elinewidth=1.4, label="lo que elegiría el VLM")
_i5 = X._ks.index(K)
b.plot(K, X._ele[_i5], "o", ms=13, color=AZUL, zorder=5)
b.annotate(f"k = {K}: {f3(X._ele[_i5])}", (K, X._ele[_i5]), xytext=(16, -52), textcoords="offset points", ha="left",
           color=AZUL, fontsize=15, fontweight="bold")
b.set_xticks(X._ks)
b.set_xlabel("k: candidatos por pieza")
b.set_ylabel("acierto")
b.set_ylim(0.45, 0.95)
b.yaxis.set_major_formatter(coma(2))
b.legend(loc="upper left")
titulo(b, "Si eligiera entre los primeros k", f"de 3 a 5, pareado: {sg(X._d35['acierto_eleccion'])} {ic_txt(*X._d35['ic95'])}")
panel_juez(c, _j5, [("k3", "3 candidatos", False), ("hibrida", "5 candidatos", True)])
lamina(5, "Elegir con un VLM, y cuántos candidatos", fig,
       f"hit@10 es {f2(_r0['hit@10'])} pero hit@1 {f2(_r0['hit@1'])}: el correcto suele estar, pero no primero. Opus mirando las "
       f"fotos del top-10 lleva hit@1 de {f3(_r0['hit@1'])} a {f3(_r_opus['hit@1'])}. De ahí sale la curva del medio: si eligiera "
       f"entre los primeros k, ¿acertaría? La punteada es el techo. De 3 a 5 sube {round(100 * X._d35['acierto_eleccion'])} "
       f"puntos, con un intervalo que no toca el cero, y a partir de 8 se aplana. De punta a punta, cinco contra tres: "
       f"{_j5['a']} a {_j5['b']}, con {_j5['emp']} empates, p igual a {f2(E._p['k3'])}. Decisión: cinco candidatos por pieza. "
       "Ojo: el reranker es una técnica aislada; el que elige arma un conjunto para el cuarto y no tiene ground truth.")

# =============================================================================================
# 6 · Con búsqueda, al azar, o con el catálogo entero (y por qué RAG: tokens y costo)
# =============================================================================================
_opus = Dt._opus
_tk_rg = [Dt._entrada(c) for c in Dt._rg]
_tk_cx = [Dt._entrada(c) for c in Dt._cx]
_c_rg = [c["cost_usd"] for c in Dt._rg]
_c_sin = [(Dt._entrada(c) * _opus["input"] + Dt._uso(c)["output_tokens"] * _opus["output"]) / 1e6 for c in Dt._cx]
_c_con = [c["cost_usd"] for c in Dt._cx if not Dt._uso(c).get("cache_creation_input_tokens")]
assert abs(statistics.mean(_c_sin) - Dt.C_CTX_SIN) < 1e-9 and abs(statistics.mean(_c_con) - Dt.C_CTX_CACHE) < 1e-9


def _ci_simple(xs):
    return ci(xs, [str(i) for i in range(len(xs))])


fig, axs = figura(17.2, ncols=4, gridspec_kw=dict(width_ratios=[1, 1, 1.05, 1.15]))
panel_juez(axs[0], J_AZAR, [("densa", "Con\nbúsqueda", True), ("azar", f"{K} al azar\ndel kind", False)],
           t1=f"Contra el azar · {J_AZAR['n']} ambientes", corto=True)
panel_juez(axs[1], J_CTX, [("hibrida", "Con\nbúsqueda", True), ("contexto", "Catálogo\nentero", False)],
           t1=f"Contra el catálogo · {J_CTX['n']} amb.", corto=True)
ax = axs[2]
for i, (xs, az) in enumerate(((_tk_rg, True), (_tk_cx, False))):
    m = statistics.median(xs)
    ax.bar(i, m, width=0.55, color=AZUL if az else GRIS, zorder=2)
    ax.plot([i] * len(xs), xs, "o", ms=6, color=TINTA, alpha=0.55, zorder=3)
    ax.text(i, max(xs) + 25_000, f"{round(m / 1000)} mil", ha="center", va="bottom", fontsize=15,
            color=AZUL if az else TINTA, fontweight="bold" if az else "normal")
ax.axhline(DOC["contexto"], color=TINTA2, ls="--", lw=1.4)
ax.text(1.4, DOC["contexto"] - 25_000, "el contexto de Opus", ha="right", va="top", fontsize=14, color=TINTA2)
ax.set_xticks([0, 1], ["Con\nbúsqueda", "Catálogo\nentero"])
ax.tick_params(axis="x", length=0, pad=8)
ax.set_xlim(-0.6, 1.6)
ax.set_ylim(0, 1_080_000)
ax.yaxis.set_major_formatter(lambda v, _: "0" if v == 0 else ("1 millón" if v >= 1e6 else f"{round(v / 1000)} mil"))
ax.set_ylabel("tokens de entrada, el paso que elige")
titulo(ax, "Tokens por pedido", "la mediana y cada ambiente")
_cs = [_c_rg, _c_sin, _c_con]
barras_v(axs[3], ["Con\nbúsqueda", "Catálogo,\nsin caché", "Catálogo,\ncon caché"], [statistics.mean(x) for x in _cs],
         [_ci_simple(x) for x in _cs], azul=[0], fmt=lambda v: usd(v, 3 if v < 1 else 2), ylim=(0, 1.75), nd=1,
         ylabel="US$ por pedido, el paso que elige", ancho=0.58)
axs[3].yaxis.set_major_formatter(lambda v, _: "0" if v == 0 else usd(v, 1))
titulo(axs[3], "Costo por pedido", "promedio por ambiente")
lamina(6, "Con búsqueda, al azar, o con el catálogo entero", fig,
       "¿La búsqueda aporta en la tarea real? ¿Y hacía falta, si el catálogo entra en el contexto? Mismo plan, mismo modelo que "
       f"elige, mismo juez, en los dos órdenes. Contra cinco al azar del mismo kind, {J_AZAR['a']} a {J_AZAR['b']}: los "
       f"productos útiles pasan de {f2(J_AZAR['util_b'])} a {f2(J_AZAR['util_a'])}, y el juez distingue. Contra el catálogo "
       f"entero en el prompt, {J_CTX['a']} a {J_CTX['b']}: empatan. ¿Por qué RAG, entonces? Con búsqueda, el que elige recibe "
       f"unos {round(statistics.median(_tk_rg) / 1000)} mil tokens; con el catálogo, {round(statistics.median(_tk_cx) / 1000)} mil, "
       f"un tercio del contexto: con el triple de productos no entra. Y elegir cuesta {usd(Dt.C_CHOOSE_V2)} contra "
       f"{usd(Dt.C_CTX_SIN)} sin caché; la caché lo baja a {usd(Dt.C_CTX_CACHE)}, pero dura cinco minutos. Con poco tráfico o "
       "un catálogo más grande conviene RAG, y por eso lo elegimos.")

# =============================================================================================
# 7 · Tres redactores
# =============================================================================================
fig, (a, b) = figura(17.2, 6.2, ncols=2, gridspec_kw=dict(width_ratios=[1.2, 1]))
for j, (_et, xs, az) in enumerate((("Versión 1\n(densa)", X._v1s, False), ("Versión 2\n(híbrida)", X._v2s, True))):
    col = AZUL if az else TINTA2
    mu, sd = statistics.mean(xs), statistics.stdev(xs)
    a.errorbar(mu, j, xerr=sd, fmt="|", ms=26, mew=2.4, color=col, elinewidth=8, alpha=0.28, capsize=0, zorder=2)
    a.plot(xs, [j] * len(xs), "o", ms=14, color=col, zorder=3)
    a.text(mu, j - 0.3, media_desvio(xs), ha="center", va="bottom", fontsize=15, color=col, fontweight="bold" if az else "normal")
a.set_yticks([0, 1], ["Versión 1\n(densa)", "Versión 2\n(híbrida)"])
a.set_ylim(1.6, -0.75)
a.tick_params(axis="y", length=0, pad=8)
a.grid(axis="y", visible=False)
a.grid(axis="x", visible=True)
a.set_xlim(0.48, 0.65)
a.xaxis.set_major_formatter(coma(2))
a.set_xlabel("hit@1")
titulo(a, "Tres redactores de las consultas", "cada punto, un redactor · la banda, el promedio ± un desvío")
forest(b, ["Redactor 1", "Redactor 2", "Redactor 3"], [d["hit@1"] for d in X._difs_r], [d["hit@1_ic95"] for d in X._difs_r],
       azul=[0, 1, 2], xlim=(-0.02, 0.14), xlabel="diferencia de hit@1")
titulo(b, "La mejora de la híbrida, en cada uno", "versión 2 menos versión 1, pareado, con su IC 95%")
lamina(7, "Tres redactores", fig,
       "Las consultas de evaluación las escribió un modelo: ¿medimos al redactor o al sistema? Las mismas consultas, escritas "
       f"otras dos veces por subagentes independientes. La versión 1 da {media_desvio(X._v1s)}; la versión 2, "
       f"{media_desvio(X._v2s)}, y la mejora de la híbrida se repite en los tres, con intervalos que no tocan el cero. El número "
       "se mueve unos dos puntos y medio según quién escribe: dos puntos no son señal.",
       pie="puntos: cada redactor · a la derecha, " + IC)


# =============================================================================================
# 8 · Buscar por imagen
# =============================================================================================
def _img_txt():
    """Lo de datos.imagen_contra_texto, con los vectores por producto (para el IC de cada lado)."""
    v0 = {(r["room_id"], r["sku"]): r["best_rank"] for r in Dt.jsonl(Dt.V0_DIR / "items.jsonl")}
    v1: dict[tuple, int | None] = {}
    for r in Dt.rankings(Dt.TXT_DIR)[Dt.BASE]:
        for sku in r["relevant"]:
            pos = r["ranked"].index(sku) + 1 if sku in r["ranked"] else None
            k = (r["room_id"], sku)
            v1[k] = pos if v1.get(k) is None else (v1[k] if pos is None else min(v1[k], pos))
    keys = sorted(v0)
    return ([float(v0[k] is not None and v0[k] <= 1) for k in keys], [float(v1.get(k) is not None and v1[k] <= 1) for k in keys],
            [k[0] for k in keys])


_ia, _tb, _g8 = _img_txt()
assert abs(statistics.mean(_ia) - VT["imagen"]) < 1e-9 and abs(statistics.mean(_tb) - VT["texto"]) < 1e-9
fig, ax = figura(9.4)
barras_v(ax, ["Por imagen\n(el recorte, DINOv3)", "Por texto\n(la descripción)"], [VT["imagen"], VT["texto"]],
         [ci(_ia, _g8), ci(_tb, _g8)], azul=[1], fmt=f2, ylim=(0, 0.8), ylabel="hit@1", ancho=0.55)
titulo(ax, f"Los mismos {VT['n']} productos anotados", f"texto − imagen, pareado: {sg(VT['dif'], 2)} {ic_txt(*VT['ic'], nd=2)}")
lamina(8, "Buscar por imagen", fig,
       "Otra arquitectura: que un generador de imágenes amueble primero, recortar cada mueble y buscarlo en el catálogo por su "
       f"foto. Con el mismo ground truth, los {VT['n']} productos anotados: por imagen encuentra primero el "
       f"{round(100 * VT['imagen'])} por ciento; por texto, el {round(100 * VT['texto'])}. Y es el mejor caso para la imagen: los "
       "recortes salen de fotos reales. Nos quedamos con el texto. Ojo: el flujo entero por imagen no lo corrimos; lo que el "
       "generador elegiría y dónde lo ubicaría no lo medimos.")

# =============================================================================================
# Los de trámite (9 a 15): un gráfico cada uno
# =============================================================================================
_emb = X._emb
_rs = [_emb("hashing"), _emb("bm25"), _emb("bge"), EMB[V1]]
fig, ax = figura(9.4)
barras_v(ax, ["Hashing de\npalabras", "BM25", "BGE-base", "Qwen3-\nEmbedding"], _vs(_rs), _ics(_rs), azul=[3], ylim=(0, 0.8),
         ylabel="hit@1")
titulo(ax, f"Set de IKEA · {N_ANS} consultas")
lamina(9, "Embedder", fig, "¿Importa el embedder? Cuatro, de contar palabras a Qwen3. Qwen3 solo se distingue de BGE; contra contar "
       "palabras no, por el molde compartido. Queda Qwen3.")

fig, ax = figura(9.4)
_ds = list(X._dims)
_rd = [X._dims[d] for d in _ds]
ax.errorbar(_ds, _vs(_rd), yerr=[[v - lo for v, (lo, _) in zip(_vs(_rd), _ics(_rd), strict=True)],
                                 [hi - v for v, (_, hi) in zip(_vs(_rd), _ics(_rd), strict=True)]],
            color=TINTA2, lw=2, marker="o", ms=9, capsize=6, capthick=1.5, elinewidth=1.5)
ax.plot(1024, X._dims[1024]["hit@1"], "o", ms=13, color=AZUL, zorder=5)
for d, r in zip(_ds, _rd, strict=True):
    ax.text(d, r["hit@1_ic95"][1] + 0.012, f3(r["hit@1"]), ha="center", va="bottom", fontsize=15,
            color=AZUL if d == 1024 else TINTA, fontweight="bold" if d == 1024 else "normal")
ax.set_xscale("log", base=2)
ax.set_xticks(_ds, [str(d) for d in _ds])
ax.minorticks_off()
ax.set_xlim(22, 1500)
ax.set_ylim(0.3, 0.7)
ax.yaxis.set_major_formatter(coma(2))
ax.set_xlabel("dimensiones del vector (Matryoshka)")
ax.set_ylabel("hit@1")
titulo(ax, f"Set de IKEA · {N_ANS} consultas")
lamina(10, "Dimensión del embedding", fig, "Qwen3 deja recortar el vector: probamos de 32 a 1024 dimensiones. Con 512 da lo mismo; "
       "con este catálogo la memoria no pesa, y queda 1024.")

_rs = [X._doc, X._chunk, X._alin]
fig, ax = figura(9.4)
barras_v(ax, ["Un documento\npor producto", "Un chunk\npor línea", "Línea contra\nlínea"], _vs(_rs), _ics(_rs), azul=[0],
         ylim=(0, 0.8), ylabel="hit@1")
titulo(ax, f"Set de IKEA · {N_ANS} consultas")
lamina(11, "Chunk size", fig, "¿Partir la descripción en pedazos? No: las líneas solas pierden el contexto del producto. Un "
       "documento por producto.")

_rs = [F[Dt.BASE], F[Dt.BASE + "|exact"]]
fig, ax = figura(9.4)
barras_v(ax, ["ChromaDB\n(HNSW, aproximada)", "Búsqueda exacta\n(contra todos)"], _vs(_rs), _ics(_rs), azul=[0], ylim=(0, 0.8),
         ylabel="hit@1", ancho=0.5)
titulo(ax, f"Set de IKEA · {N_ANS} consultas", f"el mismo top-10 en {X._iguales} de {len(X._ex_a)} consultas")
lamina(12, "Base vectorial", fig, "ChromaDB busca con un índice aproximado. Contra comparar con todos no pierde nada: el mismo top-10 "
       f"en las {len(X._ex_a)} consultas. La usamos porque persiste y escala.")

_rs = [X._f_none, X._f_type, Dt.B1]
_j13 = E._j13
fig, (a, b) = figura(17.2, ncols=2, gridspec_kw=dict(width_ratios=[1.2, 1]))
barras_v(a, ["Ninguno", "Por tipo\n(la línea Type)", "Por kind\n(la categoría)"], _vs(_rs, "hit@5"), _ics(_rs, "hit@5"), azul=[2],
         ylabel="hit@5", ancho=0.55)
titulo(a, f"Set de IKEA · {N_ANS} consultas",
       f"sin el de kind, el {round(100 * DOC['otro_kind'])}% de los candidatos reales sería de otra categoría")
panel_juez(b, _j13, [("sin_kind", "Ninguno", False), ("hibrida", "Por kind", True)])
lamina(13, "Filtros por metadata", fig,
       "¿Suman los filtros? En el set de IKEA, no. De punta a punta, sin el filtro por kind: "
       f"{_j13['b']} a {_j13['a']}, con {_j13['emp']} empates; empatan. Lo usamos igual: no cuesta nada y asegura cinco "
       f"candidatos del tipo pedido. Sin él, el {round(100 * DOC['otro_kind'])} por ciento de los candidatos de los pedidos "
       "reales sería de otra categoría.")

_rs = [RLOC[Dt.BASE], X._mini, X._qrr]
fig, ax = figura(9.4)
barras_v(ax, ["Sin reranker", "MiniLM\n(cross-encoder)", "Qwen3-\nReranker"], _vs(_rs), _ics(_rs), azul=[0], ylim=(0, 0.8),
         ylabel="hit@1")
titulo(ax, f"Set de IKEA · {N_ANS} consultas")
lamina(14, "Rerankers de texto", fig, "¿Un reranker de texto ordena mejor? No: los dos empeoran, porque releen el texto que ya usó la "
       "búsqueda. El que suma mira las fotos: el experimento 5.")


def _reconocidos(res):
    xs, gs = [], []
    for c in res["por_corrida"]:
        slug = c["corrida"].split("-", 1)[1]
        xs += [1.0] * c["identificados"] + [0.0] * (c["productos"] - c["identificados"])
        gs += [slug] * c["productos"]
    return sum(xs) / len(xs), ci(xs, gs)


_pl, _llm = _reconocidos(IMG_PL), _reconocidos(IMG_LLM)
fig, ax = figura(9.4)
barras_v(ax, ["Una plantilla\n(sin llamada)", "Escrito por el LLM\n(una llamada más)"], [_pl[0], _llm[0]], [_pl[1], _llm[1]],
         azul=[0], fmt=f2, ylim=(0, 0.8), ylabel="productos reconocidos en la imagen", ancho=0.5)
titulo(ax, f"Los {IMG_PL['corridas']} ambientes · {IMG_PL['productos']} productos",
       f"LLM − plantilla, por ambiente: IC 95% {ic_txt(*DOC['escena_ic'], nd=2)}")
lamina(15, "La escena", fig, "El prompt de la imagen: ¿una plantilla, o que lo escriba el LLM? Empatan, y la plantilla ahorra una "
       "llamada: queda la plantilla.")

# =============================================================================================
# 5b · Elegir con texto o con fotos
# =============================================================================================
X.ETAPA_TXT["5b"] = "elección"
_rb = [E._r_bus, E._r_foto, E._r_txt]
_jt = E._jt
_cf = [c["cost_usd"] for c in E._elecciones("hibrida").values()]
_ct = [c["cost_usd"] for c in E._elecciones("texto").values()]
fig, (a, b, c) = figura(17.2, ncols=3, gridspec_kw=dict(width_ratios=[1.2, 1, 0.85]))
barras_v(a, ["Solo la\nbúsqueda", "Con fotos", "Solo texto"], _vs(_rb), _ics(_rb), azul=[1], ylim=(0, 0.8), ylabel="hit@1",
         ancho=0.58)
titulo(a, "Set de IKEA · reordenar el top-10", f"texto − fotos, pareado: {dif(E._d_txt)}")
panel_juez(b, _jt, [("hibrida", "Con fotos", True), ("texto", "Solo texto", False)])
barras_v(c, ["Con fotos", "Solo texto"], [statistics.mean(_cf), statistics.mean(_ct)], [_ci_simple(_cf), _ci_simple(_ct)],
         azul=[0], fmt=lambda v: usd(v, 3), ylim=(0, 0.2), nd=2, ylabel="US$ por pedido, el paso que elige", ancho=0.55)
c.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
c.yaxis.set_major_formatter(lambda v, _: "0" if v == 0 else usd(v, 2))
titulo(c, "Costo de elegir", "promedio por ambiente")
lamina("5b", "Elegir con texto o con fotos", fig,
       "El último, y por eso va al final: se nos ocurrió después de decidir todo lo demás. Elegir es, en el fondo, reordenar; "
       "el 5 lo midió mirando las fotos, nunca sin ellas. En el set de IKEA, reordenando el top-10: con fotos "
       f"{f3(E._r_foto['hit@1'])}, solo con texto {f3(E._r_txt['hit@1'])}; la diferencia pareada es casi cero. De punta a "
       f"punta, {_jt['a']} a {_jt['b']}, con {_jt['emp']} empate: dentro del ruido, que es {E.J_RUIDO['a']} a "
       f"{E.J_RUIDO['b']}. Y con texto, elegir cuesta la mitad: {usd(statistics.mean(_ct))} en vez de {usd(statistics.mean(_cf))}, porque entran "
       f"{round(E._k_txt / 1000)} mil tokens en vez de {round(E._k_foto / 1000)} mil. Decisión: el flujo sigue con fotos, como se midió todo lo "
       "demás; si con más ambientes sigue empatando, conviene el texto, por costo.")


# =============================================================================================
# ¿Sirve el coseno sin juez? El coseno de cada pieza, con su IC por bootstrap de ambientes
# =============================================================================================
def _cosenos() -> dict[str, dict]:
    """Por variante, el coseno de cada pieza y su ambiente (lo de endtoend.match_cosine, sin
    promediar). Los vectores salen de la caché del índice; el resultado se guarda en _trabajo."""
    cache = TRAB / "simple_cosenos.json"
    if cache.exists():
        return json.loads(cache.read_text())
    import numpy as np

    from amoblai import paths
    from amoblai.config import load_config
    from amoblai.evaluation.endtoend import _written
    from amoblai.furnish import steps as st
    from amoblai.infra.budget import ledger_for
    from amoblai.rag.embed import get_embedder
    from amoblai.rag.index import vectors_cached

    cfg = load_config(paths.CONFIG, {})
    emb = get_embedder("qwen3", cfg)
    ledger = ledger_for(cfg.budget, emb.account)
    out = {}
    for v, _, _ in E._COS_FILAS:
        qs, ds, gs = [], [], []
        for run in sorted((E.H / v).glob("*/")):
            if not (run / "3_choice.json").exists():
                continue
            found = json.loads((run / "2_candidates.json").read_text())
            choice = json.loads((run / "3_choice.json").read_text())
            for spec, h in st.picks(found, choice):
                if _written(h.id):
                    qs.append(spec["query"])
                    ds.append(_written(h.id))
                    gs.append(run.name)
        q, d = vectors_cached(qs, emb, cfg, ledger)[0], vectors_cached(ds, emb, cfg, ledger)[0]
        cos = np.sum(q * d, axis=1) / (np.linalg.norm(q, axis=1) * np.linalg.norm(d, axis=1))
        out[v] = {"cos": [float(x) for x in cos], "grupos": gs}
    cache.write_text(json.dumps(out))
    return out


_COS = _cosenos()
for _v, _c in _COS.items():
    assert abs(statistics.mean(_c["cos"]) - E._cos(_v)) < 5e-4, (_v, statistics.mean(_c["cos"]), E._cos(_v))
fig, ax = figura(17.2)
_fil = E._COS_FILAS  # ya ordenadas de mayor a menor
for i, (v, _et, m) in enumerate(_fil):
    mu = statistics.mean(_COS[v]["cos"])
    lo, hi = ci(_COS[v]["cos"], _COS[v]["grupos"])
    col = AZUL if v == "hibrida" else TINTA2
    ax.plot([lo, hi], [i, i], color=col, lw=2.2)
    ax.plot([lo, lo], [i - 0.15, i + 0.15], color=col, lw=2.2)
    ax.plot([hi, hi], [i - 0.15, i + 0.15], color=col, lw=2.2)
    ax.plot(mu, i, "o", ms=11, color=col, zorder=4)
    ax.text(hi + 0.002, i, f"  {f3(mu)}", va="center", ha="left", fontsize=15, color=col,
            fontweight="bold" if v == "hibrida" else "normal")
    if m != "—":
        ax.text(1.01, i, f"juez {m}", transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=15, color=TINTA2)
ax.set_yticks(range(len(_fil)), [e for _, e, _ in _fil])
ax.invert_yaxis()
ax.tick_params(axis="y", length=0, pad=8)
ax.grid(axis="y", visible=False)
ax.grid(axis="x", visible=True)
ax.set_xlim(0.66, 0.84)
ax.xaxis.set_major_formatter(coma(2))
ax.set_xlabel("coseno entre la ficha del plan y el producto elegido (Qwen3), promedio con su IC 95%")
titulo(ax, "Los 11 ambientes vacíos, cada variante",
       f"a la derecha, el juez: ambientes ganados por la variante contra la versión 2 · * al azar, contra la versión 1, en "
       f"{E.J_AZ['n']} ambientes")
fig.get_layout_engine().set(rect=(0, 0, 0.93, 1))
lamina(None, "¿Sirve el coseno sin juez?", fig,
       "Una métrica sin juez: el coseno entre la ficha que escribe el plan y el producto elegido, con el mismo embedder para "
       f"todas las variantes. Es gratis. Separa lo malo: al azar da {f3(E._cos('azar'))}, y la frase natural y el texto del "
       f"vendedor, {f3(E._cos('frase'))}. Pero no ordena lo bueno: la versión 1 saca más que la 2, {f3(E._cos('densa'))} contra "
       f"{f3(E._cos('hibrida'))}, y pierde {E._vs2(E.J_V1, True)} con el juez; y tres candidatos queda segundo, y pierde {E._vs2(E._j5)}. Sirve de alarma barata; no reemplaza al juez.",
       pie=f"{IC} · en azul, la versión 2", sid="s-cos")

