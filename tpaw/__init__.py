"""Tildes Python API Wrapper."""

from datetime import datetime, timedelta

import lxml.html
import requests

__version__ = "0.0.1a4"


def one_class(element, class_selector, /):
    collection = element.find_class(class_selector)
    if len(collection) != 1:
        raise TPAWError(
            "Expected to find exactly 1 element", collection=collection, element=element
        )
    return collection[0]


def parse_group_name(name, /):
    assert name.startswith("~")
    return name[1:]


class HTMLParser:
    @staticmethod
    def enrich_article(topic, /, *, title_a, **kwargs):
        result = {}
        for metadata in topic.find_class("topic-content-metadata"):
            text = metadata.text.strip().rstrip(",")
            if text.startswith("published"):
                result["published"] = datetime.strptime(text[10:], "%b %d %Y").date()
            else:
                result["word_count"] = TextParser.parse_number_phrase(text)

        result.update(HTMLParser.enrich_link(topic, title_a=title_a, **kwargs))
        return result

    @staticmethod
    def enrich_ask(topic, /, *, type_, **_kwargs):
        result = {"type": "Ask"}
        if type_ != "Ask":
            result["subtype"] = type_[5:-1]
        return result

    @staticmethod
    def enrich_image(topic, /, **kwargs):
        return HTMLParser.enrich_link(topic, **kwargs)

    @staticmethod
    def enrich_link(topic, /, title_a, **_kwargs):
        return {
            "source": one_class(topic, "topic-info-source").get("title"),
            "url": title_a.get("href"),
        }

    @staticmethod
    def enrich_pdf(topic, /, **kwargs):
        return HTMLParser.enrich_link(topic, **kwargs)

    @staticmethod
    def enrich_text(topic, /, **_kwargs):
        one_class(topic, "topic-text-excerpt")
        return {
            "word_count": TextParser.parse_number_phrase(
                one_class(topic, "topic-content-metadata").text
            ),
        }

    @staticmethod
    def enrich_tweet(topic, /, **kwargs):
        return {
            "tweet": one_class(topic, "topic-text-excerpt").text,
            **HTMLParser.enrich_link(topic, **kwargs),
        }

    @staticmethod
    def enrich_video(topic, /, **kwargs):
        result = {}
        for metadata in topic.find_class("topic-content-metadata"):
            text = metadata.text.strip().rstrip(",")
            if text.startswith("published"):
                result["published"] = datetime.strptime(text[10:], "%b %d %Y").date()
            else:
                minutes, seconds = text.split(":")
                result["duration"] = timedelta(
                    minutes=int(minutes), seconds=int(seconds)
                )

        result.update(HTMLParser.enrich_link(topic, **kwargs))
        return result

    @staticmethod
    def parse_group(group, /):
        return {
            "activity": TextParser.parse_group_description(
                one_class(group, "group-list-activity").text
            ),
            "description": one_class(group, "group-list-description").text,
            "name": parse_group_name(group.find("a").text),
            "subscribed": "group-list-item-subscribed" in group.classes,
        }

    @staticmethod
    def parse_topic(topic, /):
        metadata = one_class(topic, "topic-metadata")
        title_a = one_class(topic, "topic-title").find("a")
        type_ = one_class(metadata, "topic-content-type").text

        result = {
            "comment_count": TextParser.parse_number_phrase(
                one_class(topic, "topic-info-comments").find("a").find("span").text
            ),
            "created_time": TextParser.parse_datetime(
                one_class(topic, "time-responsive").get("datetime")
            ),
            "group": parse_group_name(one_class(metadata, "link-group").text),
            "id": topic.get("id")[6:],
            "tags": [
                li.find("a").text for li in metadata.find_class("label-topic-tag")
            ],
            "title": title_a.text,
            "type": type_,
            "votes": int(one_class(topic, "topic-voting-votes").text),
        }

        method_suffix = "ask" if type_.startswith("Ask") else type_.lower()
        method = getattr(HTMLParser, f"enrich_{method_suffix}")

        result.update(method(topic, title_a=title_a, type_=type_))
        return result


class TPAWError(Exception):
    def __init__(self, *args, **kwargs):
        self.__dict__ = kwargs
        super().__init__(*args)


class TextParser:
    @staticmethod
    def parse_datetime(datetime_string):
        assert datetime_string.endswith(
            "Z"
        ), "Expected datetime to end with Z {datetime_string}"
        return datetime.fromisoformat(datetime_string[:-1] + "+00:00")

    @staticmethod
    def parse_group_description(description, /):
        tokens = description.split()
        return {"comments": int(tokens[5]), "topics": int(tokens[3])}

    @staticmethod
    def parse_number_phrase(number_phrase, /):
        return int(number_phrase.split(None, 1)[0])


class Tildes:
    BASE_URL = "https://tildes.net"
    DEFAULT_HEADERS = {"User-Agent": f"tpaw/{__version__}"}

    def __init__(self):
        self._session = requests.Session()

    def _get(self, path, /, *, params=None):
        response = self._session.get(
            f"{self.BASE_URL}/{path}", headers=self.DEFAULT_HEADERS, params=params
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
        for group in one_class(document, "group-list").iter("li"):
            yield HTMLParser.parse_group(group)

    def topics(self):
        response = self._get("", params={"order": "new"})
        document = lxml.html.document_fromstring(response.content)
        for topic in document.iter("article"):
            yield HTMLParser.parse_topic(topic)


if __name__ == "__main__":
    tildes = Tildes()
    for topic in tildes.topics():
        import pprint

        pprint.pprint(topic)
