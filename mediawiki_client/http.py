from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

import requests


def _read_manifest_version() -> str:
    """Read the authoritative plugin version from manifest.yaml at import time.

    The top-level ``version:`` field in manifest.yaml is the single source of
    truth; deriving it here keeps the User-Agent from silently drifting out of
    sync with the published version. Falls back to ``0`` if the manifest cannot
    be located (e.g. the core package is vendored without it).
    """
    manifest = Path(__file__).resolve().parent.parent / "manifest.yaml"
    try:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*version\s*:\s*(['\"]?)([^'\"\s#]+)\1", line)
            if match:
                return match.group(2)
    except OSError:
        pass
    return "0"


PLUGIN_VERSION = _read_manifest_version()
USER_AGENT = f"dify-plugin-mediawiki/{PLUGIN_VERSION}"

# Coordinated HTTP timeouts (seconds). DEFAULT_TIMEOUT is used for runtime reads
# (search / get_page); VALIDATE_TIMEOUT for the lighter siteinfo / credential
# checks. Keeping validation close to the runtime value avoids a credential
# check passing while a real read times out on a slow wiki.
DEFAULT_TIMEOUT = 30
VALIDATE_TIMEOUT = 20

# fetch callable: (url, timeout) -> parsed JSON (dict). Overridden in tests.
Fetch = Callable[[str, int], Any]


def default_fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> Any:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    response.raise_for_status()
    return response.json()


def api_get(
    api_url: str,
    params: dict,
    *,
    fetch: Fetch,
    timeout: int,
    check_error: bool = True,
) -> dict:
    """GET api.php with JSON-format parameters. Returns the parsed response.

    A MediaWiki ``action=query`` can return HTTP 200 with a top-level ``error``
    object (e.g. ``readapidenied`` on a private wiki). When ``check_error`` is
    True this raises :class:`MediaWikiAPIError` so callers don't silently treat
    it as an empty result. Callers that need to map specific error codes to their
    own exceptions (e.g. get_page → PageNotFound) pass ``check_error=False`` and
    inspect ``data["error"]`` themselves.
    """
    from .errors import MediaWikiAPIError, MediaWikiError

    query = dict(params)
    query.setdefault("format", "json")
    sep = "&" if "?" in api_url else "?"
    data = fetch(f"{api_url}{sep}{urlencode(query)}", timeout)
    if not isinstance(data, dict):
        raise MediaWikiError("MediaWiki API returned a non-JSON response")
    if check_error:
        error = data.get("error")
        if isinstance(error, dict):
            raise MediaWikiAPIError(
                str(error.get("code") or ""),
                str(error.get("info") or error.get("code") or "MediaWiki API error"),
            )
    return data
