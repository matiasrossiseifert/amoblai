"""El catálogo ABO (selección, medidas, un producto por modelo) y la comparación de punta a punta
(la agregación del juez en los dos órdenes), sin red ni modelos."""

import json
from pathlib import Path

from amoblai.catalog import abo
from amoblai.evaluation import endtoend as e2e


def test_abo_kinds_come_from_type_and_name_and_skip_what_is_not_for_a_room():
    assert abo.guess_kind("SOFA", "Rivet Revolve Modern Sofa, 80in, Grey") == "sofa"
    assert abo.guess_kind("SOFA", "Stone & Beam Sleeper Sofa Bed") == "sofa bed"
    assert abo.guess_kind("CHAIR", "AmazonBasics Mid-Back Office Desk Chair") == "desk chair"
    assert abo.guess_kind("CHAIR", "Rivet Mid-Century Accent Chair") == "armchair"
    assert abo.guess_kind("TABLE", "Walnut Coffee Table") == "coffee table"
    assert abo.guess_kind("CHAIR", "Outdoor Patio Dining Chair") is None
    assert abo.guess_kind("LAMP", "Replacement Lamp Shade Kit") is None


def test_abo_variants_of_a_model_share_a_family():
    a = abo.family("Rivet", 'Rivet Revolve Modern Sofa, 80"W, Light Grey')
    b = abo.family("Rivet", 'Rivet Revolve Modern Sofa, 80"W, Navy Blue')
    c = abo.family("Rivet", "Rivet Emerly Sofa, Grey")
    assert a == b != c


def test_abo_dimensions_in_cm_width_the_longer_side_on_the_floor():
    listing = {
        "item_dimensions": {
            "length": {"normalized_value": {"unit": "inches", "value": 30}},
            "width": {"normalized_value": {"unit": "inches", "value": 80}},
            "height": {"normalized_value": {"unit": "inches", "value": 34}},
        }
    }
    assert abo.dimensions(listing) == {"width": 203.2, "depth": 76.2, "height": 86.4}
    assert abo.dimensions({}) is None


def _run(root: Path, name: str, slug: str, ids: list[str]) -> None:
    d = root / name / slug
    d.mkdir(parents=True)
    cands = {
        "pieces": [
            {
                "spec": {"piece": f"p{n}"},
                "candidates": [
                    {
                        "id": i,
                        "name": i,
                        "category": "sofa",
                        "dimensions_cm": None,
                        "source": "x",
                        "photos": ["room.jpg"],
                        "description": f"Type: {i}\n",
                        "score": 0.5,
                    }
                ],
            }
            for n, i in enumerate(ids)
        ]
    }
    choice = {
        "answer": {"choices": [{"piece": n + 1, "id": i, "quantity": 1} for n, i in enumerate(ids)]}
    }
    (d / "2_candidates.json").write_text(json.dumps(cands))
    (d / "3_choice.json").write_text(json.dumps(choice))


def test_a_variant_wins_a_room_only_if_it_wins_in_both_orders(tmp_path, monkeypatch):
    rooms = [
        {"slug": "r1", "foto": "x.jpg", "pedido": "p"},
        {"slug": "r2", "foto": "x.jpg", "pedido": "p"},
    ]
    for slug in ("r1", "r2"):
        _run(tmp_path, "a", slug, ["a1", "a2"])
        _run(tmp_path, "b", slug, ["b1"])

    def judge(cfg, llm, room, la, lb):
        first_is_a = la[0]["id"].startswith("a")
        side = {"grades": [2] * len(la), "request": 4, "room": 4, "together": 4}
        other = {"grades": [1] * len(lb), "request": 3, "room": 3, "together": 3}
        if room["slug"] == "r1":  # prefers a in both orders
            return {
                "A": side,
                "B": other,
                "preferred": "A" if first_is_a else "B",
                "cost_usd": 0.01,
            }
        return {"A": side, "B": other, "preferred": "A", "cost_usd": 0.01}  # position bias

    monkeypatch.setattr(e2e, "judge", judge)
    res = e2e.compare(None, {}, rooms, tmp_path, "a", "b")
    assert res["resumen"]["a"]["gana"] == 1 and res["resumen"]["b"]["gana"] == 0
    assert res["empates"] == 1 and res["acuerdo_entre_ordenes"] == 0.5
    assert res["votos_por_posicion_A"] == 0.75
    assert res["resumen"]["a"]["productos_por_lista"] == 2.0 and res["costo_usd"] == 0.04
