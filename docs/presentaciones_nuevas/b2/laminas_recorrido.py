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

from PIL import Image

from datos import (ABO_ITEMS, C_DESC, C_SCENE, CFG, CLA, CLA_IMG, CLA_SLUG, D, DESCR_TODO, DOC, ESC_FALLARON_1, ESC_RESCATADOS,
                   FILTRO_MAX, FINALES, GEN, HERO, IMG_LLM, IMG_PL,
                   HERO_CHOICE, HERO_CHOOSE, HERO_COSTO_CLAUDE, HERO_FOUND, HERO_IMG, HERO_PICKS, HERO_PLAN, HERO_PZ, HERO_REQ,
                   HERO_SCENE, HERO_SLUG, IMG_TOT, ITEMS, K, KIND_ES, N_HERO, N_HERO_ABO, N_HERO_PRIMERO, NO_PASAN, PASAN,
                   ROOM_CHECK, ROOT, SLACK, SOFA, VQ, credito, esc, f1, f2, medida, miles, tipo_de, usd)
from piezas import flujo, foto, kick, producto
from recorrido import cuerpo_prompt, exps, mapa, prompt_tk, sift_pares, vector_chroma, versiones
from registro import lam

PZ = HERO_PZ
ESCENA = HERO_SCENE["answer"]["prompt"]
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
  <h2 class="t chico">El recorrido: <em>once fases</em>, en dos pipelines</h2>
  <div class="rm-grupos">
    <div class="rm-g" data-en="1"><h3>1–3 · una vez, offline</h3><p>Describir e indexar el catálogo: se paga <b>una sola vez</b>.</p></div>
    <div class="rm-g" data-en="2"><h3>4–11 · por pedido</h3><p><b>Tres llamadas pagas</b>: Claude Opus 5.5 en el plan y en la elección, y Nano Banana 2 en la imagen. La búsqueda y el control corren locales.</p></div>
    <div class="rm-g" data-en="3"><h3>en cada fase</h3><p>Qué entra y qué sale, qué decidimos y <b>el prompt que mandamos</b>, siguiendo un pedido real con la configuración final.</p></div>
  </div>
