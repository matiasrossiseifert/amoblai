"""Los trece experimentos. Cada uno: una lámina oscura con la pregunta (por qué y el experimento,
con la etapa encendida en el flujo) y una clara con los resultados y la decisión (el talón).
Los experimentos 4 y 5 van en una sola lámina."""

from __future__ import annotations

import statistics

import yaml

from datos import (AM, BASE, C268, C855, CREV, D, ESTILO, F, HERO, ITEMS, N_HERO, REPL, REPL_CORTO, REPL_N, REPL_R1, REPL_R2,
                   REPLICA, ROOM_CHECK, ROOT, RR, cajas_dibujadas, esc, f1, f2, f3, ic, pct, usd)
from piezas import ETAPA_EXP, barras, flujo, foto, kick, letra, lineas_svg, minimapa, producto, talon, variantes_html
from recorrido import cuerpo_prompt, prompt_tk
from registro import lam

ETAPA_TXT = {1: "descripción", 2: "índice", 3: "búsqueda", 4: "índice", 5: "índice", 6: "índice y plan", 7: "elección",
             8: "búsqueda y elección", 9: "catálogo", 10: "catálogo", 11: "cómo medimos la búsqueda",
             12: "escena, imagen y control", 13: "imagen"}


def pregunta(n, tema, titulo, porque, variantes, metrica, notas, seg, extra="", ancho_t="", cls="", fuera=""):
    """Lámina oscura: el porqué (paso 0) y el experimento (paso 1), con el flujo a la derecha.
    variantes: lista de (letra, nombre, detalle), o el HTML ya armado. fuera: HTML suelto en la lámina."""
    vs = variantes if isinstance(variantes, str) else variantes_html(variantes)
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
<div class="izq {cls}">
  {kick(f"E{n}", f"experimento {n} de 13 · {ETAPA_TXT[n]}")}
  <h2 class="t chico {ancho_t}">{titulo}</h2>
  <p class="porque">{porque}</p>
  {extra}
  <div class="exp-blq" data-paso="1">
    <span class="et">el experimento</span>
    {vs}
    <p class="metrica">{metrica}</p>
  </div>
</div>
<div class="esq">{flujo(pines=[n])}</div>{fuera}''', notas, seg, focos=[" ".join(ETAPA_EXP[n])])


def resultado(n, tema, cuerpo, clave, valor, decision, notas, seg, paso_dec=2, sufijo="r", kick_txt="resultados",
              rotulo="configuración"):
    lam(f"e{n}{sufijo}", f"Exp. {n}: {kick_txt}", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · {kick_txt}")}
<h2 class="t chico">{tema}</h2>
{minimapa(n)}
{cuerpo}
{talon(clave, valor, decision, paso=paso_dec, rotulo=rotulo) if decision else ""}''', notas, seg, clase="clara")


# =============================================================================================
# E1 · Qué texto se indexa
# =============================================================================================
_nol = ITEMS["102.335.32"]
pregunta(1, "Qué texto se indexa", "¿Alcanza con el texto del vendedor, o conviene <em>describir cada producto mirando su foto</em>?",
         "Nadie pide como escribe el vendedor: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está "
         "en la foto. Describir cada producto con un VLM es un costo que se paga una sola vez.",
         [("A", "Texto del vendedor", "nombre, tipo, colores y la frase de marketing"),
          ("B", "Descripción del VLM", "8 líneas mirando la foto, en el mismo formato que la consulta del plan"),
          ("C", "Nombre comercial + descripción", "la misma descripción con el nombre adelante")],
         f"las mismas {D['n_respondibles']} búsquedas, todo lo demás fijo (Qwen3, filtro) · hit@1",
         ["La primera pregunta fue qué texto indexar. IKEA trae nombre, tipo, colores y una frase de marketing del estilo «The "
          "armchair is lightweight and easy to move». Pero nadie pide así: se pide un sillón nórdico, de madera clara, con "
          "tapizado crema, y eso está en la foto.",
          f"Indexamos tres textos y corrimos las mismas {D['n_respondibles']} búsquedas del ground truth, con todo lo demás "
          "fijo: el texto del vendedor; la descripción del VLM que vimos en el recorrido; y esa descripción con el nombre "
          "comercial adelante."],
         30, extra=f'''<div class="vend">{producto("102.335.32", 92)}<div><span class="et">el texto de IKEA de este sillón · {_nol["name"]}</span>
         <q>{esc(_nol["description"])}</q></div></div>''')
resultado(1, "Qué texto se indexa", f'''
<div class="res-e1">
  <div>{barras([dict(letra="A", et="Texto del vendedor", v=D['e1_vendedor'], ic=ic(F, 'qwen3|seller|filtro-type')),
                dict(letra="B", et="Descripción del VLM", v=D['e1_desc'], ic=ic(F, BASE), gana=True)], titulo="hit@1 · filtro por tipo")}
       {barras([dict(letra="B", et="Descripción del VLM", v=D['e1_desc_kind'], ic=ic(F, 'qwen3|description|filtro-kind'), gana=True),
                dict(letra="C", et="Nombre + descripción", v=D['e1_nombre_kind'], ic=ic(F, 'qwen3|name+description|filtro-kind'))],
               titulo="hit@1 · filtro por kind (el mismo para las dos)", cls="sep")}</div>
  <div class="grande-n" data-paso="1"><b>×{f1(D['e1_veces'])}</b><span>el cambio más grande de todo el trabajo</span>
    <p>NOLMYRA no le dice nada al embedding.</p></div>
</div>''', "texto", "descripción", "Indexamos solo la descripción del VLM. Y queda una idea para todo el trabajo: consulta y "
          "documento <mark>escritos en el mismo formato</mark>.",
          [f"Con el texto del vendedor, hit@1 da {f2(D['e1_vendedor'])}; con la descripción del VLM, {f2(D['e1_desc'])}: más de "
           f"{int(D['e1_veces'])} veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el "
           f"mismo filtro, de {f2(D['e1_desc_kind'])} a {f2(D['e1_nombre_kind'])}. NOLMYRA no le dice nada al embedding.",
           "Decisión: indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el "
           "documento escritos en el mismo formato."], 40)

# =============================================================================================
# E2 · Embedder
# =============================================================================================
_e2 = D["e2"]


def _e2f(j, met):
    return [dict(letra=l, et=n, v=_e2[k][j], ic=ic(F, f"{k}|description|filtro-type", met), gana=(k == "qwen3"))
            for l, k, n in (("A", "hashing", "Hashing"), ("B", "bge", "BGE-base"), ("C", "qwen3", "Qwen3-Embedding"))]


pregunta(2, "Embedder", "¿Cuánto aporta <em>el modelo de embeddings</em>?",
         "Un modelo más grande cuesta memoria y tiempo, y nos pusimos una restricción: el retrieval corre local, en CPU, sin "
         "pagar una API. ¿Cuánto gana un modelo entrenado contra una línea de base sin modelo?",
         [("A", "Hashing", "bolsa de palabras hasheada, sin ningún modelo"), ("B", "BGE-base", "110 millones de parámetros"),
          ("C", "Qwen3-Embedding", "600 millones de parámetros")],
         "el mismo texto y las mismas búsquedas · hit@1 y MRR@10",
         ["Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta "
          "memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos "
          "ver cuánto gana un modelo entrenado contra una línea de base sin modelo.",
          "Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún "
          "modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones."], 30)
