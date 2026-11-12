"""The RAG core with no network: the catalog, the filters and the ranking, the vector database
and the index cache, the describers and embedders, the paid gate, the LLM steps and the flow."""

import ast
import json
from pathlib import Path

import httpx
import numpy as np
import pytest
import yaml
from PIL import Image

import amoblai
from amoblai.catalog.loader import load_catalog
from amoblai.config import load_config
from amoblai.furnish import steps as st
from amoblai.furnish.flow import run_flow
from amoblai.furnish.llm import OpenAIChat, parse_json
from amoblai.infra import http
from amoblai.infra.budget import BudgetExceeded, Ledger, PaidCallsDisabled
from amoblai.infra.http import ProviderError
from amoblai.rag import describe
from amoblai.rag.embed import OpenAIEmbedder
from amoblai.rag.filters import Filters
from amoblai.rag.index import build_index, open_index
from amoblai.rag.search import Hit, search
from amoblai.rag.store import ChromaStore

PRODUCTS = [  # id, category, name, colors, materials, W x D x H cm
    ("chair-oak", "chair", "Oak dining chair", ["natural oak"], ["solid oak"], (45, 50, 80)),
    ("chair-black", "chair", "Black metal cafe chair", ["black"], ["steel"], (42, 48, 82)),
    ("sofa-green", "sofa", "Green velvet sofa", ["green"], ["velvet", "oak legs"], (200, 90, 80)),
    ("desk-oak", "desk", "Oak writing desk", ["natural oak"], ["solid oak"], (120, 60, 75)),
]
CLAUDE = {
    "kind": "anthropic",
    "model": "claude-sonnet-5-5",
    "effort": "low",
    "models": {
        "claude-sonnet-5-5": {"usd_per_m": {"input": 2.0, "output": 10.0}, "estimate_usd": 0.025}
    },
}
OPENAI = {
    "kind": "openai_chat",
    "model": "gpt-6.1-sol",
    "models": {"gpt-6.1-sol": {"usd_per_m": {"input": 2.0, "output": 10.0}, "estimate_usd": 0.015}},
}


def cfg_for(tmp_path, **rag):
    paths = []
    for pid, cat, name, colors, materials, (w, d, h) in PRODUCTS:
        p = tmp_path / "products" / pid
        (p / "photos").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 48), (120, 90, 60)).save(p / "photos" / "00.jpg")
        info = {
            "id": pid,
            "name": name,
            "category": cat,
            "dimensions_cm": {"width": w, "depth": d, "height": h},
            "photos": [{"file": "photos/00.jpg", "is_primary": True}],
            "colors": colors,
            "materials": materials,
        }
        (p / "product.json").write_text(json.dumps(info))
        paths.append(f"products/{pid}")
    (tmp_path / "catalog.yaml").write_text(yaml.safe_dump({"name": "test", "products": paths}))
    over = {
        "root": str(tmp_path),
        "cache_dir": str(tmp_path / "cache"),
        "budget": {"ledger": str(tmp_path / "ledger.jsonl")},
        "rag": {
            "catalog": "catalog.yaml",
            "describer": "fields",
            "embedder": "hashing",
            "describers": {
                "fields": {"kind": "fields"},
                "anthropic": {**CLAUDE, "kind": "anthropic_vision"},
                "openai": {**OPENAI, "kind": "openai_chat_vision"},
            },
            **rag,
        },
        "furnish": {
            "llm": {
                **CLAUDE,
                "model": "claude-opus-5-5",
                "models": {
                    "claude-opus-5-5": {
                        "usd_per_m": {"input": 4.0, "output": 20.0},
                        "estimate_usd": 0.15,
                    }
                },
            }
        },
    }
    return load_config(None, over)


def test_the_core_does_not_import_the_evaluation_or_the_cli():
    """The layers the flow runs on (catalog, rag, furnish, infra) stand on their own."""
    root = Path(amoblai.__file__).parent
    for pkg in ("catalog", "rag", "furnish", "infra", "prompts"):
        for f in (root / pkg).glob("*.py"):
            for node in ast.walk(ast.parse(f.read_text())):
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    assert not (node.module or "").startswith(
                        ("amoblai.evaluation", "amoblai.cli")
                    ), f"{pkg}/{f.name}: {node.module}"


