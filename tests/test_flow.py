import gzip
import io
import json
import re
from pathlib import Path

import httpx
import pytest
from PIL import Image

from amoblai.evaluation.report import build_report
from amoblai.evaluation.retrieval import Method, load_ablation, run_eval
from amoblai.furnish.flow import run_flow
from amoblai.furnish.image_models import FalNanoBanana
from amoblai.furnish.llm import claude_cost, text_block
from amoblai.furnish.steps import size_text
from amoblai.infra import http
from amoblai.infra.budget import BudgetExceeded, Ledger, PaidCallsDisabled
from amoblai.infra.http import ProviderError
from amoblai.prompts import load_prompt
from amoblai.rag.search import Hit
from tests.conftest import CLAUDE, PRODUCTS, ROOM_ID, ROOT


def _png(color="green", size=(80, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


def fal_handler(seen: list):
    """La API de colas de fal: alta, estado, resultado y la imagen en el CDN."""

    def handle(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        seen.append((request.method, url, request.headers.get("authorization")))
        if request.method == "POST" and url.endswith("/fal-ai/nano-banana-2/edit"):
            body = json.loads(request.content)
            seen.append(("payload", body))
            base = "https://queue.fal.run/fal-ai/nano-banana-2/edit/requests/r1"
            return httpx.Response(
                200, json={"request_id": "r1", "status_url": f"{base}/status", "response_url": base}
            )
        if url.endswith("/requests/r1/status"):
            return httpx.Response(200, json={"status": "COMPLETED"})
        if url.endswith("/requests/r1"):
            return httpx.Response(
                200, json={"images": [{"url": "https://v3.fal.media/out.png"}], "description": "ok"}
            )
        if url == "https://v3.fal.media/out.png":
            return httpx.Response(200, content=_png())
        return httpx.Response(404)

    return handle


def claude_handler(seen: list, answers: list[dict]):
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        answer = answers[(len(seen) - 1) % len(answers)]  # cicla: una corrida = 3 llamadas
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-5-5",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps(answer)}],
                "usage": {"input_tokens": 10000, "output_tokens": 1000},
            },
        )

    return handle


def test_fal_generator_runs_the_queue_and_saves_the_image(tmp_path, monkeypatch):
    seen: list = []
    monkeypatch.setenv("FAL_KEY", "fal-test")
    room, prod = tmp_path / "room.jpg", tmp_path / "p.jpg"
    Image.new("RGB", (300, 200), "white").save(room)
    Image.new("RGB", (64, 64), "red").save(prod)
    gen = FalNanoBanana(
        {"poll_s": 0}, None, client=httpx.Client(transport=httpx.MockTransport(fal_handler(seen)))
    )
    g = gen.generate("put the product of image 2 in the room", [room, prod], tmp_path)
    assert g.image.name == "final.png" and g.cost_usd == 0.08 and g.cost_source == "estimate"
    payload = next(x[1] for x in seen if x[0] == "payload")
    assert len(payload["image_urls"]) == 2 and payload["image_urls"][0].startswith(
        "data:image/png;base64,"
    )
    assert payload["aspect_ratio"] == "auto" and payload["resolution"] == "1K"
    assert ("GET", "https://v3.fal.media/out.png", None) in seen  # el CDN, sin la clave
    assert all(auth == "Key fal-test" for m, url, auth in [s for s in seen if s[0] in ("POST",)])


def test_text_retrieval_eval_finds_the_annotated_products(tmp_path, cfg, dataset_root):
    queries = {
        "_meta": {"prompt": "test"},
        ROOM_ID: {
            "room": "a living room",
            "pieces": [
                {"piece": "red sofa", "kinds": ["sofa"], "query": PRODUCTS["100.000.01"][3]},
                {
                    "piece": "oak table",
                    "kinds": ["coffee table"],
                    "query": PRODUCTS["100.000.05"][3],
                },
                {"piece": "blue rug", "kinds": ["rug"], "query": PRODUCTS["100.000.06"][3]},
                {
                    "piece": "an armchair not in the room",
                    "kinds": ["armchair"],
                    "query": PRODUCTS["100.000.04"][3],
                },
            ],
        },
    }
    qpath = tmp_path / "consultas.json"
    qpath.write_text(json.dumps(queries))
    methods = [
        Method("hashing", "description", "kind"),
        Method("hashing", "description", "kind", store="exact"),
        Method("hashing", "description", "kind", query="kind"),
        Method("hashing", "seller", "none"),
        Method("hashing", "description", "kind", dim=256),
        Method("hashing", "description", "kind", chunks="lines-max"),
        Method("hashing", "description", "kind", chunks="lines-aligned"),
        Method("bm25", "description", "kind"),  # búsqueda léxica
        Method("hashing", "description", "kind", fusion="bm25"),  # híbrida: densa + léxica
        Method("hashing", "description", "kind", fusion="bm25", fusion_rule="rrf"),
        Method("hashing", "seller-full", "none", query="piece"),  # naive: sin reescribir
        Method("hashing", "description", "kind", drop="Feel+Goes with"),
    ]
    run = run_eval(cfg, qpath, dataset_root, tmp_path / "evals", methods, name="t", n_boot=50)
    m = json.loads((run / "metricas.json").read_text())
    ours = m["hashing|description|filtro-kind"]
    # la léxica y la híbrida encuentran lo mismo en este catálogo chico, y cada método trae su
    # diferencia pareada contra el primero y contra el anterior
    for variant in ("bm25|description|filtro-kind", "hashing|description|filtro-kind|+bm25"):
        assert m[variant]["hit@1"] == 1.0
        assert m[variant]["vs_base"]["hit@1"] == 0.0 and "hit@5_ic95" in m[variant]["vs_anterior"]
    assert "hashing|description|filtro-kind|+bm25|fusion-rrf" in m
    assert "hashing|seller-full|filtro-none|consulta-piece" in m
    assert "hashing|description|filtro-kind|sin-Feel+Goes with" in m
    assert "vs_base" not in ours  # el primero es la base
    assert json.loads((run / "corrida.json").read_text())["embedders"]["bm25"] == {"kind": "bm25"}
    # ChromaDB (HNSW) y la búsqueda exacta ordenan igual
    rows = [
        json.loads(x)
        for x in gzip.decompress((run / "rankings.jsonl.gz").read_bytes()).splitlines()
    ]
    by = {}
    for r in rows:
        by.setdefault(r["method"], []).append(r["ranked"])
    assert by["hashing|description|filtro-kind"] == by["hashing|description|filtro-kind|exact"]
    assert "hashing|description|filtro-kind|consulta-kind" in m
    assert ours["answerable"] == 3  # el sillón no está anotado en el ambiente: sin relevantes
    assert ours["hit@1"] == 1.0 and ours["recall_item@10"] == 1.0
    assert ours["familia_hit@1"] == 1.0  # el anotado es de su propia familia
    assert ours["azar_hit@1"] < 1.0
    assert ours["context_precision@10"] == ours["ndcg@10"] == 1.0
    assert ours["context_recall@3"] == ours["context_recall@10"] == 1.0
    assert ours["curva_hit@k"]["1"] == ours["curva_hit@k"]["50"] == 1.0
    for variant in ("dim-256", "chunks-lines-max", "chunks-lines-aligned"):
        assert m[f"hashing|description|filtro-kind|{variant}"]["hit@1"] == 1.0
    assert (run / "rankings.jsonl.gz").exists() and json.loads((run / "corrida.json").read_text())[
        "rooms"
    ] == 1
    written = build_report(tmp_path / "evals", tmp_path / "reporte", v0_runs=tmp_path / "nada")
    assert "Retrieval por texto" in written["reporte"].read_text()


def test_the_class_metrics_on_the_slide_example():
    from amoblai.evaluation.metrics import auroc, context_precision_at_k, ndcg_at_k

    # Clase 11: dos chunks, solo el segundo relevante -> (0 * 0 + 0.5 * 1) / 1 = 0.5
    assert context_precision_at_k(["vinos", "paris"], ["paris"], 2) == 0.5
    assert context_precision_at_k(["a", "b", "c"], ["a", "c"], 3) == (1 + 2 / 3) / 2
    assert context_precision_at_k(["a", "b"], ["z"], 2) == 0.0
    assert ndcg_at_k(["a", "b"], ["a"], 10) == 1.0
    assert abs(ndcg_at_k(["b", "a"], ["a"], 10) - 1 / 1.5849625) < 1e-6
    assert auroc([0.9, 0.8, 0.3], [True, True, False]) == 1.0
    assert auroc([0.5, 0.5], [True, False]) == 0.5


def test_relevance_groups_split_lamps_and_decoration_by_kind():
    from amoblai.catalog.loader import Product
    from amoblai.evaluation.retrieval import group_of, product_group

    def product(category, kind, tp):
        return Product(
            Path("."), {"id": "1", "category": category, "kind": kind, "category_tp": tp}
        )

    assert group_of("side table") == group_of("coffee table") == "table"
    assert group_of("cushion") == "cushion" != group_of("vase")
    assert group_of("plant pot") == group_of("plant") and group_of("desk lamp") == "table lamp"
    assert group_of("TV stand") == group_of("sideboard") == "cabinet"
    assert product_group(product("deco", "picture frame", "deco")) == group_of("wall art")
    assert product_group(product("chair", "armchair", "chair")) == "chair"  # su tipo de IKEA
    assert product_group(product("desk", "desk", "table")) == "desk"  # corregido a escritorio


def test_an_ablation_is_a_grid_plus_loose_methods(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text(
        "name: prueba\n"
        "grid: {embedder: [hashing, bge], text: [description, seller], filter: [kind, type, none]}\n"
        "methods:\n"
        "  - {embedder: bge, text: name+description}\n"
        "  - {embedder: bge, filter: type, store: exact}\n"
        "  - {embedder: hashing}\n"  # ya está en la grilla
    )
    name, methods = load_ablation(f)
    assert name == "prueba" and len(methods) == 2 * 2 * 3 + 2
    assert methods[-1].name == "bge|description|filtro-type|exact"
    assert not any(m.paid for m in methods)
    real = load_ablation(ROOT / "datos" / "configs" / "ablaciones" / "reranking.yaml")[1]
    assert [m.paid for m in real] == [False, True]
    local = load_ablation(ROOT / "datos" / "configs" / "ablaciones" / "reranking-local.yaml")[1]
    assert not any(m.paid for m in local)  # los cross-encoders corren acá, gratis


def test_the_vlm_reranks_the_top_and_its_answers_are_cached(
    tmp_path, cfg, dataset_root, monkeypatch
):
    seen: list = []

    def reverse(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen.append(body)
        text = body["messages"][0]["content"][-1]["text"]
        ids = re.findall(r"image \d+\. (\S+):", text)
        answer = [f"image {i}" for i in range(len(ids), 0, -1)]  # a veces contesta así
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-5-5",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": json.dumps({"ranking": answer})}],
                "usage": {"input_tokens": 3000, "output_tokens": 200},
            },
        )

    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(reverse))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    cfg.evaluation.rerank_top = 3
    cfg.evaluation.rerankers = {"opus": CLAUDE}
    queries = {
        ROOM_ID: {
            "room": "living",
            "pieces": [{"piece": "rug", "kinds": ["rug"], "query": PRODUCTS["100.000.06"][3]}],
        }
    }
    qpath = tmp_path / "consultas.json"
    qpath.write_text(json.dumps(queries))
    methods = [
        Method("hashing", "description", "none"),
        Method("hashing", "description", "none", rerank="opus"),
    ]
    with pytest.raises(PaidCallsDisabled):
        run_eval(cfg, qpath, dataset_root, tmp_path / "evals", methods, name="r", n_boot=10)
    cfg.budget.allow_paid = True
    run = run_eval(cfg, qpath, dataset_root, tmp_path / "evals", methods, name="r", n_boot=10)
    rows = [
        json.loads(x)
        for x in gzip.decompress((run / "rankings.jsonl.gz").read_bytes()).splitlines()
    ]
    base, reranked = rows[0]["ranked"], rows[1]["ranked"]
    assert reranked[:3] == base[:3][::-1] and reranked[3:] == base[3:]
    assert (
        len(seen) == 1 and sum(b["type"] == "image" for b in seen[0]["messages"][0]["content"]) == 3
    )
    run_eval(cfg, qpath, dataset_root, tmp_path / "evals", methods, name="r2", n_boot=10)
    assert len(seen) == 1  # de la caché: no se paga dos veces


