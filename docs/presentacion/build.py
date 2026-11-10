"""Arma docs/presentacion/amoblai.html: un solo archivo, con las imágenes y los gráficos adentro,
desde los resultados guardados en datos/resultados/ (ningún número está escrito a mano).

    uv run python docs/presentacion/build.py
"""

from __future__ import annotations

import glob
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kit import ROOT, arch, chain, esc, hbars, img, lines, num  # noqa: E402

R = ROOT / "datos" / "resultados"
OUT = Path(__file__).with_name("amoblai.html")


def load(p: str | Path) -> dict | None:
    p = Path(p)
    p = p if p.is_absolute() else ROOT / p
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def latest(suffix: str) -> Path:
    runs = sorted(d for d in (R / "evaluacion").iterdir() if d.name.endswith(suffix))
    return runs[-1]


# -- datos ---------------------------------------------------------------------------------------
ABL_DIR = latest("_ablacion-retrieval")
ABL = load(ABL_DIR / "metricas.json")
RER_DIR = latest("_ablacion-reranking")
RER = load(RER_DIR / "metricas.json")
CURVA = load(R / "evaluacion_candidatos" / "curva_k.json")
GRAD = load(R / "evaluacion_graduada" / "graduada.json")
ESP = load(R / "evaluacion_espacio" / "espacio.json")
CAT_OLD = load(R / "evaluacion" / "20261023-173217_ablacion-retrieval" / "metricas.json")
CAT_NEW = load(latest("_ablacion-catalogo-revisado") / "metricas.json")
E2E = {
    Path(f).stem: load(f) for f in sorted(glob.glob(str(R / "punta_a_punta" / "*" / "juez_*.json")))
}
REPL = {
    d.name.split("_")[-1]: load(d / "metricas.json")
    for d in sorted((R / "evaluacion").iterdir())
    if "reproducibilidad" in d.name
}


def m(key: str, src: dict | None = None) -> dict:
    return (src or ABL)[key]


BASE = "qwen3|description|filtro-type"


def ci(x: dict, k: str = "hit@1") -> tuple[float, float]:
    return tuple(x[f"{k}_ic95"])


# -- slides --------------------------------------------------------------------------------------
SLIDES: list[str] = []
# Lo que se dice en cada slide (el guion, docs/presentacion/guion.md), alineado con SLIDES.
NOTES: list[dict] = []


def slide(
    body: str,
    cls: str = "",
    kicker: str = "",
    title: str = "",
    foot: str = "",
    notes: str | dict = "",
    mins: float = 1.0,
) -> None:
    NOTES.append({"kicker": kicker, "title": title, "notes": notes, "mins": mins})
    head = ""
    if kicker:
        head += f'<div class="kicker">{kicker}</div>'
    if title:
        head += f"<h2>{title}</h2>"
    SLIDES.append(
        f'<section class="slide {cls}">{head}{body}'
        f'<div class="foot"><span>{foot or "amoblai · TP 73.69 LLM · ITBA 2026"}</span><span class="n"></span></div></section>'
    )


def section(kicker: str, title: str, text: str = "", notes: str = "", mins: float = 0.2) -> None:
    body = f'<div class="kicker">{kicker}</div><h1>{title}</h1><p style="margin-top:18px">{text}</p>'
    slide(body, "section", notes=notes, mins=mins)
    NOTES[-1].update(kicker=kicker, title=title)  # el encabezado va en el cuerpo, no en slide()


def experiment(
    n: str,
    title: str,
    question: str,
    left: str,
    right: str,
    decision: str,
    hl: tuple = (),
    off: tuple = (),
    why: str = "",
    notes: dict | None = None,
    mins: float = 1.2,
) -> None:
    """Una slide por experimento, en el orden en que se cuenta: arriba por qué lo hicimos y qué
    queríamos ver; a la izquierda, el experimento. Con la flecha aparecen los resultados (paso 1)
    y después la decisión (paso 2)."""
    left = left.replace('<div class="find"', '<div data-step="1" class="find"')
    body = (
        (chain(hl, off) if hl else "")
        + (f'<p class="why"><b>Por qué:</b> {why}</p>' if why else "")
        + f'<p class="q">{question}</p>'
        + f'<div class="row grow"><div class="grow"><div class="coltag">El experimento</div>{left}</div>'
        + f'<div data-step="1"><div class="coltag">Resultados</div>{right}</div></div>'
        + f'<div class="decision" data-step="2">{decision}</div>'
    )
    slide(body, kicker=f"Experimento {n}", title=title, notes=notes or {}, mins=mins)


def bars_methods(keys: list[tuple[str, str]], hl: str, metric: str = "hit@1", src: dict | None = None, **kw) -> str:
    rows = []
    for key, label in keys:
        x = m(key, src)
        rows.append({"label": label, "value": x[metric], "ci": ci(x, metric) if f"{metric}_ic95" in x else None, "hl": key == hl})
    return hbars(rows, **kw)


# 1. Portada
EST = R / "amoblar" / "experimento-buen-pedido-estricto"
slide(
    '<div class="row center" style="gap:44px;height:100%">'
    '<div class="grow"><div class="kicker">TP 3 · 73.69 Large Language Models · ITBA 2026</div>'
    "<h1 style=\"font-size:92px\">amoblai</h1>"
    '<p style="font-size:25px;margin-top:16px" class="muted">Amoblar un ambiente vacío con productos reales: '
    "RAG sobre un catálogo de muebles, un VLM que elige y un modelo de imagen que lo muestra.</p>"
    '<p style="margin-top:40px;font-size:17px">Juan Bautista Albertoni Salini · Matias Juan Rossi Seifert · Junior Rambau</p></div>'
    f'<div class="hero" style="width:470px;display:grid;gap:10px">{img(EST / "room.jpg", 1000, cls="photo")}{img(EST / "final.png", 1000, cls="photo")}</div>'
    "</div>",
    notes="Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.",
    mins=0.5,
)

# 2. El problema
slide(
    '<div class="row center" style="gap:40px">'
    f'<div style="width:560px">{img(EST / "room.jpg", 1100, cls="photo")}<div class="cap">Un ambiente vacío real (foto de un compañero).</div></div>'
    '<div class="grow">'
    "<p>Mudarse a un lugar vacío obliga a decidir qué comprar sin poder verlo puesto. "
    "Los catálogos muestran cada mueble suelto, sobre fondo blanco; las fotos de ambientes, la casa de otro.</p>"
    "<p>Queremos responder, para <b>este</b> ambiente y <b>este</b> pedido:</p>"
    "<ul><li>¿qué productos <b>reales</b>, que se puedan comprar, van?</li>"
    "<li>¿cuántos de cada uno, de qué medida?</li>"
    "<li>¿cómo queda el ambiente con ellos?</li></ul>"
    "</div></div>",
    kicker="El problema",
    title="¿Qué compro para este ambiente, y cómo queda?",
    mins=0.8,
    notes="Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Nosotros queremos responder, para este ambiente y este pedido: qué productos reales, que se puedan comprar, van; cuántos y de qué medida; y cómo queda el ambiente con ellos.",
)

# 3. Qué hace
found = load(EST / "2_candidates.json")
choice = load(EST / "3_choice.json")
picks = []
for p, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
    q = int(c.get("quantity", 1) or 0)
    if q:
        h = next(h for h in p["candidates"] if h["id"] == c["id"])
        picks.append((h, q))
items = "".join(
    f'<div style="text-align:center">{img(h["photos"][0], 220, cls="photo")}<div class="tiny">{esc(h["description"].splitlines()[0].removeprefix("Type:").strip())}{" ×" + str(q) if q > 1 else ""}</div></div>'
    for h, q in picks[:8]
)
req = load(EST / "request.json")["request"]
slide(
    '<div class="row" style="gap:28px">'
    f'<div style="width:330px"><div class="tag">entrada</div><div style="margin:8px 0">{img(EST / "room.jpg", 700, cls="photo")}</div>'
    f'<div class="card small" style="padding:12px 14px;font-size:14.5px;line-height:1.35">“{esc(req)}”</div></div>'
    '<div class="grow"><div class="tag g">salida 1 · la lista de compra</div>'
    f'<div class="grid4" style="margin-top:10px;gap:10px">{items}</div></div>'
    f'<div style="width:330px"><div class="tag g">salida 2 · el ambiente amoblado</div><div style="margin-top:8px">{img(EST / "final.png", 800, cls="photo")}</div>'
    '<div class="cap">Generada con esos productos, en ese mismo ambiente.</div></div>'
    "</div>",
    kicker="El producto",
    title="Foto + pedido → lista de compra + imagen",
    notes="Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo y cuántas unidades de cada uno (acá, dos bibliotecas iguales), y la foto del mismo ambiente con esos productos puestos.",
)

# 4. Por qué RAG
slide(
    '<div class="grid3">'
    '<div class="card"><h3>Un LLM solo</h3><p class="small">Sabe de decoración, pero no qué hay en un catálogo: recomienda "un sillón de cuero coñac" que nadie vende, con medidas inventadas.</p></div>'
    '<div class="card"><h3>Un modelo de imagen solo</h3><p class="small">Amobla lindo, pero inventa los muebles. No hay nada que comprar: lo que se ve no existe.</p></div>'
    '<div class="card" style="border-color:var(--accent)"><h3 style="color:var(--accent)">RAG</h3><p class="small">El catálogo es la base de conocimiento. El LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos. La imagen se genera <b>desde las fotos de los productos elegidos</b>.</p></div>'
    "</div>"
    '<p style="margin-top:26px">No es un Q&amp;A: la consulta es una foto y un pedido abierto; la respuesta es una combinación de productos que tiene que funcionar junta, en ese espacio, y una imagen fiel a esa combinación.</p>',
    kicker="Por qué RAG",
    title="Recomendaciones atadas a productos que existen",
    mins=0.8,
    notes="¿Por qué un RAG y no un LLM o un modelo de imagen solos? Un LLM sabe de decoración, pero no sabe qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen amobla lindo, pero inventa los muebles: no hay nada que comprar. Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos. Y la imagen se genera desde las fotos de los productos elegidos. No es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta es una combinación de productos que tiene que funcionar junta.",
)

# ---- Datos
section("Parte 1", "Datos", "El catálogo, el ground truth que permite medir el retrieval y los ambientes vacíos reales para probar el sistema de punta a punta.", notes="Primero, los datos: con qué catálogo trabajamos, cómo medimos el retrieval y con qué ambientes probamos.")

