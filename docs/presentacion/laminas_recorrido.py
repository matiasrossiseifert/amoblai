"""El recorrido por las once fases del flujo, con el mapa que avanza (la fase actual encendida, las
vistas marcadas). Por fase: qué entra y qué sale, lo que decidimos (con el pin del experimento que
le hizo la pregunta), el prompt que mandamos (extracto literal del archivo) y cómo lo reescribimos,
y un ejemplo real: una corrida de la configuración final, el loft de estilo industrial sobre una
foto pública (datos/resultados/amoblar/final-publica-loft-industrial), seguida de punta a punta, y
su sofá, un producto del catálogo de Amazon, seguido de su foto a la lista."""

from __future__ import annotations

import collections
import json
import re


from datos import (ABO_ITEMS, CFG, CLA, CLA_IMG, D, DESCR_TODO, FILTRO_MAX, FINALES, HERO, HERO_CHOICE, HERO_CHOOSE, HERO_FOUND, HERO_IMG, HERO_PICKS, HERO_PZ, HERO_REQ,
                   HERO_SCENE, IMG_TOT, ITEMS, K, KIND_ES, N_HERO, N_HERO_PRIMERO, PASAN,
                   ROOM_CHECK, ROOT, SLACK, SOFA, esc, f2, miles)
from piezas import flujo, foto, kick, producto
from recorrido import cuerpo_prompt, mapa, prompt_tk, sift_pares, vector_chroma, versiones
from registro import lam

PZ = HERO_PZ
LAMP = next(h["id"] for h, *_ in HERO_PICKS if h["kind"] == "floor lamp" and h["id"] in ITEMS)  # el de IKEA de la lista
HNSW = CFG.rag.hnsw
LLM = CFG.furnish.llm
# el pedido que se sigue usó la escena de la configuración final, y la búsqueda de la versión 2
assert HERO_SCENE["prompt"] + ".md" == CFG.furnish.scene_prompt and CFG.rag.hybrid == ["bm25", "siglip2"]


def fase(id_, n_txt, tema, titulo, lead, banda, notas, actual, pines=None, focos=None, cls_banda="", extra=""):
    lam(id_, f"Fase {n_txt.split(' ', 1)[0]}: {tema}", f"Recorrido · {n_txt.split(' ', 1)[0]}", f'''
<div class="izq-rt">
  {kick("02", f"recorrido · fase {n_txt} de 11 · {tema.lower()}")}
  <h2 class="t chico rt-t">{titulo}</h2>
  {lead}
</div>
{mapa(actual, pines, focos=focos is not None)}
<div class="rt-banda {cls_banda}">{banda}</div>{extra}''', notas, 30, focos=focos)


def ficha(q: str, n: int = 8) -> str:
    filas = []
    for l_ in q.strip().splitlines()[:n]:
        if ":" in l_:
            a, b = l_.split(":", 1)
            filas.append(f'<div><dt>{esc(a.strip())}</dt><dd>{esc(b.strip())}</dd></div>')
    return f'<dl class="ficha">{"".join(filas)}</dl>'


def _cat(pid: str) -> str:
    return "Amazon" if pid.startswith("abo-") else "IKEA"


# =============================================================================================
# 0 · El mapa: once fases, dos pipelines
# =============================================================================================
lam("rec-mapa", "El recorrido", "Recorrido", f'''
<div class="rm-izq">
  {kick("02", "arquitectura · el recorrido")}
  <h2 class="t">El recorrido: <em>once fases</em>, en dos pipelines</h2>
</div>
<div class="rm-esq">{flujo(ruta=True)}</div>''',
    ["El sistema, fase por fase, sobre este mapa: once fases en dos pipelines.",
     "Las tres primeras corren una vez, offline: el catálogo, la descripción de cada producto y el índice.",
     "Las otras ocho corren en cada pedido: el plan decide las piezas, la búsqueda trae "
     "candidatos, la elección arma la lista, y después la escena, la imagen y el control. Solo tres llaman a "
     "un modelo: Opus en el plan y en la elección, y Nano Banana 2 en la imagen.",
     "En cada fase vamos a ver qué entra, qué sale y el prompt."],
    35, focos=["", "indexing catalogo descripcion indice", "consulta foto plan busqueda eleccion escena imagen control salida", ""])

