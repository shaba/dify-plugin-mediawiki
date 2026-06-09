"""Lightweight cleanup of MediaWiki HTML (action=parse) and conversion to markdown.

No third-party dependencies (bs4/markdownify) — stdlib only, to keep the plugin
dependency-free. Sufficient for wiki article text: headings, paragraphs, lists,
links, tables, and basic formatting.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

# MediaWiki noise classes that should be dropped entirely along with their content.
# Matched as whole whitespace-separated class tokens (optionally as a prefix, see
# _PREFIX_NOISE) so that legitimate classes such as ``reference-text`` or
# ``tocsection-1`` are NOT swept away by a naive substring test.
_NOISE_CLASSES = frozenset(
    {
        "mw-editsection",
        "navbox",
        "metadata",
        "noprint",
        "mw-empty-elt",
        "toc",
        "mw-jump-link",
        "printfooter",
        "mw-references-wrap",
    }
)

# Class prefixes: an element is noise if any of its class tokens starts with one
# of these (covers families like ``navbox-foo`` / ``toc-foo`` without matching
# unrelated classes that merely contain the substring).
_PREFIX_NOISE = (
    "navbox",
    "mw-references-",
)

_DROP_TAGS = ("script", "style")


class _MarkdownExtractor(HTMLParser):
    def __init__(self, server: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._server = server.rstrip("/") if server else ""
        self._skip_depth = 0
        self._skip_tag: str | None = None
        # Each entry: {"tag": "ul"|"ol", "n": int} — counter for ordered lists.
        self._list_stack: list[dict] = []
        self._pre_depth = 0
        self._blockquote_depth = 0
        # Pending link target while inside an <a href=...>; href resolved on close.
        self._link_href: str | None = None
        self._link_text_start: int | None = None
        # Table state as a stack so nested tables (common in infoboxes) keep
        # independent row/cell bookkeeping. Each frame:
        # {"cells": list[str]|None, "cell_start": int|None, "rows": int,
        #  "header": bool}.
        self._table_stack: list[dict] = []

    # --- skipping of noise subtrees ---
    @staticmethod
    def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
        for name, value in attrs:
            if name == "class" and value:
                return set(value.split())
        return set()

    def _is_noise(self, attrs: list[tuple[str, str | None]]) -> bool:
        classes = self._classes(attrs)
        if classes & _NOISE_CLASSES:
            return True
        return any(c.startswith(_PREFIX_NOISE) for c in classes)

    @staticmethod
    def _is_reference_sup(attrs: list[tuple[str, str | None]]) -> bool:
        for name, value in attrs:
            if name == "class" and value and "reference" in value.split():
                return True
        return False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            if tag == self._skip_tag:
                self._skip_depth += 1
            return
        # Drop reference markers (<sup class="reference">) but keep other <sup>
        # content (exponents, units, etc.).
        if tag in _DROP_TAGS or self._is_noise(attrs) or (
            tag == "sup" and self._is_reference_sup(attrs)
        ):
            self._skip_depth = 1
            self._skip_tag = tag
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.parts.append("\n\n" + "#" * level + " ")
        elif tag == "p":
            self.parts.append("\n\n")
        elif tag in ("ul", "ol"):
            self._list_stack.append({"tag": tag, "n": 0})
        elif tag == "li":
            depth = max(0, len(self._list_stack) - 1)
            indent = "    " * depth
            if self._list_stack and self._list_stack[-1]["tag"] == "ol":
                self._list_stack[-1]["n"] += 1
                marker = f"{self._list_stack[-1]['n']}. "
            else:
                marker = "- "
            self.parts.append("\n" + indent + marker)
        elif tag == "dl":
            self.parts.append("\n")
        elif tag == "dt":
            self.parts.append("\n**")
        elif tag == "dd":
            self.parts.append("\n: ")
        elif tag == "blockquote":
            self._blockquote_depth += 1
            self.parts.append("\n\n> ")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "pre":
            self._pre_depth += 1
            self.parts.append("\n\n```\n")
        elif tag == "code":
            if self._pre_depth == 0:
                self.parts.append("`")
        elif tag == "a":
            href = None
            for name, value in attrs:
                if name == "href":
                    href = value
            self._link_href = href
            self._link_text_start = len(self.parts)
        elif tag == "table":
            nested = bool(self._table_stack)
            self._table_stack.append(
                {
                    "cells": None,
                    "cell_start": None,
                    "rows": 0,
                    "header": False,
                    "nested": nested,
                }
            )
            # A nested table is flattened inline into its enclosing cell; emitting
            # a blank-line block boundary would break that cell's capture.
            self.parts.append(" " if nested else "\n\n")
        elif tag == "tr" and self._table_stack:
            self._table_stack[-1]["cells"] = []
        elif tag in ("td", "th") and self._table_stack:
            self._table_stack[-1]["cell_start"] = len(self.parts)
            if tag == "th":
                self._table_stack[-1]["header"] = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if not self._skip_depth and tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth:
            if tag == self._skip_tag:
                self._skip_depth -= 1
                if self._skip_depth == 0:
                    self._skip_tag = None
            return

        if tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
            if not self._list_stack:
                self.parts.append("\n")
        elif tag == "dt":
            self.parts.append("**")
        elif tag == "blockquote":
            if self._blockquote_depth > 0:
                self._blockquote_depth -= 1
            self.parts.append("\n\n")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")
        elif tag == "pre":
            if self._pre_depth > 0:
                self._pre_depth -= 1
            self.parts.append("\n```\n\n")
        elif tag == "code":
            if self._pre_depth == 0:
                self.parts.append("`")
        elif tag == "a":
            self._close_link()
        elif tag in ("td", "th") and self._table_stack:
            self._close_cell()
        elif tag == "tr" and self._table_stack:
            self._close_row()
        elif tag == "table" and self._table_stack:
            frame = self._table_stack.pop()
            self.parts.append(" " if frame["nested"] else "\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self.parts.append("\n")

    def _close_link(self) -> None:
        if self._link_text_start is None:
            return
        text = "".join(self.parts[self._link_text_start:]).strip()
        href = self._link_href
        self._link_href = None
        start = self._link_text_start
        self._link_text_start = None
        if not href or href.startswith("#") or not text:
            return  # keep bare text already in self.parts
        url = urljoin(self._server + "/", href) if self._server else href
        del self.parts[start:]
        self.parts.append(f"[{text}]({url})")

    def _close_cell(self) -> None:
        frame = self._table_stack[-1] if self._table_stack else None
        if frame is None or frame["cell_start"] is None or frame["cells"] is None:
            return
        text = "".join(self.parts[frame["cell_start"]:])
        text = re.sub(r"\s+", " ", text).strip()
        if not frame["nested"]:
            text = text.replace("|", "\\|")
        del self.parts[frame["cell_start"]:]
        frame["cell_start"] = None
        frame["cells"].append(text)

    def _close_row(self) -> None:
        frame = self._table_stack[-1] if self._table_stack else None
        if frame is None or not frame["cells"]:
            if frame is not None:
                frame["cells"] = None
            return
        cells = frame["cells"]
        if frame["nested"]:
            # Flatten the nested table inline so it stays inside the enclosing cell.
            self.parts.append(" ".join(c for c in cells if c))
            frame["cells"] = None
            return
        if frame["rows"] == 0 and not frame["header"]:
            # First row has no <th>: emit an empty header + separator first, so this
            # real data row stays in the table body instead of being promoted to a
            # header (which would shift all subsequent data up by one row).
            self.parts.append("\n| " + " | ".join("" for _ in cells) + " |")
            self.parts.append("\n| " + " | ".join("---" for _ in cells) + " |")
        self.parts.append("\n| " + " | ".join(cells) + " |")
        if frame["rows"] == 0 and frame["header"]:
            # GFM requires a header separator after the header row.
            self.parts.append("\n| " + " | ".join("---" for _ in cells) + " |")
        frame["rows"] += 1
        frame["cells"] = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        # Inside a <pre>/code fence, whitespace is significant — keep it verbatim.
        if self._pre_depth == 0 and data.strip() == "" and "\n" in data:
            # Inter-block whitespace (the newlines MediaWiki pretty-prints between
            # block elements). Emitting it verbatim would split markdown lists with
            # blank lines. Drop it when it follows a structural boundary; otherwise
            # collapse it to a single space so inline spacing survives.
            if not self.parts or self.parts[-1].endswith(("\n", " ")):
                return
            self.parts.append(" ")
            return
        self.parts.append(data)


def html_to_markdown(fragment_html: str, server: str = "") -> str:
    """Clean article HTML from action=parse and return markdown.

    ``server`` (scheme://host) is used to resolve relative link hrefs into
    absolute markdown links; when empty, hrefs are emitted as-is.
    """
    parser = _MarkdownExtractor(server=server)
    parser.feed(fragment_html or "")
    text = html.unescape("".join(parser.parts))
    # collapse extra blank lines and trailing whitespace
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces/tabs, but never the leading indentation of a line
    # (preserves nested-list / fenced-block structure).
    text = re.sub(r"(?<=\S)[ \t]{2,}", " ", text)
    return text.strip()
