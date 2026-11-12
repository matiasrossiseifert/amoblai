"""Arma docs/presentacion/amoblai.html: un solo archivo, con las imágenes y los gráficos adentro,
desde los resultados guardados en datos/resultados/ (ningún número está escrito a mano, salvo los
de DOC, que solo están en los documentos y dicen de dónde salen) y los prompts reales de
src/amoblai/prompts/.

    uv run python docs/presentacion/build.py

El orden (el de la revisión del 2026-11-12, docs/REVISION.md): el producto y por qué es un RAG; el
recorrido por las once fases del pipeline, con un mapa arriba que se va encendiendo, siguiendo una
corrida de la configuración final; los desafíos; cómo evaluamos; los experimentos por su ranking
(los que tienen lámina propia, el camino incremental y los de trámite, con su minimapa); el
Ejercicio 4 (versión 1 y versión 2); el cierre. También escribe el guion (guion.md), con las notas
de cada lámina.
"""

from __future__ import annotations

import glob
import gzip
import io
import json
import re
import statistics
import sys
from math import comb
from pathlib import Path

import yaml
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).parent))
from kit import (  # noqa: E402
    BANCO,
    FASES,
    FKEYS,
    FNAME,
    PINES,
    ROOT,
    TRAMITE,
    arrowhead,
    esc,
    hbars,
    img,
    lines,
    num,
    pin,
    pin_inline,
    pipeline,
    prompt_card,
    route,
    versions,
)

from amoblai.config import load_config  # noqa: E402
from amoblai.evaluation.retrieval import paired_difference  # noqa: E402
from amoblai.infra.budget import purpose  # noqa: E402
from amoblai.rag.filters import Filters  # noqa: E402
from amoblai.rag.hybrid import visual_query  # noqa: E402

R = ROOT / "datos" / "resultados"
OUT = Path(__file__).with_name("amoblai.html")


def load(p: str | Path) -> dict | None:
    p = Path(p)
    p = p if p.is_absolute() else ROOT / p
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def runs(suffix: str) -> list[Path]:
    return sorted(d for d in (R / "evaluacion").iterdir() if d.name.endswith(suffix) and (d / "metricas.json").exists())


def latest(suffix: str) -> Path:
    return runs(suffix)[-1]


def jsonl(p: str | Path) -> list[dict]:
    return [json.loads(x) for x in (ROOT / p).read_text().splitlines() if x.strip()]


# -- datos ---------------------------------------------------------------------------------------
# El buscador, sobre el ground truth de IKEA (549 consultas con respuesta, catálogo de 819).
ABL_DIR = latest("_ablacion-retrieval")  # la grilla: embedder, dimensión, splitting, base vectorial
ABL = load(ABL_DIR / "metricas.json")
RER_DIR = latest("_ablacion-reranking")  # un VLM ordena el top-10 mirando las fotos
RER = load(RER_DIR / "metricas.json")
CAM = load(latest("_ablacion-camino") / "metricas.json")  # el camino incremental, un cambio por paso
CON = load(latest("_ablacion-consulta") / "metricas.json")  # la ficha contra la frase natural
HIB_DIR = latest("_ablacion-hibrido")  # léxica, por foto y fusiones
HIB = load(HIB_DIR / "metricas.json")
HIB_R = [load(latest(f"_ablacion-hibrido-{r}") / "metricas.json") for r in ("r2", "r3")]  # otros dos redactores
EMB = load(latest("_ablacion-embedders") / "metricas.json")  # embedders con el filtro del flujo, exacto y por familia
RLOC = load(latest("_ablacion-reranking-local") / "metricas.json")  # Qwen3-Reranker
LIN = load(latest("_ablacion-lineas") / "metricas.json")  # qué líneas de la descripción hacen el trabajo
TODOS_DIR = latest("_ablacion-catalogo-todos")  # las mismas consultas con ABO de distractores
CURVA = load(R / "evaluacion_candidatos" / "curva_k.json")
GRAD = load(R / "evaluacion_graduada" / "graduada.json")
CAT_OLD = load(R / "evaluacion" / "20261023-173217_ablacion-retrieval" / "metricas.json")
CAT_NEW = load(latest("_ablacion-catalogo-revisado") / "metricas.json")
# El flujo entero, sobre ambientes vacíos reales: el juez de listas y el diagnóstico sin juez.
E2E = {Path(f).stem: load(f) for f in sorted(glob.glob(str(R / "punta_a_punta" / "*" / "juez_*.json")))}
DIAG = load(R / "punta_a_punta" / "hibrida" / "diagnostico.json")
DIAG_CAT = load(R / "punta_a_punta" / "catalogos" / "diagnostico.json")
FM = load(R / "punta_a_punta" / "hibrida" / "filtro_medidas.json")  # qué cambia el filtro de medidas (T6h)
RESP = load(R / "evaluacion_respuesta" / "resumen_version2.json")  # faithfulness y answer relevance (jueces v2), listas de la versión 2
RESP1 = load(R / "evaluacion_respuesta" / "resumen.json")  # lo mismo sobre otras 11 listas (búsqueda de la versión 1): la réplica
IMG_FIN = load(R / "evaluacion_imagen" / "final.json")  # las 11 imágenes de la configuración final (la plantilla)
IMG_ESC = load(R / "evaluacion_imagen" / "escena_llm.json")  # las mismas listas, con la escena escrita por el LLM
REPLICA = load(R / "replica" / "living-dagarna" / "resultados.json")
ITEMS = {x["id"]: x for x in jsonl("datos/procesados/items.jsonl")}
DESC = {x["id"]: x for x in jsonl("datos/catalogo/descripciones.jsonl")}
ABO_DESC = jsonl("datos/catalogo/abo/descripciones.jsonl")
ABO_N = len(ABO_DESC)
LEDGER = jsonl("datos/resultados/gastos.jsonl")
CFG = load_config(ROOT / "datos" / "configs" / "amoblai.yaml")

V1 = "qwen3|description|filtro-kind"  # la búsqueda de la versión 1: el coseno, con filtro por kind
V2 = V1 + "|+bm25+siglip2"  # la de la versión 2 (la del flujo): densa + léxica + foto
BASE = "qwen3|description|filtro-type"  # la base de la grilla de 2026-10 (filtro por tipo)

# Lo que solo está en los documentos (no hay un archivo de resultados del que leerlo).
DOC = {
    "otro_kind": 0.11,  # EXPERIMENTOS.md, T1 (corrección): con filtro por tipo, candidatos de otro kind en los 11 ambientes
    "con_variantes": 0.69,  # EXPERIMENTOS.md, T6g: consultas cuyo producto tiene variantes del mismo modelo
    "abo_listados": "147.702",  # EXPERIMENTOS.md, T1f
    "catalogo_268": 0.6364,  # EXPERIMENTOS.md, T1: hit@1 con el primer catálogo de 268 productos
    "generador_v1": ("0,89–0,96", "0,69–0,73"),  # EXPERIMENTOS.md, T1d: faithfulness y answer relevance con los jueces viejos
    "escena_pareado": "−0,014 [−0,103; +0,068]",  # EXPERIMENTOS.md, T10: fracción de reconocidos, LLM − plantilla, pareado por ambiente
    "escena_usd": 0.056,  # EXPERIMENTOS.md, T10: costo medio de la escena escrita por el LLM (11 llamadas)
}

# Las corridas del flujo con la configuración final (catálogo IKEA + ABO, búsqueda híbrida).
AMO = R / "amoblar"
LEC = AMO / "final-experimento-lectura"  # el producto: el cuarto de un compañero
RUN = AMO / "final-publica-loft-industrial"  # la que sigue el recorrido: pasa el control al primer intento
RUN_REQ = load(RUN / "request.json")["request"]
RUN_PLAN = load(RUN / "1_searches.json")
RUN_FOUND = load(RUN / "2_candidates.json")
RUN_CHOICE = load(RUN / "3_choice.json")
RUN_SCENE = load(RUN / "4_scene.json")
RUN_IMG = load(RUN / "5_image.json")
RUN_MET = load(RUN / "6_metricas_imagen.json")
CLA = AMO / "final-publica-living-clasico"  # una que el control rechazó en los tres intentos
CLA_IMG = load(CLA / "5_image.json")
FINALES = [
    {"slug": d.name.removeprefix("final-"), "dir": d, "img": load(d / "5_image.json"), "met": load(d / "6_metricas_imagen.json")}
    for d in sorted(AMO.glob("final-*"))
]

# Los ambientes vacíos y el crédito de las fotos públicas (las propias no llevan fuente).
AMBIENTES = yaml.safe_load((ROOT / "datos/ambientes_vacios/pedidos.yaml").read_text())["ambientes"]
PUB = {f["archivo"]: f for f in yaml.safe_load((ROOT / "datos/ambientes_vacios/publicas.yaml").read_text())["fotos"]}
FOTO = {r["slug"]: r["foto"] for r in AMBIENTES}


def credito(*slugs: str) -> str:
    """Autor y licencia de las fotos públicas de esos ambientes (publicas.yaml), sin repetir."""
    out = []
    for s in slugs:
        f = PUB[FOTO[s]]
        c = f'{f["autor"]} ({f["licencia"]})'
        if c not in out:
            out.append(c)
    return "; ".join(esc(c) for c in out)


PIE = "amoblai · TP 73.69 LLM · ITBA 2026"


def pie(*slugs: str) -> str:
    """El pie de una lámina que muestra fotos públicas: con su crédito."""
    return f'{PIE} · Foto{"s" if len(slugs) > 1 else ""} de{" los ambientes" if len(slugs) > 1 else "l ambiente"}: {credito(*slugs)}'


def ci(x: dict, k: str = "hit@1") -> tuple[float, float]:
    return tuple(x[f"{k}_ic95"])


def sg(x: float, d: int = 3) -> str:
    """+0,075 o −0,005: con signo."""
    return ("−" if x < 0 else "+") + num(abs(x), d)


def ic(lo: float, hi: float, d: int = 3) -> str:
    """[0,041; 0,111]; con signos cuando no es todo positivo: [−0,015; +0,006]."""
    return f"[{num(lo, d)}; {num(hi, d)}]" if lo >= 0 else f"[{sg(lo, d)}; {sg(hi, d)}]"


def dif(v: dict, k: str = "hit@1", d: int = 3, flip: bool = False) -> str:
    """Una diferencia pareada con su IC 95%: +0,075 [0,041; 0,111]. `flip`: al revés (b − a)."""
    x, (lo, hi) = v[k], v[f"{k}_ic95"]
    if flip:
        x, lo, hi = -x, -hi, -lo
    return f"{sg(x, d)} {ic(lo, hi, d)}"


def nb(s: str) -> str:
    """Sin cortes de línea adentro (una diferencia con su intervalo)."""
    return f'<span style="white-space:nowrap">{s}</span>'


_RANK: dict[Path, dict[str, list[dict]]] = {}


def rankings(run: Path) -> dict[str, list[dict]]:
    """Los rankings guardados de una corrida de evaluación, por método."""
    if run not in _RANK:
        f = run / "rankings.jsonl.gz"
        by: dict[str, list[dict]] = {}
        with gzip.open(f, "rt") if f.exists() else open(run / "rankings.jsonl") as fh:
            for line in fh:
                r = json.loads(line)
                by.setdefault(r["method"], []).append(r)
        _RANK[run] = by
    return _RANK[run]


def paired(run: Path, a: str, b: str, run_b: Path | None = None) -> dict:
    """a − b sobre las mismas consultas, con su IC 95% por bootstrap de ambientes. Es la cuenta de
    `vs_base` (evaluation/retrieval.py, misma semilla), hecha acá para las corridas anteriores a
    esa columna, desde sus rankings guardados."""
    return paired_difference(rankings(run)[a], rankings(run_b or run)[b])


def p_signos(a: int, b: int) -> float:
    """Test de signos a dos colas sobre los ambientes decididos (a ganados, b perdidos)."""
    n, k = a + b, max(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2**n)


def media_desvio(xs: list[float]) -> str:
    return f"{num(statistics.mean(xs), 3)} ± {num(statistics.stdev(xs), 3)}"


def recorte(path: Path, box: list[float], max_side: int = 300, pad: float = 0.04) -> str:
    """Un pedazo de una imagen (la caja de una detección), embebido."""
    import base64

    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    x0, y0, x1, y1 = box
    px, py = (x1 - x0) * pad, (y1 - y0) * pad
    im = im.crop((max(0, x0 - px), max(0, y0 - py), min(im.width, x1 + px), min(im.height, y1 + py)))
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=80, optimize=True)
    return f'<img alt="" src="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}">'


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
        f'<div class="foot"><span>{foot or PIE}</span><span class="n"></span></div></section>'
    )


def section(kicker: str, title: str, text: str = "", notes: str = "", mins: float = 0.1) -> None:
    body = f'<div class="kicker">{kicker}</div><h1>{title}</h1><p style="margin-top:18px">{text}</p>'
    slide(body, "section", notes=notes, mins=mins)
    NOTES[-1].update(kicker=kicker, title=title)  # el encabezado va en el cuerpo, no en slide()


def fase(key: str, title: str, body: str, take: str, notes: str, mins: float, foot: str = "") -> None:
    """Una lámina del recorrido: arriba el mapa con esta fase encendida y las anteriores vistas;
    abajo, la frase de cierre."""
    i = FKEYS.index(key)
    slide(
        route(cur=key) + body + (f'<div class="take">{take}</div>' if take else ""),
        cls="fase",
        kicker=f"El recorrido · fase {i + 1} de {len(FASES)} · {FNAME[key]}",
        title=title,
        foot=foot,
        notes=notes,
        mins=mins,
    )


def dec(n: int | None, html: str) -> str:
    """Una decisión con el pin del experimento que la midió (o sin pin)."""
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
    foot: str = "",
) -> None:
    """Una slide por experimento, en el orden en que se cuenta: arriba el minimapa (a qué fase le
    hizo la pregunta, con su pin), por qué lo hicimos y qué queríamos ver; a la izquierda, qué se
    comparó. Con la flecha aparecen los resultados (paso 1) y después la decisión (paso 2)."""
    left = left.replace('<div class="find"', '<div data-step="1" class="find"')
    body = (
        (route(lit=fases, pins={f: [int(n)] for f in fases}) if fases else "")
        + (f'<p class="why"><b>Por qué:</b> {why}</p>' if why else "")
        + f'<p class="q">{question}</p>'
        + f'<div class="row grow"><div class="grow"><div class="coltag">Qué se comparó</div>{left}</div>'
        + f'<div data-step="1"><div class="coltag">Resultados</div>{right}</div></div>'
        + f'<div class="decision" data-step="2">{decision}</div>'
    )
    slide(body, kicker=f"Experimento {n}", title=title, notes=notes or {}, mins=mins, foot=foot)


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


def elegidos(found: dict, choice: dict) -> list[tuple[dict, int, int]]:
    """Lo que eligió una corrida: (el producto, cuántas unidades, su puesto en la búsqueda)."""
    out = []
    for p, c in zip(found["pieces"], choice["answer"]["choices"], strict=True):
        q = int(c.get("quantity", 1) or 0)
        if q:
            ids = [h["id"] for h in p["candidates"]]
            out.append((p["candidates"][ids.index(c["id"])], q, ids.index(c["id"]) + 1))
    return out


# Los números que se repiten en varias láminas.
B1, B2 = CAM[V1], CAM[V2]  # versión 1 y versión 2 de la búsqueda, sobre el ground truth
D21 = HIB[V2]["vs_base"]  # versión 2 − versión 1, pareado
N_ANS, N_BUS = B2["answerable"], B2["searches"]
N_AMB = len({r["room_id"] for r in rankings(HIB_DIR)[V1]})  # ambientes de IKEA con consultas
N_AMB_ANS = len({r["room_id"] for r in rankings(HIB_DIR)[V1] if r["relevant"]})  # con alguna con respuesta
JV = E2E["juez_densa_vs_hibrida"]  # versión 1 contra versión 2, de punta a punta
JA = E2E["juez_densa_vs_azar_7ambientes"]  # con búsqueda contra sin búsqueda
JR = E2E["juez_hibrida_vs_hibrida_bis"]  # la versión 2 contra sí misma: el piso de ruido
jr = JR["resumen"]
ruido_total = sum(len(d["listas"]["hibrida"]) for d in JR["detalle"])
ruido_cambian = sum(x["id"] != y["id"] for d in JR["detalle"] for x, y in zip(d["listas"]["hibrida"], d["listas"]["hibrida_bis"], strict=True))
JC = E2E["juez_ikea_vs_todos"]  # IKEA contra IKEA + ABO
votos_v = [v for d in JV["detalle"] for v in d["votos"]]
IMG_TOT = {
    "productos": sum(len(f["met"]["productos"]) for f in FINALES),
    "detectados": sum(bool(p["detectado"]) for f in FINALES for p in f["met"]["productos"]),
    "reconocidos": sum(p.get("puesto") == 1 for f in FINALES for p in f["met"]["productos"]),
    "coseno": statistics.mean(p["coseno"] for f in FINALES for p in f["met"]["productos"] if p.get("coseno") is not None),
    "pasan": sum(bool(f["img"]["room_check"]["ok"]) for f in FINALES),
    "pasan_al_primero": sum(bool(f["img"]["attempts"][0]["ok"]) for f in FINALES),
    "intentos": sum(len(f["img"]["attempts"]) for f in FINALES),
}


def _avg(step: str) -> float:
    """El costo medio de un paso del flujo desde el 10/11 (catálogo IKEA + ABO), del registro."""
    v = [r["cost_usd"] for r in LEDGER if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == step]
    return sum(v) / max(1, len(v))


c_plan, c_choose = _avg("furnish.plan"), _avg("furnish.choose")
c_img = CFG.furnish.generators["nano_banana_2"]["usd_per_image"]["1K"]
c_pedido = c_plan + c_choose + c_img


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
    f'<div class="hero" style="width:470px;display:grid;gap:10px">{img(LEC / "room.jpg", 1000, cls="photo")}{img(LEC / "final.png", 1000, cls="photo")}</div>'
    "</div>",
    notes="Somos Juan Bautista, Matías y Junior. amoblai responde una pregunta concreta: tengo este ambiente vacío, ¿qué compro y cómo queda? Sacás una foto, escribís qué querés, y te devuelve una lista de productos reales de un catálogo y la imagen del mismo ambiente con esos productos.",
    mins=0.35,
)

# 2. El problema
slide(
    '<div class="row center" style="gap:40px">'
    f'<div style="width:560px">{img(LEC / "room.jpg", 1100, cls="photo")}<div class="cap">Un ambiente vacío real (foto de un compañero).</div></div>'
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
    mins=0.4,
    notes="Cuando te mudás a un lugar vacío tenés que decidir qué comprar sin poder verlo puesto. Los catálogos muestran cada mueble suelto, sobre fondo blanco, y las fotos de ambientes muestran la casa de otro. Queremos responder, para este ambiente y este pedido: qué productos reales van, cuántos, y cómo queda el ambiente con ellos.",
)

# 3. Qué hace: una corrida de la configuración final sobre ese mismo cuarto
lec_picks = elegidos(load(LEC / "2_candidates.json"), load(LEC / "3_choice.json"))
lec_req = load(LEC / "request.json")["request"]
items = "".join(
    f'<div style="text-align:center">{img(h["photos"][0], 220, cls="photo")}<div class="tiny">{esc(type_line(h["description"]))}{" ×" + str(q) if q > 1 else ""}</div></div>'
    for h, q, _ in lec_picks[:8]
)
slide(
    '<div class="row" style="gap:28px">'
    f'<div style="width:330px"><div class="tag">entrada</div><div style="margin:8px 0">{img(LEC / "room.jpg", 700, cls="photo")}</div>'
    f'<div class="card small" style="padding:12px 14px;font-size:14.5px;line-height:1.35">“{esc(lec_req)}”</div></div>'
    '<div class="grow"><div class="tag g">salida 1 · la lista de compra</div>'
    f'<div class="grid4" style="margin-top:10px;gap:10px">{items}</div></div>'
    f'<div style="width:330px"><div class="tag g">salida 2 · el ambiente amoblado</div><div style="margin-top:8px">{img(LEC / "final.png", 800, cls="photo")}</div>'
    '<div class="cap">Generada con esos productos, en ese mismo ambiente.</div></div>'
    "</div>",
    kicker="El producto",
    title="Foto + pedido → lista de compra + imagen",
    mins=0.5,
    notes=f"Así se usa. La entrada es una foto del ambiente y un pedido en texto libre, como este: un rincón de lectura con una biblioteca alta de madera oscura. La salida son dos cosas: la lista de compra, con productos reales del catálogo, acá {len(lec_picks)}, entre IKEA y Amazon, y la foto del mismo ambiente con esos productos puestos.",
)

