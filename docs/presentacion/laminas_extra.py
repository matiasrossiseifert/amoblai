"""Lo que se sumó el 2026-11-15 (datos/configs/punta_a_punta/experimentos.yaml):

- el experimento 5b, elegir con texto o con fotos, que se nos ocurrió después de decidir todo lo demás
  (va al final de los experimentos, después del 15), y el coseno sin juez;
- los experimentos 1, 2, 5 y 13 repetidos de punta a punta en los 11 ambientes vacíos, sin ground truth:
  la versión 2 contra la misma con un solo cambio, con el juez de listas en los dos órdenes.

DESPUES dice después de qué lámina va cada una (laminas.py las inserta en ORDEN)."""

from __future__ import annotations

import statistics

from datos import ESTILO, K, PAP, f2, f3, ic_txt, jload, metricas, nb, p_signos, resumen_juez, sg, ultima, usd
from laminas_exp import ETAPA_TXT, SOBRE, _marcador, pregunta, resultado
from piezas import ETAPA_EXP, PIN_NODO, barras, kick, minimapa
from registro import lam

H = PAP / "hibrida"
DIAG2 = jload(H / "diagnostico.json")
J_RUIDO = resumen_juez(jload(H / "juez_hibrida_vs_hibrida_bis.json"))  # la misma configuración, dos veces


def _juez(v: str) -> dict:
    """La versión 2 (a, híbrida) contra la variante v (b), en los 11 ambientes."""
    return resumen_juez(jload(H / f"juez_hibrida_vs_{v}.json"))


def _cos(v: str) -> float:
    return DIAG2[v]["coseno_ficha_elegido"]["media"]


def _elecciones(v: str) -> dict[str, dict]:
    return {f.parent.name: jload(f) for f in sorted((H / v).glob("*/3_choice.json"))}


def _costo(v: str) -> float:
    return statistics.mean(c["cost_usd"] for c in _elecciones(v).values())


def _tokens(v: str) -> float:
    return statistics.median(c["meta"]["usage"]["input_tokens"] for c in _elecciones(v).values())


def _cambian(v: str) -> tuple[int, int]:
    """Cuántos productos elegidos cambian contra la versión 2 (pieza por pieza), de cuántos."""
    a, b = _elecciones("hibrida"), _elecciones(v)
    dif = tot = 0
    for slug, ca in a.items():
        for x, y in zip(ca["answer"]["choices"], b[slug]["answer"]["choices"], strict=False):
            tot += 1
            dif += x.get("id") != y.get("id")
    return dif, tot


def _emp(n: int) -> str:
    return f"y {n} empate{'s' if n != 1 else ''}"


_N_RUIDO = _cambian("hibrida_bis")


# =============================================================================================
# 5b · Elegir con texto o con fotos (el último: se nos ocurrió después de decidir todo)
# =============================================================================================
ETAPA_TXT["5b"] = "elección"
ETAPA_EXP["5b"] = ["eleccion"]
PIN_NODO["5b"] = "eleccion"
SOBRE["5b"] = "IKEA: como el 5 · ambientes: la versión 2"

_RT = metricas(ultima("_ablacion-reranking-texto"))
_BASE = "qwen3|description|filtro-type"
_r_bus, _r_foto, _r_txt = _RT[_BASE], _RT[_BASE + "|rerank-opus"], _RT[_BASE + "|rerank-opus-texto"]
_d_txt = _r_txt["vs_anterior"]  # solo texto menos con fotos, pareado
_jt = _juez("texto")
_p_t = p_signos(_jt["a"], _jt["b"])
_ct, _tt = _cambian("texto")
_c_foto, _c_txt = _costo("hibrida"), _costo("texto")
_k_foto, _k_txt = _tokens("hibrida"), _tokens("texto")
_mil = lambda n: f"{round(n / 1000)} mil"  # noqa: E731