</div>
<div class="rm-esq">{flujo(ruta=True)}</div>
<p class="remate rem-rm" data-paso="3">La elección solo puede tomar productos recuperados: la respuesta queda <mark>atada al catálogo</mark>.</p>''',
    ["El sistema, fase por fase, sobre este mapa: once fases en dos pipelines.",
     "Las tres primeras corren una vez, offline: el catálogo, la descripción de cada producto y el índice.",
     "Las otras ocho corren en cada pedido: el plan decide las piezas, la búsqueda trae "
     "candidatos, la elección arma la lista, y después la escena, la imagen y el control. Se pagan solo tres "
     "llamadas: Opus en el plan y en la elección, y Nano Banana 2 en la imagen.",
     "En cada fase, qué entra, qué sale y el prompt. Y una idea: la respuesta queda atada al catálogo."],
    35, focos=["", "indexing catalogo descripcion indice", "consulta foto plan busqueda eleccion escena imagen control salida", ""])

# =============================================================================================
# 1 · Catálogo
# =============================================================================================
_lamp = ITEMS[LAMP]
_sofa = ABO_ITEMS[SOFA]
_sofa_nom = re.sub(r"^Amazon Brand\s*[–-]\s*", "", _sofa["name"]).split(",")[0]
_abo_px = max(Image.open(ROOT / _sofa["photos"][0]).size)


def _dim(d, ax):
    v = (d or {}).get(ax)
    return f"{v:g}".replace(".", ",") if v else None


def _regcard(fuente, pid, nombre, it, px, vendedor):
    d = it.get("dimensions_cm")
    med = " × ".join(x or "—" for x in (_dim(d, "width"), _dim(d, "depth"), _dim(d, "height")))
    filas = [("tipo", it["category"]), ("kind", it["kind"]), ("medidas", f"{med} cm" if d else "—"), ("foto", f"{px} px")]
    dl = "".join(f'<div><dt>{a}</dt><dd{" class=nohay" if b == "—" else ""}>{b}</dd></div>' for a, b in filas)
    return (f'<div class="reg-card">{producto(pid, 130)}<div class="rg-d"><h4>{fuente} · <b>{pid.removeprefix("abo-")}</b></h4>'
            f'<p class="rg-n">{esc(nombre)}</p><dl>{dl}</dl></div><q><span>el texto del vendedor</span>«{esc(vendedor)}»</q></div>')


_cat_banda = f'''
<div class="rc-mitad"><div class="rc-col"><div class="rc-cifra"><span>{D["prod_855"]}</span><i>→</i><span class="co">{D["prod_819"]}</span></div>
  <p class="rc-src">IKEA · Tautkute et al., 2017<br>uso no comercial</p>
  <ul class="rc-l"><li><b>Fotos de {D["foto_lado"]} px</b></li><li>Con alguna medida, <b>el {round(100 * D["ikea_con_medida"])}%</b>; ningún sofá ni sillón</li>
  <li>Al revisar: <b>{D["rev_afuera"]} afuera</b>, {D["rev_kinds"]} kinds corregidos</li></ul></div>
{_regcard("IKEA", LAMP, _lamp["name"], _lamp, D["foto_lado"], _lamp["description"])}</div>
<div class="rc-mitad"><div class="rc-col"><div class="rc-cifra"><span class="co">{D["n_abo"]}</span></div>
  <p class="rc-src">Amazon Berkeley Objects · Collins et al., CVPR 2022 · CC BY-NC 4.0</p>
  <ul class="rc-l"><li>Listados reales: de {miles(DOC["abo_listados"])} quedaron {D["n_abo"]}</li><li><b>Medidas en el {round(D["abo_con_medida"] * 100)}%</b></li><li>Fotos de {_abo_px} px</li></ul></div>
{_regcard("ABO", SOFA, _sofa_nom, _sofa, _abo_px, _sofa["description"].split(". ")[0] + ".")}</div>'''
fase("rec-catalogo", "1", "Catálogo", "El catálogo: <em>dos fuentes</em>, un mismo registro",
     '<p class="rt-lead">Cada producto es un registro: <b>id, foto, tipo, kind y medidas</b> cuando las hay. Tipo, kind y medidas '
     'son para filtrar; la foto, para describirlo. El texto del vendedor casi no se usa: es marketing. Estos dos van a terminar '
     'en la lista del pedido que seguimos.</p>',
     _cat_banda,
     [f"Fase uno, el catálogo: la base de conocimiento. Son dos. El dataset de IKEA: lo ampliamos a {D['prod_855']} productos "
      f"de living y comedor y, revisado mirando cada foto, quedaron {D['prod_819']}. Y Amazon Berkeley Objects, listados "
      f"reales de Amazon: de casi 150 mil quedaron {D['n_abo']}. El flujo usa los dos, {miles(D['prod_todos'])} productos. "
      "Así viene una lámpara de IKEA: el texto es "
      "marketing y no tiene medidas. Y así un sofá de Amazon, con medidas. Qué catálogo usar lo midió el experimento 6."],
     actual=["catalogo"], pines={"catalogo": [6]},
     extra=f'<div class="rc-tot"><b>{miles(D["prod_todos"])}</b><span>productos en el catálogo del flujo: IKEA + ABO, en un mismo registro</span>'
           + exps([(6, "IKEA + Amazon (ABO)", f"de punta a punta, en {D['n_ambientes_vacios']} ambientes"),
                   ("—", "Ampliar y revisar", f"{D['prod_268']} → {D['prod_855']} → {D['prod_819']}: decisiones de datos")]) + '</div>')

# =============================================================================================
# 2 · Descripción
# =============================================================================================
# cuántas descripciones de IKEA escribió cada versión del prompt (queda registrado en cada una)
_NV = collections.Counter(json.loads(x)["prompt"].split("@")[0] for x in
                          (ROOT / "datos" / "catalogo" / "descripciones.jsonl").read_text().splitlines())
_vers_d = versiones([
    ("v2", f"{_NV['describe_product_v2']} muebles de IKEA.", "Las 8 líneas en el formato de la consulta, sin marca ni medidas, y nada de lo que no es: los embeddings no leen el «no».", ""),
    ("v3", f"+{_NV['describe_product_v3']} al ampliar: guardado, luces, textiles, deco.", "Qué mirar en una lámpara, un almohadón o un florero; un tercer ejemplo.", "actual"),
    ("api_v1", "ABO, por la API.", "La misma receta, diez productos por llamada; además da el kind y si entra al catálogo.", "actual"),
], cls="rd-vers")
_pal = len(DESCR_TODO[SOFA].split())
# el ejemplo (el sofá, de ABO) lo escribió la versión por la API: las mismas reglas que se muestran
_api = cuerpo_prompt("describe_products_api_v1.md")
for _regla in ("Exactly these eight lines, in this order", "one to three of these, the closest first", "60 to 90 words in all."):
    assert _regla in _api and _regla in cuerpo_prompt("describe_product_v3.md"), _regla
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
  <div class="ej-par">{producto(SOFA, 120)}<p class="ej-por"><b>{esc(_sofa_nom)}</b><br>{_sofa["kind"]} · {medida(_sofa["dimensions_cm"])} · {_pal} palabras<br>
  ABO: Opus 5.5 por la API (api_v1), {usd(C_DESC, 3)} por producto<br>IKEA: subagentes de Claude Code (Opus 5.5)</p></div>
  <div class="ficha-tk">{ficha(DESCR_TODO[SOFA])}</div></div>''',
     ["Fase dos: la descripción. Un VLM, Opus 5.5, mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, "
      "estilo, materiales, colores, forma, sensación y con qué combina. El prompt pide exactamente esas ocho líneas, sin "
      "marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. "
      "Este es el sofá de Amazon que vamos a "
      "seguir. Es el preprocesamiento que más pesa: lo mide el experimento 1."],
     actual=["descripcion"], pines={"descripcion": [1]})

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
    filas = [("id", SOFA), ("embedding", f"[{VEC['dim']} números]"), ("document", "la descripción"),
             ("category", md["category"]), ("kind", md["kind"]),
             ("w · d · h", " · ".join(f"{md[a]:g}".replace(".", ",") for a in ("width", "depth", "height")))]
    for i, (a, b) in enumerate(filas):
        o.append(f'<text class="t-mono" x="{rx + 20}" y="{68 + i * 24}"><tspan class="k">{a}</tspan></text>'
                 f'<text class="t-mono" x="{rx + 128}" y="{68 + i * 24}"><tspan class="d">{esc(b).replace("-1", "−1")}</tspan></text>')
    o.append(f'<text class="t-mono chico" x="{rx + 20}" y="{H - 22}"><tspan class="k">HNSW · coseno · ef_search {HNSW["ef_search"]} · M {HNSW["max_neighbors"]}</tspan></text>')
    o.append("</svg>")
    return "".join(o)