# 4. Por qué RAG: los tres desafíos de la clase
slide(
    '<div class="grid3">'
    '<div class="card"><div class="lab">Información actualizada</div><h3>El catálogo cambia; el modelo no se reentrena</h3>'
    '<p class="small">Un producto nuevo es una fila más en el índice: se describe, se embebe y ya se puede recomendar.</p></div>'
    '<div class="card"><div class="lab">Información personalizada</div><h3>Este catálogo, este ambiente, este pedido</h3>'
    f'<p class="small">El LLM no conoce estos {miles(len(ITEMS) + ABO_N)} productos. La búsqueda le trae {CFG.furnish.candidates} candidatos reales por pieza, y elige mirando sus fotos y la del cuarto.</p></div>'
    '<div class="card" style="border-color:var(--accent)"><div class="lab" style="color:var(--accent)">Sin alucinaciones</div><h3>Solo productos que existen</h3>'
    '<p class="small">Un LLM solo recomienda "un sillón de cuero coñac" que nadie vende; un modelo de imagen solo inventa los muebles. Acá la lista solo puede tener ids que trajo la búsqueda, y la imagen se genera <b>desde las fotos de los elegidos</b>.</p></div>'
    "</div>"
    '<div class="grid2" style="margin-top:24px;gap:34px">'
    "<p><b>No es un Q&amp;A.</b> La consulta es una foto y un pedido abierto; la respuesta, una combinación de productos que tiene que funcionar junta, en ese espacio.</p>"
    "<p><b>Dos generaciones aumentadas</b> con lo recuperado: la lista (qué producto, cuántos y por qué) y la imagen del ambiente amoblado.</p>"
    "</div>"
    '<div class="take">Los tres desafíos de la clase: información <b>actualizada</b>, <b>personalizada</b> y <b>sin alucinaciones</b>.</div>',
    kicker="Por qué RAG",
    title="Recomendaciones atadas a productos que existen",
    mins=0.8,
    notes=f"¿Por qué un RAG? Por los tres desafíos de la clase. Información actualizada: el catálogo cambia y el modelo no se reentrena; un producto nuevo es una fila más en el índice. Información personalizada: el LLM no conoce estos {miles(len(ITEMS) + ABO_N)} productos; la búsqueda le trae cinco candidatos reales por pieza. Y sin alucinaciones: un LLM solo recomienda un sillón que nadie vende, y un modelo de imagen solo inventa los muebles; acá la lista solo puede tener productos que trajo la búsqueda, y la imagen se genera desde sus fotos. No es un Q&A: la consulta es una foto y un pedido abierto, y hay dos generaciones aumentadas, la lista y la imagen.",
)


# ================================================================================================
# Parte 1: el recorrido, fase por fase
# ================================================================================================
section(
    "Parte 1",
    "El recorrido",
    "Las once fases del pipeline, en orden: qué entra y qué sale de cada una, qué decidimos, con qué modelo, y los prompts que mandamos y cómo los fuimos reescribiendo.",
    notes="Primero, el recorrido: todo el pipeline, fase por fase, con un mapa que se va encendiendo.",
)

slide(
    pipeline()
    + '<div class="grid2 small" style="margin-top:8px;gap:24px">'
    "<div><b>Una vez, offline.</b> Entran los productos de dos catálogos, con su foto; sale un índice con la descripción, los vectores y la metadata de cada uno.</div>"
    "<div><b>Por cada pedido.</b> Entran una foto del ambiente vacío y un pedido en texto libre; salen la lista de compra y la foto amoblada.</div>"
    "</div>"
    '<div class="lab" style="margin-top:22px">Quién hace cada fase</div><div class="who" style="grid-template-columns:repeat(6,1fr)">'
    "<div><b>Opus 5.5</b><span>fases 2, 5 y 7: describe cada producto, planea y elige</span></div>"
    "<div><b>Qwen3-Embedding</b><span>fases 3 y 6: embebe descripciones y consultas, local</span></div>"
    "<div><b>BM25 y SigLIP 2</b><span>fases 3 y 6: las palabras y la foto de cada producto, locales</span></div>"
    "<div><b>ChromaDB</b><span>fases 3 y 6: guarda los vectores y la metadata de los filtros</span></div>"
    "<div><b>Nano Banana 2</b><span>fase 9: edita la foto, por fal</span></div>"
    "<div><b>SIFT + RANSAC</b><span>fase 10: compara con la foto original</span></div>"
    "</div>"
    '<div class="take">Por pedido se pagan tres llamadas: <b>Opus 5.5</b> en el plan y en la elección, y <b>Nano Banana 2</b> en la imagen. Lo demás corre local.</div>',
    kicker="El recorrido · el mapa",
    title="Once fases: una vez offline, y por cada pedido",
    notes="Este es el mapa completo, con dos pipelines. Arriba, lo que se hace una vez, offline: el catálogo, la descripción de cada producto y el índice. Abajo, lo que pasa en cada pedido: entran la foto y el pedido, el plan decide las piezas, la búsqueda trae candidatos, la elección arma la lista, y después la escena, la imagen y el control. Por pedido se pagan solo tres llamadas: Opus en el plan y en la elección, y Nano Banana 2 en la imagen. Lo demás corre local.",
    mins=0.65,
)


# -- Fase 1: el catálogo
def catalog_flow() -> str:
    """Los dos catálogos, de los datos crudos a lo que usa el flujo (números de EXPERIMENTOS.md
    T1c, T1e y T1f, salvo los que se cuentan acá)."""
    cw, gap, chh, x0 = 150, 34, 70, 212
    lanes = [
        ("IKEA", ["Tautkute et al., 2017", "uso no comercial"], 24,
         [("2.191", "productos del dataset"), ("268", "primer alcance: cuatro tipos"), ("855", "+ guardado, luz, textiles y deco"), (f"{len(ITEMS)}", "revisado: 36 productos afuera")]),
        ("ABO", ["Amazon Berkeley Objects", "Collins et al., CVPR 2022"], 112,
         [(DOC["abo_listados"], "listados de Amazon"), ("781", "uno por modelo, con tope por kind"), ("759", "sin fotos de relleno"), (f"{ABO_N}", "descriptos, en el alcance")]),
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
    fx, fw, fy, fh = 962, 198, 50, 96
    out.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="12" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="1.6"/>')
    out.append(f'<text x="{fx + 16}" y="{fy + 40}" font-family="Fraunces, Georgia, serif" font-size="32" font-weight="650" fill="var(--accent)">{miles(len(ITEMS) + ABO_N)}</text>')
    out.append(f'<text x="{fx + 16}" y="{fy + 62}" font-size="12.5" fill="var(--ink)">el catálogo del flujo</text>')
    out.append(f'<text x="{fx + 16}" y="{fy + 79}" font-size="11.5" font-family="JetBrains Mono, monospace" fill="var(--muted)">todos.yaml</text>')
    out.append(pin(fx + fw - 14, fy + 7, 10, 6))
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
ikea_con_medida = sum(any(v is not None for v in (x.get("dimensions_cm") or {}).values()) for x in ITEMS.values()) / len(ITEMS)
fase(
    "catalogo",
    "Dos catálogos de productos reales, con foto",
    catalog_flow()
    + '<div class="row" style="gap:30px;margin-top:10px">'
    f'<div style="width:560px"><div class="lab">Un producto de IKEA, como viene</div><div class="code"><div class="ph"><b>items.jsonl</b><span>un sofá del catálogo</span></div><pre>{rec}</pre></div></div>'
    '<div class="grow"><div class="lab">Lo que guardamos de cada uno</div>'
    + dec(None, "<b>Fotos</b>: la imagen sale de ellas, y el VLM las mira para describir.")
    + dec(None, "<b>Tipo</b> (14) y <b>kind</b> (44: mesa ratona, lámpara de pie…): el kind es el filtro duro de la búsqueda.")
    + dec(None, f"<b>Medidas</b>, cuando hay: en IKEA, el {num(100 * ikea_con_medida, 0)} % (ningún sofá ni sillón); en ABO, el 90 %.")
    + "</div></div>",
    "El texto del vendedor es marketing y faltan medidas: por eso cada producto <b>se describe mirando su foto</b>.",
    notes=f"Fase uno, el catálogo. Son dos. El dataset de IKEA: de sus 2.191 productos empezamos con 268 muebles, lo ampliamos a 855 de living y comedor y, revisado mirando cada foto, quedaron {len(ITEMS)}. Y Amazon Berkeley Objects, listados reales de Amazon: de casi 150 mil quedaron {ABO_N}. El flujo usa los dos, {miles(len(ITEMS) + ABO_N)} productos. De cada uno guardamos las fotos, el tipo, el kind y las medidas cuando hay. Así viene un sofá de IKEA: el texto es marketing y no tiene medidas.",
    mins=0.6,
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
    notes="Fase dos: la descripción. Un VLM mira la foto de cada producto y lo escribe en ocho líneas fijas: tipo, uso, estilo, materiales, colores, forma, sensación y con qué combina. Es el mismo sofá: a la izquierda, lo que dice IKEA; en el medio, lo que escribió el modelo. El prompt pide exactamente esas ocho líneas, sin marca, precio ni medidas, y nada de lo que el producto no es, porque el embedding no entiende la negación. Para Amazon usamos la misma receta, por la API. Es el preprocesamiento que más pesa: lo mide el experimento 1.",
    mins=0.7,
)


# -- Fase 3: el índice
def index_flow() -> str:
    boxes = [
        ("La descripción", ["un documento por producto", "8 líneas, unas 80 palabras"], 11),
        ("Qwen3-Embedding-0.6B", ["local, en CPU (Apache 2.0)", "último token, sin instrucción"], 9),
        ("Un vector", ["1.024 dimensiones", "norma 1: el producto es el coseno"], 10),
        ("ChromaDB", ["HNSW, coseno · ef_search 100 · M 16", "+ metadata: tipo, kind y medidas"], 12),
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


siglip = CFG.rag.embedders["siglip2"]["model"]
fase(
    "indice",
    "Un vector por producto: Qwen3, local, en ChromaDB",
    index_flow()
    + '<div class="row" style="gap:36px;margin-top:14px">'
    '<div style="width:610px"><div class="lab">Las preguntas de trámite (lo elegido, en negrita)</div>'
    + dec(9, "<b>Embedder</b>: hashing (sin modelo) · BM25 · BGE-base · <b>Qwen3-Embedding-0.6B</b>")
    + dec(11, "<b>Splitting</b>: <b>un documento por producto</b> · un chunk por línea · línea contra línea")
    + dec(10, "<b>Dimensión</b> (Matryoshka): de 32 a 512 · <b>1.024</b> (con 512 alcanza)")
    + dec(12, "<b>Base</b>: <b>ChromaDB con HNSW</b> · búsqueda exacta con numpy")
    + "</div>"
    '<div class="grow"><div class="lab">Para la búsqueda híbrida, dos índices más</div>'
    + dec(3, "<b>Léxico (BM25)</b>: las palabras de esas mismas descripciones, sin modelo.")
    + dec(3, f'<b>Por foto (SigLIP 2)</b>: un vector por la foto de cada producto, en el mismo espacio que el texto de la consulta <span class="tiny" style="font-family:var(--mono);font-size:11.5px">({esc(siglip)})</span>.')
    + '<p class="tiny" style="margin:4px 0 0 33px">Las dos rutas de la clase para un catálogo con fotos: pasar la imagen a texto, y embeberla directamente.</p></div>'
    "</div>",
    "Se arma una vez, local y gratis: la descripción embebida, sus palabras y la foto de cada producto, con la metadata al lado para filtrar.",
    notes="Fase tres: el índice. Se embebe la descripción entera, un documento por producto, con Qwen3-Embedding, local, en CPU: 1.024 dimensiones, a ChromaDB, con la metadata de los filtros. Embedder, splitting, dimensión y base vectorial son las preguntas de trámite, por eso su pin va hueco: las contestamos juntas más adelante. Para la búsqueda híbrida se suman dos índices sobre los mismos productos: uno léxico, BM25 sobre las palabras de las descripciones, y uno por foto, con SigLIP 2, que pone la foto y el texto de la consulta en un mismo espacio.",
    mins=0.65,
)

# -- Fase 4: lo que entra
fase(
    "entrada",
    "Entra una foto del ambiente vacío y un pedido libre",
    '<div class="row" style="gap:30px">'
    f'<div style="width:520px" class="fix h360">{img(RUN / "room.jpg", 1100, cls="photo")}<div class="cap">La foto que se amobla: la imagen 1 de todo el recorrido.</div></div>'
    '<div class="grow">'
    f'<div class="lab">El pedido, como lo escribe el usuario</div><div class="quote" style="font-size:16.5px;line-height:1.45">“{esc(RUN_REQ)}”</div>'
    '<div class="lab" style="margin-top:16px">Qué va a dónde</div>'
    + dec(None, "<b>La foto</b> va al plan y a la elección (reducida a 1.024 px) y al modelo de imagen.")
    + dec(None, "<b>Otras fotos del mismo ambiente</b> (opcionales) van solo al LLM, para entenderlo. Nunca medimos si cambian la lista.")
    + "</div></div>",
    "No hay formulario: qué piezas, de qué tipo y de qué tamaño lo decide <b>el plan</b>.",
    notes="Fase cuatro, lo que entra: una foto del ambiente vacío y un pedido en texto libre. Vamos a seguir este loft hasta el final: un pedido de estilo industrial, sobre una foto pública, con la configuración con la que entregamos.",
    mins=0.3,
    foot=pie("publica-loft-industrial"),
)

# -- Fase 5: el plan
p1 = RUN_PLAN["answer"]["pieces"][0]
hl_req = "un sofá de cuero marrón envejecido"
assert hl_req in RUN_REQ, "el pedido de la corrida del recorrido cambió: revisar la fase 5"
req_cut = RUN_REQ[RUN_REQ.index("Quiero"): RUN_REQ.index(hl_req) + len(hl_req)]
plan_meta = RUN_PLAN["meta"]
fase(
    "plan",
    "El plan descompone el pedido y escribe una ficha por pieza",
    '<div class="row" style="gap:24px">'
    '<div style="width:510px">'
    f'<div class="lab">Entra (con la foto)</div><div class="quote" style="font-size:14.5px">“…{esc(req_cut).replace(esc(hl_req), "<b>" + esc(hl_req) + "</b>")}…”</div>'
    f'<div class="lab" style="margin-top:12px">Sale: la pieza 1 de {len(RUN_PLAN["answer"]["pieces"])}</div>'
    '<div class="code"><div class="ph"><b>1_searches.json</b>'
    f'<span>Opus 5.5 · effort medium · {round(plan_meta["latency_s"])} s · US${num(RUN_PLAN["cost_usd"], 2)}</span></div>'
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
    + '<div style="height:6px"></div>'
    + versions(
        [
            ("v1", "Con “una silla” para un escritorio, pidió un <b>sillón</b>.", False),
            ("v2", "Leer el ambiente; <b>la pieza que nombró</b>; el kind de una lista; de 1 a 4 piezas.", False),
            ("v3", "Lámparas y deco: hasta 6 piezas, <b>terminar el ambiente</b>.", False),
            ("v4", "<b>Sin tope de piezas</b>: un rincón de lectura ya llegaba a 6.", True),
        ]
    )
    + "</div></div>",
    f"{pin_inline(2)} En palabras de la clase: <b>query expansion con respuesta hipotética (HyDE)</b> y <b>descomposición del pedido</b>.",
    notes=f"Fase cinco, el plan. Opus recibe la foto y el pedido y hace de diseñador: lee el ambiente, descompone el pedido en piezas y, para cada una, da el kind, que va a ser el filtro, la medida máxima, y la consulta: el producto ideal escrito en las mismas ocho líneas que el catálogo. En los términos de la clase es query expansion con respuesta hipotética, HyDE: en la base no hay preguntas, hay respuestas, así que la consulta se escribe como una respuesta. Más la descomposición del pedido: una consulta por pieza. Del “sofá de cuero marrón envejecido” sale esta pieza: kind sofá, hasta {p1['max_width_cm']} centímetros, y su ficha. Propuso {len(RUN_PLAN['answer']['pieces'])} piezas. Cuánto suma escribir la ficha lo mide el experimento 2.",
    mins=0.9,
    foot=pie("publica-loft-industrial"),
)

# -- Fase 6: la búsqueda (híbrida: la versión 2)
slack = CFG.furnish.size_slack
most = {f"max_{a}_cm": round(p1[f"max_{a}_cm"] * (1 + slack), 1) for a in ("width", "depth", "height") if p1.get(f"max_{a}_cm") is not None}
filtro = Filters(kinds=p1["kinds"], **most)
EJE = {"max_width_cm": "ancho", "max_depth_cm": "fondo", "max_height_cm": "alto"}
filtro_txt = " · ".join([f'kind = {", ".join(p1["kinds"])}'] + [f"{EJE[k]} ≤ {num(v, 0)} cm" for k, v in most.items()])
# cuántos productos del índice del flujo deja pasar ese filtro (el índice está en la caché)
idx_items = ROOT / CFG.cache_dir / "rag" / "index" / f"{Path(CFG.rag.catalog).stem}-{CFG.rag.describer}-{CFG.rag.embedder}" / "items.jsonl"
pasan = sum(filtro.allows(json.loads(x)) for x in idx_items.read_text().splitlines() if x.strip()) if idx_items.exists() else None
pasan_txt = f" → <b>{pasan} de {miles(len(ITEMS) + ABO_N)}</b>" if pasan else ""
chosen_ids = {c["id"] for c in RUN_CHOICE["answer"]["choices"] if c.get("quantity")}
sofas = RUN_FOUND["pieces"][0]["candidates"]
sofas_abo = sum(h["id"].startswith("abo-") for h in sofas)
cards = "".join(
    f'<div class="c{" pick" if h["id"] in chosen_ids else ""}">'
    + ('<span class="flag">lo elige la fase 7</span>' if h["id"] in chosen_ids else "")
    + f'{img(h["photos"][0], 300)}<div class="s">{num(h["score"], 2)} · {"ABO" if h["id"].startswith("abo-") else "IKEA"}</div><div class="t">{esc(type_line(h["description"]))}</div></div>'
    for h in sofas
)
vq = visual_query(p1["query"])
fase(
    "busqueda",
    "Filtro por kind, después búsqueda híbrida: 5 candidatos",
    '<div class="row" style="gap:28px">'
    '<div style="width:486px"><div class="lab">Para cada pieza del plan</div>'
    + dec(13, f'<b>Filtro duro</b> de metadata: el kind del plan y sus medidas máximas, con un {round(100 * slack)} % de margen; un producto sin medidas pasa.<br><span class="mono">{esc(filtro_txt)}</span>{pasan_txt}')
    + dec(3, "<b>Tres puntajes</b> para cada producto que pasa, con la misma ficha:")
    + '<div class="tri">'
    "<div><b>Qwen3</b><span>el coseno entre la ficha y la descripción del producto</span></div>"
    "<div><b>BM25</b><span>las palabras de la ficha que están en la descripción</span></div>"
    f'<div><b>SigLIP 2</b><span>la ficha en una frase, contra la <b>foto</b> del producto: <i>“{esc(vq[:64])}…”</i></span></div>'
    "</div>"
    + dec(None, "<b>Fusión</b>: cada puntaje se estandariza (z-score) entre los que pasaron, y se promedian.")
    + dec(5, f"<b>Los {CFG.furnish.candidates} mejores</b> le llegan a la elección (antes 3).")
    + "</div>"
    f'<div class="grow"><div class="lab">Los {len(sofas)} sofás que le llegan a la elección (puntaje fusionado · catálogo)</div>'
    f'<div class="cand" style="grid-template-columns:repeat({len(sofas)},1fr);margin-top:14px">{cards}</div>'
    '<p class="tiny" style="margin-top:12px">El puntaje es el promedio de los tres z-scores: 2,3 quiere decir 2,3 desvíos por encima de la media de los sofás que pasaron el filtro.</p></div>'
    "</div>",
    "Tres miradas del mismo producto (su descripción, sus palabras, su foto) traen candidatos plausibles; el orden fino lo decide <b>quien mira las fotos</b>.",
    notes="Fase seis, la búsqueda. Para cada pieza, primero un filtro duro de metadata: el kind del plan y las medidas máximas, con margen porque salen de una foto."
    + (f" Acá quedan {pasan} de los {miles(len(ITEMS) + ABO_N)} productos." if pasan else "")
    + f" Sobre esos, tres puntajes: el coseno de Qwen3 entre la ficha y la descripción; BM25, las palabras de la ficha que están en la descripción; y SigLIP 2, la ficha en una frase contra la foto del producto. Cada puntaje se estandariza y se promedian: es la búsqueda híbrida, la versión 2 del sistema. Quedan los cinco mejores: estos sofás, {sofas_abo} de Amazon y {len(sofas) - sofas_abo} de IKEA.",
    mins=0.85,
    foot=pie("publica-loft-industrial"),
)

# -- Fase 7: la elección: la generación de la lista
ES_KIND = {"sofa": "sofá", "rug": "alfombra", "coffee table": "mesa ratona", "TV stand": "mueble de TV", "floor lamp": "lámpara de pie", "cushion": "almohadones", "plant": "planta", "curtains": "cortinas", "bookcase": "biblioteca", "plant pot": "maceta", "armchair": "sillón", "side table": "mesa auxiliar", "throw": "manta"}
grid_rows = []
for p, c in zip(RUN_FOUND["pieces"], RUN_CHOICE["answer"]["choices"], strict=True):
    k = p["spec"]["kinds"][0]
    th = "".join(
        f'<div class="th{" pick" if h["id"] == c.get("id") else ""}" style="width:34px;height:34px">{img(h["photos"][0], 90, alt="")}</div>'
        for h in p["candidates"]
    )
    qty = f'<span style="font-size:12.5px;font-weight:650;color:var(--accent);margin-left:4px">×{c["quantity"]}</span>' if c.get("quantity", 1) > 1 else ""
    grid_rows.append(f'<div style="display:flex;align-items:center;gap:4px"><div style="width:100px;font-size:12.5px">{esc(ES_KIND.get(k, k))}</div>{th}{qty}</div>')
ch_meta = RUN_CHOICE["meta"]
run_picks = elegidos(RUN_FOUND, RUN_CHOICE)
n_first = sum(rk == 1 for *_, rk in run_picks)
i_far = max(range(len(run_picks)), key=lambda i: run_picks[i][2])  # la pieza cuyo elegido estaba más abajo en la búsqueda
far_rank = run_picks[i_far][2]
far_piece = next(i for i, c in enumerate(RUN_CHOICE["answer"]["choices"]) if c.get("id") == run_picks[i_far][0]["id"])
far_kind = ES_KIND.get(RUN_FOUND["pieces"][far_piece]["spec"]["kinds"][0], RUN_FOUND["pieces"][far_piece]["spec"]["kinds"][0])
far_why = RUN_CHOICE["answer"]["choices"][far_piece]["why"]
assert (far_kind, far_rank) == ("biblioteca", 5), "la nota de la fase 7 cuenta ese caso: revisarla si la corrida cambió"
fase(
    "eleccion",
    "Opus ve el cuarto y los 5 de cada pieza, y arma la lista",
    '<div class="row" style="gap:26px">'
    '<div style="width:540px">'
    f'<div class="lab">Lo que ve: {ch_meta["images"]} imágenes (el cuarto y 5 por pieza)</div>'
    '<div style="display:flex;gap:14px;align-items:flex-start">'
    f'<div style="width:170px">{img(RUN / "room.jpg", 400, cls="photo")}<div class="tiny" style="margin-top:4px">imagen 1</div></div>'
    f'<div style="display:grid;gap:3px">{"".join(grid_rows)}</div></div>'
    f'<div class="tiny" style="margin-top:6px">Con borde naranja, lo elegido. {miles(ch_meta["usage"]["input_tokens"])} tokens de entrada · {round(ch_meta["latency_s"])} s · US${num(RUN_CHOICE["cost_usd"], 2)}.</div>'
    f'<div class="quote" style="margin-top:10px;font-size:14px"><b>{esc(far_kind.capitalize())} (el {far_rank}.º de la búsqueda):</b> <i>“{esc(far_why)}”</i></div>'
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
    f"{pin_inline(5)} Es <b>la generación</b> del RAG, no un reranker: tomó el 1.º de la búsqueda en {n_first} de las {len(run_picks)} piezas.",
    notes=f"Fase siete, la elección: es la generación de la lista, la G del RAG. Opus ve la foto del ambiente y los cinco candidatos de cada pieza, acá {ch_meta['images']} imágenes, cada uno con su id, su tipo y su medida. El prompt le pide elegir las piezas juntas, como un solo look, y decir cuántas unidades; cero deja una pieza afuera. Solo puede elegir productos que trajo la búsqueda: si no, el código rechaza la respuesta. No es un reranker: arma un conjunto para este cuarto. Acá tomó el primero de la búsqueda en {n_first} de las {len(run_picks)} piezas; la {far_kind} era el quinto candidato.",
    mins=0.8,
    foot=pie("publica-loft-industrial"),
)

# -- Fase 8: la escena
scene_text = RUN_SCENE["answer"]["prompt"]
scene_lines = scene_text.splitlines()
ln_first = next(x for x in scene_lines if x.startswith("image 2:"))
ln_units = next((x for x in scene_lines if x.startswith("image ") and x.endswith("units")), None)
c_scene = statistics.mean(r["cost_usd"] for r in LEDGER if r["step"] == "furnish.scene")
fase(
    "escena",
    "El prompt de la imagen: una plantilla, sin LLM",
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
            ln_first,
            *([ln_units] if ln_units else []),
            "[[Add exactly these products and nothing else]]",
            "Each one must be the product of its photo, not a similar one",
        ],
        note="completada para este pedido (4_scene.json)",
        source=scene_text,
    )
    + '<div style="margin-top:14px">'
    + dec(None, f"<b>A contra B en los {IMG_FIN['corridas']} ambientes</b>, con las mismas listas: con la escena escrita por Opus se reconocen {IMG_ESC['identificados']} de {IMG_ESC['productos']} productos y el cuarto se conserva en {IMG_ESC['ambiente_conservado']}; con la plantilla, {IMG_FIN['identificados']} y {IMG_FIN['ambiente_conservado']}. <b>Empate</b>: queda la plantilla, que ahorra una llamada (US${num(DOC['escena_usd'], 3)} por pedido).")
    + "</div></div></div>",
    "La escena no la escribe nadie: una plantilla fija le pide al modelo <b>editar la foto del cliente</b>. Que la escriba un LLM no mejora nada medible.",
    notes="Fase ocho, la escena: el prompt para el modelo de imagen. Probamos dos caminos: que Opus escriba dónde va cada producto, o una plantilla sin LLM, que se completa con la lista. La última versión de la plantilla es estricta: es una edición de la foto del cliente, con la misma cámara, las mismas paredes y ventanas, y exactamente estos productos. Las comparamos en los once ambientes, con las mismas listas: empatan en productos reconocidos y en cuartos conservados. Nos quedamos con la plantilla, que ahorra una llamada.",
    mins=0.65,
)

