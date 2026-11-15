"""El Ejercicio 4 (la versión 1 y su limitación, el cambio con la configuración antes y después, y los
resultados en las dos versiones), el costo, las limitaciones, el trabajo futuro (con la réplica de un
ambiente real: indicar el lugar ayuda), las conclusiones y gracias."""

from __future__ import annotations

from datos import (AM, B1, B2, C_CHOOSE, C_CHOOSE_MAX, C_CHOOSE_MIN, C_DESC, C_IMG, C_PEDIDO, C_PLAN, N_ELEC, CAM, CASO, CASO_R, CFG, J_RUIDO, JR,
                   RUIDO_CAMBIAN, RUIDO_PROD, f1, J_CTX,
                   CFG_TXT, D, D21, DIAG, FINALES, GASTO, HIB, HIB_R, IMG_TOT, ITEMS, J_AZAR, J_VER, K, N_ANS, P_VER, POR_USO,
                   REPL, REPL_N, RESP2, ROOM_CHECK, RV, TOPES, V1, V2, credito, dif, f2, f3, media_desvio, miles, pct, sg, usd)
from laminas_exp import D_CONSULTA, K_DESC
from piezas import barras, codigo_barras, flujo, foto, kick, producto
from registro import lam

# =============================================================================================
# Ejercicio 4 · 1 de 3: la versión 1 y su limitación, medida
# =============================================================================================
_cat1 = B1["hit@1_por_categoria"]
_kinds = [x.get("kind") for x in ITEMS.values()]
_bm, _ft = HIB["bm25|description|filtro-kind"], HIB["siglip2|description|filtro-kind"]


def _fila_caso(key: str, n: int = 5) -> str:
    """Los primeros de una búsqueda para el caso, con los anotados marcados."""
    r = CASO_R[key]
    return '<div class="caso5">' + "".join(
        f'<div class="cz{" ok" if pid in r["relevant"] else ""}">{producto(pid, 104)}<span>{i}.º</span></div>'
        for i, pid in enumerate(r["ranked"][:n], 1)) + "</div>"


_anot = "".join(f'<div class="cz ok">{producto(pid, 104)}</div>' for pid in CASO_R[V1]["relevant"])
lam("ej4-v1", "Ejercicio 4: la versión 1", "Ejercicio 4 · 1 de 3", f'''
{kick("05", "ejercicio 4 · 1 de 3 · la versión anterior y su limitación")}
<h2 class="t chico">Versión 1: el índice lee la descripción, <em>no ve el producto</em></h2>
<div class="ej-izq">
  <span class="et">la versión 1: el sistema hasta el 11/11</span>
  <p class="ej-p">La búsqueda era el coseno de Qwen3 entre la ficha y las descripciones, con el filtro por kind: <code>rag.hybrid: []</code>. Lo demás, igual que hoy.</p>
  <span class="et">su limitación, medida sobre el ground truth</span>
  <div class="ej-trio">
    <div><b>{f2(B1["hit@1"])}</b><span>hit@1: entre productos casi iguales, el primero es el anotado la mitad de las veces</span></div>
    <div><b>1 de cada {round(1 / (1 - B1["hit@5"]))}</b><span>piezas donde el correcto no llega a los {K} candidatos (hit@5 {f2(B1["hit@5"])}): el que elige ya no puede acertar</span></div>
    <div><b>{f2(_cat1["rug"])} · {f2(_cat1["deco"])}</b><span>en alfombras y deco, donde hay muchos parecidos ({_kinds.count("rug")} alfombras, {_kinds.count("cushion")} almohadones); en sillas, {f2(_cat1["chair"])}</span></div>
  </div>
  <p class="ej-p">El índice <b>lee una descripción, pero no ve el producto</b>, y no aprovecha las palabras exactas de la consulta.</p>
</div>
<div class="ej-der" data-paso="1">
  <span class="et">un caso del banco de prueba · se busca</span>
  <p class="ej-q">«{CASO}»<span>un almohadón blanco con un estampado de hojas negras</span></p>
  <span class="et">los {K} candidatos de la versión 1</span>
  {_fila_caso(V1)}
  <p class="ej-c">Blancos y negros, ninguno con hojas: <b>el anotado quedó {CASO_R[V1]["rank"]}.º</b>, fuera de lo que ve el que elige.</p>
  <div class="ej-anot"><span class="et">lo anotado en ese ambiente</span><div class="caso5">{_anot}</div></div>
</div>
<p class="remate chico" data-paso="2">Dos señales de que había información sin usar: contar palabras ({f3(_bm["hit@1"])}) y la foto sola ({f3(_ft["hit@1"])}) rendían como el embedder, <mark>y fallaban en cosas distintas</mark>.</p>''',
    ["El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del embedder sobre las "
     f"descripciones, con el filtro por kind. Su limitación, medida: entre productos casi iguales, el primero es el anotado el "
     f"{round(100 * B1['hit@1'])} por ciento de las veces, y en una de cada cinco piezas el correcto no llega a los cinco "
     "candidatos.",
     "Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado "
     "quedó sexto. El índice lee una descripción, pero no ve el producto ni aprovecha las palabras exactas.",
     "Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas."],
    45)

