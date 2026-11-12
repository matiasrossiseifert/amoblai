"""Las métricas de la imagen generada y de la respuesta en texto, sin modelos (las piezas puras)."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from amoblai.catalog.loader import Product
from amoblai.evaluation.answer import answer_text, faithfulness
from amoblai.evaluation.image import (
    Det,
    assign,
    detector_labels,
    inside,
    iou,
    nms,
    rank_among,
)
from amoblai.furnish.room import preservation
from tests.conftest import ROOT


def test_boxes_overlap_and_nms_keeps_the_best():
    a, b = (0, 0, 10, 10), (5, 0, 15, 10)
    assert iou(a, a) == 1.0 and abs(iou(a, b) - 50 / 150) < 1e-9
    assert inside((2, 2, 4, 4), a) == 1.0 and inside(b, a) == 0.5
    dets = [Det(a, "sofa", "sofa", 0.5), Det((1, 0, 11, 10), "sofa", "couch", 0.9)]
    assert [d.score for d in nms(dets, 0.5)] == [0.9]


def test_every_category_phrase_goes_to_its_category():
    labels = detector_labels(ROOT / "datos" / "configs" / "categories.yaml")
    assert labels["couch"] == "sofa" and labels["armchair"] == "armchair"
    assert labels["carpet"] == "rug" and labels["cushion"] == "deco"


def test_a_crop_ranks_its_product_and_ties_do_not_count_against_it():
    cands = {
        "a": np.array([1.0, 0.0]),
        "b": np.array([0.0, 1.0]),
        "a2": np.array([1.0, 0.0]),  # la misma foto en otro SKU
    }
    r = rank_among(np.array([0.9, 0.1]), {"a"}, cands)
    assert r["rank"] == 1 and r["n"] == 3
    assert rank_among(np.array([0.1, 0.9]), {"a"}, cands)["rank"] == 2
    assert rank_among(np.array([1.0, 0.0]), {"zzz"}, cands)["rank"] is None


def test_products_get_a_detection_of_their_category_or_family():
    def product(pid, tp):
        return Product(Path("."), {"id": pid, "category": tp, "kind": tp, "category_tp": tp})

    sofa, chair, table = product("s", "sofa"), product("c", "armchair"), product("t", "table")
    dets = [
        Det((0, 0, 50, 50), "sofa", "sofa", 0.8),
        Det((60, 0, 90, 40), "sofa", "couch", 0.4),  # el sillón, visto como sofá
        Det((0, 60, 40, 90), "table", "table", 0.7),
    ]
    got = assign([sofa, chair, table], dets, lambda p, d: 0.0)
    assert got == {"s": 0, "t": 2, "c": 1}


def test_the_same_room_is_preserved_and_a_different_one_is_not():
    rng = np.random.default_rng(0)
    base = Image.fromarray((rng.random((400, 600, 3)) * 255).astype("uint8")).resize((1200, 800))
    furnished = base.copy()
    ImageDraw.Draw(furnished).rectangle((300, 400, 700, 700), fill=(200, 30, 30))
    same = preservation(base, furnished, [(300, 400, 700, 700)])
    noise = (np.random.default_rng(1).random((400, 600, 3)) * 255).astype("uint8")
    other = preservation(base, Image.fromarray(noise).resize((1200, 800)), [])
    turned = preservation(base, base.transpose(Image.Transpose.ROTATE_180), [])
    assert same["ssim_fuera_de_los_muebles"] > 0.95 > other["ssim_fuera_de_los_muebles"]
    assert same["sift_reencontrados"] > 10 * other.get("sift_reencontrados", 0.0)
    # SIFT reencuentra una foto girada (es invariante a la rotación): la cámara se movió
    assert same["sift_desplazamiento_mediano"] < 0.01 < turned["sift_desplazamiento_mediano"]


def test_faithfulness_counts_supported_factual_claims():
    claims = [
        {"claim": "white sofa", "about": "1", "supported": True},
        {"claim": "oak legs", "about": "1", "supported": False},
        {"claim": "long room", "about": "room", "supported": True},
    ]
    f = faithfulness(claims)
    assert f["faithfulness"] == round(2 / 3, 4) and f["sobre_el_ambiente"] == 1.0
    assert f["no_sostenidas"] == ["oak legs"]
    assert faithfulness([])["faithfulness"] is None
    text = answer_text({"choices": [{"id": "1", "why": "it fits"}], "why": "all together"})
    assert text == "- 1: it fits\n- The combination: all together"


def test_separability_counts_neighbours_of_the_same_kind():
    from amoblai.evaluation.space import separability

    v = np.array([[1, 0], [0.99, 0.1], [0, 1], [0.1, 0.99]], float)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    m = separability(v, ["sofa", "sofa", "rug", "rug"], ["sofa", "sofa", "rug", "rug"])
    assert m["vecino_mismo_kind"] == m["vecino_mismo_tipo"] == 1.0 and m["silhouette_kind"] > 0.5


def test_graded_relevance_scores_the_top3_and_checks_the_judge(tmp_path):
    import gzip
    import json

    from amoblai.evaluation.graded import score

    rows = [
        {
            "method": "m",
            "room_id": "r1",
            "piece": 0,
            "ranked": ["a", "b", "c", "d"],
            "relevant": ["b"],
        },
        {"method": "m", "room_id": "r2", "piece": 1, "ranked": ["e", "f", "g"], "relevant": []},
    ]
    run = tmp_path / "run"
    run.mkdir()
    (run / "rankings.jsonl.gz").write_bytes(
        gzip.compress("\n".join(json.dumps(r) for r in rows).encode())
    )
    answers = tmp_path / "graduada"
    answers.mkdir()
    (answers / "lote_01.json").write_text(
        json.dumps({"r1#0": {"a": 1, "b": 2, "c": 0}, "r2#1": {"e": 0, "f": 0, "g": 1}})
    )
    r = score(run, "m", answers)
    todas = r["consultas"]["todas"]
    assert todas["n"] == 2 and todas["util1"] == 0.5 and todas["util3"] == 1.0
    assert r["consultas"]["sin anotado"]["exacto3"] == 0.0
    assert r["acuerdo_con_gt"] == {"anotados_en_top3": 1, "anotado_con_2": 1.0, "otros_con_2": 0.0}


def test_an_armchair_takes_the_detection_that_looks_like_it_not_the_top_score():
    chair = Product(
        Path("."), {"id": "c", "category": "chair", "kind": "armchair", "category_tp": "armchair"}
    )
    dets = [
        Det((0, 0, 30, 30), "stool", "bar stool", 0.6),  # unas mesitas nido
        Det((40, 0, 90, 60), "chair", "chair", 0.4),  # el sillón
    ]
    looks = {0: 0.1, 1: 0.9}
    got = assign([chair], dets, lambda p, d: looks[dets.index(d)])
    assert got == {"c": 1}


def test_the_runs_page_reads_each_run_and_marks_reused_steps(tmp_path):
    import json

    from amoblai.furnish.viewer import build

    runs = tmp_path / "amoblar"
    plan = {
        "answer": {"room": "un cuarto", "pieces": [{"piece": "un sofá", "kinds": ["sofa"]}]},
        "cost_usd": 0.05,
        "prompt": "search_query_v3",
    }
    cands = {"pieces": [{"piece": "un sofá", "candidates": [{"id": "1", "name": "A"}]}]}
    choice = {"answer": {"choices": [{"piece": 1, "id": "1", "why": "va"}]}, "cost_usd": 0.04}
    for name in ("base", "base-libre"):
        d = runs / name
        d.mkdir(parents=True)
        (d / "request.json").write_text(json.dumps({"request": "un living"}))
        for f, data in (
            ("1_searches.json", plan),
            ("2_candidates.json", cands),
            ("3_choice.json", choice),
        ):
            (d / f).write_text(json.dumps(data))
    page = build(runs, root=tmp_path).read_text()
    data = json.loads(page[page.index("const DATA = ") + 13 : page.index(";\nconst e =")])
    by = {r["id"]: r for r in data["runs"]}
    assert by["base"]["cost"] == 0.09 and by["base-libre"]["cost"] == 0.0
    assert by["base-libre"]["steps"][0]["reused_from"] == "base"
    assert by["base"]["search"][0]["candidates"][0]["chosen"]


class TwoTriesGenerator:
    """Paid and fake: first another room (noise), then the user's room with a red box."""

    paid = True
    account = None

    def __init__(self, params, cfg, name):
        self.name, self.calls = name, 0

    def estimate_cost(self, images):
        return 0.01

    def generate(self, prompt, images, out):
        from amoblai.furnish.generate import Generated

        self.calls += 1
        room = Image.open(images[0]).convert("RGB")
        if self.calls == 1:
            noise = np.random.default_rng(7).random((40, 60, 3)) * 255
            img = Image.fromarray(noise.astype("uint8")).resize(room.size)
        else:
            img = room.copy()
            ImageDraw.Draw(img).rectangle((100, 200, 300, 400), fill=(200, 30, 30))
        dst = Path(out) / "final.png"
        img.save(dst)
        return Generated(dst, "fake", 0.01, "estimate", {})


