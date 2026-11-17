"""Los experimentos, por el ranking de la revisión del 2026-11-12 (docs/REVISION.md, sección 4).
Ocho con lámina propia (del 1 al 8): una lámina oscura con la pregunta (por qué y qué se comparó, con la etapa
encendida en el flujo) y una clara con los resultados, la diferencia pareada y la decisión (el
talón); el 4 y el 7, que miden al set de evaluación, y el 8, buscar por imagen, van en una sola lámina. En el medio, el camino
incremental que resume los tres primeros. Y al final, juntos en dos láminas, los siete de trámite:
lo que la cátedra dijo que iba a preguntar, con la respuesta en una línea (y la escena, que se
midió en los 11 ambientes y empató)."""

from __future__ import annotations

import statistics

from datos import (ABL_DIR, B1, B2, BASE, GT_ROOM_PATH, ROOT, V0_REC, V0_SOFA_OK, VT, CTX_TOKENS, IMG_LLM, IMG_PL, J_CTX, CAM, CON, CURVA, D,
                   D21, DIAG, DOC, EMB, ESTILO, F, FAM_REL, FAM_TOP, FRASES, HIB, HIB_R, ITEMS, J_AZAR, JA, K, N_ANS, P_AZAR, RLOC, RR, RR_DIR, UTIL1, V1, V2, dif, esc,
                   f1, f2, f3, ic_txt, media_desvio, miles, nb, paired, pct, rankings, sg, G_ANOT2, G_OTROS2, usd, C_PEDIDO)
from piezas import ETAPA_EXP, barras, flujo, foto, kick, lineas_svg, minimapa, producto, variantes_html
from registro import lam

ETAPA_TXT = {1: "descripción", 2: "plan", 3: "búsqueda", 4: "el set de evaluación", 5: "búsqueda y elección",
             6: "búsqueda", 7: "el set de evaluación", 8: "búsqueda"}


# Sobre qué configuración corrió cada uno (la lámina de partida dice que cada experimento cambia una sola cosa)
_TIPO = "la versión 1, con filtro por tipo"
SOBRE = {1: "el RAG naive", 2: "la descripción, con filtro por kind", 3: "descripción + ficha, con filtro por kind",
         4: "la versión 1", 5: _TIPO, 6: "A y B, la versión 1 · C, contra la versión 2", 7: "las versiones 1 y 2",
         8: "por texto, descripción + ficha, con filtro por tipo",
         9: "la versión 1", 10: _TIPO, 11: _TIPO, 12: _TIPO, 13: "la versión 1", 14: _TIPO, 15: "el flujo entero", None: _TIPO}


def sobre(n) -> str:
    return f'<p class="sobre"><span>sobre</span> {SOBRE[n]}</p>' if n not in (1, 2) else ""


def pregunta(n, tema, titulo, porque, variantes, notas, seg, extra="", cls=""):
    """Lámina de la pregunta: el porqué en una línea (paso 0) y qué se comparó, en etiquetas (paso 1),
    con la etapa encendida en el flujo. variantes: lista de (letra, nombre, detalle) o el HTML ya armado."""
    vs = variantes if isinstance(variantes, str) else variantes_html(variantes)
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
<div class="izq {cls}">
  {kick(f"E{n}", f"experimento {n} · {ETAPA_TXT[n]}")}
  <h2 class="t chico">{titulo}</h2>
  {f'<p class="porque">{porque}</p>' if porque else ""}
  {extra}
  <div class="exp-blq" data-paso="1">
    <span class="et">qué se comparó</span>
    {vs}
    {sobre(n)}
  </div>
</div>
<div class="esq">{flujo(pines=[n])}</div>''', notas, seg, focos=[" ".join(ETAPA_EXP[n])])


def resultado(n, tema, cuerpo, clave, valor, decision, notas, seg, paso_dec=2, rotulo="decisión"):
    lam(f"e{n}r", f"Exp. {n}: resultados", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · resultados")}
<h2 class="t chico">{tema}</h2>
{minimapa(n)}
<div class="res-cuerpo">{cuerpo}</div>''', notas, seg, clase="clara")


def unica(n, tema, titulo, porque, variantes, res_html, clave, valor, decision, notas, seg, rotulo="decisión"):
    """La pregunta, qué se comparó, el resultado y la decisión en una sola lámina."""
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · {ETAPA_TXT[n]}")}
{minimapa(n)}
<div class="un-izq">
  <h2 class="t chico">{titulo}</h2>
  <p class="porque">{porque}</p>
  <div class="exp-blq" data-paso="1">
    <span class="et">qué se comparó</span>
    {variantes_html(variantes)}
    {sobre(n)}
  </div>
</div>
<div class="un-der" data-paso="2">{res_html}</div>''', notas, seg, clase="clara unica")


# =============================================================================================
# 1 · Qué se indexa
# =============================================================================================
K_NAIVE, K_DESC, K_FICHA = "qwen3|seller-full|filtro-none|consulta-piece", "qwen3|description|filtro-none|consulta-piece", "qwen3|description|filtro-none"
_n1, _n2 = CAM[K_NAIVE], CAM[K_DESC]
_d_idx = _n2["vs_anterior"]
_d_ficha = paired(ABL_DIR, "qwen3|description|filtro-none", "qwen3|seller|filtro-none")  # lo mismo, con la consulta escrita como ficha
_nol = ITEMS["102.335.32"]
pregunta(1, "Qué se indexa", "¿Alcanza con el texto del vendedor, o hay que <em>describir cada producto mirando su foto</em>?",
         "La gente pide estilo, color y materiales, y eso está en la foto.",
         [("A", "El texto del vendedor", ""), ("B", "La descripción desde la foto", "")],
         ["El texto de IKEA es una frase de marketing, como esta, y la gente pide estilo, color y materiales, que están en la "
          "foto. ¿Vale la pena describir cada producto? Se hace una sola vez, offline.",
          "Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una "
          "frase corta sin reescribir, para medir un solo cambio."],
         30, extra=f'''<div class="vend">{producto("102.335.32", 92)}<div><span class="et">el texto de IKEA de este sillón</span>
         <q>{esc(_nol["description"])}</q></div></div>''')
resultado(1, "Qué se indexa", f'''
<div class="res-e1">
  <div>{barras([dict(letra="A", et="Texto del vendedor", v=_n1["hit@1"], ic=_n1["hit@1_ic95"]),
                dict(letra="B", et="Descripción desde la foto", v=_n2["hit@1"], ic=_n2["hit@1_ic95"], gana=True)], titulo="hit@1")}
       {barras([dict(letra="A", et="Texto del vendedor", v=_n1["hit@5"], ic=_n1["hit@5_ic95"]),
                dict(letra="B", et="Descripción desde la foto", v=_n2["hit@5"], ic=_n2["hit@5_ic95"], gana=True)],
               titulo="hit@5", cls="sep")}</div>
  <div class="grande-n" data-paso="1"><b>{sg(_d_idx["hit@1"], 2)}</b><span>de hit@1, pareado · IC 95% {ic_txt(*_d_idx["hit@1_ic95"])}</span></div>