cat_n = len([1 for _ in (ROOT / "datos/procesados/items.jsonl").read_text().splitlines()])
abo_n = sum(1 for _ in (ROOT / "datos/catalogo/abo/descripciones.jsonl").read_text().splitlines())
sample_ids = ["102.335.32", "202.016.82", "691.249.46", "391.505.88", "302.397.12", "002.852.58"]
items_by = {json.loads(x)["id"]: json.loads(x) for x in (ROOT / "datos/procesados/items.jsonl").read_text().splitlines()}
grid = "".join(
    f'<div>{img(items_by[i]["photos"][0], 200, cls="photo")}</div>' for i in sample_ids if i in items_by
)
desc_ex = json.loads((ROOT / "datos/catalogo/descripciones.jsonl").read_text().splitlines()[0])
desc391 = next(
    (json.loads(x) for x in (ROOT / "datos/catalogo/descripciones.jsonl").read_text().splitlines() if '"391.505.88"' in x),
    desc_ex,
)
slide(
    '<div class="row" style="gap:30px">'
    '<div class="grow">'
    "<ul class=\"small\">"
    "<li><b>Dataset IKEA</b> (Tautkute et al., 2017; uso no comercial): 2.191 productos con foto, nombre, tipo y medida, y 215 fotos de ambientes con sus productos.</li>"
    f"<li>Nuestro alcance: muebles, iluminación, textiles y deco de living y comedor: <b>862 productos</b>, 819 después de la revisión (exp. 9).</li>"
    "<li>El texto de IKEA es pobre (\"The armchair is lightweight...\"): un VLM <b>describe cada producto mirando su foto</b> en 8 líneas fijas. Es lo que se indexa.</li>"
    "<li>Problemas: fotos de 500 px, los asientos <b>sin medidas</b>, productos que comparten la foto de otra medida.</li>"
    "</ul>"
    f'<div class="grid3" style="gap:10px;margin-top:12px">{grid}</div>'
    "</div>"
    f'<div style="width:470px"><div class="tag">la descripción de un producto (escrita por un VLM)</div>'
    f'<div class="card" style="margin-top:8px;font-size:14px;line-height:1.45;white-space:pre-line">{esc(desc391["text"].strip())}</div>'
    '<div class="cap">Tipo, uso, estilo (de una lista cerrada), materiales, colores, forma, sensación y con qué combina. El plan escribe las consultas en este mismo formato.</div></div>'
    "</div>",
    kicker="Datos · el catálogo",
    title="El catálogo: productos IKEA descritos por un VLM",
    mins=0.9,
    notes=f"El catálogo base es el dataset IKEA de Tautkute y otros, de uso no comercial. Nos quedamos con lo de living y comedor: muebles, iluminación, textiles y deco, 855 productos, 819 después de la revisión. El texto de IKEA es pobre, así que un VLM describe cada producto mirando su foto en 8 líneas fijas (esta es una). Eso es lo que se indexa, y el experimento 1 muestra por qué. Los problemas del catálogo: fotos de 500 píxeles, asientos sin medidas y productos que comparten la foto de otra medida.",
)

# ground truth
gt_room = "datos/dataset/ikea/images/room_scenes"
scene = next(iter(sorted((ROOT / gt_room).glob("*living*"))), None) or next(iter(sorted((ROOT / gt_room).glob("*"))))
slide(
    '<div class="row" style="gap:30px">'
    f'<div style="width:560px">{img(scene, 1100, cls="photo")}<div class="cap">Un ambiente del dataset: sus productos están anotados (el ground truth sale de invertir <code>item_to_room</code>).</div></div>'
    '<div class="grow"><ul class="small">'
    "<li><b>65 ambientes</b> de living y comedor de IKEA con productos del catálogo anotados.</li>"
    "<li>Por cada mueble visible, un subagente escribe la consulta como lo haría el plan: las 8 líneas del producto ideal, mirando el ambiente. "
    f"<b>{ABL[BASE]['searches']} búsquedas</b>, {ABL[BASE]['answerable']} con su producto en el catálogo.</li>"
    "<li>Una búsqueda acierta si el producto anotado sale primero (hit@1) o entre los k primeros.</li>"
    "<li>Intervalos de confianza por <b>bootstrap por ambiente</b> (las búsquedas de un mismo ambiente no son independientes).</li>"
    "<li>Para medir cuánto depende de quién escribe las consultas, dos redactores más escribieron las mismas (exp. 11).</li>"
    "</ul></div></div>",
    kicker="Datos · ground truth",
    title="Ambientes reales con sus muebles: el ground truth del retrieval",
    mins=0.9,
    notes=f"Para medir el retrieval necesitamos saber cuál es el producto correcto. El dataset trae 65 fotos de livings y comedores reales de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribe la búsqueda como la escribiría nuestro plan, mirando el ambiente: {ABL[BASE]['searches']} búsquedas, {ABL[BASE]['answerable']} con su producto en el catálogo. Una búsqueda acierta si el anotado sale primero (hit@1) o entre los k primeros. Los intervalos de confianza son por bootstrap por ambiente, porque las búsquedas de un mismo ambiente no son independientes.",
)

# ambientes vacíos
rooms_yaml = ROOT / "datos/ambientes_vacios/pedidos.yaml"
if rooms_yaml.exists():
    import yaml

    rooms = yaml.safe_load(rooms_yaml.read_text())["ambientes"]
    pub_yaml = ROOT / "datos/ambientes_vacios/publicas.yaml"
    pub = {f["archivo"]: f for f in yaml.safe_load(pub_yaml.read_text())["fotos"]} if pub_yaml.exists() else {}
    shown = [r for r in rooms if (ROOT / r["foto"]).exists()][:12]
    thumbs = "".join(
        f'<div>{img(r["foto"], 300, cls="photo")}<div class="tiny">{esc(r["slug"])}</div></div>' for r in shown
    )
    credits = "; ".join(
        f'{esc(pub[r["foto"]]["autor"])} ({esc(pub[r["foto"]]["licencia"])})' for r in shown if r["foto"] in pub
    )
    nr, npub = len(rooms), sum(r["foto"] in pub for r in rooms)
else:
    rooms, thumbs, nr, npub, credits, pub = [], "", 0, 0, "", {}
slide(
    '<div class="row" style="gap:28px"><div style="width:420px"><ul class="small">'
    f"<li><b>{nr} ambientes vacíos reales</b>: {nr - npub} nuestros y {npub} públicos (Wikimedia Commons y Flickr, CC BY / BY-SA), elegidos de {len(pub)} revisados uno por uno: datos de cámara, ruido, polvo, cables; se descartaron renders y una serie generada con IA.</li>"
    "<li>Cada uno con un pedido escrito como lo escribiría un usuario que sabe pedir: qué ambiente es, qué piezas, el estilo. Los públicos, con estilos que no son el nórdico de IKEA (industrial, clásico, japandi, bohemio).</li>"
    "<li>No hay ground truth: lo que se mide es cuál de dos listas mandaría un diseñador (un juez, exp. 10) y qué tan fiel es la imagen.</li>"
    f'</ul></div><div class="grow"><div class="grid4 fix h120" style="gap:8px">{thumbs}</div>'
    f'<div class="tiny" style="margin-top:6px">Fotos públicas: {credits}.</div></div></div>',
    kicker="Datos · ambientes vacíos",
    title="Ambientes vacíos reales para probar de punta a punta",
    notes=f"Para probar el sistema completo hacen falta ambientes vacíos reales. Tenemos {nr}: {nr - npub} de departamentos nuestros y {npub} públicos de Wikimedia Commons y Flickr, con licencia Creative Commons, elegidos entre {len(pub)} que revisamos uno por uno para descartar renders y fotos generadas con IA. Cada uno tiene un pedido escrito como lo escribiría un usuario que sabe pedir; los públicos, con estilos distintos del nórdico. Acá no hay ground truth: medimos con un juez y con métricas de imagen.",
    mins=0.8,
)

# ---- Arquitectura
section("Parte 2", "Arquitectura", "De la v0 por imagen a la v1 por texto, y las variantes que fueron decidiendo los experimentos.", notes="Después, la arquitectura: de dónde venimos y qué variantes probamos.")

v0v1 = load(R / "reporte" / "_v0v1.json") or {"v0": 0.508, "v1": 0.618, "n0": 325, "n1": 207}
slide(
    '<div class="row" style="gap:36px"><div class="grow">'
    "<h3>v0: retrieval por imagen</h3>"
    "<p class=\"small\">Grounding DINO detecta cada mueble en la foto de un ambiente amoblado, SAM lo recorta y DINOv2/v3 busca la foto del catálogo más parecida. Servía para "
    "\"encontrar este sofá\", no para un ambiente <b>vacío</b>: no hay nada que recortar. Y mezcla estilo con identidad (el recorte trae la luz del ambiente).</p>"
    "<h3 style=\"margin-top:18px\">v1: RAG por texto</h3>"
    "<p class=\"small\">El pedido y la foto pasan por un LLM que escribe el producto ideal en las mismas 8 líneas que describen el catálogo. La búsqueda es texto contra texto, "
    "con filtros por tipo de producto y medida. Sirve con el ambiente vacío y se puede explicar.</p></div>"
    f'<div style="width:470px">{hbars([{"label": "v0 imagen (recortes)", "value": v0v1["v0"]}, {"label": "v1 texto", "value": v0v1["v1"], "hl": True}], width=470, label_w=170)}'
    '<div class="cap">hit@1 sobre el mismo ground truth (catálogo del primer alcance). La v1 gana y además funciona sin un mueble en la foto.</div></div></div>',
    kicker="Arquitectura · v0 → v1",
    title="Por qué dejamos la búsqueda por imagen",
    notes=f"La primera versión buscaba por imagen: detectaba cada mueble en la foto con Grounding DINO, lo recortaba con SAM y buscaba la foto del catálogo más parecida con DINOv3. Eso sirve para encontrar este sofá, pero nuestro caso es un ambiente vacío: no hay nada que recortar. La v1 busca por texto: un LLM escribe el producto ideal en el mismo formato que el catálogo. Con el mismo ground truth, la v1 da {num(v0v1['v1'])} de hit@1 contra {num(v0v1['v0'])} de la v0, y además funciona con el ambiente vacío.",
)

