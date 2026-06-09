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


def test_noise_filter_keeps_lookalike_classes():
    # reference-text / tocsection contain noise tokens as substrings but are content.
    md = html_to_markdown(
        '<p>see <span class="reference-text">important note</span></p>'
        '<p><span class="tocsection-1">visible</span></p>'
    )
    assert "important note" in md
    assert "visible" in md


def test_noise_filter_still_drops_exact_tokens():
    md = html_to_markdown(
        '<div class="toc">CONTENTS</div>'
        '<table class="navbox"><tr><td>NAV</td></tr></table>'
        '<sup class="reference">[1]</sup>keep'
    )
    assert "CONTENTS" not in md
    assert "NAV" not in md
    assert "[1]" not in md
    assert "keep" in md


def test_sup_non_reference_kept():
    md = html_to_markdown("<p>x<sup>2</sup> and m<sup>3</sup></p>")
    assert "x2" in md
    assert "m3" in md


def test_pre_block_is_fenced():
    md = html_to_markdown("<pre>line1\nline2</pre>")
    assert "```" in md
    assert "line1\nline2" in md
    # not wrapped as a single inline backtick span
    assert "`line1" not in md


def test_inline_code_still_backticked():
    md = html_to_markdown("<p>run <code>systemctl</code> now</p>")
    assert "`systemctl`" in md


def test_ordered_list_increments():
    md = html_to_markdown("<ol><li>x</li><li>y</li><li>z</li></ol>")
    assert "1. x" in md
    assert "2. y" in md
    assert "3. z" in md


def test_nested_list_no_blank_lines():
    md = html_to_markdown("<ul><li>a<ul><li>b</li></ul></li><li>c</li></ul>")
    # nested item indented, no blank line splitting the list
    assert "- a" in md
    assert "    - b" in md
    assert "- c" in md
    assert "\n\n" not in md.strip()


def test_links_become_markdown_with_resolved_url():
    md = html_to_markdown(
        'See <a href="/wiki/Foo">Foo</a> page', server="https://example.com"
    )
    assert "[Foo](https://example.com/wiki/Foo)" in md


def test_links_without_server_keep_href():
    md = html_to_markdown('See <a href="/wiki/Foo">Foo</a>')
    assert "[Foo](/wiki/Foo)" in md


def test_table_rendered_as_pipes():
    md = html_to_markdown(
        "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>"
    )
    assert "| A | B |" in md
    assert "| --- | --- |" in md
    assert "| 1 | 2 |" in md


def test_definition_list_and_blockquote():
    md = html_to_markdown("<dl><dt>Term</dt><dd>Definition</dd></dl>")
    assert "**Term**" in md
    assert "Definition" in md
    bq = html_to_markdown("<blockquote>quoted</blockquote>")
    assert "> quoted" in bq


def test_pretty_printed_list_has_no_blank_lines():
    # Real MediaWiki HTML has newlines between block elements.
    md = html_to_markdown("<ul><li>a</li>\n<li>b</li>\n<li>c</li></ul>")
    assert md == "- a\n- b\n- c"


def test_nested_table_flattened_into_outer_cell():
    md = html_to_markdown(
        "<table><tr><td>outer<table><tr><td>inner</td></tr></table></td></tr></table>"
    )
    # Single table; outer cell keeps its own text and the inner content inline.
    assert "outer" in md and "inner" in md
    # No stray pipe-escapes leaking the inner table's markup into the cell.
    assert "\\|" not in md
    assert md.count("| --- |") == 1


def test_table_without_header_row_keeps_data_rows():
    md = html_to_markdown(
        "<table><tr><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td></tr></table>"
    )
    # First <td> row must stay in the body, not be promoted to a header.
    assert "| 1 | 2 |" in md
    assert "| 3 | 4 |" in md


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
