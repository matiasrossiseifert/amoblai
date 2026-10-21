import io
import json

import httpx
import pytest
from PIL import Image
from roomrag import http
from roomrag.budget import BudgetExceeded, Ledger, PaidCallsDisabled
from roomrag.flow import run_flow
from roomrag.prompts import load_prompt
from roomrag.search import Hit
from roomrag.steps import _size

from amoblai.evaluacion import Method, default_methods, run_eval
from amoblai.generacion import FalNanoBanana
from amoblai.reporte import build_report
from tests.conftest import PRODUCTS, ROOM_ID


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
    methods = [Method("hashing", "description", "kind"), Method("hashing", "seller", "none")]
    run = run_eval(cfg, qpath, dataset_root, tmp_path / "evals", methods, name="t", n_boot=50)
    m = json.loads((run / "metricas.json").read_text())
    ours = m["hashing|description|filtro-kind"]
    assert ours["answerable"] == 3  # el sillón no está anotado en el ambiente: sin relevantes
    assert ours["hit@1"] == 1.0 and ours["recall_item@10"] == 1.0
    assert ours["azar_hit@1"] < 1.0
    assert (run / "rankings.jsonl").exists() and json.loads((run / "corrida.json").read_text())[
        "rooms"
    ] == 1
    assert len(default_methods(["hashing", "bge"])) == 2 * 2 * 3 + 1
    written = build_report(tmp_path / "evals", tmp_path / "reporte", v0_runs=tmp_path / "nada")
    assert "Retrieval por texto" in written["readme"].read_text()


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
    assert _size(hit(full)) == "220 cm wide, 90 cm deep, 80 cm high"  # como antes
    assert _size(hit({"width": 140, "depth": 200})) == "140 cm wide, 200 cm deep"  # alfombra
    assert _size(hit(None)) == "size unknown"  # los asientos: el dataset no trae medidas


def test_scene_prompt_v2_takes_the_same_inputs_as_v1():
    from tests.conftest import ROOT

    filled = {}
    for name in ("scene_prompt_v1.md", "src/amoblai/prompts/scene_prompt_v2.md"):
        tmpl = load_prompt(name, ROOT)
        filled[tmpl.version] = tmpl.fill(request="un sofá", room="a room", products="image 2. x")
    assert set(filled) == {"scene_prompt_v1", "scene_prompt_v2"}
    assert all('"prompt"' in t and "image 2. x" in t for t in filled.values())
