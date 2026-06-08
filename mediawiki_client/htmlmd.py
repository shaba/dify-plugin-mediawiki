"""Lightweight cleanup of MediaWiki HTML (action=parse) and conversion to markdown.

No third-party dependencies (bs4/markdownify) — stdlib only, to keep the plugin
dependency-free. Sufficient for wiki article text: headings, paragraphs, lists,
links, and basic formatting.
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser

# MediaWiki noise blocks that should be dropped entirely along with their content.
_NOISE_CLASSES = (
    "mw-editsection",
    "navbox",
    "metadata",
    "noprint",
    "mw-empty-elt",
    "toc",
    "mw-jump-link",
    "printfooter",
    "mw-references-wrap",
    "reference",
)

_DROP_TAGS = ("script", "style", "sup", "table")


class _MarkdownExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip_depth = 0
        self._skip_tag: str | None = None
        self._list_stack: list[str] = []

    # --- skipping of noise subtrees ---
    def _is_noise(self, attrs: list[tuple[str, str | None]]) -> bool:
        cls = ""
        for name, value in attrs:
            if name == "class" and value:
                cls = value
        return any(noise in cls for noise in _NOISE_CLASSES)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth:
            if tag == self._skip_tag:
                self._skip_depth += 1
            return
        if tag in _DROP_TAGS or self._is_noise(attrs):
            self._skip_depth = 1
            self._skip_tag = tag
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.parts.append("\n\n" + "#" * level + " ")
        elif tag == "p":
            self.parts.append("\n\n")
        elif tag in ("ul", "ol"):
            self._list_stack.append(tag)
            self.parts.append("\n")
        elif tag == "li":
            indent = "  " * max(0, len(self._list_stack) - 1)
            marker = "- " if (not self._list_stack or self._list_stack[-1] == "ul") else "1. "
            self.parts.append("\n" + indent + marker)
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")
        elif tag in ("br",):
            self.parts.append("\n")
        elif tag in ("pre", "code"):
            self.parts.append("`")

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
            self.parts.append("\n")
        elif tag in ("b", "strong"):
            self.parts.append("**")
        elif tag in ("i", "em"):
            self.parts.append("*")
        elif tag in ("pre", "code"):
            self.parts.append("`")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)


def html_to_markdown(fragment_html: str) -> str:
    """Clean article HTML from action=parse and return markdown."""
    parser = _MarkdownExtractor()
    parser.feed(fragment_html or "")
    text = html.unescape("".join(parser.parts))
    # collapse extra blank lines and whitespace
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()