# =============================================================================================
# Ejercicio 4 · 2 de 3: el cambio, y la configuración antes y después
# =============================================================================================
assert CFG.rag.hybrid == ["bm25", "siglip2"] and CFG.rag.fusion == "sum" and "  hybrid: [bm25, siglip2]" in CFG_TXT, \
    "amoblai.yaml ya no es la versión 2: revisar la lámina del cambio"


def _hibrida_svg() -> str:
    """La búsqueda antes y después: en trazo claro, lo que ya hacía la versión 1; en coral, lo que
    agrega la versión 2."""
    W, H = 864, 372
    o = [f'<svg class="hb-svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="La búsqueda híbrida">']

    def caja(x, y, w, h, titulo, sub="", nueva=False, tag=""):
        o.append(f'<g class="hb{" nueva" if nueva else ""}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>')
        if sub:
            o.append(f'<text class="hb-t" x="{x + 18}" y="{y + 30}">{titulo}</text><text class="hb-s" x="{x + 18}" y="{y + 54}">{sub}</text>')
        else:
            o.append(f'<text class="hb-t" x="{x + w / 2}" y="{y + h / 2 + 8}" text-anchor="middle">{titulo}</text>')
        if tag:
            o.append(f'<text class="hb-tag" x="{x + w - 14}" y="{y + 24}" text-anchor="end">{tag}</text>')
        o.append("</g>")

    def flecha(x, y1, y2, nueva=False):
        o.append(f'<path class="hb-fl{" nueva" if nueva else ""}" d="M{x} {y1}V{y2 - 5}" marker-end="url(#pf)"/>')

    caja(212, 0, 440, 46, "La ficha de la pieza (8 líneas)")
    flecha(432, 46, 70)
    caja(0, 70, W, 46, "Filtro duro: kind y medidas. Sobre los productos que pasan:")
    sw, gap, y = 272, 24, 146
    for i, (t, sub, nueva, tag) in enumerate([("Qwen3", "coseno con la descripción", False, "versión 1"),
                                              ("BM25", "palabras de la descripción", True, "nuevo"),
                                              ("SigLIP 2", "la frase contra la foto", True, "nuevo")]):
        x = i * (sw + gap)
        flecha(x + sw / 2, 116, y, nueva)
        caja(x, y, sw, 70, t, sub, nueva, tag)
        flecha(x + sw / 2, y + 70, 246, nueva)
    caja(0, 246, W, 46, "Fusión: z-score de cada puntaje, y el promedio", nueva=True, tag="nuevo")
    flecha(432, 292, 322)
    caja(212, 322, 440, 46, f"Los {K} mejores, a la elección")
    o.append("</svg>")
    return "".join(o)


