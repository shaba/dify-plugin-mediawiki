from __future__ import annotations

from typing import Any

from .api import derive_api, siteinfo
from .errors import PageNotFound
from .htmlmd import html_to_markdown
from .http import Fetch, api_get, default_fetch
from .search import page_url


def get_page(
    title: str,
    base_url: str,
    *,
    fetch: Fetch = default_fetch,
    timeout: int = 30,
) -> dict[str, Any]:
    """Fetch an article via action=parse&prop=text (following redirects) and return markdown.

    Returns a dict: title, markdown, source_url.
    Raises PageNotFound if the page does not exist.
    """
    title = str(title or "").strip()
    if not title:
        raise PageNotFound("No page title provided")

    api_url = derive_api(base_url)
    data = api_get(
        api_url,
        {
            "action": "parse",
            "page": title,
            "prop": "text",
            "redirects": 1,
            "formatversion": 2,
        },
        fetch=fetch,
        timeout=timeout,
    )

    error = data.get("error")
    if error:
        info = str(error.get("info") or error.get("code") or "page not found")
        raise PageNotFound(f'Page "{title}" not found: {info}')

    parse = data.get("parse") or {}
    text = parse.get("text")
    if isinstance(text, dict):  # formatversion=1 returns {"*": html}
        text = text.get("*", "")
    markdown = html_to_markdown(str(text or ""))
    resolved_title = str(parse.get("title") or title)

    try:
        info = siteinfo(api_url, fetch=fetch, timeout=timeout)
        source_url = page_url(info["server"], info["articlepath"], resolved_title)
    except Exception:  # noqa: BLE001 — source_url is not critical
        source_url = ""

    return {
        "title": resolved_title,
        "markdown": markdown,
        "source_url": source_url,
    }
