from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from mediawiki_client import validate_mediawiki
from mediawiki_client.http import VALIDATE_TIMEOUT


class MediaWikiProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        base_url = str(credentials.get("base_url") or "").strip().rstrip("/")
        if not base_url:
            raise ToolProviderCredentialValidationError(
                "base_url is required (e.g. https://example.com)"
            )
        try:
            validate_mediawiki(base_url, timeout=VALIDATE_TIMEOUT)
        except Exception as exc:  # noqa: BLE001 — surface the cause to the user
            raise ToolProviderCredentialValidationError(str(exc)) from exc
