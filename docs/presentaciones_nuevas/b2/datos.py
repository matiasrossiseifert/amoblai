"""Los datos de la presentación: todo número sale de los archivos de resultados, del catálogo y de
la config (los mismos que leía b_mismo_contenido/build.py). Nada se escribe a mano."""

from __future__ import annotations

import collections
import gzip
import html
import json
import re
import statistics
from pathlib import Path

import yaml
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
TRAB = OUT / "_trabajo"
D_ = ROOT / "datos"
RES = D_ / "resultados"
EV = RES / "evaluacion"
AM = RES / "amoblar"
REPL = RES / "replica" / "living-dagarna"

TRAB.mkdir(exist_ok=True)


# --- formato (coma decimal, como se dice) ---------------------------------------------------------

def f2(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def f3(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def f1(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def usd(x: float, nd: int = 2) -> str:
    return "US$" + f"{x:.{nd}f}".replace(".", ",")


def mmss(seg: int) -> str:
    return f"{seg // 60}:{seg % 60:02d}"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def jload(p: Path):
    return json.loads(p.read_text())


def metricas(run: str) -> dict:
    return jload(EV / run / "metricas.json")


def corrida(run: str) -> dict:
    return jload(EV / run / "corrida.json")


# --- corridas -------------------------------------------------------------------------------------

F = metricas("20261110-003643_ablacion-retrieval")          # catálogo final, todas las ablaciones
RR = metricas("20261109-235522_ablacion-reranking")         # reranking con Opus
C855 = metricas("20261023-173217_ablacion-retrieval")       # catálogo de 855
CREV = metricas("20261109-235406_ablacion-catalogo-revisado")
CTOD = metricas("20261110-010145_ablacion-catalogo-todos")
C268 = metricas("20261021-161057_ablacion-retrieval")       # catálogo de 268
TXT = metricas("20261021-133226_ablacion-texto")            # v1 contra v0, mismas fotos
REP2 = metricas("20261023-200437_reproducibilidad-r2")
REP3 = metricas("20261023-202248_reproducibilidad-r3")
CURVA = jload(RES / "evaluacion_candidatos" / "curva_k.json")
GRAD = jload(RES / "evaluacion_graduada" / "graduada.json")
J_ABO5 = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_abo_5ambientes.json")
J_TOD5 = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_todos_5ambientes.json")
J_TOD = jload(RES / "punta_a_punta" / "catalogos" / "juez_ikea_vs_todos.json")
V0_DIR = next((RES / "v0_imagen" / "corridas").glob("*retriever_abl-retriever-name-dinov3__method-none__category_filter-true"))
V0 = jload(V0_DIR / "metrics.json")
GRAD_RUN = metricas(GRAD["run"])

BASE = "qwen3|description|filtro-type"


def m(run: dict, key: str, met: str = "hit@1") -> float:
    return run[key][met]


def ic(run: dict, key: str, met: str = "hit@1"):
    return run[key].get(met + "_ic95")


ITEMS = {}
for _line in (D_ / "procesados" / "items.jsonl").read_text().splitlines():
    _it = json.loads(_line)
    ITEMS[_it["id"]] = _it
DESCR = {}
for _line in (D_ / "catalogo" / "descripciones.jsonl").read_text().splitlines():
    _it = json.loads(_line)
    DESCR[_it["id"]] = _it["text"]
ABO_DESCR = [json.loads(x) for x in (D_ / "catalogo" / "abo" / "descripciones.jsonl").read_text().splitlines()]

CATS = yaml.safe_load((D_ / "configs" / "categories.yaml").read_text())["categories"]
CFG = yaml.safe_load((D_ / "configs" / "amoblai.yaml").read_text())
try:
    from amoblai.config import FurnishConfig
    ROOM_CHECK = FurnishConfig().room_check
except Exception:  # sin el paquete: se lee del código fuente
    _src = (ROOT / "src" / "amoblai" / "config.py").read_text()
    _mm = re.search(r'"attempts": (\d+), "min_inliers": (\d+), "max_shift": ([\d.]+)', _src)
    ROOM_CHECK = {"attempts": int(_mm[1]), "min_inliers": int(_mm[2]), "max_shift": float(_mm[3])}

PEDIDOS = yaml.safe_load((D_ / "ambientes_vacios" / "pedidos.yaml").read_text())["ambientes"]
PUBLICAS = yaml.safe_load((D_ / "ambientes_vacios" / "publicas.yaml").read_text())["fotos"]
PUB_POR_ARCHIVO = {p["archivo"]: p for p in PUBLICAS}

GASTOS = [json.loads(x) for x in (RES / "gastos.jsonl").read_text().splitlines() if x.strip()]


def gasto(step: str, model: str | None = None):
    return [g["cost_usd"] for g in GASTOS if g["step"] == step and (model is None or g.get("model") == model) and not g.get("cached")]


def corrida_idx(run: str) -> dict:
    return corrida(run).get("index", {})


# --- números que se dicen -------------------------------------------------------------------------
D: dict = {}
D["n_busquedas"] = F[BASE]["searches"]
D["n_respondibles"] = F[BASE]["answerable"]
D["n_ambientes_gt"] = corrida("20261110-003643_ablacion-retrieval")["rooms"]
D["prod_268"] = corrida_idx("20261021-161057_ablacion-retrieval")["products"]
D["prod_855"] = corrida_idx("20261023-173217_ablacion-retrieval")["products"]
D["prod_819"] = corrida_idx("20261110-003643_ablacion-retrieval")["products"]
D["prod_todos"] = corrida_idx("20261110-010145_ablacion-catalogo-todos")["products"]
assert D["prod_819"] == len(ITEMS)
D["n_abo"] = sum(1 for x in ABO_DESCR if "(API)" in x.get("by", ""))
D["n_tipos"] = len(CATS)
D["n_kinds"] = len({it["kind"] for it in ITEMS.values()})

_corr_txt = (D_ / "catalogo" / "correcciones.yaml").read_text()
_rev = _corr_txt.split("# Revisión del catálogo ampliado", 1)[1].split("\n", 1)[1]
_rev_entries = yaml.safe_load(_rev) or {}
D["rev_afuera"] = sum(1 for v in _rev_entries.values() if v.get("excluir"))
D["rev_kinds"] = sum(1 for v in _rev_entries.values() if "kind" in v)
assert D["prod_855"] - D["rev_afuera"] == D["prod_819"]

_seats = [it for it in ITEMS.values() if it["category_tp"] in ("sofa", "armchair", "chair", "stool", "bench", "ottoman")]
D["asientos"] = len(_seats)
D["asientos_sin_medida"] = sum(1 for it in _seats if not it["dimensions_cm"])
_fotos_lado = collections.Counter(Image.open(ROOT / it["photos"][0]).size for it in list(ITEMS.values())[:60])
D["foto_lado"] = _fotos_lado.most_common(1)[0][0][0]
_wc = sorted(len(DESCR[i].split()) for i in ITEMS)
D["palabras_lo"] = (_wc[len(_wc) // 20] // 10) * 10
D["palabras_hi"] = -(-_wc[-(len(_wc) // 20)] // 10) * 10

D["n_ambientes_vacios"] = len(PEDIDOS)
D["n_publicos"] = sum(1 for p in PEDIDOS if p["slug"].startswith("publica"))
D["n_propios"] = D["n_ambientes_vacios"] - D["n_publicos"]
D["n_publicas_revisadas"] = len(PUBLICAS)

D["v0_hit1"] = V0["retrieval"]["hit@1"]
D["v0_ic"] = V0["retrieval"].get("hit@1_ci95")
D["v0_n"] = V0["retrieval"]["n"]
D["v1_hit1"] = m(TXT, BASE)
D["v1_n"] = TXT[BASE]["answerable"]

D["k_flujo"] = CFG["furnish"]["candidates"]

# experimento 1
D["e1_vendedor"] = m(F, "qwen3|seller|filtro-type")
D["e1_desc"] = m(F, BASE)
D["e1_desc_kind"] = m(F, "qwen3|description|filtro-kind")
D["e1_nombre_kind"] = m(F, "qwen3|name+description|filtro-kind")
D["e1_veces"] = D["e1_desc"] / D["e1_vendedor"]
# experimento 2
D["e2"] = {e: (m(F, f"{e}|description|filtro-type"), m(F, f"{e}|description|filtro-type", "mrr@10")) for e in ("hashing", "bge", "qwen3")}
# experimento 3
D["e3"] = {f: (m(F, f"qwen3|description|filtro-{f}"), m(F, f"qwen3|description|filtro-{f}", "hit@10")) for f in ("none", "type", "kind")}
# experimento 4
D["e4"] = {"whole": m(F, BASE), "aligned": m(F, BASE + "|chunks-lines-aligned"), "max": m(F, BASE + "|chunks-lines-max")}
# experimento 5
D["e5"] = [(d, m(F, BASE + f"|dim-{d}"), ic(F, BASE + f"|dim-{d}")) for d in (32, 64, 128, 256, 512)] + [(1024, m(F, BASE), ic(F, BASE))]
# experimento 6
D["e6_exacta"] = m(F, BASE + "|exact")
D["e6_hnsw"] = m(F, BASE)
D["e6_type"] = m(F, BASE + "|consulta-type")
D["e6_kind"] = m(F, BASE + "|consulta-kind")
# experimento 7
D["e7_base"] = (m(RR, BASE), m(RR, BASE, "mrr@10"), m(RR, BASE, "hit@10"))
D["e7_minilm"] = (m(F, BASE + "|rerank-minilm-reranker"), m(F, BASE + "|rerank-minilm-reranker", "mrr@10"))
D["e7_opus"] = (m(RR, BASE + "|rerank-opus"), m(RR, BASE + "|rerank-opus", "mrr@10"))
D["e7_costo"] = statistics.mean(gasto("eval.rerank", "claude-opus-5-5"))
# experimento 8
D["curva"] = {int(k): v for k, v in CURVA["por_k"].items()}
D["e8_falta3"] = 1 - D["curva"][3]["techo_hit@k"]
# experimento 9
D["e9"] = [(D["prod_268"], m(C268, BASE), C268[BASE]["searches"]), (D["prod_855"], m(C855, BASE), C855[BASE]["searches"]),
           (D["prod_819"], m(CREV, BASE), CREV[BASE]["searches"])]


# experimento 10
def resumen_juez(j: dict, filtro=None):
    rows = [r for r in j["detalle"] if filtro is None or filtro(r["slug"])]
    a, b = j["a"], j["b"]
    gana_a = sum(1 for r in rows if r["ganador"] == a)
    gana_b = sum(1 for r in rows if r["ganador"] == b)
    emp = sum(1 for r in rows if r["ganador"] not in (a, b))

    def util(side):
        n = t = 0
        for r in rows:
            for p in r["puntajes"][side]:
                n += len(p["grades"])
                t += sum(1 for g in p["grades"] if g == 2)
        return t / n
    return {"n": len(rows), "a": gana_a, "b": gana_b, "emp": emp, "util_a": util(a), "util_b": util(b), "rows": rows,
            "lado_a": a, "lado_b": b}


def es_pub(s: str) -> bool:
    return s.startswith("publica")


D["j_abo5"] = resumen_juez(J_ABO5)
D["j_tod5"] = resumen_juez(J_TOD5)
D["j_nord"] = resumen_juez(J_TOD, lambda s: not es_pub(s))
D["j_otros"] = resumen_juez(J_TOD, es_pub)
D["j_todos"] = resumen_juez(J_TOD)
D["j_acuerdo"] = J_TOD["acuerdo_entre_ordenes"]
D["e10_gt_ikea"] = m(F, BASE)
D["e10_gt_todos"] = m(CTOD, BASE)
# experimento 11
D["g_n"] = GRAD["consultas"]["todas"]["n"]
D["g_anot2"] = GRAD["acuerdo_con_gt"]["anotado_con_2"]
D["g_otros2"] = GRAD["acuerdo_con_gt"]["otros_con_2"]
D["g_util1"] = GRAD["consultas"]["todas"]["util1"]
D["g_util1_ic"] = GRAD["consultas"]["todas"]["util1_ic95"]
D["g_hit1"] = m(GRAD_RUN, GRAD["method"])
D["g_hit1_ic"] = ic(GRAD_RUN, GRAD["method"])
D["rep"] = [m(C855, BASE), m(REP2, BASE), m(REP3, BASE)]
D["rep_sd"] = statistics.stdev(D["rep"])


# experimento 12
def img_metrics(run):
    return jload(AM / run / "6_metricas_imagen.json")


E12_RUNS = ("experimento", "experimento-libre", "experimento-buen-pedido", "experimento-buen-pedido-estricto")
D["e12"] = {}
D["e12_piezas"] = {r: len(jload(AM / r / "3_choice.json")["answer"]["choices"]) for r in E12_RUNS}
for _r in E12_RUNS:
    _mi = img_metrics(_r)["ambiente"]
    D["e12"][_r] = (_mi["sift_inliers"], _mi["ssim_fuera_de_los_muebles"])
# punta a punta
D["cab_liv"] = jload(AM / "caballito-living" / "5_image.json")
D["cab_com"] = jload(AM / "caballito-comedor" / "5_image.json")


# costos
def costo_pedido(carpeta: Path) -> float:
    t = 0.0
    for fn in ("1_searches.json", "3_choice.json"):
        p = carpeta / fn
        if p.exists():
            t += jload(p).get("cost_usd") or 0
    return t


_cp = [costo_pedido(p) for p in sorted((RES / "punta_a_punta" / "catalogos" / "todos").iterdir()) if p.is_dir()]
D["costo_n"] = len(_cp)
D["costo_claude"] = statistics.mean(_cp)
D["costo_imagen"] = CFG["furnish"]["generators"]["nano_banana_2"]["usd_per_image"]["1K"]
D["costo_describir"] = sum(gasto("catalog.describe")) / D["n_abo"]
# camino
D["camino"] = [
    ("Texto del vendedor + bolsa de palabras", m(F, "hashing|seller|filtro-none")),
    ("+ descripción del VLM", m(F, "hashing|description|filtro-none")),
    ("+ Qwen3-Embedding", m(F, "qwen3|description|filtro-none")),
    ("+ filtro por tipo", m(F, BASE)),
    ("+ un VLM reordena el top-10", m(RR, BASE + "|rerank-opus")),
]

# --- el caso que recorre la charla (rincón de lectura, edición estricta) -------------------------
HERO = AM / "experimento-buen-pedido-estricto"
HERO_REQ = jload(HERO / "request.json")["request"]
HERO_CHOICE = jload(HERO / "3_choice.json")["answer"]["choices"]
HERO_CAND = jload(HERO / "2_candidates.json")["pieces"]
CAND_INFO = {c["id"]: c for p in HERO_CAND for c in p["candidates"]}
N_HERO = len(HERO_CHOICE)
N_HERO_UNID = sum(ch["quantity"] for ch in HERO_CHOICE)
HERO_IMG = img_metrics("experimento-buen-pedido-estricto")

KIND_ES = {
    "bookcase": "Biblioteca", "armchair": "Sillón", "floor lamp": "Lámpara de pie", "side table": "Mesita",
    "rug": "Alfombra", "throw": "Manta", "cushion": "Almohadón", "curtains": "Cortinas", "plant": "Planta",
    "coffee table": "Mesa ratona", "sofa": "Sofá", "pendant lamp": "Lámpara colgante", "TV stand": "Mueble de TV",
    "dining table": "Mesa de comedor", "dining chair": "Silla", "sideboard": "Aparador", "desk lamp": "Lámpara de escritorio",
    "display cabinet": "Vitrina", "console table": "Mesa consola", "picture frame": "Marco", "ottoman": "Puf",
    "shelving unit": "Estantería",
}


def medida(dim) -> str:
    if not dim:
        return ""
    w, dd = dim.get("width"), dim.get("depth")
    if w and dd:
        return f"{w:g} × {dd:g} cm"
    if w:
        return f"{w:g} cm de ancho"
    return ""


# --- ground truth: un living real de IKEA, con sus búsquedas ------------------------------------
GT_ROOM = "ikea-find-your-living-room-design-inspiration__1364308433351-s4.jpg"
GT_ROOM_PATH = "datos/dataset/ikea/images/room_scenes/" + GT_ROOM
RANK_ROWS = {}
with gzip.open(EV / "20261110-003643_ablacion-retrieval" / "rankings.jsonl.gz", "rt") as _fh:
    for _line in _fh:
        _r = json.loads(_line)
        if _r["method"] == BASE and _r["room_id"] == GT_ROOM:
            RANK_ROWS[_r["piece"]] = _r
GT_ANY = [x for x in RANK_ROWS[0]["relevant_any"] if x in ITEMS]
Q_MESA = next(r for r in RANK_ROWS.values() if r["kind"] == "coffee table")
Q_LAMPARA = next(r for r in RANK_ROWS.values() if r["kind"] == "floor lamp")

# v0: el recorte del sofá en ese mismo living
V0_REC = None
for _line in (V0_DIR / "recortes.jsonl").read_text().splitlines():
    _r = json.loads(_line)
    if _r["room_id"] == GT_ROOM and _r["category"] == "sofa":
        V0_REC = _r
V0_SOFA_OK = V0_REC["relevant"][1] if V0_REC["relevant"][1] in V0_REC["ranked_skus"] else V0_REC["relevant"][0]

# --- ambientes vacíos ---------------------------------------------------------------------------
ESTILO = {
    "caballito-living": ("Living", "moderno, luminoso"), "caballito-comedor": ("Comedor", "nórdico"),
    "alvear-escritorio": ("Escritorio", "nórdico"), "alvear-living-comedor": ("Living comedor", "nórdico"),
    "experimento-lectura": ("Rincón de lectura", "cálido, maderas"),
    "publica-loft-industrial": ("Loft", "industrial"), "publica-living-clasico": ("Sala con chimenea", "clásico"),
    "publica-comedor-clasico-moderno": ("Comedor abierto", "clásico actual"), "publica-living-japandi": ("Living", "japandi"),
    "publica-living-bohemio": ("Living", "bohemio"), "publica-estudio-sobrio": ("Estudio", "moderno sobrio"),
}

# --- réplica de un living del ground truth (E13) y cajas (pasos a futuro) ------------------------
REPLICA = jload(REPL / "resultados.json")
REPL_N = len(REPLICA["productos"])
REPL_CORTO = {"802.991.95": "sofá", "702.991.91": "puf", "802.133.09": "mesa ratona",
              "302.837.81": "alfombra", "599.026.58": "estantería", "302.865.67": "lámpara"}
# Ronda 1 (prompt largo) y ronda 2 (un prompt corto común; cambia la línea de dónde va cada mueble):
# (clave en resultados.json, letra, nombre, cómo se le dice dónde)
REPL_R1 = [("sin_cajas", "", "Sin decir dónde", ""), ("con_cajas", "", "Cajas 2D en la foto", ""),
           ("con_cajas_3d", "", "Cajas 3D en la foto", "")]
REPL_R2 = [("simple_sin_cajas", "A", "Sin decir dónde", "el modelo los ubica"),
           ("simple_texto", "B", "En palabras", "una o dos frases por mueble"),
           ("simple_cajas", "C", "Cajas 2D en la foto", "dibujadas, y que las borre"),
           ("simple_cajas_guia", "D", "Cajas 2D aparte", "la foto limpia y, al final, una copia con las cajas"),
           ("simple_cajas_3d", "E", "Cajas 3D en la foto", "dibujadas, y que las borre"),
           ("simple_cajas_3d_guia", "F", "Cajas 3D aparte", "la foto limpia y, al final, una copia con las cajas")]


def replica_por_producto(variant: str) -> dict[str, float]:
    """IoU medio de cada producto en las repeticiones (no detectado = 0)."""
    out: dict[str, list[float]] = {}
    for r in REPLICA["variantes"][variant]["imagenes"]:
        for p in r["productos"]:
            out.setdefault(p["id"], []).append(p.get("iou") or 0.0)
    return {k: sum(v) / len(v) for k, v in out.items()}


def cajas_dibujadas(img: str):
    """True si la observación dice que el modelo dejó las cajas dibujadas, False si no quedó rastro,
    None si esa imagen no tiene observación escrita."""
    obs = REPLICA.get("observaciones", {}).get(img)
    if not obs:
        return None
    o = obs.lower()
    if "sin rastro" in o or o.startswith("limpia"):
        return False
    if "dibujad" in o or "deja" in o or "copia los" in o:
        return True
    return None


for _v, *_ in REPL_R1 + REPL_R2:
    assert all((REPL / r["imagen"]).exists() for r in REPLICA["variantes"][_v]["imagenes"]), _v
