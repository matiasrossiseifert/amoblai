import numpy as np
import pytest
from PIL import Image

from amoblai_imagen.config import BackgroundConfig, DetectionConfig, PreprocessConfig
from amoblai_imagen.indexing.preprocess import apply_mask, pad_to_square
from amoblai_imagen.indexing.splitter import split_catalog
from amoblai_imagen.retrieval.retriever import Retriever, load_threshold, resolve_threshold
from amoblai_imagen.vision.background import clean_mask
from amoblai_imagen.vision.boxes import Box, box_percent, describe_location
from amoblai_imagen.vision.crops import make_crops
from amoblai_imagen.vision.detection import Detection, nms, phrase_token_positions, postprocess
from conftest import ROOM_BOXES, FakeDetector, make_room_image


def test_box_geometry():
    a, b = Box(0, 0, 10, 10), Box(5, 5, 15, 15)
    assert a.area == 100
    assert a.iou(b) == pytest.approx(25 / 175)
    assert a.expand(0.1).as_list() == [-1.0, -1.0, 11.0, 11.0]
    assert a.expand(0.5, 12, 12).as_list() == [0.0, 0.0, 12.0, 12.0]
    assert describe_location(Box(0, 250, 50, 300), 300, 300) == "front left"
    assert box_percent(Box(0, 0, 150, 300), 300, 300) == "x 0–50%, y 0–100%"


class WordTokenizer:
    """Tokenizador mínimo con offsets: palabras y puntos (como BERT, más [CLS]/[SEP])."""

    def __call__(self, text, return_offsets_mapping=False):
        import re

        offsets = [(0, 0)] + [m.span() for m in re.finditer(r"\w+|\.", text)] + [(0, 0)]
        return {"offset_mapping": offsets}


def test_phrase_token_positions_separates_chair_and_armchair():
    text, positions = phrase_token_positions(WordTokenizer(), ["armchair", "chair", "dining chair"])
    assert text == "armchair. chair. dining chair."
    # [CLS]=0, armchair=1, .=2, chair=3, .=4, dining=5, chair=6, .=7
    assert positions == [[1], [3], [5, 6]]


def test_nms_and_cross_category_resolution():
    cfg = DetectionConfig(min_area_frac=0.0, max_area_frac=1.0)
    dets = [
        Detection(Box(0, 0, 10, 10), "chair", "chair", 0.6),
        Detection(Box(0, 0, 10, 10.5), "armchair", "armchair", 0.8),
        Detection(Box(1, 0, 10, 10), "chair", "chair", 0.5),
        Detection(Box(50, 50, 60, 60), "table", "table", 0.4),
    ]
    out = postprocess(dets, cfg, 100, 100)
    assert [(d.category, d.score) for d in out] == [("armchair", 0.8), ("table", 0.4)]
    assert len(nms(dets[:3], 0.99)) == 3


def test_postprocess_filters_by_area():
    cfg = DetectionConfig(min_area_frac=0.01, max_area_frac=0.5)
    dets = [
        Detection(Box(0, 0, 2, 2), "chair", "chair", 0.9),  # muy chica
        Detection(Box(0, 0, 90, 90), "rug", "rug", 0.9),  # muy grande
        Detection(Box(0, 0, 30, 30), "table", "table", 0.9),
    ]
    assert [d.category for d in postprocess(dets, cfg, 100, 100)] == ["table"]


def test_pad_to_square_and_mask():
    img = Image.new("RGB", (40, 20), (10, 10, 10))
    sq = pad_to_square(img, margin=0.0)
    assert sq.size == (40, 40)
    assert sq.getpixel((0, 0)) == (255, 255, 255)
    assert sq.getpixel((20, 20)) == (10, 10, 10)
    mask = np.zeros((20, 40), dtype=bool)
    mask[:, :20] = True
    masked = apply_mask(img, mask)
    assert masked.getpixel((5, 5)) == (10, 10, 10)
    assert masked.getpixel((30, 5)) == (255, 255, 255)