resultado(2, "Embedder", f'''
<div class="res-2">
  <div>{barras(_e2f(0, "hit@1"), titulo="hit@1", cls="gb-compacto")}</div>
  <div>{barras(_e2f(1, "mrr@10"), titulo="MRR@10", cls="gb-compacto")}</div>
</div>
<p class="nota" data-paso="1">Las descripciones usan vocabulario controlado (los estilos y los kinds salen de listas cerradas): hasta contar palabras funciona bastante.</p>''',
          "embedder", "Qwen3", "Qwen3-Embedding-0.6B (Apache 2.0, corre en CPU). La lección: <mark>el formato del texto</mark> vale más que el modelo.",
          [f"Gana Qwen3, con {f2(_e2['qwen3'][0])}. Pero el hashing queda cerca ({f2(_e2['hashing'][0])}) y BGE último "
           f"({f2(_e2['bge'][0])}). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen "
           f"de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR "
           f"({f2(_e2['qwen3'][1])} contra {f2(_e2['hashing'][1])}).",
           "Decisión: Qwen3-Embedding-0.6B, Apache 2.0, corre en CPU. La lección: el formato del texto vale más que el modelo."], 30)

# =============================================================================================
# E3 · Filtros duros
# =============================================================================================
_e3 = D["e3"]


def _e3f(j, met):
    return [dict(letra=l, et=n, v=_e3[k][j], ic=ic(F, f"qwen3|description|filtro-{k}", met), gana=(k == "type"))
            for l, k, n in (("A", "none", "Sin filtro"), ("B", "type", "Filtro por tipo"), ("C", "kind", "Filtro por kind"))]


pregunta(3, "Filtros duros", "¿Conviene filtrar por categoría? <em>¿Con qué granularidad?</em>",
         "El plan sabe qué pieza busca. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta "
         "que un sofá. Filtrar por metadata es gratis, pero si el plan y el catálogo no coinciden en la categoría, el correcto "
         "queda afuera.",
         [("A", "Sin filtro", "solo similitud"), ("B", "Filtro por tipo", f"{D['n_tipos']} categorías gruesas: sofá, mesa, lámpara…"),
          ("C", "Filtro por kind", f"{D['n_kinds']} categorías finas: mesa ratona, mesa de comedor…")],
         "en ChromaDB va como <code>where</code> · hit@1 y, sobre todo, hit@10",
         ["El filtro duro que vimos en la búsqueda: por similitud sola, una mesa nórdica de madera clara se puede parecer más a "
          "la consulta que un sofá. Filtrar es gratis, pero si el plan y el catálogo no coinciden en la categoría, el correcto "
          "queda afuera.",
          f"Tres opciones: sin filtro; por tipo, {D['n_tipos']} categorías gruesas como sofá, mesa o lámpara; y por kind, "
          f"{D['n_kinds']} categorías finas como mesa ratona o mesa de comedor. Miramos hit@1 y sobre todo hit@10."], 30)
resultado(3, "Filtros duros", f'''
<div class="res-2">
  <div>{barras(_e3f(0, "hit@1"), titulo="hit@1 · casi no cambia", cls="gb-compacto")}</div>
  <div>{barras(_e3f(1, "hit@10"), titulo="hit@10 · el filtro fino resta", cls="gb-compacto")}</div>
</div>
<p class="nota" data-paso="1">Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro por kind la deja afuera.</p>''',
          "filtro", "siempre", "Filtrar siempre, más las <mark>medidas máximas</mark> del plan. El flujo filtra por los kinds que "
          "elige el plan (puede dar más de uno); pasarlo a tipo es lo próximo a probar.",
          [f"Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da {f2(_e3['kind'][1])} "
           f"contra {f2(_e3['type'][1])} del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa "
           "ratona, el filtro fino la deja afuera.",
           "Decisión: filtrar siempre, más las medidas máximas del plan. El flujo filtra por los kinds que elige el plan, que "
           "puede dar más de uno; contra el tipo, la diferencia en hit@1 está dentro del intervalo, y pasarlo a tipo es lo "
           "próximo que probaríamos."], 35)


# =============================================================================================
# E4 y E5: una lámina cada uno
# =============================================================================================
def unica(n, tema, titulo, porque, variantes, metrica, res_html, clave, valor, decision, notas, seg):
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} de 13 · {ETAPA_TXT[n]}")}
{minimapa(n)}
<div class="un-izq">
  <h2 class="t chico">{titulo}</h2>
  <p class="porque">{porque}</p>
  <div class="exp-blq" data-paso="1">
    <span class="et">el experimento</span>
    {variantes_html(variantes)}
    <p class="metrica">{metrica}</p>
  </div>
