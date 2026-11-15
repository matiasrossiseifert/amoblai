"""Los experimentos, por el ranking de la revisión del 2026-11-12 (docs/REVISION.md, sección 4).
Ocho con lámina propia: una lámina oscura con la pregunta (por qué y qué se comparó, con la etapa
encendida en el flujo) y una clara con los resultados, la diferencia pareada y la decisión (el
talón); el 4 y el 8, que miden al banco de prueba, van en una sola lámina. En el medio, el camino
incremental que resume los tres primeros. Y al final, juntos en dos láminas, los siete de trámite:
lo que la cátedra dijo que iba a preguntar, con la respuesta en una línea (y la escena, que se
midió en los 11 ambientes y empató)."""

from __future__ import annotations

import statistics

from datos import (ABL_DIR, B1, B2, BASE, C268, C855, C_CHOOSE_V2, C_CTX_CACHE, C_CTX_SIN, C_DESC, CTX_EN_TOP5, CTX_PIEZAS, C_RERANK, C_SCENE, CTX_TOKENS, ESC_DIF,
                   IMG_LLM, IMG_PL, J_CTX, CAM, CON, CREV, CTOD, CURVA, D,
                   D21, DIAG, DOC, EMB, ESTILO, F, FAM_R, FAM_REL, FAM_TOP, FRASES, G_N, HIB, HIB_R, ITEMS, J_AZAR, JA, K, LIN, N_ANS, P_AZAR, RLOC, RR, RR_DIR, TODOS_DIR, UTIL1, V1, V2, dif, esc,
                   f1, f2, f3, ic_txt, media_desvio, miles, nb, paired, pct, rankings, sg, usd, FM)
from piezas import ETAPA_EXP, barras, flujo, kick, lineas_svg, minimapa, producto, talon, variantes_html
from registro import lam

ETAPA_TXT = {1: "descripción", 2: "plan", 3: "búsqueda", 4: "el banco de la búsqueda", 5: "búsqueda y elección",
             6: "búsqueda", 7: "el banco de la búsqueda"}


def pregunta(n, tema, titulo, porque, variantes, metrica, notas, seg, extra="", ancho_t="", cls="", fuera=""):
    """Lámina oscura: el porqué (paso 0) y qué se comparó (paso 1), con el flujo a la derecha.
    variantes: lista de (letra, nombre, detalle), o el HTML ya armado. fuera: HTML suelto en la lámina."""
    vs = variantes if isinstance(variantes, str) else variantes_html(variantes)
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
<div class="izq {cls}">
  {kick(f"E{n}", f"experimento {n} · {ETAPA_TXT[n]}")}
  <h2 class="t chico {ancho_t}">{titulo}</h2>
  <p class="porque">{porque}</p>
  {extra}
  <div class="exp-blq" data-paso="1">
    <span class="et">qué se comparó</span>
    {vs}
    <p class="metrica">{metrica}</p>
  </div>
</div>
<div class="esq">{flujo(pines=[n])}</div>{fuera}''', notas, seg, focos=[" ".join(ETAPA_EXP[n])])


def resultado(n, tema, cuerpo, clave, valor, decision, notas, seg, paso_dec=2, rotulo="decisión"):
    lam(f"e{n}r", f"Exp. {n}: resultados", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · resultados")}
<h2 class="t chico">{tema}</h2>
{minimapa(n)}
{cuerpo}
{talon(clave, valor, decision, paso=paso_dec, rotulo=rotulo)}''', notas, seg, clase="clara")


def unica(n, tema, titulo, porque, variantes, metrica, res_html, clave, valor, decision, notas, seg, rotulo="decisión"):
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
    <p class="metrica">{metrica}</p>
  </div>