def test_an_image_that_is_not_the_room_is_set_aside_and_tried_again(tmp_path, cfg):
    from amoblai.furnish import steps as st

    rng = np.random.default_rng(0)
    room = tmp_path / "room.jpg"
    Image.fromarray((rng.random((40, 60, 3)) * 255).astype("uint8")).resize((900, 600)).save(
        room, quality=95
    )
    cfg.furnish.generators["dos"] = {"kind": "tests.test_metrics:TwoTriesGenerator"}
    cfg.furnish.generator = "dos"
    cfg.budget.allow_paid = True
    cfg.budget.max_usd_total = 1.0
    cfg.budget.ledger = str(tmp_path / "gastos.jsonl")
    rec = st.generate(cfg, "amoblalo", room, [], tmp_path)
    assert [a["ok"] for a in rec["attempts"]] == [False, True]
    assert rec["room_check"]["image"] == "final_intento_2.png" and rec["cost_usd"] == 0.02
    assert Image.open(tmp_path / "final.png").getpixel((200, 300)) == (200, 30, 30)


def test_the_image_summary_adds_products_rooms_and_attempts_over_runs(tmp_path):
    from amoblai.evaluation.image import summary

    def run(name, products, attempts):
        d = tmp_path / name
        d.mkdir()
        rows = [
            {"detectado": rank is not None, "puesto": rank, "coseno": 0.5 if rank else None}
            for rank in products
        ]
        (d / "6_metricas_imagen.json").write_text(
            json.dumps({"productos": rows, "fidelidad": {"coseno_medio": 0.5}})
        )
        tries = [{"ok": ok, "cost_usd": 0.08} for ok in attempts]
        (d / "5_image.json").write_text(json.dumps({"attempts": tries, "room_check": tries[-1]}))
        return d

    # a: three products (two found, one of them the exact one), the room kept at the first try
    # b: one product, not found; the room lost in the three tries
    s = summary([run("b", [None], [False, False, False]), run("a", [1, 4, None], [True])])
    assert [r["corrida"] for r in s["por_corrida"]] == ["a", "b"]
    assert (s["productos"], s["detectados"], s["identificados"]) == (4, 2, 1)
    assert s["identificados@1"] == 0.25 and s["coseno_medio"] == 0.5
    assert (s["ambiente_conservado"], s["ambiente_al_primer_intento"], s["intentos"]) == (1, 1, 4)
    assert s["costo_usd"] == 0.32
