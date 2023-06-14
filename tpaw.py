"""Tildes Python API Wrapper."""

import sys

import requests
import lxml.html

__version__ = "0.0.1-alpha"


def one(collection):
    assert len(collection) == 1, f"Expected exactly 1 element in {collection}"
    return collection[0]


class HTMLParser:
    @staticmethod
    def parse_group(group):
        return {
            "activity": TextParser.parse_group_description(
                one(group.find_class("group-list-activity")).text
            ),
            "description": one(group.find_class("group-list-description")).text,
            "name": group.find("a").text,
            "subscribed": "group-list-item-subscribed" in group.classes,
        }


class TextParser:
    @staticmethod
    def parse_group_description(description):
        tokens = description.split()
        return {"comments": int(tokens[5]), "topics": int(tokens[3])}


class Tildes:
    BASE_URL = "https://tildes.net"
    DEFAULT_HEADERS = {"User-Agent": "tpaw/experimental (bboe)"}

    def __init__(self):
        self._session = requests.Session()

    def _get(self, path):
        response = self._session.get(
            f"{self.BASE_URL}/{path}", headers=self.DEFAULT_HEADERS
        )
        assert (
            response.status_code == 200
        ), f"Invalid status code {response.status_code}"
        content_type = response.headers["Content-Type"]
        assert content_type.startswith(
            "text/html;"
        ), f"Invalid content type {content_type}"
        return response

    def groups(self):
        response = self._get("groups")
        document = lxml.html.document_fromstring(response.content)
        for group in one(document.find_class("group-list")).iter("li"):
            yield HTMLParser.parse_group(group)



if __name__ == "__main__":
    tildes = Tildes()
    for group in tildes.groups():
        import pprint

        pprint.pprint(group)

    return 0
