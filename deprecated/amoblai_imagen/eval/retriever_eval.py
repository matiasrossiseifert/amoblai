"""Evaluación del retriever sobre las fotos de ambientes de IKEA (livings y comedores).

Para cada ambiente: detectar los muebles del alcance → recortar → buscar. Las
anotaciones del dataset dicen qué productos aparecen en cada ambiente, pero no
dónde, así que la métrica es permisiva:

- **Relevantes de un recorte** = SKUs anotados en ese ambiente de la *misma
  categoría* que la detección. Un recorte cuya categoría no tiene ningún SKU
  anotado en el ambiente no tiene respuesta posible: se cuenta aparte.
- **Variante literal** = cualquier SKU anotado del ambiente dentro del alcance
  (sin mirar la categoría). Infla los resultados sin filtro por categoría y se
  reporta solo como referencia.
- **Recall por ítem** = para cada SKU anotado del alcance, si algún recorte del
  ambiente lo recuperó en el top-k. Castiga también lo que el detector no ve.

La versión estricta (recorte → SKU exacto, etiquetado a mano) está en strict_eval.py.
"""

from __future__ import annotations

import hashlib
import io
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml
from rich.progress import track

from amoblai_imagen.categories import OTHER
from amoblai_imagen.components import RetrievalComponents, build_retrieval_components
from amoblai_imagen.config import AppConfig
from amoblai_imagen.data.ikea import IkeaDataset, RoomScene
from amoblai_imagen.eval.metrics import (
    best_f1_threshold,
    bootstrap_ci,
    first_relevant_rank,
    hit_at_k,
    random_hit_at_k,
    random_mrr,
    reciprocal_rank,
)
from amoblai_imagen.indexing.indexer import collection_name, threshold_key
from amoblai_imagen.infra.images import load_image, thumbnail, to_rgb
from amoblai_imagen.infra.runs import RunContext
from amoblai_imagen.vision.crops import make_crops

log = logging.getLogger(__name__)


def eval_rooms(cfg: AppConfig, dataset: IkeaDataset, comps: RetrievalComponents) -> list[RoomScene]:
    """Ambientes de los tipos configurados que tienen al menos un SKU anotado del alcance."""
    scope = set(comps.categories.scope)
    rooms = [
        r
        for r in dataset.rooms_of_type(cfg.dataset.eval_room_types)
        if any(s in comps.catalog and comps.catalog.get(s).category in scope for s in r.skus)
    ]
    rooms.sort(key=lambda r: r.room_id)
    return rooms[: cfg.eval.max_rooms] if cfg.eval.max_rooms else rooms


def _indexed_counts(comps: RetrievalComponents) -> tuple[Counter[str], int]:
    """SKUs con imagen por categoría y en total (el universo del ranking aleatorio)."""
    products = [p for p in comps.catalog.products.values() if p.image_paths]
    if comps.config.index.scope_only:
        products = [p for p in products if p.category != OTHER]
    return Counter(p.category for p in products), len(products)