</div>
<div class="un-der" data-paso="2">{res_html}</div>
{talon(clave, valor, decision, paso=3, rotulo=rotulo)}''', notas, seg, clase="clara unica")


# =============================================================================================
# 1 · Qué se indexa
# =============================================================================================
K_NAIVE, K_DESC, K_FICHA = "qwen3|seller-full|filtro-none|consulta-piece", "qwen3|description|filtro-none|consulta-piece", "qwen3|description|filtro-none"
_n1, _n2 = CAM[K_NAIVE], CAM[K_DESC]
_d_idx = _n2["vs_anterior"]
_d_ficha = paired(ABL_DIR, "qwen3|description|filtro-none", "qwen3|seller|filtro-none")  # lo mismo, con la consulta escrita como ficha
_d_name = paired(ABL_DIR, "qwen3|name+description|filtro-kind", V1)
_nol = ITEMS["102.335.32"]
pregunta(1, "Qué se indexa", "¿Alcanza con el texto del vendedor, o hay que <em>describir cada producto mirando su foto</em>?",
         "Nadie pide como escribe el vendedor: se pide estilo, color y materiales, y todo eso está en la foto, no en el texto. "
         "Describir cada producto con un VLM es un costo que se paga una sola vez.",
         [("A", "El texto del vendedor", "nombre, su tipo («Easy chair»), colores y la frase de marketing"),
          ("B", "La descripción desde la foto", "las 8 líneas que escribe el VLM")],
         f"lo demás, fijo: Qwen3, sin filtro, la consulta en una frase corta sin reescribir · las mismas {N_ANS} consultas · "
         "hit@1 y hit@5, con la diferencia pareada",
         ["El texto de IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. ¿Vale "
          "la pena describir cada producto?",
          "Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una "
          "frase corta sin reescribir, para medir un solo cambio."],
         30, extra=f'''<div class="vend">{producto("102.335.32", 92)}<div><span class="et">el texto de IKEA de este sillón · {_nol["name"]}</span>
         <q>{esc(_nol["description"])}</q></div></div>''')
resultado(1, "Qué se indexa", f'''
<div class="res-e1">
  <div>{barras([dict(letra="A", et="Texto del vendedor", v=_n1["hit@1"], ic=_n1["hit@1_ic95"]),
                dict(letra="B", et="Descripción desde la foto", v=_n2["hit@1"], ic=_n2["hit@1_ic95"], gana=True)], titulo="hit@1 · el anotado sale primero")}
       {barras([dict(letra="A", et="Texto del vendedor", v=_n1["hit@5"], ic=_n1["hit@5_ic95"]),
                dict(letra="B", et="Descripción desde la foto", v=_n2["hit@5"], ic=_n2["hit@5_ic95"], gana=True)],
               titulo=f"hit@5 · está entre los {K} que ve el que elige", cls="sep")}</div>
  <div class="grande-n" data-paso="1"><b>{sg(_d_idx["hit@1"], 2)}</b><span>de hit@1, pareado · IC 95% {ic_txt(*_d_idx["hit@1_ic95"])}</span>
    <p>Con la consulta ya escrita como ficha la diferencia es mayor ({sg(_d_ficha["hit@1"], 2)}): los dos cambios se potencian. Con el nombre comercial adelante («NOLMYRA»), peor: {nb(dif(_d_name))}.</p></div>
</div>''', "se indexa", "la descripción", "Se indexa la descripción hecha desde la foto, no el texto del vendedor. Es "
          f"<mark>lo que más pesa</mark> de todo el trabajo, y un costo único: {usd(C_DESC, 3)} por producto.",
          [f"Con el texto del vendedor, hit@1 da {f2(_n1['hit@1'])}; con la descripción, {f2(_n2['hit@1'])}: casi el triple, y "
           f"hit@5 pasa de {f2(_n1['hit@5'])} a {f2(_n2['hit@5'])}. La diferencia es pareada y su intervalo no toca el cero.",
           "Decisión: se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo."], 35)

# =============================================================================================
# 2 · Cómo se escribe la consulta, contra no reescribirla
# =============================================================================================
_q_full, _q_piece = CON[V1], CON[V1 + "|consulta-piece"]
_q_type, _q_kind = CON[V1 + "|consulta-type"], CON[V1 + "|consulta-kind"]
_s_full, _s_piece = CON["siglip2|description|filtro-kind"], CON["siglip2|description|filtro-kind|consulta-piece"]
_d_q = _q_piece["vs_base"]  # la frase natural menos la ficha
D_CONSULTA = -_d_q["hit@1"]  # lo que suma la ficha sobre la frase natural
pregunta(2, "Cómo se escribe la consulta", "¿Cuánto suma escribir la consulta <em>como una ficha del catálogo</em>, contra no reescribirla?",
         "El plan no busca con el pedido: escribe el producto ideal en las 8 líneas del catálogo. Es la técnica de Advanced RAG "
         "del flujo y cuesta tokens en cada pedido, pero no la habíamos medido contra no hacerla: la comparábamos con buscar "
         "solo con el nombre del kind, que es azar por construcción.",
         [("A", "La ficha", "las 8 líneas, como las escribe el plan"),
          ("B", "La frase natural, sin reescribir", f"como el redactor nombró la pieza: «{esc(FRASES[0])}» ({round(statistics.median(len(x.split()) for x in FRASES))} palabras de mediana)"),
          ("C·D", "Solo la línea Type, o solo el kind", "el piso: lo que comparábamos antes")],
         "con el coseno del flujo (densa) y contra la foto del producto (SigLIP 2) · hit@1, con la diferencia pareada",
         ["El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced "
          "RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que "
          "es azar por construcción.",
          "La ficha contra la frase natural: las pocas palabras con que el redactor nombró la pieza. Con la "
          "búsqueda del flujo, y también contra la foto."],
         30, extra='<p class="adv">Advanced RAG · query expansion con respuesta hipotética (HyDE)</p>', cls="denso")
resultado(2, "Cómo se escribe la consulta", f'''
<div class="res-2 r-2">
  <div>{barras([dict(letra="A", et="La ficha", v=_q_full["hit@1"], ic=_q_full["hit@1_ic95"], gana=True, vtxt=f3(_q_full["hit@1"])),
                dict(letra="B", et="La frase natural", v=_q_piece["hit@1"], ic=_q_piece["hit@1_ic95"], vtxt=f3(_q_piece["hit@1"])),
                dict(letra="C", et="Solo la línea Type", v=_q_type["hit@1"], ic=_q_type["hit@1_ic95"], vtxt=f3(_q_type["hit@1"])),
                dict(letra="D", et="Solo el kind", v=_q_kind["hit@1"], ic=_q_kind["hit@1_ic95"], vtxt=f3(_q_kind["hit@1"]))],
               titulo="hit@1 · búsqueda densa, contra la descripción (la del flujo)", cls="gb-compacto")}</div>
  <div>{barras([dict(letra="A", et="La ficha", v=_s_full["hit@1"], ic=_s_full["hit@1_ic95"], vtxt=f3(_s_full["hit@1"])),
                dict(letra="B", et="La frase natural", v=_s_piece["hit@1"], ic=_s_piece["hit@1_ic95"], gana=True, vtxt=f3(_s_piece["hit@1"]))],
               titulo="hit@1 · por foto: SigLIP 2, contra la foto del producto", cls="gb-compacto")}
    <p class="nota chica r2-n" data-paso="1">Contra la foto, no reescribir cuesta solo {nb(dif(_s_piece["vs_anterior"]))}.</p></div>