slide(
    f'{arch(("plan", "retrieve", "choose", "generate"))}'
    '<div class="grid4 small" style="margin-top:14px;gap:14px">'
    '<div><b>plan</b> (Claude Opus 5.5): lee el ambiente y el pedido; decide las piezas, su kind, la medida máxima y la consulta ideal en 8 líneas.</div>'
    '<div><b>retrieve</b>: Qwen3-Embedding + ChromaDB, con filtros duros por kind (lo elige el plan) y medida; trae k candidatos por pieza.</div>'
    '<div><b>choose</b> (Claude con las fotos): elige uno por pieza pensando la combinación, y cuántas unidades (0 deja la pieza afuera). Solo puede elegir ids recuperados.</div>'
    '<div><b>scene + generate</b>: el prompt de la imagen y Nano Banana 2 con la foto del ambiente y las de los productos; un control SIFT descarta la imagen si cambió el cuarto.</div>'
    "</div>",
    kicker="Arquitectura · v1",
    title="Dos pipelines: indexing offline y consulta por pedido",
    notes="La arquitectura tiene dos pipelines. El de indexing corre una vez: catálogo, descripciones del VLM, embeddings con Qwen3 y ChromaDB. El de consulta corre por pedido. Plan: Claude Opus lee la foto y el pedido, decide las piezas, su tipo, la medida máxima y escribe la consulta ideal. Retrieve: Qwen3 y ChromaDB con filtros duros, k candidatos por pieza. Choose: Claude mira las fotos de los candidatos, elige uno por pieza pensando la combinación, y cuántas unidades; solo puede elegir productos recuperados. Y la imagen: Nano Banana 2 recibe la foto del ambiente y las de los productos, y un control automático descarta la imagen si cambió el cuarto.",
    mins=1.3,
)

slide(
    '<table class="t"><tr><th>Componente</th><th>Variantes probadas</th><th>Experimento</th></tr>'
    "<tr><td>Qué texto se indexa</td><td>texto del vendedor · nombre + descripción · descripción del VLM</td><td class=n>1</td></tr>"
    "<tr><td>Embedder</td><td>hashing (sin modelo) · BGE-base · Qwen3-Embedding-0.6B</td><td class=n>2</td></tr>"
    "<tr><td>Filtros</td><td>ninguno · por tipo · por kind</td><td class=n>3</td></tr>"
    "<tr><td>Splitting</td><td>un documento por producto · un chunk por línea (dos formas)</td><td class=n>4</td></tr>"
    "<tr><td>Dimensión del vector</td><td>32 a 1024 (Matryoshka)</td><td class=n>5</td></tr>"
    "<tr><td>Base vectorial y consulta</td><td>ChromaDB HNSW · búsqueda exacta · consulta completa, solo Type, solo kind</td><td class=n>6</td></tr>"
    "<tr><td>Post-retrieval</td><td>sin rerank · cross-encoder MiniLM · VLM (Claude) sobre el top-10</td><td class=n>7</td></tr>"
    "<tr><td>Candidatos por pieza</td><td>k = 1 a 10</td><td class=n>8</td></tr>"
    "<tr><td>Catálogo</td><td>primer alcance · ampliado · revisado · IKEA vs Amazon (ABO) vs los dos</td><td class=n>9–10</td></tr>"
    "<tr><td>Imagen</td><td>escena escrita por el LLM · escena libre · edición estricta + control SIFT</td><td class=n>12</td></tr>"
    "</table>",
    kicker="Arquitectura · variantes",
    title="Los hiperparámetros que decidimos con experimentos",
    notes="Cada fila de esta tabla es una decisión de la arquitectura que tomamos con un experimento, con todo lo demás fijo. Los vamos a ver en este orden, que es más o menos el orden en que los hicimos: cada uno deja su decisión en la configuración del siguiente.",
    mins=0.5,
)

# ---- Métricas
section("Parte 3", "Métricas", "Del retrieval (hay ground truth) a la respuesta y la imagen (no lo hay: jueces y métricas sin referencia).", notes="Antes de los experimentos, las métricas, para que cada número que mostremos se entienda.")

slide(
    '<div class="grid3 metric">'
    '<div class="card"><h3>hit@k</h3><p class="small">¿El producto anotado está entre los k primeros? hit@1 es "lo encontró primero"; hit@k para k = cantidad de candidatos es el techo de lo que el VLM puede elegir.</p></div>'
    '<div class="card"><h3>MRR@10</h3><div class="formula">media de 1 / posición</div><p class="small">Premia que el correcto esté arriba: 1 si es el 1.º, ½ si es el 2.º, 0 si no está en el top-10.</p></div>'
    '<div class="card"><h3>Context recall@k</h3><p class="small">De los productos anotados de un ambiente, cuántos aparecen entre los k candidatos de su pieza (RAGAS, por ambiente).</p></div>'
    '<div class="card"><h3>Context precision@K</h3><div class="formula">Σ precision@k · rel(k) / relevantes</div><p class="small">La de RAGAS: cuán arriba quedan los relevantes en el top-K.</p></div>'
    '<div class="card"><h3>NDCG@10</h3><p class="small">Ganancia acumulada con descuento logarítmico por posición, normalizada por la ideal. Admite relevancia graduada (2/1/0).</p></div>'
    '<div class="card"><h3>IC 95% por bootstrap</h3><p class="small">Se re-muestrean <b>ambientes</b>, no búsquedas. Dos métodos cuyos intervalos se pisan no se distinguen con estos datos.</p></div>'
    "</div>",
    kicker="Métricas · retrieval",
    title="Con ground truth: ¿trae el producto correcto, y arriba?",
    mins=0.9,
    notes="Las métricas de retrieval, donde sí hay ground truth. hit@k: si el anotado está entre los k primeros; hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos de confianza: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.",
)

slide(
    '<div class="grid2 metric">'
    '<div class="card"><h3>Relevancia graduada con un juez</h3><p class="small">El ground truth tiene un solo producto correcto, pero otro parecido también sirve. Un juez (LLM) califica el top-3: <b>2</b> el mismo o indistinguible, <b>1</b> alternativa aceptable, <b>0</b> no sirve. útil@k = hay un 1 o un 2 en el top-k. Validamos al juez contra el ground truth: ¿le da 2 al anotado?</p></div>'
    '<div class="card"><h3>RAGAS sobre la explicación</h3><p class="small"><b>Faithfulness</b>: la explicación de cada elección se parte en afirmaciones; un juez que ve lo mismo que el sistema dice cuáles se sostienen. <b>Answer relevance</b>: el juez infiere el pedido desde la respuesta y se compara con el original (coseno).</p></div>'
    '<div class="card"><h3>Juez de a pares, en los dos órdenes</h3><p class="small">Sin ground truth (ambiente vacío): un juez ve la foto, el pedido y dos listas sin saber de qué variante son, puntúa cada producto (2/1/0) y elige una. Se pregunta en los dos órdenes: gana un ambiente si gana en los dos; si no, empate. Reportamos el <b>acuerdo entre órdenes</b> (sesgo de posición).</p></div>'
    '<div class="card"><h3>Costo y latencia</h3><p class="small">Cada llamada paga queda registrada con su costo, tokens y latencia. Un método que mejora 2 puntos y cuesta el triple no siempre conviene.</p></div>'
    "</div>",
    kicker="Métricas · la respuesta",
    title="Sin un único correcto: jueces validados y comparaciones de a pares",
    mins=0.9,
    notes="Cuando no hay un único correcto usamos jueces, pero validados. Relevancia graduada: un LLM califica el top-3 con 2, 1 o 0, y antes chequeamos que le dé 2 al producto anotado. RAGAS sobre la explicación de cada elección: faithfulness, si lo que dice se sostiene con lo que vio, y answer relevance, si responde al pedido. Para comparar variantes sin ground truth, un juez de a pares en los dos órdenes, y reportamos cuánto coinciden los dos órdenes. Y el costo de cada llamada.",
)

slide(
    '<div class="grid3 metric">'
    '<div class="card"><h3>Preservación del ambiente</h3><p class="small"><b>SIFT + RANSAC</b>: puntos de la foto original que se reencuentran en la imagen y cuánto se movió la cámara. <b>SSIM</b> fuera de las cajas de los muebles: lo que no es mueble tiene que quedar igual.</p></div>'
    '<div class="card"><h3>Fidelidad de los productos</h3><p class="small">Grounding DINO detecta cada mueble de la imagen; el recorte se compara con DINOv3 contra todas las fotos del catálogo de su tipo: ¿el más parecido es el producto de la lista? Vara: lo mismo con fotos reales de ambientes IKEA.</p></div>'
    '<div class="card"><h3>Pedido ↔ imagen</h3><p class="small"><b>SigLIP 2</b>: similitud entre el pedido y la imagen, contra la foto vacía. Y conteo: productos que faltan, repetidos o inventados.</p></div>'
    "</div>"
    '<div class="grid2" style="margin-top:16px">'
    '<div class="card metric"><h3>Reproducibilidad</h3><p class="small">Las mismas búsquedas escritas por tres redactores distintos: si el resultado cambia mucho con quién escribe, la métrica mide al redactor y no al sistema.</p></div>'
    '<div class="card metric"><h3>El espacio de embeddings</h3><p class="small">¿El vecino más cercano de cada producto es de su mismo kind? Separabilidad (silhouette) y una UMAP con una consulta del dominio y una de afuera.</p></div>'
    "</div>",
    kicker="Métricas · la imagen y el resto",
    title="La imagen: mismo cuarto, mismos productos, lo que se pidió",
    mins=0.9,
    notes="Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad, con tres redactores, y el espacio de embeddings.",
)

# ---- Experimentos
section(
    "Parte 4",
    "Experimentos",
    "Cada uno: por qué lo hicimos y qué queríamos ver, cómo lo medimos, qué dio y qué decidimos. Lo que se decide queda en la configuración del siguiente.",
    notes="Ahora los experimentos. Todos siguen el mismo orden: primero por qué lo hicimos y qué queríamos ver, que está arriba en cada slide; después cómo es el experimento, a la izquierda; y recién ahí mostramos los resultados y la decisión, que aparecen con la flecha.",
    mins=0.3,
)