pregunta("5b", "Elegir con texto o con fotos", "¿El que elige necesita <em>ver las fotos</em> de los candidatos?",
         "Elegir es reordenar los candidatos. El 5 lo midió con fotos; nunca sin ellas.",
         [("A", "Con la foto de cada candidato", "el flujo"), ("B", "Con su descripción, sin fotos", "")],
         ["El último, y por eso va al final: se nos ocurrió después de haber decidido todo lo demás. Elegir es, en el fondo, "
          "un reranker: ordena los candidatos y se queda con uno. El experimento 5 mostró que, mirando las fotos, ordena mucho "
          "mejor que la búsqueda. Pero nunca lo probamos sin las fotos.",
          "Mismo Opus, mismo prompt; lo único que cambia es cómo ve a los candidatos: su foto, o su descripción de ocho líneas. "
          "En el set de IKEA, reordenando el top-10, y de punta a punta en los once ambientes."],
         30, extra='<p class="adv">el último · se nos ocurrió al final</p>')

resultado("5b", "Elegir con texto o con fotos", f'''
<div class="r-7 r7n">
  <div>
    <span class="et r7-et">set de IKEA · {_r_txt["answerable"]} consultas · reordenar el top-10</span>
    {barras([dict(letra="", et="Solo la búsqueda", v=_r_bus["hit@1"], vtxt=f3(_r_bus["hit@1"])),
             dict(letra="A", et="Con fotos", v=_r_foto["hit@1"], vtxt=f3(_r_foto["hit@1"])),
             dict(letra="B", et="Solo texto", v=_r_txt["hit@1"], vtxt=f3(_r_txt["hit@1"]))],
            titulo="hit@1", cls="gb-compacto r7-b")}
    <p class="un-nota">B − A: {nb(f"{sg(_d_txt['hit@1'])} {ic_txt(*_d_txt['hit@1_ic95'])}")}, pareado: <b>empatan</b>.</p>
  </div>
  <div data-paso="1">
    <span class="et r7-et">de punta a punta · {_jt["n"]} ambientes · juez en los dos órdenes</span>
    {_marcador("Con fotos", _jt["a"], _jt["b"], "Solo texto", f"{_emp(_jt['emp'])} · cambian {_ct} de {_tt} productos")}
    {barras([dict(letra="A", et="Con fotos", v=_jt["util_a"]), dict(letra="B", et="Solo texto", v=_jt["util_b"])],
            titulo="productos útiles", cls="gb-compacto r7-b")}
    <p class="un-nota">Elegir: {usd(_c_foto)} con fotos, <b>{usd(_c_txt)}</b> con texto.</p>
  </div>
</div>''', "", "", "",
          [f"En el set de IKEA, reordenando el top-10: con fotos {f3(_r_foto['hit@1'])}, solo con texto {f3(_r_txt['hit@1'])}; "
           f"la diferencia pareada es casi cero. Los dos, muy por encima de la búsqueda sola, {f3(_r_bus['hit@1'])}.",
           f"De punta a punta, {_jt['a']} a {_jt['b']}, con {_jt['emp']} empate: está dentro del ruido, que es "
           f"{J_RUIDO['a']} a {J_RUIDO['b']}. Productos útiles, {f2(_jt['util_a'])} contra {f2(_jt['util_b'])}. Y con "
           f"texto, elegir cuesta la mitad: {usd(_c_txt)} en vez de {usd(_c_foto)}, porque entran {_mil(_k_txt)} tokens en vez "
           f"de {_mil(_k_foto)}.",
           "Los sesgos tiran para lados opuestos: en el set de IKEA, consulta y descripción las escribe el mismo modelo, y eso "
           "favorece al texto; el juez mira fotos. Aun así, empatan. Decisión: el flujo sigue con fotos, que es como se midió "
           "todo lo demás; con más ambientes, si sigue empatando, conviene el texto, por costo."], 50)

# =============================================================================================
# Los experimentos 1, 2, 5 y 13, de punta a punta en los 11 ambientes (sin ground truth)
# =============================================================================================
def _tiles2(j: dict, var_lbl: str, v2_lbl: str) -> str:
    """Quién ganó cada ambiente (en los dos órdenes), con el nombre corto de cada lado."""
    out = []
    for r in j["rows"]:
        nombre, estilo = ESTILO.get(r["slug"], (r["slug"], ""))
        if r["ganador"] == j["lado_a"]:
            cls, lbl = "t-b", v2_lbl
        elif r["ganador"] == j["lado_b"]:
            cls, lbl = "t-a", var_lbl
        else:
            cls, lbl = "t-e", "empate"
        out.append(f'<div class="tj {cls}"><b>{nombre}</b><span>{estilo}</span><em>{lbl}</em></div>')
    return f'<div class="tiles">{"".join(out)}</div>'


