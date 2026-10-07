"""Estudios de ablación: una corrida por combinación de configuraciones.

Un plan de ablación (configs/ablaciones/*.yaml) define:
- `kind`: `retriever` (ambientes de IKEA, gratis) o `e2e` (ambientes vacíos, usa
  los generadores configurados; con la caché, cambiar solo la entrada o el modo
  del generador n.º 2 reusa la imagen 1);
- `base`: config de partida;
- `grid`: valores por campo; se corre el producto cartesiano;
- `incremental`: (opcional) el camino E0 → E1 → … que se muestra en la presentación,
  con los overrides de cada paso.

El retrieval es local y gratis, así que conviene correr la grilla completa y
después leer el camino incremental en el reporte. Las ablaciones e2e cuestan
plata (salvo con el editor manual o en dry-run): conviene una grilla chica.
"""

from __future__ import annotations

import itertools
import logging
from pathlib import Path
from typing import Any

import yaml

from amoblai.config import AppConfig, load_config
from amoblai.eval.retriever_eval import run_retriever_eval
from amoblai.infra.runs import RunContext

log = logging.getLogger(__name__)


def expand_plan(plan: dict[str, Any]) -> list[tuple[str, list[str]]]:
    """Devuelve (nombre, overrides) por cada corrida del plan."""
    runs: list[tuple[str, list[str]]] = []
    for step in plan.get("incremental", []) or []:
        overrides = [f"{k}={_yaml_value(v)}" for k, v in step["set"].items()]
        runs.append((step["name"], overrides))
    grid = plan.get("grid") or {}
    keys = list(grid)
    for values in itertools.product(*(grid[k] for k in keys)):
        overrides = [f"{k}={_yaml_value(v)}" for k, v in zip(keys, values, strict=True)]
        name = "__".join(f"{k.split('.')[-1]}-{v}" for k, v in zip(keys, values, strict=True))
        runs.append((name, overrides))
    return runs


def _yaml_value(value: Any) -> str:
    return yaml.safe_dump(value, default_flow_style=True).strip().removesuffix("...").strip()


def run_ablation(
    plan_path: Path, only: list[str] | None = None, calibrate: bool = False
) -> list[Path]:
    """Corre el plan. Con `calibrate`, guarda el umbral de cada combinación (solo retriever)."""
    plan = yaml.safe_load(Path(plan_path).read_text())
    kind = plan.get("kind", "retriever")
    if kind not in ("retriever", "e2e"):
        raise ValueError(f"kind desconocido en el plan: {kind!r}")
    base = Path(plan_path).parent / plan["base"]
    done: list[Path] = []
    seen: set[str] = set()
    for name, overrides in expand_plan(plan):
        if only and name not in only:
            continue
        cfg: AppConfig = load_config(
            base, [*overrides, f"name={plan.get('name', 'ablacion')}-{name}"]
        )
        signature = cfg.model_dump_json(exclude={"name"})
        if signature in seen:
            log.info("Saltando %s: misma config que una corrida anterior del plan", name)
            continue
        seen.add(signature)
        log.info("Ablación %s: %s", name, overrides)
        run = RunContext(cfg, kind, name=cfg.name)
        if kind == "retriever":
            metrics = run_retriever_eval(cfg, run, calibrate=calibrate)
        else:
            from amoblai.eval.e2e_eval import run_e2e_eval

            metrics = run_e2e_eval(cfg, run)
        metrics["ablation"] = {"plan": str(plan_path), "step": name, "overrides": overrides}
        run.finish(metrics)
        done.append(run.dir)
    return done