def test_the_whole_flow_with_claude_and_fal_stays_within_the_caps(tmp_path, cfg, monkeypatch):
    seen_claude: list = []
    seen_fal: list = []
    plan = {
        "room": "an empty living room with white walls",
        "pieces": [
            {
                "piece": "a sofa against the wall",
                "kinds": ["sofa"],
                "query": PRODUCTS["100.000.01"][3],
            },
            {"piece": "a bed", "kinds": ["bed"], "query": "Type: bed"},  # el catálogo no tiene
        ],
    }
    choice = {
        "choices": [{"piece": 1, "id": "100.000.01", "why": "red is bold"}],
        "why": "one bold piece",
    }
    scene = {
        "prompt": "Image 1 is the room. Put the sofa of image 2 against the back wall.",
        "placements": [],
    }
    claude = claude_handler(seen_claude, [plan, choice, scene])
    fal = fal_handler(seen_fal)

    def route(request: httpx.Request) -> httpx.Response:
        return claude(request) if request.url.host == "api.anthropic.com" else fal(request)

    monkeypatch.setattr(http, "TRANSPORT", httpx.MockTransport(route))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("FAL_KEY", "fal-test")
    photo = tmp_path / "vacio.jpg"
    Image.new("RGB", (300, 200), (220, 215, 210)).save(photo)

    cfg.furnish.generator = "nano_banana_2"
    with pytest.raises(PaidCallsDisabled):  # sin permiso, nada pago sale
        run_flow(photo, "un living con un sofá rojo", cfg, tmp_path / "run0", log=lambda _: None)
    assert not seen_claude

    cfg.budget.allow_paid = True
    out = tmp_path / "run"
    run = run_flow(photo, "un living con un sofá rojo", cfg, out, log=lambda _: None)
    assert len(seen_claude) == 3 and (out / "final.png").exists()
    assert [_images_and_notes(b)[0] for b in seen_claude][::2] == [
        1,
        2,
    ]  # sin vistas: igual que antes
    assert run.data["retrieve"]["empty"] == ["a bed"]
    assert [h.id for h in run.chosen()] == ["100.000.01"]
    spent = Ledger(cfg.budget.ledger, 1.0, "anthropic").spent()
    assert spent == pytest.approx(3 * (10000 * 4 + 1000 * 20) / 1e6)
    assert Ledger(cfg.budget.ledger, 0.1, "fal").spent() == pytest.approx(0.08)

    # Con tope de productos en la imagen, el prompt y el modelo de imagen reciben solo los
    # primeros; el resto queda en la lista (acá hay uno solo: nada cambia)
    assert "left_out_of_image" not in run.data["scene"]

    # La misma carpeta con el mismo pedido se retoma sin llamar a nadie; con otro pedido se
    # rechaza: devolvería la lista y la imagen del pedido anterior como si fueran del nuevo.
    run_flow(photo, "un living con un sofá rojo", cfg, out, log=lambda _: None)
    assert len(seen_claude) == 3
    with pytest.raises(ValueError, match="another request"):
        run_flow(photo, "un comedor para ocho", cfg, out, log=lambda _: None)
    assert json.loads((out / "request.json").read_text())["request"] == "un living con un sofá rojo"

    # El tope de fal (US$0,10) deja una sola imagen: la segunda se corta antes de salir.
    with pytest.raises(BudgetExceeded):
        run_flow(photo, "otro pedido", cfg, tmp_path / "run2", log=lambda _: None)