</div>
<div class="un-der" data-paso="2">{res_html}</div>
{talon(clave, valor, decision, paso=3)}''', notas, seg, clase="clara unica")


_e4 = D["e4"]
unica(4, "Splitting", "¿Conviene partir cada descripción <em>en chunks</em>?",
      f"En la materia vimos que el chunking es central en un RAG. Nuestros documentos son cortos ({D['palabras_lo']} a "
      f"{D['palabras_hi']} palabras), pero tienen 8 líneas con roles distintos. Hipótesis: comparar colores contra colores podía "
      "ser más preciso que un solo vector por producto.",
      [("A", "Un documento por producto", "las 8 líneas juntas"),
       ("B", "Un chunk por línea", "el producto vale lo que su línea más parecida"),
       ("C", "Línea contra línea", "cada línea contra la del mismo rótulo, promediado")],
      "las mismas búsquedas · hit@1",
      barras([dict(letra="A", et="Un documento", v=_e4['whole'], ic=ic(F, BASE), gana=True),
              dict(letra="B", et="Un chunk por línea", v=_e4['max'], ic=ic(F, BASE + '|chunks-lines-max')),
              dict(letra="C", et="Línea contra línea", v=_e4['aligned'], ic=ic(F, BASE + '|chunks-lines-aligned'))],
             titulo="hit@1", paso=2, gana_paso=3, cls="gb-unica")
      + '<p class="nota chica">Una línea suelta como <code>Colors: light wood</code> se parece a cualquier cosa de madera clara: partir pierde el contexto.</p>',
      "chunking", "ninguno", "Un documento por producto: con documentos tan cortos, <mark>no hay nada que partir</mark>.",
      [f"El chunking es central en un RAG. Nuestros documentos son cortos, de {D['palabras_lo']} a {D['palabras_hi']} "
       "palabras, pero tienen 8 líneas con roles distintos. ¿Comparar colores contra colores sería más preciso que un solo "
       "vector?",
       "Tres formas: un documento por producto; un chunk por línea, donde el producto vale lo que su línea más parecida; y "
       "línea contra línea, cada una contra la del mismo rótulo.",
       f"Gana un documento ({f2(_e4['whole'])}). Línea contra línea queda cerca ({f2(_e4['aligned'])}) y el chunk por línea "
       f"se desploma ({f2(_e4['max'])}): «Colors: light wood» se parece a cualquier cosa de madera clara.",
       "Decisión: un documento por producto. Con documentos tan cortos no hay nada que partir."], 35)

_dims = [d for d, _, _ in D["e5"]]
_vals = [v for _, v, _ in D["e5"]]
_v = dict((d, v) for d, v, _ in D["e5"])
_e5_chart = lineas_svg(_dims, [dict(ys=_vals, clase="sol", paso=2)], 980, 470, 0.3, 0.65, [0.3, 0.4, 0.5, 0.6],
                       xlab="componentes del vector (escala log)", logx=True, banda=([c[0] for _, _, c in D["e5"]], [c[1] for _, _, c in D["e5"]]),
                       marcas=[(512, _v[512], f"512: {f2(_v[512])} · la mitad de memoria", -20, -26, "end", True),
                               (1024, _v[1024], f"1024: {f2(_v[1024])}", 0, 48, "end", False),
                               (32, _v[32], f"32: {f2(_v[32])}", 20, 44, "start", False)], paso=2, gana_paso=3, mt=40, mb=96)
unica(5, "Dimensión del embedding", "¿Cuánto se puede <em>achicar el vector</em> sin perder?",
      f"Qwen3 se entrenó con Matryoshka: las primeras componentes concentran la información, así que se puede truncar sin "
      f"reentrenar. Con {D['prod_819']} productos no importa; en un catálogo de millones, la memoria y la latencia crecen con la "
      "dimensión.",
      [("A", "Truncar", "a 32, 64, 128, 256, 512 y 1024 componentes"), ("B", "Renormalizar", "y correr las mismas búsquedas")],
      "hit@1, con su intervalo de confianza",
      f'<div class="gl-tit">hit@1 con su IC 95% (la banda)</div>{_e5_chart}',
      "dim", "1024", "Para este catálogo dejamos 1024, porque no cuesta nada; <mark>si creciera, 512</mark>.",
      [f"Qwen3 se entrenó con Matryoshka: se puede truncar el vector sin reentrenar. Con {D['prod_819']} productos no "
       "importa; en un catálogo de millones, la memoria y la latencia crecen con la dimensión.",
       "Truncamos de 32 a 1024 componentes, renormalizamos y repetimos las búsquedas.",
       f"Con 512 da casi lo mismo que con 1024 ({f2(_v[512])} contra {f2(_v[1024])}), con la mitad de memoria. Con 32 cae a "
       f"{f2(_v[32])}.",
       "Decisión: para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512."], 35)

# =============================================================================================
# E6 · Base vectorial y query rewriting
# =============================================================================================
pregunta(6, "Base vectorial y consulta", "¿HNSW pierde resultados? ¿Hace falta que el plan <em>reescriba la consulta entera</em>?",
         "Pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no "
         "perdiera resultados. Y el plan escribe para cada pieza el producto ideal en 8 líneas: eso cuesta tokens y latencia en "
         "cada pedido.",
         [("A·B", "Exacta contra ChromaDB", "con la misma consulta"), ("C", "Consulta completa", "las 8 líneas que escribe el plan"),
          ("D·E", "Consultas cortas", "solo la línea Type, o solo el nombre del kind (no reescribir)")],
         "hit@1",
         ["Dos dudas. ChromaDB usa HNSW, un índice aproximado: había que verificar que no perdiera resultados contra la búsqueda "
          "exacta con numpy. Y el query rewriting que vimos en el plan cuesta tokens y latencia en cada pedido: ¿alcanzaba una "
          "consulta más corta?",
          "ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra "
          "solo el kind, que sería no reescribir."], 30)
resultado(6, "Base vectorial y query rewriting", f'''
<div class="res-2 r-6">
  <div>{barras([dict(letra="A", et="Exacta (numpy)", v=D['e6_exacta'], ic=ic(F, BASE + '|exact'), vtxt=f3(D['e6_exacta'])),
                dict(letra="B", et="ChromaDB (HNSW)", v=D['e6_hnsw'], ic=ic(F, BASE), gana=True, vtxt=f3(D['e6_hnsw']))],
               titulo="hit@1 · la base vectorial", cls="gb-compacto")}</div>
  <div>{barras([dict(letra="C", et="Consulta completa", v=D['e6_hnsw'], ic=ic(F, BASE), gana=True),
                dict(letra="D", et="Solo la línea Type", v=D['e6_type'], ic=ic(F, BASE + '|consulta-type')),
                dict(letra="E", et="Solo el kind", v=D['e6_kind'], ic=ic(F, BASE + '|consulta-kind'))],
               titulo="hit@1 · la consulta", cls="gb-compacto")}</div>
</div>
<p class="nota" data-paso="1">El estilo, los colores y la forma son lo que distingue un sofá de otro.</p>''',
          "consulta", "8 líneas", "ChromaDB con la consulta completa que escribe el plan: el query rewriting cuesta, pero "
          "<mark>vale la pena</mark>.",
          [f"HNSW da exactamente lo mismo que la búsqueda exacta ({f3(D['e6_exacta'])} y {f3(D['e6_hnsw'])}). Con solo la línea "
           f"Type, hit@1 cae a {f2(D['e6_type'])}; con solo el kind, a {f2(D['e6_kind'])}. El estilo, los colores y la forma son "
           "lo que distingue un sofá de otro.",
           "Decisión: ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena."], 35)

# =============================================================================================
# E7 · Reranking
# =============================================================================================
_b, _mi, _op = D["e7_base"], D["e7_minilm"], D["e7_opus"]


def _e7f(j, met):
    return [dict(letra="—", et="Sin reranking", v=_b[j], ic=ic(RR, BASE, met)),
            dict(letra="A", et="Cross-encoder MiniLM", v=_mi[j], ic=ic(F, BASE + '|rerank-minilm-reranker', met)),
            dict(letra="B", et="VLM (Claude Opus)", v=_op[j], ic=ic(RR, BASE + '|rerank-opus', met), gana=True)]


pregunta(7, "Reranking", "¿Un segundo modelo, que mira la consulta y cada candidato juntos, <em>ordena mejor</em>?",
         f"hit@10 daba {f2(_b[2])} pero hit@1 {f2(_b[0])}: el correcto casi siempre está entre los 10 primeros, pero no primero. "
         "El cuello de botella era el orden. Advanced RAG propone un reranker: un segundo modelo que mira la consulta y cada "
         "candidato juntos.",
         [("A", "Cross-encoder MiniLM", "entrenado en MS MARCO, local y gratis: lee la consulta y la descripción juntas"),
          ("B", "Claude Opus como VLM", "ve la consulta y las fotos de los 10 candidatos, y los ordena")],
         "los dos reordenan el mismo top-10 · hit@1 y MRR@10",
         [f"Mirando los resultados, hit@10 era {f2(_b[2])} pero hit@1 {f2(_b[0])}: el correcto casi siempre está entre los 10 "
          "primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker: un segundo modelo que "
          "mira la consulta y cada candidato juntos.",
          "Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee consulta y "
          "descripción juntas; y Claude Opus como VLM, que ve las fotos de los 10 y los ordena."], 30,
         extra='<p class="adv">Advanced RAG</p>')
resultado(7, "Reranking", f'''
<div class="res-2">
  <div>{barras(_e7f(0, "hit@1"), titulo="hit@1", cls="gb-compacto")}</div>
  <div>{barras(_e7f(1, "mrr@10"), titulo="MRR@10", cls="gb-compacto")}</div>