</div>''', "se indexa", "la descripción", "Se indexa la descripción: <mark>lo que más pesa</mark>.",
          [f"Con el texto del vendedor, hit@1 da {f2(_n1['hit@1'])}; con la descripción, {f2(_n2['hit@1'])}: casi el triple, y "
           f"hit@5 pasa de {f2(_n1['hit@5'])} a {f2(_n2['hit@5'])}. La diferencia es pareada y su intervalo no toca el cero; con "
           "la consulta escrita como ficha es mayor: los dos cambios se potencian.",
           "Decisión: se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo."], 35)

# =============================================================================================
# 2 · Cómo se escribe la consulta, contra no reescribirla
# =============================================================================================
_q_full, _q_piece = CON[V1], CON[V1 + "|consulta-piece"]
_q_type, _q_kind = CON[V1 + "|consulta-type"], CON[V1 + "|consulta-kind"]
_s_full, _s_piece = CON["siglip2|description|filtro-kind"], CON["siglip2|description|filtro-kind|consulta-piece"]
_d_q = _q_piece["vs_base"]  # la frase natural menos la ficha
D_CONSULTA = -_d_q["hit@1"]  # lo que suma la ficha sobre la frase natural
_lo_q, _hi_q = _d_q["hit@1_ic95"]
pregunta(2, "Cómo se escribe la consulta", "¿Cuánto suma escribir la consulta <em>como una ficha del catálogo</em>, contra no reescribirla?",
         "",
         [("A", "La ficha: las 8 líneas del catálogo", ""), ("B", "La frase natural, sin reescribir", ""),
          ("C·D", "Solo la línea Type, o solo el kind", "")],
         ["El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced "
          "RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que "
          "es azar por construcción.",
          f"La ficha contra la frase natural: las pocas palabras con que el redactor nombró la pieza, como «{esc(FRASES[0])}». "
          "Con la búsqueda densa del flujo, y también contra la foto del producto."],
         30, extra='<p class="adv">Advanced RAG · query expansion (HyDE)</p>')
resultado(2, "Cómo se escribe la consulta", f'''
<div class="res-2 r-2 r2n">
  <div>{barras([dict(letra="A", et="La ficha", v=_q_full["hit@1"], ic=_q_full["hit@1_ic95"], gana=True, vtxt=f3(_q_full["hit@1"])),
                dict(letra="B", et="La frase natural", v=_q_piece["hit@1"], ic=_q_piece["hit@1_ic95"], vtxt=f3(_q_piece["hit@1"])),
                dict(letra="C", et="Solo la línea Type", v=_q_type["hit@1"], ic=_q_type["hit@1_ic95"], vtxt=f3(_q_type["hit@1"])),
                dict(letra="D", et="Solo el kind", v=_q_kind["hit@1"], ic=_q_kind["hit@1_ic95"], vtxt=f3(_q_kind["hit@1"]))],
               titulo="hit@1", cls="gb-compacto")}</div>
  <div>
    <div class="grande-n" data-paso="1"><b>{sg(D_CONSULTA, 2)}</b><span>de hit@1 con la ficha · IC 95% {ic_txt(-_hi_q, -_lo_q)}</span></div>
  </div>
</div>''',
          "consulta", "la ficha", "El plan sigue escribiendo la ficha. Texto y foto <mark>fallan distinto</mark>: un argumento "
          "para la híbrida.",
          [f"La ficha da {f3(_q_full['hit@1'])} y la frase natural {f3(_q_piece['hit@1'])}: suma {sg(-_d_q['hit@1'], 2)}, con un "
           "intervalo lejos del cero. El texto necesita que la consulta hable como el catálogo.",
           "Decisión: el plan sigue escribiendo la ficha."], 40)

# =============================================================================================
# 3 · Búsqueda léxica, por foto e híbrida
# =============================================================================================
HK = {"lexica": "bm25|description|filtro-kind", "foto": "siglip2|description|filtro-kind", "clip": "clip|description|filtro-kind",
      "densa+lexica": V1 + "|+bm25", "densa+foto": V1 + "|+siglip2", "lexica+foto": "bm25|description|filtro-kind|+siglip2",
      "rrf": V2 + "|fusion-rrf"}


def _hrow(letra_, key, et, sub="", gana=False):
    x = HIB[key]
    return dict(letra=letra_, et=et, sub=sub, v=x["hit@1"], ic=x["hit@1_ic95"], vtxt=f3(x["hit@1"]), gana=gana,
                nota=dif(x["vs_base"]) if "vs_base" in x else "la base: versión 1")


pregunta(3, "Léxica, por foto e híbrida", "¿Suman la búsqueda por palabras <em>y la foto del producto</em>?",
         "¿Hace falta el embedder? ¿Y embeber la foto, que nunca medimos?",
         [("A", "Densa: Qwen3", ""), ("B", "Léxica: BM25", ""), ("C", "Por foto: SigLIP 2 (y CLIP)", ""),
          ("+", "Fusionadas", "")],
         ["Dos dudas sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo "
          "tiene fotos: hay dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa "
          "nunca la habíamos medido.",
          "Tres buscadores sobre las mismas consultas, con el filtro por kind: el denso, Qwen3 sobre las descripciones; el "
          "léxico, BM25; y por foto, SigLIP 2, la consulta en una frase contra la foto. Y sus fusiones."],
         30, extra='<p class="adv">Advanced RAG · búsqueda híbrida y multimodal</p>')
resultado(3, "Búsqueda léxica, por foto e híbrida", f'''
<div class="res-e3">
  <div>{barras([_hrow("A", V1, "Densa: Qwen3"), _hrow("B", HK["lexica"], "Léxica: BM25"), _hrow("C", HK["foto"], "Por foto: SigLIP 2"),
                _hrow("C", HK["clip"], "Por foto: CLIP ViT-B/32"), _hrow("+", HK["densa+lexica"], "Densa + léxica"),
                _hrow("+", HK["densa+foto"], "Densa + foto"), _hrow("+", HK["lexica+foto"], "Léxica + foto"),
                _hrow("+", V2, "Densa + léxica + foto", gana=True)],
               titulo="hit@1 · y la diferencia pareada contra la densa", cls="gb-e3")}</div>
  <div class="grande-n" data-paso="1"><b>{sg(D21["hit@1"])}</b><span>de hit@1, las tres juntas</span>
    <p>Solos rinden parecido: <b>se equivocan en cosas distintas</b>.</p></div>
