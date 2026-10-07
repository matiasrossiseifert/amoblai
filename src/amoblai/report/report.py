"""Reporte comparativo: junta las métricas de todas las corridas en tablas y gráficos.

Lee `resultados/corridas/*/metrics.json` y escribe en `resultados/reporte/`:
- `retriever.csv` / `retriever.md`: una fila por corrida del retriever;
- `estricto.csv` / `estricto.md`: evaluación con el set etiquetado a mano;
- `e2e.csv` / `e2e.md`: una fila por corrida de punta a punta;
- `retriever_incremental.png`, `retriever_mrr.png`, `e2e.png`.
Cada gráfico tiene su tabla al lado (los valores exactos están en el .md).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

log = logging.getLogger(__name__)

# Paleta categórica validada (primeros 3 slots: pasan CVD en todos los pares).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"


def load_runs(runs_dir: Path) -> list[dict[str, Any]]:
    runs = []
    for d in sorted(Path(runs_dir).glob("*")):
        metrics_path, manifest_path = d / "metrics.json", d / "manifest.json"
        if not (metrics_path.exists() and manifest_path.exists()):
            continue
        manifest = json.loads(manifest_path.read_text())
        runs.append(
            {"dir": d, "manifest": manifest, "metrics": json.loads(metrics_path.read_text())}
        )
    return runs


def _ci(value: list[float] | None) -> str:
    return f"[{value[0]:.3f}, {value[1]:.3f}]" if value else ""


def _readable_step(step: str, setup: dict[str, Any]) -> str:
    """Los pasos de la grilla se nombran por su configuración; los incrementales, por su nombre."""
    if not step.startswith("name-"):
        return step
    fondo = "fondo quitado" if setup.get("background") == "sam" else "con fondo"
    filtro = "con filtro" if setup.get("category_filter") else "sin filtro"
    return f"{setup.get('embedding')} · {fondo} · {filtro}"


def retriever_table(runs: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in runs:
        if r["manifest"]["kind"] != "retriever":
            continue
        m = r["metrics"]
        ret, setup = m.get("retrieval", {}), m.get("setup", {})
        rows.append(
            {
                "run_id": r["manifest"]["run_id"],
                "paso": _readable_step(
                    m.get("ablation", {}).get("step", r["manifest"]["config_name"]), setup
                ),
                "embedder": setup.get("embedding"),
                "fondo": setup.get("background"),
                "filtro_categoria": setup.get("category_filter"),
                "recortes": ret.get("n"),
                "hit@1": ret.get("hit@1"),
                "hit@1_ic95": _ci(ret.get("hit@1_ci95")),
                "hit@5": ret.get("hit@5"),
                "hit@10": ret.get("hit@10"),
                "hit@10_ic95": _ci(ret.get("hit@10_ci95")),
                "mrr@10": ret.get("mrr@10"),
                "mrr@10_ic95": _ci(ret.get("mrr@10_ci95")),
                "recall_items@10": m.get("items", {}).get("recall@10"),
                "azar_hit@1": m.get("random_baseline", {}).get("hit@1"),
                "azar_hit@10": m.get("random_baseline", {}).get("hit@10"),
                "umbral_f1": m.get("threshold_calibration", {}).get("threshold"),
                "_ci": {k: ret.get(f"{k}_ci95") for k in ("hit@1", "hit@5", "hit@10", "mrr@10")},
            }
        )
    return pd.DataFrame(rows)


def strict_table(runs: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in runs:
        s = r["metrics"].get("strict")
        if not s:
            continue
        rows.append(
            {
                "run_id": r["manifest"]["run_id"],
                "config": r["manifest"]["config_name"],
                "etiquetas": s.get("labels"),
                "hit@1": s.get("hit@1"),
                "hit@5": s.get("hit@5"),
                "hit@10": s.get("hit@10"),
                "mrr@10": s.get("mrr@10"),
            }
        )
    return pd.DataFrame(rows)


def e2e_table(runs: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in runs:
        if r["manifest"]["kind"] != "e2e":
            continue
        m = r["metrics"]
        s = m.get("setup", {})
        rows.append(
            {
                "run_id": r["manifest"]["run_id"],
                "config": r["manifest"]["config_name"],
                "generador1": s.get("generator1"),
                "generador2": s.get("generator2"),
                "entrada_gen2": s.get("gen2_base"),
                "modo_gen2": s.get("gen2_mode"),
                "compositing": s.get("composite"),
                "ambientes": m.get("rooms_done"),
                "cobertura": m.get("coverage"),
                "reid@1": m.get("reid@1"),
                "reid@5": m.get("reid@5"),
                "ssim_fuera_final": m.get("ssim_outside_final"),
                "ssim_fuera_imagen1": m.get("ssim_outside_image1"),
                "usd_por_ambiente": m.get("cost_usd_per_room"),
                "latencia_s_por_ambiente": m.get("latency_s_per_room"),
            }
        )
    return pd.DataFrame(rows)


def _style(ax: plt.Axes) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def grouped_bars(
    df: pd.DataFrame, label_col: str, metrics: list[str], title: str, path: Path, ci: bool = True
) -> None:
    n = len(df)
    fig, ax = plt.subplots(figsize=(max(6.0, 1.3 * n + 2), 4.2), facecolor=SURFACE)
    width = 0.8 / len(metrics)
    for j, metric in enumerate(metrics):
        xs = [i - 0.4 + width * (j + 0.5) for i in range(n)]
        values = df[metric].astype(float).tolist()
        yerr = None
        if ci and "_ci" in df:
            lows, highs = [], []
            for v, cis in zip(values, df["_ci"], strict=True):
                c = cis.get(metric) if isinstance(cis, dict) else None
                lows.append(v - c[0] if c else 0.0)
                highs.append(c[1] - v if c else 0.0)
            yerr = [lows, highs]
        ax.bar(
            xs, values, width=width * 0.92, color=SERIES[j % len(SERIES)], label=metric, zorder=2
        )
        if yerr is not None:
            ax.errorbar(
                xs,
                values,
                yerr=yerr,
                fmt="none",
                ecolor=INK_SECONDARY,
                elinewidth=1,
                capsize=2,
                zorder=3,
            )
        if j == 0:  # rotular solo la primera serie (selectivo), por encima de la barra de error
            tops = [v + (yerr[1][i] if yerr is not None else 0.0) for i, v in enumerate(values)]
            for x, v, top in zip(xs, values, tops, strict=True):
                ax.text(x, top + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(range(n), df[label_col].tolist(), rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    _style(ax)
    ax.legend(
        frameon=False, fontsize=9, labelcolor=INK_SECONDARY, ncols=len(metrics), loc="upper left"
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def horizontal_bars(df: pd.DataFrame, label_col: str, metric: str, title: str, path: Path) -> None:
    df = df.sort_values(metric)
    fig, ax = plt.subplots(figsize=(7.5, 0.38 * len(df) + 1.4), facecolor=SURFACE)
    values = df[metric].astype(float).tolist()
    ax.barh(range(len(df)), values, height=0.6, color=SERIES[0], zorder=2)
    for i, v in enumerate(values):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(df)), df[label_col].tolist(), fontsize=8)
    ax.set_xlim(0, 1.0)
    ax.set_title(title, color=INK, fontsize=11, loc="left")
    _style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def build_report(runs_dir: Path, out_dir: Path) -> dict[str, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = load_runs(runs_dir)
    written: dict[str, Path] = {}
    sections = [
        "# Reporte de experimentos",
        "",
        f"Generado a partir de {len(runs)} corridas en `{runs_dir}`.",
        "",
    ]

    ret = retriever_table(runs)
    if not ret.empty:
        public = ret.drop(columns=["_ci"], errors="ignore")
        public.to_csv(out_dir / "retriever.csv", index=False)
        md = public.to_markdown(index=False)
        (out_dir / "retriever.md").write_text(md + "\n")
        sections += ["## Retriever (ambientes IKEA)", "", md, ""]
        written["retriever"] = out_dir / "retriever.md"
        steps = ret[ret["paso"].astype(str).str.match(r"^E\d")].drop_duplicates(
            "paso", keep="first"
        )
        if not steps.empty:
            steps = steps.sort_values("paso")
            grouped_bars(
                steps,
                "paso",
                ["hit@1", "hit@5", "hit@10"],
                "Retriever: camino incremental (IC 95% bootstrap por ambiente)",
                out_dir / "retriever_incremental.png",
            )
            sections += ["![incremental](retriever_incremental.png)", ""]
        # Una barra por configuración: si se corrió dos veces (grilla y camino
        # incremental), se muestra la del camino incremental.
        ret["_setup"] = (
            ret[["embedder", "fondo", "filtro_categoria", "recortes"]]
            .astype(str)
            .agg("|".join, axis=1)
        )
        ret["_incremental"] = ret["paso"].astype(str).str.match(r"^E\d")
        latest = ret.sort_values("_incremental", ascending=False).drop_duplicates("_setup")
        horizontal_bars(
            latest, "paso", "mrr@10", "MRR@10 por configuración", out_dir / "retriever_mrr.png"
        )
        sections += ["![mrr](retriever_mrr.png)", ""]

    strict = strict_table(runs)
    if not strict.empty:
        md = strict.to_markdown(index=False)
        strict.to_csv(out_dir / "estricto.csv", index=False)
        (out_dir / "estricto.md").write_text(md + "\n")
        sections += ["## Retriever, set estricto (etiquetado a mano)", "", md, ""]

    e2e = e2e_table(runs)
    if not e2e.empty:
        md = e2e.to_markdown(index=False)
        e2e.to_csv(out_dir / "e2e.csv", index=False)
        (out_dir / "e2e.md").write_text(md + "\n")
        sections += ["## De punta a punta (ambientes vacíos)", "", md, ""]
        plot = e2e.dropna(subset=["reid@1", "cobertura", "ssim_fuera_final"])
        if not plot.empty:
            plot = plot.assign(etiqueta=plot["entrada_gen2"] + " · " + plot["modo_gen2"])
            grouped_bars(
                plot,
                "etiqueta",
                ["reid@1", "cobertura", "ssim_fuera_final"],
                "De punta a punta: re-identificación, cobertura y preservación",
                out_dir / "e2e.png",
                ci=False,
            )
            sections += ["![e2e](e2e.png)", ""]

    (out_dir / "README.md").write_text("\n".join(sections) + "\n")
    written["readme"] = out_dir / "README.md"
    return written
