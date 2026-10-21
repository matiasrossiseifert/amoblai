"""Registro de uso (tokens, latencia) y cálculo de costo en USD.

Los precios viven en `configs/pricing.yaml` y se aplican a los tokens del campo
`usage` que devuelve cada API. Antes de llamar, `estimate` da una cota para el
control de presupuesto.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class UsageRecord(BaseModel):
    stage: str
    provider: str
    model: str
    input_text_tokens: int = 0
    input_image_tokens: int = 0
    output_text_tokens: int = 0
    output_image_tokens: int = 0
    images_out: int = 0
    latency_s: float = 0.0
    cost_usd: float = 0.0
    cached: bool = False
    dry_run: bool = False
    manual: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    extra: dict[str, Any] = {}

    @property
    def total_tokens(self) -> int:
        return (
            self.input_text_tokens
            + self.input_image_tokens
            + self.output_text_tokens
            + self.output_image_tokens
        )


class ModelPrice(BaseModel):
    """USD por millón de tokens."""

    text_input: float = 0.0
    image_input: float = 0.0
    text_output: float | None = None  # si falta, se cobra como image_output (cota superior)
    image_output: float = 0.0
    # Parámetros para estimar antes de la llamada.
    est_output_tokens_per_mpx: dict[str, float] = {}
    est_input_tokens_per_image: float = 1500.0
    est_prompt_tokens: float = 400.0


class PricingTable:
    def __init__(self, prices: dict[str, dict[str, ModelPrice]], batch_discount: float = 0.5):
        self.prices = prices
        self.batch_discount = batch_discount

    @classmethod
    def load(cls, path: Path) -> PricingTable:
        data = yaml.safe_load(Path(path).read_text())
        prices = {
            provider: {model: ModelPrice.model_validate(spec) for model, spec in models.items()}
            for provider, models in data["providers"].items()
        }
        return cls(prices, data.get("batch_discount", 0.5))

    def price(self, provider: str, model: str) -> ModelPrice | None:
        return self.prices.get(provider, {}).get(model)

    def cost(self, record: UsageRecord, batch: bool = False) -> float:
        p = self.price(record.provider, record.model)
        if p is None:
            return 0.0
        text_out = p.text_output if p.text_output is not None else p.image_output
        usd = (
            record.input_text_tokens * p.text_input
            + record.input_image_tokens * p.image_input
            + record.output_text_tokens * text_out
            + record.output_image_tokens * p.image_output
        ) / 1e6
        return usd * (self.batch_discount if batch else 1.0)

    def estimate(
        self, provider: str, model: str, quality: str, size: tuple[int, int], n_input_images: int
    ) -> float:
        """Cota del costo de una edición, para autorizar la llamada antes de hacerla."""
        p = self.price(provider, model)
        if p is None:
            return 0.0
        mpx = size[0] * size[1] / 1e6
        out_tokens = p.est_output_tokens_per_mpx.get(quality) or max(
            p.est_output_tokens_per_mpx.values(), default=4000.0
        )
        return (
            p.est_prompt_tokens * p.text_input
            + n_input_images * p.est_input_tokens_per_image * p.image_input
            + out_tokens * mpx * p.image_output
        ) / 1e6


def summarize_usage(records: list[UsageRecord]) -> dict[str, Any]:
    paid = [r for r in records if not r.cached and not r.dry_run]
    return {
        "api_calls": sum(1 for r in paid if not r.manual),
        "manual_steps": sum(1 for r in records if r.manual and not r.cached),
        "cached_calls": sum(1 for r in records if r.cached),
        "cost_usd": round(sum(r.cost_usd for r in paid), 4),
        "estimated_cost_usd_dry_run": round(sum(r.cost_usd for r in records if r.dry_run), 4),
        "tokens": sum(r.total_tokens for r in paid),
        "latency_s": round(sum(r.latency_s for r in records), 2),
        "by_stage": {
            stage: {
                "cost_usd": round(sum(r.cost_usd for r in paid if r.stage == stage), 4),
                "latency_s": round(sum(r.latency_s for r in records if r.stage == stage), 2),
            }
            for stage in sorted({r.stage for r in records})
        },
    }


class SpendLedger:
    """Registro append-only de cada llamada paga (resultados/gastos.jsonl)."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, record: UsageRecord, run_id: str | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = record.model_dump(mode="json") | {"run_id": run_id}
        with self.path.open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def total_usd(self) -> float:
        if not self.path.exists():
            return 0.0
        total = 0.0
        for line in self.path.read_text().splitlines():
            if line.strip():
                total += float(json.loads(line).get("cost_usd", 0.0))
        return total