fase("rec-indice", "3", "Índice", "Un vector por producto: <em>la descripción entera</em>",
     '<p class="rt-lead"><b>Qué</b> se embebe: la descripción, un documento por producto. <b>Con qué</b>: Qwen3-Embedding, '
     f'local, {VEC["dim"]} componentes. <b>Dónde</b>: ChromaDB, con la metadata de los filtros al lado. Así queda el sofá:</p>',
     _indice_svg() + exps([
         (1, "Se embebe la descripción del VLM", "no el texto del vendedor"),
         (9, "Qwen3-Embedding-0.6B", "contra hashing, BM25 y BGE-base"),
         (12, "ChromaDB con HNSW", "contra recorrer todos los vectores con numpy"),
         (11, "Un documento por producto", f"unas {D['palabras_med']} palabras, sin partir en chunks"),
         (10, f"{VEC['dim']} dimensiones", "Matryoshka: se puede truncar sin reentrenar"),
         (3, "Dos índices más, para la búsqueda híbrida", "léxico: BM25 sobre las mismas descripciones · por foto: SigLIP 2, un vector por la foto de cada producto"),
     ], cls="ri-dec"),
     ["Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: "
      f"{miles(VEC['dim'])} dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, splitting, dimensión y base "
      "vectorial son preguntas de trámite: las contestamos juntas más adelante. Para la búsqueda "
      "híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las descripciones, y uno "
      "por foto, con SigLIP 2, que pone la foto y el texto en un mismo espacio."],
     actual=["indice"], pines={"indice": [9, 10, 11, 12]}, cls_banda="ri")

