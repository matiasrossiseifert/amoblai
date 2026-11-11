"""Las cajas 3D sin modelos: el plano, las esquinas, la proyección, qué aristas se ven y el dibujo."""

import numpy as np
from PIL import Image

from amoblai.evaluation import cajas3d as c3

AXES = (np.array([1.0, 0, 0]), np.array([0, 0, -1.0]), np.array([0, -1.0, 0]))  # along, out, up


def test_the_floor_plane_is_found_among_outliers():
    rng = np.random.default_rng(1)
    floor = np.c_[rng.uniform(-2, 2, 400), np.full(400, 1.2), rng.uniform(2, 6, 400)]
    noise = rng.uniform(-2, 6, (100, 3))
    n, d, frac = c3.fit_plane(np.r_[floor, noise], thr=0.02, iters=300)
    assert abs(abs(n[1]) - 1) < 1e-6 and abs(abs(d) - 1.2) < 1e-6
    assert frac >= 0.8


def test_a_box_on_the_floor_projects_with_its_base_below_its_top():
    origin = np.array([0, 1.0, 4.0])  # el piso, 1 m debajo de la cámara, 4 m adelante
    b = {"along": [-0.5, 0.5], "out": [0.0, 0.8], "h": [0.0, 0.7]}
    corners = c3.box_corners(origin, AXES, b)
    assert corners.shape == (8, 3)
    assert np.allclose(corners[4] - corners[0], [0, -0.7, 0])  # arriba = y de cámara negativa
    px = c3.project(corners, f=1000, cx=500, cy=400)
    assert (px[:4, 1] > px[4:, 1]).all()  # la base se ve más abajo que la tapa
    vis = c3.visible_corners(corners)
    assert {4, 5, 6, 7} <= vis  # desde arriba se ve la tapa


def test_drawn_box_uses_its_color_and_leaves_the_rest_of_the_photo():
    img = Image.new("RGB", (400, 300), "white")
    box = {"esquinas": [[0.2, 0.8], [0.6, 0.8], [0.7, 0.7], [0.3, 0.7],
                        [0.2, 0.4], [0.6, 0.4], [0.7, 0.3], [0.3, 0.3]],
           "visibles": [0, 1, 4, 5, 6, 7]}  # fmt: skip
    out = c3.draw_boxes3d(img, [(2, box)], [(255, 0, 0)])
    assert out.getpixel((160, 240)) == (255, 0, 0)  # la arista de abajo, al frente
    assert out.getpixel((10, 10)) == (255, 255, 255)
    assert img.getpixel((160, 240)) == (255, 255, 255)  # no toca la original
