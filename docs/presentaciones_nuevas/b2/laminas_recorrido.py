"""El recorrido por las once fases del flujo, con el mapa que avanza (la fase actual encendida, las
vistas marcadas). Por fase: qué entra y qué sale, lo que decidimos (con el número del experimento
que lo decidió), el prompt que mandamos (extracto literal del archivo) y cómo lo reescribimos, y un
ejemplo real: el pedido del rincón de lectura (datos/resultados/amoblar/experimento-buen-pedido-estricto),
seguido de punta a punta, y la HEMNES, una biblioteca del catálogo, seguida de su foto a la lista."""

from __future__ import annotations

import json
import re

from datos import (AM, CFG, D, DESCR, HERO, HERO_CAND, HERO_CHOICE, HERO_REQ, ITEMS, KIND_ES, ROOM_CHECK, ROOT, esc, f1,
                   f2, f3, jload, medida, usd)
from piezas import flujo, foto, kick, producto
from recorrido import exps, mapa, prompt_tk, sift_pares, vector_chroma, versiones
from registro import lam

PLAN = jload(HERO / "1_searches.json")
PZ = PLAN["answer"]["pieces"]
ESCENA = jload(HERO / "4_scene.json")["answer"]["prompt"]
IMG = jload(HERO / "5_image.json")
HEM = "802.456.40"                       # la HEMNES: la biblioteca que se sigue por las fases
ABO_ID = "abo-B07QJLYCCL"
ABO_IT = next(json.loads(x) for x in (ROOT / "datos" / "procesados" / "abo_items.jsonl").read_text().splitlines()
              if json.loads(x)["id"] == ABO_ID)
ABO_ITEMS = [json.loads(x) for x in (ROOT / "datos" / "procesados" / "abo_items.jsonl").read_text().splitlines()]
ABO_DESC_IDS = {json.loads(x)["id"] for x in (ROOT / "datos" / "catalogo" / "abo" / "descripciones.jsonl").read_text().splitlines()}
_abo_idx = [it for it in ABO_ITEMS if it["id"] in ABO_DESC_IDS]
ABO_MEDIDAS = sum(1 for it in _abo_idx if it.get("dimensions_cm")) / len(_abo_idx)
IDX = jload(ROOT / "datos" / "cache" / "rag" / "index" / "todos-written_todos-qwen3" / "index.json")
HNSW = CFG["rag"]["hnsw"]
try:
    from amoblai.config import FurnishConfig
    SLACK = FurnishConfig().size_slack
except Exception:  # sin el paquete: el default del código fuente
    SLACK = float(re.search(r"size_slack: float = ([\d.]+)", (ROOT / "src" / "amoblai" / "config.py").read_text())[1])
K = CFG["furnish"]["candidates"]
LLM = CFG["furnish"]["llm"]
GEN = CFG["furnish"]["generators"]["nano_banana_2"]
assert IDX["products"] == D["prod_todos"]
# el pedido que se sigue usó la misma escena que la configuración final
assert jload(HERO / "4_scene.json")["prompt"] + ".md" == CFG["furnish"]["scene_prompt"]


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


# =============================================================================================
# 0 · El mapa: once fases, dos pipelines
# =============================================================================================
lam("rec-mapa", "El recorrido", "Recorrido", f'''
<div class="rm-izq">
  {kick("02", "arquitectura · el recorrido")}
  <h2 class="t chico">El recorrido: <em>once fases</em>, en dos pipelines</h2>
  <div class="rm-grupos">
    <div class="rm-g" data-en="1"><h3>1–3 · una vez, offline</h3><p>Describir e indexar el catálogo: se paga <b>una sola vez</b>.</p></div>
    <div class="rm-g" data-en="2"><h3>4–11 · por pedido</h3><p><b>Dos llamadas a Claude Opus 5.5</b> (plan y elección) y <b>una a Nano Banana 2</b> (la imagen, hasta {ROOM_CHECK["attempts"]} intentos). Embeddings, búsqueda y control corren locales.</p></div>
    <div class="rm-g" data-en="3"><h3>en cada fase</h3><p>Qué entra y qué sale, qué decidimos, <b>el prompt que mandamos</b> y el número del experimento que lo decidió.</p></div>
  </div>
</div>
<div class="rm-esq">{flujo(ruta=True)}</div>
<p class="remate rem-rm" data-paso="3">La elección solo puede tomar productos recuperados: la respuesta queda <mark>atada al catálogo</mark>.</p>''',
    ["El sistema, fase por fase, sobre este mapa: once fases en dos pipelines.",
     "Las tres primeras corren una vez, offline: el catálogo, una descripción de cada producto escrita por un VLM, y el "
     "índice vectorial.",
     "Las otras ocho corren en cada pedido: dos llamadas a Claude, el plan y la elección, y una al modelo de imagen. Lo demás "
     "es local.",
     "En cada fase, qué entra, qué sale, el prompt y el experimento que la decidió. Y una idea: la elección solo toma "
     "productos que trajo la búsqueda, así que la respuesta queda atada al catálogo."],
    35, focos=["", "indexing catalogo descripcion indice", "consulta foto plan busqueda eleccion escena imagen control salida", ""])

