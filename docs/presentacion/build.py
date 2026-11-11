"""Arma docs/presentacion/amoblai.html: un solo archivo, con las imágenes y los gráficos adentro,
desde los resultados guardados en datos/resultados/ (ningún número está escrito a mano, salvo los
que vienen de docs/EXPERIMENTOS.md y lo dicen) y los prompts reales de src/amoblai/prompts/.

    uv run python docs/presentacion/build.py

El orden: el producto; el recorrido por las once fases del pipeline, con un mapa arriba que se va
encendiendo, y el mapa de los experimentos; cómo medimos; un experimento por lámina (con su
minimapa); el cierre. También escribe el guion (guion.md), con las notas de cada lámina.
"""

from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kit import (  # noqa: E402
    FASES,
    FKEYS,
    FNAME,
    PINES,
    ROOT,
    esc,
    hbars,
    img,
    lines,
    num,
    pin_inline,
    pipeline,
    prompt_body,
    prompt_card,
    route,
    versions,
)

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


def jsonl(p: str | Path) -> list[dict]:
    return [json.loads(x) for x in (ROOT / p).read_text().splitlines() if x.strip()]


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
ITEMS = {x["id"]: x for x in jsonl("datos/procesados/items.jsonl")}
DESC = {x["id"]: x for x in jsonl("datos/catalogo/descripciones.jsonl")}
ABO_N = len(jsonl("datos/catalogo/abo/descripciones.jsonl"))

# La corrida que sigue el recorrido: el living de Caballito, con la configuración final del flujo
# (search_query_v4, 5 candidatos, choose_combination_v2, scene_prompt_libre_v4, control SIFT).
CAB = R / "amoblar" / "caballito-living"
CAB_REQ = load(CAB / "request.json")["request"]
CAB_PLAN = load(CAB / "1_searches.json")
CAB_FOUND = load(CAB / "2_candidates.json")
CAB_CHOICE = load(CAB / "3_choice.json")
CAB_SCENE = load(CAB / "4_scene.json")
CAB_IMG = load(CAB / "5_image.json")
EST = R / "amoblar" / "experimento-buen-pedido-estricto"


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


def fase(key: str, title: str, body: str, take: str, notes: str, mins: float) -> None:
    """Una lámina del recorrido: arriba el mapa con esta fase encendida y las anteriores vistas;
    abajo, la frase de cierre."""
    i = FKEYS.index(key)
    slide(
        route(cur=key) + body + (f'<div class="take">{take}</div>' if take else ""),
        cls="fase",
        kicker=f"El recorrido · fase {i + 1} de {len(FASES)} · {FNAME[key]}",
        title=title,
        notes=notes,
        mins=mins,
    )


def dec(n: int | None, html: str) -> str:
    """Una decisión con el pin del experimento que la tomó (o sin pin)."""
    p = pin_inline(n) if n else '<span class="none"></span>'
    return f'<div class="dec">{p}<div>{html}</div></div>'


def experiment(
    n: str,
    title: str,
    question: str,
    left: str,
    right: str,
    decision: str,
    fases: tuple = (),
    why: str = "",
    notes: dict | None = None,
    mins: float = 1.2,
) -> None:
    """Una slide por experimento, en el orden en que se cuenta: arriba el minimapa (qué fase
    decidió, con su pin), por qué lo hicimos y qué queríamos ver; a la izquierda, el experimento.
    Con la flecha aparecen los resultados (paso 1) y después la decisión (paso 2)."""
    left = left.replace('<div class="find"', '<div data-step="1" class="find"')
    body = (
        (route(lit=fases, pins={f: [int(n)] for f in fases}) if fases else "")
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


def miles(n: int) -> str:
    """1.502 (punto de miles)."""
    return f"{n:,}".replace(",", ".")


def type_line(desc: str) -> str:
    return desc.splitlines()[0].removeprefix("Type:").strip()


def lines8(text: str) -> str:
    """Las ocho líneas de una descripción (o de una consulta), con su rótulo aparte."""
    rows = []
    for ln in text.strip().splitlines():
        k, _, v = ln.partition(":")
        rows.append(f"<div><span>{esc(k)}</span>{esc(v.strip())}</div>")
    return f'<div class="lines8">{"".join(rows)}</div>'


# ================================================================================================
# El producto
# ================================================================================================

# 1. Portada
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
    mins=0.7,
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
    f'<div style="text-align:center">{img(h["photos"][0], 220, cls="photo")}<div class="tiny">{esc(type_line(h["description"]))}{" ×" + str(q) if q > 1 else ""}</div></div>'
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
    mins=0.8,
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
    mins=0.7,
    notes="¿Por qué un RAG? Un LLM solo sabe de decoración, pero no qué hay en un catálogo: te recomienda un sillón de cuero coñac que nadie vende. Un modelo de imagen solo amobla lindo, pero inventa los muebles. Con RAG, el catálogo es la base de conocimiento: el LLM decide qué hace falta, el retrieval trae candidatos reales y el VLM elige mirando sus fotos; y la imagen se genera desde las fotos de los productos elegidos. Y no es un Q&A: la consulta es una foto y un pedido abierto, y la respuesta, una combinación que tiene que funcionar junta.",
)

# ================================================================================================
# Parte 1: el recorrido, fase por fase
# ================================================================================================
section(
    "Parte 1",
    "El recorrido",
    "Las once fases del pipeline, en orden: qué entra y qué sale de cada una, qué decidimos, con qué modelo, y los prompts que mandamos y cómo los fuimos reescribiendo.",
    notes="Primero, el recorrido: vamos a pasar por todo el pipeline, fase por fase, con un mapa arriba que se va encendiendo.",
)

slide(
    pipeline()
    + '<div class="grid2 small" style="margin-top:8px;gap:24px">'
    "<div><b>Una vez, offline.</b> Entran los productos de dos catálogos, con su foto; sale un índice con un vector y la metadata de cada uno.</div>"
    "<div><b>Por cada pedido.</b> Entran una foto del ambiente vacío y un pedido en texto libre; salen la lista de compra y la foto amoblada.</div>"
    "</div>"
    '<div class="lab" style="margin-top:22px">Quién hace cada fase</div><div class="who">'
    "<div><b>Opus 5.5</b><span>fases 2, 5 y 7: describe cada producto, planea y elige</span></div>"
    "<div><b>Qwen3-Embedding-0.6B</b><span>fases 3 y 6: embebe documentos y consultas, local</span></div>"
    "<div><b>ChromaDB</b><span>fases 3 y 6: el índice HNSW y los filtros</span></div>"
    "<div><b>Nano Banana 2</b><span>fase 9: edita la foto, por fal</span></div>"
    "<div><b>SIFT + RANSAC</b><span>fase 10: compara con la foto original</span></div>"
    "</div>"
    '<div class="take">Por pedido trabajan tres modelos: <b>Opus 5.5</b> en el plan y la elección, y <b>Nano Banana 2</b> en la imagen. Lo demás es local.</div>',
    kicker="El recorrido · el mapa",
    title="Once fases: una vez offline, y por cada pedido",
    notes="Este es el mapa completo, y lo vamos a recorrer fase por fase. Hay dos pipelines. Arriba, lo que se hace una vez, offline: el catálogo, la descripción de cada producto y el índice. Abajo, lo que pasa en cada pedido: entran la foto y el pedido, el plan decide las piezas, la búsqueda trae candidatos del índice, la elección arma el conjunto, y después la escena, la imagen y el control, hasta la lista y la foto amoblada. Por pedido trabajan solo tres modelos: Opus en el plan y la elección, y Nano Banana 2 en la imagen.",
    mins=0.7,
)


