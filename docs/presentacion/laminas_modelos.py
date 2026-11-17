"""Los experimentos del 2026-11-16, al final de presentacion_simple.html (después del Ejercicio 4):
qué modelo elige, qué modelo juzga, qué modelo dibuja y el embedding de OpenAI. Van después del
camino que ya teníamos: lo que cambia una decisión queda como un paso más, al final.

Corridas (todas en datos/):
- elegir, contra el set de IKEA: configs/ablaciones/reranking-modelos.yaml
- elegir, de punta a punta: configs/punta_a_punta/modelos.yaml (juez Opus)
- juzgar: configs/punta_a_punta/juez_sonnet.yaml y juez_haiku.yaml (las mismas listas que ya
  juzgó Opus)
- dibujar: `amoblai comparar-imagen` (amoblar/img-<modelo>-<ambiente>) y `evaluar-imagen`
- el embedding: configs/ablaciones/embedder-openai.yaml (con las réplicas r2 y r3) y
  configs/punta_a_punta/openai.yaml
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

import datos as Dt
import laminas_extra as E
from datos import AM, PAP, f2, f3, ic_txt, jload, p_signos, resumen_juez, sg, usd
from graficos_simple import (
    AZUL,
    ERR,
    GRIS,
    TINTA,
    TINTA2,
    barras_v,
    ci,
    coma,
    figura,
    forest,
    panel_juez,
    png,
    titulo,
)
from laminas_simple import IC
from piezas import foto, kick
from registro import lam

CSS = """
.simple .cu{position:absolute;left:96px;right:96px;top:196px;bottom:108px;display:flex;flex-direction:column;justify-content:center;gap:26px}
.simple .cu-f{display:flex;gap:12px;justify-content:center}
.simple .cu-c{margin:0;display:flex;flex-direction:column;gap:8px}
.simple .cu-c .foto{background-size:contain;background-color:transparent}
.simple .cu-c figcaption{font:500 17px/1.2 var(--sans);color:var(--tinta-2);text-align:center}
.simple .cu-c:first-child figcaption{color:var(--tinta-3)}
"""
IDS: list[str] = []
H = PAP / "hibrida"
MOD = {"opus": "Opus 5.5", "sonnet": "Sonnet 5.5", "haiku": "Haiku 5.5"}


def lamina(n: int, tema: str, etapa: str, fig, notas: str, pie: str, sid: str = "") -> None:
    b64, w, h = png(fig)
    sid = sid or f"s{n}"
    lam(sid, f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · {etapa}")}
<h2 class="t chico">{tema}</h2>
<div class="sf"><img src="data:image/png;base64,{b64}" style="width:{w}px;height:{h}px" alt="{tema}"></div>
<p class="sf-pie">{pie}</p>''', notas, 0, clase="clara simple")
    IDS.append(sid)


def _gasto(step: str) -> dict[str, float]:
    """Lo que costó en promedio cada llamada de un paso, por modelo (datos/resultados/gastos.jsonl)."""
    por: dict[str, list[float]] = {}
    for line in (Dt.RES / "gastos.jsonl").read_text().splitlines():
        t = json.loads(line)
        if t["step"] == step:
            por.setdefault(t["model"], []).append(t["cost_usd"])
    return {m: statistics.mean(v) for m, v in por.items()}


def _costo_lista(variante: str) -> float:
    """Lo que costó elegir la lista de un ambiente (3_choice.json), en promedio, en una variante."""
    cs = [jload(d / "3_choice.json")["cost_usd"] for d in sorted((H / variante).glob("*/")) if (d / "3_choice.json").exists()]
    return statistics.mean(cs)


# =============================================================================================
# 16 · Qué modelo elige
# =============================================================================================
RM = Dt.ultima("_ablacion-reranking-modelos")
_RM = Dt.metricas(RM)
_B = "qwen3|description|filtro-type"
_rm = {k: _RM[f"{_B}|rerank-{k}"] for k in MOD}
_rd = {k: Dt.paired(RM, f"{_B}|rerank-{k}", f"{_B}|rerank-opus") for k in ("sonnet", "haiku")}
_fallas = {k: 0 for k in MOD}  # respuestas que no eran el JSON pedido, dos veces: queda el orden de la búsqueda
for _f in (Dt.D_ / "cache" / "rerank").glob("*.json"):
    _x = json.loads(_f.read_text())
    if "error" in _x:
        _fallas[next((k for k in MOD if k in _x.get("model", "")), "opus")] += 1
J_SON, J_HAI = E._juez("sonnet"), E._juez("haiku")
_cl = {k: _costo_lista(v) for k, v in (("opus", "hibrida"), ("sonnet", "sonnet"), ("haiku", "haiku"))}

fig, (a, b, c, d) = figura(17.2, ncols=4, gridspec_kw=dict(width_ratios=[1.25, 0.78, 0.78, 0.72]))
_et = ["sin VLM", *[MOD[k].split()[0] for k in MOD]]
_rr = [_RM[_B], *[_rm[k] for k in MOD]]
barras_v(a, _et, [r["hit@1"] for r in _rr], [r["hit@1_ic95"] for r in _rr], azul=[1], fmt=f3, ylim=(0, 0.85), ylabel="hit@1")
titulo(a, f"Set de IKEA · {_RM[_B]['answerable']} consultas",
       f"contra Opus: Sonnet {sg(_rd['sonnet']['hit@1'], 2)} · Haiku {sg(_rd['haiku']['hit@1'], 2)}")
panel_juez(b, J_SON, [("hibrida", "Opus", True), ("sonnet", "Sonnet", False)], t1="Opus contra Sonnet", corto=True)
panel_juez(c, J_HAI, [("hibrida", "Opus", True), ("haiku", "Haiku", False)], t1="Opus contra Haiku", corto=True)
c.set_ylabel("")
_cv = [_cl[k] for k in MOD]
barras_v(d, [MOD[k].split()[0] for k in MOD], _cv, [None] * 3, azul=[0], fmt=lambda v: usd(v, 3), ylim=(0, 0.18), nd=2,
         ylabel="US$ por lista")
titulo(d, "Lo que cuesta elegir", "una lista, de punta a punta")
_gr = _gasto("eval.rerank")
lamina(16, "Qué modelo elige", "elección", fig,
       f"Hasta acá elige Opus. ¿Cuánto se pierde con uno más chico? Mismo paso y mismo prompt, con Sonnet y con Haiku. En el "
       f"set de IKEA se pierde poco: Opus {f3(_rm['opus']['hit@1'])}, Sonnet {f3(_rm['sonnet']['hit@1'])} y Haiku "
       f"{f3(_rm['haiku']['hit@1'])}. De punta a punta, más: el juez prefiere a Opus {J_SON['a']} a {J_SON['b']} contra Sonnet "
       f"y {J_HAI['a']} a {J_HAI['b']} contra Haiku. Ese juez es Opus; lo revisamos en la que sigue. Una lista cuesta "
       f"{round(100 * _cl['opus'])} centavos con Opus, {round(100 * _cl['sonnet'])} con Sonnet y menos de uno con Haiku. "
       "Sigue Opus: el camino no cambia.",
       pie=f"{IC} · en azul, lo que queda en el flujo · sin VLM: el primero de la búsqueda")


# =============================================================================================
# 17 · Qué modelo juzga
# =============================================================================================
COMP = [("densa", "hibrida"), ("hibrida", "k3"), ("hibrida", "vendedor"), ("hibrida", "texto")]


def _jueces(m: str) -> list[dict]:
    suf = "" if m == "opus" else f"_juez-{m}"
    return [jload(H / f"juez_{a}_vs_{b}{suf}.json") for a, b in COMP]


_JZ = {m: _jueces(m) for m in MOD}


def _acuerdo(m: str) -> dict:
    """Contra Opus, sobre las mismas listas: el ganador de cada ambiente y la nota de cada producto."""
    gan, gg, notas, ng, coh, cg, util, ug = [], [], [], [], [], [], [], []
    for jo, jm in zip(_JZ["opus"], _JZ[m], strict=True):
        ro = {r["slug"]: r for r in jo["detalle"]}
        for r in jm["detalle"]:
            o = ro[r["slug"]]
            gan.append(float(r["ganador"] == o["ganador"]))
            gg.append(r["slug"])
            coh.append(float(r["votos"][0] == r["votos"][1]))
            cg.append(r["slug"])
            for lado in r["puntajes"]:
                for pm, po in zip(r["puntajes"][lado], o["puntajes"][lado], strict=True):
                    for x, y in zip(pm["grades"], po["grades"], strict=True):
                        notas.append(float(x == y))
                        ng.append(r["slug"])
                    for x in pm["grades"]:
                        util.append(float(x == 2))
                        ug.append(r["slug"])
    costo = sum(j["costo_usd"] for j in _JZ[m]) / sum(2 * len(j["detalle"]) for j in _JZ[m])
    return {"ganador": (statistics.mean(gan), ci(gan, gg)), "nota": (statistics.mean(notas), ci(notas, ng)),
            "coherencia": (statistics.mean(coh), ci(coh, cg)), "util": (statistics.mean(util), ci(util, ug)),
            "costo": costo, "n": len(gan)}


def _contra(m: str) -> int:
    """Ambientes donde el juez m y Opus eligen ganadores opuestos (no cuenta los empates)."""
    n = 0
    for jo, jm in zip(_JZ["opus"], _JZ[m], strict=True):
        ro = {r["slug"]: r["ganador"] for r in jo["detalle"]}
        n += sum(1 for r in jm["detalle"] if "tie" not in (r["ganador"], ro[r["slug"]]) and r["ganador"] != ro[r["slug"]])
    return n


AC = {m: _acuerdo(m) for m in MOD}

fig, (a, b, c) = figura(17.2, ncols=3, gridspec_kw=dict(width_ratios=[1.2, 1, 0.75]))
for k, met in enumerate(("ganador", "nota")):
    for s, m in enumerate(("sonnet", "haiku")):
        x = k + (s - 0.5) * 0.36
        v, (lo, hi) = AC[m][met]
        a.bar(x, v, width=0.34, color=GRIS if m == "sonnet" else "#C9CFDB", label=MOD[m] if k == 0 else None, zorder=2)
        a.errorbar(x, v, yerr=[[v - lo], [hi - v]], **ERR)
        a.text(x, hi + 0.015, f2(v), ha="center", va="bottom", fontsize=15, color=TINTA)
a.set_xticks([0, 1], ["quién gana\nel ambiente", "la nota de\ncada producto"])
a.tick_params(axis="x", length=0, pad=8)
a.set_ylim(0, 1.1)
a.yaxis.set_major_formatter(coma(1))
a.legend(loc="upper right")
titulo(a, "¿Coincide con Opus?", f"{AC['sonnet']['n']} veredictos ({len(COMP)} comparaciones × 11 ambientes) · lo contradicen: "
       f"{_contra('sonnet')} y {_contra('haiku')}")
barras_v(b, [MOD[m].split()[0] for m in MOD], [AC[m]["coherencia"][0] for m in MOD], [AC[m]["coherencia"][1] for m in MOD],
         azul=[0], fmt=f2, ylim=(0, 1.1), nd=1, ylabel="ambientes")
titulo(b, "El mismo veredicto en los dos órdenes", "cambiar de lugar las listas no cambia al ganador")
barras_v(c, [MOD[m].split()[0] for m in MOD], [AC[m]["costo"] for m in MOD], [None] * 3, azul=[0],
         fmt=lambda v: usd(v, 3), ylim=(0, 0.06), nd=2, ylabel="US$ por veredicto")
titulo(c, "Lo que cuesta", "un veredicto (dos listas)")
CONTRA = {m: _contra(m) for m in ("sonnet", "haiku")}
lamina(17, "Qué modelo juzga", "evaluación", fig,
       f"¿Y un juez más chico? Sonnet y Haiku juzgaron los mismos {AC['sonnet']['n']} pares de listas que Opus. Casi nunca lo "
       f"contradicen, {CONTRA['sonnet']} y {CONTRA['haiku']} veces: el resto de las diferencias son empates. Pero son menos "
       f"coherentes: si se invierte el orden de las listas, Opus mantiene el veredicto en el "
       f"{round(100 * AC['opus']['coherencia'][0])}% de los ambientes; Sonnet, en el {round(100 * AC['sonnet']['coherencia'][0])}, "
       f"y Haiku, en el {round(100 * AC['haiku']['coherencia'][0])}. Sigue juzgando Opus. Lo que falta es un juez de otro "
       "proveedor.",
       pie=f"{IC} · en azul, el juez del trabajo")


# =============================================================================================
# 18 · Qué modelo dibuja
# =============================================================================================
GEN = {"nano_banana_2": "Nano Banana 2", "nano_banana_pro": "Nano Banana Pro", "seedream_45": "Seedream 4.5",
       "gpt_image_2": "gpt-image-2", "gpt_image_15": "gpt-image-1.5", "gpt_image_mini": "gpt-image-1-mini"}
CUENTA = {"nano_banana_2": "fal", "nano_banana_pro": "fal", "seedream_45": "fal",
          "gpt_image_2": "OpenAI", "gpt_image_15": "OpenAI", "gpt_image_mini": "OpenAI"}
_FINALES = sorted(d.name.removeprefix("final-") for d in AM.glob("final-*"))


def _corridas(g: str) -> list[Path] | None:
    ds = [AM / f"img-{g}-{s}" for s in _FINALES]
    return ds if all((d / "6_metricas_imagen.json").exists() for d in ds) else None


def _imagen(g: str) -> dict:
    """Sobre los productos que recibió cada modelo: cuáles aparecen y cuáles se reconocen como el
    exacto; si conservó el ambiente (SIFT, un intento) y lo que costó."""
    from amoblai.furnish import steps as st

    rec, pres, gr, amb, ag, cost = [], [], [], [], [], []
    for d in _corridas(g):
        met = jload(d / "6_metricas_imagen.json")
        img = jload(d / "5_image.json")
        found = jload(d / "2_candidates.json")
        choice = jload(d / "3_choice.json")
        limite = 9 if g == "seedream_45" else 13
        recibidos = {h.id for _, h in st.picks(found, choice)[:limite]}
        for p in met["productos"]:
            if p["id"] in recibidos:
                pres.append(float(p["detectado"]))
                rec.append(float(p["detectado"] and p["puesto"] == 1))
                gr.append(d.name)
        a0 = img["attempts"][0]
        amb.append(float(bool(a0.get("ok"))))
        ag.append(d.name)
        cost.append(a0.get("cost_usd") or 0.0)
    return {"rec": (statistics.mean(rec), ci(rec, gr)), "pres": (statistics.mean(pres), ci(pres, gr)),
            "amb": (statistics.mean(amb), ci(amb, ag)), "amb_n": int(sum(amb)), "costo": statistics.mean(cost), "n": len(ag)}


GENS = [g for g in GEN if _corridas(g)]
IM_ = {g: _imagen(g) for g in GENS}

fig, (a, b, c) = figura(17.2, ncols=3, gridspec_kw=dict(width_ratios=[1.15, 1.15, 0.9]))
_eg = [GEN[g].replace(" ", "\n", 1) if g.startswith("nano") else GEN[g].replace("-", "-\n", 1) for g in GENS]
barras_v(a, _eg, [IM_[g]["rec"][0] for g in GENS], [IM_[g]["rec"][1] for g in GENS], azul=[0], fmt=f2, ylim=(0, 0.8), nd=1,
         ylabel="productos")
titulo(a, "El producto exacto, reconocido en la imagen", "de los que recibió cada modelo")
barras_v(b, _eg, [IM_[g]["amb"][0] for g in GENS], [IM_[g]["amb"][1] for g in GENS], azul=[0],
         fmt=lambda v: f"{round(v * 11)} de 11", ylim=(0, 1.15), nd=1, ylabel="imágenes")
titulo(b, "Conserva el ambiente (SIFT)", "al primer intento")
barras_v(c, _eg, [IM_[g]["costo"] for g in GENS], [None] * len(GENS), azul=[0], fmt=lambda v: usd(v, 3), ylim=(0, 0.2),
         nd=2, ylabel="US$ por imagen")
titulo(c, "Lo que cuesta", "una imagen")
for ax in (a, b, c):
    ax.tick_params(axis="x", labelsize=13)
_nb, _g2, _g15, _mini = (IM_[g] for g in ("nano_banana_2", "gpt_image_2", "gpt_image_15", "gpt_image_mini"))
# Lo que dicen las notas: gpt-image-2 empata con Nano Banana 2 y los otros dos quedan abajo
assert abs(_g2["rec"][0] - _nb["rec"][0]) < 0.05 and abs(_g2["amb_n"] - _nb["amb_n"]) <= 1 and _g2["costo"] > _nb["costo"]
assert max(_g15["rec"][0], _mini["rec"][0]) < _nb["rec"][0] - 0.05
lamina(18, "Qué modelo dibuja", "imagen", fig,
       f"El modelo de imagen nunca lo habíamos puesto a prueba. Misma lista, mismo prompt, un intento cada uno: Nano Banana 2 "
       f"contra tres de OpenAI. gpt-image-2 empata: reconoce el producto exacto en {round(100 * _g2['rec'][0])} de cada 100, "
       f"contra {round(100 * _nb['rec'][0])}, y conserva el cuarto en {_g2['amb_n']} de 11, contra {_nb['amb_n']}. Pero cuesta "
       f"{round(100 * _g2['costo'])} centavos, contra {round(100 * _nb['costo'])}. gpt-image-1.5 y el mini quedan abajo: "
       f"reconocen {round(100 * _g15['rec'][0])} y {round(100 * _mini['rec'][0])} de cada 100. Sigue Nano Banana 2: con "
       "gpt-image-2 la decisión no cambiaría.",
       pie=f"{IC} · los 11 ambientes vacíos, la misma lista y el mismo prompt · en azul, el del flujo")

# La comparación cualitativa: dos ambientes, la foto vacía y lo que dibujó cada modelo
CUAL = ["publica-living-japandi", "publica-loft-industrial"]
_w = 1728 // (len(GENS) + 1) - 12
_h = min(round(_w * 0.66), 330)     # dos filas con su epígrafe entre el título y el pie
_w = min(_w, round(_h / 0.66))


def _fila(slug: str) -> str:
    celdas = [("Foto vacía", AM / f"final-{slug}" / "room.jpg")] + [(GEN[g], AM / f"img-{g}-{slug}" / "final.png") for g in GENS]
    return "".join(f'<figure class="cu-c">{foto(f"cu-{i}-{slug}", src, _w, _h, q=80, modo="fit")}<figcaption>{et}</figcaption></figure>'
                   for i, (et, src) in enumerate(celdas))


lam("s18b", "Exp. 18: lo que se ve", "Experimentos · 18", f'''
{kick("E18", "experimento 18 · imagen")}
<h2 class="t chico">Lo que se ve</h2>
<div class="cu">{"".join(f'<div class="cu-f">{_fila(s)}</div>' for s in CUAL)}</div>
<p class="sf-pie">la misma lista y el mismo prompt · un intento por modelo</p>''',
    "Así se ve, en dos ambientes; a la izquierda, la foto vacía. Nano Banana 2 y gpt-image-2 amoblan esa misma foto. "
    "gpt-image-1.5 cambia el encuadre, y el mini vuelve a dibujar el cuarto entero, con otra cámara y otra luz. Para "
    "mostrarle a alguien su propio ambiente, eso no sirve.", 0, clase="clara simple")
IDS.append("s18b")


# =============================================================================================
# 19 · El embedding de OpenAI
# =============================================================================================
OA = {r: Dt.metricas(Dt.ultima(f"_ablacion-embedder-openai{s}")) for r, s in (("r1", ""), ("r2", "-r2"), ("r3", "-r3"))}
OA_RUN = {r: Dt.ultima(f"_ablacion-embedder-openai{s}") for r, s in (("r1", ""), ("r2", "-r2"), ("r3", "-r3"))}
_K = "description|filtro-kind"
_FU = "|+bm25+siglip2"
_od = {(r, t): Dt.paired(OA_RUN[r], f"openai|{_K}{t}", f"qwen3|{_K}{t}") for r in OA for t in ("", _FU)}
J_OA = resumen_juez(jload(H / "juez_hibrida_vs_openai.json"))
P_OA = p_signos(J_OA["b"], J_OA["a"])

fig, (a, b, c) = figura(17.2, ncols=3, gridspec_kw=dict(width_ratios=[1.05, 1.15, 0.85]))
for k, t in enumerate(("", _FU)):
    for s, (e, lbl, az) in enumerate((("qwen3", "Qwen3 (local)", False), ("openai", "OpenAI (por API)", True))):
        r = OA["r1"][f"{e}|{_K}{t}"]
        x, v, (lo, hi) = k + (s - 0.5) * 0.36, r["hit@1"], r["hit@1_ic95"]
        a.bar(x, v, width=0.34, color=AZUL if az else GRIS, label=lbl if k == 0 else None, zorder=2)
        a.errorbar(x, v, yerr=[[v - lo], [hi - v]], **ERR)
        a.text(x, hi + 0.015, f3(v), ha="center", va="bottom", fontsize=15, color=AZUL if az else TINTA,
               fontweight="bold" if az else "normal")
a.set_xticks([0, 1], ["solo la densa", "híbrida"])
a.tick_params(axis="x", length=0, pad=8)
a.set_ylim(0, 0.85)
a.yaxis.set_major_formatter(coma(2))
a.set_ylabel("hit@1")
a.legend(loc="upper left")
titulo(a, f"Set de IKEA · {OA['r1'][f'qwen3|{_K}']['answerable']} consultas", "el mismo índice, cambia el embedder")
_fl = [(r, t) for t in ("", _FU) for r in OA]
forest(b, [f"{'densa' if t == '' else 'híbrida'} · redactor {r[1]}" for r, t in _fl], [_od[x]["hit@1"] for x in _fl],
       [_od[x]["hit@1_ic95"] for x in _fl], azul=[3], xlim=(-0.03, 0.12), nd=3,
       xlabel="hit@1, OpenAI menos Qwen3, pareado, con su IC 95%")
titulo(b, "Con los tres redactores de consultas", "las mismas consultas escritas tres veces")
panel_juez(c, J_OA, [("hibrida", "Qwen3", False), ("openai", "OpenAI", True)], t1="Los 11 ambientes vacíos", corto=True)
_eo = sum(json.loads(x)["cost_usd"] for x in (Dt.RES / "gastos.jsonl").read_text().splitlines()
          if json.loads(x)["model"] == "text-embedding-3-large")
_hr = [_od[(r, _FU)]["hit@1"] for r in OA]
assert max(abs(x) for x in _hr[1:]) < 0.015   # «con los otros dos redactores, casi cero»
lamina(19, "El embedding de OpenAI", "índice", fig,
       f"Faltaba un embedding pago: cambiamos Qwen3, local, por el más grande de OpenAI, solo en la parte densa. Sola, la densa "
       f"sube {f2(_od[('r1', '')]['hit@1'])} de hit@1. Dentro de la híbrida, {f2(_od[('r1', _FU)]['hit@1'])}, y con los otros "
       f"dos redactores, casi cero: la léxica y la foto ya cubren mucho. De punta a punta, el juez elige la de OpenAI "
       f"{J_OA['b']} a {J_OA['a']}, con {J_OA['emp']} empates; el piso de ruido era {E.J_RUIDO['a']} a {E.J_RUIDO['b']}. "
       f"Embeber todo costó {round(100 * _eo)} centavos. Es la versión 3, y va al final para que todo lo anterior quede medido "
       "con Qwen3.",
       pie=f"{IC} · en azul, lo que queda: la versión 3")