# -- Fase 9: la imagen
gen = CFG.furnish.generators["nano_banana_2"]
att = RUN_IMG["attempts"]
prod_th = "".join(f'<div class="th" style="height:62px">{img(h["photos"][0], 140, alt="")}</div>' for h, *_ in run_picks)
fase(
    "imagen",
    "Nano Banana 2 edita la foto con las fotos de los productos",
    '<div style="display:grid;grid-template-columns:430px 34px 250px 34px 1fr;align-items:center;gap:0">'
    f'<div><div class="lab">Entra</div><div style="display:grid;grid-template-columns:190px 1fr;gap:10px;align-items:center">'
    f'<div>{img(RUN / "room.jpg", 500, cls="photo")}<div class="tiny" style="margin-top:3px">imagen 1: el cuarto</div></div>'
    f'<div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px">{prod_th}</div><div class="tiny" style="margin-top:3px">imágenes 2 a {RUN_IMG["meta"]["images_in"]}: los productos</div></div></div>'
    '<div class="tiny" style="margin-top:8px">+ el prompt de la fase 8</div></div>'
    '<div style="text-align:center;color:var(--muted);font-size:24px">→</div>'
    '<div class="card" style="border-color:var(--accent)"><h3 style="font-size:19px;margin-bottom:2px">Nano Banana 2</h3>'
    '<div class="small" style="font-size:14px;line-height:1.45">Gemini 3.1 Flash Image, por fal<br>'
    f'<span style="font-family:var(--mono);font-size:12px;color:var(--muted)">{esc(gen["endpoint"])}</span><br>'
    f'{gen["resolution"]}, con la proporción de la foto<br><b>US${num(gen["usd_per_image"]["1K"])} por imagen</b> · ~{round(RUN_IMG["meta"]["latency_s"])} s por imagen</div></div>'
    '<div style="text-align:center;color:var(--muted);font-size:24px">→</div>'
    f'<div><div class="lab">Sale (intento 1)</div><div class="shot">{img(RUN / att[0]["image"], 900)}</div></div>'
    "</div>"
    '<div class="grid2" style="gap:26px;margin-top:18px">'
    + dec(None, f"<b>Hasta {CFG.furnish.max_image_products} productos en la imagen</b>: el modelo acepta 14 imágenes, la foto del cuarto y 13 más. Las piezas que sobran quedan solo en la lista de compra.")
    + dec(None, "<b>El modelo no salió de un experimento</b>: la comparación entre modelos de imagen quedó diseñada, sin correr.")
    + "</div>",
    "La segunda generación aumentada: la imagen sale de <b>las fotos de lo que se compra</b>, no de una descripción.",
    notes=f"Fase nueve, la imagen. Nano Banana 2, en modo edición: recibe la foto del ambiente, las fotos de los productos y el prompt. Cuesta {round(100 * gen['usd_per_image']['1K'])} centavos por intento. Acepta 14 imágenes, así que muestra hasta {CFG.furnish.max_image_products} productos; el resto queda en la lista. El modelo no lo elegimos con un experimento: esa comparación quedó sin correr.",
    mins=0.4,
    foot=pie("publica-loft-industrial"),
)

# -- Fase 10: el control: una corrida que pasa y una que no
rc = CFG.furnish.room_check
cla_best = next(a for a in CLA_IMG["attempts"] if a["image"] == CLA_IMG["room_check"]["image"])
cla_k = [a["image"] for a in CLA_IMG["attempts"]].index(cla_best["image"]) + 1
no_pasan = len(FINALES) - IMG_TOT["pasan"]
# lo que cuentan la lámina y su nota: una corrida que pasa al primer intento, otra que no pasa en ninguno
assert att[0]["ok"] and not any(a["ok"] for a in CLA_IMG["attempts"]), "las corridas de la fase 10 cambiaron: revisar la lámina"
assert IMG_TOT["pasan"] == IMG_TOT["pasan_al_primero"], "alguna corrida final pasó el control al reintentar: revisar la fase 10 y la lámina de la imagen"


def shot(path: Path, badge: str, kind: str, cap: str) -> str:
    return f'<div><div class="shot">{img(path, 700)}<span class="badge {kind}">{badge}</span></div><div class="cap">{cap}</div></div>'


shots = [
    shot(RUN / "room.jpg", "original", "", "El loft, como lo mandó el usuario."),
    shot(RUN / att[0]["image"], "intento 1 · aceptado", "ok", f'<b>{att[0]["sift_inliers"]} puntos</b> reencontrados · cámara corrida {num(100 * att[0]["sift_desplazamiento_mediano"], 0)} %'),
    shot(CLA / "room.jpg", "original", "", "Otro pedido: un living clásico alrededor de la chimenea."),
    shot(CLA / cla_best["image"], f"intento {cla_k} · descartado", "no", f'<b>{cla_best["sift_inliers"]} puntos</b> · cámara corrida {num(100 * cla_best["sift_desplazamiento_mediano"], 0)} %: reencuadró hacia la chimenea'),
]
fase(
    "control",
    "¿Es el mismo cuarto? SIFT lo controla, y si no, reintenta",
    f'<div class="grid4" style="gap:12px">{"".join(shots)}</div>'
    '<div class="grid2" style="margin-top:14px;gap:30px">'
    + dec(None, f"<b>SIFT + RANSAC</b> entre la foto original y la generada: se acepta si reencuentra al menos <b>{int(rc['min_inliers'])} puntos</b> del cuarto y la cámara se movió como mucho <b>{num(100 * rc['max_shift'], 0)} % del ancho</b> (umbrales puestos a mano). Si no, se genera otra, <b>hasta {int(rc['attempts'])}</b>; si ninguna pasa, se entrega la que mejor conserva el cuarto, marcada.")
    + dec(None, f"<b>En las {len(FINALES)} corridas de la configuración final</b>: {IMG_TOT['pasan']} pasan, todas al primer intento. En las otras {no_pasan} fallaron los {int(rc['attempts'])} intentos: el modelo vuelve a mover la cámara o a rehacer el cuarto.")
    + "</div>",
    "El control detecta cuando el modelo rehace el cuarto. <b>Reintentar con el mismo prompt pocas veces lo arregla.</b>",
    notes=f"Fase diez, el control. Comparamos la foto original con la generada con SIFT y RANSAC: si reencuentra al menos {int(rc['min_inliers'])} puntos del cuarto y la cámara casi no se movió, se acepta; si no, se genera otra, hasta {int(rc['attempts'])} veces. Los umbrales están puestos a mano. El loft pasó al primer intento. Este otro pedido, un living clásico, no: el modelo reencuadró hacia la chimenea en los tres intentos, y se entrega el mejor, marcado. En las {len(FINALES)} corridas finales pasan {IMG_TOT['pasan']}, todas al primer intento; en las otras {no_pasan} fallaron los tres. El control detecta; reintentar pocas veces arregla.",
    mins=0.75,
    foot=pie("publica-loft-industrial", "publica-living-clasico"),
)

# -- Fase 11: lo que sale
rows_list = [
    f'<div style="display:grid;grid-template-columns:46px 1fr auto;gap:12px;align-items:center;padding:4px 0;border-top:1px solid var(--grid)">'
    f'<div class="th" style="width:46px;height:40px">{img(h["photos"][0], 110, alt="")}</div>'
    f'<div style="font-size:14.5px">{esc(type_line(h["description"]))}<span style="color:var(--muted);font-family:var(--mono);font-size:11.5px;margin-left:8px">{h["id"]}</span></div>'
    f'<div style="font-size:14.5px;font-weight:650">×{q}</div></div>'
    for h, q, _ in run_picks
]
run_abo = sum(h["id"].startswith("abo-") for h, *_ in run_picks)
cost_claude = RUN_PLAN["cost_usd"] + RUN_CHOICE["cost_usd"]
cost_img = RUN_IMG["cost_usd"]
fase(
    "salida",
    "Sale la lista de compra y el ambiente amoblado",
    '<div class="row" style="gap:30px">'
    f'<div style="width:520px"><div class="lab">La lista: {len(rows_list)} productos del catálogo ({run_abo} de Amazon, {len(rows_list) - run_abo} de IKEA)</div>{"".join(rows_list)}</div>'
    '<div class="grow"><div class="lab">El mismo ambiente, con esos productos</div>'
    f'<div class="grid2" style="gap:8px">{img(RUN / "room.jpg", 700, cls="photo")}{img(RUN / "final.png", 700, cls="photo")}</div>'
    f'<p class="small" style="margin-top:10px;font-size:14.5px">Este pedido: US${num(cost_claude)} de Claude (plan y elección) y US${num(cost_img)} de la imagen ({len(att)} intento{"s" if len(att) > 1 else ""}). '
    "Cada fase deja su archivo en la carpeta de la corrida (<code>1_searches.json</code> a <code>5_image.json</code>) y la webapp muestra cada paso mientras se hace.</p></div>"
    "</div>",
    "Cada producto de la lista es un id real del catálogo: el código <b>rechaza cualquiera que la búsqueda no haya traído</b>.",
    notes=f"Y fase once, lo que sale: la lista de compra, con productos reales y cuántos de cada uno, acá {run_abo} de Amazon y {len(rows_list) - run_abo} de IKEA, y la foto del mismo ambiente con ellos. Este pedido costó unos {round(100 * cost_claude)} centavos de Claude y {round(100 * cost_img)} de la imagen. Cada fase deja su archivo en la carpeta de la corrida.",
    mins=0.4,
    foot=pie("publica-loft-industrial"),
)


# ================================================================================================
# Los desafíos
# ================================================================================================
def imagen_contra_texto() -> dict:
    """La búsqueda de la propuesta original (por imagen: el recorte de cada mueble contra las fotos
    del catálogo, DINOv3) contra la búsqueda por texto, con el mismo ground truth y la misma
    unidad: el producto anotado de cada ambiente, sobre el catálogo de 275 de ese momento.
    recall@1 de cada una y la diferencia pareada con su IC 95% (bootstrap de ambientes)."""
    from amoblai.evaluation.metrics import bootstrap_ci

    v0_dir = R / "v0_imagen" / "corridas" / "20261006-231131_retriever_abl-retriever-name-dinov3__method-none__category_filter-true"
    v0 = {(r["room_id"], r["sku"]): r["best_rank"] for r in jsonl(v0_dir / "items.jsonl")}
    v1: dict[tuple, int | None] = {}
    for r in rankings(R / "evaluacion" / "20261021-133226_ablacion-texto")["qwen3|description|filtro-type"]:
        for sku in r["relevant"]:
            pos = r["ranked"].index(sku) + 1 if sku in r["ranked"] else None
            k = (r["room_id"], sku)
            v1[k] = pos if v1.get(k) is None else (v1[k] if pos is None else min(v1[k], pos))
    keys = sorted(v0)
    a = [float(v0[k] is not None and v0[k] <= 1) for k in keys]
    b = [float(v1.get(k) is not None and v1[k] <= 1) for k in keys]
    d = [y - x for x, y in zip(a, b, strict=True)]
    ic95 = bootstrap_ci(d, [k[0] for k in keys], n_samples=4000)  # 4.000 remuestreos, como el recálculo de la revisión
    return {"n": len(keys), "imagen": statistics.mean(a), "texto": statistics.mean(b), "dif": statistics.mean(d), "ic": ic95}


def dos_flujos() -> str:
    """La propuesta aprobada (generar, recortar y buscar por imagen) y lo que quedó."""
    rows = [
        ("La propuesta aprobada", "buscar por imagen", False, [
            ("Foto + pedido", ""),
            ("Generar una imagen", "con muebles inventados"),
            ("Recortar cada mueble", "Grounding DINO + SAM"),
            ("Buscar el más parecido", "por imagen (DINOv3)"),
            ("Lista de compra", "lo que más se parezca"),
        ]),
        ("Lo que quedó", "RAG por texto", True, [
            ("Foto + pedido", ""),
            ("Plan", "una ficha por pieza"),
            ("Búsqueda", "en el catálogo descripto"),
            ("Elección: la lista", "productos reales"),
            ("Imagen", "al final, con ellos"),
        ]),
    ]
    x0, cw, gap, ch = 196, 176, 17, 54
    out = ['<svg class="pipe" viewBox="0 0 1160 152" width="1160" role="img">']
    for j, (name, sub, now, chips) in enumerate(rows):
        y = 8 + j * 80
        color = "var(--accent)" if now else "var(--line)"
        dash = "" if now else ' stroke-dasharray="5 4"'
        out.append(f'<text x="0" y="{y + 24}" font-size="16" font-weight="700" fill="var(--ink)">{esc(name)}</text>')
        out.append(f'<text x="0" y="{y + 42}" font-size="12.5" fill="{"var(--accent)" if now else "var(--muted)"}">{esc(sub)}</text>')
        for i, (t, s) in enumerate(chips):
            x = x0 + i * (cw + gap)
            out.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="10" fill="var(--card)" stroke="{color}" stroke-width="{1.5 if now else 1.2}"{dash}/>')
            out.append(f'<text x="{x + 12}" y="{y + (23 if s else 32)}" font-size="13.5" font-weight="650" fill="var(--ink)">{esc(t)}</text>')
            if s:
                out.append(f'<text x="{x + 12}" y="{y + 41}" font-size="11.5" fill="var(--muted)">{esc(s)}</text>')
            if i:
                out.append(f'<line x1="{x - gap + 2}" y1="{y + ch / 2}" x2="{x - 4}" y2="{y + ch / 2}" stroke="var(--muted)" stroke-width="1.4"/>' + arrowhead(x - 3, y + ch / 2, x - 16, y + ch / 2, 6))
    out.append("</svg>")
    return "".join(out)


VT = imagen_contra_texto()
slide(
    dos_flujos()
    + '<div class="row" style="gap:40px;margin-top:16px">'
    '<div style="width:520px"><div class="lab">Lo que medimos antes de cambiar: su buscador</div>'
    + hbars(
        [
            {"label": "por imagen (recorte)", "value": VT["imagen"]},
            {"label": "por texto (descripción)", "value": VT["texto"], "hl": True, "note": f'{sg(VT["dif"], 2)} {ic(*VT["ic"], d=2)}'},
        ],
        width=520,
        label_w=176,
        row_h=36,
        pad_r=176,
    )
    + f'<p class="small" style="font-size:14.5px;margin-top:6px">Encontrar primero el producto anotado, con el mismo ground truth y la misma unidad ({VT["n"]} productos anotados, catálogo de 275). Y por texto hace falta <b>una generación de imagen menos</b> por pedido.</p></div>'
    '<div class="grow"><div class="lab">Otros tres</div>'
    + dec(None, f"<b>El catálogo traía fotos equivocadas</b>: 36 productos de IKEA con la foto de otro producto o de otra medida, o que no eran de living. La lista diría una cosa y la imagen mostraría otra: se revisó mirando cada foto (de 855 quedaron {len(ITEMS)}).")
    + dec(None, "<b>No hay ground truth de la tarea real</b>: nadie anotó la lista ideal para un ambiente vacío. Hay uno para la búsqueda y, para el flujo entero, un juez que compara listas.")
    + dec(None, f"<b>El modelo de imagen rehace el cuarto</b>: mueve la cámara, inventa una ventana. Edición estricta y un control automático; aun así, {no_pasan} de {len(FINALES)} no se conservan.")
    + "</div></div>"
    '<div class="take">Cambiamos la arquitectura con una medición de su buscador. La versión por imagen <b>nunca corrió de punta a punta</b>: comparamos buscadores, no sistemas.</div>',
    kicker="Desafíos",
    title="De buscar por imagen a RAG por texto, y otros tres desafíos",
    notes=f"Los desafíos. El más grande fue cambiar la arquitectura que nos aprobaron. La propuesta era generar primero una imagen amoblada, recortar cada mueble y buscar en el catálogo el más parecido, por imagen. Construimos y medimos su buscador sobre el mismo ground truth: encontraba primero el {num(100 * VT['imagen'], 0)} por ciento de los productos anotados, contra {num(100 * VT['texto'], 0)} buscando por texto. Con eso, y con una generación de imagen menos por pedido, cambiamos a RAG por texto. Ojo: esa versión nunca corrió de punta a punta; comparamos buscadores, no sistemas. Los otros tres: el catálogo traía fotos de otro producto y hubo que revisarlo a mano; no hay ground truth de la tarea real; y el modelo de imagen rehace el cuarto.",
    mins=0.9,
)

# ================================================================================================
# Parte 2: cómo evaluamos
# ================================================================================================
section(
    "Parte 2",
    "Cómo evaluamos",
    "Dos bancos de prueba: ambientes de IKEA con sus productos anotados (hay ground truth: mide la búsqueda) y ambientes vacíos reales (no lo hay: un juez y métricas de la imagen). Qué mide cada número, y cuánto creerle.",
    notes="Antes de los experimentos, cómo evaluamos: qué mide cada número y cuánto creerle.",
)