# =============================================================================================
# 1 · Catálogo
# =============================================================================================
_lamp = ITEMS[LAMP]
_sofa = ABO_ITEMS[SOFA]
_sofa_nom = re.sub(r"^Amazon Brand\s*[–-]\s*", "", _sofa["name"]).split(",")[0]
def _dim(d, ax):
    v = (d or {}).get(ax)
    return f"{v:g}".replace(".", ",") if v else None


def _regcard(fuente, pid, nombre, it):
    d = it.get("dimensions_cm")
    med = " × ".join(x or "—" for x in (_dim(d, "width"), _dim(d, "depth"), _dim(d, "height")))
    filas = [("tipo", it["category"]), ("kind", it["kind"]), ("medidas", f"{med} cm" if d else "—")]
    dl = "".join(f'<div><dt>{a}</dt><dd{" class=nohay" if b == "—" else ""}>{b}</dd></div>' for a, b in filas)
    return (f'<div class="reg-card" data-paso="1">{producto(pid, 190)}<div class="rg-d"><h4>{fuente} · <b>{pid.removeprefix("abo-")}</b></h4>'
            f'<p class="rg-n">{esc(nombre)}</p><dl>{dl}</dl></div></div>')


def _fuente(n, nombre, cita, cls=""):
    return f'<div class="rc-n {cls}"><b>{n}</b><span>{nombre}</span><i>{cita}</i></div>'


_cat_eq = (f'<div class="rc-eq">{_fuente(D["prod_819"], "IKEA", "Tautkute et al., 2017")}<span class="rc-op">+</span>'
           f'{_fuente(D["n_abo"], "Amazon (ABO)", "Collins et al., 2022")}<span class="rc-op">=</span>'
           f'{_fuente(miles(D["prod_todos"]), "productos", "un mismo registro", "tot")}</div>')
fase("rec-catalogo", "1", "Catálogo", "El catálogo: <em>dos fuentes</em>, un mismo registro", _cat_eq,
     _regcard("IKEA", LAMP, _lamp["name"], _lamp) + _regcard("Amazon", SOFA, _sofa_nom, _sofa),
     [f"Fase uno, el catálogo: la base de conocimiento. Son dos fuentes. El dataset de IKEA: lo ampliamos a {D['prod_855']} "
      f"productos de living y comedor y, revisado mirando cada foto, quedaron {D['prod_819']}. Y Amazon Berkeley Objects, "
      f"listados reales de Amazon: de casi 150 mil quedaron {D['n_abo']}. En total, {miles(D['prod_todos'])} productos.",
      "Cada producto es un mismo registro: id, foto, tipo, kind y medidas. Tipo, kind y medidas sirven para filtrar; la "
      "foto, para describirlo. Así viene una lámpara de IKEA, sin medidas, y así un sofá de Amazon, con medidas."],
     actual=["catalogo"], cls_banda="rc-b")

# =============================================================================================
# 2 · Descripción
# =============================================================================================
# cuántas descripciones de IKEA escribió cada versión del prompt (queda registrado en cada una)
_NV = collections.Counter(json.loads(x)["prompt"].split("@")[0] for x in
                          (ROOT / "datos" / "catalogo" / "descripciones.jsonl").read_text().splitlines())
# el ejemplo (el sofá, de ABO) lo escribió la versión por la API: las mismas reglas que se muestran
_api = cuerpo_prompt("describe_products_api_v1.md")
for _regla in ("Exactly these eight lines, in this order", "one to three of these, the closest first", "60 to 90 words in all."):
    assert _regla in _api and _regla in cuerpo_prompt("describe_product_v3.md"), _regla