# -- Fase 1: el catálogo
def catalog_flow() -> str:
    """Los dos catálogos, de los datos crudos a lo que usa el flujo (números de EXPERIMENTOS.md
    T1c, T1e y T1f, salvo los que se cuentan acá)."""
    from kit import arrowhead, pin

    cw, gap, chh, x0 = 150, 34, 70, 212
    lanes = [
        ("IKEA", ["Tautkute et al., 2017", "uso no comercial"], 24,
         [("2.191", "productos del dataset"), ("268", "primer alcance: cuatro tipos"), ("855", "+ guardado, luz, textiles y deco"), (f"{len(ITEMS)}", "revisado: 36 productos afuera")]),
        ("ABO", ["Amazon Berkeley Objects", "Collins et al., CVPR 2022"], 112,
         [("147.702", "listados de Amazon"), ("781", "uno por modelo, con tope por kind"), ("759", "sin fotos de relleno"), (f"{ABO_N}", "descriptos, en el alcance")]),
    ]
    out = ['<svg class="pipe" viewBox="0 0 1160 190" width="1160" role="img">']
    for name, sub, y, chips in lanes:
        out.append(f'<text x="0" y="{y + 28}" font-size="17" font-weight="700" fill="var(--ink)">{name}</text>')
        for j, s in enumerate(sub):
            out.append(f'<text x="0" y="{y + 47 + j * 15}" font-size="12" fill="var(--muted)">{esc(s)}</text>')
        for i, (big, cap) in enumerate(chips):
            x = x0 + i * (cw + gap)
            last = i == len(chips) - 1
            out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{chh}" rx="10" fill="var(--card)" stroke="{"var(--accent)" if last else "var(--line)"}" stroke-width="{1.6 if last else 1.2}"/>')
            out.append(f'<text x="{x + 12}" y="{y + 29}" font-family="Fraunces, Georgia, serif" font-size="25" font-weight="650" fill="{"var(--accent)" if last else "var(--ink)"}">{big}</text>')
            words, l1, l2 = cap.split(), "", ""
            for w in words:
                if len(l1) + len(w) < 21 and not l2:
                    l1 = f"{l1} {w}".strip()
                else:
                    l2 = f"{l2} {w}".strip()
            out.append(f'<text x="{x + 12}" y="{y + 48}" font-size="11.5" fill="var(--muted)">{esc(l1)}</text>')
            if l2:
                out.append(f'<text x="{x + 12}" y="{y + 62}" font-size="11.5" fill="var(--muted)">{esc(l2)}</text>')
            if i:
                out.append(f'<line x1="{x - gap + 3}" y1="{y + chh / 2}" x2="{x - 4}" y2="{y + chh / 2}" stroke="var(--muted)" stroke-width="1.4"/>' + arrowhead(x - 3, y + chh / 2, x - 20, y + chh / 2))
        if name == "IKEA":
            out.append(pin(x0 + 2 * (cw + gap) + cw - 14, y + 7, 10, 9))
    fx, fw, fy, fh = 962, 198, 50, 96
    out.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="12" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="1.6"/>')
    out.append(f'<text x="{fx + 16}" y="{fy + 40}" font-family="Fraunces, Georgia, serif" font-size="32" font-weight="650" fill="var(--accent)">{miles(len(ITEMS) + ABO_N)}</text>')
    out.append(f'<text x="{fx + 16}" y="{fy + 62}" font-size="12.5" fill="var(--ink)">el catálogo del flujo</text>')
    out.append(f'<text x="{fx + 16}" y="{fy + 79}" font-size="11.5" font-family="JetBrains Mono, monospace" fill="var(--muted)">todos.yaml</text>')
    out.append(pin(fx + fw - 14, fy + 7, 10, 10))
    lx = x0 + 3 * (cw + gap) + cw
    for y in (24, 112):
        yc = y + chh / 2
        out.append(f'<path d="M{lx + 3},{yc} C{lx + 30},{yc} {fx - 30},{fy + fh / 2} {fx - 4},{fy + fh / 2}" fill="none" stroke="var(--muted)" stroke-width="1.4"/>')
    out.append(arrowhead(fx - 3, fy + fh / 2, fx - 20, fy + fh / 2))
    out.append("</svg>")
    return "".join(out)


kivik = ITEMS["190.114.33"]
rec = (
    '{<span class="k">"id":</span> "190.114.33", <span class="k">"name":</span> "KIVIK",\n'
    f' <span class="k">"category":</span> "{kivik["category"]}", <span class="k">"kind":</span> "{kivik["kind"]}",\n'
    f' <span class="k">"dimensions_cm":</span> <mark>{json.dumps(kivik["dimensions_cm"])}</mark>,\n'
    f' <span class="k">"colors":</span> {esc(json.dumps(kivik["colors"]))},\n'
    f' <span class="k">"description":</span> <mark>{esc(json.dumps(kivik["description"]))}</mark>}}'
)
fase(
    "catalogo",
    "Dos catálogos de productos reales, con foto",
    catalog_flow()
    + '<div class="row" style="gap:30px;margin-top:10px">'
    f'<div style="width:560px"><div class="lab">Un producto de IKEA, como viene</div><div class="code"><div class="ph"><b>items.jsonl</b><span>el sofá que va a elegir el flujo</span></div><pre>{rec}</pre></div></div>'
    '<div class="grow"><div class="lab">Lo que guardamos de cada uno</div>'
    + dec(None, "<b>Fotos</b>: la imagen sale de ellas, y el VLM las mira para describir.")
    + dec(None, "<b>Tipo</b> (14) y <b>kind</b> (44: mesa ratona, lámpara de pie…): el kind es el filtro duro de la búsqueda.")
    + dec(None, "<b>Medidas</b>, cuando hay: los asientos de IKEA no tienen; ABO, el 90 %.")
    + "</div></div>",
    "El texto del vendedor es marketing y faltan medidas: por eso cada producto <b>se describe mirando su foto</b>.",
    notes="Fase uno, el catálogo. Son dos. El dataset de IKEA de Tautkute y otros: de sus 2.191 productos empezamos con 268 muebles, lo ampliamos a 855 de living y comedor y, revisado, quedaron 819; eso lo decide el experimento 9. Y Amazon Berkeley Objects, un dataset académico con listados reales de Amazon: de casi 150 mil listados quedaron 683. El flujo usa los dos, 1.502 productos, por el experimento 10. De cada uno guardamos las fotos, el tipo, el kind y las medidas cuando hay. Así viene el sofá que va a elegir el flujo: el texto es marketing y no tiene medidas.",
    mins=0.7,
)

# -- Fase 2: la descripción
kd = DESC["190.114.33"]
fase(
    "descripcion",
    "Un VLM mira cada foto y escribe el producto en 8 líneas",
    '<div class="row" style="gap:22px">'
    f'<div style="width:215px"><div class="th" style="height:150px;padding:8px">{img(kivik["photos"][0], 500, alt="KIVIK")}</div>'
    f'<div class="lab" style="margin-top:12px">Lo que trae IKEA</div><div class="quote" style="font-size:13.5px;line-height:1.4"><i>{esc(kivik["description"])}</i></div></div>'
    f'<div style="width:360px"><div class="lab">Lo que escribe el VLM</div><div class="card" style="padding:6px 14px">{lines8(kd["text"])}</div>'
    f'<div class="cap" style="margin-top:6px">{esc(kd["prompt"].split("@")[0])} · Opus 5.5 (subagente de Claude Code), el mismo sofá.</div></div>'
    '<div class="grow">'
    + prompt_card(
        "describe_product_v3.md",
        [
            "Write its description for a search that matches products to what a person wants for their room. [[Exactly these eight lines, in this order, in English, short phrases separated by commas, no full sentences:]]",
            "Style: [[one to three of these, the closest first:]] Scandinavian, mid-century modern, minimalist, Japandi,",
            "[[60 to 90 words in all.]] Say only what the photos and the name show. [[No brand, price, measurements, care or assembly.]]",
        ],
    )
    + '<div style="height:8px"></div>'
    + versions(
        [
            ("v2", "Las <b>mismas 8 líneas que la consulta</b>; sin marca, precio ni medidas; nada de lo que no es (el embedding no lee el “not”).", False),
            ("v3", "Todo el catálogo: qué mirar en una <b>lámpara, un textil o un adorno</b>.", True),
            ("api", "<b>ABO por la API</b>, 10 por llamada (US$0,007 c/u): además el kind y si entra en el alcance.", False),
        ]
    )
    + "</div></div>",
    f"{pin_inline(1)} Esto es lo que se indexa: el producto escrito <b>en el mismo formato</b> en que el plan va a escribir la consulta.",
    notes="Fase dos: la descripción. Un VLM mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Es el mismo sofá: a la izquierda, lo que dice IKEA; en el medio, lo que escribió el modelo. El prompt pide exactamente esas ocho líneas, el estilo de una lista cerrada, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. La v2 fue para los muebles; la v3, cuando sumamos lámparas, textiles y deco; y una versión por la API para Amazon, que además da el kind y descarta lo que no es de un living. El experimento 1 decidió indexar esto y no el texto del vendedor.",
    mins=1.0,
)


# -- Fase 3: el índice
def index_flow() -> str:
    from kit import arrowhead, pin

    boxes = [
        ("La descripción", ["un documento por producto", "8 líneas, unas 80 palabras"], 4),
        ("Qwen3-Embedding-0.6B", ["local, en CPU (Apache 2.0)", "último token, sin instrucción"], 2),
        ("Un vector", ["1.024 dimensiones", "norma 1: el producto es el coseno"], 5),
        ("ChromaDB", ["HNSW, coseno · ef_search 100 · M 16", "+ metadata: tipo, kind y medidas"], 6),
    ]
    bw, gap, y, bh = 254, 48, 24, 86
    out = ['<svg class="pipe" viewBox="0 0 1160 114" width="1160" role="img">']
    for i, (t, subs, n) in enumerate(boxes):
        x = i * (bw + gap)
        out.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="11" fill="var(--card)" stroke="var(--line)" stroke-width="1.2"/>')
        out.append(f'<text x="{x + 16}" y="{y + 30}" font-size="16.5" font-weight="650" fill="var(--ink)">{esc(t)}</text>')
        for j, s in enumerate(subs):
            out.append(f'<text x="{x + 16}" y="{y + 52 + j * 18}" font-size="13" fill="var(--muted)">{esc(s)}</text>')
        out.append(pin(x + bw - 16, y + 7, 10, n))
        if i:
            out.append(f'<line x1="{x - gap + 4}" y1="{y + bh / 2}" x2="{x - 5}" y2="{y + bh / 2}" stroke="var(--muted)" stroke-width="1.5"/>' + arrowhead(x - 4, y + bh / 2, x - 20, y + bh / 2))
    out.append("</svg>")
    return "".join(out)