def test_clean_mask_keeps_largest_component_inside_box():
    mask = np.zeros((50, 50), dtype=bool)
    mask[10:30, 10:30] = True
    mask[12:14, 12:14] = False  # hueco
    mask[40:45, 40:45] = True  # fuera de la caja
    out = clean_mask(mask, Box(5, 5, 35, 35))
    assert out[13, 13] and not out[42, 42]


def test_crops_with_and_without_mask():
    room = make_room_image()
    det = Detection(ROOM_BOXES["100.000.01"], "sofa", "sofa", 0.9)
    bg, pre = BackgroundConfig(crop_margin=0.0), PreprocessConfig(pad_margin=0.0)

    class HalfMask:
        def masks(self, image, boxes):
            out = []
            for box in boxes:
                m = np.zeros((image.size[1], image.size[0]), dtype=bool)
                x0, y0, x1, y1 = box.to_int()
                m[y0:y1, x0 : (x0 + x1) // 2] = True
                out.append(m)
            return out

    crop = make_crops(room, [det], HalfMask(), bg, pre)[0]
    assert crop.background_removed
    assert crop.query.size[0] == crop.query.size[1]
    skip = make_crops(room, [det], HalfMask(), BackgroundConfig(skip_categories=["sofa"]), pre)[0]
    assert not skip.background_removed


def test_splitter_one_entry_per_image(catalog):
    entries = split_catalog(catalog)
    assert len(entries) == 8
    e = next(x for x in entries if x.sku == "100.000.01")
    assert e.id == "100.000.01#0"
    assert e.metadata["category"] == "sofa"
    assert e.metadata["dim1_cm"] == 200.0
    assert all(v is not None for v in e.metadata.values())
    assert len(split_catalog(catalog, scope_only=True)) == 7  # sin la lámpara


def test_retriever_with_category_filter(components):
    room = make_room_image()
    crops = make_crops(
        room,
        FakeDetector().detect(room),
        components.remover,
        BackgroundConfig(),
        PreprocessConfig(),
    )
    results = components.retriever.search(crops)
    chosen = {r.category: r.chosen_sku for r in results}
    assert chosen == {"sofa": "100.000.01", "chair": "100.000.03", "table": "100.000.05"}
    for r in results:
        assert all(c.category == r.category for c in r.candidates)
        assert r.candidates[0].score > 0.95


def test_retriever_without_filter_searches_whole_catalog(components):
    room = make_room_image()
    crops = make_crops(
        room,
        FakeDetector().detect(room),
        components.remover,
        BackgroundConfig(),
        PreprocessConfig(),
    )
    retr = Retriever(components.embedder, components.store, top_k=8, category_filter=False)
    cats = {c.category for r in retr.search(crops) for c in r.candidates}
    assert "other" in cats


def test_threshold_discards_low_similarity(components):
    room = make_room_image()
    crops = make_crops(
        room,
        FakeDetector().detect(room),
        components.remover,
        BackgroundConfig(),
        PreprocessConfig(),
    )
    retr = Retriever(components.embedder, components.store, top_k=3, threshold=1.01)
    assert all(not r.accepted for r in retr.search(crops))


def test_threshold_resolution(cfg, tmp_path):
    from amoblai_imagen.eval.retriever_eval import write_threshold

    path = tmp_path / "u.yaml"
    assert load_threshold(path, "col") is None
    write_threshold(
        path, "col", {"threshold": 0.42, "f1": 0.8, "precision": 0.7, "recall": 0.9}, "r1"
    )
    assert load_threshold(path, "col") == pytest.approx(0.42)
    cfg.retrieval.threshold = "auto"
    assert resolve_threshold(cfg.retrieval, path, "col") == pytest.approx(0.42)
    cfg.retrieval.threshold = 0.3
    assert resolve_threshold(cfg.retrieval, path, "col") == 0.3
