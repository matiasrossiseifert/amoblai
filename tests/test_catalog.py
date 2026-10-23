import json

import pytest
import yaml

from amoblai.catalog.descriptions import check_text, make_batches, validate
from amoblai.catalog.loader import load_catalog
from amoblai.evaluation.queries import check_query
from amoblai.evaluation.queries import validate as validate_queries

SAMPLE = (
    "Type: wide lounge accent chair\nUse: lounging, reading; living room, bedroom, reading nook\n"
    "Style: contemporary, modern, minimalist\nMaterials: felt-like woven fabric upholstery, brushed "
    "stainless steel wire base\nColors: light warm grey, brushed silver\nShape: tall flat upright "
    "back, low wide seat with flared wing-like arms that slope down at the ends, loose seat cushion, "
    "crossed sled-style wire legs, sculptural body on a light open base\nFeel: relaxed, sculptural, "
    "airy, inviting\nGoes with: exposed brick, warm wood, white walls, brass or chrome accents; loft, "
    "modern or industrial rooms"
)


def test_items_only_in_scope_with_the_catalog_types(catalog_dir):
    items = {
        json.loads(x)["id"]: json.loads(x)
        for x in (catalog_dir / "items.jsonl").read_text().splitlines()
    }
    assert "100.000.07" not in items  # la cama queda afuera
    assert items["100.000.04"]["category"] == "chair" and items["100.000.04"]["kind"] == "armchair"
    assert items["100.000.05"]["kind"] == "coffee table"
    assert items["100.000.01"]["dimensions_cm"] == {"width": 200.0, "depth": 90.0, "height": 80.0}
    assert items["100.000.06"]["dimensions_cm"] == {"width": 133.0, "depth": 195.0}
    assert items["100.000.02"]["dimensions_cm"] is None
    assert items["100.000.01"]["colors"] == ["Red", "oak"]


def test_catalog_files_apply_corrections_and_load(catalog_dir):
    kinds = yaml.safe_load((catalog_dir / "kinds.yaml").read_text())
    assert kinds["100.000.08"] == "desk"
    cat = {p.id: p for p in load_catalog(catalog_dir / "ikea.yaml", ".").products}
    assert cat["100.000.08"].category == "desk" and cat["100.000.08"].kind == "desk"
    assert len(cat) == 7
    rows = (catalog_dir / "descripciones.jsonl").read_text().splitlines()
    assert {json.loads(r)["id"] for r in rows} == set(cat)


def test_a_product_whose_photo_does_not_show_it_is_left_out(catalog_dir):
    from amoblai.catalog.ikea import write_catalog_files

    fixes = catalog_dir / "correcciones.yaml"
    fixes.write_text(fixes.read_text() + '"100.000.06": {excluir: true, motivo: "otra foto"}\n')
    stats = write_catalog_files(
        catalog_dir / "items.jsonl",
        catalog_dir / "descripciones",
        catalog_dir / "descripciones.jsonl",
        catalog_dir / "kinds.yaml",
        fixes,
        catalog_dir / "ikea.yaml",
    )
    cat = {p.id for p in load_catalog(catalog_dir / "ikea.yaml", ".").products}
    assert stats["excluded"] == 1 and "100.000.06" not in cat and len(cat) == 6


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


@pytest.mark.parametrize(
    ("ikea_type", "category", "kind"),
    [
        ("Swivel chair", "chair", "desk chair"),
        ("LED work,wall lamp", "lamp", "desk lamp"),  # la primera palabra de la lista
        ("Ceiling,wall lamp", "lamp", "ceiling lamp"),
        ("Floor,reading lamp", "lamp", "floor lamp"),
        ("Cushion cover", "deco", "cushion"),
        ("Artificial potted plant", "deco", "plant"),
        ("Hanging planter", "deco", "plant pot"),
        ("Frame for 2 pictures", "deco", "picture frame"),
        ("Lantern for block candle", "deco", "candle holder"),
        ("TV bench", "cabinet", "TV stand"),
        ("Chest of 3 drawers", "dresser", "dresser"),
    ],
)
def test_default_kind_of_the_new_types(ikea_type, category, kind):
    from amoblai.catalog.ikea import default_kind
    from amoblai.dataset.products import Product

    assert default_kind(Product(sku="1", name="X", type=ikea_type, category=category)) == kind


def test_storage_furniture_keeps_only_its_width():
    from amoblai.catalog.ikea import dimensions
    from amoblai.dataset.products import Product

    def dims(category, numbers):
        return dimensions(Product(sku="1", name="X", type="T", category=category, dims_cm=numbers))

    assert dims("shelf", [200.0, 237.0, 30.0]) == {"width": 200.0}  # ancho x alto x prof.
    assert dims("dresser", [80.0, 78.0]) == {"width": 80.0}  # ancho x alto
    assert dims("desk", [120.0, 60.0]) == {"width": 120.0, "depth": 60.0}
    assert dims("lamp", [38.0]) is None and dims("deco", [50.0, 50.0]) is None


def test_only_the_products_without_a_description_go_to_new_lots(tmp_path, catalog_dir):
    from amoblai.catalog.descriptions import described

    items = [json.loads(x) for x in (catalog_dir / "items.jsonl").read_text().splitlines()]
    done = described(sorted((catalog_dir / "descripciones").glob("lote_*.jsonl")))
    assert done == {it["id"] for it in items}
    (batch,) = make_batches(items[:2], tmp_path / "lotes", 10, catalog_dir, first=9)
    assert batch.name == "lote_09.json"


def test_a_second_pass_of_queries_goes_after_the_first(tmp_path):
    from amoblai.evaluation.queries import EXPANSION_TYPES, extend, load_queries

    queries = tmp_path / "consultas.json"
    first = {"piece": "sofa", "kinds": ["sofa"], "query": "Type: sofa"}
    queries.write_text(
        json.dumps({"_meta": {"prompt": "v1", "rooms": 1}, "r1": {"room": "a", "pieces": [first]}})
    )
    part = tmp_path / "lote_01.json"
    lamp = {"piece": "lamp", "kinds": ["pendant lamp"], "query": "Type: pendant lamp"}
    part.write_text(
        json.dumps({"r1": {"room": "b", "pieces": [lamp]}, "r2": {"room": "c", "pieces": []}})
    )
    assert extend(queries, [part], "v2", "test") == 1
    rooms = load_queries(queries)
    assert rooms["r1"]["room"] == "a" and rooms["r1"]["pieces"] == [first, {**lamp, "prompt": "v2"}]
    assert rooms["r2"]["pieces"] == []
    meta = json.loads(queries.read_text())["_meta"]
    assert meta["passes"] == [{"prompt": "v2", "by": "test", "pieces": 1}] and meta["rooms"] == 2
    assert "lamp" in EXPANSION_TYPES


def test_v2_query_lots_carry_their_kinds(tmp_path):
    from amoblai.evaluation.queries import EXPANSION_TYPES, make_batches

    (batch,) = make_batches([{"room_id": "r1", "photo": "x.jpg"}], tmp_path, 5, EXPANSION_TYPES)
    query = SAMPLE.replace("Type: wide lounge accent chair", "Type: cushion, square linen")
    out = tmp_path / "out.json"
    piece = {"piece": "cushion", "kinds": ["cushion"], "query": query}
    out.write_text(json.dumps({"r1": {"room": "a living room", "pieces": [piece]}}))
    assert validate_queries(out, batch) == []
    piece["kinds"] = ["sofa"]  # fuera de esta pasada
    out.write_text(json.dumps({"r1": {"room": "a living room", "pieces": [piece]}}))
    assert any("kinds" in e for e in validate_queries(out, batch))
