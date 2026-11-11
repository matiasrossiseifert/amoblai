"""Lee todos los números de la presentación desde los archivos de resultados del repo.

Nada de lo que muestra la presentación se escribe a mano: todo sale de acá. Si un archivo cambia,
se vuelve a correr build.py y los números se actualizan solos.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]
RES = REPO / "datos" / "resultados"
EV = RES / "evaluacion"

RUN_FINAL = "20261110-003643_ablacion-retrieval"  # catálogo revisado (819), 549 búsquedas
RUN_RERANK = "20261109-235522_ablacion-reranking"
RUN_TODOS = "20261110-010145_ablacion-catalogo-todos"
RUN_REVISADO = "20261109-235406_ablacion-catalogo-revisado"
RUNS_REPRO = [  # las tres escrituras de las consultas (catálogo de 855)
    "20261023-173217_ablacion-retrieval",
    "20261023-200437_reproducibilidad-r2",
    "20261023-202248_reproducibilidad-r3",
]
RUN_V1_275 = "20261021-133226_ablacion-texto"  # el catálogo que vio la v0
RUN_V1_268 = "20261021-161057_ablacion-retrieval"
RUN_RERANK_268 = "20261022-175001_ablacion-reranking"
RUN_855 = "20261022-213008_ablacion-retrieval"

BEST = "qwen3|description|filtro-type"

# La foto de IKEA que se usa de ejemplo en "cómo medimos" y en el reranking
EJ_ROOM = "ikea-a-leather-look-made-for-lounging__1364309444239-s4.jpg"
EJ_PIECE = 2  # la alfombra crema de pelo largo

PUBLICAS_ORDEN = [
    "publica-loft-industrial",
    "publica-living-clasico",
    "publica-comedor-clasico-moderno",
    "publica-living-japandi",
    "publica-living-bohemio",
    "publica-estudio-sobrio",
]


def jload(p: Path):
    return json.loads(Path(p).read_text())


def metricas(run: str) -> dict:
    return jload(EV / run / "metricas.json")


def rankings(run: str, method: str | None = None) -> list[dict]:
    rows = []
    with gzip.open(EV / run / "rankings.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            if method is None or r["method"] == method:
                rows.append(r)
    return rows


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


def run_date(run: str) -> dt.date:
    return dt.datetime.strptime(run[:8], "%Y%m%d").date()


def load() -> dict:
    D: dict = {}

    # ---------- catálogo ----------
    items = {}
    for line in (REPO / "datos/procesados/items.jsonl").read_text().splitlines():
        r = json.loads(line)
        items[r["id"]] = r
    desc = {}
    for line in (REPO / "datos/catalogo/descripciones.jsonl").read_text().splitlines():
        r = json.loads(line)
        desc[r["id"]] = r["text"].strip()
    abo_desc = {}
    for line in (REPO / "datos/catalogo/abo/descripciones.jsonl").read_text().splitlines():
        r = json.loads(line)
        abo_desc[r["id"]] = r["text"].strip()
    abo_items = {}
    for line in (REPO / "datos/procesados/abo_items.jsonl").read_text().splitlines():
        r = json.loads(line)
        abo_items[r["id"]] = r
    D["items"], D["desc"], D["abo_desc"], D["abo_items"] = items, desc, abo_desc, abo_items

    corrida = jload(EV / RUN_FINAL / "corrida.json")
    D["n_ikea"] = corrida["index"]["products"]
    D["n_abo"] = len(abo_desc)
    D["n_todos"] = D["n_ikea"] + D["n_abo"]
    D["rooms"] = corrida["rooms"]
    D["embed_max_len"] = corrida["index"]["embedder"]["key"]["max_length"]
    D["embed_model"] = corrida["index"]["embedder"]["key"]["model"].split("/")[-1]
    D["hnsw"] = corrida["index"]["vector_store"]["hnsw"]
    import glob

    cfgs = glob.glob(str(Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-Embedding-0.6B"
                         "/snapshots/*/config.json"))
    D["best_dim"] = json.loads(Path(cfgs[0]).read_text())["hidden_size"] if cfgs else 1024
    D["indice_mb"] = D["n_todos"] * D["best_dim"] * 4 / 1e6  # float32
    D["abo_listados"] = len(abo_items)

    # ABO: medidas y tamaño de foto entre los descriptos; IKEA: asientos sin medidas
    described = [abo_items[i] for i in abo_desc if i in abo_items]
    D["abo_con_medidas"] = sum(1 for r in described if r.get("dimensions_cm")) / len(described)
    D["abo_px_max"] = int(np.median([max(r["image_px"]) for r in described if r.get("image_px")]))
    seats = [r for r in items.values() if r["kind"] in ("sofa", "armchair") or r["category"] == "chair"]
    D["ikea_asientos_sin_medidas"] = sum(1 for r in seats if not r.get("dimensions_cm")) / len(seats)
    from PIL import Image

    sample = [r["photos"][0] for r in list(items.values())[::25]]
    D["ikea_px"] = int(np.median([max(Image.open(REPO / p).size) for p in sample]))

    # ---------- retrieval: la ablación final ----------
    M = metricas(RUN_FINAL)
    D["M"] = M
    b = M[BEST]
    D["best"] = b
    D["n_busquedas"] = b["searches"]
    D["n_resp"] = b["answerable"]
    D["azar_h1"] = b["azar_hit@1"]
    D["azar_h10"] = b["azar_hit@10"]
    D["naive"] = M["hashing|seller|filtro-none"]
    D["desc_hash"] = M["hashing|description|filtro-none"]
    D["minilm"] = M[BEST + "|rerank-minilm-reranker"]
    D["q_type"] = M[BEST + "|consulta-type"]
    D["q_kind"] = M[BEST + "|consulta-kind"]
    D["exact"] = M[BEST + "|exact"]
    D["chunks_max"] = M[BEST + "|chunks-lines-max"]
    D["chunks_al"] = M[BEST + "|chunks-lines-aligned"]
    D["dims"] = {int(k.split("dim-")[1]): v for k, v in M.items() if "|dim-" in k}
    D["dims"][1024] = b
    D["kind"] = M["qwen3|description|filtro-kind"]
    D["none"] = M["qwen3|description|filtro-none"]
    D["namedesc"] = M["qwen3|name+description|filtro-kind"]

    # correlación entre métricas de ranking sobre todas las configuraciones de la corrida
    keys = [k for k in M if M[k].get("mrr@10") is not None]
    mrr = np.array([M[k]["mrr@10"] for k in keys])
    cp = np.array([M[k]["context_precision@10"] for k in keys])
    nd = np.array([M[k]["ndcg@10"] for k in keys])
    D["n_configs"] = len(keys)
    D["corr_cp"] = float(np.corrcoef(mrr, cp)[0, 1])
    D["corr_ndcg"] = float(np.corrcoef(mrr, nd)[0, 1])

    # Chroma contra búsqueda exacta: ¿mismo ranking, búsqueda por búsqueda?
    rows_all = rankings(RUN_FINAL)
    by_method = defaultdict(dict)
    for r in rows_all:
        by_method[r["method"]][(r["room_id"], r["piece"], r["prompt"])] = r["ranked"]
    for f in ("type", "kind"):
        ch = by_method[f"qwen3|description|filtro-{f}"]
        ex = by_method[f"qwen3|description|filtro-{f}|exact"]
        same = sum(1 for k in ch if ch[k] == ex.get(k))
        first = sum(1 for k in ch if ex.get(k) and ch[k][:1] == ex[k][:1])
        D[f"chroma_igual_{f}"] = same
        D[f"chroma_primero_{f}"] = first
        D[f"chroma_total_{f}"] = len(ch)

    # ---------- el ejemplo de "cómo medimos" ----------
    best_rows = [r for r in rows_all if r["method"] == BEST]
    ej = next(r for r in best_rows if r["room_id"] == EJ_ROOM and r["piece"] == EJ_PIECE)
    D["ej"] = ej
    room_rows = [r for r in best_rows if r["room_id"] == EJ_ROOM]
    D["ej_room_queries"] = len(room_rows)
    gt, ctx = set(), set()
    for r in room_rows:
        gt |= set(r["relevant"])
        ctx |= set(r["ranked"][:3])
    D["ej_cr3"] = (len(gt & ctx), len(gt))
    D["ej_annotated"] = room_rows[0]["relevant_any"]
    rk = ej["rank"]
    D["ej_metrics"] = {
        "rank": rk,
        "hit1": int(rk <= 1),
        "hit3": int(rk <= 3),
        "hit5": int(rk <= 5),
        "rr": 1 / rk,
        "ndcg": 1 / np.log2(rk + 1),
        "cp": 1 / rk,
    }
    # el mismo ejemplo después del reranking con Opus
    rr_rows = rankings(RUN_RERANK, BEST + "|rerank-opus")
    ej_rr = next(r for r in rr_rows if r["room_id"] == EJ_ROOM and r["piece"] == EJ_PIECE)
    D["ej_rr"] = ej_rr

    # bootstrap del mejor método (histograma) y una búsqueda por ambiente
    ans = [r for r in best_rows if r["relevant"]]
    vals = [1.0 if r["rank"] == 1 else 0.0 for r in ans]
    groups = [r["room_id"] for r in ans]
    means, lo, hi = bootstrap_means(vals, groups)
    D["boot_means"], D["boot_lo"], D["boot_hi"] = means, lo, hi
    D["boot_rooms"] = len(set(groups))
    D["boot_n"] = len(means)

    # ---------- reranking ----------
    R = metricas(RUN_RERANK)
    D["opus"] = R[BEST + "|rerank-opus"]
    cats_n = b["consultas_por_categoria"]
    D["cats"] = sorted(
        [c for c, n in cats_n.items() if n >= 18], key=lambda c: -b["hit@1_por_categoria"][c]
    )
    D["cats_n"] = cats_n
    led = [json.loads(x) for x in (RES / "gastos.jsonl").read_text().splitlines()]
    rer = [x["cost_usd"] for x in led if x["step"] == "eval.rerank" and not x.get("cached")
           and x["model"] == "claude-opus-5-5"
           and x["time"][:10] == run_date(RUN_RERANK).isoformat()]
    D["rerank_costo_llamada"] = float(np.mean(rer))
    D["rerank_llamadas"] = len(rer)
    D["rerank_total"] = float(sum(rer))
    R268 = metricas(RUN_RERANK_268)
    D["opus268"] = R268[BEST + "|rerank-opus"]
    D["base268"] = R268[BEST]

    # ---------- cuántos candidatos ----------
    D["curva"] = jload(RES / "evaluacion_candidatos/curva_k.json")
    D["k_flujo"] = yaml.safe_load((REPO / "datos/configs/amoblai.yaml").read_text())["furnish"][
        "candidates"
    ]
    cfg_txt = (REPO / "datos/configs/amoblai.yaml").read_text()
    m = re.search(r"candidates: \d+.*?(\d) → 0,\d+, (\d) → 0,\d+", cfg_txt)
    D["k_antes"] = int(m.group(1)) if m else 3

    # ---------- v0 contra v1 ----------
    v0 = []
    import csv

    with open(RES / "v0_imagen/reporte/retriever.csv") as f:
        for r in csv.DictReader(f):
            v0.append(r)
    path = ["E0-naive-clip", "E1-quitar-fondo", "E2-filtro-categoria", "E3-dinov2", "E3-dinov3",
            "E4-dinov3-sin-quitar-fondo"]
    D["v0_path"] = []
    for p in path:
        r = next(x for x in v0 if x["paso"] == p)
        D["v0_path"].append(
            {
                "paso": p,
                "hit1": float(r["hit@1"]),
                "ic": json.loads(r["hit@1_ic95"]),
                "hit10": float(r["hit@10"]),
                "mrr": float(r["mrr@10"]),
                "n": int(r["recortes"]),
            }
        )
    D["v0_det1"] = next(x for x in v0 if x["paso"] == "base-dinov2")
    D["v0_det2"] = next(x for x in v0 if x["paso"] == "base-dinov2-detector-v2")
    D["v1_275"] = metricas(RUN_V1_275)[BEST]
    D["v1_268"] = metricas(RUN_V1_268)[BEST]
    v0m = jload(
        RES / "v0_imagen/corridas/20261006-231521_retriever_abl-retriever-e4-dinov3-sin-quitar-fondo/metrics.json"
    )
    D["v0_cats"] = v0m["crops_per_category"]

    # ---------- reproducibilidad ----------
    reps = [metricas(r) for r in RUNS_REPRO]
    methods = [
        ("qwen3|description|filtro-type", "Qwen3, filtro por tipo"),
        ("qwen3|description|filtro-kind", "Qwen3, filtro por kind"),
        ("hashing|description|filtro-type", "hashing, filtro por tipo"),
        ("bge|description|filtro-type", "BGE, filtro por tipo"),
        ("hashing|seller|filtro-none", "naive: texto del vendedor"),
    ]
    D["repro"] = []
    for k, lab in methods:
        h = [rp[k]["hit@1"] for rp in reps]
        mr = [rp[k]["mrr@10"] for rp in reps]
        D["repro"].append({"k": k, "label": lab, "h": h, "mrr": mr,
                           "mean": float(np.mean(h)), "sd": float(np.std(h, ddof=1)),
                           "mrr_mean": float(np.mean(mr)), "mrr_sd": float(np.std(mr, ddof=1))})
    D["repro_n"] = [rp["qwen3|description|filtro-type"]["answerable"] for rp in reps]
    D["repro_catalogo"] = jload(EV / RUNS_REPRO[0] / "corrida.json")["index"]["products"]
    # ¿el orden entre métodos se mantiene en las tres escrituras?
    q = [rp["qwen3|description|filtro-type"]["hit@1"] for rp in reps]
    D["repro_orden"] = all(
        q[i] > rp[k]["hit@1"]
        for i, rp in enumerate(reps)
        for k in ("bge|description|filtro-type", "hashing|description|filtro-type",
                  "qwen3|description|filtro-kind")
    )

    # ---------- relevancia graduada ----------
    D["grad"] = jload(RES / "evaluacion_graduada/graduada.json")
    D["grad_catalogo"] = jload(EV / D["grad"]["run"] / "corrida.json")["index"]["products"]
    D["h1_855"] = metricas(D["grad"]["run"])[BEST]["hit@1"]

    # ---------- RAGAS sobre la respuesta ----------
    D["ragas"] = []
    for run, lab in [("prueba-alvear", "living, vista 1"), ("prueba-alvear2", "living, vista 2"),
                     ("prueba-alvear2-scene-v2", "living, vista 2 (otro juez)"),
                     ("experimento", "rincón de lectura")]:
        r = jload(RES / "amoblar" / run / "7_metricas_respuesta.json")
        D["ragas"].append({"run": run, "label": lab, **r})

    # ---------- catálogos de punta a punta ----------
    PP = RES / "punta_a_punta/catalogos"
    D["j_abo5"] = jload(PP / "juez_ikea_vs_abo_5ambientes.json")
    D["j_todos5"] = jload(PP / "juez_ikea_vs_todos_5ambientes.json")
    D["j_todos11"] = jload(PP / "juez_ikea_vs_todos.json")
    j = D["j_todos11"]

    def pooled(xs, cat):
        gs = [g for x in xs for s in x["puntajes"][cat] for g in s["grades"]]
        return sum(1 for g in gs if g == 2) / len(gs)

    def crit(xs, cat, k):
        v = [s[k] for x in xs for s in x["puntajes"][cat]]
        return sum(v) / len(v)

    own = [x for x in j["detalle"] if not x["slug"].startswith("publica")]
    pub = [x for x in j["detalle"] if x["slug"].startswith("publica")]
    D["j_grupos"] = {}
    for name, xs in (("propios", own), ("publicos", pub)):
        D["j_grupos"][name] = {
            "n": len(xs),
            "gana_ikea": sum(x["ganador"] == "ikea" for x in xs),
            "gana_todos": sum(x["ganador"] == "todos" for x in xs),
            "empates": sum(x["ganador"] == "tie" for x in xs),
            "util_ikea": pooled(xs, "ikea"),
            "util_todos": pooled(xs, "todos"),
            "pedido_ikea": crit(xs, "ikea", "request"),
            "pedido_todos": crit(xs, "todos", "request"),
            "abo_share": sum(1 for x in xs for p in x["listas"]["todos"] if p["id"].startswith("abo-"))
            / sum(len(x["listas"]["todos"]) for x in xs),
        }
    D["todos_ret"] = metricas(RUN_TODOS)[BEST]
    juez_costo = sum(x["cost_usd"] for x in led if x["step"] == "eval.juez_listas" and not x.get("cached"))
    D["juez_costo"] = juez_costo
    D["describe_costo"] = sum(
        x["cost_usd"] for x in led if x["step"] == "catalog.describe" and not x.get("cached")
    )

    # ambientes vacíos y créditos de las fotos públicas
    ped = yaml.safe_load((REPO / "datos/ambientes_vacios/pedidos.yaml").read_text())["ambientes"]
    D["pedidos"] = {a["slug"]: a for a in ped}
    pubs = yaml.safe_load((REPO / "datos/ambientes_vacios/publicas.yaml").read_text())["fotos"]
    D["publicas"] = {Path(p["archivo"]).name: p for p in pubs}

    # ---------- la imagen ----------
    A = RES / "amoblar"
    D["img"] = {}
    for run in ["caballito-living", "caballito-comedor", "experimento", "experimento-libre",
                "experimento-buen-pedido", "experimento-buen-pedido-estricto", "prueba-alvear2"]:
        d = {"run": run}
        for f, k in (("5_image.json", "gen"), ("6_metricas_imagen.json", "met"),
                     ("4_scene.json", "scene"), ("request.json", "req"), ("3_choice.json", "choice")):
            if (A / run / f).exists():
                d[k] = jload(A / run / f)
        D["img"][run] = d
    D["ref_ikea"] = jload(RES / "evaluacion_imagen/referencia_ikea.json")
    from_cfg = (REPO / "src/amoblai/config.py").read_text()
    m = re.search(r'"attempts": (\d+), "min_inliers": (\d+), "max_shift": ([\d.]+)', from_cfg)
    D["sift_attempts"], D["sift_min_inliers"], D["sift_max_shift"] = (
        int(m.group(1)), int(m.group(2)), float(m.group(3)))
    m = re.search(r"experimento 12, (\d{4}-\d{2}-\d{2})", cfg_txt)
    D["fecha_sift"] = dt.date.fromisoformat(m.group(1))

    # ---------- costos ----------
    cfgy = yaml.safe_load(cfg_txt)
    D["img_precio"] = cfgy["furnish"]["generators"]["nano_banana_2"]["usd_per_image"]["1K"]
    pl, ch = [], []
    for dd in sorted((PP / "todos").iterdir()):
        pl.append(jload(dd / "1_searches.json")["cost_usd"])
        ch.append(jload(dd / "3_choice.json")["cost_usd"])
    D["costo_plan"] = float(np.mean(pl))
    D["costo_choose"] = float(np.mean(ch))
    D["costo_corrida"] = D["costo_plan"] + D["costo_choose"] + D["img_precio"]
    lat = [jload(dd / "3_choice.json")["meta"]["latency_s"] for dd in sorted((PP / "todos").iterdir())]
    D["lat_choose"] = float(np.median(lat))
    by_step = defaultdict(float)
    by_prov = defaultdict(float)
    for x in led:
        if x.get("cached"):
            continue
        by_step[x["step"]] += x["cost_usd"]
        by_prov[x["provider"]] += x["cost_usd"]
    D["gasto_paso"] = dict(by_step)
    D["gasto_prov"] = dict(by_prov)
    D["gasto_total"] = sum(by_prov.values())
    D["n_llamadas"] = sum(1 for x in led if not x.get("cached"))

    # ---------- fechas para la línea de tiempo ----------
    D["fecha_v0"] = run_date(next((RES / "v0_imagen/corridas").iterdir()).name)
    D["fechas"] = {
        "v0": min(run_date(p.name) for p in (RES / "v0_imagen/corridas").iterdir()),
        "v1": run_date(RUN_V1_275),
        "rerank": run_date(RUN_RERANK_268),
        "c855": run_date(RUN_855),
        "metricas": run_date(RUNS_REPRO[0]),
        "sift": D["fecha_sift"],
        "revisado": run_date(RUN_REVISADO),
        "abo": run_date(RUN_TODOS),
    }
    D["n_855"] = jload(EV / RUN_855 / "corrida.json")["index"]["products"]
    D["n_268"] = 268 if False else jload(EV / RUN_V1_268 / "corrida.json").get("index", {}).get("products")
    D["n_275"] = jload(EV / RUN_V1_275 / "corrida.json").get("index", {}).get("products")
    D["revisado_h1"] = (metricas(RUN_855)[BEST]["hit@1"], metricas(RUN_REVISADO)[BEST]["hit@1"])

    # ---------- T4: los experimentos de imagen diseñados (tabla de EXPERIMENTOS.md) ----------
    txt = (REPO / "docs/EXPERIMENTOS.md").read_text()
    sec = txt.split("## T4")[1].split("\n## ")[0]
    D["t4"] = []
    for line in sec.splitlines():
        if line.startswith("| I"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            D["t4"].append(cells)
        if line.startswith("| |") and "Jueces" in line:
            D["t4_jueces"] = [c.strip() for c in line.strip("|").split("|")]
    m = re.search(r"\*\*Total estimado: (.*?)\*\*", sec)
    D["t4_total"] = m.group(1) if m else ""
    return D


if __name__ == "__main__":
    D = load()
    for k in sorted(D):
        v = D[k]
        if isinstance(v, (int, float, str, tuple)) or v is None:
            print(f"{k:28s} {v}")
    print(D["t4"], D["t4_total"])
