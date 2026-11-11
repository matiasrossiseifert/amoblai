"""Los trece experimentos. Cada uno: una lámina oscura con la pregunta (por qué y el experimento,
con la etapa encendida en el flujo) y una clara con los resultados y la decisión (el talón).
Los experimentos 4 y 5 van en una sola lámina."""

from __future__ import annotations

import statistics

from datos import (AM, BASE, C268, C855, CREV, D, ESTILO, F, HERO, ITEMS, N_HERO, REPL, REPL_CORTO, REPL_N, REPLICA,
                   ROOM_CHECK, ROOT, RR, esc, f1, f2, f3, ic, pct, usd)
from piezas import ETAPA_EXP, barras, flujo, foto, kick, letra, lineas_svg, minimapa, producto, talon, variantes_html
from registro import lam

ETAPA_TXT = {1: "descripción", 2: "índice", 3: "búsqueda", 4: "índice", 5: "índice", 6: "índice y plan", 7: "elección",
             8: "búsqueda y elección", 9: "catálogo", 10: "catálogo", 11: "cómo medimos la búsqueda",
             12: "escena, imagen y control", 13: "imagen"}


def pregunta(n, tema, titulo, porque, variantes, metrica, notas, seg, extra="", ancho_t="", cls=""):
    """Lámina oscura: el porqué (paso 0) y el experimento (paso 1), con el flujo a la derecha."""
    lam(f"e{n}", f"Exp. {n}: {tema}", f"Experimentos · {n}", f'''
<div class="izq {cls}">
  {kick(f"E{n}", f"experimento {n} de 13 · {ETAPA_TXT[n]}")}
  <h2 class="t chico {ancho_t}">{titulo}</h2>
  <p class="porque">{porque}</p>
  {extra}
  <div class="exp-blq" data-paso="1">
    <span class="et">el experimento</span>
    {variantes_html(variantes)}
    <p class="metrica">{metrica}</p>
  </div>
</div>
<div class="esq">{flujo(pines=[n])}</div>''', notas, seg, focos=[" ".join(ETAPA_EXP[n])])


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
         ["Lo primero que miramos fue qué texto trae el catálogo. IKEA tiene nombre, tipo, colores y una frase de marketing del "
          "estilo «The armchair is lightweight and easy to move». Pero nadie pide así: se pide un sillón nórdico, de madera "
          "clara, con tapizado crema, y todo eso está en la foto. La pregunta era si alcanzaba con el texto del vendedor o si "
          "valía la pena describir cada producto mirando su foto, un costo que se paga una sola vez.",
          f"Indexamos tres textos y corrimos las mismas {D['n_respondibles']} búsquedas del ground truth, con todo lo demás "
          "fijo (Qwen3, filtro): el texto del vendedor; la descripción de 8 líneas que escribe un VLM mirando la foto, en el "
          "mismo formato en que el plan escribe la consulta; y esa descripción con el nombre comercial adelante."],
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
         ["El plan sabe qué pieza está buscando: un sofá, una lámpara. Por similitud sola, una mesa nórdica de madera clara se "
          "puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita y es gratis, pero tiene un riesgo: si el "
          "plan y el catálogo no coinciden en la categoría, el producto correcto queda afuera. Queríamos ver si conviene "
          "filtrar, y con qué granularidad.",
          f"Tres opciones: sin filtro; filtro por tipo, {D['n_tipos']} categorías gruesas como sofá, mesa o lámpara; y filtro "
          f"por kind, {D['n_kinds']} categorías finas como mesa ratona o mesa de comedor. En ChromaDB el filtro va como where. "
          "Miramos hit@1 y sobre todo hit@10."], 30)
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
           "ratona, el filtro fino la deja afuera. El de tipo protege de los errores gruesos sin ese costo.",
           "Decisión: filtrar siempre, más las medidas máximas que estima el plan. El flujo filtra por los kinds que elige el "
           "plan, que puede dar más de uno para no dejar afuera al correcto; contra el filtro por tipo la diferencia en hit@1 "
           "está dentro del intervalo, y pasarlo a tipo es lo próximo que probaríamos."], 35)


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
      [f"En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos, de "
       f"{D['palabras_lo']} a {D['palabras_hi']} palabras, pero tienen 8 líneas con roles distintos: tipo, estilo, colores, "
       "materiales. La hipótesis era que comparar línea por línea, colores contra colores, podía ser más preciso que un solo "
       "vector por producto.",
       "Tres formas: un documento por producto, con las 8 líneas juntas; un chunk por línea, donde el producto vale lo que su "
       "línea más parecida a la consulta; y línea contra línea, cada una contra la del mismo rótulo en la consulta, promediado.",
       f"Gana un documento por producto ({f2(_e4['whole'])}). Línea contra línea queda cerca ({f2(_e4['aligned'])}) y el chunk "
       f"por línea se desploma ({f2(_e4['max'])}): una línea suelta como «Colors: light wood» se parece a cualquier cosa de "
       "madera clara. Partir pierde el contexto.",
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
      [f"Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede "
       f"truncar sin reentrenar. Con {D['prod_819']} productos no importa, pero en un catálogo de millones la memoria y la "
       "latencia crecen con la dimensión. Queríamos saber cuánto se puede achicar sin perder.",
       "Truncamos los vectores a 32, 64, 128, 256, 512 y 1024 componentes, los renormalizamos y corrimos las mismas búsquedas.",
       f"Con 512 da prácticamente lo mismo que con 1024 ({f2(_v[512])} contra {f2(_v[1024])}), con la mitad de memoria. Por "
       f"debajo de 128 cae rápido: con 32, {f2(_v[32])}.",
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
         ["Dos dudas. Primero, pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que "
          "verificar que no perdiera resultados. Segundo, el query rewriting: el plan escribe para cada pieza el producto ideal "
          "en 8 líneas, y eso cuesta tokens y latencia en cada pedido. Queríamos ver si una consulta más corta alcanzaba.",
          "ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra "
          "solo el nombre del kind, que sería no reescribir."], 30)
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
         [f"Mirando los resultados vimos que hit@10 era {f2(_b[2])} pero hit@1 {f2(_b[0])}: el producto correcto casi siempre "
          "está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker, un "
          "segundo modelo que mira la consulta y cada candidato juntos. Queríamos ver si eso ordena mejor, y con qué tipo de "
          "modelo.",
          "Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee la consulta y la "
          "descripción juntas; y Claude Opus como VLM, que ve la consulta y las fotos de los 10 candidatos y los ordena."], 30,
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
           "Decisión: el reranking con VLM funciona, y nuestro paso de elección ya es eso: Claude elige mirando las fotos de los "
           "candidatos. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento "
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
          "en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más "
          "difícil elegir entre muchos parecidos. Queríamos encontrar el k que maximiza la chance de que el VLM elija bien.",
          "Lo sacamos gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el "
          "mejor ordenado de esos k. Así sale la curva para k de 1 a 10 sin pagar nada más. Es un proxy: la elección real además "
          "ve el ambiente y el pedido."], 30)
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
          "pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Así que ampliamos. Y mientras los subagentes "
          "describían los productos, marcaron varios con la foto de otro producto o mal clasificados: la lista diría una cosa y "
          "la imagen mostraría otra. Queríamos saber cuánto cuesta ampliar en retrieval y qué cambia la limpieza.",
          f"Las mismas métricas sobre tres catálogos: el de {D['prod_268']}, el ampliado a {D['prod_855']} (guardado, "
          f"iluminación, textiles y deco) y el revisado, con {D['rev_afuera']} productos afuera y {D['rev_kinds']} kinds "
          "corregidos."], 30)
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
         [f"El catálogo de IKEA tiene límites: es de 2013, las fotos son de {D['foto_lado']} píxeles, los asientos no tienen "
          "medidas y tiene una sola estética, la nórdica. Encontramos Amazon Berkeley Objects, un dataset académico con listados "
          "reales de Amazon, con medidas y fotos grandes. Queríamos ver si con otro catálogo, o con los dos juntos, salen mejores "
          "listas para ambientes reales.",
          "Acá no hay ground truth: nadie anotó qué sofá de Amazon va en un living vacío. Comparamos de punta a punta: mismos "
          "ambientes, mismos pedidos y el mismo plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las "
          "dos listas sin saber de qué catálogo es cada una, y elige. Se le pregunta en los dos órdenes, y una variante gana un "
          "ambiente solo si gana en los dos. Primero, en nuestros 5 departamentos."], 35)
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
          "un sillón casi igual al anotado, ¿se equivocó? Y las búsquedas de evaluación las escribieron subagentes: si las "
          "escribiera otro, ¿cambiaría el número? Queríamos saber cuánto mide realmente el ground truth.",
          f"Dos cosas. Un juez califica el top-3 de {D['g_n']} búsquedas: 2 si es el mismo o indistinguible, 1 si es una "
          "alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth. Y tres redactores "
          "independientes escribieron las mismas búsquedas."], 30)
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
           f"confiable. Con él, el primer candidato sirve en el {pct(D['g_util1'])} de los casos, aunque hit@1 en esas mismas "
           f"búsquedas sea {f2(D['g_hit1'])}: el ground truth subestima. Con tres redactores, hit@1 varía unos "
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
         ["Cuando empezamos a generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. En este ejemplo "
          "inventó una ventana y movió la biblioteca. Para el usuario eso no sirve: quiere ver su cuarto con esos productos. "
          "Queríamos encontrar cómo pedirle al modelo que respete el ambiente, y cómo detectar automáticamente cuando no lo hace.",
          "El mismo ambiente, cuatro versiones del paso de la imagen: una escena que escribe el LLM diciendo dónde va cada "
          "cosa; una escena libre; libre y sin tope de piezas; y una edición estricta, que exige el mismo encuadre, las mismas "
          "paredes y aberturas y solo los productos de las fotos. Medimos con SIFT cuántos puntos de la foto original se "
          "reencuentran, y SSIM fuera de los muebles."], 35,
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
           f"reintenta, hasta {ROOM_CHECK['attempts']} veces. En el cierre se ve funcionando."], 45)