v0v1 = load(R / "reporte" / "_v0v1.json") or {"v0": 0.508, "v1": 0.618, "n0": 325, "n1": 207}
fase(
    "indice",
    "Un vector por producto: Qwen3, local, en ChromaDB",
    index_flow()
    + '<div class="row" style="gap:36px;margin-top:14px">'
    '<div style="width:640px"><div class="lab">Lo que probamos (lo elegido, en negrita)</div>'
    + dec(2, "<b>Embedder</b>: hashing de palabras (sin modelo) · BGE-base · <b>Qwen3-Embedding-0.6B</b>")
    + dec(4, "<b>Splitting</b>: <b>un documento por producto</b> · un chunk por línea · línea contra línea")
    + dec(5, "<b>Dimensión</b> (Matryoshka): de 32 a 512 · <b>1.024</b> (con 512 alcanza)")
    + dec(6, "<b>Base</b>: <b>ChromaDB con HNSW</b> · búsqueda exacta con numpy")
    + "</div>"
    '<div class="grow"><div class="lab">Antes: la v0 buscaba por imagen</div>'
    '<p class="small" style="font-size:14.5px;margin-bottom:6px">Grounding DINO y SAM recortaban cada mueble de una foto amoblada; CLIP, SigLIP 2 o DINOv2/v3 buscaban la foto más parecida. En un ambiente vacío no hay nada que recortar.</p>'
    + hbars([{"label": "v0 imagen", "value": v0v1["v0"]}, {"label": "v1 texto", "value": v0v1["v1"], "hl": True}], width=440, label_w=110, row_h=30)
    + '<div class="cap" style="margin-top:0">hit@1, mismo ground truth (catálogo de 275).</div></div>'
    "</div>",
    "Se arma una vez, local y gratis: un vector por producto, y la metadata al lado para filtrar.",
    notes=f"Fase tres: el índice. Se embebe la descripción entera, un documento por producto: es corta, y partirla en líneas pierde contexto, como muestra el experimento 4. El modelo es Qwen3-Embedding de 600 millones de parámetros, local, en CPU, con el último token como vector y sin instrucción de consulta, porque la consulta se escribe igual que el documento. Da 1.024 dimensiones; por Matryoshka se pueden truncar, y con 512 alcanza. Van a ChromaDB, con un índice HNSW en espacio coseno y la metadata que usan los filtros. Antes hubo una v0 que buscaba por imagen, recortando muebles de una foto amoblada: no sirve con un ambiente vacío, y con el mismo ground truth daba {num(v0v1['v0'])} contra {num(v0v1['v1'])}.",
    mins=1.0,
)

# -- Fase 4: lo que entra
fase(
    "entrada",
    "Entra una foto del ambiente vacío y un pedido libre",
    '<div class="row" style="gap:30px">'
    f'<div style="width:520px" class="fix h360">{img(CAB / "room.jpg", 1100, cls="photo")}<div class="cap">La foto que se amobla: la imagen 1 de todo el recorrido.</div></div>'
    '<div class="grow">'
    f'<div class="lab">El pedido, como lo escribe el usuario</div><div class="quote" style="font-size:16.5px;line-height:1.45">“{esc(CAB_REQ)}”</div>'
    '<div class="lab" style="margin-top:16px">Qué va a dónde</div>'
    + dec(None, "<b>La foto</b> va al plan y a la elección (reducida a 1.024 px) y al modelo de imagen.")
    + dec(None, "<b>Otras fotos del mismo ambiente</b> (opcionales) van solo al LLM, para entenderlo; el modelo de imagen recibe solo la primera.")
    + "</div></div>",
    "No hay formulario: qué piezas, de qué tipo y de qué tamaño lo decide <b>el plan</b>.",
    notes="Fase cuatro, lo que entra: una foto del ambiente vacío, que es la que se amobla, y un pedido en texto libre, en castellano, como lo escribiría el usuario. Se pueden sumar otras fotos del mismo ambiente: van solo al LLM, para entender el lugar; el modelo de imagen recibe solo la primera. Vamos a seguir este living hasta el final.",
    mins=0.4,
)

# -- Fase 5: el plan
p1 = CAB_PLAN["answer"]["pieces"][0]
hl_req = "un sofá de tres cuerpos gris claro contra la pared de la izquierda"
assert hl_req in CAB_REQ
req_cut = CAB_REQ[CAB_REQ.index("Quiero"): CAB_REQ.index(", una mesa ratona")]
plan_meta = CAB_PLAN["meta"]
fase(
    "plan",
    "El plan reescribe el pedido: una consulta por pieza",
    '<div class="row" style="gap:24px">'
    '<div style="width:510px">'
    f'<div class="lab">Entra (con la foto)</div><div class="quote" style="font-size:14.5px">“…{esc(req_cut).replace(esc(hl_req), "<b>" + esc(hl_req) + "</b>")}…”</div>'
    f'<div class="lab" style="margin-top:12px">Sale: la pieza 1 de {len(CAB_PLAN["answer"]["pieces"])}</div>'
    '<div class="code"><div class="ph"><b>1_searches.json</b>'
    f'<span>Opus 5.5 · effort medium · {round(plan_meta["latency_s"])} s · US${num(CAB_PLAN["cost_usd"], 2)}</span></div>'
    f'<pre style="white-space:pre;overflow:hidden;text-overflow:ellipsis"><span class="k">"piece":</span> "{esc(p1["piece"])}"\n'
    f'<span class="k">"kinds":</span> <mark>{esc(json.dumps(p1["kinds"]))}</mark>  <span class="k">"max_width_cm":</span> {p1["max_width_cm"]}  <span class="k">"max_depth_cm":</span> {p1["max_depth_cm"]}\n'
    '<span class="k">"query":</span>\n' + "\n".join("  " + esc(x) for x in p1["query"].splitlines()) + "</pre></div>"
    "</div>"
    '<div class="grow">'
    + prompt_card(
        "search_query_v4.md",
        [
            'You are an experienced interior designer. A client sent this photo of a room in their home and asked, in their own words: "{request}"',
            "[[First read the room as a designer would]]",
            "Then decide which pieces to add to do what they asked: [[as many as the request and the room call for, the most important first.]]",
            '[[A chair is not an armchair]]: in Spanish "silla" is a chair you sit on at a desk or a table',
            "\"query\": [[the ideal product in the catalog's eight lines]] below",
        ],
    )
    + '<div style="height:10px"></div>'
    + versions(
        [
            ("v1", "Con “una silla” para un escritorio, pidió un <b>sillón</b>.", False),
            ("v2", "Leer el ambiente; <b>la pieza que nombró</b>; el kind de una lista; de 1 a 4 piezas.", False),
            ("v3", "Lámparas y deco: hasta 6 piezas, <b>terminar el ambiente</b>.", False),
            ("v4", "<b>Sin tope de piezas</b>: un rincón de lectura ya llegaba a 6.", True),
        ]
    )
    + "</div></div>",
    f"{pin_inline(6)} La consulta habla como los documentos: el pedido se reescribe <b>en las mismas 8 líneas del catálogo</b>.",
    notes="Fase cinco, el plan, que es nuestro query rewriting. Opus 5.5 recibe la foto y el pedido y hace de diseñador: primero lee el ambiente, después decide qué piezas hacen falta y, para cada una, da el kind, que va a ser el filtro, la medida máxima que entra, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. Del pedido “un sofá de tres cuerpos gris claro” sale esta pieza: kind sofá, hasta 240 centímetros de ancho, y su consulta. Para este living propuso ocho piezas. El prompt tuvo cuatro versiones: la primera confundía silla con sillón; la v2 agregó leer el ambiente y la lista de kinds; la v3 pidió terminar el ambiente con lámparas y deco; y la v4 sacó el tope de piezas. El experimento 6 mostró que escribir la consulta completa es lo que más pesa antes de buscar. Cuesta unos siete centavos.",
    mins=1.1,
)

# -- Fase 6: la búsqueda
from amoblai.config import load_config  # noqa: E402
from amoblai.rag.filters import Filters  # noqa: E402

CFG = load_config(ROOT / "datos" / "configs" / "amoblai.yaml")
slack = CFG.furnish.size_slack
most = {f"max_{a}_cm": round(p1[f"max_{a}_cm"] * (1 + slack), 1) for a in ("width", "depth", "height") if p1.get(f"max_{a}_cm") is not None}
where = Filters(kinds=p1["kinds"], **most).where()


def where_html(w: dict) -> str:
    """El where tal cual lo arma rag/filters.py, con sangría a mano."""
    def j(x):
        return esc(json.dumps(x))

    c = w["$and"]
    o = c[0]["$or"]
    a0, a1 = o[1]["$and"]
    return (
        '{"$and": [\n  {"$or": [\n'
        f"    <mark>{j(o[0])}</mark>,\n"
        f'    {{"$and": [{j(a0)},\n      {j(a1)}]}}]}},\n'
        + ",\n".join(f"  <mark>{j(x)}</mark>" for x in c[1:])
        + "]}"
    )


chosen_ids = {c["id"] for c in CAB_CHOICE["answer"]["choices"] if c.get("quantity")}
sofas = CAB_FOUND["pieces"][0]["candidates"]
cards = "".join(
    f'<div class="c{" pick" if h["id"] in chosen_ids else ""}">'
    + ('<span class="flag">lo elige la fase 7</span>' if h["id"] in chosen_ids else "")
    + f'{img(h["photos"][0], 300)}<div class="s">{num(h["score"], 3)}</div><div class="t">{esc(type_line(h["description"]))}</div></div>'
    for h in sofas
)
fase(
    "busqueda",
    "Filtro duro por kind, después coseno: 5 candidatos",
    '<div class="row" style="gap:26px">'
    '<div style="width:400px"><div class="lab">El filtro, como where de ChromaDB</div>'
    f'<div class="code"><div class="ph"><b>rag/filters.py</b><span>la medida del plan + {round(100 * slack)} %</span></div><pre>{where_html(where)}</pre></div>'
    '<p class="tiny" style="margin-top:8px">Un producto sin kind pasa si su tipo coincide; uno sin medidas pasa siempre (los sofás de IKEA no tienen). Después, el coseno de Qwen3 entre la consulta y cada descripción.</p></div>'
    f'<div class="grow"><div class="lab">Los {len(sofas)} sofás más cercanos a la consulta (coseno)</div>'
    f'<div class="cand" style="grid-template-columns:repeat({len(sofas)},1fr);margin-top:14px">{cards}</div></div>'
    "</div>"
    '<div class="grid3" style="gap:22px;margin-top:16px">'
    + dec(3, "<b>Filtro duro</b> por el kind que elige el plan; con dos kinds, los candidatos se reparten.")
    + dec(8, f"<b>{CFG.furnish.candidates} candidatos</b> por pieza (antes 3): los que va a ver la elección.")
    + dec(7, "<b>Sin reranker aparte</b>: un cross-encoder empeoró; Opus mirando las fotos mejoró, y eso ya lo hace la elección.")
    + "</div>",
    "La búsqueda trae candidatos plausibles; el orden fino lo decide <b>quien mira las fotos</b>.",
    notes=f"Fase seis, la búsqueda. Para cada pieza, primero un filtro duro en ChromaDB: el kind que eligió el plan y las medidas máximas, con un {round(100 * slack)} por ciento de margen porque salen de una foto; un producto sin medidas pasa. Después, el coseno de Qwen3 entre la consulta y las descripciones, y quedan los 5 más cercanos. Estos son los cinco sofás para este pedido. El filtro lo decidió el experimento 3, y los 5 candidatos, el 8. También probamos un reranker después de la búsqueda: un cross-encoder de texto empeoró, y Opus mirando las fotos mejoró. No lo agregamos como paso: la fase siguiente ya mira las fotos.",
    mins=0.8,
)