# =============================================================================================
# 4 y 5 · Foto + pedido → plan
# =============================================================================================
_p0 = PZ[0]


def _md(p):
    v = [p.get(f"max_{a}_cm") for a in ("width", "depth", "height")]
    return "≤ " + " × ".join("—" if x is None else f"{x:g}" for x in v) if any(v) else "—"


_pzs = "".join(f'<div class="rp-pz{" uno" if i == 0 else ""}"><span class="q">{i + 1}</span><b>{esc(", ".join(p["kinds"]))}</b>'
               f'<span class="md">{_md(p)}</span></div>' for i, p in enumerate(PZ))
_room = HERO_PLAN["answer"]["room"]
_pm = HERO_PLAN["meta"]
fase("rec-plan", "4 y 5", "Foto, pedido y plan", "Del pedido a <em>una consulta por pieza</em>",
     f'<p class="rt-lead rp-lead">«{esc(HERO_REQ)}»</p>',
     f'''<div class="rp-ent">{foto("rec-hero-room", HERO / "room.jpg", 440, 293)}
  <p class="rp-vista">entra la foto del ambiente vacío y el pedido; opcional, otra foto desde otro ángulo, que ve Claude y no el modelo de imagen</p>
  <p class="cred-l">Foto: {credito(HERO_SLUG)}</p></div>
<div class="ticket rp-plan" data-paso="1"><div class="tk-cab"><b>Plan · {len(PZ)} piezas</b><span>Claude Opus 5.5 · effort {LLM["effort"]}<br>{round(_pm["latency_s"])} s · {usd(HERO_PLAN["cost_usd"])}</span></div>
  <p class="rp-room">«{esc(_room[:150].rsplit(" ", 1)[0])}…»</p>
  <div class="rp-pz" style="border-top:0;color:var(--tinta-3)"><span></span><span>kind (lista cerrada)</span><span class="md">medida máx., cm</span></div>
  {_pzs}</div>
<div class="rp-q" data-paso="1"><span class="et">la consulta de la pieza 1, en las 8 líneas del catálogo</span>
  <div class="ficha-tk">{ficha(_p0["query"])}</div>
  <p class="rp-tec"><span>en las palabras de la clase</span><b>Query expansion con respuesta hipotética (HyDE)</b>: en la base no hay preguntas, hay respuestas. Y <b>descomposición del pedido</b>: una consulta por pieza.</p></div>''',
     ["Fases cuatro y cinco. Entra una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el "
      "final: un pedido de estilo industrial, sobre una foto pública.",
      f"El plan es la primera llamada a Opus, que hace de diseñador: lee el ambiente, descompone el pedido en piezas, acá "
      f"{len(PZ)}, y para cada una da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal "
      "escrito en las mismas ocho líneas que el catálogo. En los términos de la clase es query expansion con respuesta "
      "hipotética, HyDE: en la base no hay preguntas, hay respuestas. Más la "
      "descomposición del pedido: una consulta por pieza. Cuánto suma escribir la ficha lo mide el experimento 2."],
     actual=["foto", "plan"], pines={"plan": [2]}, focos=["foto", "plan"])

# =============================================================================================
# 5 · El prompt del plan y sus versiones
# =============================================================================================
fase("rec-plan-prompt", "5", "Plan", "El prompt del plan, <em>reescrito cuatro veces</em>",
     '<p class="rt-lead">Cada versión salió de algo que vimos en una corrida. Lo que no cambió desde la v2: '
     '<b>la consulta en las 8 líneas del catálogo</b>, que es lo que mide el experimento 2.</p>',
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
      "consulta en ocho líneas. La v3 pide terminar el ambiente, y la v4 saca el tope de piezas."],
     actual=["plan"], pines={"plan": [2]})

