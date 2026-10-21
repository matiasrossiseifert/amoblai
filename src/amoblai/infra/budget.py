"""Spend ledger and budget guard (append-only JSONL, shared by all runs on a machine): every paid
call is checked against a cap before it is sent and recorded after."""

from __future__ import annotations

import fcntl
import json
import time
from pathlib import Path


class BudgetExceeded(RuntimeError):
    pass


class PaidCallsDisabled(BudgetExceeded):
    """A paid provider was requested while budget.allow_paid is false."""


class Ledger:
    """One cap over one pool of spend. The shared pool (`pool=None`) is every account without a
    cap of its own (budget.max_usd_total); an account with its own cap (budget.accounts) is a
    pool of its own, and its entries carry `"pool": <account>`."""

    def __init__(self, path: str | Path, cap_usd: float, pool: str | None = None):
        self.path = Path(path)
        self.cap = float(cap_usd)
        self.pool = pool
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def spent(self) -> float:
        return round(
            sum(
                e.get("cost_usd") or 0.0
                for e in self.entries()
                if not e.get("cached") and e.get("pool") == self.pool
            ),
            6,
        )

    def check(self, estimate_usd: float) -> None:
        spent = self.spent()
        if spent + estimate_usd > self.cap + 1e-9:
            raise BudgetExceeded(
                f"budget cap ${self.cap:.2f}{f' ({self.pool})' if self.pool else ''} would be "
                f"exceeded: spent ${spent:.4f} + next call ~${estimate_usd:.4f}. Raise "
                f"{f'budget.accounts.{self.pool}' if self.pool else 'budget.max_usd_total'} in "
                "the config."
            )

    def record(self, **entry) -> None:
        if self.pool:
            entry["pool"] = self.pool
        entry.setdefault("time", time.strftime("%Y-%m-%dT%H:%M:%S"))
        with self.path.open("a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(entry) + "\n")
            fcntl.flock(f, fcntl.LOCK_UN)


def ledger_for(budget, account: str | None = None) -> Ledger:
    """The ledger an API account spends from: its own cap if budget.accounts has one, else the
    shared budget.max_usd_total."""
    own = account is not None and account in budget.accounts
    return Ledger(
        budget.ledger,
        budget.accounts[account] if own else budget.max_usd_total,
        account if own else None,
    )


def check_spend(ledger: Ledger, estimate_usd: float, *, paid: bool, allow_paid: bool, what: str):
    """The gate before every call that may cost: a paid API is refused unless paid calls are
    allowed (budget.allow_paid), and no call may take the ledger past the cap."""
    if paid and not allow_paid:
        raise PaidCallsDisabled(
            f"{what} is a paid API (~${estimate_usd:.3f}) and budget.allow_paid is false. "
            "Paid calls need approval, then --set budget.allow_paid=true."
        )
    ledger.check(estimate_usd)