# =============================================================================================
# 1 · Catálogo
# =============================================================================================
_hem = ITEMS[HEM]
_abo_nom = re.sub(r"^Amazon Brand\s*[–-]\s*", "", ABO_IT["name"]).split(",")[0]
_abo_px = max(__import__("PIL.Image", fromlist=["Image"]).open(ROOT / ABO_IT["photos"][0]).size)


def _dim(d, ax):
    v = (d or {}).get(ax)
    return f"{v:g}".replace(".", ",") if v else None


def _regcard(fuente, pid, nombre, it, px, vendedor, foto_html):
    d = it.get("dimensions_cm")
    med = " × ".join(x or "—" for x in (_dim(d, "width"), _dim(d, "depth"), _dim(d, "height")))
    filas = [("tipo", it["category"]), ("kind", it["kind"]), ("medidas", f"{med} cm" if d else "—"), ("foto", f"{px} px")]
    dl = "".join(f'<div><dt>{a}</dt><dd{" class=falta" if b == "—" else ""}>{b}</dd></div>' for a, b in filas)
    return (f'<div class="reg-card">{foto_html}<div class="rg-d"><h4>{fuente} · <b>{pid}</b></h4><p class="rg-n">{esc(nombre)}</p>'
            f'<dl>{dl}</dl></div><q><span>el texto del vendedor</span>«{esc(vendedor)}»</q></div>')


_abo_vend = ABO_IT["description"].split(". ")[0] + "."
_cat_banda = f'''
<div class="rc-mitad"><div class="rc-col"><div class="rc-cifra"><span>{D["prod_855"]}</span><i>→</i><span class="co">{D["prod_819"]}</span></div>
  <p class="rc-src">IKEA · Tautkute et al., 2017<br>uso no comercial</p>
  <ul class="rc-l"><li><b>Fotos de {D["foto_lado"]} px</b></li><li><b>{D["asientos_sin_medida"]} de {D["asientos"]}</b> asientos sin medidas</li>
  <li>Al revisar: <b>{D["rev_afuera"]} afuera</b>, {D["rev_kinds"]} kinds corregidos</li></ul></div>
{_regcard("IKEA", HEM, _hem["name"], _hem, D["foto_lado"], _hem["description"], producto(HEM, 130))}</div>
<div class="rc-mitad"><div class="rc-col"><div class="rc-cifra"><span class="co">{D["n_abo"]}</span></div>
  <p class="rc-src">Amazon Berkeley Objects · Collins et al., CVPR 2022 · CC BY-NC 4.0</p>
  <ul class="rc-l"><li>Listados reales de Amazon</li><li><b>Medidas en el {round(ABO_MEDIDAS * 100)}%</b></li><li>Fotos de {_abo_px} px</li></ul></div>
{_regcard("ABO", ABO_ID.replace("abo-", ""), _abo_nom, ABO_IT, _abo_px, _abo_vend,
          foto("abo-sillon", ROOT / ABO_IT["photos"][0], 130, 130, modo="fit", estilo="background-color:#fff;background-size:contain"))}</div>'''
fase("rec-catalogo", "1", "Catálogo", "El catálogo: <em>dos fuentes</em>, un mismo registro",
     '<p class="rt-lead">Cada producto es un registro: <b>id, foto, tipo, kind y medidas</b> cuando las hay. Tipo, kind y medidas '
     'son para filtrar; la foto, para describirlo. El texto del vendedor casi no se usa: es marketing.</p>',
     _cat_banda,
     [f"La primera fase es el catálogo, la base de conocimiento del RAG. Dos fuentes: IKEA, el dataset de Tautkute y otros, "
      f"con {D['prod_855']} productos de living y comedor, {D['prod_819']} después de revisarlos, fotos chicas y casi sin "
      f"medidas en los asientos; y Amazon Berkeley Objects, listados reales, {D['n_abo']} productos con medidas en el "
      f"{round(ABO_MEDIDAS * 100)}%. Juntos, {D['prod_todos']}. Cada registro tiene tipo, kind y medidas, que filtran la "
      "búsqueda. Y el texto del vendedor de la HEMNES, «la madera maciza se siente natural», no sirve para buscar. Qué entra "
      "lo decidieron los experimentos 9 y 10."],
     actual=["catalogo"], pines={"catalogo": [9, 10]},
     extra=f'<div class="rc-tot"><b>{D["prod_todos"]}</b><span>productos en el catálogo del flujo: IKEA + ABO, en un mismo registro</span>'
           + exps([(9, "Ampliar y revisar", f"{D['prod_268']} → {D['prod_855']} → {D['prod_819']}"),
                   (10, "Sumar Amazon (ABO)", "para pedidos de otros estilos")]) + '</div>')

# =============================================================================================
# 2 · Descripción
# =============================================================================================
# cuántas descripciones de IKEA escribió cada versión del prompt (queda registrado en cada una)
_NV = __import__("collections").Counter(json.loads(x)["prompt"].split("@")[0] for x in
                                         (ROOT / "datos" / "catalogo" / "descripciones.jsonl").read_text().splitlines())