_otros = [CASO_R[V2]["ranked"].index(pid) + 1 for pid in CASO_R[V2]["relevant"] if pid in CASO_R[V2]["ranked"][1:5]]
_otro_txt = f"; el otro anotado, {_otros[0]}.º" if _otros else ""
lam("ej4-v2", "Ejercicio 4: la versión 2", "Ejercicio 4 · 2 de 3", f'''
{kick("05", "ejercicio 4 · 2 de 3 · el cambio y la configuración")}
<h2 class="t chico">Versión 2: <em>búsqueda híbrida</em>, una línea de configuración</h2>
<div class="ej-izq">
  <span class="et">el cambio: la configuración, antes y después</span>
  <div class="pr-tk ej-yaml"><div class="pr-cab"><b>datos/configs/amoblai.yaml</b><span>antes y después</span></div>
<pre class="pr-tx">rag:
  embedder: qwen3
<span class="del">- hybrid: []                  # versión 1</span>
<span class="add">+ hybrid: [bm25, siglip2]     # versión 2</span>
  fusion: sum                 <i class="com"># z-score, y el promedio</i></pre></div>
  <span class="et ej-et2">por qué este cambio</span>
  <ol class="ej-por">
    <li><p>Sale de una <b>limitación medida</b> de la versión 1: el índice no ve el producto ni usa las palabras exactas.</p></li>
    <li><p>Es una técnica de <b>Advanced RAG</b>: búsqueda híbrida (densa + léxica) y multimodal (la foto embebida).</p></li>
    <li><p><b>No cuesta nada por pedido</b>: BM25 y SigLIP 2 corren locales, y los vectores de las fotos se calculan una vez.</p></li>
  </ol>
</div>
<div class="ej-der" data-paso="1">
  <span class="et">la búsqueda, antes y después · en coral, lo que agrega la versión 2</span>
  {_hibrida_svg()}
  <div class="ej-caso2"><div><span class="et">el caso del almohadón, con la versión 2</span>{_fila_caso(V2)}</div>
    <p class="ej-c">El anotado sale <b>1.º</b> (antes, {CASO_R[V1]["rank"]}.º){_otro_txt}.</p></div>
</div>
<p class="remate chico" data-paso="1">Tres miradas del mismo producto: lo que dice <mark>su descripción</mark>, sus <mark>palabras exactas</mark> y <mark>su foto</mark>.</p>''',
    ["El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. ¿Por qué este cambio? Sale "
     "de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y no cuesta nada por pedido, "
     "porque corre local.",
     "La búsqueda ahora promedia tres puntajes estandarizados: el coseno con la descripción, que ya "
     "estaba; BM25, las palabras; y SigLIP 2, la foto. En el caso "
     "del almohadón, ahora el anotado sale primero."],
    40)

# =============================================================================================
# Ejercicio 4 · 3 de 3: resultados en las dos versiones
# =============================================================================================
_v1s = [CAM[V1]["hit@1"]] + [h[V1]["hit@1"] for h in HIB_R]
_v2s = [CAM[V2]["hit@1"]] + [h[V2]["hit@1"] for h in HIB_R]
_difs_r = " · ".join(sg(x["hit@1"]) for x in [D21] + [h[V2]["vs_base"] for h in HIB_R])


def _fv(label, a, b, d="", cls=""):
    return f'<div class="v-l {cls}"><span class="v-n">{label}</span><span class="v-a">{a}</span><span class="v-b">{b}</span><span class="v-d">{d}</span></div>'


