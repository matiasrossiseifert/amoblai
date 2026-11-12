"""Cuántos candidatos por pieza pasarle al LLM que elige (`furnish.candidates`).

Sale gratis de una corrida de reranking ya paga (`evaluar --ablacion reranking.yaml`): si el VLM
ordenó el top-10 de cada búsqueda, la pieza que elegiría entre los primeros k del retrieval es la
mejor ordenada de esas k. Para cada k: el acierto de esa elección (¿es un producto anotado?) y el
techo (hit@k: ¿había alguno anotado entre los k?). Supone que el orden que da el VLM no depende de
cuántos candidatos ve. Es un sustituto: el reranker ordena contra la consulta, sin el ambiente;
el paso choose del flujo elige con la foto del ambiente y el pedido.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

from amoblai.evaluation.metrics import bootstrap_ci

BASE = "qwen3|description|filtro-type"
OUT = Path("datos/resultados/evaluacion_candidatos/curva_k.json")


def choice_curve(run: Path, base: str = BASE, reranker: str = "opus", n_boot: int = 1000) -> dict:
    rows: dict[str, dict[tuple, dict]] = {base: {}, f"{base}|rerank-{reranker}": {}}
    with gzip.open(Path(run) / "rankings.jsonl.gz", "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if r["method"] in rows and r["relevant"]:
                rows[r["method"]][(r["room_id"], r["piece"])] = r
    first, second = rows[base], rows[f"{base}|rerank-{reranker}"]
    keys = sorted(set(first) & set(second))
    groups = [room for room, _ in keys]
    hits: dict[int, np.ndarray] = {}
    out: dict[str, Any] = {"corrida": str(run), "consultas": len(keys), "por_k": {}}
    for k in range(1, 11):
        chosen, ceiling = [], []
        for key in keys:
            top = first[key]["ranked"][:k]
            order = {pid: i for i, pid in enumerate(second[key]["ranked"])}
            pick = min(top, key=lambda pid: order.get(pid, len(order)))
            relevant = set(first[key]["relevant"])
            chosen.append(float(pick in relevant))
            ceiling.append(float(bool(relevant & set(top))))
        hits[k] = np.array(chosen)
        out["por_k"][str(k)] = {
            "acierto_eleccion": round(float(np.mean(chosen)), 4),
            "ic95": [round(v, 4) for v in bootstrap_ci(chosen, groups, n_boot)],
            "techo_hit@k": round(float(np.mean(ceiling)), 4),
        }
    out["diferencias_pareadas"] = {}
    for a, b in ((3, 5), (5, 8), (5, 10)):
        diff = hits[b] - hits[a]
        out["diferencias_pareadas"][f"{a}->{b}"] = {
            "acierto_eleccion": round(float(diff.mean()), 4),
            "ic95": [round(v, 4) for v in bootstrap_ci(list(diff), groups, n_boot)],
        }
    return out