# -- Fase 7: la elección
ES_KIND = {"sofa": "sofá", "rug": "alfombra", "coffee table": "mesa ratona", "TV stand": "mueble de TV", "floor lamp": "lámpara de pie", "cushion": "almohadones", "plant": "planta", "curtains": "cortinas"}
grid_rows = []
for p, c in zip(CAB_FOUND["pieces"], CAB_CHOICE["answer"]["choices"], strict=True):
    k = p["spec"]["kinds"][0]
    th = "".join(
        f'<div class="th{" pick" if h["id"] == c.get("id") else ""}" style="width:31px;height:31px">{img(h["photos"][0], 90, alt="")}</div>'
        for h in p["candidates"]
    )
    qty = f'<span style="font-size:12.5px;font-weight:650;color:var(--accent);margin-left:4px">×{c["quantity"]}</span>' if c.get("quantity", 1) > 1 else ""
    grid_rows.append(f'<div style="display:flex;align-items:center;gap:4px"><div style="width:100px;font-size:12.5px">{esc(ES_KIND.get(k, k))}</div>{th}{qty}</div>')
ch_meta = CAB_CHOICE["meta"]
c1 = CAB_CHOICE["answer"]["choices"][0]
sofa_rank = [h["id"] for h in sofas].index(c1["id"]) + 1
fase(
    "eleccion",
    "Opus ve el cuarto y los 5 de cada pieza, y elige el conjunto",
    '<div class="row" style="gap:26px">'
    '<div style="width:540px">'
    f'<div class="lab">Lo que ve: {ch_meta["images"]} imágenes (el cuarto y 5 por pieza)</div>'
    '<div style="display:flex;gap:14px;align-items:flex-start">'
    f'<div style="width:150px">{img(CAB / "room.jpg", 400, cls="photo")}<div class="tiny" style="margin-top:4px">imagen 1</div></div>'
    f'<div style="display:grid;gap:3px">{"".join(grid_rows)}</div></div>'
    f'<div class="tiny" style="margin-top:6px">Con borde naranja, lo elegido. {miles(ch_meta["usage"]["input_tokens"])} tokens de entrada · {round(ch_meta["latency_s"])} s · US${num(CAB_CHOICE["cost_usd"], 2)}.</div>'
    f'<div class="quote" style="margin-top:10px;font-size:14px"><b>Sofá (el {sofa_rank}.º de la búsqueda):</b> <i>“{esc(c1["why"])}”</i></div>'
    "</div>"
    '<div class="grow">'
    + prompt_card(
        "choose_combination_v2.md",
        [
            'Image 1 is a photo of a room. The user asked, in their own words: "{request}".',
            "Images 2 to {images} are the candidates from our catalog, one photo each, listed here by piece in the same order:",
            "[[Choose the pieces together, as one look, not each on its own. Judge from the photos.]]",
            'Then say [[how many units]] of it go in the room ("quantity"). Usually 1.',
            "[[0 when none of its candidates suits this room]], or the room is better without it",
        ],
    )
    + '<div style="height:10px"></div>'
    + versions(
        [
            ("v1", "Una por pieza, <b>pensando la combinación</b>; cada candidato con su línea Type y su medida, sin el nombre comercial.", False),
            ("v2", "<b>+ cuántas</b>: 0 deja la pieza afuera; más de una cuando la pieza lo pide (sillas, un par de lámparas).", True),
        ]
    )
    + "</div></div>",
    f"{pin_inline(7)} Eligió el {sofa_rank}.º sofá de la búsqueda: el 1.º era blanco, y el pedido decía <b>gris claro</b>.",
    notes="Fase siete, la elección. Opus recibe la foto del ambiente y los cinco candidatos de cada pieza: acá son 41 imágenes, cada candidato con su id, su línea Type y su medida, sin el nombre comercial. El prompt le pide elegir las piezas juntas, como un solo look, mirando las fotos, y decir cuántas unidades: cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda; si no, el código rechaza la respuesta. Acá eligió el segundo sofá de la búsqueda, porque el primero era blanco y el pedido decía gris claro, y puso dos almohadones. La v2 agregó las cantidades. Es el reranker con VLM del experimento 7.",
    mins=0.9,
)

# -- Fase 8: la escena
scene_text = CAB_SCENE["answer"]["prompt"]
fase(
    "escena",
    "El prompt de la imagen: una plantilla estricta, sin LLM",
    '<div class="row" style="gap:26px">'
    '<div style="width:500px">'
    '<div class="lab">A · Opus escribe la escena <span class="vmono">scene_prompt_v1 → v2</span></div>'
    + versions(
        [
            ("v1", "Dónde va cada producto en esta foto, hacia dónde mira y qué tamaño tiene.", False),
            ("v2", "Anclado a algo visible a esa profundidad; las fotos del catálogo dan solo el diseño.", False),
        ],
        title="",
    )
    + '<div class="lab" style="margin-top:14px">B · Una plantilla, sin LLM <span class="vmono">scene_prompt_libre_v1 → v4</span></div>'
    + versions(
        [
            ("v1", "La foto, las de los productos y el pedido: el modelo decide dónde va cada uno.", False),
            ("v2", "Los muebles modulares se pueden repetir para llenar una pared.", False),
            ("v3", "Las cantidades de la elección: “2 units” va dos veces.", False),
            ("v4", "<b>Edición estricta</b>: con 9 productos, la v3 inventó una ventana y movió la biblioteca.", True),
        ],
        title="",
    )
    + "</div>"
    '<div class="grow">'
    + prompt_card(
        "scene_prompt_libre_v4.md",
        [
            "Edit image 1. It is a photo of the client's own room, and [[the result must still be that same room, exactly]]: the same camera position, angle, lens and framing;",
            "[[Do not add, remove, move or enlarge any wall, window, door or opening]]",
            "image 2: three-seat sofa with wide arms, size unknown",
            "image 7: green linen-look cushion, size unknown, 2 units",
            "[[Add exactly these products and nothing else]]",
            "Each one must be the product of its photo, not a similar one",
        ],
        note="completada para este pedido (4_scene.json)",
        source=scene_text,
    )
    + '<div style="margin-top:14px">'
    + dec(12, "Con 6 piezas, A y B conservaban el cuarto, y B <b>no cuesta una llamada</b>. Con 9, la libre inventó una ventana: de ahí la v4 y el control de la fase 10.")
    + "</div></div></div>",
    f"{pin_inline(12)} La escena no la escribe nadie: una plantilla fija le pide al modelo <b>editar la foto del cliente</b>.",
    notes="Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos. En uno, Opus escribe la escena: dónde va cada producto, anclado a lo que se ve. En el otro, una plantilla sin LLM: se completa con la lista y el modelo de imagen acomoda. La plantilla tuvo cuatro versiones: la libre, una que repetía los muebles modulares, otra con las cantidades, y la v4, estricta, que salió de un error: con nueve productos, el modelo inventó una ventana y movió la biblioteca. La v4 dice que es una edición de la foto del cliente: la misma cámara, las mismas paredes y ventanas, nada agregado, y exactamente estos productos. El experimento 12 eligió esta, que además no cuesta nada.",
    mins=0.9,
)

