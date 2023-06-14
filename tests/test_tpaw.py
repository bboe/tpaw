import pytest
from lxml.html import fragment_fromstring

import tpaw


def test_tildes_groups():
    tildes = tpaw.Tildes()
    for i, group in enumerate(tildes.groups()):
        assert isinstance(group, dict)
    assert i == 29


def test_one_class():
    with pytest.raises(tpaw.TPAWError) as exception_info:
        tpaw.one_class(fragment_fromstring("<a>"), "notfound")
    assert len(exception_info.value.collection) == 0

    with pytest.raises(tpaw.TPAWError) as exception_info:
        tpaw.one_class(fragment_fromstring('<p class="notfound">'), "found")
    assert len(exception_info.value.collection) == 0

    with pytest.raises(tpaw.TPAWError) as exception_info:
        tpaw.one_class(
            fragment_fromstring('<div><p class="found"><p class="found">'), "found"
        )
    assert len(exception_info.value.collection) == 2

    element = fragment_fromstring('<p class="found">')
    assert tpaw.one_class(element, "found") is element

    element = fragment_fromstring('<div><p class="found">')
    assert tpaw.one_class(element, "found") in element