</div>''', "rag.hybrid", "bm25 + siglip2", "La búsqueda pasa a ser <mark>híbrida</mark>: densa + léxica + foto. Es la "
          "<b>versión 2</b>.",
          [f"Solos, los tres rinden parecido: {f3(HIB[V1]['hit@1'])}, {f3(HIB[HK['lexica']]['hit@1'])} y "
           f"{f3(HIB[HK['foto']]['hit@1'])}. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. "
           f"Pero se equivocan en cosas distintas: fusionados dan {f3(HIB[V2]['hit@1'])}, {sg(D21['hit@1'])} de hit@1, con un "
           f"intervalo que no toca el cero; y {sg(D21['hit@5'])} de hit@5. Y contra la foto, la frase sin reescribir da "
           f"{f3(_s_piece['hit@1'])}, casi como la ficha, {f3(_s_full['hit@1'])}: la foto no necesita que la consulta hable "
           "como el catálogo.",
           "Decisión: la búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4."], 40)

# =============================================================================================
# El camino incremental: un cambio por paso (y, aparte, lo que da un VLM eligiendo)
# =============================================================================================
PASOS = [  # (método, etiqueta, paso en que aparece)
    (K_NAIVE, "RAG naive", 0),
    (K_DESC, "+ descripción desde la foto", 1),
    (K_FICHA, "+ consulta como ficha (HyDE)", 1),
    (V1, "+ filtro por kind: versión 1", 2),
    (V1 + "|+bm25", "+ léxica (BM25)", 3),
    (V2, "+ foto (SigLIP 2): versión 2", 3),
]
_r_opus = RR[BASE + "|rerank-opus"]
APARTE = [("un VLM elige entre los 5 primeros", CURVA["por_k"]["5"]["acierto_eleccion"]),
          ("un VLM reordena los 10 primeros", _r_opus["hit@1"])]


def _lineas(et: str, ancho: int = 18) -> list[str]:
    out, cur = [], ""
    for w_ in et.split(" "):
        if cur and len(cur) + 1 + len(w_) > ancho:
            out.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    return out + [cur]


def _camino_svg():
    W, H = 1728, 760
    x0, bw, paso_x = 96, 150, 207
    base, top = 610, 110
    sy = lambda v: base - (base - top) * v / 0.8  # noqa: E731
    o = [f'<svg class="graf-l camino" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    for t in (0, 0.2, 0.4, 0.6, 0.8):
        o.append(f'<line x1="{x0 - 20}" y1="{sy(t)}" x2="{W}" y2="{sy(t)}" class="gl-grilla"/>'
                 f'<text x="{x0 - 34}" y="{sy(t) + 6}" class="gl-eje" text-anchor="end">{f2(t)}</text>')
    prev = None
    for i, (key, et, paso) in enumerate(PASOS):
        x, r = x0 + i * paso_x, CAM[key]
        v = r["hit@1"]
        cl = " gana" if key == V2 else (" v1" if key == V1 else "")
        o.append(f'<g class="cm-b{cl}" data-paso="{paso}">')
        if prev is not None:
            o.append(f'<line x1="{x - paso_x + bw}" y1="{sy(prev)}" x2="{x}" y2="{sy(prev)}" class="cm-guia"/>')
        o.append(f'<rect x="{x}" y="{sy(v):.1f}" width="{bw}" height="{sy(0) - sy(v):.1f}" rx="3"/>')
        lo, hi = r["hit@1_ic95"]
        o.append(f'<path class="cm-ic" d="M{x + bw / 2} {sy(lo):.1f}V{sy(hi):.1f}M{x + bw / 2 - 9} {sy(lo):.1f}h18M{x + bw / 2 - 9} {sy(hi):.1f}h18"/>')
        o.append(f'<text x="{x + bw / 2}" y="{sy(hi) - 14:.1f}" class="cm-v" text-anchor="middle">{f2(v)}</text>')
        if "vs_anterior" in r:
            d = r["vs_anterior"]
            sube = d["hit@1_ic95"][0] > 0
            o.append(f'<text x="{x + bw / 2}" y="{sy(hi) - 62:.1f}" class="cm-d{" sube" if sube else ""}" text-anchor="middle">{dif(d)}</text>')
        o.append(f'<text x="{x + bw / 2}" y="{sy(0) - 12}" class="cm-h5" text-anchor="middle">hit@5 {f2(r["hit@5"])}</text>')
        for j, ln in enumerate(_lineas(et)):
            o.append(f'<text x="{x + bw / 2}" y="{sy(0) + 34 + j * 25}" class="cm-et" text-anchor="middle">{ln}</text>')
        o.append("</g>")
        prev = v
    # aparte: una técnica aislada, no un paso del flujo
    xa = x0 + len(PASOS) * paso_x + 30
    o.append(f'<g class="cm-ap" data-paso="4"><line x1="{xa - 34}" y1="{top - 40}" x2="{xa - 34}" y2="{sy(0) + 90}" class="cm-sep"/>'
             f'<text x="{xa - 14}" y="{top - 52}" class="cm-apt">aparte · técnicas aisladas,</text>'
             f'<text x="{xa - 14}" y="{top - 28}" class="cm-apt">no pasos del flujo</text>')
    for j, (et, v) in enumerate(APARTE):
        x = xa + j * 182
        o.append(f'<rect x="{x}" y="{sy(v):.1f}" width="{bw}" height="{sy(0) - sy(v):.1f}" rx="3"/>'
                 f'<text x="{x + bw / 2}" y="{sy(v) - 14:.1f}" class="cm-v" text-anchor="middle">{f3(v)}</text>')
        for jj, ln in enumerate(_lineas(et)):
            o.append(f'<text x="{x + bw / 2}" y="{sy(0) + 34 + jj * 25}" class="cm-et" text-anchor="middle">{ln}</text>')
    o.append("</g></svg>")
    return "".join(o)


_d_desc, _d_hyde, _d_kind = CAM[K_DESC]["vs_anterior"], CAM[K_FICHA]["vs_anterior"], CAM[V1]["vs_anterior"]
lam("camino", "El camino incremental", "Experimentos", f'''
{kick("E", "experimentos · la ablación incremental")}
<h2 class="t chico">El camino: de {f2(_n1["hit@1"])} a <em>{f2(B2["hit@1"])}</em> de hit@1, un cambio por paso</h2>
<div class="camino-w">{_camino_svg()}</div>''',
    [f"La ablación incremental: un cambio por paso, con su diferencia pareada, sobre las {N_ANS} consultas. Arrancamos del RAG "
     f"naive, el texto del vendedor y la consulta sin reescribir: {f2(_n1['hit@1'])}.",
     f"Describir cada producto desde su foto lo lleva a {f2(_n2['hit@1'])}; escribir la consulta como una ficha, a "
     f"{f2(CAM[K_FICHA]['hit@1'])}. Esos dos pasos son los que más pesan.",
     "El filtro por kind no suma en este set de evaluación: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la "
     "versión 1 del flujo.",
     f"Con la búsqueda léxica, {f2(CAM[V1 + '|+bm25']['hit@1'])}; con la foto, {f2(B2['hit@1'])}: la versión 2.",
     f"Aparte queda el {f2(_r_opus['hit@1'])} que mostrábamos antes: es un VLM reordenando el top-10, una técnica aislada, no "
     "un escalón del flujo."],
    35, clase="clara")

# =============================================================================================
# 4 · ¿Error, o el mismo mueble en otro color? Tres niveles de correcto
# =============================================================================================
_e_q = EMB[V1]
_frac_var = (_e_q["familia_hit@1"] - _e_q["hit@1"]) / (1 - _e_q["hit@1"])
_fam = {k: EMB[f"{k}|description|filtro-kind"]["vs_base"] for k in ("bm25", "siglip2", "bge")}
assert _fam["bm25"]["familia_hit@1_ic95"][0] < 0 < _fam["bm25"]["familia_hit@1_ic95"][1] and _fam["bge"]["familia_hit@1_ic95"][1] < 0, \
    "por familia cambió el orden entre buscadores: revisar el texto del experimento 4"
unica(4, "¿Error, o una variante?", "Si el primero no es el anotado, <em>¿se equivocó?</em>",
      f"El {round(100 * DOC['con_variantes'])}% de las consultas busca un producto que tiene variantes.",
      [("A", "Exacto", ""), ("B", "El mismo modelo", ""),
       ("C", "Sirve, según un juez", f"lo probamos: al anotado le dice «sirve» el {pct(G_ANOT2)}; a otros candidatos, el {pct(G_OTROS2)}")],
      barras([dict(letra="A", et="El producto exacto", v=_e_q["hit@1"], ic=_e_q["hit@1_ic95"]),
              dict(letra="B", et="El mismo modelo", v=_e_q["familia_hit@1"], ic=_e_q["familia_hit@1_ic95"]),
              dict(letra="C", et="Sirve, según un juez", v=UTIL1, gana=True)],
             titulo="el primer candidato es…", paso=2, gana_paso=3, cls="gb-unica")
      + f'''<div class="fam-ej"><figure>{producto(FAM_REL, 96)}<figcaption>el anotado</figcaption></figure>
      <figure>{producto(FAM_TOP, 96)}<figcaption>salió primero</figcaption></figure>
      <p>El mismo modelo, en otro color: <b>1 de cada {round(1 / _frac_var)}</b> «errores».</p></div>''',
      "correcto", "tres niveles", "El exacto <mark>subestima el nivel, no el orden</mark>: sirve para comparar.",
      ["hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que "
       "cuenta como error es el mismo mueble en otro color?",
       "Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez. "
       f"Al juez lo probamos con las anotaciones: al producto anotado le dice que sirve el {round(100 * G_ANOT2)} por ciento de "
       f"las veces, y a los otros candidatos, el {round(100 * G_OTROS2)}.",
       f"El exacto, {f2(_e_q['hit@1'])}; el mismo modelo, {f2(_e_q['familia_hit@1'])}; uno que sirve, {f2(UTIL1)}. Una de cada "
       f"{round(1 / _frac_var)} veces que el primero falla es otra variante del mismo mueble, como esta alfombra.",
       "El exacto subestima el nivel, no el orden: sirve para comparar, y los tres juntos dicen cuánto sirve."],
      40, rotulo="conclusión")

# =============================================================================================
# 5 · Elegir con un VLM, y cuántos candidatos
# =============================================================================================
_r0 = RR[BASE]
_d_opus = paired(RR_DIR, BASE + "|rerank-opus", BASE)
_ks = sorted(int(k) for k in CURVA["por_k"])
_ele = [CURVA["por_k"][str(k)]["acierto_eleccion"] for k in _ks]
_tech = [CURVA["por_k"][str(k)]["techo_hit@k"] for k in _ks]
_d35 = CURVA["diferencias_pareadas"]["3->5"]
_c = {k: CURVA["por_k"][str(k)]["acierto_eleccion"] for k in (3, 5, 8)}
_dh = DIAG["hibrida"]
_e5_chart = lineas_svg(_ks, [dict(ys=_tech, clase="punt", et="techo (hit@k)", et_dy=-16),
                             dict(ys=_ele, clase="sol", et="lo que elegiría el VLM", et_dy=-4)], 1100, 520, 0.5, 0.92,
                       [0.5, 0.6, 0.7, 0.8, 0.9], xlab="k: candidatos por pieza", mr=250, yfmt=f2,
                       marcas=[(3, _c[3], f"k = 3: {f3(_c[3])}", 0, 46, "middle", False),
                               (5, _c[5], f"k = 5: {f3(_c[5])}", 0, 46, "middle", True),
                               (8, _c[8], f"k = 8: {f3(_c[8])}", 0, 46, "middle", False)])
pregunta(5, "Elegir con un VLM, y cuántos", "¿Un VLM que mira las fotos <em>ordena mejor que la búsqueda</em>? ¿Y cuántos candidatos pasarle?",
         f"hit@10 es {f2(_r0['hit@10'])} pero hit@1 {f2(_r0['hit@1'])}: el correcto suele estar, pero no primero.",
         [("A", "Un VLM reordena el top-10 mirando las fotos", ""), ("k", "De 1 a 10 candidatos", "")],
         [f"hit@10 es {f2(_r0['hit@10'])} pero hit@1 {f2(_r0['hit@1'])}: el correcto casi siempre está entre los diez primeros, "
          "pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar?",
          "Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera "
          "entre los primeros k, ¿acertaría? La punteada es el techo."],
         30, extra='<p class="adv">Advanced RAG · reranking con un VLM</p>')
resultado(5, "Elegir con un VLM, y cuántos candidatos", f'''
<div class="r-5">
  <div class="r5-izq">
    <span class="et">hit@1, reordenando el top-10</span>
    <div class="r5-num"><span>{f3(_r0["hit@1"])}</span><i>→</i><b>{f3(_r_opus["hit@1"])}</b></div>
    <p class="r5-d">{nb(dif(_d_opus))}, pareado</p>
  </div>
  <div>{_e5_chart}</div>