lam("ej4-res", "Ejercicio 4: resultados", "Ejercicio 4 · 3 de 3", f'''
{kick("05", "ejercicio 4 · 3 de 3 · resultados en las dos versiones")}
<h2 class="t chico">Resultados: gana en el ground truth y <em>no pierde con el juez</em></h2>
<div class="ticket ver-tk">
  <div class="v-l v-cab"><span></span><span class="v-a">versión 1</span><span class="v-b">versión 2</span><span class="v-d">diferencia</span></div>
  {_fv("Configuración", "<code>rag.hybrid: []</code>", "<code>rag.hybrid: [bm25, siglip2]</code>", "densa → densa + léxica + foto")}
  <div class="v-sec">sobre el ground truth · {N_ANS} consultas con respuesta</div>
  {_fv("hit@1", f3(B1["hit@1"]), f3(B2["hit@1"]), dif(D21))}
  {_fv(f"hit@5 (lo que ve el que elige)", f3(B1["hit@5"]), f3(B2["hit@5"]), dif(D21, "hit@5"))}
  {_fv("MRR@10", f3(B1["mrr@10"]), f3(B2["mrr@10"]), dif(D21, "mrr@10"))}
  {_fv("hit@1 con tres redactores (media ± desvío)", media_desvio(_v1s), media_desvio(_v2s), f"{_difs_r}: se repite con los tres")}
  <div class="v-sec">de punta a punta · {J_VER["n"]} ambientes vacíos reales, el mismo plan, el juez en los dos órdenes</div>
  {_fv("Ambientes que gana", str(J_VER["a"]), str(J_VER["b"]), f'{J_VER["emp"]} empates · {J_VER["votos_b"]} votos a {J_VER["votos_a"]} · p = {f2(P_VER)}')}
  {_fv("Productos útiles según el juez", f2(J_VER["util_a"]), f2(J_VER["util_b"]), "la fracción con la nota máxima")}
  {_fv("El piso de ruido: la versión 2 contra sí misma", "—", f'{J_RUIDO["a"]} a {J_RUIDO["b"]}', f'{J_RUIDO["emp"]} empates · el que elige cambia {RUIDO_CAMBIAN} de {RUIDO_PROD} productos')}
  {_fv("Costo por pedido", usd(C_PEDIDO), "igual", "BM25 y SigLIP 2 corren locales")}
</div>
<div class="ver-dos" data-paso="1">
  <div class="claro"><b>Lo que es claro.</b> En el ground truth, los intervalos de la diferencia no tocan el cero, y la mejora se repite con los tres redactores.</div>
  <div class="no"><b>Lo que no.</b> De punta a punta son {J_VER["n"]} ambientes: {J_VER["b"]} a {J_VER["a"]} da p = {f2(P_VER)}, y en {J_VER["emp"]} el juez no se decide. Que una variante gane un ambiente no alcanza: cuenta la asimetría ({J_VER["b"]} a {J_VER["a"]}, contra {J_RUIDO["a"]} a {J_RUIDO["b"]} entre dos corridas iguales).</div>
</div>
<p class="remate chico" data-paso="1">La versión 2 es hoy la búsqueda del flujo: clara en el ground truth y <mark>«no peor, probablemente mejor»</mark> en la tarea real.</p>''',
    [f"Sobre el ground truth: hit@1 pasa de {f3(B1['hit@1'])} a {f3(B2['hit@1'])}, y "
     f"hit@5, lo que ve el que elige, de {f3(B1['hit@5'])} a {f3(B2['hit@5'])}. Los intervalos de la diferencia "
     f"no tocan el cero, y con los otros dos redactores la mejora se repite. De punta a punta, en los {J_VER['n']} ambientes: "
     f"la versión 2 gana {J_VER['b']}, empata {J_VER['emp']} y no pierde ninguno. "
     f"Los productos útiles pasan de {f2(J_VER['util_a'])} a {f2(J_VER['util_b'])}, y el costo es el mismo.",
     f"Lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da p igual a "
     f"{f2(P_VER)}, y en seis el juez no se decide. Corrimos la misma versión dos veces y el juez repartió los ambientes "
     f"{J_RUIDO['a']} a {J_RUIDO['b']}: ganar un ambiente no alcanza, cuenta la asimetría. Clara en el banco; no peor, "
     "probablemente mejor, en la tarea real."],
    55, clase="clara")

