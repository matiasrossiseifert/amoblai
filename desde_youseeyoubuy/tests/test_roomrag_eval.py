"""The catalog search test's scoring (roomrag.evaluate): grades in, metrics out."""

import pytest

from roomrag.evaluate import Search, ndcg, score


def test_ndcg_is_one_for_the_best_order_and_less_otherwise():
    assert ndcg([2, 1, 0], [2, 1, 0, 0], 3) == pytest.approx(1.0)
    assert ndcg([0, 1, 2], [2, 1, 0], 3) < 1.0
    assert ndcg([0, 0, 0], [], 3) == 0.0


def test_score_counts_ungraded_and_missing_results_as_wrong():
    searches = [Search("c", 0, {"query": "q"}), Search("c", 1, {"query": "q"})]
    judged = {("c", 0, "a"): 2, ("c", 0, "b"): 1, ("c", 1, "a"): 0, ("c", 1, "d"): 2}
    results = {"m": [["a", "b", "x"], ["a"]]}  # x ungraded; the second search brought one
    row = score(results, searches, judged, 3)["m"]
    assert row["ok@3"] == pytest.approx((2 / 3 + 0) / 2, abs=1e-3)
    assert row["good@3"] == pytest.approx((1 / 3) / 2, abs=1e-3)
    assert row["first_ok"] == 0.5 and row["ungraded"] == 1