_vers_d = versiones([
    ("v2", f"{_NV['describe_product_v2']} muebles de IKEA.", "Las 8 líneas en el formato de la consulta, sin marca ni medidas, y nada de lo que no es: los embeddings no leen el «no».", ""),
    ("v3", f"+{_NV['describe_product_v3']} al ampliar: guardado, luces, textiles, deco.", "Qué mirar en una lámpara, un almohadón o un florero; un tercer ejemplo.", "actual"),
    ("api_v1", "ABO, por la API.", "Diez productos por llamada, y además el kind y si entra al catálogo.", ""),
], cls="rd-vers")
_pal = len(DESCR[HEM].split())
fase("rec-descripcion", "2", "Descripción", "Un VLM mira cada foto y <em>escribe 8 líneas fijas</em>",
     _vers_d,
     prompt_tk("describe_product_v3.md", [
         ("The images are photos of one product", "{height_cm} cm high."),
         ("Write its description for a search", "no full sentences:"),
         ("Type: the common name of what it is, two to six words", "two to six words"),
         ("Style: one to three of these", "contemporary, modern."),
         ("Shape: its silhouette and the details that make it recognizable", "visual weight for its type"),
         ("60 to 90 words in all.", "care or assembly."),
     ], resaltar=["Exactly these eight lines, in this order", "one to three of these, the closest first",
                  "Say only what the photos and the name show", "No brand, price, measurements"], ancho=1044)
     + f'''<div class="rd-ej" style="width:640px"><span class="et">entra la foto con su nombre y medidas · sale esto</span>
  <div class="ej-par">{producto(HEM, 120)}<p class="ej-por"><b>HEMNES</b> · {ITEMS[HEM]["kind"]} · {medida(ITEMS[HEM]["dimensions_cm"])}<br>
  {_pal} palabras<br>IKEA: subagentes de Claude Code (Opus 5.5)<br>ABO: Opus 5.5 por la API, {usd(D["costo_describir"], 3)} por producto</p></div>
  <div class="ficha-tk">{ficha(DESCR[HEM])}</div></div>''',
     ["Segunda fase: la descripción. Claude Opus 5.5 mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, "
      "uso, estilo, materiales, colores, forma, sensación y con qué combina. El estilo sale de una lista cerrada, y no van "
      "marca, precio ni medidas. A IKEA lo describieron subagentes de Claude Code; a Amazon, la API. El prompt tuvo tres "
      "versiones: la v2 para los muebles, la v3 para lámparas y deco, y la de la API, que además da el kind. Por qué "
      "describir: el experimento 1."],
     actual=["descripcion"], pines={"descripcion": [1]})

# =============================================================================================
# 3 · Índice
# =============================================================================================
VEC = vector_chroma(HEM)