def run_retriever_eval(
    cfg: AppConfig,
    run: RunContext,
    comps: RetrievalComponents | None = None,
    calibrate: bool = False,
) -> dict[str, Any]:
    comps = comps or build_retrieval_components(cfg, use_threshold=False)
    comps.retriever.threshold = None  # para evaluar se mira el ranking completo
    dataset = IkeaDataset.load(cfg.paths.raw_dir)
    rooms = eval_rooms(cfg, dataset, comps)
    per_category, total_items = _indexed_counts(comps)
    k_max = max(cfg.eval.ks)
    records: list[dict[str, Any]] = []
    room_items: list[dict[str, Any]] = []

    for room in track(rooms, description="Evaluando retriever"):
        image = load_image(cfg.paths.raw_dir / room.path)
        detections = comps.detector.detect(image)
        crops = make_crops(image, detections, comps.remover, cfg.background, cfg.preprocess)
        results = comps.retriever.search(crops)
        gt_scope = {
            s: comps.catalog.get(s).category
            for s in room.skus
            if s in comps.catalog and comps.catalog.get(s).category in comps.categories.scope
        }
        rankings: list[tuple[str, list[str]]] = []
        for crop, res in zip(crops, results, strict=True):
            ranked = res.ranked_skus()[:k_max]
            rankings.append((res.category, ranked))
            relevant_same = sorted(s for s, c in gt_scope.items() if c == res.category)
            n_universe = (
                per_category[res.category] if cfg.retrieval.category_filter else total_items
            )
            crop_rel = (
                save_shared_crop(crop.query, cfg.paths.results_dir) if cfg.eval.save_crops else None
            )
            records.append(
                {
                    "room_id": room.room_id,
                    "room_type": room.room_type,
                    "crop_index": crop.index,
                    "category": res.category,
                    "det_label": crop.detection.label,
                    "det_score": round(crop.detection.score, 4),
                    "box": crop.detection.box.as_list(),
                    "background_removed": crop.background_removed,
                    "ranked_skus": ranked,
                    "scores": [c.score for c in res.candidates][:k_max],
                    "candidate_categories": [c.category for c in res.candidates][:k_max],
                    "relevant": relevant_same,
                    "relevant_any": sorted(gt_scope),
                    "answerable": bool(relevant_same),
                    "rank": first_relevant_rank(ranked, relevant_same),
                    "rank_any": first_relevant_rank(ranked, gt_scope),
                    "n_universe": n_universe,
                    "crop_path": crop_rel,
                }
            )
        for sku, cat in gt_scope.items():
            ranks = [r.index(sku) + 1 for c, r in rankings if c == cat and sku in r]
            room_items.append(
                {
                    "room_id": room.room_id,
                    "sku": sku,
                    "category": cat,
                    "best_rank": min(ranks, default=None),
                }
            )

    for row in records:
        run.append_jsonl("recortes.jsonl", row)
    for row in room_items:
        run.append_jsonl("items.jsonl", row)
    metrics = compute_retriever_metrics(records, room_items, cfg)
    metrics["rooms"] = len(rooms)
    metrics["collection"] = collection_name(cfg)
    metrics["threshold_key"] = threshold_key(cfg)
    metrics["setup"] = {
        "embedding": cfg.embedding.name,
        "background": cfg.background.method,
        "category_filter": cfg.retrieval.category_filter,
        "detector": cfg.detection.provider,
    }
    if calibrate and "threshold_calibration" in metrics:
        cal = metrics["threshold_calibration"]
        write_threshold(cfg.paths.thresholds_file, metrics["threshold_key"], cal, run.run_id)
    return metrics


def save_shared_crop(image, results_dir: Path) -> str:
    """Guarda la miniatura del recorte en un almacén compartido por contenido.

    Los recortes son iguales entre corridas con el mismo detector y el mismo
    método de fondo (no dependen del embedder ni del filtro): así no se repiten
    en cada corrida de la ablación. Devuelve la ruta relativa a `results_dir`.
    """
    buf = io.BytesIO()
    to_rgb(thumbnail(image, 224)).save(buf, format="JPEG", quality=85, optimize=True)
    data = buf.getvalue()
    rel = f"recortes/{hashlib.sha256(data).hexdigest()[:20]}.jpg"
    path = Path(results_dir) / rel
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return rel