</div>
<p class="nota r2-nota" data-paso="1">La ficha suma <b>{nb(dif(_d_q, flip=True))}</b> de hit@1 sobre la frase sin reescribir. Y lo que no esperábamos: el texto necesita que la consulta hable como el catálogo; <b>la foto, casi no</b>.</p>''',
          "consulta", "la ficha", "El plan escribe la ficha: es la técnica de Advanced RAG del flujo. Y queda un argumento para la "
          "búsqueda híbrida: las dos rutas <mark>fallan distinto</mark>.",
          [f"La ficha da {f3(_q_full['hit@1'])} y la frase natural {f3(_q_piece['hit@1'])}: suma {sg(-_d_q['hit@1'], 2)}, con un "
           f"intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la frase sin reescribir da {f3(_s_piece['hit@1'])}, "
           "casi lo mismo que la ficha. El texto necesita que la consulta hable como el catálogo; la foto, casi no.",
           "Decisión: el plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos rutas fallan "
           "distinto."], 40)

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
         "Dos dudas de fondo sobre el índice. ¿Hace falta el embedder neuronal, o alcanza con contar palabras? Y el catálogo tiene "
         "fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la "
         "habíamos medido.",
         [("A", "Densa: Qwen3", "el coseno sobre las descripciones: la búsqueda de la versión 1"),
          ("B", "Léxica: BM25", "las palabras de esas mismas descripciones, sin modelo"),
          ("C", "Por foto: SigLIP 2 (y CLIP)", "la consulta en una frase contra la foto del producto, sin descripción"),
          ("+", "Fusionadas", "cada puntaje estandarizado (z-score), y el promedio")],
         f"las mismas {N_ANS} consultas, con el filtro por kind · hit@1, y la diferencia pareada contra la densa",
         ["Dos dudas sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo "
          "tiene fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa "
          "nunca la habíamos medido.",
          "Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, "
          "SigLIP 2, la consulta en una frase contra la foto. Y sus fusiones."],
         30, extra='<p class="adv">Advanced RAG · búsqueda híbrida y multimodal</p>', cls="denso")
resultado(3, "Búsqueda léxica, por foto e híbrida", f'''
<div class="res-e3">
  <div>{barras([_hrow("A", V1, "Densa: Qwen3"), _hrow("B", HK["lexica"], "Léxica: BM25"), _hrow("C", HK["foto"], "Por foto: SigLIP 2"),
                _hrow("C", HK["clip"], "Por foto: CLIP ViT-B/32"), _hrow("+", HK["densa+lexica"], "Densa + léxica"),
                _hrow("+", HK["densa+foto"], "Densa + foto"), _hrow("+", HK["lexica+foto"], "Léxica + foto"),
                _hrow("+", V2, "Densa + léxica + foto", gana=True)],
               titulo="hit@1 · a la derecha, la diferencia pareada contra la densa, con su IC 95%", cls="gb-e3")}</div>
  <div class="grande-n" data-paso="1"><b>{sg(D21["hit@1"])}</b><span>de hit@1, las tres fusionadas · IC 95% {ic_txt(*D21["hit@1_ic95"])}</span>
    <p>Y {nb(dif(D21, "hit@5"))} de hit@5. Solos, los tres rinden parecido: ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. Pero <b>se equivocan en cosas distintas</b>.</p></div>