def _indice_svg():
    W, H = 1728, 236
    o = [f'<svg class="ri-svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    # el documento
    o.append(f'<rect class="caja-t" x="0" y="8" width="372" height="{H - 16}" rx="6"/>')
    o.append('<text class="t-mono" x="20" y="38"><tspan class="k">documento · la descripción</tspan></text>')
    lineas = DESCR[HEM].strip().splitlines()
    for i, l_ in enumerate(lineas[:5]):
        a, b = l_.split(":", 1)
        b = b.strip()
        b = b if len(a) + len(b) < 33 else b[:31 - len(a)].rstrip(" ,") + "…"
        o.append(f'<text class="t-mono" x="20" y="{72 + i * 26}"><tspan class="k">{esc(a)}:</tspan> <tspan class="d">{esc(b)}</tspan></text>')
    o.append(f'<text class="t-mono" x="20" y="{72 + 5 * 26}"><tspan class="k">… 8 líneas, {_pal} palabras</tspan></text>')
    # flecha
    o.append('<path class="flr" d="M384 120H436" marker-end="url(#pf)"/>')
    # el modelo
    o.append('<rect class="caja-m" x="448" y="22" width="372" height="196" rx="10"/>')
    o.append('<text class="t-mod" x="472" y="72">Qwen3-Embedding</text>')
    o.append('<text class="t-mod-s" x="472" y="104">0.6B · local, en CPU · Apache 2.0</text>')
    o.append('<text class="t-mod-s" x="472" y="140">pooling: el último token</text>')
    o.append('<text class="t-mod-s" x="472" y="170">la consulta entra igual,</text>')
    o.append('<text class="t-mod-s" x="472" y="194">sin instrucción de consulta</text>')
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
    o.append(f'<text class="t-vn" x="{x0}" y="40">{VEC["dim"]} componentes</text>')
    o.append(f'<text class="t-v" x="{x0}" y="222">las primeras {len(vs)} · norma {f1(VEC["norma"])}</text>')
    o.append(f'<path class="flr" d="M{x0 + len(vs) * (bw + 1) + 14} 120H{x0 + len(vs) * (bw + 1) + 62}" marker-end="url(#pf)"/>')
    # el registro en ChromaDB
    rx = x0 + len(vs) * (bw + 1) + 76
    md = VEC["metadata"]
    o.append(f'<rect class="caja-t" x="{rx}" y="8" width="{W - rx}" height="{H - 16}" rx="6"/>')
    o.append(f'<text class="t-mono" x="{rx + 20}" y="38"><tspan class="k">ChromaDB · un registro</tspan></text>')
    filas = [("id", HEM), ("embedding", f"[{VEC['dim']} números]"), ("document", "la descripción"),
             ("category", md["category"]), ("kind", md["kind"]),
             ("w · d · h", " · ".join(f"{md[a]:g}" for a in ("width", "depth", "height")))]
    for i, (a, b) in enumerate(filas):
        o.append(f'<text class="t-mono" x="{rx + 20}" y="{68 + i * 24}"><tspan class="k">{a}</tspan></text>'
                 f'<text class="t-mono" x="{rx + 128}" y="{68 + i * 24}"><tspan class="d">{esc(b).replace("-1", "−1")}</tspan></text>')
    o.append(f'<text class="t-mono chico" x="{rx + 20}" y="{H - 22}"><tspan class="k">HNSW · coseno · ef_search {HNSW["ef_search"]} · M {HNSW["max_neighbors"]}</tspan></text>')
    o.append("</svg>")
    return "".join(o)


fase("rec-indice", "3", "Índice", "Un vector por producto: <em>la descripción entera</em>",
     '<p class="rt-lead"><b>Qué</b> se embebe: la descripción, un documento por producto. <b>Con qué</b>: Qwen3-Embedding, '
     f'local, {VEC["dim"]} componentes. <b>Dónde</b>: ChromaDB, con la metadata al lado para los filtros. Así queda la HEMNES:</p>',
     _indice_svg() + exps([
         (1, "Se embebe la descripción del VLM", "no el texto del vendedor"),
         (2, "Qwen3-Embedding-0.6B", "contra hashing y BGE-base; la v0 embebía recortes de fotos con CLIP, SigLIP 2 y DINO"),
         (6, "ChromaDB con HNSW", "contra recorrer todos los vectores con numpy"),
         (4, "Un documento por producto", f"unas {_pal} palabras, sin partir en chunks"),
         (5, f"{VEC['dim']} dimensiones", "Matryoshka: se puede truncar sin reentrenar"),
         ("—", "La metadata, para filtrar", "tipo, kind y medidas; la que falta va como −1 y pasa cualquier tope"),
     ], cls="ri-dec"),
     [f"El índice. Embebemos la descripción entera, un documento por producto, de unas {_pal} palabras. El modelo es "
      f"Qwen3-Embedding, de 600 millones de parámetros, local y en CPU: toma el último token y da {VEC['dim']} componentes. "
      "La consulta entra igual, sin instrucción, porque ya está escrita como una descripción. Los vectores van a ChromaDB, con "
      "HNSW en coseno, y al lado la metadata que leen los filtros; la que falta va como menos uno y pasa cualquier tope. Cada "
      "decisión tiene su experimento: el 1, el 2, el 4, el 5 y el 6."],
     actual=["indice"], pines={"indice": [2, 4, 5, 6]}, cls_banda="ri")

# =============================================================================================
# 4 y 5 · Foto + pedido → plan
# =============================================================================================
_p0 = PZ[0]


def _md(p):
    v = [p.get(f"max_{a}_cm") for a in ("width", "depth", "height")]
    return "≤ " + " × ".join("—" if x is None else f"{x:g}" for x in v) if any(v) else "—"


_pzs = "".join(f'<div class="rp-pz{" uno" if i == 0 else ""}"><span class="q">{i + 1}</span><b>{esc(", ".join(p["kinds"]))}</b>'
               f'<span class="md">{_md(p)}</span></div>' for i, p in enumerate(PZ))
_room = PLAN["answer"]["room"]
fase("rec-plan", "4 y 5", "Foto, pedido y plan", "Del pedido a <em>una consulta por pieza</em>",
     f'<p class="rt-lead rp-lead">«{esc(HERO_REQ)}»</p>',
     f'''<div class="rp-ent">{foto("rec-hero-room", HERO / "room.jpg", 440, 330)}
  <p class="rp-vista">entra la foto del ambiente vacío y el pedido; opcional, otra foto desde otro ángulo, que ve Claude y no el modelo de imagen</p></div>
<div class="ticket rp-plan" data-paso="1"><div class="tk-cab"><b>Plan · {len(PZ)} piezas</b><span>Claude Opus 5.5<br>effort {LLM["effort"]}</span></div>
  <p class="rp-room">«{esc(_room[:150].rsplit(" ", 1)[0])}…»</p>
  <div class="rp-pz" style="border-top:0;color:var(--tinta-3)"><span></span><span>kind (lista cerrada)</span><span class="md">medida máx., cm</span></div>
  {_pzs}</div>
<div class="rp-q" data-paso="1"><span class="et">la consulta de la pieza 1, en las 8 líneas del catálogo</span>
  <div class="ficha-tk">{ficha(_p0["query"])}</div>
  <p class="rp-why"><span>why</span>«{esc(_p0["why"])}»</p></div>''',
     ["Fases 4 y 5. Entra una foto del ambiente vacío y el pedido en texto libre, como este rincón de lectura. Puede entrar "
      "otra foto del mismo ambiente, que ve Claude pero no el modelo de imagen.",
      f"El plan es la primera llamada a Claude. Lee el ambiente como un diseñador y decide las piezas: acá, {len(PZ)}. Para "
      "cada una elige el kind de una lista cerrada, que después es un filtro, estima la medida máxima que entra, y escribe el "
      "producto ideal en las mismas ocho líneas que las descripciones. Ese es nuestro query rewriting: la consulta habla como "
      "los documentos."],
     actual=["foto", "plan"], pines={"plan": [6]}, focos=["foto", "plan"])

# =============================================================================================
# 5 · El prompt del plan y sus versiones
# =============================================================================================
fase("rec-plan-prompt", "5", "Plan", "El prompt del plan, <em>reescrito cuatro veces</em>",
     '<p class="rt-lead">Cada versión salió de algo que vimos en una corrida. Lo que no cambió desde la v2: '
     '<b>la consulta en las 8 líneas del catálogo</b>, que es lo que pone a prueba el experimento 6.</p>',
     prompt_tk("search_query_v4.md", [
         ("You are an experienced interior designer.", 'own words: "{request}"'),
         ("Then decide which pieces to add", "the most important first."),
         ("- If they name a piece, give them that piece", "A chair is not an armchair"),
         ('  - "kinds": from the list below', "a desk chair)."),
         ('  - "max_width_cm"', "otherwise null."),
         ('  - "query": the ideal product', "The Type line starts with the kind."),
     ], resaltar=["as many as the request and the room call for", "A chair is not an armchair", "the one kind the piece is",
                  "the most it can measure to fit where it goes", "the ideal product in the catalog's eight lines"], ancho=1044)
     + versiones([
         ("v1", "Una silla no es un sillón.", "Le dio un sillón a quien pidió «una silla» para un escritorio que ya tenía una (no quedó en el repo: lo cuentan las notas de la v2).", "fuera"),
         ("v2", "La pieza como la nombró el usuario.", "El kind de una lista cerrada, que es el filtro; las medidas máximas; la consulta en las 8 líneas.", ""),
         ("v3", "Terminar el ambiente.", "La primera imagen era un living largo con cuatro muebles y nada más: hasta 6 piezas, y lámparas y deco si se pide amoblar.", ""),
         ("v4", "Sin tope de piezas.", "Un rincón de lectura ya llegaba a 6: tantas como pidan el pedido y el cuarto.", "actual"),
     ], cls="rpp-vers"),
     ["Es el prompt que más reescribimos. La primera versión le dio un sillón a alguien que pidió una silla para su "
      "escritorio. La v2 pide la pieza como la nombró el usuario, el kind de una lista cerrada, las medidas máximas y la "
      "consulta en ocho líneas. Con la primera imagen, un living largo con cuatro muebles y nada más, la v3 pide terminar el "
      "ambiente, hasta seis piezas. Como un rincón de lectura ya llegaba a seis, la v4 saca el tope. Si conviene reescribir "
      "la consulta entera, lo responde el experimento 6."],
     actual=["plan"], pines={"plan": [6]})

# =============================================================================================
# 6 · Búsqueda
# =============================================================================================
try:
    from amoblai.rag.filters import Filters
    _f = Filters(kinds=_p0["kinds"], **{f"max_{a}_cm": round(_p0[f"max_{a}_cm"] * (1 + SLACK), 1)
                                         for a in ("width", "depth", "height") if _p0.get(f"max_{a}_cm") is not None})
    WHERE = _f.where()
except Exception:  # sin el paquete
    WHERE = None


def _json_ancho(o, ind: int, ancho: int) -> str:
    """JSON compacto que se parte en líneas solo donde no entra en `ancho` caracteres."""
    t = json.dumps(o, ensure_ascii=False)
    if ind + len(t) <= ancho:
        return t
    if isinstance(o, dict) and len(o) == 1:
        (k, v), = o.items()
        cab = json.dumps(k) + ": "
        return "{" + cab + _json_ancho(v, ind, ancho) + "}"
    if isinstance(o, list):
        sang = " " * (ind + 2)
        return "[\n" + ",\n".join(sang + _json_ancho(x, ind + 2, ancho) for x in o) + "]"
    return t


def _where_html(w) -> str:
    t = esc("where = " + _json_ancho(w, 0, 62))
    t = re.sub(r'"(kind|category|width|depth|height)"', r'<b>"\1"</b>', t)
    t = re.sub(r'"(\$\w+)"', r'<u>"\1"</u>', t)
    return re.sub(r"(\d+\.\d)", r"<i>\1</i>", t)


_cands = sorted(HERO_CAND[0]["candidates"], key=lambda c: -(c.get("score") or 0))
_cs = "".join(f'<div class="rb-c{" uno" if c["id"] == HEM else ""}">{producto(c["id"], 130)}<em>{f3(c["score"])}</em>'
              f'<b>{esc(c.get("name") or "")}</b><span>{c["id"]}</span></div>' for c in _cands)
fase("rec-busqueda", "6", "Búsqueda", "Filtro duro y coseno: <em>la consulta habla como el documento</em>",
     f'<p class="rt-lead">Primero el filtro, como <code>where</code> de ChromaDB: el kind del plan y las medidas máximas, con '
     f'{round(SLACK * 100)}% de margen porque salen de una foto. Después, el coseno con Qwen3 entre la consulta y cada '
     f'descripción que pasó: quedan los <b>{K} más cercanos</b> por pieza.</p>',
     f'''<div><div class="rb-cab"><span class="et">la consulta · la escribió el plan</span><span></span><span class="et">el documento · lo escribió el VLM</span></div>
  <div class="rb-par"><div class="ficha-tk">{ficha(_p0["query"])}</div>
    <div class="rb-cos"><i>↔</i><b>{f3(_cands[0]["score"])}</b><span>coseno</span></div>
    <div class="ficha-tk">{ficha(DESCR[HEM])}</div></div>
  <p class="rb-nota">El filtro lo decidió el <b>experimento 3</b>. Esta corrida es del 25/10 y traía 3 candidatos por pieza; desde el <b>experimento 8</b> son {K}.</p></div>
<div class="rb-der">
  {f'<pre class="rb-where">{_where_html(WHERE)}</pre>' if WHERE else ""}
  <div><span class="et">lo que trajo para la pieza 1</span><div class="rb-cands">{_cs}</div></div>
</div>''',
     [f"La búsqueda tiene dos pasos. Primero un filtro duro, que en ChromaDB va como where: el kind del plan y las medidas "
      f"máximas, con {round(SLACK * 100)}% de margen porque salen de una foto. Después, el coseno entre la consulta y cada "
      "descripción que pasó. Acá se ve por qué funciona: la consulta del plan y el documento del VLM hablan igual, línea por "
      f"línea, y la HEMNES sale primera. Quedan los {K} más cercanos; esta corrida es de antes del experimento 8 y traía 3. "
      "El filtro lo decidió el experimento 3."],
     actual=["busqueda"], pines={"busqueda": [3, 8]})

# =============================================================================================
# 7 · Elección
# =============================================================================================
_ch = {c["piece"]: c for c in HERO_CHOICE}


def _fila_eleccion(i, nombre, why_corte):
    p = HERO_CAND[i - 1]
    cs = sorted(p["candidates"], key=lambda c: -(c.get("score") or 0))
    c = _ch[i]
    out = []
    for pos, cand in enumerate(cs, 1):
        el = cand["id"] == c["id"]
        q = f'<i>×{c["quantity"]}</i>' if el and c["quantity"] > 1 else ""
        out.append(f'<div class="re-c{" elegido" if el else ""}">{producto(cand["id"], 88)}{q}<span>{pos}.º · {f2(cand["score"])}</span></div>')
    why = c["why"]
    assert why_corte in why
    i0 = why.index(why_corte)
    frag = ("…" if i0 else "") + why[i0:i0 + 150].rsplit(" ", 1)[0].rstrip(",;") + "…"
    pos_el = [x["id"] for x in cs].index(c["id"]) + 1
    return (f'<div class="re-fila"><div class="re-pz"><b>{nombre}</b><span>elige el {pos_el}.º por coseno</span></div>'
            f'<div class="re-cs">{"".join(out)}</div><p class="re-why">«{esc(frag)}»</p></div>')


fase("rec-eleccion", "7", "Elección", "Claude mira las fotos y <em>elige la combinación</em>",
     '<p class="rt-lead">La segunda llamada a Claude Opus 5.5: la foto del cuarto y las fotos de los candidatos de <b>todas las '
     'piezas juntas</b>, cada uno con su tipo y sus medidas. Elige un producto por pieza pensando en el conjunto, y cuántas unidades.</p>',
     f'''<div class="re-izq">{prompt_tk("choose_combination_v2.md", [
         ("We are adding {pieces} piece(s)", "in the same order:"),
         ("Choose the pieces together, as one look", "Judge from the photos."),
         ('Then say how many units of it go in the room ("quantity"). Usually 1.', "Usually 1."),
         ("0 when none of its candidates suits this room", "left out of the list."),
     ], resaltar=["Choose the pieces together, as one look, not each on its own. Judge from the photos.", '("quantity")',
                  "0 when none of its candidates suits this room"], ancho=760, cls="chico")}
  {versiones([("v1", "Un producto por pieza, la mejor combinación.", "Los candidatos con su línea Type y su medida, no el nombre de la tienda.", ""),
              ("v2", "Y cuántas unidades.", "0 deja la pieza afuera; más de una, sillas alrededor de una mesa.", "actual")])}</div>
<div class="re-der"><span class="et">tres de las {len(PZ)} piezas de este pedido: los candidatos en orden de coseno y el elegido</span>
  {_fila_eleccion(1, "Biblioteca", "dos unidades")}
  {_fila_eleccion(3, "Lámpara de pie", "El brazo articulado")}
  {_fila_eleccion(5, "Alfombra", "No hay alfombras redondas")}</div>''',
     ["La elección es la segunda llamada a Claude. Ve la foto del cuarto y las fotos de los candidatos de todas las piezas "
      "juntas, y elige la combinación, no el mejor de cada una por separado; la v2 del prompt agregó cuántas unidades. Acá "
      "eligió dos HEMNES para llenar la pared; para la lámpara, la tercera por coseno, porque el brazo articulado sirve para "
      "leer; y avisó que no hay alfombras redondas. Es un reranker que mira fotos: lo mostraron los experimentos 7 y 8."],
     actual=["eleccion"], pines={"eleccion": [7, 8]})

# =============================================================================================
# 8 · Escena
# =============================================================================================
fase("rec-escena", "8", "Escena", "El prompt de la imagen: <em>una plantilla, sin LLM</em>",
     '<p class="rt-lead">No lo escribe Claude: es una plantilla que se llena con el pedido y los productos elegidos, con su tipo, '
     'sus medidas y cuántas unidades. Probamos que lo escribiera el LLM: decidió el <b>experimento 12</b>.</p>',
     f'''<div class="rs-arbol">
  <div class="rs-rama pierde"><h3>la escribe Claude · scene_prompt</h3>{versiones([
      ("v1", "Dónde va cada producto.", "Hacia dónde mira y qué tamaño tiene al lado de lo que hay.", ""),
      ("v2", "Anclado a lo que se ve.", "La primera imagen dejó todo cerca de la cámara y con la luz del catálogo.", "")])}</div>
  <div class="rs-rama gana"><h3>plantilla, sin LLM · scene_prompt_libre</h3>{versiones([
      ("v1", "El modelo de imagen decide dónde.", "", ""),
      ("v2", "Repetir los muebles por módulos.", "Para que una biblioteca no sea un mueble chico contra una pared enorme.", ""),
      ("v3", "Las cantidades de la elección.", "", ""),
      ("v4", "Edición estricta.", "Inventó una ventana y movió la biblioteca: es la foto del cliente, el mismo cuarto, y solo estos productos.", "actual")])}</div></div>
{prompt_tk("scene_prompt_libre_v4.md", [
         ("Edit image 1. It is a photo of the client's own room", "lens and framing;"),
         ("Do not add, remove, move or enlarge any wall", "do not change its light."),
         ("Images 2 to", "size unknown\nimage 4: swing-arm floor lamp with drum shade, size unknown"),
         ("Add exactly these products and nothing else:", "lamps, plants, rugs or decoration than these"),
         ("The client asked:", "acogedor."),
         ("Arrange the products as an interior designer would", "lit by this room's light."),
     ], resaltar=["the result must still be that same room, exactly", "Do not add, remove, move or enlarge any wall, window, door or opening",
                  "image 2: tall solid wood bookcase, 90 cm wide, 2 units", "Add exactly these products and nothing else"],
     texto=ESCENA, titulo="scene_prompt_libre_v4.md · lleno", rotulo="el de esta corrida, tal cual se mandó", cls="rs-tk")}''',
     ["La escena es el prompt del modelo de imagen. Primero lo escribía Claude, diciendo dónde va cada producto. En paralelo "
      "probamos una plantilla sin LLM, donde el modelo de imagen decide dónde va cada cosa. La v3 le pasó las cantidades, y "
      "la v4, después de que el modelo inventara una ventana, es una edición estricta: la foto del cliente, el mismo cuarto, y "
      "solo estos productos. A la derecha, el prompt lleno de este pedido, con su tipo, su medida y sus unidades. La "
      "plantilla la decidió el experimento 12."],
     actual=["escena"], pines={"escena": [12]})

# =============================================================================================
# 9 y 10 · Imagen y control
# =============================================================================================
SIFT = sift_pares(HERO / "room.jpg", HERO / "final.png", "hero")
_att = IMG["attempts"][0]
assert SIFT["inliers"] == _att["sift_inliers"], (SIFT["inliers"], _att["sift_inliers"])
_W, _H = 480, 360


def _sift_svg():
    s = _W / SIFT["w"]
    o = [f'<svg class="ri2-sift" viewBox="0 0 1180 {_H}" width="1180" height="{_H}" data-paso="1">']
    for i, (x0, y0, x1, y1) in enumerate(SIFT["pares"]):
        a = (x0 * s, y0 * s)
        b = (680 + x1 * s, y1 * s)
        if i % 3 == 0:
            o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}"/>')
        o.append(f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.6"/><circle cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="2.6"/>')
    o.append("</svg>")
    return "".join(o)


_prods = "".join(producto(c["id"], 50) for c in HERO_CHOICE)
_cl = D["cab_liv"]
_ints = "".join(
    f'<figure class="{"si" if a["ok"] else "no"}">{foto(f"rec-cab-int{i}", AM / "caballito-living" / a["image"], 126, 95, q=74)}'
    f'<figcaption><b>{a["sift_inliers"]}</b>{"queda" if a["ok"] else "descartada"}</figcaption></figure>'
    for i, a in enumerate(_cl["attempts"], 1))
fase("rec-imagen", "9 y 10", "Imagen y control", "La imagen, y un control: <em>¿es el mismo cuarto?</em>",
     f'<p class="rt-lead"><b>Nano Banana 2</b> (Gemini 3.1 Flash Image), por fal, en modo edición, a {GEN["resolution"]}: '
     f'{usd(GEN["usd_per_image"][GEN["resolution"]])} por imagen. Entran la foto del cuarto y una foto por producto. Después, '
     f'<b>SIFT + RANSAC</b> contra la foto original: si no es el mismo cuarto, se descarta y se pide otra.</p>',
     f'''<div class="ri2-par">
  {foto("rec-hero-room2", HERO / "room.jpg", _W, _H, extra="ri2-a")}
  <div class="ri2-gen" data-hasta="1"><i>→</i><b>Nano Banana 2</b><span>{IMG["meta"]["images_in"]} imágenes<br>{round(IMG["meta"]["latency_s"])} s</span></div>
  {foto("rec-hero-final", HERO / "final.png", _W, _H, extra="ri2-b", q=80)}
  {_sift_svg()}
  <div class="ri2-prods" data-hasta="1">{_prods}<span>+ el prompt de la escena</span></div>
  <p class="ri2-veredicto" data-paso="1"><b>{SIFT["inliers"]} puntos</b>reencontrados, la cámara quieta: queda al primer intento</p>
</div>
<div class="ri2-der" data-paso="1">
  <p class="ri2-regla">Queda si reencuentra <b>al menos {ROOM_CHECK["min_inliers"]} puntos</b> y la cámara se movió <b>menos del {f1(ROOM_CHECK["max_shift"] * 100)}%</b>; si no, otra imagen, <b>hasta {ROOM_CHECK["attempts"]}</b>.</p>
  <span class="et">en otro departamento: dos descartadas</span>
  <div class="ri2-ints">{_ints}</div></div>''',
     ["La imagen la hace Nano Banana 2, el modelo de imagen de Gemini, por fal, en modo edición: recibe la foto del cuarto, "
      f"una foto por producto y el prompt de la escena. Cuesta {round(GEN['usd_per_image'][GEN['resolution']] * 100)} "
      "centavos de dólar.",
      "Como a veces redecora, hay un control automático: SIFT busca puntos de la foto original en la generada, y RANSAC "
      f"verifica que encajen con el mismo encuadre. Si reencuentra al menos {ROOM_CHECK['min_inliers']} y la cámara no se "
      f"movió, queda; si no, se pide otra, hasta {ROOM_CHECK['attempts']} veces. Acá pasó al primer intento, con "
      f"{SIFT['inliers']} puntos. En otro departamento descartó dos y se quedó con la tercera."],
     actual=["imagen", "control"], pines={"imagen": [12, 13], "control": [12]}, focos=["imagen", "control"], cls_banda="ri2")

# =============================================================================================
# 11 · Lista + imagen
# =============================================================================================
_info = {c["id"]: c for p in HERO_CAND for c in p["candidates"]}
_ls = []
for ch in HERO_CHOICE:
    p = HERO_CAND[ch["piece"] - 1]
    cs = sorted(p["candidates"], key=lambda c: -(c.get("score") or 0))
    pos = [c["id"] for c in cs].index(ch["id"]) + 1
    k_ = _info[ch["id"]].get("kind", "")
    _ls.append(f'<div class="rl-l">{producto(ch["id"], 34)}<b>{KIND_ES.get(k_, k_)}</b><span class="id">{ch["id"]}</span>'
               f'<span class="tr">plan → búsqueda <i>{pos}.º de {len(cs)}</i> → elección</span><span class="q">×{ch["quantity"]}</span></div>')
fase("rec-lista", "11", "Lista + imagen", "Lo que sale: <em>cada línea, con su recorrido</em>",
     '<p class="rt-lead">La lista sale de la elección: <b>productos que existen</b>, con su id y cuántas unidades. La imagen, de '
     'las fotos de esos mismos productos. Cada decisión de este recorrido salió de un experimento: son trece.</p>',
     f'''<div class="ticket rl-tk"><div class="tk-cab"><b>Lista de compra</b><span>{len(HERO_CHOICE)} productos · {sum(c["quantity"] for c in HERO_CHOICE)} unidades</span></div>{"".join(_ls)}</div>
<div class="rl-fin">{foto("hero-final", HERO / "final.png", 640, 480, q=82)}<p>la imagen: el mismo cuarto, con esos productos</p></div>''',
     ["Y la última fase es lo que sale: la lista y la imagen. Cada línea tiene su recorrido: el kind lo puso el plan, la "
      "búsqueda trajo los candidatos y la elección tomó uno, a veces no el primero por coseno, y cuántas unidades. La imagen "
      "sale de las fotos de esos mismos productos. Cada decisión que fuimos nombrando salió de un experimento: son trece."],
     actual=["salida"])