</div>
<p class="nota" data-paso="1">MiniLM está entrenado con preguntas y pasajes web, no con muebles. El VLM mira la foto, que tiene lo que la descripción no dijo. Cuesta unos <b>{usd(D['e7_costo'])}</b> por búsqueda.</p>''',
          "rerank", "la elección", "El reranking con VLM funciona, y nuestro paso de elección <mark>ya es eso</mark>: no agregamos "
          "un paso. La pregunta pasa a ser cuántos candidatos mostrarle.",
          [f"MiniLM empeora ({f2(_mi[0])}): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM "
           f"sube hit@1 de {f2(_b[0])} a {f2(_op[0])} y MRR de {f2(_b[1])} a {f2(_op[1])}: mira la foto, que tiene lo que la "
           f"descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda.",
           "Decisión: el reranking con VLM funciona, y nuestro paso de elección ya es eso. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento "
           "siguiente."], 40)

# =============================================================================================
# E8 · Candidatos por pieza
# =============================================================================================
_ks = sorted(D["curva"])
_ele = [D["curva"][k]["acierto_eleccion"] for k in _ks]
_tech = [D["curva"][k]["techo_hit@k"] for k in _ks]
_e3v, _e5v = D["curva"][3]["acierto_eleccion"], D["curva"][5]["acierto_eleccion"]
_plano = next(k for k in _ks if abs(D["curva"][k]["acierto_eleccion"] - max(_ele)) < 1e-9)
_e8_chart = lineas_svg(_ks, [dict(ys=_tech, clase="punt", et="techo: el correcto está entre los k", et_dy=-4),
                             dict(ys=_ele, clase="sol", et="lo que elegiría el VLM", et_dy=14)], 1420, 560, 0.5, 0.92,
                       [0.5, 0.6, 0.7, 0.8, 0.9], xlab="k: candidatos por pieza", mr=380, yfmt=f2,
                       marcas=[(3, _e3v, f"k=3: {f3(_e3v)}", 0, 46, "middle", False),
                               (5, _e5v, f"k=5: {f3(_e5v)}", 0, 46, "middle", True)])
pregunta(8, "Candidatos por pieza", "¿Cuántos candidatos <em>le mostramos al VLM</em>?",
         f"La elección ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en "
         f"el {pct(D['e8_falta3'])} de las piezas: una de cada cuatro. Más candidatos suben ese techo, pero son más fotos en la "
         "llamada: más caro, y más difícil elegir entre parecidos.",
         [("k", "De 1 a 10 candidatos", "lo que elegiría el VLM entre los primeros k = el mejor ordenado por él de esos k")],
         "sale gratis del experimento anterior · es un proxy: la elección real además ve el ambiente y el pedido",
         ["La elección ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba "
          "en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos: más caro, y más difícil elegir entre "
          "parecidos.",
          "Sale gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor "
          "ordenado de esos k. Es un proxy: la elección real además ve el ambiente y el pedido."], 30)
resultado(8, "Candidatos por pieza", f'''
<div class="r-8">{_e8_chart}</div>
<p class="nota r8-n" data-paso="1">A partir de {_plano} se aplana, y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.</p>''',
          "k", str(D["k_flujo"]), f"{D['k_flujo']} candidatos por pieza: casi toda la mejora, y la llamada queda en "
          f"<mark>{D['k_flujo'] * N_HERO} fotos</mark> para {N_HERO} piezas.",
          [f"La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 "
           f"candidatos, la elección sube de {f3(_e3v)} a {f3(_e5v)}; a partir de {_plano} se aplana. Y la distancia al techo "
           "crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.",
           f"Decisión: {D['k_flujo']} candidatos por pieza: casi toda la mejora, y la llamada queda en "
           f"{D['k_flujo'] * N_HERO} fotos para {N_HERO} piezas."], 35)

# =============================================================================================
# E9 · Catálogo: ampliación y revisión
# =============================================================================================
_e9 = D["e9"]
pregunta(9, "Ampliación y revisión", "¿Cuánto cuesta ampliar el catálogo en retrieval, <em>y qué cambia la limpieza</em>?",
         f"El primer alcance eran sofás, sillones, mesas y alfombras: {D['prod_268']} productos. Con pedidos reales, la gente "
         "pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Y al describir, los subagentes marcaron productos "
         "con la foto de otro o mal clasificados: la lista diría una cosa y la imagen mostraría otra.",
         [("A", f"{D['prod_268']} productos", "el primer alcance"),
          ("B", f"Ampliado a {D['prod_855']}", "guardado, iluminación, textiles y deco"),
          ("C", f"Revisado: {D['prod_819']}", f"{D['rev_afuera']} productos afuera y {D['rev_kinds']} kinds corregidos")],
         "las mismas métricas sobre los tres catálogos · hit@1",
         [f"El primer alcance eran sofás, sillones, mesas y alfombras: {D['prod_268']} productos. Con pedidos reales, la gente "
          "pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Y al describir, los subagentes marcaron productos "
          "con la foto de otro o mal clasificados: la lista diría una cosa y la imagen otra.",
          f"Las mismas métricas sobre tres catálogos: el de {D['prod_268']}, el ampliado a {D['prod_855']} y el revisado, con "
          f"{D['rev_afuera']} productos afuera y {D['rev_kinds']} kinds corregidos."], 30)
resultado(9, "Catálogo: ampliación y revisión", f'''
<div class="r-9">{barras([dict(letra="A", et=f"{_e9[0][0]} productos", sub="sofás, sillones, mesas, alfombras", v=_e9[0][1], ic=ic(C268, BASE)),
                         dict(letra="B", et=f"{_e9[1][0]} productos", sub="+ guardado, iluminación, textiles, deco", v=_e9[1][1], ic=ic(C855, BASE)),
                         dict(letra="C", et=f"{_e9[2][0]} productos", sub="el ampliado, revisado", v=_e9[2][1], ic=ic(CREV, BASE), gana=True)],
                        titulo="hit@1", cls="gb-9")}</div>
<p class="nota aviso" data-paso="1"><b>Ojo:</b> no son números directamente comparables. Cambia el universo, y las búsquedas ({_e9[0][2]} en A, {_e9[1][2]} en B y C): las nuevas son de deco, que es más difícil.</p>''',
          "catálogo", str(D["prod_819"]), "Catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de "
          "<mark>poder amoblar un living completo</mark>.",
          [f"Ampliar baja hit@1 de {f3(_e9[0][1])} a {f3(_e9[1][1])}: hay más productos parecidos y las búsquedas nuevas son de "
           f"deco, que es más difícil. La revisión casi no lo cambia ({f3(_e9[1][1])} a {f3(_e9[2][1])}), pero hace que el "
           "producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo.",
           "Decisión: catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living "
           "completo."], 35)

# =============================================================================================
# E10 · Qué catálogo (resultados en dos láminas)
# =============================================================================================
_ja, _jt5, _jn, _jo = D["j_abo5"], D["j_tod5"], D["j_nord"], D["j_otros"]


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


def _marcador(res, b_lbl, sub):
    return (f'<div class="marcador"><div class="mk-t"><span>IKEA</span><b>{res["a"]}</b><i>–</i><b>{res["b"]}</b><span>{b_lbl}</span></div>'
            f'<div class="mk-s">{sub}</div></div>')


pregunta(10, "Qué catálogo", "¿Con otro catálogo, o con los dos juntos, <em>salen mejores listas</em> para ambientes reales?",
         f"El catálogo de IKEA es de 2013, con fotos de {D['foto_lado']} píxeles, asientos sin medidas y una sola estética: la "
         "nórdica. Amazon Berkeley Objects (ABO) es un dataset académico con listados reales de Amazon, con medidas y fotos "
         "grandes.",
         [("A", "IKEA", f"{D['prod_819']} productos"), ("B", "Amazon (ABO)", f"{D['n_abo']} productos, descritos con el mismo formato"),
          ("C", "IKEA + Amazon", f"{D['prod_todos']} productos")],
         "sin ground truth: de punta a punta, mismos ambientes, pedidos y plan; cambia solo el catálogo. Un juez (Claude Opus) "
         "ve la foto, el pedido y las dos listas a ciegas, en los dos órdenes: gana un ambiente solo si gana en los dos",
         [f"IKEA es de 2013, con fotos de {D['foto_lado']} píxeles, asientos sin medidas y una sola estética, la nórdica. "
          "Queríamos ver si con Amazon, o con los dos juntos, salen mejores listas para ambientes reales.",
          "Acá no hay ground truth: comparamos de punta a punta, con los mismos ambientes, pedidos y plan; cambia solo el "
          "catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige, "
          "en los dos órdenes: una variante gana un ambiente solo si gana en los dos. Primero, en nuestros 5 departamentos."], 35)
resultado(10, "Qué catálogo: nuestros 5 departamentos", f'''
<div class="r-10a">
  <div class="r10-col">{_marcador(_ja, "Amazon", f"{_ja['emp']} empate · nuestros {_ja['n']} departamentos")}{_tiles(_ja, "Amazon")}</div>
  <div class="r10-col">{_marcador(_jt5, "IKEA + Amazon", f"{_jt5['emp']} empate · los mismos {_jt5['n']}")}{_tiles(_jt5, "IKEA + Amazon")}</div>
