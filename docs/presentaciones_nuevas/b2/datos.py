"""Los datos de la presentación: todo número sale de los archivos de resultados, del catálogo y de
la config (los mismos que lee docs/presentacion/build.py). Nada se escribe a mano, salvo lo de DOC:
lo que solo está en los documentos, con la sección de la que sale."""

from __future__ import annotations

import collections
import gzip
import html
import json
import re
import statistics
from math import comb
from pathlib import Path

import yaml
from PIL import Image

from amoblai.config import load_config
from amoblai.evaluation.metrics import bootstrap_ci
from amoblai.evaluation.retrieval import paired_difference
from amoblai.rag.filters import Filters
from amoblai.rag.hybrid import visual_query

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


def miles(n: int) -> str:
    """1.502 (punto de miles)."""
    return f"{n:,}".replace(",", ".")


def mmss(seg: int) -> str:
    return f"{seg // 60}:{seg % 60:02d}"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def sg(x: float, nd: int = 3) -> str:
    """+0,075 o −0,005: con signo."""
    return ("−" if x < 0 else "+") + f"{abs(x):.{nd}f}".replace(".", ",")


def ic_txt(lo: float, hi: float, nd: int = 3) -> str:
    """[0,041; 0,111]; con signos cuando no es todo positivo: [−0,015; +0,006]."""
    n = lambda v: f"{v:.{nd}f}".replace(".", ",")  # noqa: E731
    return f"[{n(lo)}; {n(hi)}]" if lo >= 0 else f"[{sg(lo, nd)}; {sg(hi, nd)}]"


def dif(v: dict, k: str = "hit@1", nd: int = 3, flip: bool = False) -> str:
    """Una diferencia pareada con su IC 95%: +0,075 [0,041; 0,111]. `flip`: al revés (b − a)."""
    x, (lo, hi) = v[k], v[f"{k}_ic95"]
    if flip:
        x, lo, hi = -x, -hi, -lo
    return f"{sg(x, nd)} {ic_txt(lo, hi, nd)}"


def nb(s: str) -> str:
    """Sin cortes de línea adentro (una diferencia con su intervalo)."""
    return f'<span class="nb">{s}</span>'


def jload(p: Path):
    return json.loads(Path(p).read_text())


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def ultima(sufijo: str) -> Path:
    """La última corrida de evaluación cuyo nombre termina así (y tiene métricas)."""
    return sorted(d for d in EV.iterdir() if d.name.endswith(sufijo) and (d / "metricas.json").exists())[-1]


def metricas(run) -> dict:
    return jload((run if isinstance(run, Path) else EV / run) / "metricas.json")


def corrida(run) -> dict:
    return jload((run if isinstance(run, Path) else EV / run) / "corrida.json")


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
    """a − b sobre las mismas consultas, con su IC 95% por bootstrap de ambientes: la cuenta de
    `vs_base` (evaluation/retrieval.py), hecha acá para las corridas anteriores a esa columna."""
    return paired_difference(rankings(run)[a], rankings(run_b or run)[b])


def p_signos(a: int, b: int) -> float:
    """Test de signos a dos colas sobre los ambientes decididos (a ganados, b perdidos)."""
    n, k = a + b, max(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2**n)


def media_desvio(xs: list[float]) -> str:
    return f"{f3(statistics.mean(xs))} ± {f3(statistics.stdev(xs))}"