</div>''', "candidatos", str(K), f"{K} candidatos por pieza (antes 3). El reranker es una <mark>técnica aislada</mark>: "
          "no ve el ambiente.",
          [f"Reordenando el top-10, hit@1 pasa de {f3(_r0['hit@1'])} a {f3(_r_opus['hit@1'])}. De 3 a 5 candidatos la elección "
           f"sube {round(100 * _d35['acierto_eleccion'])} puntos, también significativo; a partir de 8 se aplana. En los "
           f"ambientes reales, el {round(100 * _dh['elegido_en_puestos_4_y_5'])} por ciento de lo elegido salió de los puestos 4 y 5.",
           "Decisión: cinco candidatos por pieza. Ojo: es una técnica aislada, no un paso del flujo. Ese reranker ordena "
           "contra la consulta, sin ver el ambiente; el que elige arma un conjunto para el cuarto, y no tiene ground "
           "truth."], 40)


# =============================================================================================
# Piezas de las láminas con juez: los votos por ambiente y el marcador
# =============================================================================================
def _tiles(res, b_lbl):
    out = []
    for r in res["rows"]:
        nombre, estilo = ESTILO.get(r["slug"], (r["slug"], ""))
        g = r["ganador"]
        if g == res["lado_a"]:
            cls, lbl = "t-a", "IKEA"
        elif g == res["lado_b"]:
            cls, lbl = "t-b", b_lbl
        else:
            cls, lbl = "t-e", "empate"
        out.append(f'<div class="tj {cls}"><b>{nombre}</b><span>{estilo}</span><em>{lbl}</em></div>')
    return f'<div class="tiles">{"".join(out)}</div>'


def _marcador(a_lbl, a, b, b_lbl, sub):
    return (f'<div class="marcador"><div class="mk-t"><span>{a_lbl}</span><b>{a}</b><i>–</i><b>{b}</b><span>{b_lbl}</span></div>'
            f'<div class="mk-s">{sub}</div></div>')



# =============================================================================================
# 6 · Con búsqueda, con 5 al azar, o con el catálogo entero en el prompt: ¿hacía falta RAG?
# =============================================================================================
_sa = JA["resumen"]
_mil_fichas = miles(D["prod_todos"])
pregunta(6, "Con búsqueda o sin búsqueda", "¿La búsqueda aporta en la tarea real? ¿Y hacía falta, <em>si el catálogo entra en el contexto</em>?",
         "",
         [("A", f"Con búsqueda: los {K} mejores", ""), ("B", f"{K} al azar del mismo kind", ""),
          ("C", "El catálogo entero en el prompt", "")],
         ["Dos extremos. Uno: darle al que elige cinco productos al azar del kind "
          "pedido; es el control del juez, porque si no distinguiera esas dos listas, ninguna comparación de punta a "
          "punta diría nada. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?",
          f"Mismo plan, mismo modelo que elige, mismo juez, en los dos órdenes. Contra el azar, en {J_AZAR['n']} ambientes. "
          f"Contra el catálogo entero en el prompt, las {_mil_fichas} fichas en texto, en los {J_CTX['n']}."], 35)
resultado(6, "Con búsqueda, al azar, o con el catálogo entero", f'''
<div class="r-7 r7n">
  <div>
    <span class="et r7-et">contra {K} al azar · {J_AZAR["n"]} ambientes</span>
    {_marcador("Con búsqueda", J_AZAR["a"], J_AZAR["b"], f"{K} al azar", f"test de signos, p = {f3(P_AZAR)}")}
    {barras([dict(letra="A", et="Con búsqueda", v=J_AZAR["util_a"], gana=True), dict(letra="B", et=f"{K} al azar", v=J_AZAR["util_b"])],
            titulo="productos útiles", cls="gb-compacto r7-b")}
  </div>
  <div data-paso="1">
    <span class="et r7-et">contra el catálogo entero en el prompt · {J_CTX["n"]} ambientes</span>
    {_marcador("Con búsqueda", J_CTX["a"], J_CTX["b"], "Catálogo entero", f"y {J_CTX['emp']} empate · con búsqueda: la versión 2")}
    {barras([dict(letra="A", et="Con búsqueda", v=J_CTX["util_a"]), dict(letra="C", et="Catálogo entero", v=J_CTX["util_b"])],
            titulo="productos útiles", cls="gb-compacto r7-b")}
  </div>
