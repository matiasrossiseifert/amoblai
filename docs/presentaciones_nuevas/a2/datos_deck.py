"""Lee todos los números de la presentación desde los archivos de resultados del repo.

Nada de lo que muestra la presentación se escribe a mano: todo sale de acá. Si un archivo cambia,
se vuelve a correr build.py y los números se actualizan solos. Las pocas cifras que solo están en
los documentos (docs/EXPERIMENTOS.md) se leen de ahí con una expresión regular (DOC): si la frase
cambia, el build falla en vez de mostrar un número viejo.

Orden (el de docs/REVISION.md, 2026-11-12): el catálogo; el buscador sobre el ground truth de IKEA
(las ablaciones de la revisión: camino, consulta, híbrido, embedders, líneas, reranking local);
el flujo entero sobre ambientes vacíos reales (el juez de listas y el diagnóstico sin juez); el
generador (faithfulness y answer relevance, jueces v2); las 11 corridas de la configuración final
(datos/resultados/amoblar/final-*); los costos (el registro de gastos); la réplica.
"""

from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import re
import statistics
from collections import defaultdict
from math import comb
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "datos" / "resultados"
EV = RES / "evaluacion"
AMO = RES / "amoblar"

V1 = "qwen3|description|filtro-kind"  # la búsqueda de la versión 1: el coseno, con filtro por kind
V2 = V1 + "|+bm25+siglip2"  # la de la versión 2 (la del flujo): densa + léxica + foto
BASE = "qwen3|description|filtro-type"  # la base de la grilla de octubre (filtro por tipo)
BEST = BASE

RUN_855 = "20261023-173217_ablacion-retrieval"  # la grilla sobre el catálogo de 855
RUN_V1_275 = "20261021-133226_ablacion-texto"  # el catálogo que vio la primera aproximación
RUN_V1_268 = "20261021-161057_ablacion-retrieval"  # el primer catálogo de 268 productos
RUN_V0 = "20261006-231131_retriever_abl-retriever-name-dinov3__method-none__category_filter-true"

# La corrida que sigue el recorrido (configuración final, foto pública, pasa el control al primer
# intento) y una que el control del ambiente rechazó en los tres intentos.
RUN_REC = "final-publica-living-japandi"
RUN_NO = "final-publica-living-clasico"
# La consulta de ejemplo de «cómo medimos»: la alfombra crema de pelo largo de este ambiente.
EJ_ROOM = "ikea-a-leather-look-made-for-lounging__1364309444239-s4.jpg"
EJ_PIECE = 2
# El caso del Ejercicio 4: la versión 1 deja al anotado fuera de los 5 candidatos.
CASO = "white cushion with black leaf print on the right armchair"


def jload(p: Path):
    return json.loads(Path(p).read_text())


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]


def latest(suffix: str) -> Path:
    """La última corrida de evaluación con ese sufijo."""
    runs = sorted(d for d in EV.iterdir() if d.name.endswith(suffix) and (d / "metricas.json").exists())
    if not runs:
        raise FileNotFoundError(f"no hay corrida *{suffix} en {EV}")
    return runs[-1]


def metricas(run) -> dict:
    return jload((run if isinstance(run, Path) else EV / run) / "metricas.json")


_RANK: dict[Path, dict[str, list[dict]]] = {}


def rankings(run) -> dict[str, list[dict]]:
    """Los rankings guardados de una corrida de evaluación, por método."""
    run = run if isinstance(run, Path) else EV / run
    if run not in _RANK:
        by: dict[str, list[dict]] = {}
        gz = run / "rankings.jsonl.gz"
        with gzip.open(gz, "rt") if gz.exists() else open(run / "rankings.jsonl") as f:
            for line in f:
                r = json.loads(line)
                by.setdefault(r["method"], []).append(r)
        _RANK[run] = by
    return _RANK[run]