# --- corridas -------------------------------------------------------------------------------------
# El buscador, sobre el ground truth de IKEA (549 consultas con respuesta, catálogo de 819).
ABL_DIR = ultima("_ablacion-retrieval")                   # la grilla: embedder, dimensión, splitting, base
F = metricas(ABL_DIR)
RR_DIR = ultima("_ablacion-reranking")                    # un VLM ordena el top-10 mirando las fotos
RR = metricas(RR_DIR)
CAM = metricas(ultima("_ablacion-camino"))                # el camino incremental, un cambio por paso
CON = metricas(ultima("_ablacion-consulta"))              # la ficha contra la frase natural
HIB_DIR = ultima("_ablacion-hibrido")                     # léxica, por foto y fusiones
HIB = metricas(HIB_DIR)
HIB_R = [metricas(ultima(f"_ablacion-hibrido-{r}")) for r in ("r2", "r3")]  # los otros dos redactores
EMB = metricas(ultima("_ablacion-embedders"))             # embedders con el filtro del flujo, exacto y por familia
RLOC = metricas(ultima("_ablacion-reranking-local"))      # Qwen3-Reranker
LIN = metricas(ultima("_ablacion-lineas"))                # qué líneas de la descripción hacen el trabajo
TODOS_DIR = ultima("_ablacion-catalogo-todos")            # las mismas consultas con ABO de distractores
CTOD = metricas(TODOS_DIR)
C855 = metricas("20261023-173217_ablacion-retrieval")     # catálogo de 855
CREV = metricas(ultima("_ablacion-catalogo-revisado"))
C268 = metricas("20261021-161057_ablacion-retrieval")     # catálogo de 268
TXT_DIR = EV / "20261021-133226_ablacion-texto"           # texto contra imagen, mismas fotos (catálogo de 275)
CURVA = jload(RES / "evaluacion_candidatos" / "curva_k.json")
GRAD = jload(RES / "evaluacion_graduada" / "graduada.json")
GRAD_RUN = metricas(GRAD["run"])
# El flujo entero, sobre ambientes vacíos reales: el juez de listas y el diagnóstico sin juez.
PAP = RES / "punta_a_punta"
JV = jload(PAP / "hibrida" / "juez_densa_vs_hibrida.json")            # versión 1 contra versión 2
JA = jload(PAP / "hibrida" / "juez_densa_vs_azar_7ambientes.json")    # con búsqueda contra sin búsqueda
JC = jload(PAP / "catalogos" / "juez_ikea_vs_todos.json")             # IKEA contra IKEA + ABO
J_ABO5 = jload(PAP / "catalogos" / "juez_ikea_vs_abo_5ambientes.json")
DIAG = jload(PAP / "hibrida" / "diagnostico.json")
DIAG_CAT = jload(PAP / "catalogos" / "diagnostico.json")
RESP2 = jload(RES / "evaluacion_respuesta" / "resumen_version2.json")  # faithfulness y answer relevance (jueces v2) sobre las 11 listas de la versión 2: el flujo de hoy
RESP = jload(RES / "evaluacion_respuesta" / "resumen.json")           # lo mismo sobre otras 11 listas (la búsqueda de la versión 1): la réplica
JR = jload(PAP / "hibrida" / "juez_hibrida_vs_hibrida_bis.json")      # el piso de ruido: la versión 2 corrida dos veces
IMG_PL = jload(RES / "evaluacion_imagen" / "final.json")              # las 11 imágenes con la plantilla (final-*)
IMG_LLM = jload(RES / "evaluacion_imagen" / "escena_llm.json")        # las mismas listas, con la escena escrita por el LLM (escena-*)
V0_DIR = next((RES / "v0_imagen" / "corridas").glob("*retriever_abl-retriever-name-dinov3__method-none__category_filter-true"))
REPLICA = jload(REPL / "resultados.json")

V1 = "qwen3|description|filtro-kind"   # la búsqueda de la versión 1: el coseno, con filtro por kind
V2 = V1 + "|+bm25+siglip2"             # la de la versión 2 (la del flujo): densa + léxica + foto
BASE = "qwen3|description|filtro-type"  # la base de la grilla de 2026-10 (filtro por tipo)

# Lo que solo está en los documentos (no hay un archivo de resultados del que leerlo).
DOC = {
    "otro_kind": 0.11,                      # EXPERIMENTOS.md, T1 (corrección): con filtro por tipo, candidatos de otro kind en los 11 ambientes
    "con_variantes": 0.69,                  # EXPERIMENTOS.md, T6g: consultas cuyo producto tiene variantes del mismo modelo
    "abo_listados": 147702,                 # EXPERIMENTOS.md, T1f
    "abo_mandados": 759,                    # EXPERIMENTOS.md, T1f: los listados de ABO que se mandaron a describir
    "generador_v1": ("0,89–0,96", "0,69–0,73"),  # EXPERIMENTOS.md, T1d: faithfulness y answer relevance con los jueces viejos
    "escena_ic": (-0.103, 0.068),           # EXPERIMENTOS.md, T10: IC 95% de la diferencia pareada por ambiente (reconocidos, LLM − plantilla)
    "contexto": 1_000_000,                  # EXPERIMENTOS.md, T8d: el contexto de Opus 5.5, en tokens
    "cache_min": 5,                         # EXPERIMENTOS.md, T8d: lo que dura la caché de prompt, en minutos
}


def m(run: dict, key: str, met: str = "hit@1") -> float:
    return run[key][met]


def ic(run: dict, key: str, met: str = "hit@1"):
    return run[key].get(met + "_ic95")