# los datos de evaluación: el ground truth y los ambientes vacíos
gt_room = "datos/dataset/ikea/images/room_scenes"
scene = next(iter(sorted((ROOT / gt_room).glob("*living*"))), None) or next(iter(sorted((ROOT / gt_room).glob("*"))))
shown = [r for r in AMBIENTES if (ROOT / r["foto"]).exists()][:12]
thumbs = "".join(f'<div>{img(r["foto"], 260, cls="photo")}</div>' for r in shown)
credits = credito(*[r["slug"] for r in shown if r["foto"] in PUB])
nr, npub = len(AMBIENTES), sum(r["foto"] in PUB for r in AMBIENTES)
slide(
    '<div class="row" style="gap:34px">'
    '<div style="width:540px"><h3>Con ground truth: la búsqueda</h3>'
    f'<div class="fix h180">{img(scene, 900, cls="photo")}</div>'
    '<ul class="small" style="margin-top:10px;font-size:15px">'
    f"<li><b>{N_AMB} ambientes</b> de living y comedor de IKEA con sus productos anotados (de invertir <code>item_to_room</code>).</li>"
    f"<li>Por cada mueble visible, un subagente escribe la consulta como la escribiría el plan, sin ver el catálogo: <b>{N_BUS} consultas</b>, {N_ANS} con su producto en el catálogo de {len(ITEMS)}.</li>"
    "<li>Es un banco de <b>producto conocido</b>: quien escribe la consulta está viendo el mueble. Mide el índice, no la recomendación.</li></ul></div>"
    f'<div class="grow"><h3>Sin ground truth: el flujo entero</h3><div class="fix h70" style="display:grid;grid-template-columns:repeat(6,1fr);gap:6px">{thumbs}</div>'
    '<ul class="small" style="margin-top:10px;font-size:15px">'
    f"<li><b>{nr} ambientes vacíos reales</b>: {nr - npub} nuestros y {npub} públicos (Wikimedia Commons y Flickr), elegidos de {len(PUB)} revisados uno por uno; cada uno con un pedido como el de un usuario.</li>"
    "<li>Un juez (Opus) compara a ciegas las listas de dos configuraciones, <b>en los dos órdenes</b>: una gana un ambiente solo si gana en los dos.</li>"
    "<li>La imagen se mide aparte: si muestra esos productos, y si sigue siendo ese cuarto.</li></ul>"
    f'<div class="tiny" style="margin-top:4px">Fotos públicas: {credits}.</div></div>'
    "</div>"
    '<div class="take">Dos bancos, dos preguntas: con ground truth se mide <b>el índice</b>; con el juez, <b>la lista</b>.</div>',
    kicker="Cómo evaluamos · los datos",
    title="Ambientes IKEA anotados y ambientes vacíos reales",
    notes=f"Usamos dos bancos de prueba, que miden cosas distintas. Para la búsqueda, {N_AMB} ambientes de IKEA con sus productos anotados. Por cada mueble visible, un subagente escribió la consulta como la escribiría el plan, sin ver el catálogo: {N_BUS} consultas, {N_ANS} con su producto en el catálogo. Es un banco de producto conocido: quien escribe está viendo el mueble, así que mide el índice, no la recomendación. Para el flujo entero, {nr} ambientes vacíos reales, cada uno con su pedido: ahí no hay ground truth, y un juez compara a ciegas las listas de dos configuraciones, en los dos órdenes.",
    mins=0.75,
)

# las métricas del buscador, con el valor de hoy
corr_cp = statistics.correlation([v["mrr@10"] for v in ABL.values()], [v["context_precision@10"] for v in ABL.values()])
slide(
    '<div class="grid3 metric">'
    '<div class="card"><h3>hit@k</h3><p class="small">¿El producto anotado está entre los k primeros? <b>hit@5 es el titular</b>: son los 5 candidatos que ve el que elige.</p>'
    f'<div class="val">hit@1 <b>{num(B2["hit@1"], 3)}</b> · hit@5 <b>{num(B2["hit@5"], 3)}</b></div><p class="tiny">Versión 1: {num(B1["hit@1"], 3)} y {num(B1["hit@5"], 3)}. Al azar dentro del kind, hit@1 {num(B2["azar_hit@1"])}.</p></div>'
    '<div class="card"><h3>Diferencia pareada</h3><p class="small">Dos métodos sobre <b>las mismas consultas</b>: la diferencia media y su IC 95 %. Si el intervalo no toca el cero, no es ruido.</p>'
    f'<div class="val">{nb(dif(D21))}</div><p class="tiny">hit@1 de la versión 2 menos la versión 1. Mirar el intervalo de cada método por separado engaña.</p></div>'
    '<div class="card"><h3>IC 95 % por bootstrap</h3><p class="small">Se remuestrean <b>ambientes</b>, no consultas: las consultas de un mismo ambiente no son independientes.</p>'
    f'<div class="val">hit@1 <b>{num(B2["hit@1"], 3)}</b> {ic(*ci(B2), d=2)}</div><p class="tiny">{N_ANS} consultas con respuesta, de {N_AMB_ANS} ambientes.</p></div>'
    '<div class="card"><h3>MRR@10</h3><p class="small">La media de 1 / posición del anotado: 1 si es el 1.º, ½ si es el 2.º, 0 si no está en el top-10.</p>'
    f'<div class="val"><b>{num(B2["mrr@10"], 3)}</b></div><p class="tiny">Versión 1: {num(B1["mrr@10"], 3)}.</p></div>'
    '<div class="card"><h3>Context precision@10 y NDCG@10</h3><p class="small">Las de la clase: cuán arriba quedan los relevantes. Con uno o dos relevantes por consulta, repiten al MRR.</p>'
    f'<div class="val"><b>{num(B2["context_precision@10"])}</b> y <b>{num(B2["ndcg@10"])}</b></div><p class="tiny">Correlación con el MRR sobre {len(ABL)} configuraciones: más de {num(int(corr_cp * 100) / 100)}.</p></div>'
    '<div class="card"><h3>Context recall</h3><p class="small">De los productos anotados de un ambiente, cuántos aparecen entre los k candidatos de sus consultas. Es <b>por ambiente</b>.</p>'
    f'<div class="val"><b>{num(B2["context_recall@3"])}</b> con k = 3 · <b>{num(B2["context_recall@10"])}</b> con k = 10</div></div>'
    "</div>"
    '<div class="take">Los valores son los de la búsqueda del flujo de hoy (versión 2), sobre el ground truth de IKEA.</div>',
    kicker="Cómo evaluamos · el retriever",
    title="El buscador: ¿trae el producto anotado, y arriba?",
    mins=0.75,
    notes=f"Las métricas del buscador, con el valor de hoy. hit@k: si el producto anotado está entre los k primeros. El titular es hit@5, porque son los cinco candidatos que ve el que elige: {num(B2['hit@5'], 3)}. Para comparar dos métodos usamos la diferencia pareada: las mismas consultas, la diferencia media y su intervalo de 95 por ciento, por bootstrap de ambientes. Si no toca el cero, no es ruido. Mirar el intervalo de cada método por separado nos había hecho leer mejoras que eran ruido. Las de la clase, context precision y NDCG, acá repiten al MRR; context recall es por ambiente.",
)

# las métricas del generador y los jueces
fid = [x["fidelidad"]["faithfulness"] for x in RESP["por_corrida"]]
_madera = re.compile(r"\b(ash|birch|oak|beech|pine|walnut)\b", re.I)  # la especie, que es lo que más se repite
no_sost = [x for r in RESP["por_corrida"] for x in r["fidelidad"]["no_sostenidas"] if _madera.search(x)][:2]
F, AR = RESP["faithfulness"], RESP["answer_relevance"]
gt_agree = GRAD["acuerdo_con_gt"]


def acuerdo(j: dict) -> str:
    """En cuántos ambientes los dos órdenes del juez votaron lo mismo."""
    return f'{sum(d["votos"][0] == d["votos"][1] for d in j["detalle"])} de {len(j["detalle"])}'


slide(
    '<div class="row" style="gap:28px">'
    '<div style="width:548px;display:grid;gap:14px" class="metric">'
    f'<div class="card"><h3>Faithfulness del porqué</h3><div class="row center" style="gap:16px"><div class="big">{num(F["global"])}</div>'
    f'<p class="small" style="margin:0"><b>{F["sostenidas"]} de {F["afirmaciones"]}</b> afirmaciones se infieren de lo que vio el generador: el pedido, la foto del cuarto y, de cada producto, su foto y una línea con su tipo y su medida.</p></div>'
    f'<p class="tiny" style="margin-top:8px">Por lista, de {num(min(fid))} a {num(max(fid))}. Lo que no se sostiene es casi siempre <b>la especie de la madera</b>, que afirma sin verla escrita: <i>“{esc(no_sost[0])}”</i>, <i>“{esc(no_sost[1])}”</i>.</p></div>'
    f'<div class="card"><h3>Answer relevance</h3><div class="row center" style="gap:16px"><div class="big">{num(AR["media"])}</div>'
    '<p class="small" style="margin:0">Un juez que no ve el pedido escribe tres pedidos que la lista contesta; se mide su coseno con el pedido original.</p></div>'
    f'<p class="tiny" style="margin-top:8px">La vara: los pedidos que el juez escribió para <b>otras</b> listas dan <b>{num(AR["vara_cruzada"])}</b> (la propia les gana en {AR["supera_a_la_cruzada"]} de {RESP["corridas"]}); pedidos sin relación, {num(AR["vara_contrastes"])}.</p></div>'
    f'<p class="tiny" style="margin:-4px 0 0">Las dos, sobre las {RESP["corridas"]} listas de la versión 2. Sobre otras {RESP1["corridas"]} listas (con la búsqueda de la versión 1) dan {num(RESP1["faithfulness"]["global"])} y {num(RESP1["answer_relevance"]["media"])} contra {num(RESP1["answer_relevance"]["vara_cruzada"])}: los dos números se repiten.</p>'
    "</div>"
    '<div class="grow">'
    + prompt_card(
        "juez_pedidos_v1.md",
        ['A furnishing app takes a photo of a room and a request in Spanish ([["un living nórdico y cálido"]], "un comedor para seis") and answers with a shopping list of products'],
        note="el juez de antes · extracto",
    )
    + '<div style="margin-top:12px">'
    + dec(None, f'<b>Data leakage.</b> Ese ejemplo era, palabra por palabra, el comienzo del pedido que se evaluaba: el juez lo copiaba. Y el juez de fidelidad leía la ficha completa, que el generador no ve. Daban {DOC["generador_v1"][0]} y {DOC["generador_v1"][1]}; los rehicimos sin el ejemplo y con el contexto real.')
    + dec(None, f"<b>Validado contra el ground truth, un juez</b>: el de relevancia graduada le da la nota máxima al producto anotado el {num(100 * gt_agree['anotado_con_2'], 0)} % de las veces, y a los demás el {num(100 * gt_agree['otros_con_2'], 0)} %.")
    + dec(None, f"<b>El juez de listas</b> no está validado contra personas: se le pregunta en los dos órdenes, y coinciden en {acuerdo(JA)} ambientes contra el azar, en {acuerdo(JC)} entre catálogos y en {acuerdo(JV)} entre versiones. Con la misma configuración dos veces reparte {jr['hibrida']['gana']} a {jr['hibrida_bis']['gana']}.")
    + "</div></div></div>"
    '<div class="take">El porqué se sostiene en <b>casi 9 de cada 10 afirmaciones</b>; lo que agrega de más es la madera. Y la lista responde a su pedido más que a los ajenos.</div>',
    kicker="Cómo evaluamos · el generador y los jueces",
    title=f"El generador: faithfulness {num(F['global'])} y answer relevance {num(AR['media'])}",
    mins=0.95,
    notes=f"El generador es el paso que elige y explica. Faithfulness: partimos el porqué en afirmaciones, y un juez dice cuáles se infieren de lo que el generador vio. Da {num(F['global'])}: {F['sostenidas']} de {F['afirmaciones']}. Lo que no se sostiene es casi siempre la especie de la madera, que afirma sin verla escrita. Answer relevance: un juez que no ve el pedido escribe los pedidos que esa lista contesta. Da {num(AR['media'])}, contra {num(AR['vara_cruzada'])} con pedidos escritos para otras listas. Estas métricas las rehicimos, y es una historia de data leakage: el prompt del juez traía de ejemplo “un living nórdico y cálido”, que era justo como empezaba el pedido evaluado, y lo copiaba. Y sobre los jueces: validado contra el ground truth hay uno solo; el de listas se controla con los dos órdenes.",
)


# la imagen: las 11 corridas de la configuración final
def pares_producto() -> str:
    """Cada producto de la lista del recorrido: su foto del catálogo, su recorte en la imagen
    generada y el puesto del producto entre los de su tipo (6_metricas_imagen.json)."""
    cells = []
    for (h, *_), p in zip(run_picks, RUN_MET["productos"], strict=True):
        assert h["id"] == p["id"]
        cat = f'<div class="th">{img(h["photos"][0], 150, alt="")}</div>'
        if p["detectado"]:
            ok = p["puesto"] == 1
            cells.append(
                f'<div class="par">{cat}<div class="th">{recorte(RUN / "final.png", p["box"], 150)}</div>'
                f'<div class="r{" ok" if ok else ""}">{p["puesto"]}.º de {p["entre"]}</div></div>'
            )
        else:
            cells.append(f'<div class="par">{cat}<div class="th vacio"></div><div class="r">no detectado</div></div>')
    return f'<div class="pares" style="grid-template-columns:repeat({len(cells)},1fr)">{"".join(cells)}</div>'


fin_th = "".join(
    f'<div class="shot">{img(f["dir"] / "final.png", 320)}<span class="badge {"ok" if f["img"]["room_check"]["ok"] else "no"}">'
    f'{"pasa" if f["img"]["room_check"]["ok"] else "no pasa"} · {sum(p.get("puesto") == 1 for p in f["met"]["productos"])} de {len(f["met"]["productos"])}</span></div>'
    for f in FINALES
)
run_rec = sum(p.get("puesto") == 1 for p in RUN_MET["productos"])
slide(
    '<div class="row" style="gap:30px">'
    '<div style="width:520px"><div class="lab">¿Son esos productos? En el loft: catálogo, recorte y puesto</div>'
    + pares_producto()
    + f'<p class="small" style="font-size:14.5px;margin-top:10px">Se detecta cada mueble en la imagen, se recorta y se compara con las fotos del catálogo de su tipo (DINOv3): <b>reconocido</b> si el más parecido es el de la lista. Acá, {run_rec} de {len(RUN_MET["productos"])}.</p>'
    '<div class="row center" style="gap:14px;margin-top:6px">'
    f'<div class="big" style="font-size:46px;white-space:nowrap">{IMG_TOT["reconocidos"]} de {IMG_TOT["productos"]}</div>'
    f'<div class="bignote" style="margin:0">productos reconocidos como el exacto ({num(100 * IMG_TOT["reconocidos"] / IMG_TOT["productos"], 0)} %) en las {len(FINALES)} imágenes; aparecen {IMG_TOT["detectados"]}. Coseno medio {num(IMG_TOT["coseno"])}.</div></div></div>'
    f'<div class="grow"><div class="lab">¿Es ese cuarto? Las {len(FINALES)} imágenes: control · productos reconocidos</div>'
    f'<div class="fines">{fin_th}'
    f'<div class="resumen"><div class="big" style="font-size:40px;white-space:nowrap">{IMG_TOT["pasan"]} de {len(FINALES)}</div><div class="bignote">conservan el cuarto, todas al primer intento</div></div></div>'
    f'<div class="tiny" style="margin-top:6px">Fotos públicas: {credito(*[f["slug"] for f in FINALES if FOTO[f["slug"]] in PUB])}.</div></div>'
    "</div>"
    '<div class="take">La lista es confiable; la imagen es una visualización: acierta el producto exacto <b>4 de cada 10 veces</b> y conserva el cuarto <b>2 de cada 3</b>.</div>',
    kicker="Cómo evaluamos · la imagen",
    title=f"La imagen: {IMG_TOT['reconocidos']} de {IMG_TOT['productos']} productos reconocidos, {IMG_TOT['pasan']} de {len(FINALES)} cuartos",
    mins=0.8,
    notes=f"La imagen la medimos sobre las {len(FINALES)} corridas finales, no sobre la mejor. Primero: ¿son esos productos? Detectamos cada mueble, lo recortamos y lo comparamos con las fotos del catálogo de su tipo: reconocido, si el más parecido es el de la lista. En el loft, el sofá, la biblioteca y la lámpara salen primeros; la alfombra, no. En total se reconocen {IMG_TOT['reconocidos']} de {IMG_TOT['productos']}, el {num(100 * IMG_TOT['reconocidos'] / IMG_TOT['productos'], 0)} por ciento, aunque aparecen {IMG_TOT['detectados']}. Segundo: ¿es ese cuarto? El control pasa en {IMG_TOT['pasan']} de {len(FINALES)}. O sea: la lista es confiable; la imagen es una visualización, que acierta el producto exacto cuatro de cada diez veces.",
)

# las trampas, dichas en voz alta
cos_banco = statistics.median(r["scores"][0] for r in rankings(HIB_DIR)[V1] if r["relevant"] and r["scores"])
cos_flujo = sorted(DIAG_CAT[v]["puntaje_del_primero"]["mediana"] for v in ("ikea", "todos"))
bm = EMB["bm25|description|filtro-kind"]
slide(
    '<div class="grid2 metric" style="gap:16px 20px">'
    '<div class="card"><h3>El banco de la búsqueda es de producto conocido</h3>'
    f'<p class="small">Quien escribió la consulta veía el mueble: mide identificar un producto, no recomendar. En el flujo real el plan lo imagina, y sus consultas quedan más lejos del catálogo: el coseno del primer candidato es {num(cos_flujo[0])}–{num(cos_flujo[1])}, contra {num(cos_banco, 3)} en el banco.</p></div>'
    '<div class="card"><h3>El mismo modelo escribe los dos lados</h3>'
    f'<p class="small">Consultas y descripciones salen del mismo modelo, con el mismo molde de 8 líneas. Por eso contar palabras rinde casi como el embedder (BM25: {num(bm["hit@1"], 3)} contra {num(B1["hit@1"], 3)}). Representa al sistema, porque el plan también es Claude; no a alguien que escribe con otras palabras.</p></div>'
    '<div class="card"><h3>No hay conjunto apartado</h3>'
    f'<p class="small">Todo se eligió y se reporta sobre los mismos {N_AMB_ANS} ambientes. Las diferencias grandes se sostienen igual; las de 2 puntos no las leemos como señal.</p></div>'
    f'<div class="card"><h3>De punta a punta son {len(AMBIENTES)} ambientes</h3>'
    f'<p class="small">El juez es el mismo modelo que elige. Con la misma configuración corrida dos veces, el que elige cambia {ruido_cambian} de {ruido_total} productos y el juez reparte {jr["hibrida"]["gana"]} a {jr["hibrida_bis"]["gana"]}: un ambiente ganado no dice nada solo, cuenta la asimetría. El pedido abierto (“un living nórdico y cálido”) no está evaluado.</p></div>'
    "</div>"
    '<div class="take">El ground truth sirve para comparar cambios grandes del índice. Lo que le sirve al usuario lo dice el juez, con n = 11.</div>',
    kicker="Cómo evaluamos · cuánto creerle",
    title="Las trampas, dichas en voz alta",
    mins=0.65,
    notes=f"Y las trampas, dichas en voz alta. Uno: el banco de la búsqueda es de producto conocido; en el flujo real el plan imagina el producto, no lo ve. Dos: el mismo modelo escribe las consultas y las descripciones, con el mismo molde; por eso contar palabras rinde casi como el embedder. Tres: no hay conjunto apartado. Y cuatro: de punta a punta son {len(AMBIENTES)} ambientes y el juez es el mismo modelo que elige; con la misma configuración corrida dos veces reparte tres a tres, así que lo que cuenta es la asimetría. Por eso leemos las diferencias grandes, y las de dos puntos, no.",
)


# ================================================================================================
# Parte 3: los experimentos, por su ranking (docs/REVISION.md, sección 4)
# ================================================================================================
section(
    "Parte 3",
    "Experimentos",
    "Por cuánto importan: ocho con lámina propia (por qué, qué se comparó, el resultado con su diferencia pareada y la decisión), el camino incremental que los resume y, juntos, los de trámite.",
    notes="Ahora los experimentos, por cuánto importan. Los que sostienen una decisión tienen su lámina; los de trámite van juntos al final.",
    mins=0.15,
)

# -- El mapa de los experimentos
EXPS = [
    (1, "Qué se indexa", "texto del vendedor · descripción desde la foto"),
    (2, "Cómo se escribe la consulta", "la ficha · la frase natural · Type · kind"),
    (3, "Léxica, por foto e híbrida", "Qwen3 · BM25 · SigLIP 2 · fusionadas"),
    (4, "¿Error, o una variante?", "exacto · el mismo modelo · sirve (juez)"),
    (5, "Elegir con un VLM, y cuántos", "top-10 mirando las fotos · k de 1 a 10"),
    (6, "Qué catálogo", "IKEA · ABO · los dos (juez)"),
    (7, "Con búsqueda o sin búsqueda", "los 5 mejores · 5 al azar · todo el catálogo (juez)"),
    (8, "Tres redactores", "las mismas consultas, escritas tres veces"),
    (9, "Embedder", "hashing · BM25 · BGE · Qwen3"),
    (10, "Dimensión del vector", "de 32 a 1.024 (Matryoshka)"),
    (11, "Splitting y líneas", "documento · por línea · qué líneas pesan"),
    (12, "Base vectorial", "ChromaDB (HNSW) · búsqueda exacta"),
    (13, "Filtros de metadata", "ninguno · por tipo · por kind"),
    (14, "Rerankers de texto", "MiniLM · Qwen3-Reranker"),
    (15, "La escena", "plantilla · escrita por el LLM"),
]
assert {n for ns in PINES.values() for n in ns} | set(BANCO) == {n for n, *_ in EXPS}
assert {n for n, *_ in EXPS if n > 8} == TRAMITE
legend = "".join(f'<div class="li">{pin_inline(n, 20)}<b>{esc(t)}</b><span>{esc(v)}</span></div>' for n, t, v in EXPS[:8])  # 8 filas: pines más chicos
legend2 = "".join(f'<div class="li">{pin_inline(n, 20)}<b>{esc(t)}</b><span>{esc(v)}</span></div>' for n, t, v in EXPS[8:])
slide(
    pipeline(pins=True, banco=f"{N_AMB} ambientes de IKEA anotados, {N_ANS} consultas con respuesta: el 4 y el 8 miden cuánto creerle a su número")
    + f'<div class="legend" style="margin-top:10px"><div>{legend}</div><div>{legend2}</div></div>'
    + '<div class="take">Pin hueco: de trámite. <b>Sin experimento: el modelo de imagen y los umbrales del control.</b></div>',
    kicker="Experimentos · el mapa",
    title="Quince experimentos: ocho con lámina propia, siete de trámite",
    notes="El mismo mapa, con los experimentos encima: cada pin es una pregunta que le hicimos a una parte del sistema. Los llenos, del 1 al 8, tienen lámina propia. Dos de ellos, el 4 y el 8, no miden una fase: miden al banco de prueba. Los huecos, del 9 al 15, son los de trámite: embedder, dimensión, splitting, base vectorial, filtros, rerankers de texto y la escena. Y dos cosas no las decidió ningún experimento: el modelo de imagen y los umbrales del control.",
    mins=0.65,
)