# =============================================================================================
# Cuánto cuesta: del registro de gastos (datos/resultados/gastos.jsonl), como gastos.md
# =============================================================================================
CORTO = {
    "Evaluación: un VLM ordena el top-10 (ground truth de IKEA)": "Evaluar el reranking con un VLM",
    "El flujo: elección de la lista": "El flujo: la elección",
    "Catálogo: descripciones de los productos de ABO": "Describir el catálogo de ABO",
    "Evaluación de punta a punta: juez que compara dos listas": "El juez de punta a punta",
    "Réplica de un ambiente real (ubicación de los muebles)": "La réplica de un ambiente",
    "El flujo: imagen del ambiente amoblado": "El flujo: las imágenes",
}
_top = sorted(POR_USO.items(), key=lambda kv: -kv[1])[:6]
_tot = GASTO["total"]
_elec = N_ELEC
_mas_caro = CORTO.get(_top[0][0], _top[0][0])
_mx = max(v for _, v in _top)
_tope = -(-_mx // 5) * 5
lam("costo", "Cuánto cuesta", "Cierre", f'''
{kick("06", "cierre · costo")}
<h2 class="t chico">Cuánto cuesta <em>un pedido</em>, y cuánto costó el trabajo</h2>
<div class="ticket costo-tk">
  <div class="tk-cab"><b>amoblai</b><span>un pedido<br>configuración final</span></div>
  <div class="tk-l"><span class="tk-n">Plan · Claude Opus 5.5</span><span class="tk-dots"></span><b>{usd(C_PLAN)}</b></div>
  <div class="tk-l"><span class="tk-n">Elección · Claude Opus 5.5 (de {f2(C_CHOOSE_MIN)} a {f2(C_CHOOSE_MAX)})</span><span class="tk-dots"></span><b>{usd(C_CHOOSE)}</b></div>
  <div class="tk-l"><span class="tk-n">Imagen · Nano Banana 2, por intento</span><span class="tk-dots"></span><b>{usd(C_IMG)}</b></div>
  <div class="tk-l"><span class="tk-n">Buscar · Qwen3, BM25, SigLIP 2 y ChromaDB, locales</span><span class="tk-dots"></span><b>{usd(0)}</b></div>
  <div class="tk-tot"><span>un pedido, con un intento de imagen</span><span>~{usd(C_PEDIDO)}</span></div>
  <p class="tk-pie">plan: la media de las llamadas del registro desde el 10/11 · elección: la media de {_elec} corridas de punta a punta (catálogo IKEA + ABO) · costo único, describir el catálogo de Amazon: {usd(C_DESC, 3)} por producto</p>
  {codigo_barras("costo", 260, 34)}
</div>
<div class="costo-der" data-paso="1">
  <div class="costo-tot"><b>{usd(_tot, 0)}</b><span>todo el trabajo: Anthropic {usd(GASTO["anthropic"])} (tope de {TOPES["anthropic"]:g}) y fal {usd(GASTO["fal"])}</span></div>
  {barras([dict(et=CORTO.get(k, k), v=v, vtxt=f2(v), gana=(i == 0)) for i, (k, v) in enumerate(_top)], xmax=_tope,
          ticks=tuple(range(0, int(_tope) + 1, 5)), titulo="en qué se fue (US$)", cls="oscuro gb-costo", paso=1, gana_paso=1,
          tick_fmt=lambda t: f"{t:g}")}
  <p class="costo-n">Cada llamada paga queda en un registro con su costo, sus tokens y su latencia, con <b>topes por cuenta</b>; lo ya pagado queda en caché. Sin LangSmith: el registro propio y la carpeta de cada corrida ya dan la traza de cada paso.</p>
</div>''',
    [f"Costos, del registro de gastos. Un pedido cuesta unos {round(100 * C_PEDIDO)} centavos de dólar: {round(100 * C_PLAN)} "
     f"el plan, {round(100 * C_CHOOSE)} la elección y {round(100 * C_IMG)} la imagen. Buscar no cuesta nada: todo corre local.",
     f"El trabajo entero costó {round(_tot)} dólares; lo que más costó fue {_mas_caro[0].lower() + _mas_caro[1:]}. Cada llamada paga "
     "queda registrada, con topes por cuenta, y lo ya pagado queda en caché."],
    30)

# =============================================================================================
# Limitaciones
# =============================================================================================
_dh = DIAG["hibrida"]
_no_sost = 1 - RESP2["faithfulness"]["global"]   # sobre las listas de la versión 2, el flujo de hoy
LIM_S = [
    ("No dice «no hay»", f"cuando el catálogo no tiene lo pedido, pone lo más parecido sin avisar: dejó afuera {_dh['piezas_dejadas_afuera']} de {_dh['piezas']} piezas"),
    ("El tamaño no se puede verificar", f"el límite lo estima el plan a ojo, y solo el {round(100 * D['ikea_con_medida'])}% de IKEA tiene alguna medida"),
    ("La imagen es una visualización", f"acierta el producto exacto 4 de cada 10 veces y conserva el cuarto en {IMG_TOT['pasan']} de {len(FINALES)}"),
    ("El generador afirma maderas que no ve", f"el {round(100 * _no_sost)}% de las afirmaciones del porqué no se sostiene"),
]
_ruido_notas = max(abs(JR["resumen"][JR["a"]][k] - JR["resumen"][JR["b"]][k]) for k in ("request", "room", "together"))
LIM_E = [
    ("El banco de la búsqueda es de producto conocido", "lo escribió el mismo modelo que las descripciones, y no hay conjunto apartado"),
    (f"De punta a punta son {D['n_ambientes_vacios']} ambientes", "con un juez que es el mismo modelo que elige, sin validar contra personas"),
    ("El pedido abierto no está evaluado", "los pedidos enumeran las piezas"),
    ("El que elige no es determinístico", f"entre dos corridas iguales cambia {RUIDO_CAMBIAN} de {RUIDO_PROD} productos, y las notas del juez se mueven hasta {f1(_ruido_notas)}"),
]


def _lim(items):
    return "".join(f"<li><div><b>{a}</b><span>{b}</span></div></li>" for a, b in items)


lam("limites", "Limitaciones", "Cierre", f'''
{kick("06", "cierre · limitaciones")}
<h2 class="t chico">Lo que <em>todavía no resuelve</em>, y lo que no medimos</h2>
<div class="lim-dos">
  <div><span class="et">del sistema</span><ol class="lim lim2">{_lim(LIM_S)}</ol></div>
  <div data-paso="1"><span class="et">de la evaluación</span><ol class="lim lim2 fut">{_lim(LIM_E)}</ol></div>
</div>
<p class="remate chico" data-paso="1">Ninguna invalida la lista: los productos son reales y salen de la búsqueda. Sí acotan <mark>cuánto podemos afirmar</mark>.</p>''',
    ["Del sistema: no dice «no hay», pone lo más parecido sin avisar; el tamaño no se puede verificar; la imagen "
     "es una visualización; y el generador afirma maderas que no ve.",
     f"De la evaluación: el banco de la búsqueda es de producto conocido, sin conjunto apartado; de punta a punta son "
     f"{D['n_ambientes_vacios']} ambientes, con un juez sin validar contra personas; y el que elige no es determinístico: entre "
     f"dos corridas iguales cambia {RUIDO_CAMBIAN} de {RUIDO_PROD} productos."],
    30)

# =============================================================================================
# Trabajo futuro, con la réplica de un ambiente real: indicar el lugar ayuda
# =============================================================================================
FUT = [
    ("Que diga «no hay»", "que el que elige avise cuando ningún candidato cumple, y mostrarlo"),
    ("Un banco escrito por personas", "con un conjunto apartado, y el voto a ciegas del equipo para validar al juez"),
    ("Un modelo más barato para elegir", f"hoy es Opus ({usd(C_CHOOSE)} por pedido), y no medimos cuánto se pierde con uno menor"),
    ("Pasarle los materiales al que elige", "hoy ve el tipo y la medida, y adivina la madera por la foto"),
    ("Medidas reales del ambiente", "el filtro de tamaño sería un filtro de verdad"),
    ("Un catálogo actual", "con precio y stock como filtros de metadata"),
]
assert RV["simple_sin_cajas"] < RV["simple_texto"] < RV["simple_cajas"] < RV["simple_cajas_3d"]
lam("futuro", "Trabajo futuro", "Cierre", f'''
{kick("06", "cierre · trabajo futuro")}
<h2 class="t chico">Lo próximo es del RAG, <em>y de cómo lo medimos</em></h2>
<div class="fut-izq">
  <span class="et">lo próximo</span>
  <ol class="lim lim2 fut futl">{_lim(FUT)}</ol>
</div>
<div class="fut-der" data-paso="1">
  <span class="et">más lejos, fuera del RAG: ubicar cada mueble · una prueba</span>
  {barras([dict(et="Sin indicar el lugar", v=RV["simple_sin_cajas"]), dict(et="Dicho en palabras", v=RV["simple_texto"]),
           dict(et="Rectángulos dibujados", v=RV["simple_cajas"]), dict(et="Cajas 3D dibujadas", v=RV["simple_cajas_3d"], gana=True)],
          xmax=1.0, titulo="IoU medio de cada mueble con su posición real", cls="oscuro gb-fut", paso=1, gana_paso=1)}
  <div class="fut-fotos">
    <figure>{foto("fut-real", REPL / "real_con_cajas_3d.jpg", 372, 234, q=78)}<figcaption>La foto real, con las cajas 3D de sus muebles.</figcaption></figure>
    <figure>{foto("fut-gen", REPL / "simple_cajas_3d" / "2.png", 372, 234, q=78)}<figcaption>Generada con esas cajas sobre la foto vacía.</figcaption></figure>
  </div>
  <p class="fut-n">Un living del ground truth de IKEA, vaciado y vuelto a amoblar con sus {REPL_N} muebles: un solo cuarto, 3 imágenes por variante (en la primera ronda, {f2(RV["sin_cajas"])}, {f2(RV["con_cajas"])} y {f2(RV["con_cajas_3d"])}). Lo único que se sostiene: <b>indicar el lugar ayuda</b>.</p>
</div>
<p class="remate chico" data-paso="1">Ubicar cada mueble a escala pide <mark>medir el ambiente</mark>: queda como trabajo futuro.</p>''',
    ["Lo próximo es del RAG y de cómo lo medimos: que el sistema diga «no hay»; un banco de consultas escrito por "
     "personas, con un conjunto apartado; validar al juez con nuestro voto a ciegas; y probar un modelo más barato para "
     "elegir. Más lejos: medidas reales del ambiente y un catálogo actual.",
     "Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto; lo "
     "único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda."],
    35)

# =============================================================================================
# Conclusiones y gracias
# =============================================================================================
_d_desc = CAM[K_DESC]["vs_anterior"]
CONC = [
    ("Lo que más pesa es la base de conocimiento y cómo se escribe la consulta:",
     f"describir cada producto desde su foto ({sg(_d_desc['hit@1'], 2)} de hit@1) y escribir la consulta como una ficha ({sg(D_CONSULTA, 2)} contra la frase natural). El embedder casi no importa."),
    ("La versión 2 es la búsqueda híbrida:",
     f"{sg(D21['hit@1'])} de hit@1 sin costo por pedido; de punta a punta gana {J_VER['b']}, empata {J_VER['emp']} y no pierde."),
    ("La búsqueda aporta en la tarea real:", f"{J_AZAR['a']} a {J_AZAR['b']} contra candidatos al azar del mismo kind. Contra el catálogo "
     f"entero en el contexto empata ({J_CTX['a']} a {J_CTX['b']}): con {miles(D['prod_todos'])} productos, RAG no hace mejor la lista; es la arquitectura que escala."),
    ("Medir bien fue la mitad del trabajo:", "nos hizo cambiar el número de cabecera."),
    ("La lista es confiable; la imagen es una visualización:",
     f"reconoce el {pct(IMG_TOT['reconocidos'] / IMG_TOT['productos'])} de los productos y conserva el cuarto en {IMG_TOT['pasan']} de {len(FINALES)}."),
]
CIERRE = ["publica-loft-industrial", "publica-living-japandi", "publica-living-bohemio", "publica-comedor-clasico-moderno"]
assert all(f["img"]["attempts"][0]["ok"] for f in FINALES if f["slug"] in CIERRE), "las del cierre tienen que haber pasado el control al primer intento"
_ims = "".join(foto(f"conc-{s}", AM / f"final-{s}" / "final.png", 318, 212, q=78) for s in CIERRE)
lam("conclusiones", "Conclusiones", "Cierre", f'''
<div class="conc-izq">
  {kick("06", "conclusiones")}
  <ol class="conc conc5">{"".join(f'<li data-paso="{i}"><em>{i + 1}</em><p><b>{a}</b> {b}</p></li>' for i, (a, b) in enumerate(CONC))}</ol>
</div>
<div class="conc-der conc4">{_ims}
  <div class="conc-et"><span>cuatro de las {len(FINALES)} corridas de la configuración final: pasaron el control al primer intento</span>
  <span class="cred-l">Fotos de los ambientes: {credito(*CIERRE)}</span></div></div>''',
    ["Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa.",
     f"Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta gana {J_VER['b']}, "
     f"empata {J_VER['emp']} y no pierde.",
     f"Tres: la búsqueda gana {J_AZAR['a']} a {J_AZAR['b']} contra el azar, y empata contra el catálogo entero en el contexto: "
     "RAG no hace mejor la lista, es la arquitectura que escala.",
     "Cuatro: medir bien fue la mitad del trabajo; nos hizo cambiar el número de cabecera.",
     "Y cinco: la lista es confiable; la imagen es una visualización."],
    45)

lam("gracias", "Gracias", "", f'''
<div class="esq-portada">{flujo(cls="arte", etiquetas_fin={"descripcion": "8 líneas, desde la foto", "indice": "Qwen3 · BM25 · SigLIP 2", "plan": "una ficha por pieza",
                                                         "busqueda": f"híbrida · {K} candidatos", "eleccion": "arma la lista", "escena": "plantilla",
                                                         "imagen": f"hasta {CFG.furnish.max_image_products} productos", "control": f"SIFT ≥ {ROOM_CHECK['min_inliers']}"})}</div>
<div class="portada-txt">
  {kick("TP", "73.69 Large Language Models · ITBA · 2026")}
  <h1 class="marca gracias">Gracias.</h1>
  <p class="portada-preg">¿Preguntas?</p>
  <ul class="equipo"><li>Juan Bautista Albertoni Salini</li><li>Matias Juan Rossi Seifert</li><li>Junior Rambau</li></ul>
</div>''', "Gracias. ¿Preguntas?", 5, clase="portada sin-hud")