</div>''', "la búsqueda", "se queda", "Cuando el que elige puede leer todo, <mark>empata</mark>: RAG se queda porque escala.",
          [f"Contra el azar, {J_AZAR['a']} a {J_AZAR['b']}, en los dos órdenes: los "
           f"productos útiles pasan de {f2(J_AZAR['util_b'])} a {f2(J_AZAR['util_a'])}. Contra el catálogo entero, {J_CTX['a']} a {J_CTX['b']}, con los mismos productos útiles: empatan.",
           "Por calidad, a esta escala, no hacía falta."],
          50)

# =============================================================================================
# 6 · por qué RAG si empata: tokens y costo del paso que elige (los mismos 11 ambientes)
# =============================================================================================
import datos as _dt  # noqa: E402

_tok_rg = sorted(_dt._entrada(c) for c in _dt._rg)
_tok_cx = statistics.median(_dt._entrada(c) for c in _dt._cx)
_cache_w = CTX_TOKENS * _dt._opus["cache_write_5m"] / 1e6
_mt = lambda n: f"{round(n / 1000)} mil"  # noqa: E731
assert _tok_cx > 10 * statistics.median(_tok_rg) and _dt.C_CTX_SIN > 5 * _dt.C_CHOOSE_V2
lam("e6c", "Exp. 6: tokens y costo", "Experimentos · 6", f'''
{kick("E6", "experimento 6 · por qué RAG")}
<h2 class="t chico">Tokens y costo</h2>
{minimapa(6)}
<div class="res-cuerpo"><div class="e6c">
  <div><div>
    <span class="et r7-et">tokens de entrada por pedido · el paso que elige</span>
    {barras([dict(letra="A", et="Con búsqueda", sub=f"{round(_tok_rg[0] / 1000)} a {_mt(_tok_rg[-1])}: las fotos",
                  v=statistics.median(_tok_rg), vtxt=_mt(statistics.median(_tok_rg)), gana=True),
             dict(letra="C", et="Catálogo entero", sub=f"{miles(D['prod_todos'])} productos", v=_tok_cx, vtxt=_mt(_tok_cx))],
            xmax=DOC["contexto"], ticks=(0, 250_000, 500_000, 750_000, 1_000_000), cls="gb-compacto e6c-b",
            tick_fmt=lambda x: "0" if x == 0 else ("1 millón" if x == 1_000_000 else _mt(x)))}
    </div><p class="e6c-n">El borde es el contexto de Opus: <b>con el triple de productos, no entra</b>. Con búsqueda, el pedido ocupa lo
      mismo con {miles(D['prod_todos'])} o con {miles(DOC['abo_listados'])} productos.</p>
  </div>
  <div data-paso="1"><div>
    <span class="et r7-et">costo por pedido · una llamada a Opus, la que elige</span>
    {barras([dict(letra="A", et="Con búsqueda", v=_dt.C_CHOOSE_V2, vtxt=usd(_dt.C_CHOOSE_V2, 3)),
             dict(letra="C", et="Catálogo, sin caché", v=_dt.C_CTX_SIN, vtxt=usd(_dt.C_CTX_SIN)),
             dict(letra="C", et="Catálogo, con caché", sub="otro pedido antes de 5 min", v=_dt.C_CTX_CACHE,
                  vtxt=usd(_dt.C_CTX_CACHE, 3))],
            xmax=1.5, ticks=(0, 0.5, 1.0, 1.5), cls="gb-compacto e6c-b", paso=1, gana_paso=1,
            tick_fmt=lambda x: "0" if x == 0 else usd(x, 1))}
    </div><p class="e6c-n">Con búsqueda, elegir es <b>la mitad del pedido entero</b> ({usd(C_PEDIDO)}, con el plan y la imagen).
      La caché dura 5 minutos: escribirla cuesta {usd(_cache_w)}, y un cambio de stock la invalida.</p>
  </div>