def test_hybrid_search_fuses_other_scorers_and_keeps_the_filters(tmp_path, monkeypatch):
    from amoblai.rag import search as search_module

    cfg = cfg_for(tmp_path)
    build_index(cfg, log=lambda _: None)
    index = open_index(cfg)
    dense = [h.id for h in search(index, "an oak chair", Filters(categories=["chair"]), cfg)]
    cfg.rag.hybrid = ["bm25"]  # lexical + dense: the same two chairs, and nothing the filter stops
    hits = search(index, "an oak chair", Filters(categories=["chair"]), cfg)
    assert [h.id for h in hits] == dense == ["chair-oak", "chair-black"]
    assert hits[0].score > hits[1].score

    # each scorer is standardized, so it counts as one vote however large its numbers are:
    # three scorers for the black chair outweigh the two (dense, lexical) for the oak one
    def photo_says_black(index, name, query, cfg):
        if name == "bm25":
            return search_module.BM25([it["description"] for it in index.items]).scores([query])[0]
        return np.array([100.0 if it["id"] == "chair-black" else 0.0 for it in index.items])

    monkeypatch.setattr(search_module, "other_scores", photo_says_black)
    cfg.rag.hybrid = ["bm25", "siglip2", "siglip2", "siglip2"]
    hits = search(index, "an oak chair", Filters(categories=["chair"]), cfg)
    assert [h.id for h in hits] == ["chair-black", "chair-oak"]
    cfg.rag.hybrid = ["nothing"]
    monkeypatch.undo()
    with pytest.raises(ValueError, match=r"rag\.hybrid"):
        search(index, "an oak chair", Filters(), cfg)


def test_search_applies_the_filters_then_ranks(tmp_path):
    cfg = cfg_for(tmp_path)
    build_index(cfg, log=lambda _: None)
    hits = search(open_index(cfg), "an oak chair", Filters(categories=["chair"]), cfg)
    assert [h.id for h in hits] == ["chair-oak", "chair-black"]
    assert hits[0].score > hits[1].score
    assert hits[0].photos == ["products/chair-oak/photos/00.jpg"]  # under the root
    hits = search(open_index(cfg), "oak", Filters(max_width_cm=100), cfg)
    assert {h.id for h in hits} == {"chair-oak", "chair-black"}  # the sofa and desk are too wide
    cfg.rag.top_k = 1
    assert len(search(open_index(cfg), "oak", Filters(), cfg)) == 1


ITEMS = [  # the filters' corner cases: no kind, no size, two of three measures
    {
        "id": "a",
        "category": "chair",
        "kind": "dining chair",
        "dimensions_cm": {"width": 45, "depth": 50, "height": 80},
    },
    {
        "id": "b",
        "category": "chair",
        "kind": "armchair",
        "dimensions_cm": {"width": 80, "depth": 85, "height": 95},
    },
    {"id": "c", "category": "chair", "kind": None, "dimensions_cm": None},
    {"id": "d", "category": "rug", "kind": "rug", "dimensions_cm": {"width": 170, "depth": 240}},
    {
        "id": "e",
        "category": "table",
        "kind": "coffee table",
        "dimensions_cm": {"width": 70, "depth": 70},
    },
    {"id": "f", "category": "sofa", "kind": "sofa", "dimensions_cm": None},
]
FILTERS = [
    Filters(),
    Filters(categories=["chair"]),
    Filters(kinds=["armchair"]),
    Filters(kinds=["dining chair", "armchair"]),
    Filters(kinds=["rug"], max_width_cm=200, max_depth_cm=230),
    Filters(categories=["table", "rug"], max_width_cm=100),
    Filters(max_height_cm=90),
]


@pytest.mark.parametrize("f", FILTERS, ids=lambda f: str(f.model_dump(exclude_defaults=True)))
def test_chroma_where_lets_through_the_same_products_as_allows(f):
    store = ChromaStore(None, "test-where")
    vectors = np.eye(len(ITEMS), 8, dtype=np.float32)
    store.create(ITEMS, vectors)
    got = {pid for pid, _ in store.query(np.ones(8, np.float32), len(ITEMS), f.where())}
    assert got == {it["id"] for it in ITEMS if f.allows(it)}


