from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

from .api import derive_api, normalize_server, siteinfo_from_query
from .http import DEFAULT_TIMEOUT, Fetch, api_get, default_fetch

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    """Strip HTML tags (a search snippet contains <span class=...>) and normalize whitespace."""
    text = _TAG_RE.sub("", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def page_url(server: str, articlepath: str, title: str) -> str:
    encoded = quote(str(title).replace(" ", "_"), safe="/:")
    path = (articlepath or "/wiki/$1").replace("$1", encoded)
    return server.rstrip("/") + path


def search(
    base_url: str,
    query: str,
    *,
    limit: int = 5,
    fetch: Fetch = default_fetch,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """Full-text search via action=query&list=search.

    Returns a list of dicts with keys title, snippet (HTML stripped), url.
    """
    api_url = derive_api(base_url)
    limit = max(1, min(int(limit or 5), 50))
    # Combine the search with meta=siteinfo in a single api.php request, so result
    # URLs can be built from server+articlepath without a second round-trip.
    data = api_get(
        api_url,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "srprop": "snippet",
            "meta": "siteinfo",
            "siprop": "general",
        },
        fetch=fetch,
        timeout=timeout,
    )
    query_block = data.get("query") or {}
    hits = query_block.get("search") or []

    info = siteinfo_from_query(query_block)
    server = normalize_server(info["server"], api_url)
    articlepath = info["articlepath"]

    results: list[dict[str, Any]] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        title = str(hit.get("title") or "").strip()
        results.append(
            {
                "title": title,
                "snippet": strip_html(str(hit.get("snippet") or "")),
                "url": page_url(server, articlepath, title) if title else "",
            }
        )
    return results


def format_search(results: list[dict[str, Any]], query: str) -> str:
    if not results:
        return f'No results found for "{query}".'
    lines = [f'Found {len(results)} result(s) for "{query}"']
    for item in results:
        head = f"- {item['title']}"
        if item.get("url"):
            head += f" ({item['url']})"
        if item.get("snippet"):
            head += f"\n  {item['snippet']}"
        lines.append(head)
    return "\n".join(lines)
