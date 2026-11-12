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


# What each paid step is for, in the spend report (longest prefix wins).
PURPOSES = {
    "furnish.plan": "El flujo: plan (lee la foto y el pedido, escribe las consultas)",
    "furnish.choose": "El flujo: elección de la lista",
    "furnish.scene": "El flujo: prompt de la imagen escrito por el LLM (configuración anterior)",
    "furnish.generate": "El flujo: imagen del ambiente amoblado",
    "catalog.describe": "Catálogo: descripciones de los productos de ABO",
    "rag.embed": "Índice: embeddings por API",
    "eval.rerank": "Evaluación: un VLM ordena el top-10 (ground truth de IKEA)",
    "eval.juez_listas": "Evaluación de punta a punta: juez que compara dos listas",
    "eval.juez_fidelidad": "Evaluación del generador: faithfulness",
    "eval.juez_pedidos": "Evaluación del generador: answer relevance",
    "eval.replica": "Réplica de un ambiente real (ubicación de los muebles)",
}


def purpose(step: str) -> str:
    for prefix in sorted(PURPOSES, key=len, reverse=True):
        if step.startswith(prefix):
            return PURPOSES[prefix]
    return step


def spend_report(path: str | Path, caps: dict[str, float]) -> str:
    """The ledger as a Markdown report: the total per account against its cap, per purpose, and
    per day and purpose (what to quote in a presentation or an expense report)."""
    rows = [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]

    def usd(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    def account(r: dict) -> str:
        return r.get("pool") or r.get("provider") or "?"

    md = [
        "# Gastos del proyecto",
        "",
        f"Generado desde `{path}` (una línea por llamada paga, con su fecha, paso, modelo y "
        "costo) con `uv run amoblai gastos --md`. No lo edites a mano: volvé a generarlo.",
        "",
        "## Por cuenta",
        "",
        "| Cuenta | Llamadas | Gastado (US$) | Tope en la config (US$) |",
        "|---|---|---|---|",
    ]
    accounts = sorted({account(r) for r in rows} | set(caps))
    for a in accounts:
        mine = [r for r in rows if account(r) == a]
        cap = usd(caps[a]) if a in caps else "—"
        md.append(f"| {a} | {len(mine)} | {usd(sum(r['cost_usd'] for r in mine))} | {cap} |")
    md += [f"| **total** | {len(rows)} | **{usd(sum(r['cost_usd'] for r in rows))}** | |", ""]

    md += [
        "## Por uso",
        "",
        "| Para qué | Cuenta | Modelo | Llamadas | US$ | US$ por llamada |",
        "|---|---|---|---|---|---|",
    ]
    by: dict[tuple, list[float]] = {}
    for r in rows:
        by.setdefault((purpose(r["step"]), account(r), r.get("model") or ""), []).append(
            r["cost_usd"]
        )
    for (what, a, model), costs in sorted(by.items(), key=lambda kv: -sum(kv[1])):
        mean = sum(costs) / len(costs)
        md.append(
            f"| {what} | {a} | {model} | {len(costs)} | {usd(sum(costs))} | "
            f"{f'{mean:.3f}'.replace('.', ',')} |"
        )
    md += [
        "",
        "## Por día",
        "",
        "| Día | Para qué | Cuenta | Llamadas | US$ |",
        "|---|---|---|---|---|",
    ]
    daily: dict[tuple, list[float]] = {}
    for r in rows:
        daily.setdefault((r["time"][:10], purpose(r["step"]), account(r)), []).append(r["cost_usd"])
    day_total: dict[str, float] = {}
    for (day, what, a), costs in sorted(daily.items()):
        md.append(f"| {day} | {what} | {a} | {len(costs)} | {usd(sum(costs))} |")
        day_total[day] = day_total.get(day, 0.0) + sum(costs)
    md += ["", "| Día | Total (US$) |", "|---|---|"]
    md += [f"| {day} | {usd(v)} |" for day, v in sorted(day_total.items())]
    md += [
        "",
        "## Lo que no está en el registro",
        "",
        "- El trabajo hecho con subagentes de Claude Code (las descripciones de los productos de "
        "IKEA, las consultas de evaluación, los jueces de relevancia graduada): va por la "
        "suscripción, no por la API.",
        "- Una imagen de fal del 2026-11-11 (US$0,08) que se pagó y no se guardó porque se llenó "
        "el disco.",
        "- Los modelos locales (embeddings, SigLIP 2, detectores, rerankers): corren en CPU, "
        "gratis.",
        "",
    ]
    return "\n".join(md)
