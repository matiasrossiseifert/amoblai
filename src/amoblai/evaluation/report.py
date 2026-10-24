"""Reporte de las evaluaciones del retrieval por texto (datos/resultados/evaluacion/*).

Junta la última corrida de cada ablación hecha sobre el mismo catálogo y las mismas consultas que
la más reciente (si un método está en varias, manda la más reciente); las de un catálogo o unas
consultas anteriores van aparte, en su propia tabla. Escribe en `datos/resultados/reporte/`:
- `reporte.md` y `retrieval_texto.csv`: una fila por método;
- `camino_texto.png`: el camino incremental (naive → nuestras descripciones → filtro → mejor
  embedder → reranking), con IC 95%;
- `avanzado.png`: base vectorial (ChromaDB vs. exacta), query rewriting y reranking;
- `texto_vs_imagen.png`: el mejor método por texto contra la mejor configuración de la v0 (por
  imagen, datos/resultados/v0_imagen), sobre los mismos 65 ambientes y el mismo catálogo (la
  corrida `V0_TWIN`, con los 275 productos del primer alcance);
- `curva_k.png`: hit@k hasta k=50 (cuántos candidatos pasarle al LLM que elige);
- `dimension.png`: hit@1 y MRR@10 según la dimensión del embedding (Matryoshka);
- la reproducibilidad: los mismos métodos con las consultas escritas otras dos veces (las
  corridas con `replica` en corrida.json), promedio y desvío;
- la imagen generada: las métricas de cada corrida del flujo con imagen
  (`6_metricas_imagen.json`, evaluation/image.py) y la vara de las fotos reales.
Cada gráfico va con su tabla (los valores exactos están en el .md).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from amoblai import paths

# Paleta categórica validada (primeros 3 slots: pasan CVD en todos los pares).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

# El camino incremental de la presentación: cada paso cambia una sola cosa.
CAMINO = [
    ("T0 naive: hashing, texto del vendedor, sin filtro", "hashing|seller|filtro-none"),
    ("T1 + nuestras descripciones", "hashing|description|filtro-none"),
    ("T2 + filtro por tipo", "hashing|description|filtro-type"),
    ("T2' filtro por kind (más fino)", "hashing|description|filtro-kind"),
    ("T3 Qwen3-Embedding", "qwen3|description|filtro-type"),
    ("T3' BGE", "bge|description|filtro-type"),
    ("T4 + reranking (VLM)", "qwen3|description|filtro-type|rerank-opus"),
]

# Advanced RAG sobre el mejor método: cada fila cambia una sola cosa.
AVANZADO = [
    ("ChromaDB (HNSW)", "qwen3|description|filtro-type"),
    ("búsqueda exacta", "qwen3|description|filtro-type|exact"),
    ("consulta: solo Type", "qwen3|description|filtro-type|consulta-type"),
    ("consulta: solo el kind", "qwen3|description|filtro-type|consulta-kind"),
    ("+ reranking cross-encoder (MiniLM)", "qwen3|description|filtro-type|rerank-minilm-reranker"),
    ("+ reranking cross-encoder (Qwen3)", "qwen3|description|filtro-type|rerank-qwen3-reranker"),
    ("+ reranking VLM (Opus 5.5)", "qwen3|description|filtro-type|rerank-opus"),
]


# La corrida por texto que se compara con la v0: el mismo catálogo que vio la v0.
V0_TWIN = "ablacion-texto"


def setup(run: Path) -> tuple:
    """Sobre qué se corrió: cuántos productos tenía el índice y qué consultas."""
    meta = json.loads((run / "corrida.json").read_text())
    queries = meta.get("queries_meta") or {}
    passes = tuple(p["prompt"] for p in queries.get("passes", []))
    return (meta["index"].get("products"), queries.get("prompt"), passes)


def latest_runs(root: Path) -> list[Path]:
    runs: dict[str, Path] = {}
    for d in sorted(Path(root).glob("*")):
        if (d / "metricas.json").exists():
            runs[d.name.split("_", 1)[1]] = d  # la última de cada nombre
    return sorted(runs.values())


def table(run: Path) -> pd.DataFrame:
    data = json.loads((run / "metricas.json").read_text())
    rows = []
    for name, m in data.items():
        meth = m["method"]
        rows.append(
            {
                "método": name,
                "corrida": run.name,
                "embedder": meth["embedder"],
                "texto": meth["text"],
                "filtro": meth["filter"],
                "base": meth.get("store", "exact"),  # antes de ChromaDB, todo era exacta
                "consulta": meth.get("query", "full"),
                "rerank": meth.get("rerank") or "",
                "consultas": m["answerable"],
                "hit@1": m["hit@1"],
                "hit@1_ic95": m["hit@1_ic95"],
                "hit@3": m["hit@3"],
                "hit@10": m["hit@10"],
                "mrr@10": m["mrr@10"],
                "mrr@10_ic95": m["mrr@10_ic95"],
                "recall_item@10": m["recall_item@10"],
                "context_precision@10": m.get("context_precision@10"),
                "ndcg@10": m.get("ndcg@10"),
                "context_recall@3": m.get("context_recall@3"),
                "context_recall@10": m.get("context_recall@10"),
                "azar_hit@1": m["azar_hit@1"],
            }
        )
    return pd.DataFrame(rows)


def v0_best(v0_runs: Path) -> dict[str, Any] | None:
    """La mejor corrida de la v0 (por imagen) por hit@1, para comparar."""
    best = None
    for d in Path(v0_runs).glob("*_retriever_*"):
        f = d / "metrics.json"
        if not f.exists():
            continue
        m = json.loads(f.read_text())
        r = m.get("retrieval") or {}
        if r.get("n", 0) < 300:  # descarta la corrida con el detector viejo
            continue
        if best is None or r["hit@1"] > best["hit@1"]:
            best = {**r, "setup": m.get("setup"), "run": d.name, "items": m.get("items", {})}
    return best


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def bars(
    labels: list[str],
    series: dict[str, list[float]],
    cis: dict[str, list] | None,
    title: str,
    path: Path,
) -> None:
    n = len(labels)
    fig, ax = plt.subplots(figsize=(max(6.5, 1.6 * n + 2), 4.4), facecolor=SURFACE)
    width = 0.8 / len(series)
    for j, (metric, values) in enumerate(series.items()):
        xs = [i - 0.4 + width * (j + 0.5) for i in range(n)]
        ax.bar(xs, values, width=width * 0.92, color=SERIES[j], label=metric, zorder=2)
        tops = list(values)
        if cis and metric in cis:
            lo = [v - c[0] for v, c in zip(values, cis[metric], strict=True)]
            hi = [c[1] - v for v, c in zip(values, cis[metric], strict=True)]
            ax.errorbar(
                xs,
                values,
                yerr=[lo, hi],
                fmt="none",
                ecolor=INK2,
                elinewidth=1,
                capsize=2,
                zorder=3,
            )
            tops = [c[1] for c in cis[metric]]
        if j == 0:
            for x, v, t in zip(xs, values, tops, strict=True):
                ax.text(x, t + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(n), labels, rotation=15, ha="right", fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, ncols=len(series), loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def lines(
    xs: list[float],
    series: dict[str, list[float]],
    title: str,
    xlabel: str,
    path: Path,
    log_x: bool = False,
    marks: dict[float, str] | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2), facecolor=SURFACE)
    for x, label in (marks or {}).items():
        ax.axvline(x, color=GRID, linewidth=1.2, zorder=1)
        ax.text(x, 0.03, f" {label}", fontsize=8, color=INK2, rotation=90, va="bottom")
    for j, (name, ys) in enumerate(series.items()):
        ax.plot(xs, ys, marker="o", color=SERIES[j % len(SERIES)], label=name, zorder=2)
        if j == 0 or len(series) < 3 or log_x:
            ax.text(xs[-1], ys[-1] + 0.015, f"{ys[-1]:.2f}", fontsize=8, color=INK, ha="center")
    if log_x:
        ax.set_xscale("log", base=2)
        ax.set_xticks(xs, [str(int(x)) for x in xs])
    else:
        ax.set_xticks(xs, [str(int(x)) for x in xs])
    ax.set_ylim(0, 1.05)
    ax.set_xlabel(xlabel, color=INK2, fontsize=9)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    _style(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def replica_of(run: Path) -> str | None:
    return json.loads((run / "corrida.json").read_text()).get("replica")


def k_curve(runs: list[Path], out_dir: Path) -> list[str]:
    """hit@k hasta k=50 de los métodos principales: cuántos candidatos hacen falta."""
    data: dict[str, dict] = {}
    for r in runs:
        for name, m in json.loads((r / "metricas.json").read_text()).items():
            if "curva_hit@k" in m:
                data[name] = m
    keys = [
        ("Qwen3, filtro por tipo", "qwen3|description|filtro-type"),
        ("BGE, filtro por tipo", "bge|description|filtro-type"),
        ("hashing, filtro por tipo", "hashing|description|filtro-type"),
    ]
    keys = [(lab, k) for lab, k in keys if k in data]
    if not keys:
        return []
    ks = [int(k) for k in data[keys[0][1]]["curva_hit@k"]]
    lines(
        ks,
        {lab: [data[k]["curva_hit@k"][str(x)] for x in ks] for lab, k in keys},
        "hit@k: ¿el producto correcto está entre los k candidatos?",
        "k (candidatos por pieza)",
        out_dir / "curva_k.png",
        marks={3: "el flujo hoy (3)", 10: "el reranker (10)"},
    )
    head = "| método | " + " | ".join(f"k={k}" for k in ks) + " |"
    md = ["## ¿Cuántos candidatos? La curva de hit@k", "", head, "|---|" + "---|" * len(ks)]
    for lab, k in keys:
        md.append(
            f"| {lab} | " + " | ".join(f"{data[k]['curva_hit@k'][str(x)]:.3f}" for x in ks) + " |"
        )
    md += ["", "![curva k](curva_k.png)", ""]
    return md


def dimension_section(by: pd.DataFrame, out_dir: Path) -> list[str]:
    """Qwen3 + filtro por tipo con los vectores truncados (Matryoshka)."""
    base = "qwen3|description|filtro-type"
    dims = [(int(n.rsplit("dim-", 1)[1]), n) for n in by.index if n.startswith(base + "|dim-")]
    if not dims or base not in by.index:
        return []
    dims = [*sorted(dims), (1024, base)]
    xs = [d for d, _ in dims]
    lines(
        xs,
        {
            "hit@1": [by.loc[n, "hit@1"] for _, n in dims],
            "MRR@10": [by.loc[n, "mrr@10"] for _, n in dims],
            "hit@10": [by.loc[n, "hit@10"] for _, n in dims],
        },
        "Qwen3-Embedding truncado (Matryoshka): dimensión del vector",
        "dimensión",
        out_dir / "dimension.png",
        log_x=True,
    )
    md = [
        "## Dimensión del embedding (Matryoshka)",
        "",
        "| dimensión | bytes por vector | hit@1 | hit@10 | MRR@10 |",
        "|---|---|---|---|---|",
    ]
    for d, n in dims:
        md.append(
            f"| {d} | {4 * d} | {by.loc[n, 'hit@1']:.3f} | {by.loc[n, 'hit@10']:.3f} "
            f"| {by.loc[n, 'mrr@10']:.3f} |"
        )
    md += ["", "![dimensión](dimension.png)", ""]
    return md


def chunks_section(by: pd.DataFrame) -> list[str]:
    base = "qwen3|description|filtro-type"
    rows = [
        ("un documento por producto (ChromaDB)", base),
        ("cada línea un chunk, el producto vale su mejor línea", base + "|chunks-lines-max"),
        ("línea contra línea del mismo rótulo, promedio", base + "|chunks-lines-aligned"),
    ]
    rows = [(lab, n) for lab, n in rows if n in by.index]
    if len(rows) < 2:
        return []
    md = [
        "## Splitting: ¿un documento por producto o un chunk por línea?",
        "",
        "| splitting | hit@1 | hit@10 | MRR@10 |",
        "|---|---|---|---|",
    ]
    for lab, n in rows:
        md.append(
            f"| {lab} | {by.loc[n, 'hit@1']:.3f} {_ci(by.loc[n, 'hit@1_ic95'])} "
            f"| {by.loc[n, 'hit@10']:.3f} | {by.loc[n, 'mrr@10']:.3f} |"
        )
    return [*md, ""]


def _ci(v) -> str:
    return f"[{v[0]:.2f}–{v[1]:.2f}]" if isinstance(v, list | tuple) else ""


def replicas_section(main: pd.DataFrame, replicas: list[Path]) -> list[str]:
    """Los mismos métodos con las consultas escritas tres veces: promedio ± desvío."""
    if not replicas:
        return []
    by_rep = {replica_of(r): table(r).set_index("método") for r in replicas}
    names = sorted({n for t in by_rep.values() for n in t.index})
    base = main.set_index("método")
    md = [
        "## Reproducibilidad: tres escrituras independientes de las consultas",
        "",
        "La búsqueda es determinística: lo que varía es quién escribe la consulta (en el flujo, "
        "el paso plan). Las mismas fotos y los mismos prompts, tres subagentes distintos por "
        "lote. Promedio ± desvío estándar (n=3) y el rango.",
        "",
        "| método | consultas (r1/r2/r3) | hit@1 | MRR@10 | hit@10 |",
        "|---|---|---|---|---|",
    ]
    for n in names:
        tabs = [base] + [by_rep[r] for r in sorted(by_rep)]
        if not all(n in t.index for t in tabs):
            continue
        cells = []
        for metric in ("hit@1", "mrr@10", "hit@10"):
            vals = pd.Series([float(t.loc[n, metric]) for t in tabs])
            cells.append(
                f"{vals.mean():.3f} ± {vals.std(ddof=1):.3f} ({vals.min():.3f}–{vals.max():.3f})"
            )
        counts = "/".join(str(int(t.loc[n, "consultas"])) for t in tabs)
        md.append(f"| {n} | {counts} | " + " | ".join(cells) + " |")
    return [*md, ""]


def image_section(runs_dir: Path, reference: Path) -> list[str]:
    """Las métricas de la imagen generada (evaluation/image.py) y la vara de fotos reales."""
    found = sorted(Path(runs_dir).glob("*/6_metricas_imagen.json"))
    if not found:
        return []
    md = [
        "## La imagen generada",
        "",
        "Fidelidad: cada producto de la lista buscado en la imagen final (Grounding DINO), "
        "recortado y comparado con su foto del catálogo (DINOv3); *identificado* = el más "
        "parecido al recorte entre los productos de su tipo es él. Ambiente: SSIM fuera de los "
        "muebles y fracción de puntos SIFT de la foto original reencontrados (RANSAC). Pedido: "
        "SigLIP 2 entre el pedido y la imagen final, menos lo mismo con la foto vacía; puesto "
        "del pedido real entre él y seis pedidos de contraste.",
        "",
        "| corrida | generador | detectados | identificados@1 | coseno | inventadas "
        "| SSIM fuera | SIFT | pedido Δ (puesto) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for f in found:
        r = json.loads(f.read_text())
        fi, a, q = r["fidelidad"], r["ambiente"], r["pedido_imagen"]
        md.append(
            f"| {r['corrida']} | {r['generador']} | {fi['detectados']}/{fi['productos']} "
            f"| {fi['identificados@1']} | {fi['coseno_medio']} | {len(r['inventadas'])} "
            f"| {a['ssim_fuera_de_los_muebles']} | {a.get('sift_reencontrados')} "
            f"| {q['delta']:+.3f} ({q['puesto_entre_contrastes']}/{q['contrastes'] + 1}) |"
        )
    md.append("")
    for f in found:
        r = json.loads(f.read_text())
        md += [
            f"### `{r['corrida']}` por producto",
            "",
            "| producto | kind | puesto | coseno |",
            "|---|---|---|---|",
        ]
        for p in r["productos"]:
            pos = f"{p['puesto']}/{p['entre']}" if p["detectado"] else "no se detectó"
            md.append(f"| {p['id']} | {p['kind']} | {pos} | {p.get('coseno')} |")
        md.append("")
    if Path(reference).exists():
        ref = json.loads(Path(reference).read_text())
        md += [
            "### La vara: la misma identificación con fotos reales (ambientes IKEA)",
            "",
            f"{ref['recortes']} recortes de {ref['ambientes']} ambientes: hit@1 {ref['hit@1']:.3f} "
            f"{_ci(ref['hit@1_ic95'])}, MRR@10 {ref['mrr@10']:.3f}, coseno medio "
            f"{ref['coseno_medio']:.3f}.",
            "",
            "| grupo | hit@1 | recortes |",
            "|---|---|---|",
            *[f"| {g} | {v[0]:.2f} | {v[1]} |" for g, v in ref["hit@1_por_grupo"].items()],
            "",
        ]
    return md


def graded_section(graded: Path) -> list[str]:
    """La relevancia graduada del top-3 (evaluation/graded.py)."""
    if not Path(graded).exists():
        return []
    r = json.loads(Path(graded).read_text())
    md = [
        "## Relevancia graduada del top-3 (juez)",
        "",
        f"Método `{r['method']}`. Un juez (subagente) califica cada uno de los tres primeros "
        "candidatos contra la pieza que se ve en el ambiente: 2 el mismo o indistinguible, 1 una "
        "alternativa aceptable, 0 no sirve. *útil@k*: alguno de los k primeros con 1 o 2.",
        "",
        "| consultas | n | nota del 1.º | útil@1 | útil@3 | un 2 en el top-3 | NDCG@3 |",
        "|---|---|---|---|---|---|---|",
    ]
    for g, m in r["consultas"].items():
        md.append(
            f"| {g} | {m['n']} | {m['nota1']:.2f} | {m['util1']:.3f} {_ci(m['util1_ic95'])} "
            f"| {m['util3']:.3f} {_ci(m['util3_ic95'])} | {m['exacto3']:.3f} | {m['ndcg3']:.3f} |"
        )
    a = r.get("acuerdo_con_gt")
    if a:
        md += [
            "",
            f"Acuerdo con el ground truth: de {a['anotados_en_top3']} productos anotados que "
            f"aparecen en el top-3, el juez le dio 2 al {100 * a['anotado_con_2']:.0f}%; a los "
            f"demás candidatos, al {100 * (a['otros_con_2'] or 0):.0f}%.",
        ]
    return [*md, ""]


def space_section(space: Path, out_dir: Path) -> list[str]:
    """El espacio de embeddings (evaluation/space.py)."""
    if not Path(space).exists():
        return []
    r = json.loads(Path(space).read_text())
    md = [
        "## El espacio de embeddings",
        "",
        f"{r['productos']} descripciones. Separabilidad: de cada producto, ¿su vecino más "
        "cercano es de su mismo kind / tipo?, y el silhouette por kind (coseno).",
        "",
        "| embedder | vecino del mismo kind | vecino del mismo tipo | silhouette por kind |",
        "|---|---|---|---|",
    ]
    for e, m in r["separabilidad"].items():
        md.append(
            f"| {e} | {m['vecino_mismo_kind']:.3f} | {m['vecino_mismo_tipo']:.3f} "
            f"| {m['silhouette_kind']:.3f} |"
        )
    md += [
        "",
        "| consulta | mejor coseno | coseno del 10.º | kinds del top-10 |",
        "|---|---|---|---|",
    ]
    for name, q in r["consultas"].items():
        md.append(
            f"| {name.replace('_', ' ')} | {q['mejor_coseno']:.3f} | {q['coseno_10']:.3f} "
            f"| {', '.join(q['kinds_top10'])} |"
        )
    md.append("")
    if (Path(out_dir) / "umap.png").exists():
        md += ["![umap](umap.png)", ""]
    return md


def answer_section(runs_dir: Path) -> list[str]:
    """RAGAS sobre la respuesta en texto del flujo (evaluation/answer.py)."""
    found = sorted(Path(runs_dir).glob("*/7_metricas_respuesta.json"))
    if not found:
        return []
    md = [
        "## La respuesta en texto: faithfulness y answer relevance (RAGAS)",
        "",
        "Faithfulness: de las afirmaciones de hecho del porqué de cada producto, cuántas se "
        "infieren de lo que vio el sistema (pedido, foto del ambiente, foto, descripción y medida "
        "de cada producto). Answer relevance: coseno medio (Qwen3) entre el pedido original y tres "
        "pedidos que un juez que no lo vio infiere de la respuesta; la vara es el mismo coseno con "
        "pedidos de contraste. Jueces: subagentes de Claude Code.",
        "",
        "| corrida | afirmaciones | faithfulness | answer relevance | vara | no sostenidas |",
        "|---|---|---|---|---|---|",
    ]
    for f in found:
        r = json.loads(f.read_text())
        fi, rel = r.get("fidelidad", {}), r.get("relevancia", {})
        bad = "; ".join(fi.get("no_sostenidas") or [])
        md.append(
            f"| {r['corrida']} | {fi.get('afirmaciones')} | {fi.get('faithfulness')} "
            f"| {rel.get('answer_relevance')} | {rel.get('vara_contrastes')} | {bad} |"
        )
    return [*md, ""]


def category_tables(run: Path, df: pd.DataFrame) -> list[str]:
    """hit@1 por categoría y por pasada de consultas, de los métodos de `run` que están en
    `df`: dónde anda bien y dónde no."""
    data = json.loads((run / "metricas.json").read_text())
    names = [n for n in data if n in set(df["método"])]
    if not names or "hit@1_por_categoria" not in data[names[0]]:
        return []
    cats = sorted({c for n in names for c in data[n]["hit@1_por_categoria"]})
    counts = data[names[0]]["consultas_por_categoria"]
    lines = [
        "## hit@1 por categoría",
        "",
        "| método | " + " | ".join(f"{c} ({counts.get(c, 0)})" for c in cats) + " |",
        "|---|" + "---|" * len(cats),
    ]
    for n in names:
        per = data[n]["hit@1_por_categoria"]
        lines.append(f"| {n} | " + " | ".join(f"{per.get(c, 0):.2f}" for c in cats) + " |")
    lines.append("")
    if any(len(data[n].get("por_pasada", {})) > 1 for n in names):
        passes = sorted(data[names[0]]["por_pasada"])
        lines += [
            "## Por pasada de consultas (v1: muebles del primer alcance; v2: la ampliación)",
            "",
            "| método | " + " | ".join(f"{p} hit@1 / MRR" for p in passes) + " |",
            "|---|" + "---|" * len(passes),
        ]
        for n in names:
            pp = data[n]["por_pasada"]
            cells = [
                f"{pp[p]['hit@1']:.3f} / {pp[p]['mrr@10']:.3f} ({pp[p]['consultas']})"
                if p in pp
                else "—"
                for p in passes
            ]
            lines.append(f"| {n} | " + " | ".join(cells) + " |")
        lines.append("")
    return lines


def build_report(
    eval_root: Path,
    out_dir: Path,
    v0_runs: Path = paths.RESULTS / "v0_imagen" / "corridas",
    runs_dir: Path = paths.RUNS,
    image_reference: Path = paths.IMAGE_REFERENCE,
) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    every = sorted(latest_runs(eval_root), key=lambda d: d.name)  # por fecha
    replicas = [r for r in every if replica_of(r)]
    all_runs = [r for r in every if not replica_of(r)]
    if not all_runs:
        return written
    current = setup(all_runs[-1])
    runs = [r for r in all_runs if setup(r) == current]
    older = [r for r in all_runs if setup(r) != current]
    df = pd.concat([table(r) for r in runs]).drop_duplicates("método", keep="last")
    public = df.copy()
    for c in ("hit@1_ic95", "mrr@10_ic95"):
        public[c] = public[c].map(lambda v: f"[{v[0]:.3f}, {v[1]:.3f}]")
    public.to_csv(out_dir / "retrieval_texto.csv", index=False)
    products = current[0]
    md = [
        f"# Retrieval por texto ({products} productos, ambientes IKEA)",
        "",
        "Corridas: " + ", ".join(f"`{r}`" for r in sorted(set(df["corrida"]))) + ".",
        "",
        public.to_markdown(index=False),
        "",
    ]
    md += category_tables(runs[-1], df)

    by = df.set_index("método")
    avanzado = [(lab, key) for lab, key in AVANZADO if key in by.index]
    if len(avanzado) > 1:
        labels = [lab for lab, _ in avanzado]
        keys = [key for _, key in avanzado]
        bars(
            labels,
            {
                "hit@1": [by.loc[k, "hit@1"] for k in keys],
                "hit@10": [by.loc[k, "hit@10"] for k in keys],
                "MRR@10": [by.loc[k, "mrr@10"] for k in keys],
            },
            {
                "hit@1": [by.loc[k, "hit@1_ic95"] for k in keys],
                "MRR@10": [by.loc[k, "mrr@10_ic95"] for k in keys],
            },
            "Qwen3 + descripciones + filtro por tipo: base vectorial, consulta y reranking",
            out_dir / "avanzado.png",
        )
        md += [
            "## Base vectorial, query rewriting y reranking",
            "",
            "![avanzado](avanzado.png)",
            "",
        ]
        written["avanzado"] = out_dir / "avanzado.png"
    camino = [(lab, key) for lab, key in CAMINO if key in by.index]
    if camino:
        labels = [lab for lab, _ in camino]
        keys = [key for _, key in camino]
        bars(
            labels,
            {
                "hit@1": [by.loc[k, "hit@1"] for k in keys],
                "hit@10": [by.loc[k, "hit@10"] for k in keys],
                "MRR@10": [by.loc[k, "mrr@10"] for k in keys],
            },
            {
                "hit@1": [by.loc[k, "hit@1_ic95"] for k in keys],
                "MRR@10": [by.loc[k, "mrr@10_ic95"] for k in keys],
            },
            "Retrieval por texto: camino incremental (IC 95% bootstrap por ambiente)",
            out_dir / "camino_texto.png",
        )
        md += ["![camino](camino_texto.png)", ""]
        written["camino"] = out_dir / "camino_texto.png"

    md += k_curve(runs, out_dir)
    if (out_dir / "curva_k.png").exists():
        written["curva_k"] = out_dir / "curva_k.png"
    md += dimension_section(by, out_dir)
    if (out_dir / "dimension.png").exists():
        written["dimension"] = out_dir / "dimension.png"
    md += chunks_section(by)
    md += replicas_section(df, replicas)
    md += image_section(runs_dir, image_reference)
    md += graded_section(paths.RESULTS / "evaluacion_graduada" / "graduada.json")
    md += answer_section(runs_dir)
    md += space_section(paths.RESULTS / "evaluacion_espacio" / "espacio.json", out_dir)

    twin = [r for r in all_runs if r.name.split("_", 1)[1] == V0_TWIN]
    v0 = v0_best(v0_runs)
    if v0 and twin:
        tw = table(twin[-1])
        best_text = tw[tw["rerank"] == ""].sort_values("hit@1", ascending=False).iloc[0]
        labels = [
            f"v0 imagen: {v0['setup']['embedding']} (fondo {v0['setup']['background']})",
            f"v1 texto: {best_text['método']}",
        ]
        bars(
            labels,
            {
                "hit@1": [v0["hit@1"], best_text["hit@1"]],
                "hit@10": [v0["hit@10"], best_text["hit@10"]],
                "MRR@10": [v0["mrr@10"], best_text["mrr@10"]],
            },
            {
                "hit@1": [v0["hit@1_ci95"], best_text["hit@1_ic95"]],
                "MRR@10": [v0["mrr@10_ci95"], best_text["mrr@10_ic95"]],
            },
            "Mismo ground truth: retrieval por imagen (v0) vs. por texto (v1)",
            out_dir / "texto_vs_imagen.png",
        )
        md += [
            "## Texto vs. imagen",
            "",
            "| | consultas | hit@1 | hit@10 | MRR@10 |",
            "|---|---|---|---|---|",
            f"| v0 imagen ({v0['run']}) | {v0['n']} recortes | {v0['hit@1']:.3f} "
            f"| {v0['hit@10']:.3f} | {v0['mrr@10']:.3f} |",
            f"| v1 texto ({best_text['método']}) | {best_text['consultas']} consultas "
            f"| {best_text['hit@1']:.3f} | {best_text['hit@10']:.3f} | {best_text['mrr@10']:.3f} |",
            "",
            "![texto vs imagen](texto_vs_imagen.png)",
            "",
        ]
        written["texto_vs_imagen"] = out_dir / "texto_vs_imagen.png"
    if older:
        md += [
            "## Corridas anteriores (otro catálogo u otras consultas)",
            "",
            "No se mezclan con las de arriba: cambian el universo de búsqueda o las consultas.",
            "",
        ]
        for r in older:
            n, _, ps = setup(r)
            t = table(r)[["método", "consultas", "hit@1", "hit@10", "mrr@10"]]
            label = f"{n} productos" + (f", consultas + {', '.join(ps)}" if ps else "")
            md += [f"### `{r.name}` ({label})", "", t.to_markdown(index=False), ""]
    (out_dir / "README.md").unlink(missing_ok=True)  # el nombre viejo
    (out_dir / "reporte.md").write_text("\n".join(md) + "\n")
    written["reporte"] = out_dir / "reporte.md"
    return written