fase("rec-descripcion", "2", "Descripción", "Un VLM mira cada foto y <em>escribe 8 líneas fijas</em>",
     prompt_tk("describe_product_v3.md", [
         ("Exactly these eight lines, in this order", "in this order"),
         ("Say only what the photos and the name show", "No brand, price, measurements"),
     ], resaltar=["Exactly these eight lines, in this order", "Say only what the photos and the name show",
                  "No brand, price, measurements"], cls="a-pr"),
     f'''<div class="a-ent"><span class="et">entra</span>{producto(SOFA, 250)}<b>{esc(_sofa_nom)}</b></div>
<div class="a-fl"><i>→</i><b>Opus 5.5</b></div>
<div class="a-sal" data-paso="1"><span class="et">sale la descripción · 8 líneas</span><div class="ficha-tk">{ficha(DESCR_TODO[SOFA])}</div></div>''',
     ["Fase dos: la descripción. Un VLM, Opus 5.5, mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, "
      "estilo, materiales, colores, forma, sensación y con qué combina. El prompt pide exactamente esas ocho líneas, sin "
      "marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación.",
      "Este es el sofá de Amazon que vamos a seguir: Amazon pasó por la API, con las mismas reglas. "
      "Es el preprocesamiento que más pesa: lo mide el experimento 1."],
     actual=["descripcion"], pines={"descripcion": [1]}, cls_banda="a-rd")

# =============================================================================================
# 3 · Índice
# =============================================================================================
VEC = vector_chroma(SOFA)
SIGLIP = CFG.rag.embedders["siglip2"]["model"]


