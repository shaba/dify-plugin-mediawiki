from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from mediawiki_client import format_search, search


class SearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url = str(self.runtime.credentials.get("base_url") or "").strip().rstrip("/")
        query = str(tool_parameters.get("query") or "").strip()
        try:
            limit = int(tool_parameters.get("limit") or 5)
        except (TypeError, ValueError):
            limit = 5

        if not base_url:
            yield self.create_text_message("Error: the plugin's base_url is not configured")
            return
        if not query:
            yield self.create_text_message("Error: the 'query' parameter is required")
            return

        try:
            results = search(base_url, query, limit=limit)
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"MediaWiki request error: {exc}")
            return

        yield self.create_text_message(format_search(results, query))
        yield self.create_json_message({"query": query, "count": len(results), "results": results})