</div>''', "rag.hybrid", "bm25 + siglip2", "La búsqueda del flujo pasa a ser <mark>híbrida</mark>: densa + léxica + foto, las dos rutas "
          "de la clase a la vez. Es la <b>versión 2</b>, el Ejercicio 4.",
          [f"Solos, los tres rinden parecido: {f3(HIB[V1]['hit@1'])}, {f3(HIB[HK['lexica']]['hit@1'])} y "
           f"{f3(HIB[HK['foto']]['hit@1'])}. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. "
           f"Pero se equivocan en cosas distintas: fusionados dan {f3(HIB[V2]['hit@1'])}, {sg(D21['hit@1'])} de hit@1, con un "
           "intervalo que no toca el cero.",
           "Decisión: la búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4."], 40)

# =============================================================================================
# El camino incremental: un cambio por paso (y, aparte, lo que da un VLM eligiendo)
# =============================================================================================
PASOS = [  # (método, etiqueta, paso en que aparece)
    (K_NAIVE, "RAG naive: texto del vendedor, sin reescribir", 0),
    (K_DESC, "+ cada producto descripto desde su foto", 1),
    (K_FICHA, "+ la consulta como una ficha (HyDE)", 1),
    (V1, "+ filtro por kind: versión 1", 2),
    (V1 + "|+bm25", "+ búsqueda léxica (BM25)", 3),
    (V2, "+ la foto (SigLIP 2): versión 2", 3),
]
_r_opus = RR[BASE + "|rerank-opus"]
APARTE = [("un VLM elige entre los 5 primeros", CURVA["por_k"]["5"]["acierto_eleccion"]),
          (f"un VLM reordena el top-10: el {f2(_r_opus['hit@1'])} de antes", _r_opus["hit@1"])]


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
    W, H = 1728, 590
    x0, bw, paso_x = 96, 150, 207
    base, top = 440, 96
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
             f'<text x="{xa - 14}" y="{top - 52}" class="cm-apt">aparte · una técnica aislada,</text>'
             f'<text x="{xa - 14}" y="{top - 28}" class="cm-apt">no un paso del flujo</text>')
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
<div class="camino-w">{_camino_svg()}</div>
<p class="remate chico" data-paso="4">El {f2(_r_opus["hit@1"])} que mostrábamos no era un escalón: es un VLM reordenando el top-10, <mark>una técnica aislada, no el flujo</mark>.</p>''',
    [f"La ablación incremental: un cambio por paso, con su diferencia pareada, sobre las {N_ANS} consultas. Arrancamos del RAG "
     f"naive, el texto del vendedor y la consulta sin reescribir: {f2(_n1['hit@1'])}.",
     f"Describir cada producto desde su foto lo lleva a {f2(_n2['hit@1'])}; escribir la consulta como una ficha, a "
     f"{f2(CAM[K_FICHA]['hit@1'])}. Esos dos pasos son los que más pesan.",
     "El filtro por kind no suma en este banco: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la "
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
      f"hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo: el "
      f"{round(100 * DOC['con_variantes'])}% de las consultas busca un producto que tiene variantes.",
      [("A", "Exacto", "el producto anotado sale primero (hit@1)"),
       ("B", "El mismo modelo", "también vale otra variante: el mismo nombre comercial y el mismo grupo"),
       ("C", "Sirve", "un juez califica el primer candidato contra la pieza del ambiente, con 2, 1 o 0")],
      f"el primer candidato de la búsqueda de la versión 1 · el juez: {G_N} consultas, reponderado a todas",
      barras([dict(letra="A", et="El producto exacto", v=_e_q["hit@1"], ic=_e_q["hit@1_ic95"]),
              dict(letra="B", et="El mismo modelo", v=_e_q["familia_hit@1"], ic=_e_q["familia_hit@1_ic95"]),
              dict(letra="C", et="Uno que sirve, según un juez", v=UTIL1, gana=True)],
             titulo="el primer candidato es…", paso=2, gana_paso=3, cls="gb-unica")
      + f'''<div class="fam-ej"><figure>{producto(FAM_REL, 96)}<figcaption>el anotado</figcaption></figure>
      <figure>{producto(FAM_TOP, 96)}<figcaption>salió primero</figcaption></figure>
      <p><span class="et">«{esc(FAM_R["phrase"])}»</span>Es el mismo modelo ({ITEMS[FAM_TOP]["name"]}) en otro color: para hit@1, un error. Pasa <b>una de cada {round(1 / _frac_var)} veces</b> que el primero «falla».</p></div>''',
      "correcto", "tres niveles", f"El banco <mark>subestima el nivel, no el orden</mark>: el exacto para comparar métodos, y los "
      f"tres juntos para decir cuánto sirve: {f2(_e_q['hit@1'])} · {f2(_e_q['familia_hit@1'])} · {f2(UTIL1)}.",
      ["hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que "
       "cuenta como error es el mismo mueble en otro color?",
       "Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez.",
       f"El exacto, {f2(_e_q['hit@1'])}; el mismo modelo, {f2(_e_q['familia_hit@1'])}; uno que sirve, {f2(UTIL1)}. Una de cada "
       f"{round(1 / _frac_var)} veces que el primero falla es otra variante del mismo mueble, como esta alfombra.",
       "El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia. Usamos el exacto para comparar, y "
       "los tres juntos para decir cuánto sirve."], 40, rotulo="conclusión")

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
         f"hit@10 es {f2(_r0['hit@10'])} pero hit@1 {f2(_r0['hit@1'])}: el correcto casi siempre está entre los diez primeros, "
         "pero no primero. En el flujo, quien elige mira las fotos de los candidatos.",
         [("A", "Un VLM reordena el top-10", "Opus recibe la consulta y las fotos de los 10 primeros, y los ordena"),
          ("k", "De 1 a 10 candidatos", "sale gratis de ahí: si eligiera entre los primeros k, ¿acertaría?")],
         "hit@1 después de reordenar, con su diferencia pareada · la curva, con su techo: el correcto está entre esos k (hit@k)",
         [f"hit@10 es {f2(_r0['hit@10'])} pero hit@1 {f2(_r0['hit@1'])}: el correcto casi siempre está entre los diez primeros, "
          "pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar?",
          "Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera "
          "entre los primeros k, ¿acertaría? La punteada es el techo."],
         30, extra='<p class="adv">Advanced RAG · reranking con un VLM</p>')
