import json

import pytest
import yaml
from roomrag.catalog import load_catalog

from amoblai.consultas import check_query
from amoblai.consultas import validate as validate_queries
from amoblai.descripciones import check_text, make_batches, validate

SAMPLE = (
    "Type: wide lounge accent chair\nUse: lounging, reading; living room, bedroom, reading nook\n"
    "Style: contemporary, modern, minimalist\nMaterials: felt-like woven fabric upholstery, brushed "
    "stainless steel wire base\nColors: light warm grey, brushed silver\nShape: tall flat upright "
    "back, low wide seat with flared wing-like arms that slope down at the ends, loose seat cushion, "
    "crossed sled-style wire legs, sculptural body on a light open base\nFeel: relaxed, sculptural, "
    "airy, inviting\nGoes with: exposed brick, warm wood, white walls, brass or chrome accents; loft, "
    "modern or industrial rooms"
)


def test_items_only_in_scope_with_roomrag_types(catalog_dir):
    items = {
        json.loads(x)["id"]: json.loads(x)
        for x in (catalog_dir / "items.jsonl").read_text().splitlines()
    }
    assert "100.000.07" not in items  # la lámpara queda afuera
    assert items["100.000.04"]["category"] == "chair" and items["100.000.04"]["kind"] == "armchair"
    assert items["100.000.05"]["kind"] == "coffee table"
    assert items["100.000.01"]["dimensions_cm"] == {"width": 200.0, "depth": 90.0, "height": 80.0}
    assert items["100.000.06"]["dimensions_cm"] == {"width": 133.0, "depth": 195.0}
    assert items["100.000.02"]["dimensions_cm"] is None
    assert items["100.000.01"]["colors"] == ["Red", "oak"]


def test_catalog_files_apply_corrections_and_load_in_roomrag(catalog_dir):
    kinds = yaml.safe_load((catalog_dir / "kinds.yaml").read_text())
    assert kinds["100.000.08"] == "desk"
    cat = {p.id: p for p in load_catalog(catalog_dir / "ikea.yaml", ".").products}
    assert cat["100.000.08"].category == "desk" and cat["100.000.08"].kind == "desk"
    assert len(cat) == 7
    rows = (catalog_dir / "descripciones.jsonl").read_text().splitlines()
    assert {json.loads(r)["id"] for r in rows} == set(cat)


def test_check_text_accepts_the_reference_format():
    assert check_text(SAMPLE) == ([], [])


@pytest.mark.parametrize(
    ("text", "error"),
    [
        (SAMPLE.replace("Feel:", "Mood:"), "Feel"),
        (SAMPLE + " IKEA", "marca"),
        (SAMPLE.replace("loft,", "loft 90 cm,"), "medidas"),
        (SAMPLE.replace("contemporary, modern, minimalist", "futuristic"), "Style"),
        ("Type: chair", "líneas"),
    ],
)
def test_check_text_errors(text, error):
    errors, _ = check_text(text)
    assert any(error in e for e in errors), errors


def test_check_text_warns_on_negations_and_trade_names():
    errors, warnings = check_text(SAMPLE.replace("relaxed", "not stiff"), name="KIVIK")
    assert not errors and any("negación" in w for w in warnings)
    errors, _ = check_text(SAMPLE.replace("loft", "KIVIK"), name="KIVIK")
    assert any("nombre comercial" in e for e in errors)


def test_validate_lot_against_batch(tmp_path, catalog_dir):
    items = [json.loads(x) for x in (catalog_dir / "items.jsonl").read_text().splitlines()]
    (batch,) = make_batches(items[:1], tmp_path / "lotes", 10, catalog_dir)
    pid = items[0]["id"]
    out = tmp_path / "out.jsonl"
    out.write_text(
        json.dumps({"id": pid, "kind": "bed", "text": SAMPLE, "by": "x", "prompt": "p"}) + "\n"
    )
    errors, _ = validate(out, batch)
    assert any("kind" in e for e in errors)
    out.write_text(
        json.dumps({"id": pid, "kind": items[0]["kind"], "text": SAMPLE, "by": "x", "prompt": "p"})
        + "\n"
    )
    assert validate(out, batch) == ([], [])


def test_room_queries_validation(tmp_path):
    batch = tmp_path / "lote.json"
    batch.write_text(
        json.dumps([{"room_id": "r1", "photo": "x.jpg"}, {"room_id": "r2", "photo": "y.jpg"}])
    )
    query = SAMPLE.replace("Type: wide lounge accent chair", "Type: armchair, wide lounge")
    out = tmp_path / "out.json"
    out.write_text(
        json.dumps(
            {
                "r1": {
                    "room": "a living room",
                    "pieces": [{"piece": "the chair", "kinds": ["chair"], "query": query}],
                }
            }
        )
    )
    errors = validate_queries(out, batch)
    assert any("r2: falta" in e for e in errors) and any("kinds" in e for e in errors)
    assert check_query(query) == []