def _indice_svg():
    W, H = 1728, 236
    o = [f'<svg class="ri-svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    # el documento
    o.append(f'<rect class="caja-t" x="0" y="8" width="372" height="{H - 16}" rx="6"/>')
    o.append('<text class="t-mono" x="20" y="38"><tspan class="k">documento · la descripción</tspan></text>')
    lineas = DESCR_TODO[SOFA].strip().splitlines()
    for i, l_ in enumerate(lineas[:3]):
        a, b = l_.split(":", 1)
        b = b.strip()
        b = b if len(a) + len(b) < 33 else b[:31 - len(a)].rstrip(" ,") + "…"
        o.append(f'<text class="t-mono" x="20" y="{86 + i * 34}"><tspan class="k">{esc(a)}:</tspan> <tspan class="d">{esc(b)}</tspan></text>')
    o.append(f'<text class="t-mono" x="20" y="{86 + 3 * 34}"><tspan class="k">… 8 líneas</tspan></text>')
    # flecha
    o.append('<path class="flr" d="M384 120H436" marker-end="url(#pf)"/>')
    # el modelo
    o.append('<rect class="caja-m" x="448" y="22" width="372" height="196" rx="10"/>')
    o.append('<text class="t-mod" x="472" y="112">Qwen3-Embedding</text>')
    o.append('<text class="t-mod-s" x="472" y="150">local, en CPU</text>')
    o.append('<path class="flr" d="M832 120H884" marker-end="url(#pf)"/>')
    # el vector
    vs = VEC["v"]
    mx = max(abs(x) for x in vs)
    x0, bw, base = 900, 5.2, 120
    o.append(f'<line class="v0" x1="{x0}" y1="{base}" x2="{x0 + len(vs) * (bw + 1)}" y2="{base}"/>')
    for i, v in enumerate(vs):
        h = abs(v) / mx * 70
        y = base - h if v >= 0 else base
        o.append(f'<rect class="vb{"" if v >= 0 else " n"}" x="{x0 + i * (bw + 1):.1f}" y="{y:.1f}" width="{bw}" height="{max(h, 1):.1f}"/>')
    o.append(f'<text class="t-vn" x="{x0}" y="40">el vector</text>')
    o.append(f'<text class="t-v" x="{x0}" y="222">las primeras {len(vs)} componentes</text>')
    o.append(f'<path class="flr" d="M{x0 + len(vs) * (bw + 1) + 14} 120H{x0 + len(vs) * (bw + 1) + 62}" marker-end="url(#pf)"/>')
    # el registro en ChromaDB
    rx = x0 + len(vs) * (bw + 1) + 76
    md = VEC["metadata"]
    o.append(f'<rect class="caja-t" x="{rx}" y="8" width="{W - rx}" height="{H - 16}" rx="6"/>')
    o.append(f'<text class="t-mono" x="{rx + 20}" y="38"><tspan class="k">ChromaDB · un registro</tspan></text>')
    filas = [("id", SOFA.removeprefix("abo-")), ("embedding", f"[{miles(VEC['dim'])} números]"), ("document", "la descripción"),
             ("kind", md["kind"]), ("medidas", " × ".join(f"{md[a]:g}".replace(".", ",") for a in ("width", "depth", "height")))]
    for i, (a, b) in enumerate(filas):
        o.append(f'<text class="t-mono" x="{rx + 20}" y="{78 + i * 32}"><tspan class="k">{a}</tspan></text>'
                 f'<text class="t-mono" x="{rx + 140}" y="{78 + i * 32}"><tspan class="d">{esc(b)}</tspan></text>')
    o.append("</svg>")
    return "".join(o)


fase("rec-indice", "3", "Índice", "Un vector por producto: <em>la descripción entera</em>",
     f'''<div class="rc-eq a-eq">{_fuente("1", "documento por producto", "la descripción entera, sin chunks")}
  {_fuente(miles(VEC["dim"]), "componentes", "Qwen3-Embedding, local", "tot")}
  {_fuente("+2", "índices más", "BM25 y SigLIP 2, para la híbrida")}</div>''',
     _indice_svg(),
     ["Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: "
      f"{miles(VEC['dim'])} dimensiones, a ChromaDB, con la metadata de los filtros al lado. Así queda el sofá. Embedder, "
      "splitting, dimensión y base vectorial son preguntas de trámite: las contestamos juntas más adelante.",
      "Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las "
      "descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto en un mismo espacio."],
     actual=["indice"], pines={"indice": [9, 10, 11, 12]}, cls_banda="ri a-ri")

# =============================================================================================
# 4 y 5 · Foto + pedido → plan
# =============================================================================================
_p0 = PZ[0]


def _md(p):
    v = [p.get(f"max_{a}_cm") for a in ("width", "depth", "height")]
    return "≤ " + " × ".join("—" if x is None else f"{x:g}" for x in v) if any(v) else "—"


_pzs = "".join(f'<div class="rp-pz{" uno" if i == 0 else ""}"><span class="q">{i + 1}</span><b>{esc(", ".join(p["kinds"]))}</b>'
               f'<span class="md">{_md(p)}</span></div>' for i, p in enumerate(PZ))
_ped_corto = HERO_REQ.split(":")[0] + "…"
fase("rec-plan", "4 y 5", "Foto, pedido y plan", "Del pedido a <em>una consulta por pieza</em>",
     f'<p class="a-ped">«{esc(_ped_corto)}»</p>',
     f'''<div class="rp-ent">{foto("rec-hero-room", HERO / "room.jpg", 440, 293)}</div>
<div class="ticket rp-plan a-plan" data-paso="1"><div class="tk-cab"><b>Plan · {len(PZ)} piezas</b><span>Claude Opus 5.5</span></div>
  <div class="rp-pz" style="border-top:0;color:var(--tinta-3)"><span></span><span>kind</span><span class="md">medida máx., cm</span></div>
  {_pzs}</div>
<div class="rp-q a-q" data-paso="1"><span class="et">la consulta de la pieza 1: una ficha del catálogo</span>
  <div class="ficha-tk">{ficha(_p0["query"])}</div>
  <p class="a-tags"><span>Query expansion · HyDE</span><span>Descomposición del pedido</span></p></div>''',
     ["Fases cuatro y cinco. Entra una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el "
      "final: un pedido de estilo industrial, sobre una foto pública.",
      f"El plan es la primera llamada a Opus, que hace de diseñador: lee el ambiente, descompone el pedido en piezas, acá "
      f"{len(PZ)}, y para cada una da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal "
      "escrito en las mismas ocho líneas que el catálogo. Es query expansion con respuesta "
      "hipotética, HyDE: en la base no hay preguntas, hay respuestas. Más la "
      "descomposición del pedido: una consulta por pieza."],
     actual=["foto", "plan"], pines={"plan": [2]}, focos=["foto", "plan"], cls_banda="a-rp")

# =============================================================================================
# 5 · El prompt del plan y sus versiones
# =============================================================================================
fase("rec-plan-prompt", "5", "Plan", "El prompt del plan, <em>reescrito cuatro veces</em>",
     versiones([
         ("v1", "Una silla no es un sillón.", "", "fuera"),
         ("v2", "La pieza como la nombró el usuario.", "", ""),
         ("v3", "Terminar el ambiente.", "", ""),
         ("v4", "Sin tope de piezas.", "", "actual"),
     ], cls="a-vers"),
     prompt_tk("search_query_v4.md", [
         ("You are an experienced interior designer.", "interior designer."),
         ("Then decide which pieces to add", "the most important first."),
         ("- If they name a piece, give them that piece", "A chair is not an armchair"),
         ('  - "query": the ideal product', "eight lines"),
     ], resaltar=["as many as the request and the room call for", "A chair is not an armchair",
                  "the ideal product in the catalog's eight lines"], cls="a-pr grande"),
     ["Es el prompt que más reescribimos, y cada versión salió de una corrida. La primera le dio un sillón a alguien que "
      "pidió una silla para su escritorio. La v2 pide la pieza como la nombró el usuario, el kind de una lista cerrada, las "
      "medidas máximas y la consulta en ocho líneas. La v3 pide terminar el ambiente, y la v4 saca el tope de piezas. La "
      "consulta en las ocho líneas no cambió desde la v2: es lo que mide el experimento 2."],
     actual=["plan"], pines={"plan": [2]}, cls_banda="a-rpp")

# =============================================================================================
# 6 · Búsqueda: filtro duro por kind y medidas, y sobre lo que pasa, búsqueda híbrida (la versión 2)
# =============================================================================================
EJE = {"max_width_cm": "ancho", "max_depth_cm": "fondo", "max_height_cm": "alto"}
_filtro_txt = " · ".join([f'kind = {", ".join(_p0["kinds"])}'] + [f"{EJE[k]} ≤ {v:g} cm" for k, v in FILTRO_MAX.items()])
_cands = HERO_FOUND[0]["candidates"]
assert [c["score"] for c in _cands] == sorted((c["score"] for c in _cands), reverse=True) and _cands[0]["id"] == SOFA
_cs = "".join(f'<div class="rb-c a-c{" uno" if c["id"] == SOFA else ""}">{producto(c["id"], 170)}<em>{f2(c["score"])}</em>'
              f'<b>{_cat(c["id"])}</b></div>' for c in _cands)
_n_abo_c = sum(c["id"].startswith("abo-") for c in _cands)
fase("rec-busqueda", "6", "Búsqueda", "Filtro por kind, y después <em>búsqueda híbrida</em>",
     f'''<div class="rc-eq a-eq">{_fuente(miles(D["prod_todos"]), "productos", "el catálogo")}<span class="rc-op">→</span>
  {_fuente(PASAN, "pasan el filtro duro", esc(_filtro_txt), "tot")}</div>''',
     f'''<div class="a-tres" data-paso="1"><span class="et">tres puntajes, con la misma ficha</span>
  <div><b>Qwen3</b><span>contra la descripción</span></div>
  <div><b>BM25</b><span>las palabras</span></div>
  <div><b>SigLIP 2</b><span>contra la foto</span></div>
  <p>z-score de cada uno, y el promedio</p></div>
<div class="a-fl" data-paso="1"><i>→</i></div>
<div class="a-cands" data-paso="1"><span class="et">los {K} mejores, a la elección</span><div class="rb-cands">{_cs}</div></div>''',
     [f"Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, "
      f"con {round(SLACK * 100)}% de margen porque salen de una foto. Acá quedan {PASAN} de los {miles(D['prod_todos'])} "
      "productos.",
      "Sobre esos, tres puntajes con la misma ficha: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras "
      "de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje "
      "se estandariza y se promedian: es la búsqueda híbrida, la versión 2. Quedan los cinco mejores: "
      f"{_n_abo_c} de Amazon y {len(_cands) - _n_abo_c} de IKEA."],
     actual=["busqueda"], pines={"busqueda": [3, 8, 13]}, cls_banda="a-rb")

# =============================================================================================
# 7 · Elección: la generación de la lista (la G del RAG)
# =============================================================================================
_ch = {c["piece"]: c for c in HERO_CHOICE}
_cm = HERO_CHOOSE["meta"]


def _fila_eleccion(i, nombre):
    p = HERO_FOUND[i - 1]
    c = _ch[i]
    ids = [x["id"] for x in p["candidates"]]
    pos_el = ids.index(c["id"]) + 1
    out = []
    for pos, cand in enumerate(p["candidates"], 1):
        el = cand["id"] == c["id"]
        q = f'<i>×{c["quantity"]}</i>' if el and c["quantity"] > 1 else ""
        out.append(f'<div class="re-c{" elegido" if el else ""}">{producto(cand["id"], 104)}{q}<span>{pos}.º</span></div>')
    return (f'<div class="re-fila a-fila"><div class="re-pz"><b>{nombre}</b><span>elige el {pos_el}.º</span></div>'
            f'<div class="re-cs">{"".join(out)}</div></div>'), pos_el


_fe = [_fila_eleccion(1, "Sofá"), _fila_eleccion(3, "Biblioteca"), _fila_eleccion(5, "Alfombra")]
assert [x[1] for x in _fe] == [1, 5, 5] and PZ[2]["kinds"] == ["bookcase"], "la corrida cambió: revisar la fase 7 y su nota"
fase("rec-eleccion", "7", "Elección", "Opus mira las fotos y arma la lista: <em>es la generación</em>",
     prompt_tk("choose_combination_v2.md", [("Choose the pieces together, as one look", "Judge from the photos.")],
               resaltar=["Choose the pieces together, as one look, not each on its own. Judge from the photos."], cls="a-pr"),
     f'''<div class="a-filas"><span class="et">los {K} candidatos de la búsqueda, en orden, y el elegido</span>{"".join(x[0] for x in _fe)}</div>
<div class="a-dos" data-paso="1">{_fuente(_cm["images"], "imágenes", "en una sola llamada")}
  {_fuente(f"{N_HERO_PRIMERO} de {N_HERO}", "piezas con el 1.º", "no es un reranker", "tot")}</div>''',
     [f"Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco "
      f"candidatos de cada pieza, acá {_cm['images']} imágenes, cada uno con su id, su tipo y su medida. El prompt le pide "
      "elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir "
      "productos que trajo la búsqueda: si no, el código rechaza la respuesta.",
      "No es un reranker: arma un conjunto para este "
      f"cuarto. Acá tomó el primero de la búsqueda en {N_HERO_PRIMERO} de las {N_HERO} piezas; la biblioteca era el quinto "
      "candidato."],
     actual=["eleccion"], pines={"eleccion": [5]}, cls_banda="a-re")

# =============================================================================================
# 8 · Escena: los dos caminos (plantilla o escrita por el LLM) y la plantilla entera; cuál conviene
# lo dice el experimento 15, de trámite (sin números acá)
# =============================================================================================
_ESC_P = "scene_prompt_libre_v4.md"
_esc_txt = cuerpo_prompt(_ESC_P).strip()
assert "{products}" in _esc_txt and "{request}" in _esc_txt
_ESC_OP = '<div class="a-op"><div class="si"><b>plantilla</b><p>se completa con la lista y el pedido, sin LLM</p></div>' \
          '<div><b>escrita por el LLM</b><p>Opus escribe dónde va cada producto: una llamada más</p></div></div>'

fase("rec-escena", "8", "Escena", "El prompt de la imagen: <em>una plantilla, sin LLM</em>",
     _ESC_OP,
     prompt_tk(_ESC_P, [(_esc_txt[:20], _esc_txt[-30:])],
               resaltar=["the result must still be that same room, exactly", "Do not add, remove, move or enlarge any wall, window, door or opening",
                         "Add exactly these products and nothing else"],
               rotulo='completo · <i class="ph">{products}</i>: la lista · <i class="ph">{request}</i>: el pedido', cls="a-esc"),
     ["Fase ocho, la escena: el prompt para el modelo de imagen. Hay dos caminos: que Opus escriba dónde va cada producto, "
      "con una llamada más, o una plantilla sin LLM, que se completa con la lista y el pedido. Esta es la plantilla: una edición "
      "de la foto del cliente, con la misma cámara, sin tocar paredes ni ventanas, y exactamente estos productos. En la "
      "configuración final va la plantilla; por qué, lo vemos en los experimentos."],
     actual=["escena"], pines={"escena": [15]}, cls_banda="a-rs")

# =============================================================================================
# 9 y 10 · Imagen y control: una corrida que pasa al primer intento y otra que no pasa en ninguno
# =============================================================================================
SIFT = sift_pares(HERO / "room.jpg", HERO / "final.png", "loft")
_att = HERO_IMG["attempts"][0]
assert SIFT["inliers"] == _att["sift_inliers"], (SIFT["inliers"], _att["sift_inliers"])
_W = 480
_H = round(_W * SIFT["h"] / SIFT["w"])
# lo que cuentan la lámina y su nota
assert _att["ok"] and not any(a["ok"] for a in CLA_IMG["attempts"]) and len(CLA_IMG["attempts"]) == ROOM_CHECK["attempts"]
assert IMG_TOT["pasan"] == IMG_TOT["pasan_al_primero"], "alguna corrida final pasó el control al reintentar: revisar la fase 10"


def _sift_svg():
    s = _W / SIFT["w"]
    o = [f'<svg class="ri2-sift" viewBox="0 0 1180 {_H}" width="1180" height="{_H}" style="height:{_H}px" data-paso="1">']
    for i, (x0, y0, x1, y1) in enumerate(SIFT["pares"]):
        a = (x0 * s, y0 * s)
        b = (680 + x1 * s, y1 * s)
        if i % 4 == 0:
            o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
        o.append(f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4"/><circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="2.4"/>')
    o.append("</svg>")
    return "".join(o)


_prods = "".join(producto(h["id"], 50) for h, *_ in HERO_PICKS)
_ints = (f'<figure class="orig">{foto("rec-cla-room", CLA / "room.jpg", 117, 78, q=74)}<figcaption><b>la foto</b>original</figcaption></figure>'
         + "".join(f'<figure class="no">{foto(f"rec-cla-int{i}", CLA / a["image"], 117, 78, q=74)}'
                   f'<figcaption><b>{a["sift_inliers"]}</b>puntos</figcaption></figure>'
                   for i, a in enumerate(CLA_IMG["attempts"], 1)))
fase("rec-imagen", "9 y 10", "Imagen y control", "La imagen, y un control: <em>¿es el mismo cuarto?</em>",
     f'''<div class="rc-eq a-eq">{_fuente(CFG.furnish.max_image_products, "productos, como máximo", "Nano Banana 2, en modo edición")}
  {_fuente(f"≥ {ROOM_CHECK['min_inliers']}", "puntos del cuarto", "SIFT + RANSAC contra la original", "tot")}
  {_fuente(ROOM_CHECK["attempts"], "intentos, como máximo", "si no es el mismo cuarto")}</div>''',
     f'''<div class="ri2-par" style="height:{_H + 110}px">
  {foto("rec-hero-room2", HERO / "room.jpg", _W, _H, extra="ri2-a")}
  <div class="ri2-gen" data-hasta="1"><i>→</i><b>Nano Banana 2</b></div>
  {foto("rec-hero-final", HERO / "final.png", _W, _H, extra="ri2-b", q=80)}
  {_sift_svg()}
  <div class="ri2-prods" style="top:{_H + 22}px" data-hasta="1">{_prods}<span>+ el prompt de la escena</span></div>
  <p class="ri2-veredicto" style="top:{_H + 22}px" data-paso="1"><b>{SIFT["inliers"]} puntos</b>queda al primer intento</p>
</div>
<div class="ri2-der a-der" data-paso="1">
  <span class="et">otro pedido: las {len(CLA_IMG["attempts"])} descartadas</span>
  <div class="ri2-ints cuatro">{_ints}</div>
  {_fuente(f'{IMG_TOT["pasan"]} de {len(FINALES)}', "corridas pasan", "todas al primer intento", "tot")}</div>''',
     ["La imagen la hace Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los "
      f"productos y el prompt. Acepta 14 imágenes, así que muestra hasta {CFG.furnish.max_image_products} productos; el resto "
      "queda en la lista.",
      "Después, el control: si la imagen no conserva el cuarto, se genera otra, hasta "
      f"{ROOM_CHECK['attempts']} veces. El loft pasó al primer intento. Este otro pedido, un "
      "living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el que mejor conserva el "
      f"cuarto. En las {len(FINALES)} corridas finales pasan {IMG_TOT['pasan']}, todas al primer intento."],
     actual=["imagen", "control"], focos=["imagen", "control"], cls_banda="ri2 a-ri2")

# =============================================================================================
# 11 · Lista + imagen
# =============================================================================================
_ls = []
for _h, _q, _rk, _c in HERO_PICKS:
    _k = _h.get("kind", "")
    _ls.append(f'<div class="rl-l a-l">{producto(_h["id"], 40)}<b>{KIND_ES.get(_k, _k)}</b><span class="id">{_h["id"].removeprefix("abo-")}</span>'
               f'<span class="tr"><i>{_rk}.º de {K}</i></span><span class="q">×{_q}</span></div>')
fase("rec-lista", "11", "Lista + imagen", "Lo que sale: <em>cada línea, con su recorrido</em>",
     "",
     f'''<div class="ticket rl-tk a-tk"><div class="tk-cab"><b>Lista de compra</b><span>{sum(q for _, q, *_ in HERO_PICKS)} unidades</span></div>
  <div class="rl-l a-l cab"><span></span><span>pieza</span><span>id</span><span>en la búsqueda</span><span class="q">unid.</span></div>{"".join(_ls)}</div>
<div class="rl-fin a-fin">{foto("hero-final-rl", HERO / "final.png", 960, 640, q=82)}</div>''',
     ["Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, y la foto del mismo "
      "ambiente con ellos. Cada línea tiene su recorrido: el kind lo puso el plan, la búsqueda trajo los candidatos y la "
      "elección tomó uno, a veces no el primero: acá se ve el puesto de cada uno en la búsqueda."],
     actual=["salida"], cls_banda="a-rl")
