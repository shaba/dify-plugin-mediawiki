import pytest

from mediawiki_client import get_page
from mediawiki_client.errors import PageNotFound
from mediawiki_client.htmlmd import html_to_markdown

from .conftest import make_router


def test_html_to_markdown_basic():
    md = html_to_markdown(
        "<p><b>systemd</b> is a <i>manager</i>.</p><h2>Usage</h2><ul><li>a</li><li>b</li></ul>"
    )
    assert "**systemd**" in md
    assert "*manager*" in md
    assert "## Usage" in md
    assert "- a" in md and "- b" in md


def test_html_to_markdown_drops_noise():
    md = html_to_markdown(
        '<p>text<span class="mw-editsection">[edit]</span></p>'
        "<table class=\"navbox\"><tr><td>NAV</td></tr></table>"
        "<script>evil()</script>"
    )
    assert "edit" not in md
    assert "NAV" not in md
    assert "evil" not in md
    assert "text" in md


def test_html_to_markdown_unescapes_entities():
    md = html_to_markdown("<p>a &mdash; b &amp; c</p>")
    assert "—" in md
    assert "&" in md and "&amp;" not in md


def test_get_page_returns_markdown(parse_payload, siteinfo_payload):
    fetch = make_router(
        {"action=parse": parse_payload, "meta=siteinfo": siteinfo_payload}
    )
    page = get_page("Systemd", "https://example.com", fetch=fetch)
    assert page["title"] == "Systemd"
    assert "**systemd**" in page["markdown"]
    assert "## Usage" in page["markdown"]
    assert "edit" not in page["markdown"]
    assert page["source_url"] == "https://example.com/Systemd"


def test_get_page_missing_raises(parse_missing_payload):
    fetch = make_router({"action=parse": parse_missing_payload})
    with pytest.raises(PageNotFound):
        get_page("Nope", "https://example.com", fetch=fetch)


def test_get_page_empty_title_raises():
    with pytest.raises(PageNotFound):
        get_page("", "https://example.com")
