from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlencode

import requests

USER_AGENT = "dify-plugin-mediawiki/0.0.1"

# fetch callable: (url, timeout) -> parsed JSON (dict). Overridden in tests.
Fetch = Callable[[str, int], Any]


def default_fetch(url: str, timeout: int = 30) -> Any:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def api_get(api_url: str, params: dict, *, fetch: Fetch, timeout: int) -> dict:
    """GET api.php with JSON-format parameters. Returns the parsed response."""
    query = dict(params)
    query.setdefault("format", "json")
    sep = "&" if "?" in api_url else "?"
    data = fetch(f"{api_url}{sep}{urlencode(query)}", timeout)
    if not isinstance(data, dict):
        from .errors import MediaWikiError

        raise MediaWikiError("MediaWiki API returned a non-JSON response")
    return data