</div>
<p class="nota" data-paso="1">Según el juez, Amazon pierde por estilo: maderas oscuras, patas doradas para pedidos nórdicos. Y sumarlo no cambia nada… <b>en estos 5</b>.</p>''',
          "", "", "",
          [f"IKEA le gana a Amazon {_ja['a']} a {_ja['b']}; según el juez, Amazon pierde por estilo (maderas oscuras, patas "
           f"doradas para pedidos nórdicos). Y IKEA + Amazon empataba con IKEA, {_jt5['a']} a {_jt5['b']}.",
           "Con esto solo, la decisión habría sido quedarse con IKEA. Pero miramos los pedidos."], 30, sufijo="r1",
          kick_txt="resultados (1 de 2)")
resultado(10, "Qué catálogo: los 11 ambientes", f'''
<p class="giro">Los {_ja["n"]} pedidos eran nórdicos, justo la estética de IKEA. Sumamos {D["n_publicos"]} ambientes públicos reales con pedidos de otros estilos.</p>
<div class="r-10b" data-paso="1">
  <div class="r10-col">{_marcador(_jn, "IKEA + Amazon", f"pedidos nórdicos · {_jn['emp']} empate")}{_tiles(_jn, "IKEA + Amazon")}</div>
  <div class="r10-col">{_marcador(_jo, "IKEA + Amazon", "otros estilos: industrial, clásico, bohemio…")}{_tiles(_jo, "IKEA + Amazon")}</div>
</div>
<div class="r10-cifras" data-paso="1">
  <div><b>{f2(_jo["util_a"])} → {f2(_jo["util_b"])}</b>productos útiles (nota 2) en los otros estilos</div>
  <div><b>{pct(D["j_acuerdo"])}</b>de los ambientes: los dos órdenes del juez coinciden</div>
  <div><b>{f3(D["e10_gt_ikea"])} → {f3(D["e10_gt_todos"])}</b>hit@1 sobre el ground truth de IKEA al sumar Amazon</div>
</div>''',
          "catálogo", "IKEA + ABO", "Usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados, "
          "<mark>habríamos decidido lo contrario</mark>.",
          [f"Los {_ja['n']} pedidos eran nórdicos, justo la estética de IKEA, así que sumamos {D['n_publicos']} ambientes "
           "públicos reales con pedidos de otros estilos: industrial, clásico, bohemio.",
           f"En los nórdicos siguen empatados, {_jn['a']} a {_jn['b']}; en los otros estilos, IKEA + Amazon gana {_jo['b']} a "
           f"{_jo['a']}, y los productos útiles pasan de {f2(_jo['util_a'])} a {f2(_jo['util_b'])}. Los dos órdenes del juez "
           f"coinciden en el {pct(D['j_acuerdo'])} de los ambientes. Y sumar Amazon casi no cambia el retrieval sobre el ground "
           f"truth de IKEA: hit@1 de {f3(D['e10_gt_ikea'])} a {f3(D['e10_gt_todos'])}.",
           "Decisión: usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión "
           "contraria."], 35, sufijo="r2", kick_txt="resultados (2 de 2)")

# =============================================================================================
# E11 · ¿Cuánto mide el ground truth?
# =============================================================================================
_rep = D["rep"]


def _rep_svg():
    W, x0, x1, lo, hi = 1600, 420, 1460, 0.45, 0.62
    sx = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)  # noqa: E731
    mu = statistics.mean(_rep)
    o = [f'<svg class="graf-l rep" viewBox="0 0 {W} 120" width="{W}" height="120">',
         '<text x="0" y="58" class="rep-et">Tres redactores</text><text x="0" y="86" class="gl-eje">hit@1 de cada uno</text>',
         f'<line x1="{x0}" y1="56" x2="{x1}" y2="56" class="gl-grilla"/>']
    for t in (0.45, 0.5, 0.55, 0.6):
        o.append(f'<line x1="{sx(t)}" y1="46" x2="{sx(t)}" y2="66" class="gl-grilla"/><text x="{sx(t)}" y="100" class="gl-eje" text-anchor="middle">{f2(t)}</text>')
    o.append(f'<g data-paso="1"><rect x="{sx(mu - D["rep_sd"])}" y="38" width="{sx(mu + D["rep_sd"]) - sx(mu - D["rep_sd"])}" height="36" class="gl-banda"/>')
    o += [f'<circle cx="{sx(v)}" cy="56" r="11" class="rep-p"/>' for v in _rep]
    o.append(f'<text x="{sx(mu)}" y="24" class="rep-t" text-anchor="middle">± {f1(D["rep_sd"] * 100)} puntos (desvío)</text></g></svg>')
    return "".join(o)


pregunta(11, "Cuánto mide el ground truth", "Si el sistema trae un sillón casi igual al anotado, <em>¿se equivocó?</em>",
         "Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Y las búsquedas de "
         "evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número?",
         [("A", f"Un juez califica el top-3 de {D['g_n']} búsquedas", "2 el mismo o indistinguible, 1 alternativa aceptable, 0 no sirve; antes, lo validamos contra el ground truth"),
          ("B", "Tres redactores independientes", "escriben las mismas búsquedas")],
         "acuerdo del juez con el anotado · útil@1 contra hit@1 · dispersión entre redactores",
         ["Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae "
          "un sillón casi igual al anotado, ¿se equivocó? Y si las búsquedas de evaluación las escribiera otro, ¿cambiaría el "
          "número?",
          f"Un juez califica el top-3 de {D['g_n']} búsquedas con la escala de 2, 1 y 0 que vimos; antes, lo validamos contra el "
          "ground truth. Y tres redactores independientes escribieron las mismas búsquedas."], 30)
resultado(11, "¿Cuánto mide el ground truth?", f'''
<div class="res-2 r-11">
  <div>{barras([dict(et="Al producto anotado", v=D['g_anot2'], vtxt=pct(D['g_anot2']), gana=True),
                dict(et="A los demás", v=D['g_otros2'], vtxt=pct(D['g_otros2']))],
               titulo="validación: ¿cuántas veces el juez pone un 2?", fmt=pct, tick_fmt=lambda t: f"{round(t * 100)}%", cls="gb-compacto")}</div>
  <div>{barras([dict(et="hit@1 (ground truth)", v=D['g_hit1'], ic=D['g_hit1_ic']),
                dict(et="El 1.º sirve (1 o 2)", v=D['g_util1'], ic=D['g_util1_ic'], gana=True)],
               titulo=f"las mismas {D['g_n']} búsquedas: el ground truth subestima", cls="gb-compacto")}</div>