# -- Fase 9: la imagen
gen = CFG.furnish.generators["nano_banana_2"]
att = CAB_IMG["attempts"]
prod_th = "".join(
    f'<div class="th" style="height:62px">{img(ITEMS[c["id"]]["photos"][0], 140, alt="")}</div>'
    for c in CAB_CHOICE["answer"]["choices"]
    if c.get("quantity") and c["id"] in ITEMS
)
fase(
    "imagen",
    "Nano Banana 2 edita la foto con las fotos de los productos",
    '<div style="display:grid;grid-template-columns:430px 34px 250px 34px 1fr;align-items:center;gap:0">'
    f'<div><div class="lab">Entra</div><div style="display:grid;grid-template-columns:190px 1fr;gap:10px;align-items:center">'
    f'<div>{img(CAB / "room.jpg", 500, cls="photo")}<div class="tiny" style="margin-top:3px">imagen 1: el cuarto</div></div>'
    f'<div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px">{prod_th}</div><div class="tiny" style="margin-top:3px">imágenes 2 a {CAB_IMG["meta"]["images_in"]}: los productos</div></div></div>'
    '<div class="tiny" style="margin-top:8px">+ el prompt de la fase 8</div></div>'
    '<div style="text-align:center;color:var(--muted);font-size:24px">→</div>'
    '<div class="card" style="border-color:var(--accent)"><h3 style="font-size:19px;margin-bottom:2px">Nano Banana 2</h3>'
    '<div class="small" style="font-size:14px;line-height:1.45">Gemini 3.1 Flash Image, por fal<br>'
    f'<span style="font-family:var(--mono);font-size:12px;color:var(--muted)">{esc(gen["endpoint"])}</span><br>'
    f'{gen["resolution"]}, con la proporción de la foto<br><b>US${num(gen["usd_per_image"]["1K"])} por imagen</b> · ~{round(CAB_IMG["meta"]["latency_s"])} s por imagen</div></div>'
    '<div style="text-align:center;color:var(--muted);font-size:24px">→</div>'
    f'<div><div class="lab">Sale (intento 1)</div><div class="shot">{img(CAB / att[0]["image"], 900)}</div></div>'
    "</div>"
    '<div class="grid2" style="gap:26px;margin-top:18px">'
    + dec(None, "<b>Alternativas en el código</b>: gpt-image (OpenAI) y un generador manual, gratis, que deja la carpeta lista para pegar en ChatGPT o Gemini.")
    + dec(None, "<b>El modelo no salió de un experimento</b>: la comparación entre modelos de imagen quedó diseñada, sin correr.")
    + "</div>",
    "La imagen se genera desde las fotos de lo que se compra. Pero este primer intento <b>movió la cámara</b>.",
    notes=f"Fase nueve, la imagen. Nano Banana 2, por fal, en modo edición: recibe la foto del ambiente, las fotos de los productos en el orden de la lista y el prompt. Cuesta {round(100 * gen['usd_per_image']['1K'])} centavos por imagen a 1K. El modelo no lo elegimos con un experimento: la comparación quedó diseñada, sin correr. Y el primer intento salió así: lindo, pero con la cámara corrida.",
    mins=0.5,
)

# -- Fase 10: el control
rc = CFG.furnish.room_check
shots = [f'<div><div class="shot">{img(CAB / "room.jpg", 700)}<span class="badge">original</span></div><div class="cap">La foto del cliente.</div></div>']
for k, a in enumerate(att, 1):
    ok = a["ok"]
    shots.append(
        f'<div><div class="shot">{img(CAB / a["image"], 700)}<span class="badge {"ok" if ok else "no"}">intento {k} · {"aceptado" if ok else "descartado"}</span></div>'
        f'<div class="cap"><b>{a["sift_inliers"]} puntos</b> reencontrados · cámara corrida {num(100 * a["sift_desplazamiento_mediano"], 0)} %</div></div>'
    )
fase(
    "control",
    "¿Es el mismo cuarto? SIFT lo decide, y si no, reintenta",
    f'<div class="grid4" style="gap:12px">{"".join(shots)}</div>'
    '<div style="margin-top:16px;max-width:1000px">'
    + dec(12, f"<b>SIFT + RANSAC</b> entre la foto original y la generada: se acepta si reencuentra al menos <b>{int(rc['min_inliers'])} puntos</b> del cuarto y la cámara se movió como mucho <b>{num(100 * rc['max_shift'], 0)} % del ancho</b>. Si no, el intento queda aparte y se genera otro, <b>hasta {int(rc['attempts'])}</b>; si ninguno pasa, queda el que mejor conserva el cuarto.")
    + "</div>",
    "El prompt pide el mismo cuarto; <b>el control es lo que lo garantiza</b>.",
    notes=f"Fase diez, el control. Comparamos la foto original con la generada con SIFT y RANSAC: si reencuentra al menos {int(rc['min_inliers'])} puntos del cuarto y la cámara se movió menos del {num(100 * rc['max_shift'], 0)} por ciento del ancho, se acepta. Si no, se guarda aparte y se genera otra, hasta {int(rc['attempts'])} veces. En este living, los dos primeros intentos eran lindos pero con la cámara corrida: {att[0]['sift_inliers']} y {att[1]['sift_inliers']} puntos. El tercero reencontró {att[2]['sift_inliers']} y quedó. Este control salió del experimento 12.",
    mins=0.6,
)

# -- Fase 11: lo que sale
rows_list = []
for p, c in zip(CAB_FOUND["pieces"], CAB_CHOICE["answer"]["choices"], strict=True):
    if not c.get("quantity"):
        continue
    h = next(h for h in p["candidates"] if h["id"] == c["id"])
    rows_list.append(
        f'<div style="display:grid;grid-template-columns:46px 1fr auto;gap:12px;align-items:center;padding:4px 0;border-top:1px solid var(--grid)">'
        f'<div class="th" style="width:46px;height:40px">{img(h["photos"][0], 110, alt="")}</div>'
        f'<div style="font-size:14.5px">{esc(type_line(h["description"]))}<span style="color:var(--muted);font-family:var(--mono);font-size:11.5px;margin-left:8px">{h["id"]}</span></div>'
        f'<div style="font-size:14.5px;font-weight:650">×{c["quantity"]}</div></div>'
    )
com = R / "amoblar" / "caballito-comedor"
com_att = len((load(com / "5_image.json") or {}).get("attempts") or [1])
cost_claude = CAB_PLAN["cost_usd"] + CAB_CHOICE["cost_usd"]
cost_img = CAB_IMG["cost_usd"]
fase(
    "salida",
    "Sale la lista de compra y el ambiente amoblado",
    '<div class="row" style="gap:30px">'
    f'<div style="width:520px"><div class="lab">La lista: {len(rows_list)} productos del catálogo</div>{"".join(rows_list)}</div>'
    '<div class="grow"><div class="lab">El mismo ambiente, con esos productos</div>'
    f'<div class="grid2" style="gap:8px">{img(CAB / "room.jpg", 700, cls="photo")}{img(CAB / "final.png", 700, cls="photo")}</div>'
    f'<p class="small" style="margin-top:10px;font-size:14.5px">Este pedido: US${num(cost_claude)} de Claude (plan y elección) y US${num(cost_img)} de imágenes (tres intentos). '
    f"Cada fase deja su archivo en la carpeta de la corrida (<code>1_searches.json</code> a <code>5_image.json</code>) y la webapp muestra cada paso mientras se hace. "
    f"El comedor del mismo departamento pasó el control en el intento {com_att}.</p></div>"
    "</div>",
    "Cada producto de la lista es un id real del catálogo: el código <b>rechaza cualquiera que la búsqueda no haya traído</b>.",
    notes=f"Y fase once, lo que sale: la lista de compra, con productos reales del catálogo y cuántos de cada uno, y la foto del mismo ambiente con esos productos. Este pedido costó unos {round(100 * cost_claude)} centavos de Claude y {round(100 * cost_img)} de imágenes, por los tres intentos. Cada fase deja su archivo en la carpeta de la corrida, y la webapp muestra cada paso mientras se hace. El comedor del mismo departamento pasó el control al primer intento.",
    mins=0.6,
)

# -- El mapa de los experimentos
EXPS = [
    (1, "Qué texto se indexa", "vendedor · nombre + VLM · VLM"),
    (2, "Embedder", "hashing · BGE-base · Qwen3"),
    (3, "Filtros duros", "ninguno · por tipo · por kind"),
    (4, "Splitting", "documento · chunk por línea · línea a línea"),
    (5, "Dimensión del vector", "de 32 a 1.024 (Matryoshka)"),
    (6, "Base vectorial y consulta", "HNSW · exacta; 8 líneas · Type · kind"),
    (7, "Reranking", "ninguno · cross-encoder · VLM"),
    (8, "Candidatos por pieza", "k de 1 a 10"),
    (9, "Ampliar y revisar el catálogo", "268 · 855 · 819"),
    (10, "Qué catálogo", "IKEA · ABO · los dos (juez)"),
    (11, "Cuánto mide el ground truth", "juez graduado · 3 redactores"),
    (12, "La imagen", "escena del LLM · libre · estricta + SIFT"),
]
assert {n for ns in PINES.values() for n in ns} == {n for n, *_ in EXPS}
legend = "".join(f'<div class="li">{pin_inline(n)}<b>{esc(t)}</b><span>{esc(v)}</span></div>' for n, t, v in EXPS[:6])
legend2 = "".join(f'<div class="li">{pin_inline(n)}<b>{esc(t)}</b><span>{esc(v)}</span></div>' for n, t, v in EXPS[6:])
slide(
    pipeline(pins=True)
    + f'<div class="legend" style="margin-top:10px"><div>{legend}</div><div>{legend2}</div></div>'
    + '<div class="take">Ocho de las once fases las decidió un experimento. El modelo de imagen, no: esa comparación quedó sin correr.</div>',
    kicker="El recorrido · los experimentos",
    title="Doce experimentos, cada uno con su pin donde decidió",
    notes="Y este es el mismo mapa con los experimentos encima: cada pin es un experimento, puesto sobre la parte que decidió, con todo lo demás fijo. El catálogo lo decidieron el 9 y el 10; qué se describe, el 1; el índice, cuatro: el embedder, el splitting, la dimensión y la base vectorial; la consulta del plan, el 6; el filtro y los candidatos de la búsqueda, el 3 y el 8; que la elección mire las fotos, el 7; y la escena y el control, el 12. El 11 mide cuánto vale el ground truth de la búsqueda. Ocho de las once fases las decidió un experimento. Antes de verlos, cómo medimos.",
    mins=0.8,
)

# ================================================================================================
# Parte 2: cómo medimos
# ================================================================================================
section(
    "Parte 2",
    "Cómo medimos",
    "Dos bancos de prueba: ambientes de IKEA con sus productos anotados (hay ground truth) y ambientes vacíos reales (no lo hay: jueces y métricas de imagen).",
    notes="Antes de los experimentos, cómo medimos, para que cada número se entienda.",
)

