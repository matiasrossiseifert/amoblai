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
  corrida `V0_TWIN`, con los 275 productos del primer alcance).
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
    ("+ reranking (Opus 5.5)", "qwen3|description|filtro-type|rerank-opus"),
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
    eval_root: Path, out_dir: Path, v0_runs: Path = paths.RESULTS / "v0_imagen" / "corridas"
) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    all_runs = sorted(latest_runs(eval_root), key=lambda d: d.name)  # por fecha
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