def punta(n, tema, var, lado_var, lado_v2, notas, seg=35, var_izq=True, despues=None):
    """La variante `var` contra la versión 2 en los 11 ambientes, con las letras de la lámina del
    experimento: lado_var y lado_v2 son (letra, etiqueta, nombre corto)."""
    j = _juez(var)
    p = p_signos(j["a"], j["b"])
    dif_, tot = _cambian(var)
    v = dict(letra=lado_var[0], et=lado_var[1], n=j["b"], v=j["util_b"])
    w = dict(letra=lado_v2[0], et=lado_v2[1], n=j["a"], v=j["util_a"], gana=j["a"] > j["b"] and p < 0.05)
    izq, der = (v, w) if var_izq else (w, v)
    lam(f"e{n}p", f"Exp. {n}: en los 11 ambientes", f"Experimentos · {n}", f'''
{kick(f"E{n}", f"experimento {n} · de punta a punta")}
<h2 class="t chico">{tema}, en los 11 ambientes</h2>
{minimapa(n)}
<div class="res-cuerpo"><div class="r-7 r7n">
  <div>
    <span class="et r7-et">juez de listas · {j["n"]} ambientes · en los dos órdenes</span>
    {_marcador(izq["et"], izq["n"], der["n"], der["et"], f"{_emp(j['emp'])} · test de signos, p = {f2(p)}")}
    {barras([{k: x[k] for k in ("letra", "et", "v", "gana") if k in x} for x in (izq, der)],
            titulo="productos útiles", cls="gb-compacto r7-b")}
  </div>
  <div data-paso="1">
    <span class="et r7-et">por ambiente · cambian {dif_} de {tot} productos</span>
    {_tiles2(j, lado_var[2], lado_v2[2])}
  </div>
</div></div>''', notas, seg, clase="clara")
    DESPUES.append((f"e{n}p", despues or f"e{n}r"))
    return j, p


DESPUES = [("e5b", "e15"), ("e5br", "e5b")]

_j1, _j2, _j5 = _juez("vendedor"), _juez("frase"), _juez("k3")
_p = {v: p_signos(j["a"], j["b"]) for v, j in (("vendedor", _j1), ("frase", _j2), ("k3", _j5))}

punta(1, "Qué se indexa", "vendedor", ("A", "Texto del vendedor", "vendedor"), ("B", "Descripción", "descripción"),
      ["¿Y en la tarea real? La versión 2 contra la misma con el índice sobre el texto del vendedor, en los once ambientes: "
       "mismo plan, mismo paso que elige, mismo juez, en los dos órdenes.",
       f"{_j1['a']} a {_j1['b']} para la descripción, con {_j1['emp']} empate: p igual a {f2(_p['vendedor'])}. Los productos "
       f"útiles bajan de {f2(_j1['util_a'])} a {f2(_j1['util_b'])}. Responde la duda del set de IKEA, donde consultas y "
       "descripciones las escribía el mismo modelo: acá el juez no lee descripciones, mira las fotos."])

punta(2, "Cómo se escribe la consulta", "frase", ("B", "La frase natural", "frase"), ("A", "La ficha", "ficha"),
      ["De punta a punta, la ficha contra la frase con que el plan nombra la pieza, sin reescribirla.",
       f"{_j2['a']} a {_j2['b']} para la ficha, con {_j2['emp']} empate, y los productos útiles caen de {f2(_j2['util_a'])} "
       f"a {f2(_j2['util_b'])}. En ambientes ganados no alcanza para la significancia, p igual a {f2(_p['frase'])}, pero va "
       "para el mismo lado que en el set de IKEA."], var_izq=False)

punta(5, "Cuántos candidatos", "k3", ("3", "3 candidatos", "3 candidatos"), ("5", "5 candidatos", "5 candidatos"),
      [f"Y la cantidad de candidatos: los {K} del flujo contra 3.",
       f"{_j5['a']} a {_j5['b']} para cinco, con {_j5['emp']} empates: p igual a {f2(_p['k3'])}; productos útiles, "
       f"{f2(_j5['util_a'])} contra {f2(_j5['util_b'])}. Con tres, el que elige tiene menos para armar el conjunto: "
       "confirma la curva del set de IKEA."])