# =============================================================================================
# 6 · Búsqueda: filtro duro por kind y medidas, y sobre lo que pasa, búsqueda híbrida (la versión 2)
# =============================================================================================
EJE = {"max_width_cm": "ancho", "max_depth_cm": "fondo", "max_height_cm": "alto"}
_filtro_chips = "".join(f"<code>{x}</code>" for x in
                        [f'kind = {", ".join(_p0["kinds"])}'] + [f"{EJE[k]} ≤ {v:g} cm" for k, v in FILTRO_MAX.items()])
_cands = HERO_FOUND[0]["candidates"]
assert [c["score"] for c in _cands] == sorted((c["score"] for c in _cands), reverse=True) and _cands[0]["id"] == SOFA
_cs = "".join(f'<div class="rb-c{" uno" if c["id"] == SOFA else ""}">{producto(c["id"], 112)}<em>{f2(c["score"])}</em>'
              f'<b>{_cat(c["id"])}</b><span>{esc(tipo_de(c["description"]))}</span></div>' for c in _cands)
_n_abo_c = sum(c["id"].startswith("abo-") for c in _cands)
fase("rec-busqueda", "6", "Búsqueda", "Filtro por kind, y después <em>búsqueda híbrida</em>",
     f'<p class="rt-lead">Para cada pieza, primero un <b>filtro duro de metadata</b>: el kind del plan y sus medidas máximas, con '
     f'{round(SLACK * 100)}% de margen porque salen de una foto. Sobre lo que pasa, <b>tres puntajes con la misma ficha</b>, '
     f'estandarizados y promediados: quedan los <b>{K} mejores</b>.</p>',
     f'''<div class="rb-izq"><div class="rb-cab"><span class="et">la ficha de la pieza 1 · del plan</span><span></span><span class="et">el producto · lo describió el VLM</span></div>
  <div class="rb-par tres"><div class="ficha-tk">{ficha(_p0["query"])}</div>
    <div class="rb-tres">
      <div><b>Qwen3</b><span>el coseno entre la ficha y la descripción</span></div>
      <div><b>BM25</b><span>las palabras de la ficha que están en la descripción</span></div>
      <div><b>SigLIP 2</b><span>la ficha en una frase, contra la <i>foto</i></span></div>
      <p><b>{f2(_cands[0]["score"])}</b><span>cada puntaje en z-score, y el promedio</span></p></div>
    <div class="ficha-tk rb-doc"><div class="rb-doc-f">{producto(SOFA, 84)}<span>la foto: lo que mira SigLIP 2<br><i>«{esc(VQ[:58].rsplit(" ", 1)[0])}…»</i></span></div>{ficha(DESCR_TODO[SOFA])}</div></div></div>
<div class="rb-der">
  <div class="rb-filtro"><span class="et">1 · el filtro duro</span><p>{_filtro_chips}</p>
    <p class="rb-pasan">pasan <b>{PASAN}</b> de {miles(D["prod_todos"])} · un producto sin medidas, pasa</p></div>
  <div><span class="et">2 · los {K} mejores, a la elección · puntaje fusionado</span><div class="rb-cands">{_cs}</div></div>
</div>''',
     [f"Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, "
      f"con margen porque salen de una foto. Acá quedan {PASAN} de los {miles(D['prod_todos'])} productos. Sobre esos, tres "
      "puntajes: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras de la ficha que están en la "
      "descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se "
      "promedian: es la búsqueda híbrida, la versión 2. Quedan los cinco mejores: "
      f"{_n_abo_c} de Amazon y {len(_cands) - _n_abo_c} de IKEA."],
     actual=["busqueda"], pines={"busqueda": [3, 13]}, cls_banda="rb")

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
        out.append(f'<div class="re-c{" elegido" if el else ""}">{producto(cand["id"], 76)}{q}<span>{pos}.º</span></div>')
    return (f'<div class="re-fila"><div class="re-pz"><b>{nombre}</b><span>elige el {pos_el}.º de la búsqueda</span></div>'
            f'<div class="re-cs">{"".join(out)}</div><p class="re-why">«{esc(c["why"])}»</p></div>'), pos_el


