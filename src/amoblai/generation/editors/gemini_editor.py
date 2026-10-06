"""Editor de imagen con la API de Gemini (modelos de imagen de Google).

Gemini no recibe máscara: la zona a editar se describe en el prompt (región en
porcentajes). Si se necesita garantizar que el resto no cambie, activar
`generation.composite`.
"""

from __future__ import annotations

import logging
import time

from amoblai.config import EditorConfig
from amoblai.generation.base import EditRequest, EditResult
from amoblai.generation.geometry import FitTransform, closest_aspect
from amoblai.infra.images import from_bytes, resize_max_side
from amoblai.infra.usage import PricingTable, UsageRecord

log = logging.getLogger(__name__)


def _aspect_size(aspect: str, long_side: int) -> tuple[int, int]:
    w, h = (int(v) for v in aspect.split(":"))
    if w >= h:
        return long_side, round(long_side * h / w)
    return round(long_side * w / h), long_side


class GeminiImageEditor:
    provider = "gemini"

    def __init__(self, cfg: EditorConfig, api_key: str, pricing: PricingTable):
        from google import genai

        self.cfg = cfg
        self.model = cfg.model
        self.pricing = pricing
        self.client = genai.Client(api_key=api_key)

    def estimate_usd(self, request: EditRequest) -> float:
        return self.pricing.estimate(
            self.provider, self.model, self.cfg.quality, (1024, 1024), len(request.images)
        )

    def edit(self, request: EditRequest) -> EditResult:
        from google.genai import types

        w, h = request.base.size
        aspect = closest_aspect(w, h)
        fit = FitTransform((w, h), _aspect_size(aspect, max(w, h)))
        refs = [resize_max_side(img, self.cfg.reference_max_side) for img in request.images[1:]]
        contents = [request.prompt, fit.apply(request.base), *refs]
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=aspect)
        )
        start = time.perf_counter()
        response = self.client.models.generate_content(
            model=self.model, contents=contents, config=config
        )
        latency = time.perf_counter() - start

        data = None
        for part in response.candidates[0].content.parts or []:
            if part.inline_data is not None and part.inline_data.data:
                data = part.inline_data.data
                break
        if data is None:
            raise RuntimeError(
                f"Gemini no devolvió imagen (finish_reason={response.candidates[0].finish_reason})"
            )
        image = fit.invert(from_bytes(data).convert("RGB"))

        um = response.usage_metadata
        record = UsageRecord(
            stage=request.stage,
            provider=self.provider,
            model=self.model,
            images_out=1,
            latency_s=round(latency, 2),
            # Gemini cobra igual texto e imagen de entrada: todo va como input de texto.
            input_text_tokens=int(getattr(um, "prompt_token_count", 0) or 0),
            output_image_tokens=int(getattr(um, "candidates_token_count", 0) or 0),
        )
        record.cost_usd = round(self.pricing.cost(record), 6)
        meta = {"aspect_ratio": aspect, "mask_ignored": request.mask is not None}
        return EditResult(image=image, usage=record, meta=meta)