def paired(run, a: str, b: str, run_b=None) -> dict:
    """a − b sobre las mismas consultas, con su IC 95% por bootstrap de ambientes: la cuenta de
    `vs_base` (evaluation/retrieval.py, misma semilla), para las corridas anteriores a esa columna."""
    from amoblai.evaluation.retrieval import paired_difference

    return paired_difference(rankings(run)[a], rankings(run_b or run)[b])


def bootstrap_means(values, groups, n_samples=1000, seed=0):
    """La misma rutina que src/amoblai/evaluation/metrics.py:bootstrap_ci, pero devuelve todas
    las medias remuestreadas (para dibujar el histograma)."""
    vals = np.asarray(values, dtype=float)
    uniq = sorted(set(groups))
    index = {g: np.flatnonzero(np.asarray(groups) == g) for g in uniq}
    rng = np.random.default_rng(seed)
    means = np.empty(n_samples)
    for s in range(n_samples):
        picked = rng.choice(len(uniq), size=len(uniq), replace=True)
        idx = np.concatenate([index[uniq[i]] for i in picked])
        means[s] = vals[idx].mean()
    lo, hi = np.quantile(means, [0.025, 0.975])
    return means, float(lo), float(hi)


def p_signos(a: int, b: int) -> float:
    """Test de signos a dos colas sobre los ambientes decididos (a ganados, b perdidos)."""
    n, k = a + b, max(a, b)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k, n + 1)) / 2**n)


def run_date(run) -> dt.date:
    name = run.name if isinstance(run, Path) else run
    return dt.datetime.strptime(name[:8], "%Y%m%d").date()


def doc(pattern: str, archivo: str = "docs/EXPERIMENTOS.md") -> str:
    """Una cifra que solo está en un documento: el primer grupo de la expresión, o el build falla."""
    m = re.search(pattern, (REPO / archivo).read_text(), re.S)
    if not m:
        raise ValueError(f"{archivo}: no encuentro {pattern!r} (¿cambió el documento?)")
    return m.group(1)


def corrida(nombre: str) -> dict:
    """Una corrida completa del flujo (datos/resultados/amoblar/<nombre>/)."""
    d = AMO / nombre
    return dict(dir=d, slug=nombre.removeprefix("final-"), req=jload(d / "request.json"),
                plan=jload(d / "1_searches.json"), cands=jload(d / "2_candidates.json"),
                choice=jload(d / "3_choice.json"), scene=jload(d / "4_scene.json"),
                gen=jload(d / "5_image.json"), met=jload(d / "6_metricas_imagen.json"))


def elegidos(run: dict) -> list[tuple[dict, int, int]]:
    """Lo que eligió una corrida: (el candidato, cuántas unidades, su puesto en la búsqueda)."""
    out = []
    for p, c in zip(run["cands"]["pieces"], run["choice"]["answer"]["choices"], strict=True):
        q = int(c.get("quantity", 1) or 0)
        if q:
            ids = [h["id"] for h in p["candidates"]]
            out.append((p["candidates"][ids.index(c["id"])], q, ids.index(c["id"]) + 1))
    return out