def compute_retriever_metrics(
    records: list[dict[str, Any]], room_items: list[dict[str, Any]], cfg: AppConfig
) -> dict[str, Any]:
    ks = cfg.eval.ks
    k_max = max(ks)
    answerable = [r for r in records if r["answerable"]]
    groups = [r["room_id"] for r in answerable]

    def block(rows: list[dict[str, Any]], rank_key: str = "rank") -> dict[str, Any]:
        out: dict[str, Any] = {"n": len(rows)}
        if not rows:
            return out
        grp = [r["room_id"] for r in rows]
        for k in ks:
            vals = [hit_at_k(r[rank_key], k) for r in rows]
            out[f"hit@{k}"] = round(sum(vals) / len(vals), 4)
            out[f"hit@{k}_ci95"] = [
                round(v, 4)
                for v in bootstrap_ci(vals, grp, cfg.eval.bootstrap_samples, cfg.eval.seed)
            ]
        rr = [reciprocal_rank(r[rank_key], k_max) for r in rows]
        out[f"mrr@{k_max}"] = round(sum(rr) / len(rr), 4)
        out[f"mrr@{k_max}_ci95"] = [
            round(v, 4) for v in bootstrap_ci(rr, grp, cfg.eval.bootstrap_samples, cfg.eval.seed)
        ]
        return out

    metrics: dict[str, Any] = {
        "crops_total": len(records),
        "crops_answerable": len(answerable),
        "crops_unanswerable": len(records) - len(answerable),
        "crops_per_category": dict(Counter(r["category"] for r in records)),
        "retrieval": block(answerable),
        "retrieval_literal": block([r for r in records if r["relevant_any"]], rank_key="rank_any"),
        "per_category": {
            cat: block([r for r in answerable if r["category"] == cat])
            for cat in sorted({r["category"] for r in answerable})
        },
    }
    if answerable:
        metrics["random_baseline"] = {
            **{
                f"hit@{k}": round(
                    sum(random_hit_at_k(r["n_universe"], len(r["relevant"]), k) for r in answerable)
                    / len(answerable),
                    4,
                )
                for k in ks
            },
            f"mrr@{k_max}": round(
                sum(random_mrr(r["n_universe"], len(r["relevant"]), k_max) for r in answerable)
                / len(answerable),
                4,
            ),
        }
    if room_items:
        item_groups = [i["room_id"] for i in room_items]
        item_block: dict[str, Any] = {"n": len(room_items)}
        for k in ks:
            vals = [hit_at_k(i["best_rank"], k) for i in room_items]
            item_block[f"recall@{k}"] = round(sum(vals) / len(vals), 4)
            item_block[f"recall@{k}_ci95"] = [
                round(v, 4)
                for v in bootstrap_ci(vals, item_groups, cfg.eval.bootstrap_samples, cfg.eval.seed)
            ]
        by_cat: dict[str, list[float]] = defaultdict(list)
        for i in room_items:
            by_cat[i["category"]].append(hit_at_k(i["best_rank"], k_max))
        item_block[f"recall@{k_max}_per_category"] = {
            c: round(sum(v) / len(v), 4) for c, v in sorted(by_cat.items())
        }
        metrics["items"] = item_block
    # Calibración del umbral: aceptar el top-1 ⇔ es correcto. Los recortes sin
    # respuesta posible (falsos positivos del detector o muebles no anotados)
    # cuentan como negativos: idealmente el umbral los descarta.
    scored = [r for r in records if r["scores"]]
    if scored:
        cal = best_f1_threshold([r["scores"][0] for r in scored], [r["rank"] == 1 for r in scored])
        correct = [r["scores"][0] for r in scored if r["rank"] == 1]
        wrong = [r["scores"][0] for r in scored if r["rank"] != 1]
        cal["mean_score_correct"] = round(sum(correct) / len(correct), 4) if correct else None
        cal["mean_score_wrong"] = round(sum(wrong) / len(wrong), 4) if wrong else None
        metrics["threshold_calibration"] = {
            k: (round(v, 4) if isinstance(v, float) else v) for k, v in cal.items()
        }
    metrics["groups"] = len(set(groups))
    return metrics


def write_threshold(path: Path, collection: str, calibration: dict[str, Any], run_id: str) -> None:
    path = Path(path)
    data = (yaml.safe_load(path.read_text()) or {}) if path.exists() else {}
    data[collection] = {
        "threshold": float(calibration["threshold"]),
        "f1": float(calibration["f1"]),
        "precision": float(calibration["precision"]),
        "recall": float(calibration["recall"]),
        "run_id": run_id,
        "method": "max F1 (top-1 correcto vs. score) sobre ambientes IKEA",
    }
    header = (
        "# Umbrales de similitud calibrados por colección (modelo + preprocesamiento),\n"
        "# método de fondo de las consultas y filtro por categoría.\n"
        "# Los escribe `amoblai eval retriever --calibrate`; editar a mano solo para fijar uno.\n"
    )
    path.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=True))
    log.info("Umbral %.4f guardado para %s en %s", calibration["threshold"], collection, path)
