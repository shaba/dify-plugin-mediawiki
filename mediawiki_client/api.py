from __future__ import annotations

from urllib.parse import urlparse

from .errors import NotMediaWiki
from .http import Fetch, api_get, default_fetch


def derive_api(base_url: str) -> str:
    """Derive the api.php endpoint from an arbitrary wiki URL.

    Accepts both a bare domain (https://example.com) and a direct
    path to api.php (https://example.com/api.php or .../w/api.php).
    """
    raw = str(base_url or "").strip()
    if not raw:
        raise NotMediaWiki("base_url is empty")
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.netloc:
        raise NotMediaWiki(f"Invalid base_url: {base_url!r}")
    path = parsed.path.split("?")[0]
    if path.rstrip("/").endswith("api.php"):
        return f"{parsed.scheme}://{parsed.netloc}{path.rstrip('/')}"
    return f"{parsed.scheme}://{parsed.netloc}/api.php"


def siteinfo(api_url: str, *, fetch: Fetch = default_fetch, timeout: int = 20) -> dict:
    """action=query&meta=siteinfo — general information about the site."""
    data = api_get(
        api_url,
        {"action": "query", "meta": "siteinfo", "siprop": "general"},
        fetch=fetch,
        timeout=timeout,
    )
    general = (data.get("query") or {}).get("general") or {}
    return {
        "generator": str(general.get("generator") or ""),
        "server": str(general.get("server") or ""),
        "sitename": str(general.get("sitename") or ""),
        "articlepath": str(general.get("articlepath") or "/wiki/$1"),
    }


def validate_mediawiki(base_url: str, *, fetch: Fetch = default_fetch, timeout: int = 20) -> dict:
    """Check that base_url points to a working MediaWiki.

    Returns siteinfo on success, otherwise raises NotMediaWiki.
    """
    api_url = derive_api(base_url)
    try:
        info = siteinfo(api_url, fetch=fetch, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 — wrap the cause in a clear error
        raise NotMediaWiki(f"Site unreachable at {api_url}: {exc}") from exc
    if "mediawiki" not in info["generator"].lower():
        raise NotMediaWiki(
            f"{api_url} does not look like MediaWiki (generator={info['generator'] or 'none'})"
        )
    return info
