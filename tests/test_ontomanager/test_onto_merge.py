# coding: utf8
from pathlib import Path

from pytest import raises

from leavedonto import OntoManager

ref = Path().absolute() / 'resources' / 'test_onto.yaml'
to_add = Path().absolute() / 'resources' / 'test_onto2.yaml'
different = Path().absolute() / 'resources' / 'test_onto_different.yaml'

om = OntoManager(ref)


def test_merge():
    word = 'lemma5'
    res = om.ref.find_word(word)
    assert res == []

    om.merge_to_onto(to_add)
    ref_words2 = om.ref.list_words()
    assert 'lemma5' in ref_words2


def test_differing_legends():
    with raises(SyntaxError):
        om.merge_to_onto(different)