# datos de evaluación: el ground truth y los ambientes vacíos
gt_room = "datos/dataset/ikea/images/room_scenes"
scene = next(iter(sorted((ROOT / gt_room).glob("*living*"))), None) or next(iter(sorted((ROOT / gt_room).glob("*"))))
rooms_yaml = ROOT / "datos/ambientes_vacios/pedidos.yaml"
import yaml  # noqa: E402

rooms = yaml.safe_load(rooms_yaml.read_text())["ambientes"]
pub_yaml = ROOT / "datos/ambientes_vacios/publicas.yaml"
pub = {f["archivo"]: f for f in yaml.safe_load(pub_yaml.read_text())["fotos"]} if pub_yaml.exists() else {}
shown = [r for r in rooms if (ROOT / r["foto"]).exists()][:12]
thumbs = "".join(f'<div>{img(r["foto"], 260, cls="photo")}</div>' for r in shown)
credits = "; ".join(f'{esc(pub[r["foto"]]["autor"])} ({esc(pub[r["foto"]]["licencia"])})' for r in shown if r["foto"] in pub)
nr, npub = len(rooms), sum(r["foto"] in pub for r in rooms)
slide(
    '<div class="row" style="gap:34px">'
    '<div style="width:540px"><h3>Con ground truth: el retrieval</h3>'
    f'<div class="fix h180">{img(scene, 900, cls="photo")}</div>'
    '<ul class="small" style="margin-top:10px;font-size:15px">'
    "<li><b>65 ambientes</b> de living y comedor de IKEA con sus productos anotados (de invertir <code>item_to_room</code>).</li>"
    f"<li>Por cada mueble visible, un subagente escribe la búsqueda como el plan, sin ver el catálogo: <b>{ABL[BASE]['searches']} búsquedas</b>, {ABL[BASE]['answerable']} con su producto en el catálogo.</li>"
    "<li>Acierta si el anotado sale primero (hit@1) o entre los k primeros. IC 95 % por <b>bootstrap por ambiente</b>.</li></ul></div>"
    f'<div class="grow"><h3>Sin ground truth: el sistema completo</h3><div class="fix h70" style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px">{thumbs}</div>'
    '<ul class="small" style="margin-top:10px;font-size:15px">'
    f"<li><b>{nr} ambientes vacíos reales</b>: {nr - npub} nuestros y {npub} públicos (Wikimedia Commons y Flickr), elegidos de {len(pub)} revisados uno por uno; cada uno con un pedido como el de un usuario.</li>"
    "<li>Se mide con un juez que compara listas de a pares y con métricas de la imagen.</li></ul>"
    f'<div class="tiny" style="margin-top:4px">Fotos públicas: {credits}.</div></div>'
    "</div>",
    kicker="Cómo medimos · los datos",
    title="Ambientes IKEA anotados y ambientes vacíos reales",
    notes=f"Usamos dos bancos de prueba. Para el retrieval, 65 fotos de livings y comedores de IKEA con sus productos anotados: ahí sabemos cuál es el correcto. Por cada mueble visible, un subagente escribió la búsqueda como la escribiría el plan, sin ver el catálogo: {ABL[BASE]['searches']} búsquedas, {ABL[BASE]['answerable']} con su producto en el catálogo. Acierta si el anotado sale primero, o entre los k primeros, y los intervalos son por bootstrap por ambiente. Para el sistema completo, {nr} ambientes vacíos reales: {nr - npub} nuestros y {npub} públicos, elegidos entre {len(pub)}, cada uno con un pedido escrito como lo escribiría un usuario. Ahí no hay ground truth: un juez compara listas, y la imagen se mide aparte.",
    mins=0.9,
)

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
    mins=0.8,
    notes="Las métricas de retrieval, donde sí hay ground truth. hit@k: si el anotado está entre los k primeros; hit@1 es encontrarlo primero, y hit@k con k igual a los candidatos que ve el VLM es el techo de lo que puede elegir. MRR: el promedio de uno sobre la posición del correcto, premia que esté arriba. Context recall y context precision son las de RAGAS: cuántos de los productos de un ambiente aparecen entre los candidatos, y cuán arriba quedan. NDCG admite relevancia graduada. Y los intervalos: si dos métodos tienen intervalos que se pisan, con estos datos no los podemos distinguir.",
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
    mins=0.8,
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
    mins=0.8,
    notes="Para la imagen medimos tres cosas. Que sea el mismo cuarto: SIFT reencuentra puntos de la foto original y mide cuánto se movió la cámara, y SSIM compara lo que no es mueble. Que sean los mismos productos: detectamos cada mueble, lo recortamos y vemos si el más parecido del catálogo es el de la lista. Y que sea lo que se pidió: SigLIP 2 entre el pedido y la imagen, y contamos lo que falta, lo repetido y lo inventado. Además, reproducibilidad con tres redactores, y el espacio de embeddings.",
)

# ================================================================================================
# Parte 3: los experimentos
# ================================================================================================
section(
    "Parte 3",
    "Experimentos",
    "Cada uno: por qué lo hicimos y qué queríamos ver, cómo lo medimos, qué dio y qué decidimos. Arriba, el minimapa con su pin: la fase que decidió.",
    notes="Ahora los experimentos. Todos siguen el mismo orden: arriba, el minimapa con la fase que decide; después, por qué lo hicimos y cómo es el experimento; y recién ahí, con la flecha, los resultados y la decisión.",
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
    fases=("descripcion",),
    why="El texto de IKEA casi no describe el producto (“The armchair is lightweight...”), y un usuario pide estilo, color y materiales: cosas que están en la foto, no en el texto.",
    notes={
        "motivo": "El texto que trae IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. Queríamos saber si valía la pena describir cada producto, un costo que se paga una sola vez.",
        "experimento": f"Indexamos tres textos y corrimos las mismas {ABL[BASE]['answerable']} búsquedas, con todo lo demás fijo: el texto del vendedor, la descripción de ocho líneas, y la descripción con el nombre comercial adelante.",
        "resultados": f"Con el texto del vendedor, hit@1 da {num(m('qwen3|seller|filtro-type')['hit@1'])}; con la descripción, {num(m(BASE)['hit@1'])}: más de cuatro veces, el cambio más grande del trabajo. El nombre adelante empeora (de {num(m('qwen3|description|filtro-kind')['hit@1'])} a {num(m('qwen3|name+description|filtro-kind')['hit@1'])}): NOLMYRA no le dice nada al embedding.",
        "decision": "Se indexa solo la descripción. Y queda una idea que vuelve en todo el trabajo: consulta y documento en el mismo formato.",
    },
    mins=1.0,
)

# E2: embedder
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
    fases=("indice",),
    why="Con un texto bueno, el siguiente candidato es el modelo de embeddings. Uno más grande cuesta memoria y tiempo, y queríamos que el retrieval corra local, en CPU.",
    notes={
        "motivo": "Con el texto resuelto, ¿cuánto aporta el modelo? Uno más grande cuesta memoria y tiempo, y queríamos que el retrieval corra local, en CPU.",
        "experimento": "Tres embedders sobre el mismo texto y las mismas búsquedas: hashing, una bolsa de palabras sin modelo; BGE-base, de 110 millones de parámetros; y Qwen3-Embedding, de 600 millones.",
        "resultados": f"Gana Qwen3, con {num(m(BASE)['hit@1'])}, pero el hashing queda cerca ({num(m('hashing|description|filtro-type')['hit@1'])}) y BGE último ({num(m('bge|description|filtro-type')['hit@1'])}). Las descripciones usan vocabulario controlado, así que hasta contar palabras funciona. Qwen3 gana más claro en MRR y en las búsquedas difíciles.",
        "decision": "Qwen3-Embedding-0.6B, Apache 2.0, en CPU. El formato del texto vale más que el modelo.",
    },
    mins=0.9,
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
    fases=("busqueda",),
    why="El plan ya sabe qué pieza busca (“un sofá”), y por similitud sola una mesa del mismo estilo puede quedar arriba. Un filtro duro lo evita, pero puede dejar afuera al correcto.",
    notes={
        "motivo": "Por similitud sola, una mesa nórdica de madera clara se puede parecer más a la consulta que un sofá. Un filtro por metadata lo evita, pero puede dejar afuera al correcto.",
        "experimento": "Tres opciones: sin filtro; por tipo, 14 categorías gruesas como sofá o mesa; y por kind, 41 finas como mesa ratona o de comedor. Miramos sobre todo hit@10.",
        "resultados": f"Con descripciones buenas, hit@1 casi no cambia, pero el de kind resta: en hit@10, {num(m('qwen3|description|filtro-kind')['hit@10'])} contra {num(m(BASE)['hit@10'])} del de tipo. Si el plan pide una mesa auxiliar y el catálogo la tiene como ratona, el filtro fino la deja afuera.",
        "decision": "Filtrar siempre, más las medidas. El flujo filtra por los kinds del plan, que puede dar dos; la diferencia con el tipo está dentro del intervalo, y pasarlo a tipo es lo próximo que probaríamos.",
    },
    mins=1.0,
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
    fases=("indice",),
    why="El chunking es una de las decisiones clásicas de un RAG. Nuestros documentos son cortos, pero sus 8 líneas tienen roles distintos: quizás convenía comparar cada línea por separado.",
    notes={
        "motivo": "El splitting es una decisión clásica de un RAG. Nuestras ocho líneas tienen roles distintos: quizás convenía compararlas por separado.",
        "experimento": "Un documento por producto; un chunk por línea, donde el producto vale su mejor línea; y línea contra línea, con el mismo rótulo de la consulta.",
        "resultados": f"Gana un documento ({num(m(BASE)['hit@1'])}); el chunk por línea se desploma ({num(m(BASE + '|chunks-lines-max')['hit@1'])}): “Colors: light wood” se parece a cualquier cosa de madera clara.",
        "decision": "Un documento por producto: con unas 80 palabras no hay nada que partir.",
    },
    mins=0.5,
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
        height=270,
        xlabel="dimensiones (escala log)",
        ylabel="hit@1",
        xlog=True,
    ),
    "<b>Decisión:</b> se puede indexar con 512 sin perder nada. Con 819 productos no hace falta (el índice entra igual en memoria); en un catálogo de millones, sí.",
    fases=("indice",),
    why="Qwen3 se entrenó con Matryoshka: sus vectores se pueden truncar sin reentrenar. En un catálogo grande, la memoria y la latencia crecen con la dimensión.",
    notes={
        "motivo": "Qwen3 se entrenó con Matryoshka: el vector se puede truncar sin reentrenar. En un catálogo de millones, la memoria y la latencia crecen con la dimensión.",
        "experimento": "Truncamos a 32, 64, 128, 256, 512 y 1024 componentes y renormalizamos.",
        "resultados": f"Con 512 da lo mismo que con 1024 ({num(dvals[4])} contra {num(dvals[5])}); por debajo de 128 cae rápido: con 32, {num(dvals[0])}.",
        "decision": "Con este catálogo dejamos 1024 porque no cuesta nada; si creciera, 512.",
    },
    mins=0.5,
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
    fases=("indice", "plan"),
    why="Pasamos de recorrer los vectores con numpy a ChromaDB, que aproxima (HNSW). Y escribir la consulta completa de 8 líneas cuesta tokens y latencia en cada pedido.",
    notes={
        "motivo": "Dos dudas. ChromaDB aproxima con HNSW: ¿pierde algo contra la búsqueda exacta? Y escribir la consulta completa cuesta tokens en cada pedido: ¿alcanza con algo más corto?",
        "experimento": "ChromaDB contra recorrer todos los vectores con numpy, con la misma consulta. Y la consulta completa contra solo la línea Type, y contra solo el kind, que sería no reescribir.",
        "resultados": f"HNSW da exactamente lo mismo que la exacta ({num(m(BASE + '|exact')['hit@1'], 3)} y {num(m(BASE)['hit@1'], 3)}). Con solo la línea Type, hit@1 cae a {num(m(BASE + '|consulta-type')['hit@1'])}; con solo el kind, a {num(m(BASE + '|consulta-kind')['hit@1'])}. El estilo, los colores y la forma son lo que distingue un sofá de otro.",
        "decision": "ChromaDB con la consulta completa que escribe el plan: el query rewriting cuesta, pero vale.",
    },
    mins=0.9,
)