resultado(5, "Elegir con un VLM, y cuántos candidatos", f'''
<div class="r-5">
  <div class="r5-izq">
    <span class="et">hit@1 · un VLM reordena el top-10 mirando las fotos</span>
    <div class="r5-num"><span>{f3(_r0["hit@1"])}</span><i>→</i><b>{f3(_r_opus["hit@1"])}</b></div>
    <p class="r5-d">{nb(dif(_d_opus))}, pareado · {usd(C_RERANK)} por búsqueda</p>
    <ul class="r5-l" data-paso="1">
      <li>De 3 a 5 candidatos, la elección sube <b>{nb(sg(_d35["acierto_eleccion"]) + " " + ic_txt(*_d35["ic95"]))}</b>; a partir de 8 se aplana.</li>
      <li>En los {_dh["ambientes"]} ambientes reales, el {pct(_dh["elegido_en_puestos_4_y_5"])} de lo que eligió el flujo salió de los puestos 4 y 5.</li>
    </ul>
  </div>
  <div>{_e5_chart}</div>
</div>''', "candidatos", str(K), f"{K} candidatos por pieza (antes 3). Ojo: es una <mark>técnica aislada, no un paso del flujo</mark>. "
          "Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige arma un conjunto para el cuarto, y no tiene ground truth.",
          [f"Reordenando el top-10, hit@1 pasa de {f3(_r0['hit@1'])} a {f3(_r_opus['hit@1'])}. De 3 a 5 candidatos la elección "
           f"sube {round(100 * _d35['acierto_eleccion'])} puntos, también significativo; a partir de 8 se aplana.",
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
         "Es el «con y sin retrieval» del flujo, con sus dos extremos: sin ranking (5 al azar) y con todo a la vista (el catálogo "
         "entero en el prompt). El primero es además el control del juez: si no distinguiera esas dos listas, ninguna "
         "comparación de punta a punta diría nada.",
         [("A", "Con búsqueda", f"para cada pieza, los {K} mejores de la búsqueda, con su foto"),
          ("B", f"{K} al azar", "entre los productos que pasan los mismos filtros (kind y medidas)"),
          ("C", "El catálogo entero en el prompt", f"las {_mil_fichas} fichas en texto ({round(CTX_TOKENS / 1000)} mil tokens, en caché), con el mismo "
                                                   "filtro; sin ranking ni fotos de candidatos")],
         f"el mismo plan, el mismo modelo que elige y el mismo juez, en los dos órdenes · contra el azar, {J_AZAR['n']} ambientes (la "
         f"versión 1) · contra el catálogo entero, {J_CTX['n']} (la versión 2)",
         ["Es el con y sin retrieval del flujo, con sus dos extremos. Uno: darle al que elige cinco productos al azar del kind "
          "pedido; es el control del juez, porque si no distinguiera esas dos listas, ninguna comparación de punta a "
          "punta diría nada. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?",
          f"Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en {J_AZAR['n']} ambientes. Contra el catálogo entero "
          f"en el prompt, las {_mil_fichas} fichas en texto, en los {J_CTX['n']}."], 35)
resultado(6, "Con búsqueda, al azar, o con el catálogo entero", f'''
<div class="r-7">
  <div>
    <span class="et r7-et">sin ranking · {K} al azar del kind · {J_AZAR["n"]} ambientes</span>
    {_marcador("Con búsqueda", J_AZAR["a"], J_AZAR["b"], f"{K} al azar", f"los {J_AZAR['votos']} votos: los dos órdenes coinciden siempre · test de signos, p = {f3(P_AZAR)}")}
    {barras([dict(letra="A", et="Con búsqueda", v=J_AZAR["util_a"], gana=True), dict(letra="B", et=f"{K} al azar", sub="dentro del kind", v=J_AZAR["util_b"])],
            titulo="productos útiles: la fracción con la nota máxima del juez", cls="gb-compacto r7-b")}
    <p class="nota chica" data-paso="1">El filtro solo no alcanza: sin el ranking, la lista tiene el tipo de pieza correcto y poco más (pedido {f1(_sa["azar"]["request"])} contra {f1(_sa["densa"]["request"])}, de 1 a 5).</p>
  </div>
  <div class="ticket rag-q" data-paso="1">
    <div class="tk-cab"><b>¿Hacía falta RAG?</b><span>todo a la vista: el catálogo entero<br>en el prompt · {J_CTX["n"]} ambientes</span></div>
    <div class="tk-l"><span class="tk-n">Ambientes que gana cada una</span><span class="tk-dots"></span><span class="tk-v">{J_CTX["a"]} a {J_CTX["b"]}, y {J_CTX["emp"]} empate</span></div>
    <div class="tk-l"><span class="tk-n">Productos útiles</span><span class="tk-dots"></span><span class="tk-v">{f2(J_CTX["util_a"])} y {f2(J_CTX["util_b"])}</span></div>
    <div class="tk-l"><span class="tk-n">Lo elegido viendo todo estaba entre los {K}</span><span class="tk-dots"></span><span class="tk-v">{CTX_EN_TOP5} de {CTX_PIEZAS} piezas</span></div>
    <div class="tk-l sep"><span class="tk-n">Elegir entre los {K} candidatos, con foto</span><span class="tk-dots"></span><span class="tk-v">{usd(C_CHOOSE_V2, 3)} por pedido</span></div>
    <div class="tk-l"><span class="tk-n">Con el catálogo entero, en caché</span><span class="tk-dots"></span><span class="tk-v">{usd(C_CTX_CACHE)}</span></div>
    <div class="tk-l"><span class="tk-n">Con el catálogo entero, sin caché</span><span class="tk-dots"></span><span class="tk-v">{usd(C_CTX_SIN)}</span></div>
    <p class="tk-pie"><b>Por calidad, no: empatan.</b> RAG se justifica porque <b>escala</b> (el catálogo ya ocupa un tercio del contexto; ABO completo son {miles(DOC["abo_listados"])} listados), porque <b>no depende de la caché</b> (dura {DOC["cache_min"]} minutos y cualquier cambio del catálogo la invalida; en el índice, un alta es un insert) y porque no ata el sistema a un modelo de contexto largo.</p>
  </div>
</div>''', "la búsqueda", "se queda", f"La búsqueda hace falta cuando el que elige ve {K} productos, y <mark>empata</mark> cuando puede leerlos todos. "
          f"Con {_mil_fichas} productos, RAG no hace mejor la lista: es la arquitectura que escala.",
          [f"Contra el azar, {J_AZAR['a']} a {J_AZAR['b']}, con los {J_AZAR['votos']} votos: los productos útiles pasan de "
           f"{f2(J_AZAR['util_b'])} a {f2(J_AZAR['util_a'])}. Y el juez distingue cuando la diferencia es grande. Contra el catálogo "
           f"entero, {J_CTX['a']} a {J_CTX['b']}, con los mismos productos útiles: empatan. Con el catálogo en la caché de prompt "
           "cuesta lo mismo; sin caché, diez veces más.",
           "O sea: por calidad, no hacía falta. Con mil quinientos productos, un modelo de contexto largo hace el trabajo de la "
           "búsqueda leyendo todo. La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos "
           "todos. RAG lo elegimos porque escala, y porque no depende del tráfico, de la caché ni de un modelo de contexto largo."],
          50)

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
      "Las consultas de evaluación las escribió un modelo. La clase pidió promedio de ejecuciones y desvío: si el número cambia "
      "mucho con quién escribe, mide al redactor y no al sistema.",
      [("A", "Tres redactores independientes", "las mismas consultas, escritas otras dos veces mirando las mismas fotos"),
       ("B", "Los dos buscadores sobre cada escritura", "la versión 1 (densa) y la versión 2 (híbrida)")],
      "hit@1 de cada escritura · media ± desvío",
      _rep_svg() + f'<p class="nota chica">La mejora de la híbrida se repite en las tres escrituras, pareada: '
                   f'{" · ".join(sg(d["hit@1"]) for d in _difs_r)}.</p>',
      "ruido", f"± {f1(100 * statistics.stdev(_v1s))} puntos", f"El número se mueve unos {f1(100 * statistics.stdev(_v1s))} puntos "
      "sin cambiar el sistema: <mark>una diferencia de 2 puntos no es señal</mark>. Por eso los embedders «no se distinguen», y la híbrida sí.",
      ["Las consultas de evaluación las escribió un modelo. La clase pidió promedio y desvío: ¿cuánto cambia el número sin "
       "cambiar el sistema?",
       "Las mismas consultas, escritas otras dos veces por subagentes independientes.",
       f"La versión 1 da {media_desvio(_v1s)}; la versión 2, {media_desvio(_v2s)}. La mejora de la híbrida se repite con los "
       "tres.",
       "El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos."],
      30, rotulo="conclusión")