</div></div>''',
    [f"¿Por qué RAG, entonces? Con búsqueda, el que elige recibe unos {_mt(statistics.median(_tok_rg))} tokens; con el "
     f"catálogo entero, {_mt(_tok_cx)}, un tercio del contexto: con el triple de productos no entra.",
     f"Elegir es una sola llamada a Opus: con búsqueda, {usd(_dt.C_CHOOSE_V2)}, la mitad del pedido entero. Con el catálogo "
     f"sin caché, {usd(_dt.C_CTX_SIN)}; la caché del proveedor lo baja a {usd(_dt.C_CTX_CACHE)}, pero dura cinco minutos.",
     "Depende del caso. Con poco tráfico, o con un catálogo mucho más grande, conviene RAG, y por eso lo elegimos. Con un "
     "catálogo de este tamaño y muchos pedidos seguidos, el catálogo en caché saldría apenas más barato."],
    45, clase="clara")

# =============================================================================================
# 7 · Tres redactores
# =============================================================================================
_v1s = [CAM[V1]["hit@1"]] + [h[V1]["hit@1"] for h in HIB_R]
_v2s = [CAM[V2]["hit@1"]] + [h[V2]["hit@1"] for h in HIB_R]
_difs_r = [D21] + [h[V2]["vs_base"] for h in HIB_R]
assert all(d["hit@1_ic95"][0] > 0 for d in _difs_r), "la mejora de la híbrida ya no se repite con los tres redactores"


def _rep_svg():
    W, x0, x1, lo, hi = 944, 250, 900, 0.48, 0.64
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)  # noqa: E731
    o = [f'<svg class="graf-l rep" viewBox="0 0 {W} 300" width="{W}" height="300">']
    for t in (0.50, 0.55, 0.60):
        o.append(f'<line x1="{sx(t)}" y1="30" x2="{sx(t)}" y2="238" class="gl-grilla"/>'
                 f'<text x="{sx(t)}" y="268" class="gl-eje" text-anchor="middle">{f2(t)}</text>')
    o.append(f'<text x="{x1}" y="296" class="gl-xlab" text-anchor="end">hit@1 de cada redactor</text>')
    for j, (et, sub, xs, gana) in enumerate((("Versión 1", "densa", _v1s, False), ("Versión 2", "híbrida", _v2s, True))):
        y = 86 + j * 104
        mu, sd = statistics.mean(xs), statistics.stdev(xs)
        o.append(f'<g class="rep-f{" gana" if gana else ""}"><text x="0" y="{y - 2}" class="rep-et">{et}</text><text x="0" y="{y + 24}" class="gl-eje">{sub}</text>'
                 f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" class="gl-grilla"/>'
                 f'<rect x="{sx(mu - sd):.1f}" y="{y - 22}" width="{sx(mu + sd) - sx(mu - sd):.1f}" height="44" class="gl-banda"/>'
                 + "".join(f'<circle cx="{sx(v):.1f}" cy="{y}" r="11" class="rep-p"/>' for v in xs)
                 + f'<text x="{sx(mu):.1f}" y="{y - 34}" class="rep-t" text-anchor="middle">{media_desvio(xs)}</text></g>')
    o.append("</svg>")
    return "".join(o)


unica(7, "Tres redactores", "¿Cuánto cambia el número <em>según quién escribe las consultas</em>?",
      "Las consultas las escribió un modelo: ¿medimos al redactor o al sistema?",
      [("A", "Tres redactores independientes", ""), ("B", "Versión 1 y versión 2 en cada uno", "")],
      _rep_svg() + f'<p class="nota chica">La mejora de la híbrida, en los tres: '
                   f'{" · ".join(sg(d["hit@1"]) for d in _difs_r)}.</p>',
      "ruido", f"± {f1(100 * statistics.stdev(_v1s))} puntos", f"El número se mueve ±{f1(100 * statistics.stdev(_v1s))} "
      "puntos sin cambiar el sistema: <mark>2 puntos no son señal</mark>.",
      ["Las consultas de evaluación las escribió un modelo. Por eso, promedio y desvío: ¿cuánto cambia el número sin "
       "cambiar el sistema?",
       "Las mismas consultas, escritas otras dos veces por subagentes independientes.",
       f"La versión 1 da {media_desvio(_v1s)}; la versión 2, {media_desvio(_v2s)}. La mejora de la híbrida se repite con los "
       "tres.",
       "El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos. Los "
       "embedders no se distinguen; la híbrida sí."],
      30, rotulo="conclusión")

# =============================================================================================
# 8 · Buscar por imagen: que un generador amueble primero, recortar cada mueble y buscarlo por su
# foto. Se midió el buscador (DINOv3 sobre el recorte) contra el de texto, con el mismo ground truth;
# el flujo entero por imagen no se corrió.
# =============================================================================================
from PIL import Image  # noqa: E402

_room8 = Image.open(ROOT / GT_ROOM_PATH)
_bx8 = [round(v) for v in V0_REC["box"]]
_W8 = 300
_s8 = _W8 / _room8.width
_caja8 = (f"left:{_bx8[0] * _s8:.0f}px;top:{_bx8[1] * _s8:.0f}px;width:{(_bx8[2] - _bx8[0]) * _s8:.0f}px;"
          f"height:{(_bx8[3] - _bx8[1]) * _s8:.0f}px")
unica(8, "Buscar por imagen", "¿Y si un generador <em>amuebla primero</em>, y buscamos cada mueble por su foto?",
      "La idea: un generador de imágenes sabe elegir, combinar y ubicar muebles.",
      [("A", "Por texto: la descripción", ""), ("B", "Por imagen: el recorte de cada mueble", "")],
      f'''<span class="et">por imagen: el recorte, contra las fotos del catálogo (DINOv3)</span>