_fe = [_fila_eleccion(1, "Sofá"), _fila_eleccion(3, "Biblioteca"), _fila_eleccion(5, "Alfombra")]
assert [x[1] for x in _fe] == [1, 5, 5] and PZ[2]["kinds"] == ["bookcase"], "la corrida cambió: revisar la fase 7 y su nota"
fase("rec-eleccion", "7", "Elección", "Opus mira las fotos y arma la lista: <em>es la generación</em>",
     f'<p class="rt-lead">La segunda llamada a Opus 5.5, y <b>la G del RAG</b>: ve la foto del cuarto y los {K} candidatos de '
     f'<b>todas las piezas juntas</b> (acá, {_cm["images"]} imágenes), cada uno con su tipo y su medida. Elige la combinación y '
     'cuántas unidades. Solo puede elegir ids que trajo la búsqueda: si no, el código rechaza la respuesta.</p>',
     f'''<div class="re-izq">{prompt_tk("choose_combination_v2.md", [
         ("We are adding {pieces} piece(s)", "in the same order:"),
         ("Choose the pieces together, as one look", "Judge from the photos."),
         ('Then say how many units of it go in the room ("quantity"). Usually 1.', "Usually 1."),
         ("0 when none of its candidates suits this room", "left out of the list."),
     ], resaltar=["Choose the pieces together, as one look, not each on its own. Judge from the photos.", '("quantity")',
                  "0 when none of its candidates suits this room"], ancho=700, cls="chico")}
  {versiones([("v1", "Un producto por pieza, la mejor combinación.", "Los candidatos con su línea Type y su medida, no el nombre de la tienda.", ""),
              ("v2", "Y cuántas unidades.", "0 deja la pieza afuera; más de una, sillas alrededor de una mesa.", "actual")])}</div>
<div class="re-der"><span class="et">tres de las {len(PZ)} piezas de este pedido: los candidatos en el orden de la búsqueda, el elegido y su porqué</span>
  {"".join(x[0] for x in _fe)}
  <p class="re-pie">No es un reranker: arma <b>un conjunto para este cuarto</b>. Tomó el 1.º de la búsqueda en {N_HERO_PRIMERO} de las {N_HERO} piezas · {miles(_cm["usage"]["input_tokens"])} tokens de entrada · {round(_cm["latency_s"])} s · {usd(HERO_CHOOSE["cost_usd"])}</p></div>''',
     [f"Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco "
      f"candidatos de cada pieza, acá {_cm['images']} imágenes, cada uno con su id, su tipo y su medida. El prompt le pide "
      "elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir "
      "productos que trajo la búsqueda: si no, el código rechaza la respuesta. No es un reranker: arma un conjunto para este "
      f"cuarto. Acá tomó el primero de la búsqueda en {N_HERO_PRIMERO} de las {N_HERO} piezas; la biblioteca era el quinto "
      "candidato."],
     actual=["eleccion"], pines={"eleccion": [5]})