# =============================================================================================
# De trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta en una línea
# =============================================================================================
def _emb(k: str) -> dict:
    return EMB[f"{k}|description|filtro-kind"]


def _sin(x: str) -> dict:
    """La búsqueda de la versión 1 sin esas líneas en documentos y consultas."""
    return LIN[f"{V1}|sin-{x}"]


def _h15(x: dict) -> str:
    return f'{f3(x["hit@1"])} / {f3(x["hit@5"])}'


def _tram(n, nombre, que, respuesta):
    pin = f'<em class="tp">{n}</em>' if n else '<em class="tp no">—</em>'
    return f'<div class="tr-l">{pin}<b>{nombre}</b><span class="tr-q">{que}</span><span class="tr-r">{respuesta}</span></div>'


def tramite(id_, k, titulo, cab_que, filas, remate, notas, pines):
    lam(id_, f"De trámite ({k} de 2)", "Experimentos · de trámite", f'''
{kick("E", f"experimentos · de trámite ({k} de 2)")}
<h2 class="t chico">{titulo}</h2>
{minimapa(*pines)}
<div class="ticket tram-tk">
  <div class="tr-cab"><span></span><span>la pregunta</span><span>{cab_que}</span><span>la respuesta</span></div>
  {"".join(filas)}
</div>
<p class="remate chico tram-rem">{remate}</p>''', notas, 40, clase="clara")