<div class="dz-v0 e8-v0">
  <div class="v-foto">{foto("e8-room", GT_ROOM_PATH, _W8, round(_room8.height * _s8))}<div class="v-caja" style="{_caja8}"></div></div>
  <span class="v-fl">→</span>{foto("e8-crop", _room8.crop(_bx8), 210, 104, modo="fit", q=82)}<span class="v-fl">→</span>{producto(V0_SOFA_OK, 120)}
</div>'''
      + barras([dict(letra="B", et="Por imagen", v=VT["imagen"]),
                dict(letra="A", et="Por texto", v=VT["texto"], gana=True, nota=f'{sg(VT["dif"], 2)} {ic_txt(*VT["ic"], nd=2)}')],
               titulo=f"hit@1 · los mismos {VT['n']} productos anotados", paso=2, gana_paso=3, cls="gb-unica e8-b"),
      "se busca", "por texto", "Aun recortando muebles reales, <mark>la imagen pierde</mark>.",
      ["Otra arquitectura, como experimento: un generador de imágenes sabe elegir, combinar y ubicar muebles; que amueble "
       "primero la foto, y buscar cada mueble recortado en el catálogo, por imagen.",
       "Comparamos los dos buscadores con el mismo ground truth: la descripción contra el recorte de cada mueble.",
       f"Por imagen encuentra primero el {round(100 * VT['imagen'])} por ciento de los productos anotados; por texto, el "
       f"{round(100 * VT['texto'])}. Y es el mejor caso para la imagen: los recortes salen de fotos reales; con un "
       "generador, los muebles serían genéricos.",
       "Nos quedamos con el texto. Ojo: el flujo entero por imagen no lo corrimos; lo que el generador elegiría y dónde lo "
       "ubicaría no lo medimos."],
      45)


# =============================================================================================
# De trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta en una línea
# =============================================================================================
def _emb(k: str) -> dict:
    return EMB[f"{k}|description|filtro-kind"]


ETAPA_TXT.update({9: "índice", 10: "índice", 11: "índice", 12: "índice", 13: "búsqueda", 14: "búsqueda", 15: "escena"})


def _b(letra, et, r, k="hit@1", gana=False):
    return dict(letra=letra, et=et, v=r[k], ic=r.get(k + "_ic95"), gana=gana, vtxt=f3(r[k]))


def _gb(filas, titulo="hit@1"):
    return barras(filas, titulo=titulo, paso=2, gana_paso=3, cls="gb-unica")


_dims = {d: (F[f"{BASE}|dim-{d}"] if d != 1024 else F[BASE]) for d in (32, 128, 512, 1024)}
_doc, _chunk, _alin = F[BASE], F[BASE + "|chunks-lines-max"], F[BASE + "|chunks-lines-aligned"]
_ex_a, _ex_b = rankings(ABL_DIR)[BASE + "|exact"], rankings(ABL_DIR)[BASE]
_iguales = sum(x["ranked"] == y["ranked"] for x, y in zip(_ex_a, _ex_b, strict=True))
_f_none, _f_type = HIB["qwen3|description|filtro-none"], HIB[BASE]
_mini, _qrr = F[BASE + "|rerank-minilm-reranker"], RLOC[BASE + "|rerank-qwen3-reranker"]

# 9 · embedder
unica(9, "Embedder", "Embedder", "",
      [("A", "Hashing de palabras", ""), ("B", "BM25", ""), ("C", "BGE-base", ""), ("D", "Qwen3-Embedding", "")],
      _gb([_b("A", "Hashing", _emb("hashing")), _b("B", "BM25", _emb("bm25")), _b("C", "BGE", _emb("bge")),
           _b("D", "Qwen3", EMB[V1], gana=True)]),
      "", "", "",
      ["¿Importa el embedder? Cuatro, de contar palabras a Qwen3.",
       "Qwen3 solo se distingue de BGE; contra contar palabras no, por el molde compartido. Queda Qwen3."], 15)

# 10 · dimensión
unica(10, "Dimensión del vector", "Dimensión del embedding", "",
      [("A", "32", ""), ("B", "128", ""), ("C", "512", ""), ("D", "1024: el vector entero", "")],
      _gb([_b(l, str(d), r, gana=d == 1024) for l, (d, r) in zip("ABCD", _dims.items(), strict=True)]),
      "", "", "",
      ["Qwen3 deja recortar el vector, Matryoshka: probamos de 32 a 1024 dimensiones.",
       "Con 512 da lo mismo; con este catálogo la memoria no pesa, y queda 1024."], 15)

# 11 · splitting
unica(11, "Splitting y líneas", "Chunk size", "",
      [("A", "Un documento por producto", ""), ("B", "Un chunk por línea", ""),
       ("C", "Línea contra línea", "cada línea de la consulta, contra la misma línea del producto")],
      _gb([_b("A", "Un documento", _doc, gana=True), _b("B", "Un chunk por línea", _chunk), _b("C", "Línea contra línea", _alin)]),
      "", "", "",
      ["¿Partir la descripción en pedazos?",
       "No: las líneas solas pierden el contexto del producto. Un documento por producto."], 15)

# 12 · base vectorial
unica(12, "Base vectorial", "¿ChromaDB <em>pierde algo</em> contra la búsqueda exacta?", "",
      [("A", "ChromaDB", "HNSW: aproximada"), ("B", "Búsqueda exacta", "el coseno contra todos")],
      _gb([_b("A", "ChromaDB", F[BASE], gana=True), _b("B", "Exacta", F[BASE + "|exact"])])
      + f'<p class="un-nota">El mismo top-10 en <b>{_iguales} de {len(_ex_a)}</b> consultas.</p>',
      "", "", "",
      ["ChromaDB busca con un índice aproximado. ¿Pierde algo contra comparar con todos?",
       f"Nada: el mismo top-10 en las {len(_ex_a)} consultas. La usamos porque persiste y escala."], 15)

# 13 · filtros
unica(13, "Filtros de metadata", "Filtros por metadata", "",
      [("A", "Ninguno", ""), ("B", "Por tipo", "la línea Type"), ("C", "Por kind", "la categoría")],
      _gb([_b("A", "Ninguno", _f_none, "hit@5"), _b("B", "Por tipo", _f_type, "hit@5"), _b("C", "Por kind", B1, "hit@5", gana=True)],
          titulo="hit@5")
      + f'<p class="un-nota">Sin el de kind, en los pedidos reales el <b>{round(100 * DOC["otro_kind"])}%</b> de los candidatos '
        "sería de otra categoría.</p>",
      "", "", "",
      ["¿Suman los filtros? En el set de evaluación, no.",
       f"Usamos el de kind igual: en los pedidos reales, sin él, el {round(100 * DOC['otro_kind'])} por ciento de los "
       "candidatos sería de otra categoría."], 15)

# 14 · rerankers de texto
unica(14, "Rerankers de texto", "¿Un <em>reranker de texto</em> ordena mejor?", "",
      [("A", "Sin reranker", ""), ("B", "MiniLM", "cross-encoder"), ("C", "Qwen3-Reranker", "")],
      _gb([_b("A", "Sin reranker", RLOC[BASE], gana=True), _b("B", "MiniLM", _mini), _b("C", "Qwen3-Reranker", _qrr)]),
      "", "", "",
      ["¿Un reranker de texto ordena mejor?",
       "No: los dos empeoran, porque releen el texto que ya usó la búsqueda. El que suma mira las fotos: el experimento 5."], 15)

# 15 · la escena
unica(15, "La escena", "¿El prompt de la imagen, <em>una plantilla</em> o escrito por el LLM?", "",
      [("A", "Una plantilla", "sin llamada"), ("B", "Escrito por el LLM", "una llamada más")],
      _gb([dict(letra="A", et="Plantilla", sub=f'{IMG_PL["identificados"]} de {IMG_PL["productos"]}', gana=True,
                v=IMG_PL["identificados"] / IMG_PL["productos"]),
           dict(letra="B", et="Escrito por el LLM", sub=f'{IMG_LLM["identificados"]} de {IMG_LLM["productos"]}',
                v=IMG_LLM["identificados"] / IMG_LLM["productos"])],
          titulo=f"productos reconocidos en la imagen · los {IMG_PL['corridas']} ambientes")
      + f'<p class="un-nota">Diferencia por ambiente: IC 95% <b>{ic_txt(*DOC["escena_ic"], nd=2)}</b>: empatan.</p>',
      "", "", "",
      ["El prompt de la imagen: ¿una plantilla, o que lo escriba el LLM?",
       "Empatan, y la plantilla ahorra una llamada: queda la plantilla."], 15)

