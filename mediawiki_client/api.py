from __future__ import annotations

from urllib.parse import urlparse

from .errors import NotMediaWiki
from .http import VALIDATE_TIMEOUT, Fetch, api_get, default_fetch


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


def origin_of(api_url: str) -> str:
    """Return the scheme://netloc origin of an api.php URL (no path)."""
    parsed = urlparse(api_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return api_url


def normalize_server(server: str, api_url: str) -> str:
    """Coerce a siteinfo ``server`` into an absolute scheme://host base.

    MediaWiki frequently reports ``server`` as protocol-relative (``//host``)
    or even host-relative; turn it into an absolute URL using the scheme (and,
    when needed, the host) derived from ``api_url`` so emitted links are usable.
    """
    server = (server or "").strip()
    api_scheme = urlparse(api_url).scheme or "https"
    if not server:
        return origin_of(api_url)
    if server.startswith("//"):
        return f"{api_scheme}:{server}"
    if "://" not in server:
        # Host-relative or bare host: anchor it on the api_url origin/scheme.
        if server.startswith("/"):
            return origin_of(api_url).rstrip("/") + server
        return f"{api_scheme}://{server}"
    return server


def siteinfo_from_query(query_block: dict) -> dict:
    """Parse the ``query.general`` block of an action=query&meta=siteinfo response."""
    general = (query_block or {}).get("general") or {}
    return {
        "generator": str(general.get("generator") or ""),
        "server": str(general.get("server") or ""),
        "sitename": str(general.get("sitename") or ""),
        "articlepath": str(general.get("articlepath") or "/wiki/$1"),
    }


def siteinfo(api_url: str, *, fetch: Fetch = default_fetch, timeout: int = VALIDATE_TIMEOUT) -> dict:
    """action=query&meta=siteinfo — general information about the site."""
    data = api_get(
        api_url,
        {"action": "query", "meta": "siteinfo", "siprop": "general"},
        fetch=fetch,
        timeout=timeout,
    )
    return siteinfo_from_query(data.get("query") or {})


def validate_mediawiki(
    base_url: str, *, fetch: Fetch = default_fetch, timeout: int = VALIDATE_TIMEOUT
) -> dict:
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
