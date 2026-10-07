import yaml

from amoblai.config import load_config
from amoblai.eval.ablation import expand_plan
from tests.conftest import ROOT


def test_expand_plan_incremental_then_grid():
    plan = {
        "incremental": [
            {"name": "E0", "set": {"embedding.name": "clip", "retrieval.category_filter": False}}
        ],
        "grid": {"embedding.name": ["clip", "dinov2"], "background.method": ["none", "sam"]},
    }
    runs = expand_plan(plan)
    assert runs[0] == ("E0", ["embedding.name=clip", "retrieval.category_filter=false"])
    assert len(runs) == 1 + 4
    assert ("name-clip__method-sam", ["embedding.name=clip", "background.method=sam"]) in runs


def test_shipped_plans_produce_valid_configs():
    for name in ("retriever.yaml", "e2e.yaml"):
        path = ROOT / "configs" / "ablaciones" / name
        plan = yaml.safe_load(path.read_text())
        assert plan.get("kind", "retriever") in ("retriever", "e2e")
        for _, overrides in expand_plan(plan):
            load_config(path.parent / plan["base"], overrides)  # valida con pydantic