# -- 1: qué se indexa
K_NAIVE, K_DESC = "qwen3|seller-full|filtro-none|consulta-piece", "qwen3|description|filtro-none|consulta-piece"
n1, n2 = CAM[K_NAIVE], CAM[K_DESC]
d_idx = n2["vs_anterior"]
d_ficha = paired(ABL_DIR, "qwen3|description|filtro-none", "qwen3|seller|filtro-none")  # lo mismo, con la consulta escrita como ficha
d_name = paired(ABL_DIR, "qwen3|name+description|filtro-kind", V1)
experiment(
    "1",
    "Qué se indexa",
    "Alcanza con el texto del vendedor, o hay que describir cada producto?",
    '<ul class="small"><li><b>El texto del vendedor</b>: nombre, su tipo (“Easy chair”), colores y la frase de IKEA.</li>'
    "<li><b>La descripción desde la foto</b>: las 8 líneas que escribe el VLM.</li>"
    f"<li>Lo demás, fijo: Qwen3, sin filtro, la consulta en una frase corta sin reescribir, las mismas {N_ANS} consultas.</li></ul>"
    f'<div class="find" style="margin-top:14px">Describir cada producto casi triplica el acierto: <b>{nb(dif(d_idx))}</b> de hit@1, y hit@5 pasa de {num(n1["hit@5"])} a {num(n2["hit@5"])}. Con la consulta escrita como ficha la diferencia es mayor ({sg(d_ficha["hit@1"], 2)}): los dos cambios se potencian.</div>',
    hbars(
        [
            {"label": "vendedor · hit@1", "value": n1["hit@1"], "ci": ci(n1)},
            {"label": "descripción · hit@1", "value": n2["hit@1"], "ci": ci(n2), "hl": True, "note": dif(d_idx)},
            {"label": "vendedor · hit@5", "value": n1["hit@5"], "ci": ci(n1, "hit@5")},
            {"label": "descripción · hit@5", "value": n2["hit@5"], "ci": ci(n2, "hit@5"), "hl": True, "note": dif(d_idx, "hit@5")},
        ],
        width=590,
        label_w=160,
        pad_r=200,
    )
    + f'<div class="cap" style="max-width:590px">A la derecha, la diferencia pareada con su IC 95 %. Con el nombre comercial adelante (“NOLMYRA”), peor: {dif(d_name)} de hit@1.</div>',
    "<b>Decisión:</b> se indexa la descripción hecha desde la foto, no el texto del vendedor. Es un costo único, offline: US$0,007 por producto por la API.",
    fases=("descripcion",),
    why="El texto de IKEA casi no describe el producto (“The armchair is lightweight...”), y un usuario pide estilo, color y materiales: cosas que están en la foto, no en el texto.",
    notes={
        "motivo": "El texto de IKEA es una frase de marketing, y la gente pide estilo, color y materiales, que están en la foto. ¿Vale la pena describir cada producto?",
        "experimento": "Indexamos dos textos, con todo lo demás fijo: el texto del vendedor y la descripción de ocho líneas. La consulta, una frase corta sin reescribir, para medir un solo cambio.",
        "resultados": f"Con el texto del vendedor, hit@1 da {num(n1['hit@1'])}; con la descripción, {num(n2['hit@1'])}: casi el triple, y hit@5 pasa de {num(n1['hit@5'])} a {num(n2['hit@5'])}. La diferencia es pareada y su intervalo no toca el cero. Con la consulta escrita como ficha, la diferencia supera 0,4.",
        "decision": "Se indexa la descripción hecha desde la foto. Es el preprocesamiento que más pesa de todo el trabajo.",
    },
    mins=0.9,
)

# -- 2: cómo se escribe la consulta, contra no reescribirla
q_full, q_piece = CON[V1], CON[V1 + "|consulta-piece"]
q_type, q_kind = CON[V1 + "|consulta-type"], CON[V1 + "|consulta-kind"]
s_full, s_piece = CON["siglip2|description|filtro-kind"], CON["siglip2|description|filtro-kind|consulta-piece"]
d_q = q_piece["vs_base"]  # la frase natural menos la ficha
frases = [r["phrase"] for r in rankings(HIB_DIR)[V1] if r.get("phrase")]
experiment(
    "2",
    "Cómo se escribe la consulta",
    "Cuánto suma escribir la consulta como una ficha del catálogo, contra no reescribirla?",
    '<ul class="small"><li><b>La ficha</b>: las 8 líneas, como las escribe el plan.</li>'
    f"<li><b>La frase natural</b>, sin reescribir: como el redactor nombró la pieza (“{esc(frases[0])}”; {num(statistics.median(len(f.split()) for f in frases), 0)} palabras de mediana).</li>"
    "<li><b>Solo la línea Type</b> y <b>solo el kind</b>: el piso.</li>"
    "<li>Con el coseno del flujo (densa) y contra la foto del producto (SigLIP 2).</li></ul>"
    f'<div class="find" style="margin-top:12px">La ficha suma <b>{nb(dif(d_q, flip=True))}</b> de hit@1 sobre la frase sin reescribir. Y lo que no esperábamos: <b>contra la foto, la frase natural da {num(s_piece["hit@1"], 3)}</b>. El texto necesita que la consulta hable como el catálogo; la foto, casi no.</div>',
    hbars(
        [
            {"label": "densa · la ficha", "value": q_full["hit@1"], "ci": ci(q_full), "hl": True, "note": dif(d_q, flip=True)},
            {"label": "densa · la frase natural", "value": q_piece["hit@1"], "ci": ci(q_piece)},
            {"label": "densa · solo la línea Type", "value": q_type["hit@1"], "ci": ci(q_type)},
            {"label": "densa · solo el kind", "value": q_kind["hit@1"], "ci": ci(q_kind)},
            {"label": "por foto · la ficha", "value": s_full["hit@1"], "ci": ci(s_full)},
            {"label": "por foto · la frase natural", "value": s_piece["hit@1"], "ci": ci(s_piece), "hl": True, "note": dif(s_piece["vs_anterior"])},
        ],
        width=610,
        label_w=188,
        row_h=30,
        pad_r=200,
    )
    + '<div class="cap">hit@1. A la derecha, la diferencia pareada contra la otra forma de escribir la consulta.</div>',
    "<b>Decisión:</b> el plan escribe la ficha: es la técnica de Advanced RAG del flujo. Antes la comparábamos con “solo el kind”, que es azar por construcción (buscar “rug” entre 89 alfombras): eso no medía reescribir.",
    fases=("plan",),
    why="El plan no busca con el pedido: escribe el producto ideal en las 8 líneas del catálogo (respuesta hipotética, HyDE). Cuesta tokens en cada pedido, y no lo habíamos medido contra no hacerlo.",
    notes={
        "motivo": "El plan no busca con el pedido: escribe el producto ideal en las ocho líneas del catálogo. Es la técnica de Advanced RAG del flujo, y no la habíamos medido contra no hacerla: la comparábamos con buscar solo con el nombre del kind, que es azar por construcción.",
        "experimento": "La ficha contra la frase natural, sin reescribir: las pocas palabras con que el redactor nombró la pieza. Con la búsqueda del flujo, y también contra la foto del producto.",
        "resultados": f"La ficha da {num(q_full['hit@1'], 3)} y la frase natural {num(q_piece['hit@1'], 3)}: suma {sg(-d_q['hit@1'], 2)}, con un intervalo lejos del cero. Y lo que no esperábamos: contra la foto, la frase sin reescribir da {num(s_piece['hit@1'], 3)}, casi lo mismo que la ficha. El texto necesita que la consulta hable como el catálogo; la foto, casi no.",
        "decision": "El plan sigue escribiendo la ficha. Y queda un argumento para la búsqueda híbrida: las dos rutas fallan distinto.",
    },
    mins=1.1,
)

# -- 3: búsqueda léxica, por foto e híbrida
HK = {
    "densa": V1,
    "lexica": "bm25|description|filtro-kind",
    "foto": "siglip2|description|filtro-kind",
    "clip": "clip|description|filtro-kind",
    "densa+lexica": V1 + "|+bm25",
    "densa+foto": V1 + "|+siglip2",
    "lexica+foto": "bm25|description|filtro-kind|+siglip2",
    "rrf": V2 + "|fusion-rrf",
}


def hrow(key: str, label: str, hl: bool = False) -> dict:
    """Una barra de la ablación de la búsqueda híbrida, con su diferencia pareada contra la densa."""
    x = HIB[key]
    return {"label": label, "value": x["hit@1"], "ci": ci(x), "hl": hl, "note": dif(x["vs_base"]) if "vs_base" in x else "la base: versión 1"}


experiment(
    "3",
    "Búsqueda léxica, por foto e híbrida",
    "Suman la búsqueda por palabras y la foto del producto?",
    '<ul class="small"><li><b>Densa</b> (Qwen3, la versión 1) y <b>léxica</b> (BM25), sobre las mismas descripciones.</li>'
    "<li><b>Por foto</b>: SigLIP 2 o CLIP: la consulta en una frase contra la foto del producto, sin descripción.</li>"
    "<li><b>Fusión</b>: cada puntaje estandarizado (z-score), y el promedio.</li></ul>"
    f'<div class="find" style="margin-top:12px">Solos, los tres rinden parecido: ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. <b>Pero se equivocan en cosas distintas</b>: juntos, {nb(dif(D21))} de hit@1 y {nb(dif(D21, "hit@5"))} de hit@5.</div>',
    hbars(
        [
            hrow(HK["densa"], "densa: Qwen3"),
            hrow(HK["lexica"], "léxica: BM25"),
            hrow(HK["foto"], "por foto: SigLIP 2"),
            hrow(HK["clip"], "por foto: CLIP ViT-B/32"),
            hrow(HK["densa+lexica"], "densa + léxica"),
            hrow(HK["densa+foto"], "densa + foto"),
            hrow(HK["lexica+foto"], "léxica + foto"),
            hrow(V2, "densa + léxica + foto", True),
        ],
        width=610,
        label_w=170,
        row_h=27,
        pad_r=206,
    )
    + '<div class="cap">hit@1. A la derecha, la diferencia pareada contra la densa, con su IC 95 %.</div>',
    f"<b>Decisión:</b> la búsqueda del flujo pasa a ser híbrida: densa + léxica + foto. Es la <b>versión 2</b> (Ejercicio 4). La fusión por z-score rinde igual o mejor que por puestos (RRF: {num(HIB[HK['rrf']]['hit@1'], 3)}).",
    fases=("busqueda",),
    why="Dos dudas de fondo: ¿hace falta el embedder neuronal, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto (lo que hacíamos) o embeberla directamente.",
    notes={
        "motivo": "Dos dudas de fondo sobre el índice. ¿El embedder neuronal hace falta, o alcanza con contar palabras? Y el catálogo tiene fotos: la clase dio dos rutas, pasar la imagen a texto, que es lo que hacíamos, o embeberla directamente. Esa nunca la habíamos medido.",
        "experimento": "Tres buscadores sobre las mismas consultas: el denso, Qwen3 sobre las descripciones; el léxico, BM25; y por foto, SigLIP 2, con la consulta en una frase contra la foto del producto. Y sus fusiones.",
        "resultados": f"Solos, los tres rinden parecido: {num(HIB[V1]['hit@1'], 3)}, {num(HIB[HK['lexica']]['hit@1'], 3)} y {num(HIB[HK['foto']]['hit@1'], 3)}. Ni el embedder le gana a contar palabras, ni describir le gana a embeber la foto. Pero se equivocan en cosas distintas: fusionados dan {num(HIB[V2]['hit@1'], 3)}, {sg(D21['hit@1'], 3)} de hit@1, con un intervalo que no toca el cero.",
        "decision": "La búsqueda híbrida pasa a ser la del flujo: es la versión 2, el Ejercicio 4. Usa las dos rutas de la clase a la vez.",
    },
    mins=1.1,
)


# -- El camino incremental: un cambio por paso
def camino_svg() -> str:
    """El camino incremental (ablaciones/camino.yaml): hit@1 de cada paso con su IC, el cambio
    contra el paso anterior (pareado) y hit@5. Aparte, punteado, lo que da un VLM eligiendo: una
    técnica aislada, no un paso del flujo."""
    pasos = [
        (K_NAIVE, "RAG naive: texto del vendedor, sin reescribir"),
        (K_DESC, "+ cada producto descripto desde su foto"),
        ("qwen3|description|filtro-none", "+ la consulta escrita como una ficha (HyDE)"),
        (V1, "+ filtro por kind: versión 1"),
        (V1 + "|+bm25", "+ búsqueda léxica (BM25) fusionada"),
        (V2, "+ la foto del producto (SigLIP 2): versión 2"),
    ]
    aparte = [
        ("un VLM elige entre los 5 primeros", CURVA["por_k"]["5"]["acierto_eleccion"]),
        (f"un VLM reordena el top-10: el {num(RER[BASE + '|rerank-opus']['hit@1'])} de antes", RER[BASE + "|rerank-opus"]["hit@1"]),
    ]
    lw, pw, xmax, rh, top = 322, 196, 0.8, 34, 24
    xd, W = 578, 830
    H = top + rh * len(pasos) + 38 + 30 * len(aparte) + 4
    o = [f'<svg class="chart" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">']
    for t, x, anchor in (("hit@1", lw, "start"), ("cambio (pareado)", xd, "start"), ("hit@5", W, "end")):
        o.append(f'<text x="{x}" y="12" text-anchor="{anchor}" font-size="11.5" font-weight="650" letter-spacing=".06em" fill="var(--muted)">{t.upper()}</text>')
    for t in (0.2, 0.4, 0.6, 0.8):
        o.append(f'<line x1="{lw + pw * t / xmax}" y1="{top - 4}" x2="{lw + pw * t / xmax}" y2="{H - 4}" stroke="var(--grid)"/>')
    for i, (key, label) in enumerate(pasos):
        x, y = CAM[key], top + i * rh
        hl = key in (V1, V2)
        w = pw * x["hit@1"] / xmax
        o.append(f'<text x="{lw - 10}" y="{y + rh / 2 + 1}" text-anchor="end" dominant-baseline="middle" font-size="13.5" font-weight="{650 if hl else 450}" fill="var(--ink)">{esc(label)}</text>')
        o.append(f'<rect x="{lw}" y="{y + 6}" width="{w}" height="{rh - 13}" rx="3" fill="{"var(--accent)" if key == V2 else "var(--bar)"}"/>')
        lo, hi = ci(x)
        ym = y + rh / 2 - 0.5
        o.append(f'<line x1="{lw + pw * lo / xmax}" y1="{ym}" x2="{lw + pw * hi / xmax}" y2="{ym}" stroke="var(--ink)" stroke-width="1.4" opacity=".55"/>')
        for xx in (lo, hi):
            o.append(f'<line x1="{lw + pw * xx / xmax}" y1="{ym - 5}" x2="{lw + pw * xx / xmax}" y2="{ym + 5}" stroke="var(--ink)" stroke-width="1.4" opacity=".55"/>')
        o.append(f'<text x="{lw + pw * hi / xmax + 8}" y="{y + rh / 2 + 1}" dominant-baseline="middle" font-size="14" font-weight="{650 if hl else 500}" fill="var(--ink)">{num(x["hit@1"], 3)}</text>')
        if "vs_anterior" in x:
            d = x["vs_anterior"]
            sube = d["hit@1_ic95"][0] > 0
            o.append(f'<text x="{xd}" y="{y + rh / 2 + 1}" dominant-baseline="middle" font-size="13" font-weight="{600 if sube else 450}" fill="{"var(--good)" if sube else "var(--muted)"}">{dif(d)}</text>')
        o.append(f'<text x="{W}" y="{y + rh / 2 + 1}" text-anchor="end" dominant-baseline="middle" font-size="13.5" font-weight="{650 if hl else 450}" fill="var(--ink)">{num(x["hit@5"], 3)}</text>')
    y0 = top + rh * len(pasos) + 14
    o.append(f'<line x1="0" y1="{y0}" x2="{W}" y2="{y0}" stroke="var(--line)" stroke-dasharray="4 4"/>')
    o.append(f'<text x="0" y="{y0 + 17}" font-size="11.5" font-weight="650" letter-spacing=".06em" fill="var(--muted)">APARTE · UNA TÉCNICA AISLADA, NO UN PASO DEL FLUJO</text>')
    for j, (label, v) in enumerate(aparte):
        y = y0 + 24 + j * 30
        w = pw * v / xmax
        o.append(f'<text x="{lw - 10}" y="{y + 15}" text-anchor="end" dominant-baseline="middle" font-size="13.5" fill="var(--muted)">{esc(label)}</text>')
        o.append(f'<rect x="{lw + 0.75}" y="{y + 5.75}" width="{w - 1.5}" height="18.5" rx="3" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 4"/>')
        o.append(f'<text x="{lw + w + 8}" y="{y + 15}" dominant-baseline="middle" font-size="14" fill="var(--muted)">{num(v, 3)}</text>')
    o.append("</svg>")
    return "".join(o)


d_desc, d_hyde = CAM[K_DESC]["vs_anterior"], CAM["qwen3|description|filtro-none"]["vs_anterior"]
d_kind = CAM[V1]["vs_anterior"]
r_opus = RER[BASE + "|rerank-opus"]
slide(
    route(lit=("descripcion", "plan", "busqueda"))
    + '<div class="row" style="gap:28px"><div>'
    + camino_svg()
    + '</div><div class="grow">'
    f'<p class="small" style="font-size:15px">Sobre las {N_ANS} consultas con respuesta del ground truth de IKEA (catálogo de {len(ITEMS)}). Cada barra suma <b>un solo cambio</b> a la anterior; el cambio es pareado, con su IC 95 %.</p>'
    f'<p class="small" style="font-size:15px">Lo que más pesa: <b>la base de conocimiento</b> ({sg(d_desc["hit@1"], 2)}) y <b>cómo se escribe la consulta</b> ({sg(d_hyde["hit@1"], 2)}).</p>'
    f'<p class="small" style="font-size:15px">El filtro por kind no suma acá, y cuesta 2 puntos de hit@5 ({nb(dif(d_kind, "hit@5"))}).</p>'
    f'<p class="small" style="font-size:15px">La híbrida: <b>{nb(dif(D21))}</b> sobre la versión 1.</p>'
    "</div></div>"
    f'<div class="take">El {num(r_opus["hit@1"])} que mostrábamos no era un escalón: es lo que da un VLM reordenando el top-10, <b>una técnica aislada, no el flujo</b>.</div>',
    kicker="Experimentos · la ablación incremental",
    title=f"El camino: de {num(n1['hit@1'])} a {num(B2['hit@1'])} de hit@1, un cambio por paso",
    notes=f"La ablación incremental: un cambio por paso, con su diferencia pareada. Arrancamos del RAG naive, el texto del vendedor y la consulta sin reescribir: {num(n1['hit@1'])}. Describir cada producto desde su foto lo lleva a {num(n2['hit@1'])}; escribir la consulta como una ficha, a {num(CAM['qwen3|description|filtro-none']['hit@1'])}. Esos dos pasos son los que más pesan. El filtro por kind no suma en este banco: lo usamos por otra razón, que vemos en los de trámite. Con el filtro, esa es la versión 1 del flujo. Con la búsqueda léxica, {num(CAM[V1 + '|+bm25']['hit@1'])}; con la foto, {num(B2['hit@1'])}: la versión 2. Aparte queda el {num(r_opus['hit@1'])} que mostrábamos antes: es un VLM reordenando el top-10, una técnica aislada, no un escalón del flujo.",
    mins=0.85,
)

