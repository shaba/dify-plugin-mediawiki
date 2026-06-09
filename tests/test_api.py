import pytest

from mediawiki_client import derive_api
from mediawiki_client.api import normalize_server, validate_mediawiki
from mediawiki_client.errors import NotMediaWiki

from .conftest import make_router


def test_derive_api_bare_domain():
    assert derive_api("https://example.com") == "https://example.com/api.php"


def test_derive_api_bare_domain_with_trailing_slash():
    assert derive_api("https://example.com/") == "https://example.com/api.php"


def test_derive_api_no_scheme():
    assert derive_api("example.com") == "https://example.com/api.php"


def test_derive_api_direct_api_php():
    assert derive_api("https://example.com/api.php") == "https://example.com/api.php"


def test_derive_api_w_path_api_php():
    assert derive_api("https://example.com/w/api.php") == "https://example.com/w/api.php"


def test_derive_api_strips_query():
    assert derive_api("https://x.org/api.php?foo=bar") == "https://x.org/api.php"


def test_derive_api_empty_raises():
    with pytest.raises(NotMediaWiki):
        derive_api("   ")


def test_derive_api_rejects_non_http_scheme():
    with pytest.raises(NotMediaWiki):
        derive_api("ftp://example.com/api.php")


def test_normalize_server_protocol_relative():
    # The live API returns protocol-relative server for Wikimedia sites.
    assert (
        normalize_server("//en.wikipedia.org", "https://en.wikipedia.org/w/api.php")
        == "https://en.wikipedia.org"
    )


def test_normalize_server_empty_uses_api_origin():
    # Falls back to the api_url origin, not a stripped path segment.
    assert (
        normalize_server("", "https://example.com/w/api.php") == "https://example.com"
    )


def test_validate_mediawiki_ok(siteinfo_payload):
    fetch = make_router({"meta=siteinfo": siteinfo_payload})
    info = validate_mediawiki("https://example.com", fetch=fetch)
    assert "mediawiki" in info["generator"].lower()
    assert info["server"] == "https://example.com"


def test_validate_mediawiki_not_a_wiki():
    not_wiki = {"query": {"general": {"generator": "nginx", "server": "https://x.org"}}}
    fetch = make_router({"meta=siteinfo": not_wiki})
    with pytest.raises(NotMediaWiki):
        validate_mediawiki("https://x.org", fetch=fetch)


def test_validate_mediawiki_unreachable():
    def fetch(url, timeout=30):
        raise ConnectionError("boom")

    with pytest.raises(NotMediaWiki):
        validate_mediawiki("https://x.org", fetch=fetch)