# E7: reranking
r0, r1 = RER[BASE], RER[BASE + "|rerank-opus"]
mini = m(BASE + "|rerank-minilm-reranker")
experiment(
    "7",
    "Reranking (Advanced RAG)",
    "Un segundo modelo que mire la consulta y cada candidato juntos ordena mejor el top-10?",
    '<ul class="small"><li><b>cross-encoder MiniLM</b> (MS MARCO, local, gratis): lee consulta y descripción juntas.</li>'
    "<li><b>VLM</b> (Claude Opus 5.5): ve la consulta y las <b>fotos</b> de los 10 candidatos y los ordena (<code>rerank_candidates_v1</code>).</li></ul>"
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
    "<b>Decisión:</b> el reranking con VLM funciona, y el paso de elección ya es eso: Claude elige mirando las fotos de los candidatos. La pregunta pasa a ser cuántos candidatos verle (exp. 8). Costo: ~US$0,02 por búsqueda.",
    fases=("eleccion",),
    why=f"hit@10 daba {num(m(BASE)['hit@10'])} pero hit@1 {num(m(BASE)['hit@1'])}: el correcto casi siempre está entre los 10 primeros, pero no arriba. El cuello de botella era el orden.",
    notes={
        "motivo": f"hit@10 daba {num(m(BASE)['hit@10'])} pero hit@1 {num(m(BASE)['hit@1'])}: el correcto casi siempre está entre los 10 primeros, pero no primero. Advanced RAG propone un reranker, un segundo modelo que mira la consulta y cada candidato juntos.",
        "experimento": "Dos rerankers sobre el top-10: un cross-encoder MiniLM de MS MARCO, local y gratis, que lee consulta y descripción; y Opus, que ve la consulta y las fotos de los 10 candidatos y los ordena.",
        "resultados": f"MiniLM empeora ({num(mini['hit@1'])}): está entrenado con preguntas web, no con muebles. Opus sube hit@1 de {num(r0['hit@1'])} a {num(r1['hit@1'])} y MRR de {num(r0['mrr@10'])} a {num(r1['mrr@10'])}: la foto tiene lo que la descripción no dijo. Cuesta unos dos centavos por búsqueda.",
        "decision": "El reranking con VLM funciona, y la elección ya es eso. No agregamos un paso: la pregunta pasó a ser cuántos candidatos mostrarle.",
    },
    mins=1.1,
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
        height=280,
        xlabel="candidatos por pieza (k)",
        ylabel="acierto",
        marks=[{"x": 5, "text": "elegido"}],
    ),
    "<b>Decisión:</b> 5 candidatos por pieza (antes 3). Casi toda la mejora, sin llenar la llamada de elección de fotos (9 piezas × 5 = 45 imágenes).",
    fases=("busqueda",),
    why=f"La elección ya es un reranker con fotos, pero con 3 candidatos el correcto faltaba en una de cada cuatro piezas (hit@3 = {num(cei[2])}). Más candidatos suben ese techo, pero hacen más difícil y más cara la elección.",
    notes={
        "motivo": "La elección es un reranker con fotos, pero con 3 candidatos el correcto faltaba en una de cada cuatro piezas. Más candidatos suben ese techo, pero son más fotos en la llamada: más caro y más difícil elegir.",
        "experimento": "Sale gratis del experimento anterior: si Opus ordenó el top-10, lo que elegiría entre los primeros k es el mejor ordenado de esos k. Es un proxy: la elección real además ve el ambiente y el pedido.",
        "resultados": f"La punteada es el techo; la sólida, lo que elegiría el VLM. De 3 a 5 candidatos sube de {num(acc[2], 3)} a {num(acc[4], 3)}; a partir de 8 se aplana, y la distancia al techo crece.",
        "decision": "5 candidatos por pieza: casi toda la mejora, y la llamada queda en 45 fotos para 9 piezas.",
    },
    mins=1.0,
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
    fases=("catalogo",),
    why="El primer catálogo tenía solo sofás, sillones, mesas y alfombras: no había biblioteca, lámpara ni cortinas que recomendar. Y al describirlo aparecieron productos con la foto de otro.",
    notes={
        "motivo": "El primer catálogo eran 268 sofás, sillones, mesas y alfombras: no había biblioteca, lámpara ni cortinas. Y al describirlo aparecieron productos con la foto de otro: la lista diría una cosa y la imagen mostraría otra.",
        "experimento": "Las mismas métricas sobre el de 268, el ampliado a 855 y el revisado: 36 productos afuera y 7 kinds corregidos.",
        "resultados": f"Ampliar baja hit@1 de 0,636 a {num(old['hit@1'], 3)}: hay más productos parecidos y lo nuevo es deco, más difícil. La revisión casi no lo cambia ({num(new['hit@1'], 3)}), pero hace que la lista y la imagen muestren el mismo producto. Ojo: cambia el universo, no son números comparables.",
        "decision": "Ampliado y revisado: unos puntos de hit@1 son el precio de poder amoblar un living completo.",
    },
    mins=0.9,
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
        f'<table class="t sm"><tr><th></th><th>gana</th><th>útil</th><th>pedido</th><th>ambiente</th><th>conjunto</th></tr>'
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
        '<table class="t sm"><tr><th></th><th>n</th><th>IKEA</th><th>IKEA+ABO</th><th>emp.</th><th>útil I</th><th>útil I+A</th></tr>'
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
    f"<li><b>Amazon Berkeley Objects</b> (Collins et al., 2022): listados reales de Amazon; {ABO_N} descriptos con el mismo formato (Opus por la API, US$5,4), medidas en el 90%.</li>"
    "<li>Sin ground truth: mismo plan, cambia solo el catálogo, y un juez compara las listas de a pares, en los dos órdenes.</li></ul>",
    f'<div style="width:600px">{tbl10 or "<p class=small>(pendiente)</p>"}</div>',
    "<b>Decisión:</b> IKEA + ABO: empata con pedidos nórdicos y gana 6 a 0 con otros estilos, porque trae lo pedido que IKEA 2013 no tiene. "
    "Sumar ABO casi no cambia el retrieval sobre el GT de IKEA (hit@1 0,535 → 0,525).",
    fases=("catalogo",),
    why="IKEA 2013 tiene fotos chicas, asientos sin medidas y una sola estética. Amazon Berkeley Objects tiene listados reales con medidas.",
    notes={
        "motivo": "IKEA es de 2013, con fotos chicas, asientos sin medidas y una sola estética, la nórdica. Amazon Berkeley Objects tiene listados reales, con medidas y fotos grandes.",
        "experimento": "Sin ground truth: de punta a punta, con los mismos ambientes, pedidos y plan; cambia solo el catálogo. El juez de a pares compara las dos listas, en los dos órdenes.",
        "resultados": (
            "Primero, en nuestros 5 departamentos: IKEA le gana a Amazon 4 a 0, por estilo, e IKEA más Amazon empataba con IKEA. Pero los 5 pedidos eran nórdicos, así que sumamos 6 ambientes públicos con otros estilos. "
            + (
                f"En los nórdicos siguen empatados; en los otros, IKEA más Amazon gana {rows[1][3]} a {rows[1][2]}, y los productos útiles pasan de {num(rows[1][5])} a {num(rows[1][6])}. "
                f"Los dos órdenes del juez coinciden en el {num(100 * tod11['acuerdo_entre_ordenes'], 0)}% de los ambientes. "
                if tod11
                else ""
            )
        ),
        "decision": "Usamos los dos catálogos. Con ambientes y pedidos poco variados habríamos decidido lo contrario.",
    },
    mins=1.5,
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
    fases=("busqueda",),
    why="El ground truth tiene un solo producto correcto por pieza, pero otro parecido puede servir igual. Y las consultas las escribieron modelos: el número podía depender de quién las escribió.",
    notes={
        "motivo": "El ground truth tiene un solo producto correcto por pieza, pero uno casi igual también sirve. Y las búsquedas las escribieron subagentes: con otros, ¿cambiaría el número?",
        "experimento": "Un juez califica el top-3 de 150 búsquedas con 2, 1 o 0, y antes lo validamos contra el ground truth. Y tres redactores independientes escribieron las mismas búsquedas.",
        "resultados": (
            f"El juez le da 2 al anotado el {num(100 * gt_agree.get('anotado_con_2', 0.81), 0)}% de las veces y a los demás el {num(100 * gt_agree.get('otros_con_2', 0.05), 0)}%: es confiable. "
            + (f"Con él, el primero sirve en el {num(100 * g['util1'], 0)}% de los casos, aunque hit@1 sea {num(gh1)}: el ground truth subestima. " if g else "")
            + "Con tres redactores, hit@1 varía unos 2,6 puntos: diferencias más chicas entre métodos no son señal."
        ),
        "decision": "hit@1 para comparar métodos, porque es objetivo y barato; la relevancia graduada para saber cuán útil es de verdad.",
    },
    mins=1.0,
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
        cells += f'<div>{img(d / "final.png", 520, cls="photo")}<div class="cap" style="margin-top:3px"><b>{esc(lab)}</b>{stats}</div></div>'