_dims = {d: (F[f"{BASE}|dim-{d}"] if d != 1024 else F[BASE])["hit@1"] for d in (32, 128, 512, 1024)}
_d512 = paired(ABL_DIR, BASE + "|dim-512", BASE)
_doc, _chunk, _alin = F[BASE], F[BASE + "|chunks-lines-max"], F[BASE + "|chunks-lines-aligned"]
_visto = _sin("Use+Style+Feel+Goes with")
_ex_a, _ex_b = rankings(ABL_DIR)[BASE + "|exact"], rankings(ABL_DIR)[BASE]
_iguales = sum(x["ranked"] == y["ranked"] for x, y in zip(_ex_a, _ex_b, strict=True))
tramite("tram1", 1, "De trámite: <em>las cuatro preguntas sobre el índice</em>", "qué se comparó (hit@1)", [
    _tram(8, "Embedder", f'hashing {f3(_emb("hashing")["hit@1"])} · BM25 {f3(_emb("bm25")["hit@1"])} · BGE {f3(_emb("bge")["hit@1"])} · <b>Qwen3 {f3(EMB[V1]["hit@1"])}</b>',
          f'Solo se sostiene Qwen3 sobre BGE ({nb(dif(_emb("bge")["vs_base"], flip=True))}). Contra contar palabras no se distingue '
          f'({nb(dif(_emb("hashing")["vs_base"], flip=True))}). Queda Qwen3 por robustez a la paráfrasis, sin evidencia medida.'),
    _tram(9, "Dimensión", " · ".join(f"{'<b>' if d == 1024 else ''}{d}: {f3(v)}{'</b>' if d == 1024 else ''}" for d, v in _dims.items()),
          f"Con 512 da lo mismo que con 1024 ({nb(dif(_d512))}). Con {miles(D['prod_todos'])} productos la memoria no pesa: queda 1024."),
    _tram(10, "Splitting y líneas", f'<b>un documento {f3(_doc["hit@1"])}</b> · un chunk por línea {f3(_chunk["hit@1"])} · línea contra línea {f3(_alin["hit@1"])}',
          f'No se parte: un producto es un documento de unas {D["palabras_med"]} palabras. Lo que importa es qué líneas lo componen: sin Colors, '
          f'{nb(dif(_sin("Colors")["vs_base"]))}; sin Shape, {nb(dif(_sin("Shape")["vs_base"]))}; con solo las cuatro de lo que se ve se encuentra igual ({f3(_visto["hit@1"])}).'),
    _tram(11, "Base vectorial", "ChromaDB (HNSW, coseno) contra recorrer todos los vectores con numpy",
          f"El mismo top-10 en {_iguales} de {len(_ex_a)} consultas. La híbrida no consulta el HNSW: puntúa a todos los que pasan el filtro (con {miles(D['prod_todos'])}, milisegundos); con millones, cada buscador traería su top-k de un índice."),
], "Con el texto bien escrito, el índice casi no decide nada: son <mark>respuestas que hay que tener</mark>, no un gran experimento.",
    "Los de trámite, con la respuesta corta. Embedder: Qwen3 solo se sostiene sobre "
    "BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten el molde. Dimensión: con 512 da lo "
    f"mismo que con {miles(1024)}, y con {miles(D['prod_todos'])} productos la memoria no pesa. Splitting: no partimos; "
    "lo que importa son las líneas de lo que se ve, colores y forma. Base "
    f"vectorial: ChromaDB da el mismo top-10 que la búsqueda exacta en las {len(_ex_a)} consultas; la usamos porque "
    "persiste y escala; la híbrida no lo consulta, puntúa a todos los que pasan el filtro.", (8, 9, 10, 11))

