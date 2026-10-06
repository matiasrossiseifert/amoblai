import json

import pytest
from pydantic import ValidationError

from amoblai.config import load_config, parse_override, stable_hash
from amoblai.infra.budget import BudgetExceededError, BudgetGuard
from amoblai.infra.cache import ArtifactCache
from amoblai.infra.runs import RunContext, SubRun, list_runs
from amoblai.infra.usage import PricingTable, SpendLedger, UsageRecord, summarize_usage
from tests.conftest import ROOT


def test_extends_and_overrides(tmp_path):
    child = tmp_path / "child.yaml"
    child.write_text(
        f"extends: {ROOT / 'configs' / 'base.yaml'}\nname: hijo\nembedding:\n  name: clip\n"
    )
    cfg = load_config(child, ["retrieval.top_k=3", "retrieval.threshold=0.5"])
    assert cfg.name == "hijo"
    assert cfg.embedding.name == "clip"
    assert cfg.embedding.batch_size == 16  # heredado
    assert cfg.retrieval.top_k == 3
    assert cfg.retrieval.threshold == 0.5


def test_unknown_fields_fail(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("retrieval:\n  topk: 3\n")
    with pytest.raises(ValidationError):
        load_config(bad)


def test_parse_override_nested():
    assert parse_override("a.b.c=[1, 2]") == {"a": {"b": {"c": [1, 2]}}}
    assert parse_override("x=null") == {"x": None}


def test_stable_hash_is_order_independent():
    assert stable_hash({"a": 1, "b": 2}) == stable_hash({"b": 2, "a": 1})


def test_cache_roundtrip(tmp_path):
    from PIL import Image

    cache = ArtifactCache(tmp_path, "ns")
    key = cache.key({"x": 1})
    assert cache.get_json(key) is None
    cache.put_json(key, {"ok": True})
    cache.put_image(key, Image.new("RGB", (4, 4), "red"))
    assert cache.get_json(key) == {"ok": True}
    assert cache.get_image(key).size == (4, 4)


def test_pricing_cost_and_estimate():
    pricing = PricingTable.load(ROOT / "configs" / "pricing.yaml")
    rec = UsageRecord(
        stage="g",
        provider="openai",
        model="gpt-image-2",
        input_text_tokens=1_000_000,
        output_image_tokens=1_000_000,
    )
    assert pricing.cost(rec) == pytest.approx(5.0 + 30.0)
    assert pricing.cost(rec, batch=True) == pytest.approx(17.5)
    est = pricing.estimate("openai", "gpt-image-2", "medium", (1024, 1024), 2)
    assert 0.01 < est < 0.2
    assert pricing.estimate("desconocido", "x", "medium", (1024, 1024), 1) == 0.0


def test_budget_limits(tmp_path):
    guard = BudgetGuard(max_calls=1, max_usd=1.0)
    guard.authorize(0.5, "a")
    guard.record(0.5)
    with pytest.raises(BudgetExceededError):
        guard.authorize(0.1, "b")  # tope de llamadas
    guard = BudgetGuard(max_usd=1.0)
    with pytest.raises(BudgetExceededError):
        guard.authorize(1.5, "c")
    ledger = SpendLedger(tmp_path / "gastos.jsonl")
    ledger.append(UsageRecord(stage="s", provider="p", model="m", cost_usd=4.0))
    guard = BudgetGuard(max_usd_total=5.0, ledger=ledger)
    with pytest.raises(BudgetExceededError):
        guard.authorize(2.0, "d")
    BudgetGuard(max_calls=0, dry_run=True).authorize(100.0, "dry-run nunca corta")


def test_usage_summary_ignores_cached_and_dry_run():
    records = [
        UsageRecord(stage="g1", provider="openai", model="m", cost_usd=0.1, latency_s=2),
        UsageRecord(stage="g1", provider="openai", model="m", cost_usd=0.0, cached=True),
        UsageRecord(stage="g2", provider="dry_run", model="m", cost_usd=0.5, dry_run=True),
    ]
    s = summarize_usage(records)
    assert s["api_calls"] == 1
    assert s["cached_calls"] == 1
    assert s["cost_usd"] == pytest.approx(0.1)
    assert s["estimated_cost_usd_dry_run"] == pytest.approx(0.5)


def test_run_context_writes_artifacts(cfg):
    run = RunContext(cfg, "test", name="Prueba 1")
    run.add_usage(UsageRecord(stage="s", provider="p", model="m", cost_usd=0.2))
    sub = SubRun(run, "ambientes/a")
    sub.add_usage(UsageRecord(stage="s", provider="p", model="m", cost_usd=0.3))
    sub.finish({"x": 1})
    run.finish({"metric": 1})
    metrics = json.loads((run.dir / "metrics.json").read_text())
    assert metrics["metric"] == 1
    assert metrics["usage"]["cost_usd"] == pytest.approx(0.5)
    assert (run.dir / "config.yaml").exists()
    manifest = json.loads((run.dir / "manifest.json").read_text())
    assert manifest["kind"] == "test" and manifest["finished_at"]
    assert list_runs(cfg.paths.runs_dir, kind="test") == [run.dir]
    # Dos corridas en el mismo segundo no chocan.
    assert RunContext(cfg, "test", name="Prueba 1").dir != run.dir
