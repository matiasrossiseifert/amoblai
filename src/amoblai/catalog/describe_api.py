"""Descriptions written by the API, for a catalog that comes without them (ABO, catalog/abo.py).

IKEA's 862 descriptions were written by Claude Code subagents (catalog/descriptions.py). For a
new catalog this does the same through the API: the same eight lines and rules
(prompts/describe_products_api_v1.md, a copy of describe_product_v3 for several products a
call), the same model (Claude Opus 5.5), and the same validation (`check_text`). Besides the
text, per product: its kind (the listing's is a guess) and whether it belongs in the catalog.

Each call's answer is cached by its content (`datos/cache/describir_api/`): running it again
pays only for what is missing. Writes, next to each other: the descriptions (JSON lines, what
the `written` describer reads), the kinds ({id: kind}) and the excluded products with why.
"""

from __future__ import annotations

import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from amoblai.catalog.descriptions import check_text
from amoblai.catalog.kinds import KINDS, kinds_text
from amoblai.config import Config
from amoblai.furnish.llm import image_block, text_block
from amoblai.furnish.steps import ask
from amoblai.prompts import load_prompt

log = logging.getLogger(__name__)

PROMPT = "describe_products_api_v1.md"


def _size(d: dict | None) -> str:
    d = d or {}
    parts = [
        f"{d[k]:.0f} cm {n}"
        for k, n in (("width", "wide"), ("depth", "deep"), ("height", "high"))
        if d.get(k)
    ]
    return ", ".join(parts) or "size unknown"


def _batch(cfg: Config, llm: dict, items: list[dict], cache: Path) -> dict:
    tmpl = load_prompt(PROMPT, cfg.root)
    lines = [
        f'image {n}. id {it["id"]}: "{it["name"][:150]}", {_size(it.get("dimensions_cm"))}'
        for n, it in enumerate(items, 1)
    ]
    text = tmpl.fill(n=len(items), products="\n".join(lines), kinds=kinds_text())
    key = {"llm": llm, "prompt": tmpl.version, "text": text}
    f = cache / f"{hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]}.json"
    if f.exists():
        return json.loads(f.read_text())
    content = [image_block(cfg.path(it["photos"][0]), 512) for it in items]  # IKEA's are 500 px
    a, data = ask(cfg, "catalog.describe", [*content, text_block(text)], llm)
    out = {"products": data.get("products") or [], "model": a.model, "cost_usd": a.cost_usd}
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(out, ensure_ascii=False))
    return out


def describe(
    cfg: Config,
    items: list[dict],
    out_dir: Path,
    llm: dict,
    per_call: int = 10,
    workers: int = 6,
) -> dict:
    """Describe `items` (catalog records) into `out_dir`: descripciones.jsonl, kinds.yaml,
    excluidos.yaml. Returns counts and the cost."""
    cache = Path(cfg.cache_dir) / "describir_api"
    batches = [items[i : i + per_call] for i in range(0, len(items), per_call)]
    with ThreadPoolExecutor(workers) as pool:
        answers = list(pool.map(lambda b: _batch(cfg, llm, b, cache), batches))
    texts, kinds, excluded, bad = {}, {}, {}, {}
    model = next((a["model"] for a in answers if a.get("model")), llm.get("model"))
    for batch, ans in zip(batches, answers, strict=True):
        got = {str(p.get("id")): p for p in ans["products"]}
        for it in batch:
            p = got.get(it["id"])
            if p is None:
                bad[it["id"]] = "the answer left it out"
                continue
            errors, _ = check_text(p.get("text", ""), it["name"])
            kind = p.get("kind")
            if kind not in KINDS and KINDS.get(it.get("kind", "")) == kind:
                kind = it["kind"]  # it answered the group ("table"): the listing's kind, if in it
            if kind not in KINDS:
                errors.append(f"kind {kind!r} not in kinds.py")
            if not p.get("in_scope", True):
                excluded[it["id"]] = {"motivo": "fuera de alcance según el describer", "kind": kind}
            elif errors:
                bad[it["id"]] = "; ".join(errors)
            else:
                texts[it["id"]] = p["text"].strip() + "\n"
                kinds[it["id"]] = kind
    out_dir.mkdir(parents=True, exist_ok=True)
    tmpl = load_prompt(PROMPT, cfg.root)
    (out_dir / "descripciones.jsonl").write_text(
        "".join(
            json.dumps({"id": i, "text": t, "by": f"{model} (API)", "prompt": tmpl.version}) + "\n"
            for i, t in sorted(texts.items())
        )
    )
    (out_dir / "kinds.yaml").write_text(
        "# Kind de cada producto según el describer (catalog/describe_api.py). No editar a mano.\n"
        + yaml.safe_dump(dict(sorted(kinds.items())), allow_unicode=True, sort_keys=False)
    )
    (out_dir / "excluidos.yaml").write_text(
        "# Productos que no entran: fuera de alcance según el describer, o su descripción no pasó\n"
        "# la validación (check_text).\n"
        + yaml.safe_dump(
            {**excluded, **{i: {"motivo": f"descripción inválida: {m}"} for i, m in bad.items()}},
            allow_unicode=True,
            sort_keys=True,
        )
    )
    return {
        "descriptos": len(texts),
        "fuera_de_alcance": len(excluded),
        "invalidos": len(bad),
        "costo_usd": round(sum(a.get("cost_usd") or 0 for a in answers), 4),
    }