_f_none, _f_type = HIB["qwen3|description|filtro-none"], HIB[BASE]
_mini, _qrr = F[BASE + "|rerank-minilm-reranker"], RLOC[BASE + "|rerank-qwen3-reranker"]
_d_abo = paired(TODOS_DIR, BASE, BASE, run_b=ABL_DIR)  # el mismo buscador, con ABO de distractores
tramite("tram2", 2, "De trámite: <em>filtros, rerankers de texto, la escena</em> y el catálogo", "qué se comparó", [
    _tram(12, "Filtros", f"hit@1 / hit@5 · sin filtro {_h15(_f_none)} · por tipo {_h15(_f_type)} · <b>por kind {_h15(B1)}</b>",
          f'No suman en este banco, y el de kind cuesta 2 puntos de hit@5 ({nb(dif(_d_kind, "hit@5"))}). Se usa por algo que el banco no mide: '
          f'en los pedidos reales evita un {round(100 * DOC["otro_kind"])}% de candidatos de otro kind (se pide un sillón y aparece una silla de comedor). '
          f'El de medidas actúa poco: cambia {FM["candidatos_reemplazados"]} de {FM["candidatos"]} candidatos en los ambientes reales, y solo el {round(100 * D["ikea_con_medida"])}% de IKEA tiene alguna medida.'),
    _tram(13, "Rerankers de texto", f"hit@1 / hit@5 · sin rerank {_h15(RLOC[BASE])} · MiniLM {_h15(_mini)} · Qwen3-Reranker {_h15(_qrr)}",
          f'Empeoran ({nb(dif(_qrr["vs_base"]))} el mejor): releen el mismo texto que ya usó la búsqueda. El que suma es el que mira las fotos (experimento 5).'),
    _tram(14, "La escena", f'<b>plantilla: {IMG_PL["identificados"]} de {IMG_PL["productos"]} reconocidos, el ambiente en {IMG_PL["ambiente_conservado"]} de {IMG_PL["corridas"]}</b> · '
          f'escrita por el LLM: {IMG_LLM["identificados"]} de {IMG_LLM["productos"]}, en {IMG_LLM["ambiente_conservado"]} de {IMG_LLM["corridas"]}',
          f'Empate, medido en los {IMG_PL["corridas"]} ambientes con las mismas listas ({nb(sg(ESC_DIF) + " " + ic_txt(*DOC["escena_ic"]))} de reconocidos, pareado). '
          f'Queda la plantilla: da lo mismo y cuesta una llamada menos ({usd(C_SCENE, 3)} por pedido). No medimos si los muebles quedan mejor repartidos.'),
    _tram(None, "El catálogo", f'hit@1 · {D["prod_268"]} productos {f3(C268[BASE]["hit@1"])} → {D["prod_855"]}: {f3(C855[BASE]["hit@1"])} → {D["prod_819"]}: {f3(CREV[BASE]["hit@1"])} · '
          f'con los {D["n_abo"]} de ABO, hit@5 {f3(F[BASE]["hit@5"])} → {f3(CTOD[BASE]["hit@5"])}',
          f'Ampliarlo y revisarlo fueron decisiones de datos, no experimentos. Sumar ABO de distractores le cuesta al buscador {nb(dif(_d_abo, "hit@5"))} de hit@5: el costo, chico, de cubrir más estilos.'),
], "Sin experimento que los sostenga quedan <mark>el modelo de imagen</mark> (comparación diseñada, sin correr) y los umbrales del control, puestos a mano.",
    "Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, por algo que el "
    f"banco no mide: en los pedidos reales, sin él, el {round(100 * DOC['otro_kind'])} por ciento de los candidatos sería de "
    "otro kind. El de medidas cambia uno de cada once candidatos, sin evidencia de que mejore la lista. Rerankers de texto: probamos "
    "el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el texto que ya usó la búsqueda. La escena: la "
    "plantilla y la escrita por el LLM empatan, como vimos. Y el catálogo: "
    f"ampliarlo y revisarlo fueron decisiones de datos, y sumar Amazon le cuesta al buscador {f1(-100 * _d_abo['hit@5'])} puntos "
    "de hit@5.", (12, 13, 14))