def test_chroma_ranks_like_the_exact_search(tmp_path):
    cfg = cfg_for(tmp_path)
    index = build_index(cfg, log=lambda _: None)
    assert (index.path / "chroma").is_dir() and index.meta["vector_store"]["kind"] == "chromadb"
    assert not (index.path / "vectors.npy").exists()  # the vectors live in ChromaDB
    for query, f in [
        ("an oak chair", Filters()),
        ("green velvet", Filters(categories=["sofa"])),
        ("black metal", Filters(max_width_cm=100)),
    ]:
        cfg.rag.vector_store = "chroma"
        chroma = [(h.id, round(h.score, 5)) for h in search(open_index(cfg), query, f, cfg)]
        cfg.rag.vector_store = "exact"
        exact = [(h.id, round(h.score, 5)) for h in search(open_index(cfg), query, f, cfg)]
        assert chroma == exact


def test_a_catalog_takes_folders_json_lines_and_other_catalogs(tmp_path):
    cfg_for(tmp_path)  # writes the products and catalog.yaml
    folder = tmp_path / "dir.yaml"
    folder.write_text(
        yaml.safe_dump(
            {"name": "dir", "product_dirs": ["products"], "categories": {"chair-black": "stool"}}
        )
    )
    cat = load_catalog(folder, tmp_path)
    assert [p.id for p in cat.products] == sorted(p[0] for p in PRODUCTS)
    assert {p.id: p.category for p in cat.products}["chair-black"] == "stool"
    Image.new("RGB", (8, 8)).save(tmp_path / "lamp.jpg")
    rows = [
        {
            "id": "lamp",
            "name": "Lamp",
            "category": "table",
            "kind": "side table",
            "photos": ["lamp.jpg"],
            "price": 10,
        }
    ]
    (tmp_path / "items.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    main = tmp_path / "main.yaml"
    main.write_text(
        yaml.safe_dump({"name": "main", "items": ["items.jsonl"], "catalogs": ["catalog.yaml"]})
    )
    cat = load_catalog(main, tmp_path)
    assert [p.id for p in cat.products] == ["lamp"] + [p[0] for p in PRODUCTS]
    assert cat.products[0].kind == "side table" and cat.products[0].photos() == [
        tmp_path / "lamp.jpg"
    ]
    # no size: the size filters let it through
    assert Filters(max_width_cm=10).allows({"category": "table", "kind": "side table"})

    (tmp_path / "bad.jsonl").write_text(json.dumps({"id": "x", "name": "X"}) + "\n")
    main.write_text(yaml.safe_dump({"name": "bad", "items": ["bad.jsonl"]}))
    with pytest.raises(ValueError, match="category"):
        load_catalog(main, tmp_path)


def test_a_piece_that_fits_turned_passes_the_size_filter():
    rug = {"category": "rug", "kind": "rug", "dimensions_cm": {"width": 200, "depth": 300}}
    spot = Filters(max_width_cm=300, max_depth_cm=220)  # the plan: 300 wide, 220 deep
    assert spot.allows(rug)  # 200 x 300 turned is 300 x 200
    assert not Filters(max_width_cm=250, max_depth_cm=220).allows(rug)  # too long either way
    assert not Filters(max_width_cm=150).allows(rug)  # one limit alone: no turning
    assert Filters(max_depth_cm=300, max_height_cm=5).allows(rug)  # a missing height passes
    where = spot.where()
    assert where == {
        "$or": [
            {"$and": [{"width": {"$lte": 300.0}}, {"depth": {"$lte": 220.0}}]},
            {"$and": [{"width": {"$lte": 220.0}}, {"depth": {"$lte": 300.0}}]},
        ]
    }


def test_kinds_come_from_the_catalog_and_filter_the_search(tmp_path):
    cfg = cfg_for(tmp_path)
    data = yaml.safe_load((tmp_path / "catalog.yaml").read_text())
    kinds = tmp_path / "kinds.yaml"
    kinds.write_text(yaml.safe_dump({"chair-oak": "dining chair", "sofa-green": "sofa"}))
    (tmp_path / "catalog.yaml").write_text(yaml.safe_dump({**data, "kinds_file": "kinds.yaml"}))
    build_index(cfg, log=lambda _: None)
    idx = open_index(cfg)
    assert {it["id"]: it["kind"] for it in idx.items}["chair-black"] is None
    hits = search(idx, "a chair", Filters(kinds=["dining chair"]), cfg)
    assert {h.id: h.kind for h in hits} == {"chair-oak": "dining chair", "chair-black": None}
    assert [h.id for h in search(idx, "a chair", Filters(kinds=["armchair"]), cfg)] == [
        "chair-black"
    ]
    assert search(idx, "a sofa", Filters(kinds=["sofa bed"]), cfg) == []
    kinds.write_text(yaml.safe_dump({"chair-oak": "throne"}))
    with pytest.raises(ValueError, match="throne"):
        load_catalog("catalog.yaml", tmp_path)


def test_whole_catalog_mode_returns_every_product_that_passes(tmp_path):
    cfg = cfg_for(tmp_path, mode="whole_catalog")
    build_index(cfg, log=lambda _: None)
    hits = search(open_index(cfg), "anything", Filters(), cfg)
    assert [h.id for h in hits] == [p[0] for p in PRODUCTS]
    assert all(h.score is None for h in hits)


def test_descriptions_are_written_once(tmp_path, monkeypatch):
    cfg = cfg_for(tmp_path)
    build_index(cfg, log=lambda _: None)

    def boom(self, product):
        raise AssertionError("described again")

    monkeypatch.setattr(describe.FieldsDescriber, "describe", boom)
    assert len(build_index(cfg, log=lambda _: None).items) == len(PRODUCTS)


def test_written_descriptions_are_read_and_a_missing_one_is_left_out(tmp_path):
    rows = [
        {"id": "chair-oak", "text": "Type: oak dining chair\nStyle: Scandinavian\n", "by": "x"},
        {"id": "sofa-green", "text": "Type: green velvet sofa\n", "by": "x"},
    ]
    (tmp_path / "written.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    cfg = cfg_for(tmp_path, describer="written")
    cfg.rag.describers["written"] = {"kind": "written", "file": "written.jsonl"}
    said: list[str] = []
    idx = build_index(cfg, log=said.append)
    assert [it["id"] for it in idx.items] == ["chair-oak", "sofa-green"]
    assert idx.items[0]["description"].startswith("Type: oak dining chair")
    assert idx.meta["left_out"] == 2 and len(said) == 2
    assert search(open_index(cfg), "green velvet sofa", Filters(), cfg)[0].id == "sofa-green"
    (tmp_path / "more.jsonl").write_text(
        json.dumps({"id": "desk-oak", "text": "Type: desk\n"}) + "\n"
    )
    cfg.rag.describers["written"] = {"kind": "written", "file": ["written.jsonl", "more.jsonl"]}
    assert len(build_index(cfg, log=said.append).items) == 3


def messages_server(seen: list, text: str = "Type: chair\n", stop_reason: str = "end_turn"):
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = {
            "model": "claude-sonnet-5-5",
            "content": [{"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "usage": {"input_tokens": 6000, "output_tokens": 800},
        }
        return httpx.Response(200, json=body)

    return handle


def test_paid_describer_needs_approval(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(messages_server(seen)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with pytest.raises(PaidCallsDisabled):
        build_index(cfg_for(tmp_path, describer="anthropic"), log=lambda _: None)
    assert seen == []


def test_anthropic_describer_request_cost_and_its_own_cap(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(messages_server(seen)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    cfg = cfg_for(tmp_path, describer="anthropic", workers=3)
    cfg.budget.allow_paid = True
    cfg.budget.max_usd_total = 0.0  # the shared pool is spent: Claude goes by its own cap
    cfg.budget.accounts = {"anthropic": 1.0}
    idx = build_index(cfg, log=lambda _: None)
    assert len(seen) == len(PRODUCTS) and len(idx.items) == len(PRODUCTS)
    req = json.loads(seen[0].content)
    assert seen[0].url.path == "/v1/messages" and seen[0].headers["x-api-key"] == "sk-ant-test"
    assert req["model"] == "claude-sonnet-5-5" and req["output_config"] == {"effort": "low"}
    image, text = req["messages"][0]["content"]
    assert image["type"] == "image" and image["source"]["media_type"] == "image/jpeg"
    assert text["type"] == "text"
    prompts = [json.loads(r.content)["messages"][0]["content"][-1]["text"] for r in seen]
    assert all(any(f'"{p[2]}"' in t for t in prompts) for p in PRODUCTS)  # 3 at once: any order
    assert {e["pool"] for e in Ledger(cfg.budget.ledger, 10).entries()} == {"anthropic"}
    assert Ledger(cfg.budget.ledger, 1.0, "anthropic").spent() == pytest.approx(
        len(PRODUCTS) * (6000 * 2.0 + 800 * 10.0) / 1e6
    )
    assert Ledger(cfg.budget.ledger, 10).spent() == 0  # the shared pool is untouched
    build_index(cfg, log=lambda _: None)
    assert len(seen) == len(PRODUCTS)  # cached: nothing sent the second time


def test_an_account_stops_at_its_own_cap_and_a_refusal_is_left_out(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(messages_server(seen)))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    cfg = cfg_for(tmp_path, describer="anthropic")
    cfg.budget.allow_paid = True
    cfg.budget.accounts = {"anthropic": 0.06}  # two products at ~$0.025 estimated each
    with pytest.raises(BudgetExceeded, match="anthropic"):
        build_index(cfg, log=lambda _: None)
    assert len(seen) == 2
    server = messages_server(seen, stop_reason="refusal")
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(server))
    cfg.budget.accounts = {"anthropic": 10.0}
    cfg.rag.describers["anthropic"]["effort"] = "medium"  # another key: described again
    with pytest.raises(ProviderError, match="no product described"):
        build_index(cfg, log=lambda _: None)


def test_openai_compatible_describer_request_and_cost(tmp_path, monkeypatch):
    seen: list = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = {
            "model": "gpt-6.1-sol",
            "choices": [{"finish_reason": "stop", "message": {"content": "Type: chair\n"}}],
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
        }
        return httpx.Response(200, json=body)

    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(handle))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    cfg = cfg_for(tmp_path, describer="openai")
    cfg.budget.allow_paid = True
    idx = build_index(cfg, log=lambda _: None)
    req = json.loads(seen[0].content)
    assert seen[0].url.path == "/v1/chat/completions"
    assert seen[0].headers["authorization"] == "Bearer sk-test"
    image, text = req["messages"][0]["content"]
    assert image["type"] == "image_url"
    assert image["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert text["type"] == "text" and '"Oak dining chair"' in text["text"]
    assert idx.items[0]["description"] == "Type: chair\n"
    spent = Ledger(cfg.budget.ledger, 10, "openai").spent() + Ledger(cfg.budget.ledger, 10).spent()
    assert spent == pytest.approx(len(PRODUCTS) * (1000 * 2.0 + 500 * 10.0) / 1e6)
    assert OpenAIChat.part({"type": "text", "text": "hi"}) == {"type": "text", "text": "hi"}


def test_openai_embedder_keeps_the_order_normalizes_and_can_go_through_fal():
    seen = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        texts = json.loads(request.content)["input"]
        data = [{"index": i, "embedding": [float(i + 1), 2.0, 0.0]} for i in range(len(texts))]
        return httpx.Response(200, json={"data": data[::-1], "usage": {"total_tokens": 30}})

    params = {
        "model": "text-embedding-3-large",
        "api_key_env": ["ROOMRAG_TEST_KEY"],
        "models": {"text-embedding-3-large": {"usd_per_m": 0.13}},
    }
    emb = OpenAIEmbedder(params, client=httpx.Client(transport=httpx.MockTransport(handle)))
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("ROOMRAG_TEST_KEY", "sk-test")
        e = emb.embed(["a", "b", "c"])
        assert np.allclose(np.linalg.norm(e.vectors, axis=1), 1.0)
        assert e.vectors[0, 0] < e.vectors[2, 0]  # row i is text i, whatever order the reply had
        assert e.cost_usd == pytest.approx(30 * 0.13 / 1e6) and e.cost_source == "api_tokens"
        fal = OpenAIEmbedder(
            {**params, "auth": "key", "base_url": "https://fal.run/x/v1"},
            client=httpx.Client(transport=httpx.MockTransport(handle)),
        )
        fal.embed(["a"])
    assert str(seen[-1].url) == "https://fal.run/x/v1/embeddings"
    assert seen[-1].headers["authorization"] == "Key sk-test"


def test_parse_json_with_or_without_a_fence():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('Here: {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ProviderError):
        parse_json("no json here")


# The LLM steps ---------------------------------------------------------------------------------


def claude_server(seen: list, answers: list[dict]):
    """Answers in turn, one per call."""

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        answer = answers[min(len(seen), len(answers)) - 1]
        body = {
            "model": "claude-opus-5-5",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": json.dumps(answer)}],
            "usage": {"input_tokens": 10000, "output_tokens": 1000},
        }
        return httpx.Response(200, json=body)

    return handle


def hit(i: int, kind: str = "dining chair") -> Hit:
    return Hit(
        f"p{i}",
        f"P{i}",
        "chair",
        {"width": 50, "depth": 50, "height": 80},
        "x",
        ["photos/a.jpg"],
        "Type: upholstered side chair\n",
        0.5,
        kind,
    )


def test_llm_steps_need_approval(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [{}])))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    with pytest.raises(PaidCallsDisabled):
        st.ask(cfg_for(tmp_path), "furnish.choose", [{"type": "text", "text": "hi"}])
    assert seen == []


def test_the_plan_gets_the_kinds_and_unknown_kinds_are_dropped(tmp_path, monkeypatch):
    seen: list = []
    room = tmp_path / "room.jpg"
    Image.new("RGB", (64, 48)).save(room)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    piece = {"piece": "a chair at the desk", "kinds": ["Desk Chair", "throne"], "query": "Type: x"}
    answer = {"room": "a study", "pieces": [piece]}
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [answer])))
    cfg = cfg_for(tmp_path)
    cfg.budget.allow_paid = True
    rec = st.plan(cfg, room, "una silla")
    assert rec["answer"]["pieces"][0]["kinds"] == ["desk chair"]
    assert rec["unknown_kinds"] == ["throne"]
    prompt = seen[0]["messages"][0]["content"][-1]["text"]
    assert "- chair: desk chair, dining chair, armchair" in prompt and "{kinds}" not in prompt
    assert (
        "- lamp: pendant lamp" in prompt
        and "as many as the request and the room call for" in prompt
        and "{max_pieces}" not in prompt
    )


def test_two_kinds_share_the_candidates_and_the_sizes_get_slack(tmp_path, monkeypatch):
    seen: list = []

    def fake_search(index, query, filters, cfg):
        seen.append((filters.kinds, filters.max_width_cm, cfg.rag.top_k))
        return [
            Hit(
                f"{filters.kinds[0]}{i}",
                "x",
                "chair",
                {},
                "p",
                [],
                "",
                0.9 - i / 10,
                filters.kinds[0],
            )
            for i in range(cfg.rag.top_k)
        ]

    monkeypatch.setattr(st, "ensure_index", lambda cfg: "the index")
    monkeypatch.setattr(st, "search", fake_search)
    cfg = cfg_for(tmp_path)
    cfg.furnish.candidates = 10
    piece = {"kinds": ["desk chair", "dining chair"], "max_width_cm": 60, "query": "q"}
    hits = st.find_candidates(cfg, piece)
    assert seen == [(["desk chair"], 69.0, 5), (["dining chair"], 69.0, 5)]
    assert len(hits) == 10 and {h.kind for h in hits} == {"desk chair", "dining chair"}
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


def test_the_choice_is_one_candidate_per_piece_and_is_logged(tmp_path, monkeypatch):
    seen: list = []
    room = tmp_path / "room.jpg"
    Image.new("RGB", (64, 48)).save(room)
    (tmp_path / "photos").mkdir()
    Image.new("RGB", (64, 48)).save(tmp_path / "photos" / "a.jpg")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    cfg = cfg_for(tmp_path)
    cfg.budget.allow_paid = True
    found = [({"piece": "a chair"}, [hit(1), hit(2)]), ({"piece": "a table"}, [hit(3)])]
    good = {"choices": [{"piece": 1, "id": "p2", "why": "warm"}, {"piece": 2, "id": "p3"}]}
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [good])))
    rec = st.choose(cfg, room, "un comedor", found)
    assert [c["id"] for c in rec["answer"]["choices"]] == ["p2", "p3"]
    content = seen[0]["messages"][0]["content"]
    assert sum(c["type"] == "image" for c in content) == 4  # the room + 3 candidates
    line = "Piece 2: a table\n  image 4. p3: dining chair, upholstered side chair, 50 cm wide"
    assert line in content[-1]["text"]
    # no cap of its own for anthropic in this config: the shared pool
    assert Ledger(cfg.budget.ledger, 30).spent() == pytest.approx((10000 * 4 + 1000 * 20) / 1e6)
    wrong = {"choices": [{"id": "p3"}, {"id": "p3"}]}  # p3 is not a chair candidate
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [wrong])))
    with pytest.raises(ProviderError, match="not a candidate"):
        st.choose(cfg, room, "un comedor", found)
    # how many of each: four chairs, and the table left out (none of its candidates suits)
    some = {
        "choices": [
            {"piece": 1, "id": "p2", "quantity": 4},
            {"piece": 2, "id": None, "quantity": 0},
        ]
    }
    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [some])))
    rec = st.choose(cfg, room, "un comedor para cuatro", found)
    assert [c["quantity"] for c in rec["answer"]["choices"]] == [4, 0]
    retrieve = {
        "pieces": [
            {"piece": s["piece"], "spec": s, "candidates": [vars(h) for h in hs]} for s, hs in found
        ]
    }
    picks = st.picks(retrieve, rec)
    assert [(p["quantity"], h.id) for p, h in picks] == [(4, "p2")]
    assert st.units(picks[0][0]) == ", 4 units" and st.units({"piece": "x"}) == ""


