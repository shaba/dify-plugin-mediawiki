import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_router(mapping: dict[str, dict]):
    """Build a fetch(url, timeout) that picks a fixture by a substring in the URL.

    mapping: URL substring -> parsed JSON response.
    """

    def fetch(url: str, timeout: int = 30):
        for needle, payload in mapping.items():
            if needle in url:
                return payload
        raise AssertionError(f"unexpected URL in test: {url}")

    return fetch


@pytest.fixture
def siteinfo_payload():
    return load_fixture("siteinfo_sample.json")


@pytest.fixture
def search_payload():
    return load_fixture("search_systemd.json")


@pytest.fixture
def parse_payload():
    return load_fixture("parse_systemd.json")


@pytest.fixture
def parse_missing_payload():
    return load_fixture("parse_missing.json")
