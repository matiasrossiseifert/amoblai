"""Control de costos: dry-run, tope de llamadas y tope en USD (por corrida y acumulado)."""

from __future__ import annotations

from dataclasses import dataclass

from amoblai_imagen.infra.usage import SpendLedger


class BudgetExceededError(RuntimeError):
    pass


@dataclass
class BudgetGuard:
    max_calls: int | None = None
    max_usd: float | None = None
    max_usd_total: float | None = None
    dry_run: bool = False
    ledger: SpendLedger | None = None
    calls: int = 0
    spent_usd: float = 0.0

    def authorize(self, estimated_usd: float, what: str) -> None:
        """Lanza `BudgetExceededError` si la llamada superaría algún tope."""
        if self.dry_run:
            return
        if self.max_calls is not None and self.calls + 1 > self.max_calls:
            raise BudgetExceededError(
                f"{what}: se alcanzó el tope de {self.max_calls} llamadas por corrida"
            )
        if self.max_usd is not None and self.spent_usd + estimated_usd > self.max_usd:
            raise BudgetExceededError(
                f"{what}: gastado {self.spent_usd:.3f} + estimado {estimated_usd:.3f} USD "
                f"supera el tope por corrida de {self.max_usd:.2f} USD"
            )
        if self.max_usd_total is not None and self.ledger is not None:
            total = self.ledger.total_usd()
            if total + estimated_usd > self.max_usd_total:
                raise BudgetExceededError(
                    f"{what}: el acumulado ({total:.2f} USD) superaría el tope total de "
                    f"{self.max_usd_total:.2f} USD (resultados/gastos.jsonl)"
                )

    def record(self, cost_usd: float) -> None:
        self.calls += 1
        self.spent_usd += cost_usd