# =============================================================================================
# 8 · Escena: una plantilla; empata con la escena escrita por el LLM en los 11 ambientes (experimento 15, de trámite)
# =============================================================================================
_ln = ESCENA.splitlines()
_ln2 = next(x for x in _ln if x.startswith("image 2:"))
_ln3 = next(x for x in _ln if x.startswith("image 3:"))
_ln_un = next(x for x in _ln if x.startswith("image ") and x.endswith("units"))
_fin_ped = HERO_REQ.split(". ")[0] + "."
fase("rec-escena", "8", "Escena", "El prompt de la imagen: <em>una plantilla, sin LLM</em>",
     '<p class="rt-lead">No lo escribe Claude: es una plantilla que se llena con el pedido y los productos elegidos, con su tipo, '
     f'sus medidas y cuántas unidades. La comparamos con la escena escrita por el LLM en los {IMG_PL["corridas"]} ambientes: se '
     f'reconocen {IMG_PL["identificados"]} de {IMG_PL["productos"]} productos contra {IMG_LLM["identificados"]}, y el ambiente se '
     f'conserva en {IMG_PL["ambiente_conservado"]} contra {IMG_LLM["ambiente_conservado"]}. <b>Empatan</b>, y la plantilla cuesta '
     f'<b>una llamada menos</b> ({usd(C_SCENE, 3)} por pedido).</p>',
     f'''<div class="rs-arbol">
  <div class="rs-rama otra"><h3>la escribe Claude · scene_prompt</h3>{versiones([
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
         ("Images 2 to", _ln3),
         (_ln_un, None),
         ("Add exactly these products and nothing else:", "lamps, plants, rugs or decoration than these"),
         ("The client asked:", _fin_ped),
         ("Arrange the products as an interior designer would", "lit by this room's light."),
     ], resaltar=["the result must still be that same room, exactly", "Do not add, remove, move or enlarge any wall, window, door or opening",
                  _ln2, "2 units", "Add exactly these products and nothing else"],
     texto=ESCENA, titulo="scene_prompt_libre_v4.md · lleno", rotulo="el de esta corrida, tal cual se mandó", cls="rs-tk")}''',
     ["Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada "
      "producto, o una plantilla sin LLM, que se completa con la lista. La plantilla es estricta: una "
      "edición de la foto del cliente, con la misma cámara y exactamente estos productos. Las "
      f"comparamos en los {IMG_PL['corridas']} ambientes y empatan: se reconocen {IMG_PL['identificados']} productos de "
      f"{IMG_PL['productos']} con la plantilla y {IMG_LLM['identificados']} con la escena del LLM, y el ambiente se conserva en "
      f"{IMG_PL['ambiente_conservado']} y en {IMG_LLM['ambiente_conservado']}. Nos quedamos con la plantilla: da lo mismo y "
      "cuesta una llamada menos."],
     actual=["escena"], pines={"escena": [15]})

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
                   f'<figcaption><b>{a["sift_inliers"]}</b>descartada</figcaption></figure>'
                   for i, a in enumerate(CLA_IMG["attempts"], 1)))
fase("rec-imagen", "9 y 10", "Imagen y control", "La imagen, y un control: <em>¿es el mismo cuarto?</em>",
     f'<p class="rt-lead"><b>Nano Banana 2</b> (Gemini 3.1 Flash Image), por fal, en modo edición, a {GEN["resolution"]}: '
     f'{usd(GEN["usd_per_image"][GEN["resolution"]])} por intento. Entran la foto del cuarto y una foto por producto: acepta 14 '
     f'imágenes, así que muestra <b>hasta {CFG.furnish.max_image_products} productos</b>; el resto queda en la lista. Después, '
     '<b>SIFT + RANSAC</b> contra la foto original: si no es el mismo cuarto, se descarta y se pide otra.</p>',
     f'''<div class="ri2-par" style="height:{_H + 110}px">
  {foto("rec-hero-room2", HERO / "room.jpg", _W, _H, extra="ri2-a")}
  <div class="ri2-gen" data-hasta="1"><i>→</i><b>Nano Banana 2</b><span>{HERO_IMG["meta"]["images_in"]} imágenes<br>{round(HERO_IMG["meta"]["latency_s"])} s</span></div>
  {foto("rec-hero-final", HERO / "final.png", _W, _H, extra="ri2-b", q=80)}
  {_sift_svg()}
  <div class="ri2-prods" style="top:{_H + 22}px" data-hasta="1">{_prods}<span>+ el prompt de la escena</span></div>
  <p class="ri2-veredicto" style="top:{_H + 22}px" data-paso="1"><b>{SIFT["inliers"]} puntos</b>reencontrados, la cámara quieta: queda al primer intento</p>
  <p class="cred-l ri2-cred" style="top:{_H + 86}px">Fotos de los ambientes: {credito(HERO_SLUG, CLA_SLUG)}</p>
</div>
<div class="ri2-der" data-paso="1">
  <p class="ri2-regla">Queda si reencuentra <b>al menos {ROOM_CHECK["min_inliers"]} puntos</b> y la cámara se movió <b>menos del {f1(ROOM_CHECK["max_shift"] * 100)}%</b>; si no, otra imagen, <b>hasta {ROOM_CHECK["attempts"]}</b>. Los umbrales están puestos a mano.</p>
  <span class="et">otro pedido, un living clásico: las {len(CLA_IMG["attempts"])} descartadas</span>
  <div class="ri2-ints cuatro">{_ints}</div>
  <p class="ri2-tot">Reencuadró hacia la chimenea las tres veces: se entrega la que mejor conserva el cuarto, marcada. En las {len(FINALES)} corridas finales <b>pasan {IMG_TOT["pasan"]}, todas al primer intento</b>; en las otras {NO_PASAN} fallaron los {ROOM_CHECK["attempts"]}. Reintentar rescata poco: contando la tanda con la escena del LLM, {ESC_RESCATADOS} de {ESC_FALLARON_1}.</p></div>''',
     ["La imagen la hace Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los "
      f"productos y el prompt. Acepta 14 "
      f"imágenes, así que muestra hasta {CFG.furnish.max_image_products} productos; el resto queda en la lista.",
      "Después, el control: comparamos la foto original con la generada con SIFT y RANSAC. Si reencuentra al menos "
      f"{ROOM_CHECK['min_inliers']} puntos del cuarto y la cámara casi no se movió, se acepta; si no, se genera otra, hasta "
      f"{ROOM_CHECK['attempts']} veces. El loft pasó al primer intento. Este otro pedido, un "
      "living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el mejor, marcado. "
      f"El control detecta; reintentar lo arregla pocas veces: contando otra tanda, rescató {ESC_RESCATADOS} de las "
      f"{ESC_FALLARON_1} que fallaron al primer intento."],
     actual=["imagen", "control"], focos=["imagen", "control"], cls_banda="ri2")