</div>
<div class="r11-rep">{_rep_svg()}</div>''',
          "métrica", "hit@1 + juez", "Reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia "
          "graduada para saber <mark>cuán útil es de verdad</mark>.",
          [f"El juez le da 2 al producto anotado el {pct(D['g_anot2'])} de las veces y a los demás el {pct(D['g_otros2'])}: es "
           f"confiable. Con él, el primer candidato sirve en el {pct(D['g_util1'])} de los casos, aunque hit@1 "
           f"sea {f2(D['g_hit1'])}: el ground truth subestima. Con tres redactores, hit@1 varía unos "
           f"{f1(D['rep_sd'] * 100)} puntos: diferencias más chicas que eso entre métodos no son señal.",
           "Decisión: reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber "
           "cuán útil es de verdad."], 40)

# =============================================================================================
# E12 · La imagen
# =============================================================================================
E12_VAR = [("A", "experimento", "Escena guiada", "el LLM describe dónde va cada cosa"),
           ("B", "experimento-libre", "Escena libre", "el modelo de imagen acomoda"),
           ("C", "experimento-buen-pedido", "Libre y sin tope de piezas", "todas las piezas del pedido"),
           ("D", "experimento-buen-pedido-estricto", "Edición estricta", "mismo encuadre, paredes y aberturas; solo los productos de las fotos")]
_cards = []
for l, run, t, _d in E12_VAR:
    inl, ssim = D["e12"][run]
    mal = inl < ROOM_CHECK["min_inliers"]
    _cards.append(f'<figure class="e12-c{" mal" if mal else ""}"{" data-gana=2" if l == "D" else ""}>'
                  f'{foto("e12-" + run, AM / run / "final.png", 400, 300, q=78)}'
                  f'<figcaption>{letra(l)}<span class="e12-t"><b>{t}</b><i>{D["e12_piezas"][run]} piezas</i></span>'
                  f'<span class="e12-v" data-paso="1"><b>{inl}</b> puntos SIFT<i>SSIM {f2(ssim)}</i></span></figcaption>'
                  f'{"<span class=e12-sello data-paso=1>cambió el cuarto</span>" if mal else ""}</figure>')
pregunta(12, "La imagen", "¿Cómo pedirle al modelo que <em>respete el ambiente</em>, y cómo detectar cuándo no lo hace?",
         "Al generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. Para el usuario eso no sirve: quiere "
         "ver su cuarto con esos productos.",
         [(l, t, d) for l, _, t, d in E12_VAR],
         f"A y B: pedido corto ({D['e12_piezas']['experimento']} piezas) · C y D: completo ({D['e12_piezas']['experimento-buen-pedido']}, "
         "sin tope) · puntos SIFT y SSIM fuera de los muebles",
         ["Cuando empezamos a generar imágenes, el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una "
          "ventana y movió la biblioteca. El usuario quiere ver su cuarto con esos productos: había que pedirle al modelo que "
          "respete el ambiente, y detectar cuándo no lo hace.",
          "El mismo ambiente, cuatro versiones del paso de la imagen: la escena guiada que escribe el LLM, la escena libre, libre "
          "y sin tope de piezas, y la edición estricta. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y "
          "SSIM fuera de los muebles."], 35,
         extra=f'''<div class="e12-motivo">{foto("hero-room-e12", HERO / "room.jpg", 176, 132)}<span class="v-fl">→</span>
         {foto("e12-bp-sm", AM / "experimento-buen-pedido" / "final.png", 176, 132)}<span class="e12-mt">inventó una ventana y movió la biblioteca</span></div>''', cls="denso")
resultado(12, "La imagen: del cuarto reimaginado al cuarto del cliente", f'''
<div class="e12-grilla">{"".join(_cards)}</div>
<p class="nota e12-n" data-paso="1">C, libre y sin tope: linda, pero inventó una ventana, y SIFT lo detecta. D conserva el cuarto, y la biblioteca es la que se pidió.</p>''',
          "imagen", "estricta", f"Edición estricta y un control: si SIFT no reencuentra el cuarto (al menos "
          f"{ROOM_CHECK['min_inliers']} puntos), la imagen se descarta y <mark>se reintenta</mark>, hasta {ROOM_CHECK['attempts']} veces.",
          [f"Las dos primeras conservan el cuarto ({D['e12']['experimento'][0]} y {D['e12']['experimento-libre'][0]} puntos) "
           f"pero la biblioteca queda chica. La tercera, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, "
           f"reencuentra solo {D['e12']['experimento-buen-pedido'][0]} puntos. La edición estricta conserva el cuarto, con "
           f"{D['e12']['experimento-buen-pedido-estricto'][0]} puntos, y la biblioteca es la que se pidió.",
           f"Decisión: edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se "
           f"reintenta, hasta {ROOM_CHECK['attempts']} veces. Es el control que vimos en el recorrido."], 45)

# =============================================================================================
# E13 · Réplica de un living real: cómo decirle al generador dónde va cada mueble.
# Ronda 2: seis variantes con un prompt corto común (cambia una línea); la ronda 1 (prompt largo)
# queda como referencia en la tabla. Todo sale de resultados.json, del yaml de la réplica y de los
# prompts: si el texto enviado no coincide con su plantilla, el build falla.
# =============================================================================================
_RV = REPLICA["variantes"]
_CFG13 = yaml.safe_load((ROOT / "datos" / "configs" / "imagen" / "replica.yaml").read_text())
_vac = REPLICA["vaciado"]
_v2 = next(t for t in _vac["intentos"] if t["imagen"] == _vac["elegido"])
_n_int, _i_eleg = len(_vac["intentos"]), _vac["intentos"].index(_v2) + 1
_reps = len(_RV["simple_cajas_3d"]["imagenes"])
_CON_CAJAS = {v for v, c in _CFG13["variantes"].items() if c.get("cajas")}
_R2 = {v: (l_, n_, d_) for v, l_, n_, d_ in REPL_R2}


def _iou(v):
    return _RV[v]["resumen"]["iou_medio"]["media"]


def _lug(v):
    return _RV[v]["resumen"]["en_su_lugar"]["media"]


def _dib(v):
    return [cajas_dibujadas(r["imagen"]) for r in _RV[v]["imagenes"]]


for _v in _CON_CAJAS:
    assert None not in _dib(_v), f"réplica: falta la observación de si quedaron cajas dibujadas en {_v}"


def _dicho(x):
    """Un número para decir en voz alta: 4 en lugar de 4,0."""
    return str(round(x)) if abs(x - round(x)) < 1e-9 else f1(x)


def _ndib(v):
    return sum(1 for d in _dib(v) if d)


def _dib_txt(v):
    return f"{_ndib(v)} de {len(_dib(v))}" if v in _CON_CAJAS else "—"


# lo que se dice en las láminas, comprobado contra los datos
_todas = [v for v, *_ in REPL_R1 + REPL_R2]
assert max(_todas, key=_iou) == "simple_cajas_3d" and _ndib("simple_cajas_3d") == 0
assert _iou("simple_cajas") >= _iou("con_cajas") and _iou("simple_cajas_3d") >= _iou("con_cajas_3d")  # el corto no empeora
assert 1.6 < _iou("simple_texto") / _iou("simple_sin_cajas") < 2.0  # «casi duplica»
assert _lug("simple_texto") < min(_lug("simple_cajas"), _lug("simple_cajas_3d"))
assert _iou("simple_cajas_guia") < _iou("simple_cajas") and _iou("simple_cajas_3d_guia") < _iou("simple_cajas_3d")
assert _ndib("simple_cajas_guia") == _ndib("simple_cajas_3d_guia") == 1  # «una de cada tres, en las dos»

# los prompts: la plantilla llena tiene que ser el texto enviado (prompt.txt de cada variante)
_PR13 = {v: _CFG13["variantes"][v]["prompt"] for v in _R2}
_ENV13 = {}
for _v, _nom in _PR13.items():
    _t = (cuerpo_prompt(_nom).replace("{last}", str(REPL_N + 1)).replace("{guide}", str(REPL_N + 2))
          .replace("{request}", REPLICA["pedido"]))
    _pre, _post = _t.split("{products}")
    _env = (REPL / _v / "prompt.txt").read_text().rstrip("\n")
    assert _env.startswith(_pre) and _env.endswith(_post.rstrip("\n")), f"{_v}: prompt.txt no es {_nom} lleno"
    _linea, _cola = _post.strip("\n").split("\n\n", 1)
    _ENV13[_v] = dict(texto=_env, linea=_linea, cabeza=_pre, cola=_cola,
                      productos=_env[len(_pre):len(_env) - len(_post.rstrip("\n"))].splitlines())
assert len({e["cabeza"] for e in _ENV13.values()}) == 1 and len({e["cola"] for e in _ENV13.values()}) == 1
_prods_base = _ENV13["simple_sin_cajas"]["productos"]
for _v, _e in _ENV13.items():
    if _v == "simple_texto":
        for _p, _l0, _l in zip(sorted(REPLICA["productos"], key=lambda p: p["imagen"]), _prods_base, _e["productos"]):
            assert _l == f"{_l0}. Where: {REPLICA['lugares'][_p['id']]}", _p["id"]
    else:
        assert _e["productos"] == _prods_base, _v

# la línea que cambia, con lo importante resaltado
_HL13 = {"simple_sin_cajas": "where an interior designer would", "simple_texto": "where its line says",
         "simple_cajas": "Then remove the rectangles and numbers", "simple_cajas_guia": "only a guide: do not draw its rectangles or numbers",
         "simple_cajas_3d": "Then remove the boxes and numbers", "simple_cajas_3d_guia": "only a guide: do not draw its boxes or numbers"}


def _marca13(txt, hl):
    assert hl in txt, (hl, txt)
    return esc(txt).replace(esc(hl), f'<mark class="hl">{esc(hl)}</mark>', 1)


# en palabras: la línea de la estantería, tal cual va en el prompt de B
_id_est = next(k for k, n in REPL_CORTO.items() if n == "estantería")
_img_est = next(p["imagen"] for p in REPLICA["productos"] if p["id"] == _id_est)
_lin_est = next(l for l in _ENV13["simple_texto"]["productos"] if l.startswith(f"image {_img_est}:"))
_lug_est = REPLICA["lugares"][_id_est]
_cita_lug = "so that someone who only sees image 2 can put it in the same place"
assert _cita_lug in cuerpo_prompt(_CFG13["prompt_lugares"])
_n1, _n3 = _ndib("con_cajas"), _ndib("con_cajas_3d")

# --- la pregunta (oscura) --------------------------------------------------------------------
def _v13(v, nombre=None, det=None):
    l_, n_, d_ = _R2[v]
    return f'<div class="r13-v">{letra(l_)}<div><b>{nombre or n_}</b><span>{det or d_}</span></div></div>'


_grid13 = f'''<div class="r13-grid">
  <div class="r13-col"><div class="r13-cab">{foto("r13-in-0", REPL / "vacio.png", 246, 154, q=76)}<b>sin cajas</b><span>la foto vacía, limpia</span></div>
    {_v13("simple_sin_cajas")}{_v13("simple_texto", det="una o dos frases por mueble, escritas por Opus")}</div>
  <div class="r13-col"><div class="r13-cab">{foto("r13-in-2d", REPL / "vacio_con_cajas.png", 246, 154, q=76)}<b>cajas 2D</b><span>un rectángulo por mueble</span></div>
    {_v13("simple_cajas", "En la foto", "dibujadas; que las borre")}{_v13("simple_cajas_guia", "Aparte", "una copia de la foto con las cajas, como guía")}</div>
  <div class="r13-col"><div class="r13-cab">{foto("r13-in-3d", REPL / "vacio_con_cajas_3d.png", 246, 154, q=76)}<b>cajas 3D</b><span>un prisma en perspectiva</span></div>
    {_v13("simple_cajas_3d", "En la foto", "dibujadas; que las borre")}{_v13("simple_cajas_3d_guia", "Aparte", "una copia de la foto con las cajas, como guía")}</div>
