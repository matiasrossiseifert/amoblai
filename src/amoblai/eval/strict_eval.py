"""Evaluación estricta del retriever: recortes etiquetados a mano con su SKU exacto.

Las etiquetas viven en `anotaciones/estricto.jsonl` (una por línea) y se cargan
con la app `apps/etiquetado.py`. Cada etiqueta fija la caja, así que esta
evaluación no depende del detector: mide solo el retriever.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from amoblai.components import RetrievalComponents, build_retrieval_components
from amoblai.config import AppConfig
from amoblai.eval.metrics import bootstrap_ci, first_relevant_rank, hit_at_k, reciprocal_rank
from amoblai.infra.images import load_image
from amoblai.infra.runs import RunContext
from amoblai.vision.boxes import Box
from amoblai.vision.crops import make_crops
from amoblai.vision.detection import Detection

NOT_IN_CATALOG = "no_esta"
NOT_FURNITURE = "no_es_mueble"


class StrictLabel(BaseModel):
    room_id: str
    box: list[float]
    category: str
    # SKU exacto, o NOT_IN_CATALOG / NOT_FURNITURE.
    sku: str
    labeler: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def key(self) -> tuple[str, tuple[float, ...]]:
        return (self.room_id, tuple(round(v, 1) for v in self.box))


def load_labels(path: Path) -> list[StrictLabel]:
    """Carga las etiquetas; si una caja se etiquetó dos veces, gana la última."""
    path = Path(path)
    if not path.exists():
        return []
    latest: dict[tuple[str, tuple[float, ...]], StrictLabel] = {}
    for line in path.read_text().splitlines():
        if line.strip():
            label = StrictLabel.model_validate_json(line)
            latest[label.key] = label
    return list(latest.values())


def append_label(path: Path, label: StrictLabel) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(label.model_dump(mode="json"), ensure_ascii=False) + "\n")


def run_strict_eval(
    cfg: AppConfig, run: RunContext, comps: RetrievalComponents | None = None
) -> dict[str, Any]:
    comps = comps or build_retrieval_components(cfg, use_threshold=False)
    comps.retriever.threshold = None
    labels = [lb for lb in load_labels(cfg.paths.labels_file) if lb.sku in comps.catalog]
    by_room: dict[str, list[StrictLabel]] = defaultdict(list)
    for lb in labels:
        by_room[lb.room_id].append(lb)
    rows: list[dict[str, Any]] = []
    k_max = max(cfg.eval.ks)
    for room_id, room_labels in sorted(by_room.items()):
        image = load_image(cfg.paths.raw_dir / "images" / "room_scenes" / room_id)
        dets = [Detection(Box.from_list(lb.box), lb.category, "manual", 1.0) for lb in room_labels]
        crops = make_crops(image, dets, comps.remover, cfg.background, cfg.preprocess)
        for lb, res in zip(room_labels, comps.retriever.search(crops), strict=True):
            ranked = res.ranked_skus()[:k_max]
            rows.append(
                {
                    "room_id": room_id,
                    "category": lb.category,
                    "sku": lb.sku,
                    "ranked_skus": ranked,
                    "rank": first_relevant_rank(ranked, [lb.sku]),
                }
            )
    for row in rows:
        run.append_jsonl("estricto.jsonl", row)
    metrics: dict[str, Any] = {"labels": len(rows)}
    if rows:
        groups = [r["room_id"] for r in rows]
        for k in cfg.eval.ks:
            vals = [hit_at_k(r["rank"], k) for r in rows]
            metrics[f"hit@{k}"] = round(sum(vals) / len(vals), 4)
            metrics[f"hit@{k}_ci95"] = [
                round(v, 4)
                for v in bootstrap_ci(vals, groups, cfg.eval.bootstrap_samples, cfg.eval.seed)
            ]
        rr = [reciprocal_rank(r["rank"], k_max) for r in rows]
        metrics[f"mrr@{k_max}"] = round(sum(rr) / len(rr), 4)
    return {"strict": metrics}
