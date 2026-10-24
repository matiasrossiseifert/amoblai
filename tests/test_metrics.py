"""Las métricas de la imagen generada y de la respuesta en texto, sin modelos (las piezas puras)."""

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
    preservation,
    rank_among,
)
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