# =============================================================================================
# 11 · Lista + imagen
# =============================================================================================
_ls = []
for _h, _q, _rk, _c in HERO_PICKS:
    _k = _h.get("kind", "")
    _ls.append(f'<div class="rl-l">{producto(_h["id"], 34)}<b>{KIND_ES.get(_k, _k)}</b><span class="id">{_cat(_h["id"])} · {_h["id"].removeprefix("abo-")}</span>'
               f'<span class="tr">plan → búsqueda <i>{_rk}.º de {K}</i> → elección</span><span class="q">×{_q}</span></div>')
fase("rec-lista", "11", "Lista + imagen", "Lo que sale: <em>cada línea, con su recorrido</em>",
     '<p class="rt-lead">La lista sale de la elección: <b>productos que existen</b>, con su id y cuántas unidades; el código rechaza '
     'cualquier id que la búsqueda no haya traído. La imagen, de las fotos de esos mismos productos. Este pedido costó '
     f'{usd(HERO_COSTO_CLAUDE)} de Claude y {usd(HERO_IMG["cost_usd"])} de la imagen.</p>',
     f'''<div class="ticket rl-tk"><div class="tk-cab"><b>Lista de compra</b><span>{N_HERO} productos · {sum(q for _, q, *_ in HERO_PICKS)} unidades · {N_HERO_ABO} de Amazon, {N_HERO - N_HERO_ABO} de IKEA</span></div>{"".join(_ls)}</div>
<div class="rl-fin">{foto("hero-final-rl", HERO / "final.png", 640, 427, q=82)}<p>la imagen: el mismo cuarto, con esos productos</p>
  <p class="cred-l">Foto del ambiente: {credito(HERO_SLUG)}</p></div>''',
     [f"Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, acá {N_HERO_ABO} de Amazon y "
      f"{N_HERO - N_HERO_ABO} de IKEA, y la foto del mismo ambiente con ellos. Cada línea tiene su recorrido: el kind lo puso "
      "el plan, la búsqueda trajo los candidatos y la elección tomó uno, a veces no el primero. Este pedido costó unos "
      f"{round(100 * HERO_COSTO_CLAUDE)} centavos de Claude y {round(100 * HERO_IMG['cost_usd'])} de la imagen."],
     actual=["salida"])
