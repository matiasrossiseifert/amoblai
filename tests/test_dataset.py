import pickle
import zipfile

import pytest

from amoblai.dataset.categories import OTHER, CategoryMap
from amoblai.dataset.download import extract_safely
from amoblai.dataset.ikea import IkeaDataset
from amoblai.dataset.products import parse_size
from amoblai.dataset.safe_pickle import load_pickle
from tests.conftest import IN_ROOM, PRODUCTS, ROOM_ID, ROOT


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


def test_dataset_joins_by_sku_and_the_ground_truth_comes_from_item_to_room(dataset_root):
    ds = IkeaDataset.load(dataset_root)
    assert set(ds.products) == set(PRODUCTS)
    assert all(p.image_paths for p in ds.products.values())
    assert ds.rooms[ROOM_ID].skus == set(IN_ROOM)


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


def test_the_category_map_of_the_scope_is_valid():
    cmap = CategoryMap.load(ROOT / "datos" / "configs" / "categories.yaml")
    assert cmap.scope == ["sofa", "armchair", "chair", "table", "rug"]
    assert cmap.category_of_type("Coffee table") == "table"
    assert cmap.category_of_type("Swivel chair") == OTHER


def test_a_type_in_two_categories_is_an_error(tmp_path):
    path = tmp_path / "cats.yaml"
    path.write_text(
        "categories:\n"
        "  a: {detector_labels: [x], ikea_types: [T]}\n"
        "  b: {detector_labels: [y], ikea_types: [T]}\n"
    )
    with pytest.raises(ValueError):
        CategoryMap.load(path)


def test_the_zip_is_extracted_safely(tmp_path):
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("ikea-abc/images/ok.jpg", b"1")
        zf.writestr("ikea-abc/images/../../../evil.txt", b"x")
    with pytest.raises(ValueError):
        extract_safely(bad, tmp_path / "out1")
    good = tmp_path / "good.zip"
    with zipfile.ZipFile(good, "w") as zf:
        zf.writestr("ikea-abc/images/a/ok.jpg", b"1")
        zf.writestr("ikea-abc/text_data/t.p", b"2")
        zf.writestr("ikea-abc/README.md", b"no")
    assert extract_safely(good, tmp_path / "out2") == 2
    assert not (tmp_path / "out2" / "README.md").exists()
