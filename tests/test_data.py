import pickle

import pytest

from amoblai.categories import OTHER, CategoryMap
from amoblai.data.catalog import Catalog, parse_size
from amoblai.data.download import extract_safely
from amoblai.data.ikea import IkeaDataset
from amoblai.data.safe_pickle import load_pickle
from tests.conftest import ROOM_ID, ROOT


def test_safe_pickle_loads_builtin_types(tmp_path):
    path = tmp_path / "ok.p"
    path.write_bytes(pickle.dumps({"a": [1, "b", (2.0,)]}, protocol=2))
    assert load_pickle(path) == {"a": [1, "b", (2.0,)]}


class Evil:
    def __reduce__(self):
        return (print, ("pwned",))


def test_safe_pickle_rejects_arbitrary_callables(tmp_path):
    path = tmp_path / "evil.p"
    path.write_bytes(pickle.dumps(Evil()))
    with pytest.raises(pickle.UnpicklingError):
        load_pickle(path)


def test_dataset_joins_by_sku_and_dedupes(dataset_root):
    ds = IkeaDataset.load(dataset_root)
    assert len(ds.products) == 8
    # La anotación apunta a images/mirror/, pero se une por SKU con la carpeta real.
    assert all(p.image_paths for p in ds.products.values())
    # La copia idéntica en images/chair/ se descarta.
    assert len(ds.products["100.000.03"].image_paths) == 1
    assert ds.stats["duplicate_identical_images"] == 1
    # clock/ no son productos.
    assert "img1" not in ds.products


def test_dataset_ground_truth_comes_from_item_to_room(dataset_root):
    ds = IkeaDataset.load(dataset_root)
    room = ds.rooms[ROOM_ID]
    assert room.room_type == "Living Room"
    assert room.skus == {"100.000.01", "100.000.03", "100.000.05"}
    # Un ambiente anotado que no está en disco no aparece.
    assert "otro.jpg" not in ds.rooms


def test_description_is_cleaned(dataset_root):
    ds = IkeaDataset.load(dataset_root)
    assert ds.products["100.000.01"].description == "Un producto."


@pytest.mark.parametrize(
    ("size", "expected"),
    [
        ("90x200 cm", [90.0, 200.0]),
        ("80x50x171 cm", [80.0, 50.0, 171.0]),
        ("75 cm", [75.0]),
        ("150x200,50x80 cm", [150.0, 200.0]),
        ("250 mm", [25.0]),
        ("2 m", [200.0]),
        ("36 l", []),
        ("Standard King", []),
        ("", []),
    ],
)
def test_parse_size(size, expected):
    assert parse_size(size) == expected


def test_catalog_roundtrip_and_card(cfg, catalog, tmp_path):
    loaded = Catalog.load(cfg.paths.catalog_file, cfg.paths.raw_dir)
    assert len(loaded) == len(catalog)
    sofa = loaded.get("100.000.01")
    assert sofa.category == "sofa"
    card = sofa.card()
    assert card["medidas"] == "200x90x80 cm"
    assert "precio" not in card and "link" not in card
    assert loaded.get("100.000.07").category == OTHER
    assert loaded.image_path("100.000.01").exists()


def test_real_category_map_is_valid():
    cmap = CategoryMap.load(ROOT / "configs" / "categories.yaml")
    assert cmap.scope == ["sofa", "armchair", "chair", "table", "rug"]
    assert cmap.category_of_type("Coffee table") == "table"
    assert cmap.category_of_type("Swivel chair") == OTHER
    assert cmap.label_to_category["couch"] == "sofa"


def test_category_map_rejects_type_in_two_categories(tmp_path):
    path = tmp_path / "cats.yaml"
    path.write_text(
        "categories:\n"
        "  a: {detector_labels: [x], ikea_types: [T]}\n"
        "  b: {detector_labels: [y], ikea_types: [T]}\n"
    )
    with pytest.raises(ValueError):
        CategoryMap.load(path)


def test_extract_safely_rejects_traversal(tmp_path):
    import zipfile

    zpath = tmp_path / "x.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("ikea-abc/images/ok.jpg", b"1")
        zf.writestr("ikea-abc/README.md", b"no")
        zf.writestr("ikea-abc/images/../../../evil.txt", b"x")
    with pytest.raises(ValueError):
        extract_safely(zpath, tmp_path / "out")


def test_extract_safely_keeps_only_data(tmp_path):
    import zipfile

    zpath = tmp_path / "x.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("ikea-abc/images/a/ok.jpg", b"1")
        zf.writestr("ikea-abc/text_data/t.p", b"2")
        zf.writestr("ikea-abc/README.md", b"no")
    assert extract_safely(zpath, tmp_path / "out") == 2
    assert (tmp_path / "out" / "images" / "a" / "ok.jpg").exists()
    assert not (tmp_path / "out" / "README.md").exists()
