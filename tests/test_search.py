from mediawiki_client.search import format_search, search, strip_html

from .conftest import make_router


def test_strip_html_removes_tags_and_entities():
    out = strip_html('<span class="searchmatch">systemd</span> &mdash; manager')
    assert out == "systemd — manager"
    assert "<" not in out


def test_search_parses_results_and_builds_urls(search_payload, siteinfo_payload):
    fetch = make_router(
        {"list=search": search_payload, "meta=siteinfo": siteinfo_payload}
    )
    results = search("https://example.com", "systemd", limit=5, fetch=fetch)
    assert len(results) == 2
    first = results[0]
    assert first["title"] == "Systemd"
    assert "<" not in first["snippet"]
    assert first["snippet"].startswith("systemd")
    # articlepath in fixture is /$1, server https://example.com
    assert first["url"] == "https://example.com/Systemd"
    assert results[1]["url"] == "https://example.com/Systemd/networkd"


def test_search_limit_clamped(search_payload, siteinfo_payload):
    fetch = make_router(
        {"list=search": search_payload, "meta=siteinfo": siteinfo_payload}
    )
    # should not raise on weird limit
    results = search("https://example.com", "systemd", limit=999, fetch=fetch)
    assert isinstance(results, list)


def test_format_search_nonempty(search_payload, siteinfo_payload):
    fetch = make_router(
        {"list=search": search_payload, "meta=siteinfo": siteinfo_payload}
    )
    results = search("https://example.com", "systemd", fetch=fetch)
    text = format_search(results, "systemd")
    assert text.startswith("Found")
    assert "Systemd" in text


def test_format_search_empty():
    assert "No results found" in format_search([], "zzz")