def load() -> dict:
    from amoblai.config import load_config
    from amoblai.evaluation.metrics import bootstrap_ci
    from amoblai.infra.budget import purpose
    from amoblai.rag.filters import Filters

    D: dict = {}
    cfg = load_config(REPO / "datos" / "configs" / "amoblai.yaml")
    cfg_txt = (REPO / "datos/configs/amoblai.yaml").read_text()
    D["cfg"], D["cfg_txt"] = cfg, cfg_txt

    # ---------- catálogo ----------
    items = {r["id"]: r for r in jsonl(REPO / "datos/procesados/items.jsonl")}
    desc = {r["id"]: r["text"].strip() for r in jsonl(REPO / "datos/catalogo/descripciones.jsonl")}
    desc_prompt = {r["id"]: r.get("prompt", "") for r in jsonl(REPO / "datos/catalogo/descripciones.jsonl")}
    abo_desc = {r["id"]: r["text"].strip() for r in jsonl(REPO / "datos/catalogo/abo/descripciones.jsonl")}
    abo_items = {r["id"]: r for r in jsonl(REPO / "datos/procesados/abo_items.jsonl")}
    D["items"], D["desc"], D["abo_desc"], D["abo_items"], D["desc_prompt"] = items, desc, abo_desc, abo_items, desc_prompt
    D["n_ikea"], D["n_abo"] = len(items), len(abo_desc)
    D["n_todos"] = D["n_ikea"] + D["n_abo"]
    D["abo_listados"] = len(abo_items)  # los que se mandaron a describir
    D["abo_total"] = doc(r"De los ([\d.]+) listados")  # los listados de ABO (T1f)
    described = [abo_items[i] for i in abo_desc if i in abo_items]
    D["abo_con_medidas"] = sum(1 for r in described if r.get("dimensions_cm")) / len(described)
    D["ikea_con_medida"] = sum(any(v is not None for v in (x.get("dimensions_cm") or {}).values())
                               for x in items.values()) / len(items)
    seats = [r for r in items.values() if r["kind"] in ("sofa", "armchair") or r["category"] == "chair"]
    D["ikea_asientos_sin_medidas"] = sum(1 for r in seats if not r.get("dimensions_cm")) / len(seats)
    from PIL import Image

    sample = [r["photos"][0] for r in list(items.values())[::25]]
    D["ikea_px"] = int(np.median([max(Image.open(REPO / p).size) for p in sample]))
    kinds_idx = [x.get("kind") for x in items.values()]
    D["n_alfombras"], D["n_almohadones"] = kinds_idx.count("rug"), kinds_idx.count("cushion")

    # ---------- el buscador, sobre el ground truth de IKEA ----------
    abl_dir = latest("_ablacion-retrieval")  # la grilla: embedder, dimensión, splitting, base vectorial
    ABL = metricas(abl_dir)
    D["ABL"], D["ABL_DIR"] = ABL, abl_dir
    D["M"] = ABL
    cor = jload(abl_dir / "corrida.json")
    D["embed_model"] = cor["index"]["embedder"]["key"]["model"].split("/")[-1]
    D["hnsw"] = cor["index"]["vector_store"]["hnsw"]
    cfgs = glob.glob(str(Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-Embedding-0.6B/snapshots/*/config.json"))
    D["best_dim"] = json.loads(Path(cfgs[0]).read_text())["hidden_size"] if cfgs else 1024
    D["indice_mb"] = D["n_todos"] * D["best_dim"] * 4 / 1e6  # float32
    rer_dir = latest("_ablacion-reranking")  # un VLM ordena el top-10 mirando las fotos
    D["RER"] = metricas(rer_dir)
    D["CAM"] = CAM = metricas(latest("_ablacion-camino"))  # el camino incremental, un cambio por paso
    D["CON"] = metricas(latest("_ablacion-consulta"))  # la ficha contra la frase natural
    hib_dir = latest("_ablacion-hibrido")  # léxica, por foto y fusiones
    D["HIB"] = HIB = metricas(hib_dir)
    D["HIB_DIR"] = hib_dir
    D["HIB_R"] = HIB_R = [metricas(latest(f"_ablacion-hibrido-{r}")) for r in ("r2", "r3")]  # otros dos redactores
    D["EMB"] = EMB = metricas(latest("_ablacion-embedders"))  # con el filtro del flujo, exacto y por familia
    D["EMB_DIR"] = latest("_ablacion-embedders")
    D["RLOC"] = metricas(latest("_ablacion-reranking-local"))  # Qwen3-Reranker
    D["LIN"] = metricas(latest("_ablacion-lineas"))  # qué líneas de la descripción hacen el trabajo
    todos_dir = latest("_ablacion-catalogo-todos")  # las mismas consultas con ABO de distractores
    D["TODOS"] = metricas(todos_dir)[BASE]
    D["CAT_OLD"] = metricas(RUN_855)[BASE]
    D["CAT_NEW"] = metricas(latest("_ablacion-catalogo-revisado"))[BASE]
    D["n_855"] = jload(EV / RUN_855 / "corrida.json")["index"]["products"]
    D["n_268"] = jload(EV / RUN_V1_268 / "corrida.json").get("index", {}).get("products")
    D["n_275"] = jload(EV / RUN_V1_275 / "corrida.json").get("index", {}).get("products")
    D["h1_268"] = metricas(RUN_V1_268)[BASE]["hit@1"]
    D["CURVA"] = jload(RES / "evaluacion_candidatos/curva_k.json")
    D["GRAD"] = GRAD = jload(RES / "evaluacion_graduada/graduada.json")

    B1, B2 = CAM[V1], CAM[V2]
    D["B1"], D["B2"] = B1, B2
    D["D21"] = HIB[V2]["vs_base"]  # versión 2 − versión 1, pareado
    D["N_ANS"], D["N_BUS"] = B2["answerable"], B2["searches"]
    rk_v1 = rankings(hib_dir)[V1]
    D["N_AMB"] = len({r["room_id"] for r in rk_v1})  # ambientes de IKEA con consultas
    D["N_AMB_ANS"] = len({r["room_id"] for r in rk_v1 if r["relevant"]})  # con alguna con respuesta
    D["azar_h1"], D["azar_h10"] = B2["azar_hit@1"], B2["azar_hit@10"]
    D["frases"] = [r["phrase"] for r in rk_v1 if r.get("phrase")]
    D["cos_banco"] = statistics.median(r["scores"][0] for r in rk_v1 if r["relevant"] and r["scores"])
    D["corr_cp"] = statistics.correlation([v["mrr@10"] for v in ABL.values()],
                                          [v["context_precision@10"] for v in ABL.values()])
    D["n_configs"] = len(ABL)

    # diferencias pareadas que no vienen en metricas.json (corridas anteriores a esa columna)
    D["d_ficha"] = paired(abl_dir, "qwen3|description|filtro-none", "qwen3|seller|filtro-none")
    D["d_name"] = paired(abl_dir, "qwen3|name+description|filtro-kind", V1)
    D["d_opus"] = paired(rer_dir, BASE + "|rerank-opus", BASE)
    D["d512"] = paired(abl_dir, BASE + "|dim-512", BASE)
    D["d_abo"] = paired(todos_dir, BASE, BASE, run_b=abl_dir)  # el mismo buscador, con ABO de distractores
    D["d_mini"] = paired(abl_dir, BASE + "|rerank-minilm-reranker", BASE)

    # Chroma contra búsqueda exacta: ¿mismo ranking, búsqueda por búsqueda?
    ex_a, ex_b = rankings(abl_dir)[BASE + "|exact"], rankings(abl_dir)[BASE]
    D["chroma_igual"] = sum(x["ranked"] == y["ranked"] for x, y in zip(ex_a, ex_b, strict=True))
    D["chroma_total"] = len(ex_a)

    # la relevancia graduada, reponderada a la población (el juez vio 75 con anotado y 75 sin)
    g_run = metricas(GRAD["run"])[GRAD["method"]]
    w_ans = g_run["answerable"] / g_run["searches"]
    G = GRAD["consultas"]
    D["util1"] = w_ans * G["con anotado"]["util1"] + (1 - w_ans) * G["sin anotado"]["util1"]
    D["util3"] = w_ans * G["con anotado"]["util3"] + (1 - w_ans) * G["sin anotado"]["util3"]
    e_q = EMB[V1]
    D["frac_variante"] = (e_q["familia_hit@1"] - e_q["hit@1"]) / (1 - e_q["hit@1"])
    D["con_variantes"] = int(doc(r"el (\d+)% de las consultas\s+busca un producto que tiene variantes")) / 100
    D["otro_kind"] = int(doc(r"con filtro por tipo el (\d+)% de los candidatos sería\s+de otro kind")) / 100
    D["generador_v1"] = re.search(r"faithfulness (0,\d+) a (0,\d+).*?answer relevance (0,\d+) a (0,\d+)",
                                  doc(r"(\*\*RAGAS sobre el porqué:\*\*[^\n]*\n[^\n]*)"), re.S).groups()

    # ---------- el ejemplo de «cómo medimos»: una búsqueda del flujo (versión 2) ----------
    rk_v2 = rankings(hib_dir)[V2]
    ej = next(r for r in rk_v2 if r["room_id"] == EJ_ROOM and r["piece"] == EJ_PIECE)
    D["ej"] = ej
    D["ej_otros"] = {k: next(r for r in rankings(hib_dir)[m] if r["room_id"] == EJ_ROOM and r["piece"] == EJ_PIECE)["rank"]
                     for k, m in (("densa", V1), ("lexica", "bm25|description|filtro-kind"),
                                  ("foto", "siglip2|description|filtro-kind"), ("hibrida", V2))}
    room_rows = [r for r in rk_v2 if r["room_id"] == EJ_ROOM]
    gt, ctx = set(), set()
    for r in room_rows:
        gt |= set(r["relevant"])
        ctx |= set(r["ranked"][:3])
    D["ej_cr3"] = (len(gt & ctx), len(gt))
    D["ej_annotated"] = room_rows[0]["relevant_any"]
    rk = ej["rank"]
    D["ej_metrics"] = {"rank": rk, "hit1": int(rk <= 1), "hit3": int(rk <= 3), "hit5": int(rk <= 5),
                       "rr": 1 / rk, "ndcg": 1 / np.log2(rk + 1), "cp": 1 / rk}

    # el caso del Ejercicio 4
    D["caso"] = {k: next(r for r in rankings(hib_dir)[k] if r.get("phrase") == CASO) for k in (V1, V2)}

    # ---------- la primera aproximación (buscar por imagen) contra el texto, misma unidad ----------
    v0 = {(r["room_id"], r["sku"]): r["best_rank"] for r in jsonl(RES / "v0_imagen/corridas" / RUN_V0 / "items.jsonl")}
    v1: dict[tuple, int | None] = {}
    for r in rankings(RUN_V1_275)[BASE]:
        for sku in r["relevant"]:
            pos = r["ranked"].index(sku) + 1 if sku in r["ranked"] else None
            k = (r["room_id"], sku)
            v1[k] = pos if v1.get(k) is None else (v1[k] if pos is None else min(v1[k], pos))
    keys = sorted(v0)
    a = [float(v0[k] is not None and v0[k] <= 1) for k in keys]
    b = [float(v1.get(k) is not None and v1[k] <= 1) for k in keys]
    d = [y - x for x, y in zip(a, b, strict=True)]
    D["VT"] = {"n": len(keys), "imagen": statistics.mean(a), "texto": statistics.mean(b), "dif": statistics.mean(d),
               "ic": bootstrap_ci(d, [k[0] for k in keys], n_samples=4000)}  # 4.000 remuestreos, como la revisión

    # ---------- el flujo entero, sobre ambientes vacíos reales ----------
    PP = RES / "punta_a_punta"
    D["JV"] = jload(PP / "hibrida/juez_densa_vs_hibrida.json")  # versión 1 contra versión 2
    D["JA"] = jload(PP / "hibrida/juez_densa_vs_azar_7ambientes.json")  # con búsqueda contra sin búsqueda
    D["JC"] = JC = jload(PP / "catalogos/juez_ikea_vs_todos.json")  # IKEA contra IKEA + ABO
    D["J5"] = jload(PP / "catalogos/juez_ikea_vs_abo_5ambientes.json")  # IKEA contra ABO solo
    D["DIAG"] = jload(PP / "hibrida/diagnostico.json")
    # el piso de ruido: la versión 2 corrida dos veces (T8c)
    D["JR"] = JR = jload(PP / "hibrida/juez_hibrida_vs_hibrida_bis.json")
    D["ruido_total"] = sum(len(d_["listas"]["hibrida"]) for d_ in JR["detalle"])
    D["ruido_cambian"] = sum(x["id"] != y["id"] for d_ in JR["detalle"]
                             for x, y in zip(d_["listas"]["hibrida"], d_["listas"]["hibrida_bis"], strict=True))
    D["ruido_iguales"] = sum(all(x["id"] == y["id"] for x, y in zip(d_["listas"]["hibrida"], d_["listas"]["hibrida_bis"], strict=True))
                             for d_ in JR["detalle"])
    # RAG contra el catálogo entero en el prompt, sin búsqueda (T8d)
    D["JX"] = jload(PP / "hibrida/juez_hibrida_vs_contexto.json")
    ctx_runs = sorted(d_ for d_ in (PP / "hibrida/contexto").iterdir() if (d_ / "3_choice.json").exists())
    ctx = [jload(d_ / "3_choice.json") for d_ in ctx_runs]
    rag = [jload(PP / "hibrida/hibrida" / d_.name / "3_choice.json") for d_ in ctx_runs]
    opus = cfg.furnish.llm["models"]["claude-opus-5-5"]["usd_per_m"]

    def uso(c):
        return c["meta"]["usage"]

    def entrada(c):
        return sum(uso(c).get(k_) or 0 for k_ in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))

    en5 = tot5 = 0
    for d_, c in zip(ctx_runs, ctx, strict=True):
        cand = jload(PP / "hibrida/hibrida" / d_.name / "2_candidates.json")["pieces"]
        for pz, ch_ in zip(cand, c["answer"]["choices"], strict=True):
            if ch_.get("id") and int(ch_.get("quantity", 1) or 0):
                tot5 += 1
                en5 += ch_["id"] in [h["id"] for h in pz["candidates"]]
    D["CTX"] = {
        "tokens": max(uso(c).get("cache_read_input_tokens") or 0 for c in ctx),  # el catálogo, en tokens de Opus 5.5
        "caliente": statistics.mean(c["cost_usd"] for c in ctx if not uso(c).get("cache_creation_input_tokens")),
        "sin_cache": statistics.mean((entrada(c) * opus["input"] + uso(c)["output_tokens"] * opus["output"]) / 1e6 for c in ctx),
        "rag_usd": statistics.mean(c["cost_usd"] for c in rag),
        "ctx_s": statistics.median(c["meta"]["latency_s"] for c in ctx),
        "rag_s": statistics.median(c["meta"]["latency_s"] for c in rag),
        "en5": en5, "piezas": tot5,
    }
    # qué cambia el filtro de medidas sobre los planes reales (T6h)
    D["FM"] = jload(PP / "hibrida/filtro_medidas.json")
    D["DIAG_CAT"] = jload(PP / "catalogos/diagnostico.json")

    def pooled(xs, cat):
        gs = [g for x in xs for s in x["puntajes"][cat] for g in s["grades"]]
        return sum(1 for g in gs if g == 2) / len(gs)

    own = [x for x in JC["detalle"] if not x["slug"].startswith("publica")]
    pub = [x for x in JC["detalle"] if x["slug"].startswith("publica")]
    D["j_grupos"] = {}
    for name, xs in (("propios", own), ("publicos", pub), ("total", JC["detalle"])):
        D["j_grupos"][name] = {
            "n": len(xs),
            "gana_ikea": sum(x["ganador"] == "ikea" for x in xs),
            "gana_todos": sum(x["ganador"] == "todos" for x in xs),
            "empates": sum(x["ganador"] == "tie" for x in xs),
            "util_ikea": pooled(xs, "ikea"),
            "util_todos": pooled(xs, "todos"),
        }

    # ambientes vacíos y créditos de las fotos públicas (las propias no llevan fuente)
    ped = yaml.safe_load((REPO / "datos/ambientes_vacios/pedidos.yaml").read_text())["ambientes"]
    D["pedidos"] = {a_["slug"]: a_ for a_ in ped}
    pubs = yaml.safe_load((REPO / "datos/ambientes_vacios/publicas.yaml").read_text())["fotos"]
    D["publicas"] = {p["archivo"]: p for p in pubs}
    D["n_publicas_revisadas"] = len(pubs)

    # ---------- el generador: faithfulness y answer relevance (jueces v2) ----------
    D["RESP"] = RESP = jload(RES / "evaluacion_respuesta/resumen_version2.json")  # las 11 listas de la versión 2
    D["RESP1"] = RESP1 = jload(RES / "evaluacion_respuesta/resumen.json")  # otras 11 listas (búsqueda de la versión 1): la réplica
    f2 = {x["corrida"].split("__")[-1]: x["fidelidad"]["faithfulness"] for x in RESP["por_corrida"]}
    f1 = {x["corrida"].split("__")[-1]: x["fidelidad"]["faithfulness"] for x in RESP1["por_corrida"]}
    D["resp_sube"] = sum(f2[k] > f1[k] for k in f2)
    D["resp_baja"] = sum(f2[k] < f1[k] for k in f2)

    # ---------- las corridas de la configuración final ----------
    D["run"] = corrida(RUN_REC)
    D["run_no"] = corrida(RUN_NO)
    fin = []
    for dd in sorted(AMO.glob("final-*")):
        fin.append({"slug": dd.name.removeprefix("final-"), "dir": dd, "img": jload(dd / "5_image.json"),
                    "met": jload(dd / "6_metricas_imagen.json")})
    D["FINALES"] = fin
    D["IMG_TOT"] = {
        "n": len(fin),
        "productos": sum(len(f["met"]["productos"]) for f in fin),
        "detectados": sum(bool(p["detectado"]) for f in fin for p in f["met"]["productos"]),
        "reconocidos": sum(p.get("puesto") == 1 for f in fin for p in f["met"]["productos"]),
        "coseno": statistics.mean(p["coseno"] for f in fin for p in f["met"]["productos"] if p.get("coseno") is not None),
        "pasan": sum(bool(f["img"]["room_check"]["ok"]) for f in fin),
        "pasan_al_primero": sum(bool(f["img"]["attempts"][0]["ok"]) for f in fin),
        "intentos": sum(len(f["img"]["attempts"]) for f in fin),
    }
    D["IMG_FIN"] = fin_ = jload(RES / "evaluacion_imagen/final.json")  # las 11 con la plantilla
    D["IMG_ESC"] = esc_ = jload(RES / "evaluacion_imagen/escena_llm.json")  # las mismas listas, con la escena escrita por el LLM
    assert fin_["identificados"] == D["IMG_TOT"]["reconocidos"] and fin_["ambiente_conservado"] == D["IMG_TOT"]["pasan"]
    D["reintentos"] = {  # entre las dos tandas: cuántas fallaron el control al primer intento, y cuántas rescató reintentar
        "fallaron": sum(x["corridas"] - x["ambiente_al_primer_intento"] for x in (fin_, esc_)),
        "rescatadas": sum(x["ambiente_conservado"] - x["ambiente_al_primer_intento"] for x in (fin_, esc_)),
    }
    D["escena_pareado"] = doc(r"la fracción de reconocidos cambia (−0,\d+\s+\[[^\]]+\])").replace("\n", " ")
    D["escena_pareado"] = " ".join(D["escena_pareado"].split())
    rc = cfg.furnish.room_check
    D["sift_attempts"], D["sift_min_inliers"], D["sift_max_shift"] = int(rc["attempts"]), int(rc["min_inliers"]), float(rc["max_shift"])

    # cuántos productos del índice del flujo deja pasar el filtro de la primera pieza del recorrido
    p1 = D["run"]["plan"]["answer"]["pieces"][0]
    slack = cfg.furnish.size_slack
    most = {f"max_{ax}_cm": round(p1[f"max_{ax}_cm"] * (1 + slack), 1) for ax in ("width", "depth", "height")
            if p1.get(f"max_{ax}_cm") is not None}
    filtro = Filters(kinds=p1["kinds"], **most)
    idx_items = REPO / cfg.cache_dir / "rag" / "index" / f"{Path(cfg.rag.catalog).stem}-{cfg.rag.describer}-{cfg.rag.embedder}" / "items.jsonl"
    D["idx_items"] = idx_items
    D["filtro_p1"] = {"most": most, "kinds": p1["kinds"],
                      "pasan": sum(filtro.allows(x) for x in jsonl(idx_items)) if idx_items.exists() else None}

    # ---------- costos: del registro de gastos (datos/resultados/gastos.jsonl) ----------
    led = jsonl(RES / "gastos.jsonl")
    D["LEDGER"] = led

    def avg(step: str) -> float:
        """El costo medio de un paso del flujo desde el 10/11 (catálogo IKEA + ABO)."""
        v = [r["cost_usd"] for r in led if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == step]
        return sum(v) / max(1, len(v))

    D["c_plan"], D["c_choose"] = avg("furnish.plan"), avg("furnish.choose")
    D["c_img"] = cfg.furnish.generators["nano_banana_2"]["usd_per_image"]["1K"]
    D["c_pedido"] = D["c_plan"] + D["c_choose"] + D["c_img"]
    ch = [r["cost_usd"] for r in led if r.get("time", "") >= "2026-11-10" and not r.get("cached") and r["step"] == "furnish.choose"]
    D["c_choose_rango"] = (min(ch), max(ch))
    D["c_scene"] = statistics.mean(r["cost_usd"] for r in led if r["step"] == "furnish.scene" and r.get("time", "") >= "2026-11-12")
    D["c_rerank"] = statistics.mean(r["cost_usd"] for r in led if r["step"].startswith("eval.rerank") and "opus" in (r.get("model") or ""))
    D["c_desc"] = sum(r["cost_usd"] for r in led if r["step"].startswith("catalog.describe")) / len(abo_items)

    def cuenta(r: dict) -> str:
        return r.get("pool") or r.get("provider") or "?"

    D["gasto"] = {acc: sum(r["cost_usd"] for r in led if cuenta(r) == acc) for acc in ("anthropic", "fal")}
    D["gasto_total"] = sum(D["gasto"].values())
    D["topes"] = dict(cfg.budget.accounts)
    por_uso: dict[str, float] = defaultdict(float)
    for r in led:
        por_uso[purpose(r["step"])] += r["cost_usd"]
    D["por_uso"] = dict(por_uso)
    D["n_llamadas"] = len(led)
    lat = [jload(dd / "3_choice.json")["meta"]["latency_s"] for dd in sorted(AMO.glob("final-*"))]
    D["lat_choose"] = float(np.median(lat))
    # el catálogo entero en el contexto: las fichas, en caracteres y en tokens (unos 4 por token)
    cat_chars = sum(len(desc[i]) for i in items) + sum(len(t) for t in abo_desc.values())
    D["cat_tokens"] = cat_chars / 4
    D["opus_in"] = cfg.furnish.llm["models"]["claude-opus-5-5"]["usd_per_m"]["input"]
    D["cat_usd"] = round(D["cat_tokens"] * D["opus_in"] / 1e6, 1)

    # ---------- la réplica (trabajo futuro) ----------
    D["REPLICA"] = jload(RES / "replica/living-dagarna/resultados.json")

    # ---------- fechas para la cronología ----------
    D["fechas"] = {
        "v0": min(run_date(p.name) for p in (RES / "v0_imagen/corridas").iterdir()),
        "v1": run_date(RUN_V1_275),
        "rerank": run_date("20261022-175001_ablacion-reranking"),
        "metricas": run_date(RUN_855),
        "revisado": run_date(latest("_ablacion-catalogo-revisado")),
        "abo": run_date(todos_dir),
        "revision": run_date(latest("_ablacion-camino")),
    }
    return D


if __name__ == "__main__":
    D = load()
    for k in sorted(D):
        v = D[k]
        if isinstance(v, (int, float, str, tuple)) or v is None:
            print(f"{k:28s} {v}")
    for k in ("VT", "IMG_TOT", "filtro_p1", "gasto", "j_grupos", "ej_metrics", "ej_otros", "d_ficha", "d_name", "d_opus",
              "d512", "d_abo", "d_mini", "D21", "fechas", "por_uso", "generador_v1", "CTX", "FM", "reintentos"):
        print(k, D[k])
    print("caso", {k: (v["rank"], v["ranked"][:5], v["relevant"]) for k, v in D["caso"].items()})