# -- 4: ¿error, o el mismo mueble en otro color? Tres niveles de correcto
e_q = EMB[V1]
g_run = load(R / "evaluacion" / GRAD["run"] / "metricas.json")[GRAD["method"]]
w_ans = g_run["answerable"] / g_run["searches"]  # el juez vio 75 consultas con anotado y 75 sin: se repondera
G = GRAD["consultas"]
util1 = w_ans * G["con anotado"]["util1"] + (1 - w_ans) * G["sin anotado"]["util1"]
util3 = w_ans * G["con anotado"]["util3"] + (1 - w_ans) * G["sin anotado"]["util3"]
frac_variante = (e_q["familia_hit@1"] - e_q["hit@1"]) / (1 - e_q["hit@1"])
fam = {k: EMB[f"{k}|description|filtro-kind"]["vs_base"] for k in ("bm25", "siglip2", "bge")}
assert fam["bm25"]["familia_hit@1_ic95"][0] < 0 < fam["bm25"]["familia_hit@1_ic95"][1] and fam["bge"]["familia_hit@1_ic95"][1] < 0, "por familia cambió el orden entre buscadores: revisar el texto del experimento 4"
experiment(
    "4",
    "¿Error, o el mismo mueble en otro color?",
    "Cuando el primero no es el producto anotado, se equivocó?",
    '<ul class="small"><li><b>Exacto</b>: el producto anotado sale primero (hit@1).</li>'
    "<li><b>El mismo modelo</b>: también vale otra variante, con el mismo nombre comercial y del mismo grupo (el mismo sillón en abedul o en negro, una alfombra en dos medidas).</li>"
    "<li><b>Sirve</b>: un juez califica el primer candidato contra la pieza del ambiente, con 2, 1 o 0.</li></ul>"
    f'<div class="find" style="margin-top:14px">Una de cada {round(1 / frac_variante)} veces que el primero “falla”, es el mismo mueble en otra medida u otro color. El banco <b>subestima el nivel, no el orden</b>: por familia tampoco se distinguen Qwen3, BM25 y SigLIP 2, y BGE sigue peor.</div>',
    hbars(
        [
            {"label": "el producto exacto", "value": e_q["hit@1"], "ci": ci(e_q)},
            {"label": "el mismo modelo", "value": e_q["familia_hit@1"], "ci": ci(e_q, "familia_hit@1")},
            {"label": "uno que sirve, según un juez", "value": util1, "hl": True},
        ],
        width=560,
        label_w=220,
        row_h=38,
    )
    + f'<div class="cap" style="max-width:560px">El primer candidato de la búsqueda de la versión 1. El juez: {G["todas"]["n"]} consultas, nota 1 o 2, reponderado a todas las consultas (alguno del top-3 sirve: {num(util3)}).</div>',
    f"<b>Conclusión:</b> el acierto exacto para comparar métodos, porque es objetivo y barato; y los tres niveles juntos para decir cuánto sirve lo que se trae: {num(e_q['hit@1'])}, {num(e_q['familia_hit@1'])} y {num(util1)}.",
    fases=("busqueda",),
    why=f"hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo: el {num(100 * DOC['con_variantes'], 0)} % de las consultas busca un producto que tiene variantes.",
    notes={
        "motivo": "hit@1 exige el producto anotado exacto, y el catálogo está lleno de variantes del mismo modelo. ¿Cuánto de lo que cuenta como error es el mismo mueble en otro color?",
        "experimento": "Tres niveles de correcto para el primer candidato: el producto exacto, el mismo modelo, y uno que sirve según un juez.",
        "resultados": f"El exacto, {num(e_q['hit@1'])}; el mismo modelo, {num(e_q['familia_hit@1'])}; uno que sirve, {num(util1)}. Una de cada {round(1 / frac_variante)} veces que el primero falla es otra variante del mismo mueble.",
        "decision": "El banco subestima el nivel, no el orden: la comparación entre buscadores no cambia. Usamos el exacto para comparar, y los tres juntos para decir cuánto sirve.",
    },
    mins=0.7,
)

# -- 5: elegir con un VLM, y cuántos candidatos
r0, r1 = RER[BASE], RER[BASE + "|rerank-opus"]
d_opus = paired(RER_DIR, BASE + "|rerank-opus", BASE)
ks = list(range(1, 11))
acc = [CURVA["por_k"][str(k)]["acierto_eleccion"] for k in ks]
cei = [CURVA["por_k"][str(k)]["techo_hit@k"] for k in ks]
d35 = CURVA["diferencias_pareadas"]["3->5"]
d35_txt = f'{sg(d35["acierto_eleccion"])} {ic(*d35["ic95"])}'
c_rerank = statistics.mean(r["cost_usd"] for r in LEDGER if r["step"].startswith("eval.rerank") and "opus" in (r.get("model") or ""))
experiment(
    "5",
    "Elegir con un VLM, y cuántos candidatos",
    "Un VLM que mira las fotos ordena mejor que la búsqueda? Y por qué 5 candidatos, y no 3 o 10?",
    '<p class="small">Opus recibe la consulta y las <b>fotos</b> de los 10 primeros, y los ordena (<code>rerank_candidates_v1</code>). De ahí sale gratis la curva: si eligiera entre los k primeros, ¿acertaría? '
    "<b>Techo</b>: el correcto está entre esos k (hit@k).</p>"
    f'<div class="find">Sobre el top-10, hit@1 pasa de {num(r0["hit@1"], 3)} a <b>{num(r1["hit@1"], 3)}</b> ({nb(dif(d_opus))}), a US${num(c_rerank)} por búsqueda. De 3 a 5 candidatos, {nb(d35_txt)}; a partir de 8 se aplana.</div>',
    lines(
        [
            {"ys": cei, "dash": True, "labels": {8: "techo (hit@k)"}},
            {"name": "elección del VLM", "ys": acc, "hl": True, "below": True, "labels": {3: num(acc[2]), 5: num(acc[4]), 8: num(acc[7])}},
        ],
        ks,
        ymin=0.5,
        ymax=0.9,
        width=560,
        height=250,
        xlabel="candidatos por pieza (k)",
        ylabel="acierto",
        marks=[{"x": 5, "text": "elegido"}],
    ),
    f"<b>Decisión:</b> {CFG.furnish.candidates} candidatos por pieza (antes 3). Ojo: es una <b>técnica aislada</b>, no un paso del flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto para el cuarto, y no tiene ground truth. En los {DIAG['hibrida']['ambientes']} ambientes, el {num(100 * DIAG['hibrida']['elegido_en_puestos_4_y_5'], 0)} % de lo que eligió salió de los puestos 4 y 5.",
    fases=("busqueda", "eleccion"),
    why=f"hit@10 es {num(r0['hit@10'])} pero hit@1 {num(r0['hit@1'])}: el correcto casi siempre está entre los 10 primeros, pero no primero. En el flujo, quien elige mira las fotos de los candidatos.",
    notes={
        "motivo": f"hit@10 es {num(r0['hit@10'])} pero hit@1 {num(r0['hit@1'])}: el correcto casi siempre está entre los diez primeros, pero no primero. ¿Mirar las fotos ordena mejor que el coseno? ¿Y cuántos candidatos conviene pasar?",
        "experimento": "Opus recibe la consulta y las fotos de los diez primeros, y los ordena. De ahí sale gratis la curva: si eligiera entre los primeros k, ¿acertaría? La punteada es el techo.",
        "resultados": f"Reordenando el top-10, hit@1 pasa de {num(r0['hit@1'], 3)} a {num(r1['hit@1'], 3)}. De 3 a 5 candidatos la elección sube {num(100 * d35['acierto_eleccion'], 0)} puntos, también significativo; a partir de 8 se aplana.",
        "decision": "Cinco candidatos por pieza. Pero ojo: es una técnica aislada, no un paso del flujo. Ese reranker ordena contra la consulta, sin ver el ambiente; el que elige en el flujo arma un conjunto para el cuarto, y no tiene ground truth. Por eso este número no es el del sistema.",
    },
    mins=1.05,
)


# -- 6: qué catálogo (punta a punta)
def split_e2e(res: dict, a: str, b: str) -> list[tuple]:
    out = []
    for lab, cond in (
        ("propios (nórdicos)", lambda x: not x.startswith("publica")),
        ("públicos (otros estilos)", lambda x: x.startswith("publica")),
        ("total", lambda x: True),
    ):
        ds = [d for d in res["detalle"] if cond(d["slug"])]

        def util(v, ds=ds):
            g = [x for d in ds for sd in d["puntajes"][v] for x in sd["grades"]]
            return sum(x == 2 for x in g) / max(1, len(g))

        out.append(
            (lab, len(ds), sum(d["ganador"] == a for d in ds), sum(d["ganador"] == b for d in ds),
             sum(d["ganador"] == "tie" for d in ds), util(a), util(b))
        )
    return out


abo5 = E2E["juez_ikea_vs_abo_5ambientes"]
s5 = abo5["resumen"]
rows_c = split_e2e(JC, "ikea", "todos")
(_, n_pro, pro_i, pro_t, *_), (_, n_pub, pub_i, pub_t, _, pub_ui, pub_ut), (_, _, tot_i, tot_t, *_) = rows_c
p_cat = p_signos(tot_t, tot_i)
d_abo = paired(TODOS_DIR, BASE, BASE, run_b=ABL_DIR)  # el mismo buscador, con ABO de distractores
tbl_cat = (
    '<h3 style="margin-bottom:4px">1. IKEA contra ABO (5 ambientes propios)</h3>'
    '<table class="t sm"><tr><th></th><th>gana</th><th>útil</th><th>pedido</th><th>ambiente</th><th>conjunto</th></tr>'
    + "".join(
        f'<tr class="{"hl" if v == "ikea" else ""}"><td>{"IKEA" if v == "ikea" else "ABO"}</td><td class=n>{s5[v]["gana"]}</td><td class=n>{num(s5[v]["util"])}</td>'
        f'<td class=n>{num(s5[v]["request"], 1)}</td><td class=n>{num(s5[v]["room"], 1)}</td><td class=n>{num(s5[v]["together"], 1)}</td></tr>'
        for v in ("ikea", "abo")
    )
    + f'</table><div class="cap">{abo5["empates"]} empate. ABO pierde por estilo: maderas oscuras, patas doradas.</div>'
    '<h3 style="margin:8px 0 3px">2. IKEA contra IKEA + ABO (11 ambientes)</h3>'
    '<table class="t sm"><tr><th></th><th>n</th><th>IKEA</th><th>IKEA+ABO</th><th>emp.</th><th>útil I</th><th>útil I+A</th></tr>'
    + "".join(
        f'<tr class="{"hl" if lab == "total" else ""}"><td>{lab}</td><td class=n>{n}</td><td class=n>{wa}</td><td class=n>{wb}</td><td class=n>{t}</td><td class=n>{num(ua)}</td><td class=n>{num(ub)}</td></tr>'
        for lab, n, wa, wb, t, ua, ub in rows_c
    )
    + f'</table><div class="cap">Test de signos sobre los {tot_i + tot_t} decididos: <b>p = {num(p_cat)}</b>. Acuerdo entre órdenes: {num(JC["acuerdo_entre_ordenes"])}. Útil: nota 2.</div>'
)
experiment(
    "6",
    "Qué catálogo",
    "Con qué catálogo salen mejores listas para ambientes reales: IKEA, Amazon (ABO) o los dos?",
    '<ul class="small">'
    f"<li><b>IKEA</b>: {len(ITEMS)} productos, fotos de 500 px, asientos sin medidas; el único con ground truth.</li>"
    f"<li><b>Amazon Berkeley Objects</b> (Collins et al., 2022): listados reales; {ABO_N} descriptos con el mismo formato, medidas en el 90 %.</li>"
    "<li>Mismo plan; cambia solo el catálogo. Un juez compara las listas de a pares, a ciegas, en los dos órdenes.</li></ul>"
    f'<div class="find" style="margin-top:8px">En los {n_pro} pedidos nórdicos empatan ({pro_i} a {pro_t}). En los {n_pub} de otros estilos, IKEA + ABO gana {pub_t} a {pub_i}, y los productos útiles pasan de {num(pub_ui)} a {num(pub_ut)}.</div>',
    f'<div style="width:600px">{tbl_cat}</div>',
    f"<b>Decisión:</b> el flujo usa IKEA + ABO. Pero {tot_t} a {tot_i} es p = {num(p_cat)}, y los pedidos de otros estilos <b>los escribimos sabiendo qué le falta a IKEA</b>: la decisión es razonable; el titular “{pub_t} a {pub_i}”, no.",
    fases=("catalogo",),
    why="IKEA 2013 tiene fotos chicas, asientos sin medidas y una sola estética. ABO tiene listados reales, con medidas, pero no tiene ambientes anotados: hay que medirlo de punta a punta.",
    notes={
        "motivo": "IKEA es de 2013, con una sola estética, la nórdica. Amazon Berkeley Objects tiene listados reales, con medidas, pero no tiene ambientes anotados: hay que medirlo de punta a punta.",
        "experimento": "Los mismos ambientes, pedidos y plan; cambia solo el catálogo. El juez compara las dos listas a ciegas, en los dos órdenes.",
        "resultados": f"En nuestros cinco departamentos, con pedidos nórdicos, IKEA le gana a Amazon solo, y los dos juntos empatan con IKEA. Sumamos seis ambientes públicos con otros estilos: ahí, IKEA más Amazon gana {pub_t} a {pub_i}. En total, {tot_t} a {tot_i}.",
        "decision": f"Usamos los dos catálogos. Con dos salvedades: {tot_t} a {tot_i} en once ambientes da p igual a {num(p_cat)}, no es concluyente; y los pedidos de otros estilos los escribimos nosotros, sabiendo qué le falta a IKEA. Muestra que Amazon cubre ese hueco, no cuán frecuente es.",
    },
    mins=1.1,
)

# -- 7: con búsqueda contra sin búsqueda (5 al azar), y contra el catálogo entero en el contexto
sa = JA["resumen"]
votos_a = [v for d in JA["detalle"] for v in d["votos"]]
p_azar = p_signos(sa["densa"]["gana"], sa["azar"]["gana"])
JX = E2E["juez_hibrida_vs_contexto"]  # la versión 2 contra el catálogo entero en el prompt (sin búsqueda)
sx = JX["resumen"]
votos_x = [v for d in JX["detalle"] for v in d["votos"]]
CTX_DIR = R / "punta_a_punta" / "hibrida"
ctx_runs = sorted(d for d in (CTX_DIR / "contexto").iterdir() if (d / "3_choice.json").exists())
ctx = [load(d / "3_choice.json") for d in ctx_runs]
rag = [load(CTX_DIR / "hibrida" / d.name / "3_choice.json") for d in ctx_runs]
opus = CFG.furnish.llm["models"]["claude-opus-5-5"]["usd_per_m"]


def _uso(c: dict) -> dict:
    return c["meta"]["usage"]