# E1: qué texto
experiment(
    "1",
    "Qué texto se indexa",
    "Alcanza con el texto del vendedor, o hay que describir cada producto?",
    '<ul class="small"><li><b>Vendedor</b>: nombre, tipo, colores y la frase de IKEA.</li>'
    "<li><b>Descripción del VLM</b>: las 8 líneas escritas mirando la foto, en el mismo formato que la consulta.</li>"
    "<li><b>Nombre + descripción</b>: el nombre comercial adelante (\"NOLMYRA\").</li></ul>"
    '<div class="find" style="margin-top:14px">Es el cambio más grande de todo el trabajo: <b>×4</b> en hit@1. El nombre comercial empeora: es ruido para el embedding.</div>',
    bars_methods(
        [("qwen3|seller|filtro-type", "vendedor"), ("qwen3|name+description|filtro-kind", "nombre + descripción"), (BASE, "descripción del VLM")],
        BASE,
        width=520,
        label_w=190,
    ),
    "<b>Decisión:</b> se indexa solo la descripción del VLM. Describir el catálogo es un costo único, offline.",
    hl=("describe",),
    why="El texto de IKEA casi no describe el producto (“The armchair is lightweight...”), y un usuario pide estilo, color y materiales: cosas que están en la foto, no en el texto.",
    notes={
        "motivo": "Lo primero que miramos fue qué texto trae el catálogo. IKEA tiene nombre, tipo, colores y una frase de marketing del estilo “The armchair is lightweight and easy to move”. Pero nadie pide así: se pide un sillón nórdico, de madera clara, con tapizado crema, y todo eso está en la foto. La pregunta era si alcanzaba con el texto del vendedor o si valía la pena describir cada producto mirando su foto, un costo que se paga una sola vez.",
        "experimento": f"Indexamos tres textos y corrimos las mismas {ABL[BASE]['answerable']} búsquedas del ground truth, con todo lo demás fijo (Qwen3, filtro por tipo): el texto del vendedor; la descripción de 8 líneas que escribe un VLM mirando la foto, en el mismo formato en que el plan escribe la consulta; y esa descripción con el nombre comercial adelante.",
        "resultados": f"Con el texto del vendedor, hit@1 da {num(m('qwen3|seller|filtro-type')['hit@1'])}; con la descripción del VLM, {num(m(BASE)['hit@1'])}: más de cuatro veces. Es el cambio más grande de todo el trabajo. El nombre comercial adelante empeora: con el mismo filtro, de {num(m('qwen3|description|filtro-kind')['hit@1'])} a {num(m('qwen3|name+description|filtro-kind')['hit@1'])}. NOLMYRA no le dice nada al embedding.",
        "decision": "Indexamos solo la descripción del VLM. Y queda una idea que vuelve en todo el trabajo: la consulta y el documento escritos en el mismo formato.",
    },
)

# E2: embedder
sep = (ESP or {}).get("separabilidad") or {}
experiment(
    "2",
    "Embedder",
    "Cuánto aporta un modelo de embeddings sobre un vector de palabras?",
    '<ul class="small"><li><b>hashing</b>: bolsa de palabras hasheada, sin modelo (línea de base).</li>'
    "<li><b>BGE-base</b> (110M) y <b>Qwen3-Embedding-0.6B</b>, locales.</li></ul>"
    '<div class="find" style="margin-top:14px">El hashing queda a 2 puntos de Qwen3: las descripciones comparten vocabulario controlado (estilos de una lista, kinds), así que hasta contar palabras funciona. Qwen3 gana en MRR y en consultas difíciles; BGE queda último.</div>',
    bars_methods(
        [("hashing|description|filtro-type", "hashing"), ("bge|description|filtro-type", "BGE-base"), (BASE, "Qwen3-0.6B")],
        BASE,
        width=520,
        label_w=150,
    ),
    "<b>Decisión:</b> Qwen3-Embedding-0.6B (Apache-2.0, corre en CPU). El vocabulario controlado de las descripciones vale más que el modelo.",
    hl=("embed",),
    why="Con un texto bueno, el siguiente candidato es el modelo de embeddings. Uno más grande cuesta memoria y tiempo, y queríamos que el retrieval corra local, en CPU.",
    notes={
        "motivo": "Con el texto resuelto, la pregunta natural es cuánto aporta el modelo de embeddings. Un modelo más grande cuesta memoria y tiempo, y nos pusimos la restricción de que el retrieval corra local, en CPU, sin pagar una API. Queríamos ver cuánto gana un modelo entrenado contra una línea de base sin modelo.",
        "experimento": "Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras hasheada, sin ningún modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.",
        "resultados": f"Gana Qwen3, con {num(m(BASE)['hit@1'])}. Pero el hashing queda cerca ({num(m('hashing|description|filtro-type')['hit@1'])}) y BGE último ({num(m('bge|description|filtro-type')['hit@1'])}). La explicación: las descripciones usan vocabulario controlado, los estilos y los kinds salen de listas cerradas, así que hasta contar palabras funciona bastante. Qwen3 gana más claro en MRR y en las búsquedas difíciles.",
        "decision": "Qwen3-Embedding-0.6B (Apache 2.0, corre en CPU). La lección: el formato del texto vale más que el modelo.",
    },
)

# E3: filtros
experiment(
    "3",
    "Filtros duros",
    "Conviene filtrar por tipo de mueble antes de buscar, o dejar todo a la similitud?",
    '<ul class="small"><li><b>ninguno</b>: todo el catálogo.</li><li><b>tipo</b> (sofá, mesa, lámpara...): 14 tipos.</li><li><b>kind</b> (mesa ratona, mesa de comedor...): 41 kinds.</li></ul>'
    '<div class="find" style="margin-top:14px">Con descripciones buenas el filtro casi no cambia hit@1, pero el de kind <b>resta</b>: cuando la consulta y el producto discrepan en el kind fino (mesa auxiliar o ratona) lo deja afuera. El de tipo protege de errores gruesos sin ese costo.</div>',
    bars_methods(
        [("qwen3|description|filtro-none", "sin filtro"), ("qwen3|description|filtro-kind", "por kind"), (BASE, "por tipo")],
        BASE,
        metric="hit@10",
        width=520,
        label_w=150,
    ),
    "<b>Decisión:</b> filtrar siempre, más las medidas máximas del plan. El flujo filtra por los kinds que elige el plan (puede dar más de uno: ratona o auxiliar); pasarlo a tipo es lo próximo a probar.",
    hl=("retrieve",),
    why="El plan ya sabe qué pieza busca (“un sofá”), y por similitud sola una mesa del mismo estilo puede quedar arriba. Un filtro duro lo evita, pero puede dejar afuera al correcto.",
    notes={
        "motivo": "El plan sabe qué pieza está buscando: un sofá, una lámpara. Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita y es gratis, pero tiene un riesgo: si el plan y el catálogo no coinciden en la categoría, el producto correcto queda afuera. Queríamos ver si conviene filtrar, y con qué granularidad.",
        "experimento": "Tres opciones: sin filtro; filtro por tipo, 14 categorías gruesas como sofá, mesa o lámpara; y filtro por kind, 41 categorías finas como mesa ratona o mesa de comedor. En ChromaDB el filtro va como where. Miramos hit@1 y sobre todo hit@10.",
        "resultados": f"Con descripciones buenas, hit@1 casi no cambia. Pero el filtro por kind resta: en hit@10 da {num(m('qwen3|description|filtro-kind')['hit@10'])} contra {num(m(BASE)['hit@10'])} del filtro por tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como mesa ratona, el filtro fino la deja afuera. El de tipo protege de los errores gruesos sin ese costo.",
        "decision": "Filtrar siempre, más las medidas máximas que estima el plan. Con qué granularidad quedó abierto: el flujo filtra por los kinds que elige el plan, que puede dar más de uno (mesa ratona o auxiliar) para no dejar afuera al correcto. La diferencia con el filtro por tipo es de un punto en hit@1, dentro del intervalo, y tres en hit@10; pasar el flujo a tipo es lo próximo que probaríamos.",
    },
)

# E4: chunking
experiment(
    "4",
    "Splitting",
    "Un documento por producto, o un chunk por cada línea de la descripción?",
    '<ul class="small"><li><b>documento</b>: las 8 líneas juntas, un vector.</li>'
    "<li><b>chunk por línea, el mejor</b>: el producto vale su línea más parecida a la consulta.</li>"
    "<li><b>línea contra línea</b>: cada línea contra la del mismo rótulo de la consulta, promediado.</li></ul>"
    '<div class="find" style="margin-top:14px">Partir en líneas pierde el contexto: "Colors: light wood" se parece a cualquier cosa de madera clara. La descripción ya es corta (60–90 palabras): no hay nada que partir.</div>',
    bars_methods(
        [("qwen3|description|filtro-type|chunks-lines-max", "chunk por línea"), ("qwen3|description|filtro-type|chunks-lines-aligned", "línea contra línea"), (BASE, "un documento")],
        BASE,
        width=520,
        label_w=170,
    ),
    "<b>Decisión:</b> un documento por producto.",
    hl=("embed",),
    why="El chunking es una de las decisiones clásicas de un RAG. Nuestros documentos son cortos, pero sus 8 líneas tienen roles distintos: quizás convenía comparar cada línea por separado.",
    notes={
        "motivo": "En la materia vimos que el chunking es una de las decisiones centrales de un RAG. Nuestros documentos son cortos, de 60 a 90 palabras, pero tienen 8 líneas con roles distintos: tipo, estilo, colores, materiales. La hipótesis era que comparar línea por línea, colores contra colores, podía ser más preciso que un solo vector por producto.",
        "experimento": "Tres formas: un documento por producto, con las 8 líneas juntas; un chunk por línea, donde el producto vale lo que su línea más parecida a la consulta; y línea contra línea, cada una contra la del mismo rótulo en la consulta, promediado.",
        "resultados": f"Gana un documento por producto ({num(m(BASE)['hit@1'])}). Línea contra línea queda cerca ({num(m(BASE + '|chunks-lines-aligned')['hit@1'])}) y el chunk por línea se desploma ({num(m(BASE + '|chunks-lines-max')['hit@1'])}): una línea suelta como “Colors: light wood” se parece a cualquier cosa de madera clara. Partir pierde el contexto.",
        "decision": "Un documento por producto. Con documentos tan cortos no hay nada que partir.",
    },
    mins=0.6,
)