# =============================================================================================
# E13 · Réplica de un living real
# =============================================================================================
_sv = REPLICA["variantes"]["sin_cajas"]
_s = _sv["resumen"]
_vac = REPLICA["vaciado"]
_v2 = next(t for t in _vac["intentos"] if t["imagen"] == _vac["elegido"])
_n_int = len(_vac["intentos"])
_i_eleg = _vac["intentos"].index(_v2) + 1
_reps = len(_sv["imagenes"])
pregunta(13, "Réplica de un living real", "¿El generador reproduce un ambiente real <em>si sabe qué muebles van</em>?",
         "En los ambientes vacíos no hay con qué comparar la imagen: nadie sabe cómo «debería» quedar. Un living del ground "
         "truth sí lo tiene: la foto real y sus productos anotados. Queríamos medir el generador solo, con la lista ya decidida.",
         [("1", "Vaciar la foto real", f"con el mismo modelo de imagen ({_n_int} intentos; queda el {_i_eleg}.º)"),
          ("2", "Volver a amoblarla", f"con sus {REPL_N} muebles anotados y el paso de imagen del flujo, {_reps} veces"),
          ("3", "Comparar con la real", "dónde quedó cada mueble (IoU de su caja con la real) y si es el producto (coseno DINOv3)")],
         "una sola habitación: es una prueba, no una medición",
         ["En los ambientes vacíos no tenemos con qué comparar la imagen: nadie sabe cómo debería quedar. Pero un living del ground truth sí lo tiene: la foto real, y la "
          "lista de sus productos. Queríamos medir el generador solo, con la lista ya decidida, sin el retrieval en el medio.",
          f"Vaciamos la foto real con el mismo modelo de imagen: el primer intento abrió el encuadre y dejó una lámpara; el "
          f"segundo conserva la puerta, las cortinas y el piso. La volvimos a amoblar con sus {REPL_N} muebles anotados, con el "
          f"paso de imagen del flujo, {_reps} veces. Y comparamos con la real: dónde quedó cada mueble, como IoU entre su caja "
          "y la real, y si es el producto, con el coseno de DINOv3. Es una sola habitación: una prueba, no una medición."], 35)

