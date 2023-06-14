from unittest.mock import Mock

import pytest
from lxml.html import fragment_fromstring

import tpaw


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


def test_tildes_groups(tildes):
    with open("tests/data/groups.html") as fp:
        content = fp.read()

    tildes._session.get.return_value = Mock(
        content=content, headers={"Content-Type": "text/html;"}, status_code=200
    )

    for i, group in enumerate(tildes.groups(), start=1):
        assert isinstance(group, dict)
    assert i == 30


def test_tildes_new(tildes):
    with open("tests/data/slash_new.html") as fp:
        content = fp.read()

    tildes._session.get.return_value = Mock(
        content=content, headers={"Content-Type": "text/html;"}, status_code=200
    )

    for i, topic in enumerate(tildes.topics(), start=1):
        assert isinstance(topic, dict)
    assert i == 10


@pytest.fixture
def tildes():
    client = tpaw.Tildes()
    client._session = Mock()
    return client
