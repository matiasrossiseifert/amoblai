"""Servicio de edición: caché + control de presupuesto + registro de gastos.

Toda llamada a un generador pasa por acá:
1. Se calcula la clave = hash(proveedor, modelo, calidad, prompt, imágenes, máscara).
2. Si la clave está en `resultados/generaciones/<proveedor>/`, se devuelve sin pagar.
3. Si no, se estima el costo y el presupuesto autoriza (o corta) la llamada.
4. El resultado se guarda en la caché y el gasto en `resultados/gastos.jsonl`.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from amoblai_imagen.config import AppConfig, EditorConfig, Secrets
from amoblai_imagen.generation.base import EditRequest, EditResult, ImageEditor
from amoblai_imagen.generation.editors.dry_run import DryRunEditor
from amoblai_imagen.infra.budget import BudgetGuard
from amoblai_imagen.infra.cache import ArtifactCache
from amoblai_imagen.infra.images import image_digest, mask_to_image
from amoblai_imagen.infra.usage import PricingTable, SpendLedger, UsageRecord

log = logging.getLogger(__name__)


class EditorService:
    def __init__(
        self,
        editor: ImageEditor,
        cfg: EditorConfig,
        cache_root: Path,
        budget: BudgetGuard,
        ledger: SpendLedger | None = None,
    ):
        self.editor = editor
        self.cfg = cfg
        self.dry_run = isinstance(editor, DryRunEditor)
        self.cache = ArtifactCache(cache_root, editor.provider)
        self.budget = budget
        self.ledger = ledger

    def cache_key(self, request: EditRequest) -> str:
        return self.cache.key(
            {
                "provider": self.editor.provider,
                "model": self.editor.model if self.editor.provider != "manual" else "manual",
                "quality": self.cfg.quality,
                "size_policy": self.cfg.size_policy,
                "input_fidelity": self.cfg.input_fidelity,
                "stage": request.stage,
                "prompt": request.prompt,
                "images": [image_digest(img) for img in request.images],
                "mask": image_digest(mask_to_image(request.mask))
                if request.mask is not None
                else None,
            }
        )

    def edit(self, request: EditRequest, run_id: str | None = None) -> EditResult:
        request.cache_key = self.cache_key(request)
        if not self.dry_run:
            cached = self.cache.get_image(request.cache_key, "image.png")
            meta = self.cache.get_json(request.cache_key)
            if cached is not None and meta is not None:
                usage = UsageRecord.model_validate(meta["usage"])
                usage.cached = True
                usage.cost_usd = 0.0
                usage.latency_s = 0.0
                log.info("%s: resultado en caché (%s)", request.stage, request.cache_key[:10])
                return EditResult(
                    cached, usage, meta | {"cached": True, "cache_key": request.cache_key}
                )
            self.budget.authorize(self.editor.estimate_usd(request), request.stage)

        start = time.perf_counter()
        result = self.editor.edit(request)
        if not result.usage.latency_s:
            result.usage.latency_s = round(time.perf_counter() - start, 2)
        if self.dry_run:
            return result

        meta = {
            **result.meta,
            "provider": self.editor.provider,
            "model": result.usage.model,
            "stage": request.stage,
            "prompt": request.prompt,
            "cache_key": request.cache_key,
            "usage": result.usage.model_dump(mode="json"),
        }
        self.cache.put_image(request.cache_key, result.image, "image.png")
        self.cache.put_json(request.cache_key, meta)
        if not result.usage.manual:
            self.budget.record(result.usage.cost_usd)
            if self.ledger is not None:
                self.ledger.append(result.usage, run_id)
        result.meta = meta
        return result


def build_editor(
    cfg: EditorConfig, app_cfg: AppConfig, secrets: Secrets, pricing: PricingTable
) -> ImageEditor:
    if cfg.provider == "manual":
        from amoblai_imagen.generation.editors.manual_editor import ManualImageEditor

        return ManualImageEditor(cfg, Path(app_cfg.paths.generations_dir) / "manual")
    if cfg.provider == "openai":
        from amoblai_imagen.generation.editors.openai_editor import OpenAIImageEditor

        if not secrets.openai_api_key:
            raise RuntimeError("Falta OPENAI_API_KEY en .env")
        return OpenAIImageEditor(cfg, secrets.openai_api_key, pricing)
    if cfg.provider == "gemini":
        from amoblai_imagen.generation.editors.gemini_editor import GeminiImageEditor

        if not secrets.gemini_key:
            raise RuntimeError("Falta GEMINI_API_KEY (o GOOGLE_API_KEY) en .env")
        return GeminiImageEditor(cfg, secrets.gemini_key, pricing)
    if cfg.provider == "dry_run":
        return DryRunEditor()
    raise ValueError(cfg.provider)  # pragma: no cover


def build_editor_service(
    cfg: EditorConfig, app_cfg: AppConfig, budget: BudgetGuard, secrets: Secrets | None = None
) -> EditorService:
    secrets = secrets or Secrets()
    pricing = PricingTable.load(app_cfg.paths.pricing_file)
    if app_cfg.budget.dry_run and cfg.provider != "dry_run":
        # Dry-run global: se simula el proveedor configurado para estimar su costo.
        simulated = None
        if cfg.provider in ("openai", "gemini"):
            simulated = _pricing_only_editor(cfg, pricing)
        editor: ImageEditor = DryRunEditor(simulated)
    else:
        editor = build_editor(cfg, app_cfg, secrets, pricing)
    return EditorService(
        editor,
        cfg,
        app_cfg.paths.generations_dir,
        budget,
        SpendLedger(app_cfg.paths.spend_ledger),
    )


class _PricingOnly:
    """Proveedor simulado (sin cliente de API) para estimar costos en dry-run."""

    def __init__(self, provider: str, cfg: EditorConfig, pricing: PricingTable):
        self.provider = provider
        self.model = cfg.model
        self.cfg = cfg
        self.pricing = pricing

    def estimate_usd(self, request: EditRequest) -> float:
        return self.pricing.estimate(
            self.provider, self.model, self.cfg.quality, request.base.size, len(request.images)
        )

    def edit(self, request: EditRequest) -> EditResult:  # pragma: no cover - nunca se llama
        raise NotImplementedError


def _pricing_only_editor(cfg: EditorConfig, pricing: PricingTable) -> ImageEditor:
    return _PricingOnly(cfg.provider, cfg, pricing)