_rt = (f'<figure class="rt">{foto("repl-real", ROOT / REPLICA["foto"], 380, 239, q=78)}<figcaption><b>la foto real</b>'
       f'<span>un living del ground truth de IKEA</span></figcaption></figure>'
       f'<figure class="rt">{foto("repl-vacio", REPL / "vacio.png", 380, 239, q=78)}<figcaption><b>vaciada</b>'
       f'<span>intento {_i_eleg} de {_n_int} · SSIM fuera de los muebles {f2(_v2["ssim_fuera_de_los_muebles"])}</span></figcaption></figure>')
_rr = "".join(f'<figure class="rt">{foto(f"repl-sin-{i}", REPL / r["imagen"], 380, 239, q=78)}<figcaption><b>réplica {i}</b>'
              f'<span>IoU {f2(r["iou_medio"])} · {r["en_su_lugar"]} de {REPL_N} en su lugar</span></figcaption></figure>'
              for i, r in enumerate(_sv["imagenes"], 1))
resultado(13, "Réplica de un living real", f'''
<div class="r-13">
  <div class="r13-fila">{_rt}</div>
  <div class="r13-fila" data-paso="1">{_rr}</div>
  <div class="r13-k" data-paso="1">
    <div><b>{_s["detectados"]["media"]:.0f}/{REPL_N}</b>productos presentes en cada imagen</div>
    <div><b>{f2(_s["coseno_producto"]["media"])}</b>coseno con la foto del producto (DINOv3)</div>
    <div class="co"><b>{f2(_s["iou_medio"]["media"])}</b>IoU medio con la caja real de cada mueble</div>
    <div class="co"><b>{f1(_s["en_su_lugar"]["media"])} de {REPL_N}</b>muebles en su lugar</div>
  </div>
</div>''',
          "hallazgo", "dónde ≠ qué", "<b>Respeta los productos, no la distribución.</b> No es un error: el pedido no dice dónde va "
          "cada cosa. <mark>Para eso hay que decírselo.</mark>",
          [f"Los {REPL_N} productos aparecen en todas, y se reconocen: coseno {f2(_s['coseno_producto']['media'])}. Pero cada vez "
           f"arma su propio living: el sofá a la izquierda, la estantería a la derecha. El IoU medio con las cajas reales es "
           f"{f2(_s['iou_medio']['media'])}: en promedio, {f1(_s['en_su_lugar']['media'])} de {REPL_N} muebles quedan en su lugar.",
           "La conclusión: el generador respeta los productos, no la distribución. Y no es un error: el pedido no dice dónde va "
           "cada cosa. Si queremos controlar dónde, hay que decírselo. Eso es lo que dejamos como paso a futuro, al final."], 40,
          rotulo="lo que vimos")