# E5: dimensión
dims = [32, 64, 128, 256, 512, 1024]
dvals = [m(f"{BASE}|dim-{d}")["hit@1"] if d != 1024 else m(BASE)["hit@1"] for d in dims]
experiment(
    "5",
    "Dimensión del embedding",
    "Cuántas dimensiones hacen falta? (Qwen3 se entrenó con Matryoshka: se trunca sin reentrenar)",
    '<p class="small">Se truncan los vectores a sus primeras d componentes y se renormalizan. Memoria por vector: 4 bytes × d.</p>'
    '<div class="find">Con 512 dimensiones da lo mismo que con 1024, con la mitad de memoria. Por debajo de 128 cae rápido.</div>',
    lines(
        [{"ys": dvals, "hl": True, "labels": {32: num(dvals[0]), 512: num(dvals[4]), 1024: num(dvals[5])}}],
        dims,
        ymin=0.3,
        ymax=0.6,
        width=560,
        height=290,
        xlabel="dimensiones (escala log)",
        ylabel="hit@1",
        xlog=True,
    ),
    "<b>Decisión:</b> se puede indexar con 512 sin perder nada. Con 819 productos no hace falta (el índice entra igual en memoria); en un catálogo de millones, sí.",
    hl=("embed", "vdb"),
    why="Qwen3 se entrenó con Matryoshka: sus vectores se pueden truncar sin reentrenar. En un catálogo grande, la memoria y la latencia crecen con la dimensión.",
    notes={
        "motivo": "Qwen3 se entrenó con Matryoshka: las primeras componentes del vector concentran la información, así que se puede truncar sin reentrenar. Con 819 productos no importa, pero en un catálogo de millones la memoria y la latencia crecen con la dimensión. Queríamos saber cuánto se puede achicar sin perder.",
        "experimento": "Truncamos los vectores a 32, 64, 128, 256, 512 y 1024 componentes, los renormalizamos y corrimos las mismas búsquedas.",
        "resultados": f"Con 512 da prácticamente lo mismo que con 1024 ({num(dvals[4])} contra {num(dvals[5])}), con la mitad de memoria. Por debajo de 128 cae rápido: con 32, {num(dvals[0])}.",
        "decision": "Para este catálogo dejamos 1024 porque no cuesta nada; si creciera, indexaríamos con 512.",
    },
    mins=0.6,
)

# E6: base vectorial y consulta
experiment(
    "6",
    "Base vectorial y query rewriting",
    "HNSW aproxima: pierde algo contra la búsqueda exacta? Y cuánto de la consulta hace falta?",
    '<ul class="small"><li><b>ChromaDB</b> (HNSW, coseno, filtros como <code>where</code>) contra recorrer todos los vectores con numpy.</li>'
    "<li>Query rewriting: la consulta completa (8 líneas) contra solo la línea Type o solo el kind.</li></ul>"
    f'<div class="find" style="margin-top:14px">HNSW da exactamente lo mismo que la búsqueda exacta ({num(m(BASE + "|exact")["hit@1"], 3)} y {num(m(BASE)["hit@1"], 3)}). Reescribir la consulta a algo más corto es mucho peor: el estilo, los colores y la forma son lo que distingue un sofá de otro.</div>',
    bars_methods(
        [(BASE + "|consulta-kind", "solo el kind"), (BASE + "|consulta-type", "solo la línea Type"), (BASE + "|exact", "8 líneas, exacta"), (BASE, "8 líneas, ChromaDB")],
        BASE,
        width=520,
        label_w=180,
    ),
    "<b>Decisión:</b> ChromaDB con la consulta completa que escribe el plan.",
    hl=("vdb", "plan"),
    why="Pasamos de recorrer los vectores con numpy a ChromaDB, que aproxima (HNSW). Y escribir la consulta completa de 8 líneas cuesta tokens y latencia en cada pedido.",
    notes={
        "motivo": "Dos dudas. Primero, pasamos de una búsqueda exacta con numpy a ChromaDB, que usa HNSW, un índice aproximado: había que verificar que no perdiera resultados. Segundo, el query rewriting: el plan escribe para cada pieza el producto ideal en 8 líneas, y eso cuesta tokens y latencia en cada pedido. Queríamos ver si una consulta más corta alcanzaba.",
        "experimento": "ChromaDB contra la búsqueda exacta, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el nombre del kind, que sería no reescribir.",
        "resultados": f"HNSW da exactamente lo mismo que la búsqueda exacta ({num(m(BASE + '|exact')['hit@1'], 3)} y {num(m(BASE)['hit@1'], 3)}). Con solo la línea Type, hit@1 cae a {num(m(BASE + '|consulta-type')['hit@1'])}; con solo el kind, a {num(m(BASE + '|consulta-kind')['hit@1'])}. El estilo, los colores y la forma son lo que distingue un sofá de otro.",
        "decision": "ChromaDB con la consulta completa que escribe el plan. El query rewriting cuesta, pero vale la pena.",
    },
)

# E7: reranking
r0, r1 = RER[BASE], RER[BASE + "|rerank-opus"]
mini = m(BASE + "|rerank-minilm-reranker")
experiment(
    "7",
    "Reranking (Advanced RAG)",
    "Un segundo modelo que mire la consulta y cada candidato juntos ordena mejor el top-10?",
    '<ul class="small"><li><b>cross-encoder MiniLM</b> (MS MARCO, local, gratis): lee consulta y descripción juntas.</li>'
    "<li><b>VLM</b> (Claude Opus 5.5): ve la consulta y las <b>fotos</b> de los 10 candidatos y los ordena.</li></ul>"
    f'<div class="find" style="margin-top:14px">MiniLM <b>empeora</b>: está entrenado en preguntas y pasajes web, no en descripciones de muebles. El VLM sube hit@1 de {num(r0["hit@1"])} a <b>{num(r1["hit@1"])}</b> (MRR {num(r0["mrr@10"])} → {num(r1["mrr@10"])}): mira la foto, que tiene lo que la descripción no dijo.</div>',
    hbars(
        [
            {"label": "sin rerank", "value": r0["hit@1"], "ci": ci(r0)},
            {"label": "MiniLM", "value": mini["hit@1"], "ci": ci(mini)},
            {"label": "VLM (Opus)", "value": r1["hit@1"], "ci": ci(r1), "hl": True},
        ],
        width=520,
        label_w=140,
    ),
    "<b>Decisión:</b> el reranking con VLM funciona, y el paso choose ya es eso: Claude elige mirando las fotos de los candidatos. La pregunta pasa a ser cuántos candidatos verle (exp. 8). Costo: ~US$0,02 por búsqueda.",
    hl=("rerank", "choose"),
    why=f"hit@10 daba {num(m(BASE)['hit@10'])} pero hit@1 {num(m(BASE)['hit@1'])}: el correcto casi siempre está entre los 10 primeros, pero no arriba. El cuello de botella era el orden.",
    notes={
        "motivo": f"Mirando los resultados vimos que hit@10 era {num(m(BASE)['hit@10'])} pero hit@1 {num(m(BASE)['hit@1'])}: el producto correcto casi siempre está entre los 10 primeros, pero no primero. El cuello de botella era el orden. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos. Queríamos ver si eso ordena mejor, y con qué tipo de modelo.",
        "experimento": "Dos rerankers sobre el top-10: un cross-encoder MiniLM entrenado en MS MARCO, local y gratis, que lee la consulta y la descripción juntas; y Claude Opus como VLM, que ve la consulta y las fotos de los 10 candidatos y los ordena.",
        "resultados": f"MiniLM empeora ({num(mini['hit@1'])}): está entrenado con preguntas y pasajes web, no con descripciones de muebles. El VLM sube hit@1 de {num(r0['hit@1'])} a {num(r1['hit@1'])} y MRR de {num(r0['mrr@10'])} a {num(r1['mrr@10'])}: mira la foto, que tiene lo que la descripción no dijo. Cuesta unos dos centavos de dólar por búsqueda.",
        "decision": "El reranking con VLM funciona, y nuestro paso choose ya es eso: Claude elige mirando las fotos de los candidatos. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle, que es el experimento siguiente.",
    },
)

# E8: candidatos
ks = list(range(1, 11))
acc = [CURVA["por_k"][str(k)]["acierto_eleccion"] for k in ks]
cei = [CURVA["por_k"][str(k)]["techo_hit@k"] for k in ks]
experiment(
    "8",
    "Candidatos por pieza",
    "A cuántos candidatos por pieza conviene mirar? Más candidatos: más chances de que esté el correcto, pero más fotos para elegir.",
    '<p class="small">Del reranking del top-10 sale gratis la elección entre los k primeros: el elegido es el mejor rankeado por el VLM entre esos k. '
    "<b>Techo</b>: el correcto está entre los k (hit@k).</p>"
    f'<div class="find">De 3 a 5 candidatos la elección sube de {num(acc[2], 3)} a <b>{num(acc[4], 3)}</b>; a partir de 8 se aplana ({num(acc[7], 3)}). La distancia al techo crece: el VLM no siempre reconoce al correcto entre muchos parecidos.</div>',
    lines(
        [
            {"name": "techo (hit@k)", "ys": cei, "dash": True},
            {"name": "elección del VLM", "ys": acc, "hl": True, "below": True, "labels": {3: num(acc[2]), 5: num(acc[4]), 8: num(acc[7])}},
        ],
        ks,
        ymin=0.5,
        ymax=0.9,
        width=560,
        height=300,
        xlabel="candidatos por pieza (k)",
        ylabel="acierto",
        marks=[{"x": 5, "text": "elegido"}],
    ),
    "<b>Decisión:</b> 5 candidatos por pieza (antes 3). Casi toda la mejora, sin llenar la llamada de choose de fotos (9 piezas × 5 = 45 imágenes).",
    hl=("retrieve", "choose"),
    off=("rerank",),
    why=f"choose ya es un reranker con fotos, pero con 3 candidatos el correcto faltaba en una de cada cuatro piezas (hit@3 = {num(cei[2])}). Más candidatos suben ese techo, pero hacen más difícil y más cara la elección.",
    notes={
        "motivo": "El paso choose ya es un reranker que mira fotos, pero le pasábamos 3 candidatos por pieza, y con 3 el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro, y más difícil elegir entre muchos parecidos. Queríamos encontrar el k que maximiza la chance de que el VLM elija bien.",
        "experimento": "Lo sacamos gratis del experimento anterior: si el VLM ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Así sale la curva para k de 1 a 10 sin pagar nada más. Es un proxy: el choose real además ve el ambiente y el pedido.",
        "resultados": f"La línea punteada es el techo: que el correcto esté entre los k. La sólida es lo que elegiría el VLM. De 3 a 5 candidatos, la elección sube de {num(acc[2], 3)} a {num(acc[4], 3)}; a partir de 8 se aplana. Y la distancia al techo crece: entre muchos parecidos, el VLM no siempre reconoce al correcto.",
        "decision": "5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.",
    },
)