# --- catálogos ------------------------------------------------------------------------------------
ITEMS = {it["id"]: it for it in jsonl(D_ / "procesados" / "items.jsonl")}
DESCR = {it["id"]: it["text"] for it in jsonl(D_ / "catalogo" / "descripciones.jsonl")}
ABO_ITEMS = {it["id"]: it for it in jsonl(D_ / "procesados" / "abo_items.jsonl")}
ABO_DESCR = {it["id"]: it for it in jsonl(D_ / "catalogo" / "abo" / "descripciones.jsonl")}
CATALOGO = {**ITEMS, **{k: v for k, v in ABO_ITEMS.items() if k in ABO_DESCR}}  # lo que busca el flujo
DESCR_TODO = {**{k: DESCR[k] for k in ITEMS}, **{k: v["text"] for k, v in ABO_DESCR.items()}}  # las 1.502 fichas

CATS = yaml.safe_load((D_ / "configs" / "categories.yaml").read_text())["categories"]
CFG = load_config(D_ / "configs" / "amoblai.yaml")
CFG_TXT = (D_ / "configs" / "amoblai.yaml").read_text()
ROOM_CHECK = dict(CFG.furnish.room_check)
K = CFG.furnish.candidates
SLACK = CFG.furnish.size_slack
GEN = CFG.furnish.generators["nano_banana_2"]

PEDIDOS = yaml.safe_load((D_ / "ambientes_vacios" / "pedidos.yaml").read_text())["ambientes"]
PUBLICAS = yaml.safe_load((D_ / "ambientes_vacios" / "publicas.yaml").read_text())["fotos"]
PUB_POR_ARCHIVO = {p["archivo"]: p for p in PUBLICAS}
FOTO = {r["slug"]: r["foto"] for r in PEDIDOS}


def credito(*slugs: str, sep: str = "; ") -> str:
    """Autor y licencia de las fotos públicas de esos ambientes (publicas.yaml), sin repetir. Las
    fotos propias no llevan fuente."""
    out = []
    for s in slugs:
        f = PUB_POR_ARCHIVO.get(FOTO[s])
        if f:
            c = f'{f["autor"]} ({f["licencia"]})'
            if c not in out:
                out.append(c)
    return sep.join(esc(c) for c in out)


LEDGER = jsonl(RES / "gastos.jsonl")

# --- números que se dicen -------------------------------------------------------------------------
B1, B2 = CAM[V1], CAM[V2]            # versión 1 y versión 2 de la búsqueda, sobre el ground truth
D21 = HIB[V2]["vs_base"]             # versión 2 − versión 1, pareado
assert HIB[V1]["hit@1"] == B1["hit@1"] and HIB[V2]["hit@1"] == B2["hit@1"]
N_ANS, N_BUS = B2["answerable"], B2["searches"]
N_AMB = len({r["room_id"] for r in rankings(HIB_DIR)[V1]})                        # ambientes de IKEA con consultas
N_AMB_ANS = len({r["room_id"] for r in rankings(HIB_DIR)[V1] if r["relevant"]})   # con alguna con respuesta