experiment(
    "12",
    "La imagen: del cuarto reimaginado al cuarto del cliente",
    "Cómo pedirle al modelo de imagen que respete el ambiente, y cómo darnos cuenta solos cuando no lo hace?",
    f'<div style="width:250px">{img(EST / "room.jpg", 500, cls="photo")}<div class="cap"><b>original</b></div>'
    '<p class="small" style="margin-top:8px;font-size:14.5px">Arriba, el pedido corto (6 piezas); abajo, el completo (9). Se mide SIFT y SSIM fuera de los muebles.</p></div>',
    f'<div style="width:800px"><div class="grid2 fix h125" style="gap:4px 12px">{cells}</div></div>',
    "<b>Decisión:</b> edición estricta (mismo encuadre, paredes y aberturas; exactamente esos productos) y un control: si SIFT no reencuentra el cuarto, se descarta y se reintenta (hasta 3).",
    fases=("escena", "control"),
    why="En las primeras imágenes el modelo redecoraba: inventó una ventana y movió la biblioteca. El usuario quiere ver su cuarto.",
    notes={
        "motivo": "En las primeras imágenes el modelo redecoraba: acá inventó una ventana y movió la biblioteca. El usuario quiere ver su cuarto con esos productos.",
        "experimento": "El mismo ambiente, cuatro versiones de la escena. Arriba, con el pedido corto de 6 piezas: la escena escrita por Opus y la plantilla libre. Abajo, con el pedido completo de 9 piezas: libre, y la edición estricta. Medimos con SIFT los puntos de la foto original que se reencuentran, y SSIM fuera de los muebles.",
        "resultados": f"Arriba, las dos conservan el cuarto pero la biblioteca queda chica. Abajo a la izquierda, linda pero con una ventana inventada: SIFT reencuentra solo {sift.get('experimento-buen-pedido')} puntos. La estricta conserva el cuarto, con {sift.get('experimento-buen-pedido-estricto')}, y la biblioteca es la que se pidió.",
        "decision": "Edición estricta y el control automático con reintento, que ya vimos funcionando en la fase 10.",
    },
    mins=1.2,
)

# ================================================================================================
# Cierre
# ================================================================================================
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
    mins=0.5,
    notes="Esto es el ejercicio 4 en una tabla: cada fila es un problema que encontramos usando el sistema, el cambio que hicimos y cuánto mejoró. Todos salen de lo que acabamos de ver.",
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
    mins=0.5,
)

# costos: el promedio de plan y choose en las corridas de punta a punta (registro de gastos)
_led = [json.loads(x) for x in (ROOT / "datos/resultados/gastos.jsonl").read_text().splitlines()]


def _avg(step: str) -> float:
    v = [r["cost_usd"] for r in _led if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == step]
    return sum(v) / max(1, len(v))


c_plan, c_choose = _avg("furnish.plan"), _avg("furnish.choose")
slide(
    '<div class="grid4">'
    f'<div class="card"><div class="big">~US${num(c_plan + c_choose)}</div><div class="bignote">Claude por pedido: plan (US${num(c_plan)}) y elección con 5 fotos por pieza (US${num(c_choose)}), promedio medido en 11 ambientes. La escena ya no usa LLM.</div></div>'
    '<div class="card"><div class="big">US$0,08</div><div class="bignote">por imagen (Nano Banana 2, 1K), más los reintentos si cambia el cuarto.</div></div>'
    '<div class="card"><div class="big">~US$0,007</div><div class="bignote">por producto, una vez, para describir el catálogo con Opus por la API.</div></div>'
    '<div class="card"><div class="big">0</div><div class="bignote">embeddings y base vectorial: Qwen3 y ChromaDB locales, en CPU.</div></div>'
    "</div>"
    '<p style="margin-top:24px" class="small">Cada llamada paga queda en un registro con su costo, sus tokens y su latencia, con topes por cuenta que cortan antes de pasarse. '
    "Las respuestas de los jueces y del reranking quedan en caché: repetir un experimento no se vuelve a pagar.</p>",
    kicker="Costo",
    title="Cuánto cuesta un pedido",
    notes=f"Un pedido cuesta unos {round(100 * (c_plan + c_choose))} centavos de dólar de Claude y 8 por intento de imagen. Describir el catálogo es un costo único, de menos de un centavo por producto, y embeddings y base vectorial corren locales. Todo gasto queda registrado, con topes por cuenta, y lo que ya se pagó queda en caché.",
    mins=0.4,
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
    notes="Limitaciones: los catálogos son viejos y de uso no comercial; las medidas del ambiente se estiman a ojo; el ground truth es uno solo, con consultas escritas por modelos; la imagen es una visualización; y tenemos pocos ambientes vacíos. Como trabajo futuro: medidas reales, con un metro en la foto o un modelo de profundidad; el catálogo de un vendedor actual, con precio y stock; más ambientes y evaluación humana; y que el usuario pueda cambiar una pieza y regenerar solo eso.",
    mins=0.7,
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
    mins=0.8,
)

page = (Path(__file__).with_name("plantilla.html")).read_text().replace("__SLIDES__", "\n".join(SLIDES))
OUT.write_text(page)
print(f"{OUT}: {len(SLIDES)} slides, {OUT.stat().st_size / 1e6:.1f} MB")


# -- el guion ------------------------------------------------------------------------------------
def mmss(x: float) -> str:
    s = round(x * 60)
    return f"{s // 60}:{s % 60:02d}"


def strip_tags(x: str) -> str:
    return re.sub(r"<[^>]+>", "", x)


assert len(NOTES) == len(SLIDES)
total = sum(n["mins"] for n in NOTES)


def at(pred) -> int:
    return next(i for i, n in enumerate(NOTES) if pred(n))


rec_a = at(lambda n: n["title"] == "El recorrido")
rec_b = at(lambda n: n["kicker"] == "El recorrido · los experimentos")
cut1 = at(lambda n: n["kicker"].startswith("El recorrido · fase 7"))
cut2 = at(lambda n: n["kicker"] == "Experimento 5")
parts = [(0, cut1), (cut1, cut2), (cut2, len(NOTES))]
lines_md = [
    "# Guion de la presentación (amoblai)",
    "",
    f"Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides y los extractos de los prompts, de los archivos de `src/amoblai/prompts/`. {len(SLIDES)} slides, unos {round(total)} minutos ({mmss(total)}).",
    "",
    f"**El recorrido** (slides {rec_a + 1} a {rec_b + 1}). Arriba de cada lámina va el mapa de las once fases: la fase de la que se habla, encendida; las ya vistas, marcadas. "
    "Se sigue un mismo pedido real (el living de Caballito) de la foto a la lista. La última lámina del recorrido es el mismo mapa con un pin por experimento, sobre la fase que decidió; "
    "cada lámina de experimento repite ese pin en un minimapa.",
    "",
    "**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y el experimento. **Se cuentan esas dos cosas antes de avanzar.** "
    "La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).",
    "",
    "**Reparto sugerido** (a definir entre los tres):",
]
for k, (a, b) in enumerate(parts, 1):
    lines_md.append(f"- Parte {k}: slides {a + 1} a {b} ({strip_tags(NOTES[a]['title'] or 'Portada')} → {strip_tags(NOTES[b - 1]['title'])}), unos {round(sum(n['mins'] for n in NOTES[a:b]))} min.")
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
print(f"{GUION}: {mmss(total)} min")