_j13 = _juez("sin_kind")
punta(13, "Filtros por metadata", "sin_kind", ("A", "Ninguno", "ninguno"), ("C", "Por kind", "por kind"),
      ["De punta a punta, sin el filtro por kind: la búsqueda trae candidatos de cualquier categoría, solo con el límite de "
       "medidas.",
       f"{_j13['b']} a {_j13['a']}, con {_j13['emp']} empates: empatan, también en productos útiles. El que elige descarta "
       "solo lo que es de otra categoría. El filtro se queda porque no cuesta nada y asegura cinco candidatos del tipo "
       "pedido, no por una mejora medida."], seg=30, despues="e13")

# =============================================================================================
# ¿Sirve el coseno sin juez? (gratis, en los 11 ambientes, todas las variantes)
# =============================================================================================
J_V1 = resumen_juez(jload(H / "juez_densa_vs_hibrida.json"))       # a = densa (versión 1), b = híbrida
J_AZ = resumen_juez(jload(H / "juez_densa_vs_azar_7ambientes.json"))  # a = densa, b = azar
J_CX = resumen_juez(jload(H / "juez_hibrida_vs_contexto.json"))     # a = híbrida, b = contexto


def _vs2(j: dict, var_es_a: bool = False) -> str:
    """El marcador de la variante contra la versión 2: variante–versión 2."""
    return f"{j['a']}–{j['b']}" if var_es_a else f"{j['b']}–{j['a']}"


_COS_FILAS = [  # (variante, etiqueta, marcador contra la versión 2)
    ("densa", "Versión 1, la densa", _vs2(J_V1, True)),
    ("k3", "3 candidatos", _vs2(_j5)),
    ("hibrida", "Versión 2", "—"),
    ("hibrida_bis", "Versión 2, otra vez", _vs2(J_RUIDO)),
    ("texto", "Elegir solo con texto", _vs2(_jt)),
    ("contexto", "Catálogo entero", _vs2(J_CX)),
    ("frase", "La frase natural", _vs2(_j2)),
    ("vendedor", "Texto del vendedor", _vs2(_j1)),
    ("sin_kind", "Sin filtro por kind", _vs2(_j13)),
    ("azar", f"{K} al azar", f"{J_AZ['b']}–{J_AZ['a']}*"),
]
_COS_FILAS = sorted(_COS_FILAS, key=lambda f: -_cos(f[0]))

lam("cos", "¿Sirve el coseno sin juez?", "Experimentos", f'''
{kick("cos", "métrica · gratis, sin juez")}
<h2 class="t chico">¿Sirve el coseno <em>sin juez</em>?</h2>
<div class="res-cuerpo"><div class="cosg">
  <div>{barras([dict(letra="", et=e, v=_cos(v), vtxt=f3(_cos(v)), nota=f"juez {m}" if m != "—" else "", gana=v == "hibrida") for v, e, m in _COS_FILAS],
               xmax=0.9, ticks=(0, 0.3, 0.6, 0.9), titulo="coseno entre la ficha y lo elegido · juez: la variante contra la versión 2",
               cls="gb-compacto cos-b")}</div>
  <div class="cos-n" data-paso="1">
    <p>Separa <b>lo malo</b>: al azar, la frase natural, el texto del vendedor.</p>
    <p>No ordena <b>lo bueno</b>: la versión 1 saca más que la 2 y pierde {_vs2(J_V1, True)}.</p>
    <p class="cos-p">* al azar, contra la versión 1, en {J_AZ["n"]} ambientes</p>
  </div>
</div></div>''', [
    "La pregunta de una métrica sin juez: el coseno entre la ficha que escribe el plan y el producto elegido, con el mismo "
    "embedder para todas las variantes. Es gratis.",
    f"Separa lo malo: al azar da {f3(_cos('azar'))}; la frase natural y el texto del vendedor, {f3(_cos('frase'))}. Pero no "
    f"ordena lo bueno: la versión 1 saca más que la 2, {f3(_cos('densa'))} contra {f3(_cos('hibrida'))}, y pierde cinco a "
    "cero. Mide parecido con la ficha, que es justo lo que la búsqueda densa maximiza, no si la lista le sirve al cliente. "
    "Sirve de alarma barata; no reemplaza al juez."], 45, clase="clara")
DESPUES.append(("cos", "e5br"))
