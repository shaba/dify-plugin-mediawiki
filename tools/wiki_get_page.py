from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from mediawiki_client import PageNotFound, get_page


class GetPageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        base_url = str(self.runtime.credentials.get("base_url") or "").strip().rstrip("/")
        title = str(tool_parameters.get("title") or "").strip()

        if not base_url:
            yield self.create_text_message("Error: the plugin's base_url is not configured")
            return
        if not title:
            yield self.create_text_message("Error: the 'title' parameter is required")
            return

        try:
            page = get_page(title, base_url)
        except PageNotFound as exc:
            yield self.create_text_message(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            yield self.create_text_message(f"MediaWiki request error: {exc}")
            return

        body = page["markdown"]
        if page.get("source_url"):
            body = f"# {page['title']}\n\n{body}\n\nSource: {page['source_url']}"
        yield self.create_text_message(body)
        yield self.create_json_message(page)