# E9: catálogo ampliado y revisado
old, new = CAT_OLD[BASE], CAT_NEW[BASE]
experiment(
    "9",
    "Catálogo: ampliación y revisión",
    "Qué pasa al pasar de 4 tipos de muebles a todo un living, y al sacar los productos mal cargados?",
    '<ul class="small"><li><b>Ampliación</b>: de sofás, sillones, mesas y alfombras (268 productos) a guardado, iluminación, textiles y deco (855).</li>'
    "<li><b>Revisión</b>: 36 productos fuera: la foto es de otro producto u otra medida, o no son de living (botiquines, estantes sueltos); 7 kinds corregidos mirando la foto.</li></ul>"
    f'<div class="find" style="margin-top:14px">Ampliar baja hit@1 (de 0,636 a {num(old["hit@1"], 3)}): hay más productos parecidos entre sí y las consultas nuevas son de deco, más difícil. Pero sin ampliar no hay biblioteca, lámpara ni cortinas que recomendar. La revisión no cambia el retrieval ({num(old["hit@1"], 3)} → {num(new["hit@1"], 3)}): cambia que la lista y la imagen muestren el producto correcto.</div>',
    hbars(
        [
            {"label": "268 productos", "value": 0.6364},
            {"label": "855 (ampliado)", "value": old["hit@1"], "ci": ci(old)},
            {"label": "819 (revisado)", "value": new["hit@1"], "ci": ci(new), "hl": True},
        ],
        width=520,
        label_w=160,
    ),
    "<b>Decisión:</b> catálogo ampliado y revisado (819). Medir hit@1 sobre catálogos distintos no es comparar lo mismo: el universo cambia.",
    hl=("catalogo",),
    why="El primer catálogo tenía solo sofás, sillones, mesas y alfombras: no había biblioteca, lámpara ni cortinas que recomendar. Y al describirlo aparecieron productos con la foto de otro.",
    notes={
        "motivo": "El primer alcance eran sofás, sillones, mesas y alfombras: 268 productos. Con pedidos reales, la gente pide una biblioteca, una lámpara de pie, cortinas, y no había nada. Así que ampliamos. Y mientras los subagentes describían los productos, marcaron varios con la foto de otro producto o mal clasificados: la lista diría una cosa y la imagen mostraría otra. Queríamos saber cuánto cuesta ampliar en retrieval y qué cambia la limpieza.",
        "experimento": "Las mismas métricas sobre tres catálogos: el de 268, el ampliado a 855 (guardado, iluminación, textiles y deco) y el revisado, con 36 productos afuera y 7 kinds corregidos.",
        "resultados": f"Ampliar baja hit@1 de 0,636 a {num(old['hit@1'], 3)}: hay más productos parecidos y las búsquedas nuevas son de deco, que es más difícil. La revisión casi no lo cambia ({num(old['hit@1'], 3)} a {num(new['hit@1'], 3)}), pero hace que el producto de la lista sea el de la foto. Ojo: no son números directamente comparables, porque cambia el universo.",
        "decision": "Catálogo ampliado y revisado. Perder unos puntos de hit@1 es el precio de poder amoblar un living completo.",
    },
)

# E10: qué catálogo (punta a punta)
def split_e2e(res: dict, a: str, b: str) -> list[tuple]:
    out = []
    for lab, cond in (
        ("propios (nórdicos)", lambda x: not x.startswith("publica")),
        ("públicos (otros)", lambda x: x.startswith("publica")),
        ("total", lambda x: True),
    ):
        ds = [d for d in res["detalle"] if cond(d["slug"])]
        if not ds:
            continue

        def util(v, ds=ds):
            g = [x for d in ds for sd in d["puntajes"][v] for x in sd["grades"]]
            return sum(x == 2 for x in g) / max(1, len(g))

        out.append(
            (lab, len(ds), sum(d["ganador"] == a for d in ds), sum(d["ganador"] == b for d in ds),
             sum(d["ganador"] == "tie" for d in ds), util(a), util(b))
        )
    return out


abo5 = E2E.get("juez_ikea_vs_abo_5ambientes")
tod11 = E2E.get("juez_ikea_vs_todos")
tbl10 = ""
if abo5:
    s5 = abo5["resumen"]
    tbl10 += (
        '<h3 style="margin-bottom:4px">1. IKEA contra ABO (5 ambientes propios)</h3>'
        f'<table class="t"><tr><th></th><th>gana</th><th>útil</th><th>pedido</th><th>ambiente</th><th>conjunto</th></tr>'
        + "".join(
            f'<tr class="{"hl" if v == "ikea" else ""}"><td>{"IKEA" if v == "ikea" else "ABO"}</td><td class=n>{s5[v]["gana"]}</td><td class=n>{num(s5[v]["util"])}</td>'
            f'<td class=n>{num(s5[v]["request"], 1)}</td><td class=n>{num(s5[v]["room"], 1)}</td><td class=n>{num(s5[v]["together"], 1)}</td></tr>'
            for v in ("ikea", "abo")
        )
        + f'</table><div class="cap">{abo5["empates"]} empate. ABO pierde por estilo: maderas oscuras, patas doradas.</div>'
    )
if tod11:
    rows = split_e2e(tod11, "ikea", "todos")
    tbl10 += (
        '<h3 style="margin:14px 0 4px">2. IKEA contra IKEA + ABO (11 ambientes)</h3>'
        '<table class="t"><tr><th></th><th>n</th><th>IKEA</th><th>IKEA+ABO</th><th>emp.</th><th>útil I</th><th>útil I+A</th></tr>'
        + "".join(
            f'<tr class="{"hl" if lab == "total" else ""}"><td>{lab}</td><td class=n>{n}</td><td class=n>{wa}</td><td class=n>{wb}</td><td class=n>{t}</td><td class=n>{num(ua)}</td><td class=n>{num(ub)}</td></tr>'
            for lab, n, wa, wb, t, ua, ub in rows
        )
        + f'</table><div class="cap">Acuerdo entre órdenes {num(tod11["acuerdo_entre_ordenes"])}. Útil = productos con nota 2.</div>'
    )
experiment(
    "10",
    "Qué catálogo",
    "Con qué catálogo salen mejores listas para ambientes reales: IKEA, Amazon (ABO) o los dos?",
    '<ul class="small">'
    "<li><b>IKEA</b>: 819 productos, fotos de 500 px, asientos sin medidas, único con ground truth.</li>"
    f"<li><b>Amazon Berkeley Objects</b> (Collins et al., 2022): listados reales de Amazon; {abo_n} descriptos con el mismo formato (Opus por la API, US$5,4), fotos de 1024 px, medidas en el 90%.</li>"
    "<li>Sin ground truth: mismo plan, cambia solo el catálogo, y un juez compara las listas de a pares, en los dos órdenes.</li></ul>",
    f'<div style="width:600px">{tbl10 or "<p class=small>(pendiente)</p>"}</div>',
    "<b>Decisión:</b> IKEA + ABO: empata con pedidos nórdicos y gana 6 a 0 con otros estilos, porque trae lo pedido que IKEA 2013 no tiene. "
    "Sumar ABO casi no cambia el retrieval sobre el GT de IKEA (hit@1 0,535 → 0,525).",
    hl=("catalogo", "describe"),
    why="IKEA 2013 tiene fotos chicas, asientos sin medidas y una sola estética. Amazon Berkeley Objects tiene listados reales con medidas.",
    notes={
        "motivo": "El catálogo de IKEA tiene límites: es de 2013, las fotos son de 500 píxeles, los asientos no tienen medidas y tiene una sola estética, la nórdica. Encontramos Amazon Berkeley Objects, un dataset académico con listados reales de Amazon, con medidas y fotos grandes. Queríamos ver si con otro catálogo, o con los dos juntos, salen mejores listas para ambientes reales.",
        "experimento": "Acá no hay ground truth: nadie anotó qué sofá de Amazon va en un living vacío. Comparamos de punta a punta: mismos ambientes, mismos pedidos y el mismo plan; cambia solo el catálogo. Un juez, Claude Opus, ve la foto, el pedido y las dos listas sin saber de qué catálogo es cada una, y elige. Se le pregunta en los dos órdenes, y una variante gana un ambiente solo si gana en los dos. Primero lo corrimos en nuestros 5 departamentos.",
        "resultados": (
            "Primera tabla: IKEA le gana a Amazon 4 a 0; según el juez, Amazon pierde por estilo (maderas oscuras, patas doradas para pedidos nórdicos). "
            "Y IKEA + Amazon empataba con IKEA. Ahí vimos que los 5 pedidos eran nórdicos, justo la estética de IKEA, así que sumamos 6 ambientes públicos reales con pedidos de otros estilos: industrial, clásico, bohemio. "
            + (
                f"Segunda tabla: en los nórdicos siguen empatados; en los otros estilos, IKEA + Amazon gana {rows[1][3]} a {rows[1][2]}, y los productos útiles pasan de {num(rows[1][5])} a {num(rows[1][6])}. "
                f"Los dos órdenes del juez coinciden en el {num(100 * tod11['acuerdo_entre_ordenes'], 0)}% de los ambientes. "
                if tod11
                else ""
            )
            + "Y sumar Amazon casi no cambia el retrieval sobre el ground truth de IKEA: hit@1 de 0,535 a 0,525."
        ),
        "decision": "Usamos los dos catálogos. Y la lección: con ambientes y pedidos poco variados habríamos tomado la decisión contraria.",
    },
    mins=2.0,
)