</div>'''
_r1img = next(r["imagen"] for r in _RV["con_cajas"]["imagenes"] if cajas_dibujadas(r["imagen"]))
_tira13 = f'''<div class="r13-r1">
  <figure>{foto("r13-real-s", ROOT / REPLICA["foto"], 208, 130, q=76)}<figcaption>la foto real</figcaption></figure><i>→</i>
  <figure>{foto("r13-vac-s", REPL / "vacio.png", 208, 130, q=76)}<figcaption>vaciada (intento {_i_eleg} de {_n_int})</figcaption></figure><i>→</i>
  <figure>{foto("r13-r1-s", REPL / _r1img, 208, 130, q=76)}<em>cajas dibujadas</em><figcaption>ronda 1 · cajas 2D</figcaption></figure>
  <p>ronda 1, prompt largo: cajas dibujadas en {_n1} de 3 con rectángulos y {_n3} de 3 con cajas 3D</p>
</div>'''
pregunta(13, "Réplica de un living real", "¿Cómo decirle al generador <em>dónde va cada mueble</em>?",
         f"Un living del ground truth tiene con qué comparar: la foto real. La vaciamos y la volvimos a amoblar con sus "
         f"{REPL_N} muebles. En una primera ronda los ponía todos, pero armaba su propio living; con cajas dibujadas en la "
         "foto ubicaba mejor, pero las dejaba dibujadas. Y los prompts eran largos.",
         _grid13,
         f"un prompt corto, igual en las seis salvo una línea · {_reps} imágenes por variante · IoU de cada mueble con su caja "
         "en la foto real; en su lugar si es 0,5 o más",
         [f"Un living del ground truth, a diferencia de un ambiente vacío, tiene con qué comparar: la foto real. "
          f"La vaciamos y la volvimos a amoblar con sus {REPL_N} muebles. En una primera ronda los ponía todos, pero armaba su "
          f"propio living. Con cajas dibujadas en la foto los ubicaba mejor, pero las dejaba dibujadas: {_n1} de 3 imágenes con "
          "rectángulos. Y los prompts eran largos.",
          f"En la segunda ronda, seis formas de decirle dónde va cada mueble: no decirlo, decirlo en palabras, o cajas, "
          f"rectángulos o 3D, dibujadas en la foto o en una copia aparte, como guía, con {_reps} imágenes por variante; "
          "un mueble está en su lugar si el IoU de su caja con la real es 0,5 o más."],
         45, cls="denso r13-izq", fuera=_tira13)

# --- los prompts (oscura): uno entero y la línea que cambia en cada uno ------------------------
_tA = _ENV13["simple_sin_cajas"]["texto"]
_filas13 = "".join(
    f'<li>{letra(_R2[v][0])}<div><b>{_R2[v][1]}</b><p>{_marca13(_ENV13[v]["linea"], _HL13[v])}</p></div></li>' for v in _R2)
lam("e13p", "Exp. 13: los prompts", "Experimentos · 13", f'''
{kick("E13", "experimento 13 · los seis prompts")}
<h2 class="t chico">Un prompt corto para las seis: <em>cambia una línea</em></h2>
<div class="p13">
  <div class="p13-izq">
    {prompt_tk(_PR13["simple_sin_cajas"], [(_tA.splitlines()[0], _tA[-40:])], resaltar=[_ENV13["simple_sin_cajas"]["linea"]],
               texto=_tA, titulo=f'{_PR13["simple_sin_cajas"]} · lleno', rotulo="A, entero, tal cual se mandó", cls="p13-tk")}
    <div class="p13-b" data-paso="1"><span class="et">B · en palabras: cada producto lleva dónde va</span>
      <div class="pr-tk p13-ej"><pre class="pr-tx">{_marca13(_lin_est, "Where: " + _lug_est)}</pre></div>
      <p>Las frases las escribió <b>Opus 5.5</b>, en una llamada, mirando la foto real y la vaciada ({esc(_CFG13["prompt_lugares"])}:
      «{esc(_cita_lug)}»). Mide si alcanza con decirlo en palabras, <b>no si un LLM sabe dónde va cada mueble</b>.</p>
    </div>
  </div>
  <div class="p13-der"><span class="et">la línea que cambia, en cada una · tal cual se mandó</span>
    <ol class="pr-tk p13-l">{_filas13}</ol>
  </div>