def _entrada(c: dict) -> int:
    return sum(_uso(c).get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


cat_tokens = max(_uso(c).get("cache_read_input_tokens") or 0 for c in ctx)  # el catálogo, en tokens de Opus 5.5
ctx_caliente = statistics.mean(c["cost_usd"] for c in ctx if not _uso(c).get("cache_creation_input_tokens"))
ctx_sin_cache = statistics.mean((_entrada(c) * opus["input"] + _uso(c)["output_tokens"] * opus["output"]) / 1e6 for c in ctx)
rag_usd = statistics.mean(c["cost_usd"] for c in rag)
ctx_s, rag_s = (statistics.median(c["meta"]["latency_s"] for c in g) for g in (ctx, rag))
# el producto elegido con todo el catálogo a la vista, ¿estaba entre los 5 de la búsqueda?
ctx_piezas = ctx_en_top5 = 0
for d, c in zip(ctx_runs, ctx, strict=True):
    cands = load(CTX_DIR / "hibrida" / d.name / "2_candidates.json")["pieces"]
    for piece, ch in zip(cands, c["answer"]["choices"], strict=True):
        ctx_piezas += 1
        ctx_en_top5 += ch.get("id") in {h["id"] for h in piece["candidates"]}


def _filas(resumen: dict, votos: list, pares: tuple) -> str:
    return "".join(
        f'<tr class="{"hl" if i == 0 else ""}"><td style="white-space:nowrap">{lab}</td><td class=n>{resumen[v]["gana"]}</td><td class=n>{votos.count(v)}</td><td class=n>{num(resumen[v]["util"])}</td>'
        f'<td class=n>{num(resumen[v]["request"], 1)}</td><td class=n>{num(resumen[v]["room"], 1)}</td><td class=n>{num(resumen[v]["together"], 1)}</td></tr>'
        for i, (v, lab) in enumerate(pares)
    )


tbl_azar = (
    '<table class="t"><tr><th></th><th>gana</th><th>votos</th><th>útil</th><th>pedido</th><th>ambiente</th><th>conjunto</th></tr>'
    + f'<tr class="sec"><td colspan="7">Contra 5 al azar · {JA["ambientes"]} ambientes · p = {num(p_azar, 3)}</td></tr>'
    + _filas(sa, votos_a, (("densa", "Con búsqueda"), ("azar", "5 al azar del kind")))
    + f'<tr class="sec"><td colspan="7">Contra el catálogo entero en el prompt · {JX["ambientes"]} ambientes</td></tr>'
    + _filas(sx, votos_x, (("hibrida", "Con búsqueda"), ("contexto", "El catálogo entero")))
    + f'</table><div class="cap">Útil: productos con nota 2; el resto, de 1 a 5. Los controles del juez: contra el azar los dos órdenes coinciden siempre; la versión 2 contra sí misma reparte {jr["hibrida"]["gana"]} a {jr["hibrida_bis"]["gana"]}. Con el catálogo entero tarda lo mismo ({num(ctx_s, 0)} y {num(rag_s, 0)} s), y en {ctx_en_top5} de {ctx_piezas} piezas lo que el modelo eligió viendo todo estaba entre los 5 de la búsqueda.</div>'
)
experiment(
    "7",
    "Con búsqueda, sin búsqueda, o con el catálogo entero",
    "La búsqueda aporta en la tarea real? Y hacía falta, si el catálogo entra en el contexto?",
    '<ul class="small"><li><b>Con búsqueda</b>: para cada pieza, los 5 mejores, con su foto.</li>'
    "<li><b>5 al azar</b> entre los que pasan los mismos filtros (kind y medidas).</li>"
    f"<li><b>El catálogo entero en el prompt</b>: las {miles(len(ITEMS) + ABO_N)} fichas en texto ({miles(round(cat_tokens / 1000))} mil tokens, en caché), con el mismo filtro; sin ranking ni fotos de candidatos.</li>"
    "<li>Mismo plan, mismo modelo que elige y mismo juez.</li></ul>"
    '<div class="card" style="margin-top:6px;padding:9px 16px"><h3 style="font-size:15.5px;margin-bottom:3px">¿Hacía falta RAG, si el catálogo entra en el contexto?</h3>'
    f'<p class="small" style="font-size:14px;line-height:1.4;margin:0"><b>Por calidad, no: empatan.</b> Por costo, depende del tráfico: con el catálogo en la caché de prompt, US${num(ctx_caliente)} por pedido contra US${num(rag_usd, 3)} de elegir entre candidatos con foto; sin caché, US${num(ctx_sin_cache)}. La búsqueda <b>escala</b> (el catálogo ya ocupa un tercio del contexto; ABO completo son {DOC["abo_listados"]} listados) y no depende de la caché, que dura 5 minutos y se invalida con cualquier cambio del catálogo.</p></div>',
    f'<div style="width:600px">{tbl_azar}</div>',
    f"<b>Conclusión:</b> la búsqueda hace falta cuando el que elige ve 5 productos, y empata cuando puede leerlos todos. Con {miles(len(ITEMS) + ABO_N)} productos, RAG no hace mejor la lista: es la arquitectura que escala.",
    fases=("busqueda",),
    why="Es el “con y sin retrieval” del flujo, con sus dos extremos: sin ranking (5 al azar) y con todo a la vista (el catálogo entero en el prompt).",
    notes={
        "motivo": "Es el con y sin retrieval del flujo, con dos extremos. Uno: darle al que elige cinco productos al azar del kind pedido. Dos, la pregunta incómoda: si el catálogo entra en el contexto, ¿hacía falta RAG?",
        "experimento": f"Mismo plan, mismo modelo que elige, mismo juez. Contra el azar, en {JA['ambientes']} ambientes. Y contra el catálogo entero en el prompt, las {miles(len(ITEMS) + ABO_N)} fichas en texto, en los {JX['ambientes']}.",
        "resultados": f"Contra el azar, {sa['densa']['gana']} a {sa['azar']['gana']}, con los {len(votos_a)} votos. Contra el catálogo entero, {sx['hibrida']['gana']} a {sx['contexto']['gana']}, con los mismos productos útiles: empatan. Y con el catálogo en la caché de prompt cuesta lo mismo; sin caché, diez veces más.",
        "decision": "La búsqueda hace falta cuando el que elige ve cinco productos, y empata cuando puede leerlos todos. Con mil quinientos productos, RAG no hace mejor la lista: lo elegimos porque escala, y porque no depende del tráfico ni de un modelo de contexto largo.",
    },
    mins=1.25,
)

# -- 8: tres redactores
v1s = [CAM[V1]["hit@1"]] + [h[V1]["hit@1"] for h in HIB_R]
v2s = [CAM[V2]["hit@1"]] + [h[V2]["hit@1"] for h in HIB_R]
tres = [("original", HIB), ("redactor 2", HIB_R[0]), ("redactor 3", HIB_R[1])]
experiment(
    "8",
    "Tres redactores",
    "Cuánto cambia el número según quién escribe las consultas?",
    '<ul class="small"><li>Las mismas consultas, escritas otras dos veces por subagentes independientes, mirando las mismas fotos.</li>'
    "<li>Los mismos buscadores sobre cada escritura: la versión 1 (densa) y la versión 2 (híbrida).</li></ul>"
    f'<div class="find" style="margin-top:14px">hit@1 según quién escribe: versión 1, <b>{media_desvio(v1s)}</b>; versión 2, <b>{media_desvio(v2s)}</b>. La mejora de la híbrida se repite en las tres escrituras.</div>',
    hbars(
        [
            row
            for lab, src in tres
            for row in (
                {"label": f"{lab} · versión 1", "value": src[V1]["hit@1"], "ci": ci(src[V1])},
                {"label": f"{lab} · versión 2", "value": src[V2]["hit@1"], "ci": ci(src[V2]), "hl": True, "note": dif(src[V2]["vs_base"])},
            )
        ],
        width=610,
        label_w=176,
        row_h=30,
        pad_r=204,
    )
    + '<div class="cap">hit@1. A la derecha, la versión 2 menos la versión 1, pareado, con su IC 95 %.</div>',
    f"<b>Conclusión:</b> el número se mueve unos {num(100 * statistics.stdev(v1s), 1)} puntos sin cambiar el sistema. Una diferencia de 2 puntos entre dos métodos no es señal: por eso los embedders “no se distinguen”, y la híbrida sí.",
    fases=("busqueda",),
    why="Las consultas de evaluación las escribió un modelo. La clase pidió promedio de ejecuciones y desvío: si el número cambia mucho con quién escribe, mide al redactor y no al sistema.",
    notes={
        "motivo": "Las consultas de evaluación las escribió un modelo. La clase pidió promedio y desvío: ¿cuánto cambia el número sin cambiar el sistema?",
        "experimento": "Las mismas consultas, escritas otras dos veces por subagentes independientes.",
        "resultados": f"La versión 1 da {media_desvio(v1s)}; la versión 2, {media_desvio(v2s)}. La mejora de la híbrida se repite con los tres.",
        "decision": "El número se mueve unos dos puntos y medio según quién escribe: por eso no leemos diferencias de dos puntos.",
    },
    mins=0.55,
)

# -- De trámite: lo que pregunta la cátedra, con la respuesta en una línea


def emb(k: str) -> dict:
    return EMB[f"{k}|description|filtro-kind"]


def sin(x: str) -> dict:
    """La búsqueda de la versión 1 sin esas líneas en documentos y consultas."""
    return LIN[f"{V1}|sin-{x}"]


def h15(x: dict) -> str:
    return f'{num(x["hit@1"], 3)} / {num(x["hit@5"], 3)}'


dims = {d: (ABL[f"{BASE}|dim-{d}"] if d != 1024 else ABL[BASE])["hit@1"] for d in (32, 128, 512, 1024)}
d512 = paired(ABL_DIR, BASE + "|dim-512", BASE)
doc_, chunk, alin = ABL[BASE], ABL[BASE + "|chunks-lines-max"], ABL[BASE + "|chunks-lines-aligned"]
visto = sin("Use+Style+Feel+Goes with")
ex_a, ex_b = rankings(ABL_DIR)[BASE + "|exact"], rankings(ABL_DIR)[BASE]
iguales = sum(x["ranked"] == y["ranked"] for x, y in zip(ex_a, ex_b, strict=True))


def tram(n: int | None, name: str, what: str, answer: str) -> str:
    p = pin_inline(n) if n else '<span style="display:inline-block;width:21px"></span>'
    return f'<tr><td class="nm">{p}<b>{name}</b></td><td>{what}</td><td>{answer}</td></tr>'


TH = '<table class="t tram"><tr><th style="width:190px">La pregunta</th><th style="width:330px">Qué se comparó (hit@1)</th><th>La respuesta</th></tr>'
slide(
    route(lit=("indice",), pins={"indice": PINES["indice"]})
    + TH
    + tram(9, "Embedder", f'hashing {num(emb("hashing")["hit@1"], 3)} · BM25 {num(emb("bm25")["hit@1"], 3)} · BGE {num(emb("bge")["hit@1"], 3)} · <b>Qwen3 {num(EMB[V1]["hit@1"], 3)}</b>',
           f'Solo se sostiene Qwen3 sobre BGE ({nb(dif(emb("bge")["vs_base"], flip=True))}). Contra contar palabras no se distingue ({nb(dif(emb("hashing")["vs_base"], flip=True))}). Queda Qwen3 por robustez a la paráfrasis, sin evidencia medida.')
    + tram(10, "Dimensión", " · ".join(f"{'<b>' if d == 1024 else ''}{miles(d)}: {num(v, 3)}{'</b>' if d == 1024 else ''}" for d, v in dims.items()),
           f"Con 512 da lo mismo que con 1.024 ({nb(dif(d512))}). Con 1.500 productos la memoria no pesa: queda 1.024.")
    + tram(11, "Splitting y líneas", f'<b>un documento {num(doc_["hit@1"], 3)}</b> · un chunk por línea {num(chunk["hit@1"], 3)} · línea contra línea {num(alin["hit@1"], 3)}',
           f'No se parte: un producto es un documento de unas 80 palabras. Lo que importa es qué líneas lo componen: sin Colors, {nb(dif(sin("Colors")["vs_base"]))}; sin Shape, {nb(dif(sin("Shape")["vs_base"]))}; con solo las cuatro de lo que se ve se encuentra igual que con las ocho ({num(visto["hit@1"], 3)}).')
    + tram(12, "Base vectorial", "ChromaDB (HNSW, coseno) contra recorrer todos los vectores con numpy",
           f"El mismo top-10 en {iguales} de {len(ex_a)} consultas. ChromaDB da la persistencia y los filtros de metadata en la misma consulta, y es la pieza que escala.")
    + "</table>"
    '<div class="take">Con el texto bien escrito, el índice casi no decide nada: son respuestas que hay que tener, no un gran experimento.</div>',
    kicker="Experimentos · de trámite (1 de 2)",
    title="De trámite: las cuatro preguntas sobre el índice",
    notes=f"Los de trámite: lo que la cátedra dijo que iba a preguntar, con la respuesta corta. Embedder: Qwen3 solo se sostiene sobre BGE; contra contar palabras no se distingue, porque consultas y descripciones comparten el molde. Dimensión: con 512 da lo mismo que con 1.024, y con 1.500 productos la memoria no pesa. Splitting: no partimos, un producto es un documento; lo que importa es qué líneas lo componen, y son las de lo que se ve: colores y forma. Base vectorial: ChromaDB da el mismo top-10 que la búsqueda exacta en las {len(ex_a)} consultas; la usamos por la persistencia y los filtros.",
    mins=0.8,
)

f_none, f_type = HIB["qwen3|description|filtro-none"], HIB[BASE]
mini, qrr = ABL[BASE + "|rerank-minilm-reranker"], RLOC[BASE + "|rerank-qwen3-reranker"]
old, new = CAT_OLD[BASE], CAT_NEW[BASE]
t_abo = load(TODOS_DIR / "metricas.json")[BASE]
slide(
    route(lit=("catalogo", "busqueda", "escena"), pins={"busqueda": [13, 14], "escena": [15]})
    + TH.replace("(hit@1)", "(hit@1 / hit@5)").replace("La pregunta", "Qué")
    + tram(13, "Filtros", f"sin filtro {h15(f_none)} · por tipo {h15(f_type)}<br><b>por kind {h15(B1)}</b>",
           f'No suman en este banco, y el de kind cuesta 2 puntos de hit@5 ({nb(dif(d_kind, "hit@5"))}). Se usa por algo que el banco no mide: en los pedidos reales evita un {num(100 * DOC["otro_kind"], 0)} % de candidatos de otro kind (se pide un sillón y aparece una silla de comedor). El de medidas actúa poco: cambia {FM["candidatos_reemplazados"]} de {FM["candidatos"]} candidatos en los ambientes reales, y solo el {num(100 * ikea_con_medida, 0)} % de IKEA tiene alguna medida.')
    + tram(14, "Rerankers de texto", f'sin rerank {h15(RLOC[BASE])} · MiniLM {h15(mini)} · Qwen3-Reranker {h15(qrr)}',
           f'Empeoran ({nb(dif(qrr["vs_base"]))} el mejor): releen el mismo texto que ya usó la búsqueda. El que suma es el que mira las fotos (experimento 5).')
    + tram(None, "El catálogo, ampliado y revisado", f'268 productos {num(DOC["catalogo_268"], 3)} → 855: {num(old["hit@1"], 3)} → {len(ITEMS)}: {num(new["hit@1"], 3)} (hit@1)',
           "Decisiones de datos, no experimentos: ampliar cambia el universo (más productos parecidos); revisar hace que la lista y la imagen muestren el mismo producto.")
    + tram(None, "ABO como distractores", f'{len(ITEMS)} productos {h15(ABL[BASE])} → con los {ABO_N} de ABO {h15(t_abo)}',
           f'Sumar productos solo puede bajar el número ({nb(dif(d_abo, "hit@5"))} de hit@5): es el costo, chico, de cubrir más estilos.')
    + tram(15, "La escena", f'plantilla: {IMG_FIN["identificados"]} de {IMG_FIN["productos"]} productos reconocidos, {IMG_FIN["ambiente_conservado"]} de {IMG_FIN["corridas"]} cuartos conservados · escrita por el LLM: {IMG_ESC["identificados"]} y {IMG_ESC["ambiente_conservado"]}',
           f'Empate en los {IMG_FIN["corridas"]} ambientes, con las mismas listas ({nb(DOC["escena_pareado"])} de reconocidos, pareado). Queda la plantilla: una llamada y US${num(DOC["escena_usd"], 3)} menos por pedido.')
    + "</table>"
    '<div class="take">Sin experimento: el modelo de imagen (comparación diseñada, sin correr) y los umbrales del control.</div>',
    kicker="Experimentos · de trámite (2 de 2)",
    title="De trámite: filtros, rerankers de texto, el catálogo y la escena",
    notes=f"Filtros de metadata: en este banco no suman, y el de kind cuesta dos puntos de hit@5. Lo usamos igual, por algo que el banco no mide: en los pedidos reales, sin él, el {num(100 * DOC['otro_kind'], 0)} por ciento de los candidatos sería de otro kind; pedís un sillón y aparece una silla de comedor. El de medidas cambia uno de cada once candidatos, sin evidencia de que mejore la lista. Rerankers de texto: probamos el MiniLM de la clase y Qwen3-Reranker, y los dos empeoran, porque releen el texto que ya usó la búsqueda. Y el catálogo: ampliarlo y revisarlo fueron decisiones de datos, y sumar Amazon le cuesta al buscador {num(-100 * d_abo['hit@5'], 1)} puntos de hit@5. Y la escena: escrita por un LLM empata con la plantilla en los once ambientes; queda la plantilla.",
    mins=0.8,
)


# ================================================================================================
# Ejercicio 4: versión 1 y versión 2 (docs/REVISION.md, sección 6)
# ================================================================================================
# Un caso del banco de prueba donde la versión 1 deja al anotado fuera de los 5 candidatos
CASO = "white cushion with black leaf print on the right armchair"
caso = {k: next(r for r in rankings(HIB_DIR)[k] if r.get("phrase") == CASO) for k in (V1, V2)}
assert caso[V1]["rank"] > CFG.furnish.candidates and caso[V2]["rank"] == 1, "el caso del Ejercicio 4 ya no muestra la limitación: elegir otro"


def fila_caso(key: str) -> str:
    """Los 5 primeros de una búsqueda para el caso, con los anotados marcados."""
    r = caso[key]
    return '<div class="fila5">' + "".join(
        f'<div class="th{" pick" if pid in r["relevant"] else ""}">{img(ITEMS[pid]["photos"][0], 150, alt="")}</div>' for pid in r["ranked"][:5]
    ) + "</div>"


cat1 = B1["hit@1_por_categoria"]
kinds_idx = [x.get("kind") for x in ITEMS.values()]
bm_solo, foto_solo = HIB["bm25|description|filtro-kind"], HIB["siglip2|description|filtro-kind"]
slide(
    '<div class="row" style="gap:34px">'
    '<div style="width:540px">'
    '<div class="lab">La versión 1: el sistema hasta el 11/11</div>'
    '<p class="small" style="font-size:15px">La búsqueda era el coseno de Qwen3 entre la ficha y las descripciones, con el filtro por kind: <code>rag.hybrid: []</code>. Lo demás, igual que hoy.</p>'
    '<div class="lab" style="margin-top:14px">Su limitación, medida sobre el ground truth</div>'
    '<div class="trio">'
    f'<div><b>{num(B1["hit@1"])}</b><span>hit@1: entre productos casi iguales, el primero es el anotado la mitad de las veces</span></div>'
    f'<div><b>1 de cada {round(1 / (1 - B1["hit@5"]))}</b><span>piezas donde el correcto no llega a los 5 candidatos (hit@5 {num(B1["hit@5"])}): el que elige ya no puede acertar</span></div>'
    f'<div><b>{num(cat1["rug"])} · {num(cat1["deco"])}</b><span>en alfombras y deco, donde hay muchos parecidos ({kinds_idx.count("rug")} alfombras, {kinds_idx.count("cushion")} almohadones); en sillas, {num(cat1["chair"])}</span></div>'
    "</div>"
    '<p class="small" style="font-size:15px;margin-top:12px">El índice <b>lee una descripción, pero no ve el producto</b>, y no aprovecha las palabras exactas de la consulta.</p>'
    "</div>"
    '<div class="grow"><div class="lab">Un caso del banco de prueba</div>'
    f'<div class="quote" style="font-size:14.5px">Se busca: <i>“{esc(CASO)}”</i> (un almohadón blanco con un estampado de hojas negras).</div>'
    '<div class="lab" style="margin-top:14px">Los 5 candidatos de la versión 1</div>'
    + fila_caso(V1)
    + f'<div class="cap">Blancos y negros, ninguno con hojas: el anotado quedó {caso[V1]["rank"]}.º, fuera de lo que ve el que elige.</div>'
    '<div class="lab" style="margin-top:12px">Lo anotado en ese ambiente</div>'
    '<div class="fila5">' + "".join(f'<div class="th pick">{img(ITEMS[pid]["photos"][0], 150, alt="")}</div>' for pid in caso[V1]["relevant"]) + "</div>"
    "</div></div>"
    f'<div class="take">Dos señales de que había información sin usar: contar palabras ({num(bm_solo["hit@1"], 3)}) y la foto sola ({num(foto_solo["hit@1"], 3)}) rendían como el embedder, <b>y fallaban en cosas distintas</b>.</div>',
    kicker="Ejercicio 4 · 1 de 3 · la versión anterior y su limitación",
    title="Versión 1: el índice lee la descripción, no ve el producto",
    notes=f"El Ejercicio 4. La versión 1 es el sistema hasta el 11 de noviembre: la búsqueda era el coseno del embedder sobre las descripciones, con el filtro por kind. Su limitación, medida: entre productos casi iguales, el primero es el anotado el {num(100 * B1['hit@1'], 0)} por ciento de las veces, y en una de cada cinco piezas el correcto no llega a los cinco candidatos. Falla donde hay muchos parecidos: alfombras y deco. Un caso: se busca un almohadón blanco con hojas negras, y la versión 1 trae almohadones blancos y negros; el anotado quedó sexto. El índice lee una descripción, pero no ve el producto ni aprovecha las palabras exactas. Y BM25 y la foto sola rendían como el embedder, fallando en cosas distintas.",
    mins=0.9,
)


def hibrida_svg() -> str:
    """La búsqueda antes y después: en gris, lo que ya hacía la versión 1; en naranja, lo que
    agrega la versión 2."""
    W, H = 600, 292
    A, MU, LI = "var(--accent)", "var(--muted)", "var(--line)"
    o = [f'<svg class="pipe" viewBox="0 0 {W} {H}" width="{W}" role="img">']

    def box(x, y, w, h, title, sub="", new=False, tag="", center=False):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{"var(--accent-soft)" if new else "var(--card)"}" stroke="{A if new else LI}" stroke-width="{1.6 if new else 1.2}"/>')
        tx, anchor = (x + w / 2, "middle") if center else (x + 12, "start")
        o.append(f'<text x="{tx}" y="{y + (20 if sub else h / 2 + 5)}" text-anchor="{anchor}" font-size="13.5" font-weight="650" fill="var(--ink)">{esc(title)}</text>')
        if sub:
            o.append(f'<text x="{x + 12}" y="{y + 37}" font-size="11.5" fill="{MU}">{esc(sub)}</text>')
        if tag:
            o.append(f'<text x="{x + w - 10}" y="{y + 16}" text-anchor="end" font-size="10" font-weight="700" letter-spacing=".06em" fill="{A if new else MU}">{tag.upper()}</text>')

    def flecha(x, y1, y2, new=False):
        c = A if new else MU
        o.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{c}" stroke-width="1.4"/>' + arrowhead(x, y2, x, y1, 6, c))

    box(150, 0, 300, 34, "La ficha de la pieza (8 líneas)", center=True)
    flecha(300, 37, 50)
    box(0, 54, W, 34, "Filtro duro: kind y medidas. Sobre los productos que pasan:", center=True)
    sw, gap, y2 = 188, 18, 108
    trio = [
        ("Qwen3", "coseno con la descripción", False, "versión 1"),
        ("BM25", "palabras de la descripción", True, "nuevo"),
        ("SigLIP 2", "la frase contra la foto", True, "nuevo"),
    ]
    for i, (t, sub, new, tag) in enumerate(trio):
        x = i * (sw + gap)
        flecha(x + sw / 2, 91, y2 - 4, new)
        box(x, y2, sw, 48, t, sub, new, tag)
        flecha(x + sw / 2, y2 + 51, 174, new)
    box(0, 178, W, 36, "Fusión: z-score de cada puntaje, y el promedio", new=True, tag="nuevo", center=True)
    flecha(300, 217, 230)
    box(150, 234, 300, 34, f"Los {CFG.furnish.candidates} mejores, a la elección", center=True)
    o.append(f'<text x="0" y="{H - 5}" font-size="11.5" fill="{MU}">En naranja, lo que agrega la versión 2. La versión 1: el filtro, el coseno y los 5 mejores.</text>')
    o.append("</svg>")
    return "".join(o)


cfg_txt = (ROOT / "datos/configs/amoblai.yaml").read_text()
otros = [caso[V2]["ranked"].index(pid) + 1 for pid in caso[V2]["relevant"] if pid in caso[V2]["ranked"][1:5]]
otro_txt = f"; el otro anotado, {otros[0]}.º" if otros else ""
assert CFG.rag.hybrid == ["bm25", "siglip2"] and CFG.rag.fusion == "sum" and "  hybrid: [bm25, siglip2]" in cfg_txt, "amoblai.yaml ya no es la versión 2: revisar la lámina del cambio"
slide(
    '<div class="row" style="gap:34px">'
    '<div style="width:500px">'
    '<div class="lab">El cambio: una línea de configuración</div>'
    '<div class="code"><div class="ph"><b>datos/configs/amoblai.yaml</b><span>antes y después</span></div>'
    '<pre>rag:\n  embedder: qwen3\n'
    '<span class="del">- hybrid: []                  # versión 1</span>\n'
    '<span class="add">+ hybrid: [bm25, siglip2]     # versión 2</span>\n'
    '  fusion: sum                 <span class="k"># z-score, y el promedio</span></pre></div>'
    '<div class="lab" style="margin-top:16px">Por qué este cambio</div>'
    + dec(None, "Sale de una <b>limitación medida</b> de la versión 1: el índice no ve el producto ni usa las palabras exactas.")
    + dec(None, "Es una técnica de <b>Advanced RAG</b>: búsqueda híbrida (densa + léxica) y multimodal (la foto embebida).")
    + dec(None, "<b>No cuesta nada por pedido</b>: BM25 y SigLIP 2 corren locales, y los vectores de las fotos se calculan una vez.")
    + "</div>"
    '<div class="grow"><div class="lab">La búsqueda, antes y después</div>'
    + hibrida_svg()
    + '<div class="lab" style="margin-top:12px">El caso del almohadón, con la versión 2</div>'
    '<div style="display:flex;gap:14px;align-items:center">' + fila_caso(V2)
    + f'<div class="cap" style="margin:0">El anotado sale <b>1.º</b> (antes, {caso[V1]["rank"]}.º){otro_txt}.</div></div>'
    "</div></div>"
    '<div class="take">Tres miradas del mismo producto: lo que dice su descripción, sus palabras exactas y su foto.</div>',
    kicker="Ejercicio 4 · 2 de 3 · el cambio y la configuración",
    title="Versión 2: búsqueda híbrida, una línea de configuración",
    notes="El cambio es una línea de configuración: rag.hybrid pasa de una lista vacía a BM25 y SigLIP 2. La búsqueda ahora calcula tres puntajes para cada producto que pasa el filtro: el coseno con la descripción, que ya estaba; BM25, las palabras; y SigLIP 2, la ficha en una frase contra la foto. Se estandarizan y se promedian. ¿Por qué este cambio? Sale de una limitación medida; es una técnica de Advanced RAG, búsqueda híbrida y multimodal; y no cuesta nada por pedido, porque corre local. En el caso del almohadón, ahora el anotado sale primero.",
    mins=0.8,
)

# resultados en las dos versiones
votos_h, votos_d = votos_v.count("hibrida"), votos_v.count("densa")
jv = JV["resumen"]
p_ver = p_signos(jv["hibrida"]["gana"], jv["densa"]["gana"])
difs_r = " · ".join(sg(x["hit@1"]) for x in [D21] + [h[V2]["vs_base"] for h in HIB_R])


def fila(label: str, a: str, b: str, d: str = "", cls: str = "") -> str:
    return f'<tr class="{cls}"><td>{label}</td><td class="c">{a}</td><td class="c v2">{b}</td><td>{d}</td></tr>'


slide(
    '<table class="t dosv"><tr><th></th><th class="c">Versión 1</th><th class="c">Versión 2</th><th>Diferencia</th></tr>'
    + fila("Configuración", "<code>rag.hybrid: []</code>", "<code>rag.hybrid: [bm25, siglip2]</code>", "densa → densa + léxica + foto")
    + f'<tr class="sec"><td colspan="4">Sobre el ground truth · {N_ANS} consultas con respuesta</td></tr>'
    + fila("hit@1", num(B1["hit@1"], 3), num(B2["hit@1"], 3), dif(D21))
    + fila("hit@5 (lo que ve el que elige)", num(B1["hit@5"], 3), num(B2["hit@5"], 3), dif(D21, "hit@5"))
    + fila("MRR@10", num(B1["mrr@10"], 3), num(B2["mrr@10"], 3), dif(D21, "mrr@10"))
    + fila("hit@1 con tres redactores (media ± desvío)", media_desvio(v1s), media_desvio(v2s), f"{difs_r}: se repite con los tres")
    + f'<tr class="sec"><td colspan="4">De punta a punta · {JV["ambientes"]} ambientes vacíos reales, el mismo plan, el juez en los dos órdenes</td></tr>'
    + fila("Ambientes que gana", str(jv["densa"]["gana"]), str(jv["hibrida"]["gana"]), f'{JV["empates"]} empates · {votos_h} votos a {votos_d} · p = {num(p_ver)}')
    + fila("Productos útiles según el juez", num(jv["densa"]["util"]), num(jv["hibrida"]["util"]))
    + fila("Costo por pedido", f"US${num(c_pedido)}", "igual", "BM25 y SigLIP 2 corren locales")
    + "</table>"
    '<div class="grid2" style="margin-top:14px;gap:20px">'
    '<div class="find" style="font-size:15.5px"><b>Lo que es claro.</b> En el ground truth, los intervalos de la diferencia no tocan el cero, y la mejora se repite con los tres redactores.</div>'
    f'<div class="decision" style="margin:0;font-size:15.5px"><b>Lo que no.</b> De punta a punta son {JV["ambientes"]} ambientes: {jv["hibrida"]["gana"]} a {jv["densa"]["gana"]} da p = {num(p_ver)}, y en {JV["empates"]} el juez no se decide. El ruido solo (la versión 2 contra sí misma) reparte {jr["hibrida"]["gana"]} a {jr["hibrida_bis"]["gana"]}.</div>'
    "</div>"
    '<div class="take">La versión 2 es hoy la búsqueda del flujo: clara en el ground truth, y <b>“no peor, probablemente mejor”</b> en la tarea real. La versión 1 queda a una línea.</div>',
    kicker="Ejercicio 4 · 3 de 3 · resultados en las dos versiones",
    title="Resultados: gana en el ground truth y no pierde con el juez",
    notes=f"Los resultados en las dos versiones. Sobre el ground truth: hit@1 pasa de {num(B1['hit@1'], 3)} a {num(B2['hit@1'], 3)}, y hit@5, lo que ve el que elige, de {num(B1['hit@5'], 3)} a {num(B2['hit@5'], 3)}. Las diferencias son pareadas y sus intervalos no tocan el cero; con los otros dos redactores, la mejora se repite. De punta a punta, en los {JV['ambientes']} ambientes, con el mismo plan y el juez en los dos órdenes: la versión 2 gana {jv['hibrida']['gana']}, empata {JV['empates']} y no pierde ninguno. Los productos útiles pasan de {num(jv['densa']['util'])} a {num(jv['hibrida']['util'])}, y el costo es el mismo. Con honestidad: lo del ground truth es claro; de punta a punta son once ambientes, cinco a cero da p igual a {num(p_ver)}, y en seis el juez no se decide; la misma configuración contra sí misma reparte tres a tres. Clara en el banco; no peor, probablemente mejor, en la tarea real.",
    mins=1.05,
)

# ================================================================================================
# Cierre
# ================================================================================================
# costos: del registro de gastos (datos/resultados/gastos.jsonl), como datos/resultados/gastos.md


def cuenta(r: dict) -> str:
    return r.get("pool") or r.get("provider") or "?"


gasto = {a: sum(r["cost_usd"] for r in LEDGER if cuenta(r) == a) for a in ("anthropic", "fal")}
por_uso: dict[str, float] = {}
for r in LEDGER:
    por_uso[purpose(r["step"])] = por_uso.get(purpose(r["step"]), 0.0) + r["cost_usd"]
CORTO = {
    "Evaluación: un VLM ordena el top-10 (ground truth de IKEA)": "evaluar el reranking con un VLM",
    "El flujo: elección de la lista": "el flujo: la elección",
    "Catálogo: descripciones de los productos de ABO": "describir el catálogo de ABO",
    "Evaluación de punta a punta: juez que compara dos listas": "el juez de punta a punta",
    "Réplica de un ambiente real (ubicación de los muebles)": "la réplica de un ambiente",
    "El flujo: imagen del ambiente amoblado": "el flujo: las imágenes",
    "Experimento: elegir con el catálogo entero en el prompt": "el catálogo entero en el prompt",
    "Evaluación del generador: faithfulness": "el juez de faithfulness",
    "El flujo: plan (lee la foto y el pedido, escribe las consultas)": "el flujo: el plan",
}
top_uso = sorted(por_uso.items(), key=lambda kv: -kv[1])[:6]
assert all(k in CORTO for k, _ in top_uso), [k for k, _ in top_uso]
ch = [r["cost_usd"] for r in LEDGER if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == "furnish.choose"]
c_desc = sum(r["cost_usd"] for r in LEDGER if r["step"].startswith("catalog.describe")) / 759  # los 759 listados de ABO que se mandaron a describir
slide(
    '<div class="grid4">'
    f'<div class="card"><div class="big">~US${num(c_pedido)}</div><div class="bignote">por pedido: plan US${num(c_plan)}, elección US${num(c_choose)} (de {num(min(ch))} a {num(max(ch))}, según las piezas y el catálogo) e imagen US${num(c_img)} por intento.</div></div>'
    f'<div class="card"><div class="big">US${num(sum(gasto.values()), 0)}</div><div class="bignote">todo el trabajo: Anthropic US${num(gasto["anthropic"])} (tope de {num(CFG.budget.accounts["anthropic"], 0)}) y fal US${num(gasto["fal"])}.</div></div>'
    f'<div class="card"><div class="big">~US${num(c_desc, 3)}</div><div class="bignote">por producto, una vez: describir el catálogo de Amazon con Opus por la API.</div></div>'
    '<div class="card"><div class="big">0</div><div class="bignote">por pedido para buscar: Qwen3, BM25, SigLIP 2 y ChromaDB corren locales, en CPU.</div></div>'
    "</div>"
    '<div class="row" style="gap:40px;margin-top:22px">'
    '<div><div class="lab">En qué se fue (US$)</div>'
    + hbars([{"label": CORTO[k], "value": v, "hl": i == 0} for i, (k, v) in enumerate(top_uso)], xmax=max(v for _, v in top_uso), width=600, label_w=250, row_h=27)
    + "</div>"
    '<div class="grow"><p class="small" style="font-size:15px">Cada llamada paga queda en un registro con su costo, sus tokens y su latencia, con <b>topes por cuenta</b> que cortan antes de pasarse.</p>'
    '<p class="small" style="font-size:15px">Las respuestas de los jueces y del reranking quedan en caché: repetir un experimento no se vuelve a pagar.</p>'
    '<p class="small" style="font-size:15px">Sin LangSmith: el registro propio y la carpeta de cada corrida ya dan el costo, los tokens y la traza de cada paso.</p></div>'
    "</div>"
    '<div class="take">Un pedido cuesta menos de 30 centavos de dólar, y buscar no cuesta nada: lo que se paga es <b>elegir</b> y <b>dibujar</b>.</div>',
    kicker="Costo",
    title="Cuánto cuesta un pedido, y cuánto costó el trabajo",
    notes=f"Costos, del registro de gastos. Un pedido cuesta unos {round(100 * c_pedido)} centavos de dólar: {round(100 * c_plan)} el plan, {round(100 * c_choose)} la elección y {round(100 * c_img)} la imagen. Buscar no cuesta nada: todo corre local. El trabajo entero costó {round(sum(gasto.values()))} dólares; lo más caro fue evaluar el reranking con el VLM. Cada llamada paga queda registrada, con topes por cuenta, y lo ya pagado queda en caché.",
    mins=0.5,
)

# limitaciones
no_sostenido = 1 - F["global"]
dh = DIAG["hibrida"]
slide(
    '<div class="grid2">'
    '<div class="card"><h3>Del sistema</h3><ul class="small">'
    f"<li><b>No dice “no hay”</b>: cuando el catálogo no tiene lo pedido, pone lo más parecido sin avisar (dejó afuera {dh['piezas_dejadas_afuera']} de {dh['piezas']} piezas).</li>"
    f"<li><b>El tamaño no se puede verificar</b>: el límite lo estima el plan a ojo, y solo el {num(100 * ikea_con_medida, 0)} % de IKEA tiene alguna medida. El filtro de medidas cambia {FM['candidatos_reemplazados']} de {FM['candidatos']} candidatos, sin evidencia de que mejore la lista.</li>"
    f"<li><b>La imagen es una visualización</b>: acierta el producto exacto 4 de cada 10 veces y conserva el cuarto en {IMG_TOT['pasan']} de {len(FINALES)}.</li>"
    f"<li><b>El generador afirma maderas que no ve</b>: el {num(100 * no_sostenido, 0)} % de las afirmaciones del porqué no se sostiene.</li>"
    "<li>Catálogos viejos y de uso no comercial (IKEA 2013, Amazon 2019–20).</li></ul></div>"
    '<div class="card"><h3>De la evaluación</h3><ul class="small">'
    "<li><b>El banco de la búsqueda es de producto conocido</b>, lo escribió el mismo modelo que las descripciones y no hay conjunto apartado.</li>"
    f"<li><b>De punta a punta son {len(AMBIENTES)} ambientes</b>, con un juez que es el mismo modelo que elige, sin validar contra personas.</li>"
    "<li><b>El pedido abierto no está evaluado</b>: los pedidos enumeran las piezas.</li>"
    f"<li><b>El que elige no es determinístico</b>: entre dos corridas iguales cambia {ruido_cambian} de {ruido_total} productos. El plan y la imagen no se repitieron.</li></ul></div>"
    "</div>"
    '<div class="take">Ninguna invalida la lista: los productos son reales y salen de la búsqueda. Sí acotan <b>cuánto podemos afirmar</b>.</div>',
    kicker="Cierre",
    title="Limitaciones",
    notes=f"Limitaciones. Del sistema: no dice “no hay”, pone lo más parecido sin avisar; el tamaño no se puede verificar; la imagen es una visualización; y el generador afirma maderas que no ve. De la evaluación: el banco de la búsqueda es de producto conocido y no hay conjunto apartado; de punta a punta son {len(AMBIENTES)} ambientes, con un juez sin validar contra personas; y ninguna corrida se repitió.",
    mins=0.55,
)

# trabajo futuro, con la réplica: indicar el lugar ayuda
RV = {k: v["resumen"]["iou_medio"]["media"] for k, v in REPLICA["variantes"].items()}
REP = R / "replica" / "living-dagarna"
slide(
    '<div class="row" style="gap:36px">'
    '<div style="width:540px"><div class="lab">Lo próximo, del RAG y de la evaluación</div>'
    + dec(None, "<b>Que diga “no hay”</b>: que el que elige avise cuando ningún candidato cumple, y mostrarlo.")
    + dec(None, "<b>Un banco escrito por personas</b>, con un conjunto apartado, y el voto a ciegas del equipo para validar al juez.")
    + dec(None, "<b>Mirar la imagen con un juez o con personas</b>: hoy medimos si están los productos y si es el mismo cuarto, no si la distribución tiene sentido.")
    + dec(None, "<b>Pasarle los materiales al que elige</b>: hoy ve el tipo y la medida, y adivina la madera por la foto.")
    + dec(None, "<b>Medidas reales del ambiente</b> (un metro en la foto, profundidad métrica): el filtro de tamaño sería un filtro de verdad.")
    + dec(None, f"<b>Un modelo más barato para elegir</b>: hoy es Opus (US${num(c_choose)} por pedido), y no medimos cuánto se pierde con uno menor.")
    + dec(None, "<b>Un catálogo actual</b>, con precio y stock como filtros de metadata.")
    + "</div>"
    '<div class="grow"><div class="lab">Fuera del RAG: ubicar los muebles (una prueba)</div>'
    + hbars(
        [
            {"label": "sin indicar el lugar", "value": RV["simple_sin_cajas"]},
            {"label": "dicho en palabras", "value": RV["simple_texto"]},
            {"label": "rectángulos dibujados", "value": RV["simple_cajas"]},
            {"label": "cajas 3D dibujadas", "value": RV["simple_cajas_3d"], "hl": True},
        ],
        xmax=1.0,
        width=560,
        label_w=180,
        row_h=28,
    )
    + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:6px" class="fix h125">'
    f'<div>{img(REP / "real_con_cajas_3d.jpg", 500, cls="photo")}<div class="cap" style="margin-top:3px">La foto real, con las cajas 3D de sus muebles.</div></div>'
    f'<div>{img(REP / "simple_cajas_3d" / "2.png", 500, cls="photo")}<div class="cap" style="margin-top:3px">Generada con esas cajas sobre la foto vacía.</div></div></div>'
    f'<p class="tiny" style="margin-top:8px">IoU medio con la posición real. Un living del ground truth de IKEA, vaciado y vuelto a amoblar con sus {len(REPLICA["productos"])} muebles: un solo cuarto, 3 imágenes por variante (en la primera ronda, {num(RV["sin_cajas"])}, {num(RV["con_cajas"])} y {num(RV["con_cajas_3d"])}). Lo único que se sostiene: <b>indicar el lugar ayuda</b>.</p>'
    "</div></div>"
    '<div class="take">Lo próximo es del RAG y de cómo lo medimos. Ubicar cada mueble a escala pide medir el ambiente: queda como trabajo futuro.</div>',
    kicker="Cierre",
    title="Trabajo futuro",
    notes="Trabajo futuro. Lo próximo es del RAG y de cómo lo medimos: que el sistema diga “no hay”; un banco de consultas escrito por personas, con un conjunto apartado; validar al juez con nuestro voto a ciegas, y repetir corridas. Más lejos: medidas reales del ambiente y un catálogo actual. Y fuera del RAG hicimos una prueba: vaciamos un living real y lo volvimos a amoblar con sus muebles. Es un solo cuarto; lo único que se sostiene es que indicarle al modelo dónde va cada mueble ayuda.",
    mins=0.65,
)

# conclusiones
CIERRE = ["publica-loft-industrial", "publica-living-japandi", "publica-living-bohemio", "publica-comedor-clasico-moderno"]
assert all(f["img"]["attempts"][0]["ok"] for f in FINALES if f["slug"] in CIERRE), "las del cierre tienen que haber pasado el control al primer intento"
slide(
    '<div class="steps" style="max-width:1080px">'
    f'<div><p><b>Lo que más pesa es la base de conocimiento y cómo se escribe la consulta</b>: describir cada producto desde su foto ({sg(d_desc["hit@1"], 2)} de hit@1) y escribir la consulta como una ficha del catálogo ({sg(d_hyde["hit@1"], 2)}). El embedder, en este banco, casi no importa.</p></div>'
    f'<div><p><b>La versión 2 es la búsqueda híbrida</b>: la descripción, sus palabras y la foto suman {sg(D21["hit@1"], 3)} de hit@1 sobre la versión 1, sin costo por pedido; de punta a punta gana {jv["hibrida"]["gana"]}, empata {JV["empates"]} y no pierde.</p></div>'
    f'<div><p><b>La búsqueda aporta en la tarea real</b>: {sa["densa"]["gana"]} a {sa["azar"]["gana"]} contra candidatos al azar del mismo kind.</p></div>'
    "<div><p><b>Medir bien fue la mitad del trabajo</b>: diferencias pareadas, tres redactores, un juez en los dos órdenes, y las trampas dichas en voz alta. Nos hizo cambiar el número de cabecera y rehacer las métricas del generador.</p></div>"
    f'<div><p><b>La lista es confiable; la imagen es una visualización</b>: los productos son reales y validados, pero la imagen reconoce el {num(100 * IMG_TOT["reconocidos"] / IMG_TOT["productos"], 0)} % y conserva el cuarto en {IMG_TOT["pasan"]} de {len(FINALES)}.</p></div>'
    "</div>"
    '<div class="lab" style="margin-top:auto">Cuatro de las once corridas de la configuración final (pasaron el control al primer intento)</div>'
    f'<div class="grid4 fix h140" style="gap:12px">{"".join(img(AMO / f"final-{s_}" / "final.png", 500, cls="photo") for s_ in CIERRE)}</div>'
    f'<div class="tiny" style="margin-top:5px">Fotos de los ambientes: {credito(*CIERRE)}.</div>',
    kicker="Cierre",
    title="Conclusiones",
    notes=f"Para cerrar. Uno: lo que más pesa es la base de conocimiento y cómo se escribe la consulta; el embedder casi no importa. Dos: la versión 2 es la búsqueda híbrida: suma en el ground truth, sin costo, y de punta a punta gana {jv['hibrida']['gana']}, empata {JV['empates']} y no pierde. Tres: la búsqueda aporta en la tarea real, {sa['densa']['gana']} a {sa['azar']['gana']} contra candidatos al azar. Cuatro: medir bien fue la mitad del trabajo; nos hizo cambiar el número de cabecera y rehacer las métricas del generador. Y cinco: la lista es confiable; la imagen es una visualización. Gracias.",
    mins=0.7,
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


def palabras(n: dict) -> int:
    """Las palabras que se dicen en una lámina (sus notas)."""
    nt = n["notes"]
    return len(" ".join(nt.values()).split()) if isinstance(nt, dict) else len(str(nt).split())


assert len(NOTES) == len(SLIDES)
total = sum(n["mins"] for n in NOTES)
dichas = sum(palabras(n) for n in NOTES)


def at(pred) -> int:
    return next(i for i, n in enumerate(NOTES) if pred(n))


rec_a = at(lambda n: n["title"] == "El recorrido")
rec_b = at(lambda n: n["kicker"].startswith(f"El recorrido · fase {len(FASES)} "))
mapa = at(lambda n: n["kicker"] == "Experimentos · el mapa")
cut1 = at(lambda n: n["kicker"] == "Desafíos")
cut2 = at(lambda n: n["kicker"] == "Experimento 4")
parts = [(0, cut1), (cut1, cut2), (cut2, len(NOTES))]
RAPIDAS = ("Experimentos · de trámite (1 de 2)", "Experimentos · de trámite (2 de 2)", "Costo")
lines_md = [
    "# Guion de la presentación (amoblai)",
    "",
    f"Generado por `docs/presentacion/build.py` junto con `amoblai.html`: los números salen de los mismos resultados que las slides y los extractos de los prompts, de los archivos de `src/amoblai/prompts/`. {len(SLIDES)} slides, unos {round(total)} minutos ({mmss(total)}); son unas {miles(round(dichas, -2))} palabras, a {round(dichas / total)} por minuto.",
    "",
    f"**El recorrido** (slides {rec_a + 1} a {rec_b + 1}). Arriba de cada lámina va el mapa de las once fases: la fase de la que se habla, encendida; las ya vistas, marcadas. "
    "Se sigue un mismo pedido real, con la configuración final (un loft de estilo industrial, sobre una foto pública), de la foto a la lista. "
    f"El mismo mapa vuelve en la slide {mapa + 1} con un pin por experimento sobre la fase a la que le hizo la pregunta (lleno: con lámina propia; hueco: de trámite), "
    "y cada lámina de experimento repite ese pin en un minimapa.",
    "",
    "**Cómo se pasa.** En cada experimento, primero se ve solo el porqué, la pregunta y qué se comparó. **Se cuentan esas dos cosas antes de avanzar.** "
    "La flecha (o espacio) muestra los resultados; otra flecha, la decisión. Flecha atrás vuelve un paso. Con `amoblai.html?todo` se ve todo de entrada (para revisar o imprimir).",
    "",
    "**Reparto sugerido** (a definir entre los tres):",
]
for k, (a, b) in enumerate(parts, 1):
    lines_md.append(f"- Parte {k}: slides {a + 1} a {b} ({strip_tags(NOTES[a]['title'] or 'Portada')} → {strip_tags(NOTES[b - 1]['title'])}), unos {round(sum(n['mins'] for n in NOTES[a:b]))} min.")
lines_md += [
    "",
    "Si falta tiempo, se pueden pasar rápido las dos láminas de trámite y la de costos (las marcadas con *).",
    "",
]
t = 0.0
for i, n in enumerate(NOTES, 1):
    head = n["title"] or n["kicker"] or "Portada"
    star = " *" if n["kicker"] in RAPIDAS else ""
    lines_md.append(f"## {i}. {strip_tags(head)}{star}")
    lines_md.append(f"*{n['kicker'] + ' · ' if n['kicker'] and n['title'] else ''}~{mmss(n['mins'])} min · desde el minuto {mmss(t)}*")
    lines_md.append("")
    nt = n["notes"]
    if isinstance(nt, dict) and nt:
        lines_md += [
            f"1. **Por qué lo hicimos y qué queríamos ver** (antes de avanzar): {nt['motivo']}",
            f"2. **Qué se comparó:** {nt['experimento']}",
            f"3. **→ Resultados** (flecha): {nt['resultados']}",
            f"4. **→ Decisión** (flecha): {nt['decision']}",
        ]
    elif nt:
        lines_md.append(nt)
    lines_md.append("")
    t += n["mins"]
GUION = OUT.with_name("guion.md")
GUION.write_text("\n".join(lines_md))
print(f"{GUION}: {mmss(total)} min, {dichas} palabras ({round(dichas / total)} por minuto)")
# El ritmo de cada lámina: avisa si alguna pide hablar más rápido de lo que se puede.
for i, n in enumerate(NOTES, 1):
    if n["mins"] >= 0.3 and palabras(n) / n["mins"] > 165:
        print(f"  ojo: la slide {i} ({strip_tags(n['title'])[:40]}) tiene {palabras(n)} palabras para {mmss(n['mins'])}: {round(palabras(n) / n['mins'])} por minuto")
if not 30 <= total <= 31:
    print(f"  ojo: el guion dura {mmss(total)}; tiene que quedar entre 30:00 y 31:00")
