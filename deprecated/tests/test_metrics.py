import itertools
import math

import pytest

from amoblai_imagen.eval.metrics import (
    best_f1_threshold,
    bootstrap_ci,
    first_relevant_rank,
    hit_at_k,
    random_hit_at_k,
    random_mrr,
    reciprocal_rank,
)


def test_rank_hit_rr():
    ranked = ["a", "b", "c", "d"]
    assert first_relevant_rank(ranked, {"c", "z"}) == 3
    assert first_relevant_rank(ranked, {"z"}) is None
    assert hit_at_k(3, 1) == 0.0 and hit_at_k(3, 5) == 1.0 and hit_at_k(None, 10) == 0.0
    assert reciprocal_rank(4) == 0.25
    assert reciprocal_rank(4, k=3) == 0.0


@pytest.mark.parametrize(("n", "r", "k"), [(6, 1, 1), (6, 2, 3), (7, 3, 2), (5, 5, 1), (8, 2, 10)])
def test_random_baselines_match_brute_force(n, r, k):
    items = range(n)
    relevant = set(range(r))
    perms = list(itertools.permutations(items))
    hits = rrs = 0.0
    for p in perms:
        rank = next(i for i, x in enumerate(p, start=1) if x in relevant)
        hits += rank <= k
        rrs += 1.0 / rank if rank <= k else 0.0
    assert random_hit_at_k(n, r, k) == pytest.approx(hits / len(perms))
    assert random_mrr(n, r, k) == pytest.approx(rrs / len(perms))


def test_bootstrap_ci_contains_mean_and_resamples_groups():
    values = [1, 1, 0, 0, 1, 0]
    groups = ["a", "a", "b", "b", "c", "c"]
    lo, hi = bootstrap_ci(values, groups, n_samples=300, seed=1)
    assert lo <= 0.5 <= hi
    assert bootstrap_ci([1.0, 1.0], ["a", "b"], 50) == (1.0, 1.0)
    assert all(math.isnan(v) for v in bootstrap_ci([], [], 10))


def test_best_f1_threshold():
    scores = [0.9, 0.8, 0.7, 0.4, 0.3]
    correct = [True, True, False, False, False]
    best = best_f1_threshold(scores, correct)
    assert best["threshold"] == 0.8
    assert best["f1"] == pytest.approx(1.0)
    assert math.isnan(best_f1_threshold([0.5], [False])["threshold"])


def test_shared_crop_store_is_content_addressed(tmp_path):
    import hashlib

    from PIL import Image

    from amoblai_imagen.eval.retriever_eval import save_shared_crop

    img = Image.new("RGB", (300, 120), (120, 30, 200))
    rel = save_shared_crop(img, tmp_path)
    assert save_shared_crop(img.copy(), tmp_path) == rel  # misma imagen → mismo archivo
    data = (tmp_path / rel).read_bytes()
    assert rel == f"recortes/{hashlib.sha256(data).hexdigest()[:20]}.jpg"
    assert save_shared_crop(Image.new("RGB", (300, 120), "white"), tmp_path) != rel
