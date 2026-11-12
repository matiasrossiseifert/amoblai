"""La búsqueda híbrida: BM25, la consulta corta para el modelo de imagen y texto, y la fusión."""

import numpy as np
import pytest

from amoblai.rag.hybrid import BM25, fuse, visual_query

DOCS = [
    "Type: sofa, three-seat\nMaterials: grey fabric\nColors: grey",
    "Type: armchair, leather lounge chair\nMaterials: brown leather, oak\nColors: brown",
    "Type: rug, flatwoven\nMaterials: wool\nColors: grey, white",
]


def test_bm25_ranks_the_document_that_shares_the_rare_words_first():
    s = BM25(DOCS).scores(["Type: armchair\nMaterials: leather", "grey wool rug"])
    assert s.shape == (2, 3)
    assert s[0].argmax() == 1
    assert s[1].argmax() == 2
    assert s[1, 1] == 0  # the armchair shares no word with "grey wool rug"


def test_bm25_words_that_are_in_every_document_weigh_less_than_rare_ones():
    s = BM25(DOCS).scores(["type", "leather"])
    assert s[1, 1] > s[0, 1] > 0


def test_the_visual_query_keeps_what_a_photo_shows_and_drops_the_labels():
    q = (
        "Type: armchair, lounge reading chair\nUse: reading; living room\nStyle: Scandinavian\n"
        "Materials: bentwood, leather\nColors: cognac brown\nShape: curved frame, low seat\n"
        "Feel: warm, relaxed\nGoes with: oak floors"
    )
    assert visual_query(q) == (
        "armchair, lounge reading chair; bentwood, leather; cognac brown; curved frame, low seat"
    )
    assert visual_query("a  red sofa") == "a red sofa"  # not in lines: as it is


def test_fuse_keeps_the_filter_and_mixes_the_rankings():
    dense = np.array([0.9, 0.8, 0.1, 0.95])
    lexical = np.array([1.0, 5.0, 0.0, 9.0])
    allowed = np.array([True, True, True, False])
    for how in ("sum", "rrf"):
        f = fuse([dense, lexical], allowed, how)
        assert f[3] == -np.inf  # the filter wins over any score
        assert f[2] == f[:3].min()  # last in both rankings: last in the fusion
    # dense says 0 > 1 by little, lexical says 1 > 0 by a lot: the sum follows the larger gap
    assert fuse([dense, lexical], allowed, "sum").argmax() == 1
    assert fuse([dense], allowed, "sum").argmax() == 0  # one score alone: its own ranking
    assert fuse([dense, lexical, lexical], allowed).argmax() == 1  # any number of scores


def test_fuse_rejects_an_unknown_method_and_survives_an_empty_filter():
    with pytest.raises(ValueError):
        fuse([np.zeros(2)], np.ones(2, bool), "max")
    assert (fuse([np.ones(2)], np.zeros(2, bool)) == -np.inf).all()