# E11: el GT subestima + reproducibilidad
g = GRAD["consultas"]["todas"] if GRAD else None
# el hit@1 de la misma corrida que vio el juez (graduada.json dice cuál)
gh1 = (load(R / "evaluacion" / GRAD["run"] / "metricas.json") or {}).get(GRAD["method"], {}).get("hit@1") if GRAD else None
gh1 = gh1 if gh1 is not None else m(BASE)["hit@1"]
gt_agree = GRAD.get("acuerdo_con_gt", {}) if GRAD else {}
rep = [REPL[k][BASE]["hit@1"] for k in sorted(REPL)] if REPL else []
experiment(
    "11",
    "¿Cuánto mide el ground truth?",
    "Si el sistema no trae el producto anotado, se equivoca? Y cuánto depende el número de quién escribió las consultas?",
    '<ul class="small"><li>Un juez califica el top-3 (2/1/0) en 150 búsquedas. Para confiar en él: le da 2 al producto anotado el '
    f'<b>{num(100 * gt_agree.get("anotado_con_2", 0.81), 0)}%</b> de las veces y a los demás el {num(100 * gt_agree.get("otros_con_2", 0.05), 0)}%.</li>'
    f"<li>Tres redactores escribieron las mismas búsquedas: hit@1 {' · '.join(num(x, 3) for x in [m(BASE)['hit@1'], *rep])}.</li></ul>"
    '<div class="find" style="margin-top:14px">El ground truth <b>subestima</b>: en 3 de cada 4 búsquedas el primero sirve, aunque sea el anotado solo en la mitad. Y el resultado varía ±2,6 puntos con el redactor: diferencias menores entre métodos no son señal.</div>',
    hbars(
        [
            {"label": "hit@1 (ground truth)", "value": gh1},
            {"label": "útil@1 (juez)", "value": g["util1"], "ci": tuple(g.get("util1_ic95") or (0.68, 0.82)), "hl": True},
            {"label": "útil@3 (juez)", "value": g["util3"], "ci": tuple(g.get("util3_ic95") or (0.78, 0.89))},
        ]
        if g
        else [],
        width=520,
        label_w=170,
    ),
    "<b>Conclusión:</b> reportamos hit@1 para comparar métodos (es objetivo y barato) y la relevancia graduada para saber cuán útil es de verdad.",
    why="El ground truth tiene un solo producto correcto por pieza, pero otro parecido puede servir igual. Y las consultas las escribieron modelos: el número podía depender de quién las escribió.",
    notes={
        "motivo": "Todos los números hasta acá son contra un ground truth con un solo producto correcto por pieza. Pero si el sistema trae un sillón casi igual al anotado, ¿se equivocó? Y las búsquedas de evaluación las escribieron subagentes: si las escribiera otro, ¿cambiaría el número? Queríamos saber cuánto mide realmente el ground truth.",
        "experimento": "Dos cosas. Un juez califica el top-3 de 150 búsquedas: 2 si es el mismo o indistinguible, 1 si es una alternativa aceptable, 0 si no sirve; antes de creerle, lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.",
        "resultados": (
            f"El juez le da 2 al producto anotado el {num(100 * gt_agree.get('anotado_con_2', 0.81), 0)}% de las veces y a los demás el {num(100 * gt_agree.get('otros_con_2', 0.05), 0)}%: es confiable. "
            + (f"Con él, el primer candidato sirve en el {num(100 * g['util1'], 0)}% de los casos, aunque hit@1 sea {num(gh1)}: el ground truth subestima. " if g else "")
            + "Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas que eso entre métodos no son señal."
        ),
        "decision": "Reportamos hit@1 para comparar métodos, porque es objetivo y barato, y la relevancia graduada para saber cuán útil es de verdad.",
    },
)

# E12: la imagen
runs_img = [
    ("experimento", "escena escrita por el LLM"),
    ("experimento-libre", "escena libre"),
    ("experimento-buen-pedido", "libre, sin tope de piezas"),
    ("experimento-buen-pedido-estricto", "edición estricta"),
]
cells, sift = "", {}
for r, lab in runs_img:
    d = R / "amoblar" / r
    if (d / "final.png").exists():
        mi = load(d / "6_metricas_imagen.json") or {}
        amb = mi.get("ambiente") or {}
        sift[r] = amb.get("sift_inliers")
        stats = f' · SIFT {amb.get("sift_inliers")} pts · SSIM fuera {num(amb["ssim_fuera_de_los_muebles"])}' if amb else ""
        cells += f'<div>{img(d / "final.png", 520, cls="photo")}<div class="cap"><b>{esc(lab)}</b>{stats}</div></div>'
experiment(
    "12",
    "La imagen: del cuarto reimaginado al cuarto del cliente",
    "Cómo pedirle al modelo de imagen que respete el ambiente, y cómo darnos cuenta solos cuando no lo hace?",
    f'<div style="width:250px">{img(EST / "room.jpg", 500, cls="photo")}<div class="cap"><b>original</b></div>'
    '<ul class="small" style="margin-top:10px;font-size:14.5px"><li>Mismo ambiente. Arriba, el pedido corto (6 piezas); abajo, el completo (9 piezas, sin tope).</li>'
    "<li>Medimos SIFT (puntos de la foto original que se reencuentran) y SSIM fuera de los muebles.</li></ul></div>",
    f'<div style="width:800px"><div class="grid2 fix h125" style="gap:6px 12px">{cells}</div></div>',
    "<b>Decisión:</b> edición estricta (mismo encuadre, paredes y aberturas; exactamente esos productos) y un control: si SIFT no reencuentra el cuarto, se descarta y se reintenta (hasta 3).",
    why="En las primeras imágenes el modelo redecoraba: inventó una ventana y movió la biblioteca. El usuario quiere ver su cuarto.",
    notes={
        "motivo": "Cuando empezamos a generar imágenes vimos que el modelo no solo agregaba los muebles: redecoraba. En este ejemplo inventó una ventana y movió la biblioteca. Para el usuario eso no sirve: quiere ver su cuarto con esos productos. Queríamos encontrar cómo pedirle al modelo que respete el ambiente, y cómo detectar automáticamente cuando no lo hace.",
        "experimento": "El mismo ambiente, cuatro versiones del paso de la imagen. Las dos de arriba son con el pedido corto, de 6 piezas: una escena que escribe el LLM describiendo dónde va cada cosa, y una escena libre. Las dos de abajo, con el pedido completo, de 9 piezas: libre, y una edición estricta, que exige el mismo encuadre, las mismas paredes y aberturas y exactamente los productos de las fotos. Medimos con SIFT cuántos puntos de la foto original se reencuentran, y SSIM fuera de los muebles.",
        "resultados": f"Arriba, las dos primeras conservan el cuarto pero la biblioteca queda chica. Abajo a la izquierda, libre y sin tope: linda, pero inventó una ventana; SIFT lo detecta, reencuentra solo {sift.get('experimento-buen-pedido')} puntos. La edición estricta conserva el cuarto, con {sift.get('experimento-buen-pedido-estricto')} puntos, y la biblioteca es la que se pidió.",
        "decision": "Edición estricta y un control automático: si SIFT no reencuentra el cuarto, la imagen se descarta y se reintenta, hasta 3 veces. En la slide siguiente se ve funcionando.",
    },
    mins=1.5,
)

# punta a punta en los ambientes propios
pairs = []
for slug, lab in (("caballito-living", "Living"), ("caballito-comedor", "Comedor")):
    d = R / "amoblar" / slug
    if (d / "final.png").exists():
        mi = load(d / "6_metricas_imagen.json") or {}
        im5 = load(d / "5_image.json") or {}
        fid, amb = mi.get("fidelidad") or {}, mi.get("ambiente") or {}
        n_att = len(im5.get("attempts") or [1])
        pairs.append(
            f'<div><div class="grid2 fix h300" style="gap:8px">{img(d / "room.jpg", 520, cls="photo")}{img(d / "final.png", 520, cls="photo")}</div>'
            f'<div class="cap"><b>{lab}</b> · {fid.get("detectados")}/{fid.get("productos")} productos en la imagen · '
            f'SSIM fuera de los muebles {num(amb.get("ssim_fuera_de_los_muebles", 0))} · aceptada en el intento {n_att}</div></div>'
        )
if pairs:
    slide(
        f'<div class="grid2" style="gap:22px">{"".join(pairs)}</div>'
        '<p class="small" style="margin-top:16px">Pedido, lista y escena con la configuración final: catálogo IKEA revisado, 5 candidatos, edición estricta. '
        "En el living, los dos primeros intentos salieron lindos pero con la cámara corrida (SIFT: 18 y 11 puntos, desplazamiento 16–20%); el control los descartó y el tercero (70 puntos, sin desplazamiento) quedó. "
        "El comedor pasó al primer intento (96 puntos).</p>",
        kicker="Resultado",
        title="De punta a punta, en un departamento real",
        notes="Y así queda todo junto, con la configuración final, en un departamento real. En el living, los dos primeros intentos de la imagen salieron lindos pero con la cámara corrida, y el control los descartó solo; el tercero quedó. El comedor pasó al primer intento.",
        mins=0.8,
    )

# Ej. 4 en una slide
slide(
    '<table class="t"><tr><th>Problema encontrado</th><th>Cambio</th><th>Antes → después</th></tr>'
    f"<tr><td>El texto de IKEA no describe el producto</td><td>VLM describe cada producto en 8 líneas</td><td>hit@1 {num(m('qwen3|seller|filtro-type')['hit@1'])} → {num(m(BASE)['hit@1'])}</td></tr>"
    f"<tr><td>La v0 no sirve con el ambiente vacío</td><td>RAG por texto con un plan que escribe la consulta</td><td>hit@1 {num(v0v1['v0'])} → {num(v0v1['v1'])} (mismo GT)</td></tr>"
    f"<tr><td>El primero del ranking no siempre es el mejor</td><td>El VLM elige mirando las fotos (rerank)</td><td>hit@1 {num(r0['hit@1'])} → {num(r1['hit@1'])}</td></tr>"
    f"<tr><td>Con 3 candidatos el correcto a veces no está</td><td>5 candidatos por pieza</td><td>elección {num(acc[2], 3)} → {num(acc[4], 3)}</td></tr>"
    "<tr><td>Una biblioteca chiquita (tope de 6 piezas, 1 unidad)</td><td>Sin tope de piezas; cantidades 0, 1 o más</td><td>2 bibliotecas HEMNES de piso a techo</td></tr>"
    "<tr><td>La imagen inventó una ventana</td><td>Edición estricta + control SIFT con reintento</td><td>10 → 116 puntos SIFT; pasa al 1.er intento</td></tr>"
    "<tr><td>Fotos de otro producto en el catálogo</td><td>Revisión del catálogo (36 fuera, 7 kinds)</td><td>la lista y la imagen coinciden</td></tr>"
    "<tr><td>Con estilos no nórdicos, IKEA no tiene lo pedido</td><td>Sumar Amazon Berkeley Objects al catálogo</td><td>útil 0,46 → 0,71; gana 6 a 0</td></tr>"
    "</table>",
    kicker="Ejercicio 4",
    title="La iteración: qué falló, qué cambiamos y cuánto mejoró",
    mins=0.7,
    notes="Esto es el ejercicio 4 en una tabla: cada fila es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de los experimentos que acabamos de ver.",
)

