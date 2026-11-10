"""El experimento de réplica sin red ni modelos: las cajas relativas, dibujarlas, lo que falta
pagar y el resumen por variante."""

from PIL import Image

from amoblai.evaluation import replica


def test_boxes_go_relative_and_back_and_centers_are_measured_on_the_diagonal():
    r = replica.rel((100, 50, 300, 150), 400, 200)
    assert r == [0.25, 0.25, 0.75, 0.75]
    assert replica.to_px(r, 800, 400) == (200, 100, 600, 300)
    assert replica.center_distance(r, r) == 0
    assert round(replica.center_distance([0, 0, 0, 0], [1, 1, 1, 1]), 6) == 1.0


def test_drawn_boxes_mark_the_photo_where_each_product_goes():
    img = Image.new("RGB", (400, 200), "white")
    out = replica.draw_boxes(img, [(2, [0.1, 0.1, 0.5, 0.9])])
    assert out.size == img.size and img.getpixel((40, 100)) == (255, 255, 255)
    assert out.getpixel((40, 100)) == replica.COLORS[0]  # el borde izquierdo
    assert out.getpixel((120, 100)) == (255, 255, 255)  # adentro queda la foto


def test_pending_counts_what_is_not_there_yet(tmp_path):
    exp = {"intentos_vaciar": 2, "repeticiones": 3, "variantes": {"a": {}, "b": {}}}
    assert replica.pending(exp, tmp_path) == 8
    (tmp_path / "vacio.png").write_bytes(b"x")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "1.png").write_bytes(b"x")
    assert replica.pending(exp, tmp_path) == 5


def test_summary_keeps_each_repetition_and_its_mean():
    rows = [
        {"iou_medio": 0.2, "en_su_lugar": 1, "detectados": 6, "centro_medio": None},
        {"iou_medio": 0.4, "en_su_lugar": 3, "detectados": 5, "centro_medio": 0.1},
    ]
    s = replica.summarize(rows)
    assert s["iou_medio"] == {"media": 0.3, "valores": [0.2, 0.4]}
    assert s["centro_medio"] == {"media": 0.1, "valores": [0.1]}
    assert s["ssim_con_la_real"]["media"] is None
