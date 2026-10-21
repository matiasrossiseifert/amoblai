"""Evaluación de punta a punta sobre ambientes vacíos (ambientes_vacios/).

- **Re-identificación**: se vuelve a detectar cada mueble en la imagen final, se
  lo vuelve a buscar y se verifica si devuelve el SKU que se insertó (top-1 y
  top-5). Mide si el generador n.º 2 reprodujo el producto real.
- **Preservación del ambiente**: SSIM y error absoluto medio entre la foto
  original y la final, fuera de las cajas de los muebles (dilatadas).
- **Cobertura**: % de muebles genéricos de la imagen 1 que encontraron un
  producto por encima del umbral.
- **Costo y latencia** por ambiente (de los registros de uso).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image
from skimage.metrics import structural_similarity

from amoblai_imagen.config import AppConfig
from amoblai_imagen.generation.geometry import boxes_mask
from amoblai_imagen.infra.images import load_image
from amoblai_imagen.infra.runs import RunContext, SubRun
from amoblai_imagen.infra.usage import summarize_usage
from amoblai_imagen.pipeline.query import FurnishPipeline, PipelineResult
from amoblai_imagen.vision.crops import make_crops

log = logging.getLogger(__name__)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def ssim_outside(
    original: Image.Image, other: Image.Image, exclude: np.ndarray
) -> dict[str, float | None]:
    """SSIM medio y error absoluto medio fuera de la máscara `exclude` (escala de grises)."""
    if other.size != original.size:
        other = other.resize(original.size, Image.Resampling.LANCZOS)
    a = np.asarray(original.convert("L"), dtype=np.float64)
    b = np.asarray(other.convert("L"), dtype=np.float64)
    keep = ~exclude
    if keep.sum() == 0:
        return {"ssim_outside": None, "mae_outside": None, "outside_frac": 0.0}
    _, ssim_map = structural_similarity(a, b, data_range=255.0, full=True)
    return {
        "ssim_outside": round(float(ssim_map[keep].mean()), 4),
        "mae_outside": round(float(np.abs(a - b)[keep].mean()), 3),
        "outside_frac": round(float(keep.mean()), 4),
    }


def reidentify(
    result: PipelineResult, pipeline: FurnishPipeline, iou_min: float = 0.3
) -> list[dict[str, Any]]:
    """Para cada producto insertado: ¿se vuelve a encontrar en la imagen final?"""
    assert result.final is not None
    comps = pipeline.comps
    dets = comps.detector.detect(result.final)
    crops = make_crops(
        result.final, dets, comps.remover, pipeline.cfg.background, pipeline.cfg.preprocess
    )
    threshold = comps.retriever.threshold
    comps.retriever.threshold = None
    try:
        retrievals = comps.retriever.search(crops)
    finally:
        comps.retriever.threshold = threshold
    rows = []
    used: set[int] = set()
    for item in result.accepted:
        best, best_iou = None, 0.0
        for j, det in enumerate(dets):
            if j in used or det.category != item.detection.category:
                continue
            iou = det.box.iou(item.detection.box)
            if iou > best_iou:
                best, best_iou = j, iou
        row: dict[str, Any] = {
            "inserted_sku": item.product.sku if item.product else None,
            "category": item.detection.category,
            "redetected": best is not None and best_iou >= iou_min,
            "iou": round(best_iou, 3),
        }
        if row["redetected"]:
            used.add(best)
            ranked = retrievals[best].ranked_skus()
            row["reid_top1"] = bool(ranked) and ranked[0] == row["inserted_sku"]
            row["reid_top5"] = row["inserted_sku"] in ranked[:5]
            row["retrieved_top5"] = ranked[:5]
        else:
            row["reid_top1"] = row["reid_top5"] = False
        rows.append(row)
    return rows


def evaluate_result(result: PipelineResult, pipeline: FurnishPipeline) -> dict[str, Any]:
    cfg = pipeline.cfg
    metrics: dict[str, Any] = {
        "status": result.status,
        "detections_image1": len(result.items),
        "accepted": len(result.accepted),
        "coverage": round(len(result.accepted) / len(result.items), 4) if result.items else None,
    }
    if result.final is None or result.image1 is None:
        return metrics
    reid = reidentify(result, pipeline) if result.accepted else []
    metrics["reid"] = reid
    if reid:
        metrics["reid@1"] = round(sum(r["reid_top1"] for r in reid) / len(reid), 4)
        metrics["reid@5"] = round(sum(r["reid_top5"] for r in reid) / len(reid), 4)
        metrics["redetected"] = round(sum(r["redetected"] for r in reid) / len(reid), 4)
    # Fuera de las cajas: las de la imagen 1 (dónde se amobló) y las de la imagen final.
    final_dets = pipeline.comps.detector.detect(result.final)
    boxes = [d.box for d in result.detections] + [d.box for d in final_dets]
    exclude = boxes_mask(result.original.size, boxes, cfg.eval.ssim_box_dilation)
    metrics["preservation_final"] = ssim_outside(result.original, result.final, exclude)
    metrics["preservation_image1"] = ssim_outside(result.original, result.image1, exclude)
    return metrics


def load_room_prompts(rooms_dir: Path) -> tuple[str, dict[str, str]]:
    path = Path(rooms_dir) / "prompts.yaml"
    if not path.exists():
        return ("", {})
    data = yaml.safe_load(path.read_text()) or {}
    return (
        str(data.get("default", "")),
        {str(k): str(v) for k, v in (data.get("rooms") or {}).items()},
    )


def list_rooms(rooms_dir: Path) -> list[Path]:
    return sorted(p for p in Path(rooms_dir).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)


def run_e2e_eval(
    cfg: AppConfig, run: RunContext, rooms_dir: Path | None = None, limit: int | None = None
) -> dict[str, Any]:
    rooms_dir = Path(rooms_dir or cfg.paths.empty_rooms_dir)
    rooms = list_rooms(rooms_dir)[:limit] if limit else list_rooms(rooms_dir)
    if not rooms:
        raise FileNotFoundError(f"No hay imágenes de ambientes vacíos en {rooms_dir}")
    default_prompt, prompts = load_room_prompts(rooms_dir)
    pipeline = FurnishPipeline.from_config(cfg)
    per_room: dict[str, dict[str, Any]] = {}
    for path in rooms:
        prompt = prompts.get(path.name, default_prompt)
        sub = SubRun(run, f"ambientes/{path.stem}")
        result = pipeline.run(load_image(path), prompt, run=sub)
        metrics = evaluate_result(result, pipeline)
        metrics["usage"] = summarize_usage(result.usage)
        metrics["pipeline_time_s"] = round(sum(result.timings.values()), 2)
        sub.finish(metrics)
        per_room[path.name] = metrics
        log.info("%s: %s", path.name, {k: v for k, v in metrics.items() if k != "reid"})
    return aggregate_e2e(per_room, cfg)


def aggregate_e2e(per_room: dict[str, dict[str, Any]], cfg: AppConfig) -> dict[str, Any]:
    done = {k: v for k, v in per_room.items() if v["status"] in ("ok", "no_furniture")}

    def mean(values: list[float | None]) -> float | None:
        vals = [v for v in values if v is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    reid_rows = [r for v in done.values() for r in v.get("reid", [])]
    return {
        "rooms": len(per_room),
        "rooms_done": len(done),
        "rooms_pending_manual": sum(
            1 for v in per_room.values() if v["status"] == "pending_manual"
        ),
        "coverage": mean([v.get("coverage") for v in done.values()]),
        "reid@1": round(sum(r["reid_top1"] for r in reid_rows) / len(reid_rows), 4)
        if reid_rows
        else None,
        "reid@5": round(sum(r["reid_top5"] for r in reid_rows) / len(reid_rows), 4)
        if reid_rows
        else None,
        "redetected": round(sum(r["redetected"] for r in reid_rows) / len(reid_rows), 4)
        if reid_rows
        else None,
        "inserted_items": len(reid_rows),
        "ssim_outside_final": mean(
            [v.get("preservation_final", {}).get("ssim_outside") for v in done.values()]
        ),
        "ssim_outside_image1": mean(
            [v.get("preservation_image1", {}).get("ssim_outside") for v in done.values()]
        ),
        "mae_outside_final": mean(
            [v.get("preservation_final", {}).get("mae_outside") for v in done.values()]
        ),
        "cost_usd_per_room": mean([v["usage"]["cost_usd"] for v in done.values()]),
        "latency_s_per_room": mean([v["usage"]["latency_s"] for v in done.values()]),
        "pipeline_time_s_per_room": mean([v.get("pipeline_time_s") for v in done.values()]),
        "setup": {
            "embedding": cfg.embedding.name,
            "generator1": f"{cfg.generation.generator1.provider}:{cfg.generation.generator1.model}",
            "generator2": f"{cfg.generation.generator2.provider}:{cfg.generation.generator2.model}",
            "gen2_base": cfg.generation.gen2_base,
            "gen2_mode": cfg.generation.gen2_mode,
            "composite": cfg.generation.composite,
            "quality": cfg.generation.generator2.quality,
        },
        "per_room": {
            k: {kk: vv for kk, vv in v.items() if kk != "reid"} for k, v in per_room.items()
        },
    }