def _images_and_notes(body: dict) -> tuple[int, str]:
    blocks = body["messages"][0]["content"]
    texts = " ".join(b["text"] for b in blocks if b["type"] == "text")
    return sum(b["type"] == "image" for b in blocks), texts


def test_another_view_of_the_room_goes_to_claude_but_not_to_the_image_model(
    tmp_path, cfg, monkeypatch
):
    seen_claude: list = []
    seen_fal: list = []
    plan = {
        "room": "a long empty living room",
        "pieces": [{"piece": "a sofa", "kinds": ["sofa"], "query": PRODUCTS["100.000.01"][3]}],
    }
    choice = {"choices": [{"piece": 1, "id": "100.000.01", "why": "red"}], "why": "bold"}
    scene = {"prompt": "Image 1 is the room. Add the sofa of image 2.", "placements": []}
    claude = claude_handler(seen_claude, [plan, choice, scene])
    fal = fal_handler(seen_fal)
    monkeypatch.setattr(
        http,
        "TRANSPORT",
        httpx.MockTransport(lambda r: claude(r) if r.url.host == "api.anthropic.com" else fal(r)),
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("FAL_KEY", "fal-test")
    photo, other = tmp_path / "vista1.jpg", tmp_path / "vista2.jpg"
    Image.new("RGB", (300, 200), (220, 215, 210)).save(photo)
    Image.new("RGB", (300, 200), (200, 205, 210)).save(other)
    cfg.furnish.generator = "nano_banana_2"
    cfg.budget.allow_paid = True

    out = tmp_path / "run"
    run = run_flow(photo, "un sofá", cfg, out, log=lambda _: None, views=[other])
    assert (out / "room_2.jpg").exists() and run.views == [out / "room_2.jpg"]
    assert json.loads((out / "request.json").read_text())["views"] == [str(other)]

    (n_plan, t_plan), (n_choose, t_choose), (n_scene, t_scene) = map(_images_and_notes, seen_claude)
    candidates = len(run.data["retrieve"]["pieces"][0]["candidates"])
    assert n_plan == 2 and "Image 2 is another photo of this same room" in t_plan
    assert n_choose == 1 + candidates + 1 and f"Image {candidates + 2} is another" in t_choose
    assert n_scene == 3 and "Image 3 is another" in t_scene and "do not mention" in t_scene
    assert all(run.data[k]["views"] == 1 for k in ("plan", "choose", "scene"))
    payload = next(x[1] for x in seen_fal if x[0] == "payload")
    assert len(payload["image_urls"]) == 2  # la foto que se amobla y el sofá, sin la otra vista


def test_the_llm_gets_the_measures_the_catalog_has():
    def hit(dims):
        return Hit("x", "X", "rug", dims, "items.jsonl", [], "", None)

    full = {"width": 220, "depth": 90, "height": 80}
    assert size_text(hit(full)) == "220 cm wide, 90 cm deep, 80 cm high"  # como antes
    assert size_text(hit({"width": 140, "depth": 200})) == "140 cm wide, 200 cm deep"  # alfombra
    assert size_text(hit(None)) == "size unknown"  # los asientos: el dataset no trae medidas


def test_scene_prompt_v2_takes_the_same_inputs_as_v1():
    from tests.conftest import ROOT

    filled = {}
    for name in ("scene_prompt_v1.md", "src/amoblai/prompts/scene_prompt_v2.md"):
        tmpl = load_prompt(name, ROOT)
        filled[tmpl.version] = tmpl.fill(request="un sofá", room="a room", products="image 2. x")
    assert set(filled) == {"scene_prompt_v1", "scene_prompt_v2"}
    assert all('"prompt"' in t and "image 2. x" in t for t in filled.values())


def test_the_image_shows_at_most_the_products_the_image_model_takes(tmp_path, cfg):
    """El plan ordena las piezas por importancia: las que pasan el tope quedan fuera de la imagen
    (el prompt y las fotos que van al modelo), no de la lista de compra."""
    from amoblai.furnish import flow

    def hit(pid: str) -> dict:
        return {
            "id": pid,
            "name": pid,
            "category": "sofa",
            "dimensions_cm": None,
            "source": "x",
            "photos": [f"{pid}.jpg"],
            "description": f"Type: sofa, {pid}",
            "score": 0.9,
            "kind": "sofa",
        }

    cfg.furnish.scene_llm, cfg.furnish.scene_prompt = False, "scene_prompt_libre_v4.md"
    cfg.furnish.max_image_products = 2
    run = flow.Run(cfg, tmp_path, "tres sofás", log=lambda _: None)
    pieces = [{"piece": f"sofá {n}", "kinds": ["sofa"], "query": "q"} for n in (1, 2, 3)]
    run.data["plan"] = {"answer": {"room": "a room", "pieces": pieces}}
    run.data["retrieve"] = {
        "pieces": [
            {"piece": p["piece"], "spec": p, "candidates": [hit(f"s{n}")]}
            for n, p in enumerate(pieces, 1)
        ]
    }
    run.data["choose"] = {"answer": {"choices": [{"piece": n, "id": f"s{n}"} for n in (1, 2, 3)]}}
    scene = flow._scene(run)
    assert scene["left_out_of_image"] == ["sofá 3"]
    assert "s1" in scene["answer"]["prompt"] and "image 3" in scene["answer"]["prompt"]
    assert "image 4" not in scene["answer"]["prompt"]  # the third product is not in the image
    assert [h.id for h in flow._in_image(run, run.chosen())] == ["s1", "s2"]
    assert len(run.chosen()) == 3  # the shopping list keeps the three


def test_without_a_search_the_whole_catalog_goes_in_the_prompt_as_a_cached_block(
    tmp_path, cfg, monkeypatch
):
    seen: list = []
    plan = {
        "room": "an empty living room with white walls",
        "pieces": [
            {"piece": "a sofa against the wall", "kinds": ["sofa"], "query": "Type: sofa"},
        ],
    }
    choice = {"choices": [{"piece": 1, "id": "100.000.02", "why": "calm"}], "why": "one piece"}
    monkeypatch.setattr(
        http, "TRANSPORT", httpx.MockTransport(claude_handler(seen, [plan, choice]))
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    photo = tmp_path / "vacio.jpg"
    Image.new("RGB", (300, 200), (220, 215, 210)).save(photo)
    cfg.rag.mode = "whole_catalog"
    cfg.furnish.steps = ["plan", "retrieve", "choose"]
    cfg.budget.allow_paid = True
    out = tmp_path / "run"
    run = run_flow(photo, "un living con un sofá", cfg, out, log=lambda _: None)

    blocks = seen[1]["messages"][0]["content"]
    # the catalog first, whole and marked for the cache; then the room, the only photo
    assert [b["type"] for b in blocks] == ["text", "image", "text"]
    assert blocks[0]["cache_control"] == {"type": "ephemeral"}
    assert blocks[0]["text"].startswith("CATALOG:")
    assert blocks[0]["text"].count("\n[100.") == 7  # every product of the index, once
    assert "## sofa (2 products)" in blocks[0]["text"]
    assert "cache_control" not in blocks[-1]
    # each piece lists the ids its hard filters let through: here, the two sofas
    ids = blocks[-1]["text"].split("ids: ")[1].splitlines()[0].split(", ")
    assert sorted(ids) == ["100.000.01", "100.000.02"]
    assert [h.id for h in run.chosen()] == ["100.000.02"]
    assert not list(out.glob("2_candidates*.jpg"))  # no contact sheet of a whole kind

    # an id from outside the piece's list is refused, as with the search
    seen.clear()
    choice["choices"][0]["id"] = "100.000.03"
    with pytest.raises(ProviderError, match="not a candidate"):
        run_flow(photo, "un living con un sofá", cfg, tmp_path / "run2", log=lambda _: None)


def test_cached_input_has_its_own_price():
    usage = {
        "input_tokens": 1000,
        "cache_creation_input_tokens": 300_000,
        "cache_creation": {
            "ephemeral_5m_input_tokens": 100_000,
            "ephemeral_1h_input_tokens": 200_000,
        },
        "cache_read_input_tokens": 400_000,
        "output_tokens": 2000,
    }
    prices = {"input": 4.0, "output": 20.0}
    cache = {"cache_read": 0.2, "cache_write_5m": 5.0, "cache_write_1h": 8.0}
    assert claude_cost({"usd_per_m": {**prices, **cache}}, usage) == pytest.approx(
        (1000 * 4 + 100_000 * 5 + 200_000 * 8 + 400_000 * 0.2 + 2000 * 20) / 1e6
    )
    # a model with no cache prices: every input token at the plain price
    assert claude_cost({"usd_per_m": prices}, usage) == pytest.approx(
        (701_000 * 4 + 2000 * 20) / 1e6
    )
    assert text_block("x", "1h")["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in text_block("x")


def test_what_the_size_filter_changes_on_saved_plans(tmp_path, cfg):
    from amoblai.evaluation.endtoend import size_filter_effect

    run = tmp_path / "variante" / "ambiente"
    run.mkdir(parents=True)
    pieces = [
        # the three-seat sofa is 200 cm wide: out with a 150 cm limit (plus the 15% slack);
        # the two-seat one has no size in the catalog, so the filter can't take it out
        {"piece": "a sofa", "kinds": ["sofa"], "query": "Type: sofa", "max_width_cm": 150},
        {"piece": "a chair", "kinds": ["dining chair"], "query": "Type: chair"},  # no limit
    ]
    (run / "1_searches.json").write_text(json.dumps({"answer": {"pieces": pieces}}))
    assert size_filter_effect(cfg, tmp_path / "variante") == {
        "piezas": 2,
        "piezas_con_limite": 1,
        "productos_del_kind_que_pasan": 0.5,
        "piezas_donde_cambia_algun_candidato": 1,
        "candidatos": 2,
        "candidatos_reemplazados": 1,
        "candidatos_sin_ninguna_medida": 1,
    }