def test_the_whole_flow_resumes_and_waits_for_the_manual_image(tmp_path, monkeypatch):
    seen: list = []
    cfg = cfg_for(tmp_path)
    cfg.budget.allow_paid = True
    photo = tmp_path / "living.jpg"
    Image.new("RGB", (80, 60), (200, 190, 180)).save(photo)
    plan = {
        "room": "an empty living room",
        "pieces": [
            {"piece": "a sofa", "kinds": ["sofa"], "query": "Type: sofa\nColors: green"},
            {"piece": "a bed", "kinds": ["bed"], "query": "Type: bed"},  # the catalog has none
            {"piece": "a chair", "kinds": [], "categories": ["chair"], "query": "Type: oak chair"},
        ],
    }
    choice = {"choices": [{"id": "sofa-green"}, {"id": "chair-oak"}], "why": "green and oak"}
    scene = {"prompt": "Put the sofa of image 2 against the back wall...", "placements": []}
    monkeypatch.setattr(
        http, "TRANSPORT", httpx.MockTransport(claude_server(seen, [plan, choice, scene]))
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    out = tmp_path / "run"
    run = run_flow(photo, "un living", cfg, out, log=lambda _: None)
    assert len(seen) == 3 and run.data["generate"]["pending"]
    found = json.loads((out / "2_candidates.json").read_text())
    assert found["empty"] == ["a bed"]
    assert [c["id"] for c in found["pieces"][1]["candidates"]] == ["chair-oak", "chair-black"]
    assert "image 3. chair-oak" in seen[2]["messages"][0]["content"][-1]["text"]  # the scene
    assert (out / "2_candidates.jpg").exists() and (out / "2_candidates_2.jpg").exists()
    job = out / "manual"
    assert (job / "prompt.txt").read_text().startswith("Put the sofa")
    assert sorted(p.name for p in job.glob("*.jpg")) == [
        "1_room.jpg",
        "2_product_1.jpg",
        "3_product_2.jpg",
    ]
    assert not (out / "5_image.json").exists()
    Image.new("RGB", (80, 60), "green").save(job / "result.png")  # the person pastes it back
    run = run_flow(photo, "un living", cfg, out, log=lambda _: None)
    assert len(seen) == 3  # nothing asked again
    assert run.data["generate"]["image"] == "final.png" and (out / "final.png").exists()
    assert [h.id for h in run.chosen()] == ["sofa-green", "chair-oak"]
