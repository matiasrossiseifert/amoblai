"""Editor de imagen con la API de OpenAI (familia gpt-image, endpoint images.edit)."""

from __future__ import annotations

import base64
import logging
import time

from amoblai.config import EditorConfig
from amoblai.generation.base import EditRequest, EditResult
from amoblai.generation.geometry import FitTransform, closest_fixed_size, free_size, openai_mask
from amoblai.infra.images import (
    from_bytes,
    image_to_mask,
    mask_to_image,
    resize_max_side,
    to_png_bytes,
)
from amoblai.infra.usage import PricingTable, UsageRecord

log = logging.getLogger(__name__)


class OpenAIImageEditor:
    provider = "openai"

    def __init__(self, cfg: EditorConfig, api_key: str, pricing: PricingTable):
        from openai import OpenAI

        self.cfg = cfg
        self.model = cfg.model
        self.pricing = pricing
        self.client = OpenAI(api_key=api_key, timeout=cfg.timeout_s, max_retries=2)

    def target_size(self, size: tuple[int, int]) -> tuple[int, int]:
        w, h = size
        if self.cfg.size_policy == "fixed":
            return closest_fixed_size(w, h)
        return free_size(w, h, max_side=max(w, h))

    def estimate_usd(self, request: EditRequest) -> float:
        return self.pricing.estimate(
            self.provider,
            self.model,
            self.cfg.quality,
            self.target_size(request.base.size),
            len(request.images),
        )

    def edit(self, request: EditRequest) -> EditResult:
        fit = FitTransform(request.base.size, self.target_size(request.base.size))
        files = [("image_1.png", to_png_bytes(fit.apply(request.base)), "image/png")]
        for i, ref in enumerate(request.images[1:], start=2):
            ref = resize_max_side(ref, self.cfg.reference_max_side)
            files.append((f"image_{i}.png", to_png_bytes(ref), "image/png"))
        kwargs: dict = {
            "model": self.model,
            "image": files,
            "prompt": request.prompt,
            "size": f"{fit.target[0]}x{fit.target[1]}",
            "quality": self.cfg.quality,
            "output_format": "png",
            "n": 1,
        }
        if request.mask is not None:
            fitted = image_to_mask(fit.apply(mask_to_image(request.mask)))
            kwargs["mask"] = ("mask.png", to_png_bytes(openai_mask(fitted)), "image/png")
        if self.cfg.input_fidelity:
            kwargs["input_fidelity"] = self.cfg.input_fidelity

        start = time.perf_counter()
        response = self.client.images.edit(**kwargs)
        latency = time.perf_counter() - start
        out = from_bytes(base64.b64decode(response.data[0].b64_json)).convert("RGB")
        image = fit.invert(out)

        usage = self._usage(request.stage, response, latency)
        return EditResult(
            image=image, usage=usage, meta={"size": kwargs["size"], "quality": self.cfg.quality}
        )

    def _usage(self, stage: str, response, latency: float) -> UsageRecord:
        u = response.usage
        record = UsageRecord(
            stage=stage,
            provider=self.provider,
            model=self.model,
            images_out=1,
            latency_s=round(latency, 2),
        )
        if u is not None:
            in_det = getattr(u, "input_tokens_details", None)
            out_det = getattr(u, "output_tokens_details", None)
            record.input_text_tokens = int(getattr(in_det, "text_tokens", 0) or 0)
            record.input_image_tokens = int(getattr(in_det, "image_tokens", 0) or 0)
            if out_det is not None:
                record.output_image_tokens = int(getattr(out_det, "image_tokens", 0) or 0)
                record.output_text_tokens = int(getattr(out_det, "text_tokens", 0) or 0)
            else:
                record.output_image_tokens = int(u.output_tokens or 0)
        record.cost_usd = round(self.pricing.cost(record), 6)
        return record
