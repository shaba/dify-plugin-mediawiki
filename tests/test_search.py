from urllib.parse import parse_qs, urlparse

import pytest

from mediawiki_client.errors import MediaWikiAPIError
from mediawiki_client.search import format_search, page_url, search, strip_html

from .conftest import make_router


def test_strip_html_removes_tags_and_entities():
    out = strip_html('<span class="searchmatch">systemd</span> &mdash; manager')
    assert out == "systemd — manager"
    assert "<" not in out


def test_search_parses_results_and_builds_urls(search_payload):
    fetch = make_router({"list=search": search_payload})
    results = search("https://example.com", "systemd", limit=5, fetch=fetch)
    assert len(results) == 2
    first = results[0]
    assert first["title"] == "Systemd"
    assert "<" not in first["snippet"]
    assert first["snippet"].startswith("systemd")
    # articlepath in fixture is /$1, server https://example.com
    assert first["url"] == "https://example.com/Systemd"
    assert results[1]["url"] == "https://example.com/Systemd/networkd"


def test_search_single_request_combines_siteinfo(search_payload):
    """search must build URLs without a second siteinfo round-trip."""
    calls: list[str] = []

    def fetch(url: str, timeout: int = 30):
        calls.append(url)
        return search_payload

    results = search("https://example.com", "systemd", fetch=fetch)
    assert len(calls) == 1
    q = parse_qs(urlparse(calls[0]).query)
    assert q["list"] == ["search"]
    assert q["meta"] == ["siteinfo"]
    assert results[0]["url"] == "https://example.com/Systemd"


def test_search_raises_on_api_error():
    """A top-level error block (e.g. readapidenied) must surface, not be hidden."""
    def fetch(url: str, timeout: int = 30):
        return {"error": {"code": "readapidenied", "info": "Read access denied"}}

    with pytest.raises(MediaWikiAPIError) as exc:
        search("https://example.com", "systemd", fetch=fetch)
    assert exc.value.code == "readapidenied"


def test_search_protocol_relative_server_builds_absolute_urls():
    payload = {
        "query": {
            "general": {"server": "//en.wikipedia.org", "articlepath": "/wiki/$1"},
            "search": [{"title": "Linux", "snippet": "x"}],
        }
    }
    fetch = make_router({"list=search": payload})
    results = search("https://en.wikipedia.org/w/api.php", "linux", fetch=fetch)
    assert results[0]["url"] == "https://en.wikipedia.org/wiki/Linux"


def test_search_limit_clamped(search_payload):
    captured: dict[str, str] = {}

    def fetch(url: str, timeout: int = 30):
        captured.update({k: v[0] for k, v in parse_qs(urlparse(url).query).items()})
        return search_payload

    results = search("https://example.com", "systemd", limit=999, fetch=fetch)
    assert isinstance(results, list)
    assert captured["srlimit"] == "50"  # clamped to the 50 ceiling


def test_search_limit_floor(search_payload):
    captured: dict[str, str] = {}

    def fetch(url: str, timeout: int = 30):
        captured.update({k: v[0] for k, v in parse_qs(urlparse(url).query).items()})
        return search_payload

    search("https://example.com", "systemd", limit=0, fetch=fetch)
    assert captured["srlimit"] == "5"  # falsy → default 5


def test_format_search_nonempty(search_payload):
    fetch = make_router({"list=search": search_payload})
    results = search("https://example.com", "systemd", fetch=fetch)
    text = format_search(results, "systemd")
    assert text.startswith("Found")
    assert "Systemd" in text


def test_format_search_empty():
    assert "No results found" in format_search([], "zzz")


def test_page_url_encoding():
    assert page_url("https://x.org", "/wiki/$1", "Foo Bar") == "https://x.org/wiki/Foo_Bar"
    # namespace colon and subpage slash stay literal
    assert page_url("https://x.org", "/wiki/$1", "Help:Contents") == "https://x.org/wiki/Help:Contents"
    assert page_url("https://x.org", "/wiki/$1", "A/B") == "https://x.org/wiki/A/B"
    # fragment '#' and '+' must be percent-encoded
    assert page_url("https://x.org", "/wiki/$1", "A#frag") == "https://x.org/wiki/A%23frag"
    assert page_url("https://x.org", "/wiki/$1", "C++") == "https://x.org/wiki/C%2B%2B"