D: dict = {}
D["prod_268"] = corrida("20261021-161057_ablacion-retrieval")["index"]["products"]
D["prod_855"] = corrida("20261023-173217_ablacion-retrieval")["index"]["products"]
D["prod_819"] = corrida(ABL_DIR)["index"]["products"]
D["prod_todos"] = corrida(TODOS_DIR)["index"]["products"]
assert D["prod_819"] == len(ITEMS) and D["prod_todos"] == len(CATALOGO)
D["n_abo"] = len(ABO_DESCR)
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
FM = json.loads((RES / "punta_a_punta" / "hibrida" / "filtro_medidas.json").read_text())  # qué cambia el filtro de medidas (T6h)
D["ikea_con_medida"] = sum(any(v is not None for v in (x.get("dimensions_cm") or {}).values()) for x in ITEMS.values()) / len(ITEMS)
_abo_idx = [ABO_ITEMS[i] for i in ABO_DESCR]
D["abo_con_medida"] = sum(1 for it in _abo_idx if it.get("dimensions_cm")) / len(_abo_idx)
_fotos_lado = collections.Counter(Image.open(ROOT / it["photos"][0]).size for it in list(ITEMS.values())[:60])
D["foto_lado"] = _fotos_lado.most_common(1)[0][0][0]
_wc = sorted(len(DESCR[i].split()) for i in ITEMS)
D["palabras_lo"] = (_wc[len(_wc) // 20] // 10) * 10
D["palabras_hi"] = -(-_wc[-(len(_wc) // 20)] // 10) * 10
D["palabras_med"] = int(round(statistics.median(len(t.split()) for t in DESCR_TODO.values()), -1))

D["n_ambientes_vacios"] = len(PEDIDOS)
D["n_publicos"] = sum(1 for p in PEDIDOS if p["slug"].startswith("publica"))
D["n_propios"] = D["n_ambientes_vacios"] - D["n_publicos"]
D["n_publicas_revisadas"] = len(PUBLICAS)


# --- desafíos: la búsqueda de la propuesta original (por imagen) contra la de texto ---------------
def imagen_contra_texto() -> dict:
    """La búsqueda de la propuesta original (el recorte de cada mueble contra las fotos del
    catálogo, DINOv3) contra la búsqueda por texto, con el mismo ground truth y la misma unidad:
    el producto anotado de cada ambiente, sobre el catálogo de 275 de ese momento. recall@1 de
    cada una y la diferencia pareada con su IC 95% (bootstrap de ambientes)."""
    v0 = {(r["room_id"], r["sku"]): r["best_rank"] for r in jsonl(V0_DIR / "items.jsonl")}
    v1: dict[tuple, int | None] = {}
    for r in rankings(TXT_DIR)[BASE]:
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


VT = imagen_contra_texto()


# --- punta a punta: el juez de listas -------------------------------------------------------------
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
    votos = [v for r in rows for v in r["votos"]]
    return {"n": len(rows), "a": gana_a, "b": gana_b, "emp": emp, "util_a": util(a), "util_b": util(b), "rows": rows,
            "lado_a": a, "lado_b": b, "votos_a": votos.count(a), "votos_b": votos.count(b), "votos": len(votos),
            "acuerdo": sum(r["votos"][0] == r["votos"][1] for r in rows)}


def es_pub(s: str) -> bool:
    return s.startswith("publica")


J_NORD = resumen_juez(JC, lambda s: not es_pub(s))
J_OTROS = resumen_juez(JC, es_pub)
J_CAT = resumen_juez(JC)
J_VER = resumen_juez(JV)       # a = densa (versión 1), b = híbrida (versión 2)
J_AZAR = resumen_juez(JA)      # a = densa (con búsqueda), b = azar (sin búsqueda)
J5 = resumen_juez(J_ABO5)      # a = ikea, b = abo, en los 5 propios
P_CAT = p_signos(J_CAT["b"], J_CAT["a"])
P_VER = p_signos(J_VER["b"], J_VER["a"])
P_AZAR = p_signos(J_AZAR["a"], J_AZAR["b"])
# el piso de ruido: la misma configuración (la versión 2), dos veces, con el mismo plan y los mismos candidatos
J_RUIDO = resumen_juez(JR)


def _ids(d: dict, lado: str) -> list[str]:
    return [x["id"] for x in d["listas"][lado]]


RUIDO_PROD = sum(len(_ids(d, JR["a"])) for d in JR["detalle"])
RUIDO_CAMBIAN = sum(sum(x != y for x, y in zip(_ids(d, JR["a"]), _ids(d, JR["b"]), strict=True)) for d in JR["detalle"])
RUIDO_IGUALES = sum(_ids(d, JR["a"]) == _ids(d, JR["b"]) for d in JR["detalle"])
assert J_RUIDO["acuerdo"] == J_RUIDO["n"] and J_RUIDO["emp"] == RUIDO_IGUALES, "el piso de ruido cambió: revisar cómo se cuenta"
# el generador: las listas de la versión 2 contra las de la versión 1, por ambiente (no es una mejora: es una réplica)
_f1 = {x["corrida"].split("__", 1)[1]: x["fidelidad"]["faithfulness"] for x in RESP["por_corrida"]}
_f2 = {x["corrida"].split("__", 1)[1]: x["fidelidad"]["faithfulness"] for x in RESP2["por_corrida"]}
assert set(_f1) == set(_f2)
GEN_SUBE = sum(_f2[s] > _f1[s] for s in _f2)
GEN_BAJA = sum(_f2[s] < _f1[s] for s in _f2)
assert (JV["a"], JV["b"], JA["a"], JA["b"], JC["a"], JC["b"]) == ("densa", "hibrida", "densa", "azar", "ikea", "todos")

# --- relevancia graduada (un juez califica el primer candidato): reponderada a todas las consultas -
_g = GRAD_RUN[GRAD["method"]]
_w_ans = _g["answerable"] / _g["searches"]   # el juez vio tantas consultas con anotado como sin: se repondera
_G = GRAD["consultas"]
UTIL1 = _w_ans * _G["con anotado"]["util1"] + (1 - _w_ans) * _G["sin anotado"]["util1"]
UTIL3 = _w_ans * _G["con anotado"]["util3"] + (1 - _w_ans) * _G["sin anotado"]["util3"]
G_N = _G["todas"]["n"]
G_ANOT2 = GRAD["acuerdo_con_gt"]["anotado_con_2"]
G_OTROS2 = GRAD["acuerdo_con_gt"]["otros_con_2"]

# --- costos ---------------------------------------------------------------------------------------
# Por pedido: el plan, del registro de cada llamada paga (gastos.jsonl); la elección, de las corridas
# de punta a punta con el prompt del flujo (choose_combination_v2: el registro mezcla, con el mismo
# paso, la variante que manda el catálogo entero en el prompt); la imagen, del precio configurado.
def _pasos(step: str) -> list[float]:
    """Lo que costó cada llamada de un paso del flujo desde el 10/11 (catálogo IKEA + ABO)."""
    return [r["cost_usd"] for r in LEDGER if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == step]


def _elecciones(carpeta: Path | None = None) -> list[float]:
    """El costo de cada elección del flujo guardada en las corridas de punta a punta."""
    out = []
    for f in sorted((carpeta or PAP).glob("*/3_choice.json" if carpeta else "*/*/*/3_choice.json")):
        c = jload(f)
        if c.get("prompt") == "choose_combination_v2" and c.get("cost_usd"):
            out.append(c["cost_usd"])
    return out


C_PLAN = statistics.mean(_pasos("furnish.plan"))
_ch = _elecciones()
C_CHOOSE, C_CHOOSE_MIN, C_CHOOSE_MAX, N_ELEC = statistics.mean(_ch), min(_ch), max(_ch), len(_ch)
C_CHOOSE_V2 = statistics.mean(_elecciones(PAP / "hibrida" / "hibrida"))   # la elección de la versión 2, en los 11 ambientes
C_IMG = GEN["usd_per_image"]["1K"]
C_PEDIDO = C_PLAN + C_CHOOSE + C_IMG
C_SCENE = statistics.mean(r["cost_usd"] for r in LEDGER if r["step"] == "furnish.scene" and r.get("time", "") >= "2026-11-12")  # la escena escrita por el LLM, en los 11 ambientes
C_RERANK = statistics.mean(r["cost_usd"] for r in LEDGER if r["step"].startswith("eval.rerank") and "opus" in (r.get("model") or ""))
C_DESC = sum(r["cost_usd"] for r in LEDGER if r["step"].startswith("catalog.describe")) / DOC["abo_mandados"]


# Todo el trabajo: del informe de gastos (datos/resultados/gastos.md, que se genera del registro
# con `amoblai gastos --md`): por cuenta y por uso.
def _tabla_md(txt: str, titulo: str) -> list[list[str]]:
    sec = txt.split(f"## {titulo}", 1)[1].split("\n## ", 1)[0]
    filas = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in sec.splitlines() if ln.startswith("|")]
    return filas[2:]  # sin el encabezado ni la línea que lo separa


def _num(s: str) -> float:
    return float(s.replace("*", "").replace(".", "").replace(",", "."))


_gastos_md = (RES / "gastos.md").read_text()
GASTO = {f[0].strip("*"): _num(f[2]) for f in _tabla_md(_gastos_md, "Por cuenta")}     # anthropic, fal, openai y total
TOPES = {f[0]: _num(f[3]) for f in _tabla_md(_gastos_md, "Por cuenta") if f[3]}
assert abs(GASTO["total"] - GASTO["anthropic"] - GASTO["fal"] - GASTO.get("openai", 0)) < 0.02
POR_USO: dict[str, float] = {}
for _f in _tabla_md(_gastos_md, "Por uso"):
    POR_USO[_f[0]] = POR_USO.get(_f[0], 0.0) + _num(_f[4])

# ¿hacía falta RAG si el catálogo entra en el contexto? Medido (EXPERIMENTOS.md, T8d): la versión 2
# contra el mismo flujo sin búsqueda, con las fichas de todo el catálogo en el prompt (en caché),
# con el mismo filtro duro; sin ranking ni fotos de candidatos. Mismo plan, mismo modelo, mismo juez.
JX = jload(PAP / "hibrida" / "juez_hibrida_vs_contexto.json")
J_CTX = resumen_juez(JX)   # a = híbrida (versión 2), b = contexto (el catálogo entero en el prompt)
assert (JX["a"], JX["b"]) == ("hibrida", "contexto")
_cx_dirs = sorted(d for d in (PAP / "hibrida" / "contexto").iterdir() if (d / "3_choice.json").exists())
_cx = [jload(d / "3_choice.json") for d in _cx_dirs]                                         # elegir con el catálogo entero
_rg = [jload(PAP / "hibrida" / "hibrida" / d.name / "3_choice.json") for d in _cx_dirs]      # elegir entre los candidatos (versión 2)
assert len(_cx) == J_CTX["n"] and all(c["prompt"] == "choose_combination_v2" for c in _rg)
_opus = CFG.furnish.llm["models"]["claude-opus-5-5"]["usd_per_m"]


def _uso(c: dict) -> dict:
    return c["meta"]["usage"]


def _entrada(c: dict) -> int:
    return sum(_uso(c).get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))


CTX_TOKENS = max(_uso(c).get("cache_read_input_tokens") or 0 for c in _cx)                   # lo que ocupa el catálogo en el prompt
C_CTX_CACHE = statistics.mean(c["cost_usd"] for c in _cx if not _uso(c).get("cache_creation_input_tokens"))   # con la caché caliente
C_CTX_SIN = statistics.mean((_entrada(c) * _opus["input"] + _uso(c)["output_tokens"] * _opus["output"]) / 1e6 for c in _cx)  # sin caché
CTX_S, RAG_S = (statistics.median(c["meta"]["latency_s"] for c in g) for g in (_cx, _rg))    # lo que tarda el paso que elige
assert abs(C_CHOOSE_V2 - statistics.mean(c["cost_usd"] for c in _rg)) < 1e-9
assert 0.30 <= CTX_TOKENS / DOC["contexto"] <= 0.37, "el catálogo ya no ocupa «un tercio» del contexto"
CTX_EN_TOP5 = CTX_PIEZAS = 0   # lo elegido viendo todo el catálogo, ¿estaba entre los 5 candidatos de la búsqueda?
for _d, _c in zip(_cx_dirs, _cx, strict=True):
    for _ch, _p in zip(_c["answer"]["choices"], jload(PAP / "hibrida" / "hibrida" / _d.name / "2_candidates.json")["pieces"], strict=True):
        CTX_PIEZAS += 1
        CTX_EN_TOP5 += _ch.get("id") in {x["id"] for x in _p["candidates"]}

# --- las corridas del flujo con la configuración final (catálogo IKEA + ABO, búsqueda híbrida) ----
HERO = AM / "final-publica-loft-industrial"   # la que sigue el recorrido: pasa el control al primer intento
HERO_SLUG = "publica-loft-industrial"
HERO_REQ = jload(HERO / "request.json")["request"]
HERO_PLAN = jload(HERO / "1_searches.json")
HERO_PZ = HERO_PLAN["answer"]["pieces"]
HERO_FOUND = jload(HERO / "2_candidates.json")["pieces"]
HERO_CHOOSE = jload(HERO / "3_choice.json")
HERO_CHOICE = HERO_CHOOSE["answer"]["choices"]
HERO_SCENE = jload(HERO / "4_scene.json")
HERO_IMG = jload(HERO / "5_image.json")
HERO_MET = jload(HERO / "6_metricas_imagen.json")
CAND_INFO = {c["id"]: c for p in HERO_FOUND for c in p["candidates"]}
CLA = AM / "final-publica-living-clasico"     # una que el control rechazó en los tres intentos
CLA_SLUG = "publica-living-clasico"
CLA_IMG = jload(CLA / "5_image.json")
FINALES = [{"slug": d.name.removeprefix("final-"), "dir": d, "img": jload(d / "5_image.json"), "met": jload(d / "6_metricas_imagen.json")}
           for d in sorted(AM.glob("final-*"))]


def elegidos(found: list, choices: list) -> list[tuple[dict, int, int, dict]]:
    """Lo que eligió una corrida: (el producto, cuántas unidades, su puesto en la búsqueda, la elección)."""
    out = []
    for p, c in zip(found, choices, strict=True):
        q = int(c.get("quantity", 1) or 0)
        if q:
            ids = [h["id"] for h in p["candidates"]]
            out.append((p["candidates"][ids.index(c["id"])], q, ids.index(c["id"]) + 1, c))
    return out


HERO_PICKS = elegidos(HERO_FOUND, HERO_CHOICE)
N_HERO = len(HERO_PICKS)
N_HERO_UNID = sum(q for _, q, *_ in HERO_PICKS)
N_HERO_ABO = sum(h["id"].startswith("abo-") for h, *_ in HERO_PICKS)
N_HERO_PRIMERO = sum(rk == 1 for _, _, rk, _ in HERO_PICKS)
HERO_COSTO_CLAUDE = HERO_PLAN["cost_usd"] + HERO_CHOOSE["cost_usd"]
SOFA = HERO_PICKS[0][0]["id"]   # el producto que se sigue por las fases: el sofá de la pieza 1
assert HERO_PICKS[0][2] == 1 and SOFA.startswith("abo-") and HERO_PZ[0]["kinds"] == ["sofa"]

IMG_TOT = {
    "productos": sum(len(f["met"]["productos"]) for f in FINALES),
    "detectados": sum(bool(p["detectado"]) for f in FINALES for p in f["met"]["productos"]),
    "reconocidos": sum(p.get("puesto") == 1 for f in FINALES for p in f["met"]["productos"]),
    "coseno": statistics.mean(p["coseno"] for f in FINALES for p in f["met"]["productos"] if p.get("coseno") is not None),
    "pasan": sum(bool(f["img"]["room_check"]["ok"]) for f in FINALES),
    "pasan_al_primero": sum(bool(f["img"]["attempts"][0]["ok"]) for f in FINALES),
    "intentos": sum(len(f["img"]["attempts"]) for f in FINALES),
}
NO_PASAN = len(FINALES) - IMG_TOT["pasan"]
assert (IMG_PL["productos"], IMG_PL["detectados"], IMG_PL["identificados"], IMG_PL["ambiente_conservado"]) == \
    (IMG_TOT["productos"], IMG_TOT["detectados"], IMG_TOT["reconocidos"], IMG_TOT["pasan"])
# la escena: plantilla contra escrita por el LLM, las mismas 11 listas (EXPERIMENTOS.md, T10)
_pl = {x["corrida"].removeprefix("final-"): x for x in IMG_PL["por_corrida"]}
_ll = {x["corrida"].removeprefix("escena-"): x for x in IMG_LLM["por_corrida"]}
assert set(_pl) == set(_ll)
ESC_DIF = statistics.mean(_ll[s]["identificados"] / _ll[s]["productos"] - _pl[s]["identificados"] / _pl[s]["productos"] for s in _pl)
assert abs(ESC_DIF - (-0.014)) < 0.002 and DOC["escena_ic"][0] < ESC_DIF < DOC["escena_ic"][1], ESC_DIF
ESC_FALLARON_1 = sum(e["corridas"] - e["ambiente_al_primer_intento"] for e in (IMG_PL, IMG_LLM))    # fallaron el control al primer intento
ESC_RESCATADOS = sum(e["ambiente_conservado"] - e["ambiente_al_primer_intento"] for e in (IMG_PL, IMG_LLM))  # y los reintentos rescataron

# el filtro de la pieza 1 y cuántos productos del índice del flujo deja pasar (el índice está en la caché)
_p1 = HERO_PZ[0]
FILTRO_MAX = {f"max_{a}_cm": round(_p1[f"max_{a}_cm"] * (1 + SLACK), 1) for a in ("width", "depth", "height") if _p1.get(f"max_{a}_cm") is not None}
FILTRO = Filters(kinds=_p1["kinds"], **FILTRO_MAX)
IDX_DIR = ROOT / CFG.cache_dir / "rag" / "index" / f"{Path(CFG.rag.catalog).stem}-{CFG.rag.describer}-{CFG.rag.embedder}"
IDX = jload(IDX_DIR / "index.json")
assert IDX["products"] == D["prod_todos"]
PASAN = sum(FILTRO.allows(x) for x in jsonl(IDX_DIR / "items.jsonl"))
VQ = visual_query(_p1["query"])   # la ficha en una frase, como la lee SigLIP 2

KIND_ES = {
    "bookcase": "Biblioteca", "armchair": "Sillón", "floor lamp": "Lámpara de pie", "side table": "Mesita",
    "rug": "Alfombra", "throw": "Manta", "cushion": "Almohadón", "curtains": "Cortinas", "plant": "Planta",
    "coffee table": "Mesa ratona", "sofa": "Sofá", "pendant lamp": "Lámpara colgante", "TV stand": "Mueble de TV",
    "dining table": "Mesa de comedor", "dining chair": "Silla", "sideboard": "Aparador", "desk lamp": "Lámpara de escritorio",
    "display cabinet": "Vitrina", "console table": "Mesa consola", "picture frame": "Marco", "ottoman": "Puf",
    "shelving unit": "Estantería", "plant pot": "Maceta",
}


def medida(dim) -> str:
    """Las medidas de un producto, en centímetros enteros: ancho × fondo (× alto si hay)."""
    if not dim:
        return ""
    v = [dim.get(a) for a in ("width", "depth")]
    if all(v):
        return " × ".join(f"{round(x)}" for x in v) + " cm"
    if v[0]:
        return f"{round(v[0])} cm de ancho"
    return ""


def tipo_de(desc: str) -> str:
    """La línea Type de una descripción."""
    return desc.splitlines()[0].removeprefix("Type:").strip()


# --- ground truth: un living real de IKEA, con sus consultas y lo que trae la búsqueda del flujo ---
GT_ROOM = "ikea-find-your-living-room-design-inspiration__1364308433351-s4.jpg"
GT_ROOM_PATH = "datos/dataset/ikea/images/room_scenes/" + GT_ROOM
_gt = [r for r in rankings(HIB_DIR)[V2] if r["room_id"] == GT_ROOM]
GT_ANY = [x for x in _gt[0]["relevant_any"] if x in ITEMS]
Q_MESA = next(r for r in _gt if r["kind"] == "coffee table")       # una que acierta primero
Q_LAMPARA = next(r for r in _gt if r["kind"] == "floor lamp")      # una que acierta, pero no primero
assert Q_MESA["rank"] == 1 and 1 < Q_LAMPARA["rank"] <= 5, (Q_MESA["rank"], Q_LAMPARA["rank"])
FRASES = [r["phrase"] for r in rankings(HIB_DIR)[V1] if r.get("phrase")]

# la propuesta original: el recorte del sofá en ese mismo living
V0_REC = None
for _r in jsonl(V0_DIR / "recortes.jsonl"):
    if _r["room_id"] == GT_ROOM and _r["category"] == "sofa":
        V0_REC = _r
V0_SOFA_OK = V0_REC["relevant"][1] if V0_REC["relevant"][1] in V0_REC["ranked_skus"] else V0_REC["relevant"][0]

# Ejercicio 4: un caso del banco de prueba donde la versión 1 deja al anotado fuera de los 5 candidatos
CASO = "white cushion with black leaf print on the right armchair"
CASO_R = {k: next(r for r in rankings(HIB_DIR)[k] if r.get("phrase") == CASO) for k in (V1, V2)}
assert CASO_R[V1]["rank"] > K and CASO_R[V2]["rank"] == 1, "el caso del Ejercicio 4 ya no muestra la limitación: elegir otro"

# Experimento 4: un «error» que es el mismo modelo en otro color (el primero no es el anotado, pero se llama igual)
_fam = [r for r in rankings(HIB_DIR)[V1] if r["relevant"] and r["rank"] and r["rank"] > 1
        and any(ITEMS[r["ranked"][0]]["name"] == ITEMS[x]["name"] and ITEMS[r["ranked"][0]]["category"] == ITEMS[x]["category"] for x in r["relevant"])]
FAM_R = next((r for r in _fam if r.get("phrase") == "large checked rug under the table"), _fam[0])
FAM_TOP = FAM_R["ranked"][0]
FAM_REL = next(x for x in FAM_R["relevant"] if ITEMS[x]["name"] == ITEMS[FAM_TOP]["name"])

# --- ambientes vacíos ---------------------------------------------------------------------------
ESTILO = {
    "caballito-living": ("Living", "moderno, luminoso"), "caballito-comedor": ("Comedor", "nórdico"),
    "alvear-escritorio": ("Escritorio", "nórdico"), "alvear-living-comedor": ("Living comedor", "nórdico"),
    "experimento-lectura": ("Rincón de lectura", "cálido, maderas"),
    "publica-loft-industrial": ("Loft", "industrial"), "publica-living-clasico": ("Sala con chimenea", "clásico"),
    "publica-comedor-clasico-moderno": ("Comedor abierto", "clásico actual"), "publica-living-japandi": ("Living", "japandi"),
    "publica-living-bohemio": ("Living", "bohemio"), "publica-estudio-sobrio": ("Estudio", "moderno sobrio"),
}

# --- réplica de un living del ground truth (trabajo futuro): IoU medio de cada forma de indicar el lugar
RV = {k: v["resumen"]["iou_medio"]["media"] for k, v in REPLICA["variantes"].items()}
REPL_N = len(REPLICA["productos"])
