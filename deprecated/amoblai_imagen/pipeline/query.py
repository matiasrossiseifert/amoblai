"""Pipeline de consulta (ver docs/ARQUITECTURA.md y el diagrama de la propuesta).

1. Pre-retrieval (transformación de la consulta): el generador n.º 1 amobla el
   ambiente vacío con muebles genéricos del alcance → imagen 1. Foto y texto se
   convierten en consultas del mismo dominio que el catálogo (idea tipo HyDE).
2. Detección y recorte de cada mueble del alcance; fondo blanco.
3. Retrieval: embedding del recorte + ANN con metadata filtering + umbral.
4. Post-retrieval: reranking (desactivado en la v1: se elige el top-1).
5. Generación: el generador n.º 2 reemplaza cada mueble genérico por el producto
   real, partiendo de la imagen 1 o de la foto original.
6. Salida: imagen final + lista de compra en JSON.

Cada etapa guarda sus artefactos en la carpeta de la corrida, así la app de
flujo puede mostrar todas las imágenes intermedias.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from amoblai_imagen.components import RetrievalComponents, build_retrieval_components
from amoblai_imagen.config import AppConfig, Secrets
from amoblai_imagen.data.catalog import Product
from amoblai_imagen.generation.base import EditRequest, ManualStepPendingError
from amoblai_imagen.generation.editors.manual_editor import fit_to_aspect
from amoblai_imagen.generation.geometry import boxes_mask, composite
from amoblai_imagen.generation.prompts import (
    PlacedProduct,
    generator1_prompt,
    generator2_item_prompt,
    generator2_single_prompt,
    unique_skus,
)
from amoblai_imagen.generation.service import EditorService, build_editor_service
from amoblai_imagen.indexing.preprocess import prepare_for_embedding
from amoblai_imagen.infra.budget import BudgetGuard
from amoblai_imagen.infra.images import load_image, mask_to_image, resize_max_side, thumbnail, to_rgb
from amoblai_imagen.infra.runs import RunContext
from amoblai_imagen.infra.tracing import traced
from amoblai_imagen.infra.usage import SpendLedger, UsageRecord
from amoblai_imagen.pipeline.output import build_shopping_list
from amoblai_imagen.retrieval.retriever import RetrievalResult
from amoblai_imagen.vision.crops import QueryCrop, make_crops
from amoblai_imagen.vision.detection import Detection

log = logging.getLogger(__name__)

CATEGORY_COLORS = {
    "sofa": (230, 57, 70),
    "armchair": (244, 162, 97),
    "chair": (42, 157, 143),
    "table": (38, 70, 83),
    "rug": (131, 56, 236),
}


@dataclass
class FurnishedItem:
    detection: Detection
    crop: QueryCrop
    retrieval: RetrievalResult
    product: Product | None


@dataclass
class PipelineResult:
    prompt: str
    original: Image.Image
    image1: Image.Image | None = None
    image1_source: str = "generator1"
    detections: list[Detection] = field(default_factory=list)
    items: list[FurnishedItem] = field(default_factory=list)
    gen2_base: str = "image1"
    gen2_steps: list[Image.Image] = field(default_factory=list)
    mask: np.ndarray | None = None
    final: Image.Image | None = None
    shopping_list: dict[str, Any] = field(default_factory=dict)
    usage: list[UsageRecord] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    status: str = "running"  # ok | pending_manual | no_furniture
    pending: ManualStepPendingError | None = None
    run_id: str | None = None

    @property
    def accepted(self) -> list[FurnishedItem]:
        return [it for it in self.items if it.product is not None]


def draw_detections(image: Image.Image, detections: list[Detection]) -> Image.Image:
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    for i, det in enumerate(detections):
        color = CATEGORY_COLORS.get(det.category, (255, 200, 0))
        draw.rectangle(det.box.to_int(), outline=color, width=4)
        x0, y0 = det.box.to_int()[:2]
        label = f"{i} {det.category} {det.score:.2f}"
        draw.rectangle([x0, y0, x0 + 8 * len(label), y0 + 16], fill=color)
        draw.text((x0 + 3, y0 + 2), label, fill=(255, 255, 255))
    return out


class FurnishPipeline:
    def __init__(
        self,
        cfg: AppConfig,
        comps: RetrievalComponents,
        gen1: EditorService,
        gen2: EditorService,
    ):
        self.cfg = cfg
        self.comps = comps
        self.gen1 = gen1
        self.gen2 = gen2

    @classmethod
    def from_config(cls, cfg: AppConfig, secrets: Secrets | None = None) -> FurnishPipeline:
        comps = build_retrieval_components(cfg)
        budget = BudgetGuard(
            max_calls=cfg.budget.max_calls_per_run,
            max_usd=cfg.budget.max_usd_per_run,
            max_usd_total=cfg.budget.max_usd_total,
            dry_run=cfg.budget.dry_run,
            ledger=SpendLedger(cfg.paths.spend_ledger),
        )
        gen1 = build_editor_service(cfg.generation.generator1, cfg, budget, secrets)
        gen2 = build_editor_service(cfg.generation.generator2, cfg, budget, secrets)
        return cls(cfg, comps, gen1, gen2)

    # ------------------------------------------------------------------ etapas

    @traced("furnish_pipeline")
    def run(
        self,
        room: Image.Image,
        prompt: str,
        run: RunContext | None = None,
        image1: Image.Image | None = None,
    ) -> PipelineResult:
        """Corre el pipeline completo. Si un paso manual queda pendiente, devuelve
        el resultado parcial con `status="pending_manual"` (volver a correr reanuda
        desde la caché)."""
        gcfg = self.cfg.generation
        original = resize_max_side(to_rgb(room), gcfg.working_max_side, multiple=16)
        result = PipelineResult(prompt=prompt, original=original, gen2_base=gcfg.gen2_base)
        result.run_id = run.run_id if run else None
        self._save(run, "00_original.jpg", original)
        if run:
            run.path("prompt.txt").write_text(prompt)
        try:
            self._stage_image1(result, run, image1)
            self._stage_retrieval(result, run)
            self._stage_generation(result, run)
            result.status = "ok" if result.accepted else "no_furniture"
        except ManualStepPendingError as pending:
            result.status = "pending_manual"
            result.pending = pending
            log.warning("Paso manual pendiente: %s", pending.workdir)
        result.shopping_list = build_shopping_list(
            [it.retrieval for it in result.items], self.comps.catalog, self.comps.categories
        )
        if run:
            self._save_summary(result, run)
        return result

    def _timed(self, result: PipelineResult, stage: str, start: float) -> None:
        result.timings[stage] = round(
            result.timings.get(stage, 0.0) + time.perf_counter() - start, 2
        )

    def _add_usage(
        self, result: PipelineResult, run: RunContext | None, usage: UsageRecord
    ) -> None:
        result.usage.append(usage)
        if run:
            run.add_usage(usage)

    @traced("pre_retrieval_generator1")
    def _stage_image1(
        self, result: PipelineResult, run: RunContext | None, image1: Image.Image | None
    ) -> None:
        start = time.perf_counter()
        if image1 is not None:
            result.image1, _ = fit_to_aspect(to_rgb(image1), result.original.size)
            result.image1_source = "provided"
        else:
            request = EditRequest(
                stage="generator1",
                prompt=generator1_prompt(result.prompt, self.comps.categories.scope),
                images=[result.original],
                image_labels=["ambiente_vacio"],
            )
            if run:
                run.path("01_prompt_generador1.txt").write_text(request.prompt)
            edit = self.gen1.edit(request, result.run_id)
            self._add_usage(result, run, edit.usage)
            result.image1 = edit.image
        self._save(run, "01_imagen1.jpg", result.image1)
        self._timed(result, "generator1", start)

    @traced("detection_and_retrieval")
    def _stage_retrieval(self, result: PipelineResult, run: RunContext | None) -> None:
        assert result.image1 is not None
        start = time.perf_counter()
        result.detections = self.comps.detector.detect(result.image1)
        self._timed(result, "detection", start)
        self._save(run, "02_detecciones.jpg", draw_detections(result.image1, result.detections))

        start = time.perf_counter()
        crops = make_crops(
            result.image1,
            result.detections,
            self.comps.remover,
            self.cfg.background,
            self.cfg.preprocess,
        )
        self._timed(result, "crops", start)
        start = time.perf_counter()
        retrievals = self.comps.retriever.search(crops)
        retrievals = [
            self.comps.reranker.rerank(c, r, result.prompt)
            for c, r in zip(crops, retrievals, strict=True)
        ]
        self._timed(result, "retrieval", start)
        for crop, res in zip(crops, retrievals, strict=True):
            product = self.comps.catalog.get(res.chosen_sku) if res.chosen_sku else None
            result.items.append(FurnishedItem(crop.detection, crop, res, product))
            self._save(
                run,
                f"03_recortes/{crop.index:02d}_{res.category}_crudo.jpg",
                thumbnail(crop.raw, 384),
            )
            self._save(
                run,
                f"03_recortes/{crop.index:02d}_{res.category}_consulta.jpg",
                thumbnail(crop.query, 384),
            )

    def _product_image(self, sku: str) -> Image.Image:
        img = load_image(self.comps.catalog.image_path(sku))
        return prepare_for_embedding(img, self.cfg.preprocess)

    @traced("generation_generator2")
    def _stage_generation(self, result: PipelineResult, run: RunContext | None) -> None:
        gcfg = self.cfg.generation
        accepted = result.accepted
        base = result.image1 if gcfg.gen2_base == "image1" else result.original
        assert base is not None
        if not accepted:
            result.final = result.original
            self._save(run, "06_final.jpg", result.final)
            return
        start = time.perf_counter()
        placed = [
            PlacedProduct(
                it.detection.category,
                it.detection.box,
                it.product.sku,
                it.product.name,
                it.product.type,
                it.product.size_raw,
            )
            for it in accepted
            if it.product is not None
        ]
        boxes = [p.box for p in placed]
        result.mask = boxes_mask(base.size, boxes, gcfg.mask_dilation)
        self._save(run, "05_mascara.png", mask_to_image(result.mask))
        if gcfg.gen2_mode == "single":
            request = EditRequest(
                stage="generator2",
                prompt=generator2_single_prompt(placed, base.size, gcfg.gen2_base),
                images=[base, *(self._product_image(sku) for sku in unique_skus(placed))],
                image_labels=["ambiente", *(f"producto_{sku}" for sku in unique_skus(placed))],
                mask=result.mask,
            )
            if run:
                run.path("05_prompt_generador2.txt").write_text(request.prompt)
            edit = self.gen2.edit(request, result.run_id)
            self._add_usage(result, run, edit.usage)
            final = (
                composite(base, edit.image, result.mask, gcfg.feather_px)
                if gcfg.composite
                else edit.image
            )
        else:
            current = base
            prompts = []
            for i, p in enumerate(placed):
                mask_i = boxes_mask(base.size, [p.box], gcfg.mask_dilation)
                request = EditRequest(
                    stage="generator2",
                    prompt=generator2_item_prompt(p, base.size, gcfg.gen2_base),
                    images=[current, self._product_image(p.sku)],
                    image_labels=["ambiente", f"producto_{p.sku}"],
                    mask=mask_i,
                )
                prompts.append(request.prompt)
                edit = self.gen2.edit(request, result.run_id)
                self._add_usage(result, run, edit.usage)
                current = (
                    composite(current, edit.image, mask_i, gcfg.feather_px)
                    if gcfg.composite
                    else edit.image
                )
                result.gen2_steps.append(current)
                self._save(run, f"05_pasos/{i:02d}_{p.category}_{p.sku}.jpg", current)
            if run:
                run.path("05_prompt_generador2.txt").write_text("\n\n---\n\n".join(prompts))
            final = current
        result.final = final
        self._save(run, "06_final.jpg", final)
        self._timed(result, "generator2", start)

    # --------------------------------------------------------------- guardado

    def _save(self, run: RunContext | None, rel: str, img: Image.Image) -> None:
        if run is not None:
            run.save_image(rel, img)

    def _save_summary(self, result: PipelineResult, run: RunContext) -> None:
        run.write_json("lista_compra.json", result.shopping_list)
        items = []
        for it in result.items:
            items.append(
                {
                    "index": it.crop.index,
                    "category": it.detection.category,
                    "det_label": it.detection.label,
                    "det_score": round(it.detection.score, 4),
                    "box": it.detection.box.as_list(),
                    "background_removed": it.crop.background_removed,
                    "chosen_sku": it.retrieval.chosen_sku,
                    "threshold": it.retrieval.threshold,
                    "candidates": [
                        {
                            "sku": c.sku,
                            "score": c.score,
                            "rank": c.rank,
                            "category": c.category,
                            "name": c.name,
                            "image_path": c.image_path,
                        }
                        for c in it.retrieval.candidates
                    ],
                }
            )
        summary = {
            "run_id": result.run_id,
            "status": result.status,
            "prompt": result.prompt,
            "image1_source": result.image1_source,
            "gen2_base": result.gen2_base,
            "gen2_mode": self.cfg.generation.gen2_mode,
            "working_size": list(result.original.size),
            "items": items,
            "timings_s": result.timings,
            "pending_workdir": str(result.pending.workdir) if result.pending else None,
        }
        run.write_json("resultado.json", summary)