</div>''',
    ["Los seis prompts son cortos y dicen qué hacer: agregar estos productos al cuarto de la imagen 1, el pedido, la lista, y "
     "que el cuarto quede igual. Cambia una sola línea, la de dónde va cada mueble. Sin decirlo: donde lo pondría un "
     "diseñador. Con cajas en la foto: cada producto llena su caja, y después hay que borrarlas. Con la guía: la imagen 8 es "
     "solo una guía, no dibujes sus cajas. Rehicimos también las de la primera ronda, para no mezclar el largo del prompt "
     "con la forma de decir dónde.",
     "En palabras, cada producto lleva una o dos frases de dónde va. Las escribió Opus mirando la foto real: mide si alcanza "
     "con decirlo en palabras, no si un LLM sabe decidir dónde van los muebles."],
    50)

# --- los resultados (clara) --------------------------------------------------------------------
_XM = 0.6
_tk13 = (0, 0.2, 0.4, 0.6)


def _fila13(v, l_, nombre, cls=""):
    g = ' data-gana="2"' if v == "simple_cajas_3d" else ""
    grilla = "".join(f'<i style="left:{t / _XM * 100:.1f}%"></i>' for t in _tk13)
    return (f'<div class="r13-f {cls}"{g}><span class="r13-n">{letra(l_) if l_ else ""}{nombre}</span>'
            f'<span class="gb-pista">{grilla}<b class="gb-lleno" data-paso="1" style="--v:{_iou(v) / _XM * 100:.2f}%"></b></span>'
            f'<span class="r13-x" data-paso="1">{f2(_iou(v))}</span><span class="r13-x" data-paso="1">{f1(_lug(v))}</span>'
            f'<span class="r13-x d{" no" if v in _CON_CAJAS and _ndib(v) else ""}" data-paso="1">{_dib_txt(v)}</span></div>')


def _mediana13(v):
    ims = sorted(_RV[v]["imagenes"], key=lambda r: r["iou_medio"])
    return ims[len(ims) // 2]


def _obs13(img, debe):
    o = REPLICA["observaciones"][img]
    assert debe in o, (img, debe, o)
    return o


_im_3d, _im_tx = _mediana13("simple_cajas_3d"), _mediana13("simple_texto")
_im_gu = next(r for r in _RV["simple_cajas_guia"]["imagenes"] if cajas_dibujadas(r["imagen"]))
assert _im_gu is _mediana13("simple_cajas_guia")  # las tres de ejemplo son la del medio de su variante
_obs13(_im_3d["imagen"], "en sus cajas"), _obs13(_im_tx["imagen"], "el sofá mira a la cámara"), _obs13(_im_gu["imagen"], "copia los rectángulos")
_ejes13 = "".join(f'<span style="left:{t / _XM * 100:.1f}%">{"0" if t == 0 else f2(t)}</span>' for t in _tk13)


def _fig13(clave, src, l_, nombre, det, r=None, sello=""):
    num = f'<small class="r13-num">IoU {f2(r["iou_medio"])} · {r["en_su_lugar"]}/{REPL_N}</small>' if r else ""
    return (f'<figure class="r13-im">{foto(clave, src, 328, 206, q=78)}{f"<i>{sello}</i>" if sello else ""}'
            f'<figcaption class="{"" if l_ else "sin-l"}">{letra(l_) if l_ else ""}<b>{nombre}</b>{num}<span class="r13-det">{det}</span>'
            f'</figcaption></figure>')


resultado(13, "Dónde va cada mueble: <em>seis formas de decirlo</em>", f'''
<div class="r13">
  <div class="r13-t">
    <div class="r13-f cab"><span></span><span class="r13-eje">{_ejes13}</span><span>IoU</span><span>en su lugar (de {REPL_N})</span><span>cajas dibujadas</span></div>
    <div class="r13-g">ronda 1 · prompt largo · de referencia</div>
    {"".join(_fila13(v, "", n_, "r1") for v, _, n_, _ in REPL_R1)}
    <div class="r13-g">ronda 2 · prompt corto · {_reps} imágenes cada una</div>
    {"".join(_fila13(v, l_, n_) for v, l_, n_, _ in REPL_R2)}
    <p class="r13-pie" data-paso="1">en su lugar: IoU de 0,5 o más con su caja real · las imágenes: de cada variante, la del medio de las {_reps}</p>
  </div>
  <div class="r13-ims" data-paso="1">
    {_fig13("r13-real", ROOT / REPLICA["foto"], "", "La foto real", "de acá salen las cajas reales")}
    {_fig13("r13-ej-3d", REPL / _im_3d["imagen"], "E", "Cajas 3D en la foto", "cada mueble en su caja, y limpia", _im_3d)}
    {_fig13("r13-ej-tx", REPL / _im_tx["imagen"], "B", "En palabras", "estantería y lámpara donde dice el texto; el sofá mira a la cámara", _im_tx)}
    {_fig13("r13-ej-gu", REPL / _im_gu["imagen"], "D", "Cajas 2D aparte", "copió los rectángulos de la guía", _im_gu, "cajas dibujadas")}
  </div>
</div>''', "dónde", "cajas 3D", "El flujo no cambia: <b>sin medidas del cuarto no hay cajas</b>. Para el paso a futuro, <mark>cajas 3D "
          "dibujadas en la foto</mark> y el prompt corto; la guía aparte, descartada.",
          ["Arriba, la primera ronda, de referencia; abajo, las seis nuevas.",
           f"El prompt corto no empeora nada: con rectángulos da {f2(_iou('simple_cajas'))} y con cajas 3D "
           f"{f2(_iou('simple_cajas_3d'))}, contra {f2(_iou('con_cajas'))} y {f2(_iou('con_cajas_3d'))}; con tres imágenes, eso es "
           f"ruido. En palabras casi duplica el IoU de no decir nada, de {f2(_iou('simple_sin_cajas'))} a "
           f"{f2(_iou('simple_texto'))}, y no deja nada que borrar, pero pocos muebles quedan justo en su lugar: "
           f"{f1(_lug('simple_texto'))} de {REPL_N}. La guía aparte no sirvió: ubica peor que las cajas en la foto, y una de cada "
           "tres igual quedó con cajas dibujadas, como esta. La mejor, cajas 3D en la "
           f"foto: {f2(_iou('simple_cajas_3d'))}, {_dicho(_lug('simple_cajas_3d'))} de {REPL_N} en su lugar, y ninguna quedó dibujada.",
           "Decisión: el flujo no cambia, porque sin medidas del cuarto no hay cajas. A futuro, con el cuarto "
           "medido, cajas 3D dibujadas en la foto y el prompt corto; la guía aparte se descarta. Hoy, sin medir nada, se podría "
           "probar que el plan diga en palabras dónde va cada mueble; ahí lo decidiría el LLM, sin foto que copiar. Es "
           "una habitación y tres imágenes por variante: una prueba, no una medición."], 70,
          rotulo="a futuro")