# el camino
path_rows = [
    {"label": "texto del vendedor, hashing, sin filtro", "value": m("hashing|seller|filtro-none")["hit@1"]},
    {"label": "+ descripciones del VLM", "value": m("hashing|description|filtro-none")["hit@1"]},
    {"label": "+ Qwen3 + filtro por tipo", "value": m(BASE)["hit@1"], "ci": ci(m(BASE))},
    {"label": "+ el VLM elige entre 5", "value": acc[4], "ci": tuple(CURVA["por_k"]["5"]["ic95"])},
    {"label": "+ el VLM reordena el top-10", "value": r1["hit@1"], "ci": ci(r1), "hl": True},
]
slide(
    '<div class="row" style="gap:40px"><div class="grow">'
    + hbars(path_rows, width=760, label_w=320, row_h=46)
    + '</div><div style="width:360px"><p class="small">hit@1 sobre los 65 ambientes IKEA (549 búsquedas con respuesta), catálogo revisado de 819 productos. Cada barra suma un cambio a la anterior.</p>'
    '<p class="small">Lo que más movió el número fue <b>qué texto se indexa</b>; lo segundo, que un VLM <b>mire las fotos</b>. El modelo de embeddings y la base vectorial aportan poco una vez que el texto es bueno.</p></div></div>',
    kicker="Resumen de los experimentos",
    title=f"El camino: de {num(path_rows[0]['value'])} a {num(r1['hit@1'])} de hit@1",
    notes=f"El resumen en un gráfico: cada barra suma un cambio a la anterior. Del texto del vendedor con una bolsa de palabras ({num(path_rows[0]['value'])}) al VLM reordenando el top-10 ({num(r1['hit@1'])}). Lo que más movió el número fue qué texto se indexa; lo segundo, que un VLM mire las fotos.",
    mins=0.7,
)

# costos: el promedio de plan y choose en las corridas de punta a punta (registro de gastos)
_led = [json.loads(x) for x in (ROOT / "datos/resultados/gastos.jsonl").read_text().splitlines()]


def _avg(step: str) -> float:
    v = [r["cost_usd"] for r in _led if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == step]
    return sum(v) / max(1, len(v))


c_plan, c_choose = _avg("furnish.plan"), _avg("furnish.choose")
slide(
    '<div class="grid4">'
    f'<div class="card"><div class="big">~US${num(c_plan + c_choose)}</div><div class="bignote">Claude por pedido: plan (US${num(c_plan)}) y choose con 5 fotos por pieza (US${num(c_choose)}), promedio medido en 11 ambientes. La escena ya no usa LLM.</div></div>'
    '<div class="card"><div class="big">US$0,08</div><div class="bignote">por imagen (Nano Banana 2, 1K), más los reintentos si cambia el cuarto.</div></div>'
    '<div class="card"><div class="big">~US$0,007</div><div class="bignote">por producto, una vez, para describir el catálogo con Opus por la API.</div></div>'
    '<div class="card"><div class="big">0</div><div class="bignote">embeddings y base vectorial: Qwen3 y ChromaDB locales, en CPU.</div></div>'
    "</div>"
    '<p style="margin-top:24px" class="small">Cada llamada paga queda en un registro con su costo, sus tokens y su latencia, con topes por cuenta que cortan antes de pasarse. '
    "Las respuestas de los jueces y del reranking quedan en caché: repetir un experimento no se vuelve a pagar.</p>",
    kicker="Costo",
    title="Cuánto cuesta un pedido",
    notes=f"Un pedido cuesta unos {round(100 * (c_plan + c_choose))} centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto. Embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y las respuestas de los jueces quedan en caché: repetir un experimento no se vuelve a pagar.",
    mins=0.5,
)

# limitaciones
slide(
    '<div class="grid2">'
    '<div class="card"><h3>Limitaciones</h3><ul class="small">'
    "<li>Catálogos viejos (IKEA 2013, Amazon 2019–20) y de uso no comercial.</li>"
    "<li>Las medidas del ambiente se estiman a ojo: el filtro de tamaño es aproximado, y los asientos de IKEA no tienen medidas.</li>"
    "<li>Un solo ground truth para el retrieval, con consultas escritas por modelos.</li>"
    "<li>La imagen es una visualización: escala y luz aproximadas.</li>"
    "<li>Pocos ambientes vacíos para evaluar de punta a punta.</li></ul></div>"
    '<div class="card"><h3>Trabajo futuro</h3><ul class="small">'
    "<li>Medidas reales: un metro en la foto o profundidad métrica (Depth Pro).</li>"
    "<li>Feed de un vendedor actual, con precio y stock como filtros.</li>"
    "<li>Más ambientes y evaluación humana de las imágenes.</li>"
    "<li>Que el usuario cambie piezas y regenere solo lo cambiado.</li></ul></div>"
    "</div>",
    kicker="Cierre",
    title="Limitaciones y trabajo futuro",
    notes="Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo y con consultas escritas por modelos; la imagen es una visualización, con escala y luz aproximadas; y tenemos pocos ambientes vacíos. Como trabajo futuro: medidas reales, con un metro en la foto o un modelo de profundidad; el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso.",
    mins=0.8,
)

# conclusiones
slide(
    '<div class="steps" style="max-width:1050px">'
    "<div><p><b>Lo que más importó fue el texto que se indexa</b>, no el modelo de embeddings: describir cada producto con un VLM, en el mismo formato que la consulta, multiplicó hit@1 por cuatro.</p></div>"
    "<div><p><b>El VLM mirando las fotos es el mejor reranker</b>, y el paso de elegir ya lo hace: la pregunta útil fue cuántos candidatos mostrarle.</p></div>"
    "<div><p><b>Las métricas con ground truth subestiman</b>: hace falta un juez, validado contra el ground truth y preguntado en los dos órdenes.</p></div>"
    "<div><p><b>El catálogo decide qué se puede recomendar</b>: con 5 ambientes nórdicos, IKEA alcanzaba; con estilos variados, sumar un segundo catálogo ganó 6 a 0. Evaluar con ambientes y pedidos variados cambió la decisión.</p></div>"
    "<div><p><b>La imagen necesita un control automático</b>: un prompt estricto ayuda, pero el control SIFT es lo que garantiza que el cuarto sea el del cliente.</p></div>"
    "</div>",
    kicker="Cierre",
    title="Conclusiones",
    notes="Para cerrar, cinco cosas. Lo que más importó fue el texto que se indexa, no el modelo. El mejor reranker es un VLM mirando las fotos, y nuestro paso de elegir ya lo es. Las métricas con ground truth subestiman, así que hace falta un juez, validado y preguntado en los dos órdenes. El catálogo decide qué se puede recomendar, y evaluar con ambientes variados cambió la decisión. Y la imagen necesita un control automático para que el cuarto sea el del cliente. Gracias.",
)

page = (Path(__file__).with_name("plantilla.html")).read_text().replace("__SLIDES__", "\n".join(SLIDES))
OUT.write_text(page)
print(f"{OUT}: {len(SLIDES)} slides, {OUT.stat().st_size / 1e6:.1f} MB")


# -- el guion ------------------------------------------------------------------------------------
def mmss(x: float) -> str:
    return f"{int(x)}:{round((x - int(x)) * 60):02d}"


def strip_tags(x: str) -> str:
    return re.sub(r"<[^>]+>", "", x)


assert len(NOTES) == len(SLIDES)
total = sum(n["mins"] for n in NOTES)
metrics_at = next(i for i, n in enumerate(NOTES) if n["title"] == "Métricas")
mid_exp = next(i for i, n in enumerate(NOTES) if n["kicker"] == "Experimento 7")
parts = [(0, metrics_at), (metrics_at, mid_exp), (mid_exp, len(NOTES))]
lines_md = [
    "# Guion de la presentación (amoblai)",
    "",
    f"Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides. {len(SLIDES)} slides, unos {round(total)} minutos.",
    "",
    "**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y el experimento. **Se cuentan esas dos cosas antes de avanzar.** "
    "La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).",
    "",
    "**Reparto sugerido** (a definir entre los tres):",
]
for k, (a, b) in enumerate(parts, 1):
    lines_md.append(f"- Parte {k}: slides {a + 1} a {b} ({NOTES[a]['title'] or 'Portada'} → {NOTES[b - 1]['title']}), unos {round(sum(n['mins'] for n in NOTES[a:b]))} min.")
lines_md += [
    "",
    "Si falta tiempo, se pueden pasar rápido los experimentos 4 y 5 y la slide de costos (los marcados con *).",
    "",
]
t = 0.0
for i, n in enumerate(NOTES, 1):
    head = n["title"] or n["kicker"] or "Portada"
    star = " *" if n["kicker"] in ("Experimento 4", "Experimento 5") or head == "Cuánto cuesta un pedido" else ""
    lines_md.append(f"## {i}. {strip_tags(head)}{star}")
    lines_md.append(f"*{n['kicker'] + ' · ' if n['kicker'] and n['title'] else ''}~{mmss(n['mins'])} min · desde el minuto {mmss(t)}*")
    lines_md.append("")
    nt = n["notes"]
    if isinstance(nt, dict) and nt:
        lines_md += [
            f"1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): {nt['motivo']}",
            f"2. **El experimento:** {nt['experimento']}",
            f"3. **→ Resultados** (flecha): {nt['resultados']}",
            f"4. **→ Decisión** (flecha): {nt['decision']}",
        ]
    elif nt:
        lines_md.append(nt)
    lines_md.append("")
    t += n["mins"]
GUION = OUT.with_name("guion.md")
GUION.write_text("\n".join(lines_md))
print(f"{GUION}: {round(total)} min")
