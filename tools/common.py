from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin.entities.tool import ToolInvokeMessage

from tubetext_client import TubeTextError, pick, run_actors, to_int


class TubeTextMixin:
    """Mixed into each tool class (the SDK expects exactly one Tool subclass per file).

    Shared flow: build input -> run Actor -> trim items -> emit JSON (+ optional text)."""

    simple_fields: list[str] = []

    def build_jobs(self, params: dict[str, Any]) -> list[tuple[str, dict[str, Any], int]]:
        """Return one ``(actor_key, actor_input, max_items)`` tuple per Actor run."""
        raise NotImplementedError

    def normalize(self, actor_key: str, item: dict[str, Any]) -> dict[str, Any]:
        return item

    def to_text(self, items: list[dict[str, Any]]) -> str | None:
        return None

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        token = (self.runtime.credentials or {}).get("apify_api_token", "").strip()
        if not token:
            raise ValueError("Add your Apify API token in the TubeText plugin credentials.")
        try:
            jobs = self.build_jobs(tool_parameters)
            wait = to_int(tool_parameters.get("max_wait_seconds"), 240, 30, 600)
            pairs, runs = run_actors(token, jobs, wait)
        except TubeTextError as e:
            raise ValueError(str(e)) from None

        items = [self.normalize(key, item) for key, item in pairs]
        if tool_parameters.get("output", "simplified") != "full":
            items = [pick(i, self.simple_fields) for i in items]
        text = self.to_text(items)
        if text:
            yield self.create_text_message(text)
        yield self.create_json_message({"count": len(items), "items": items, "runs": runs})


def transcripts_as_text(items: list[dict[str, Any]], author_field: str = "author") -> str:
    blocks = []
    for item in items:
        head = f"# {item.get('title') or item.get('url') or item.get('input')}"
        if item.get(author_field):
            head += f" ({item[author_field]})"
        body = item.get("timestampedText") or item.get("transcript") or f"[{item.get('status')}] {item.get('error', '')}"
        blocks.append(f"{head}\n{item.get('url', '')}\n\n{body}")
    return "\n\n---\n\n".join(blocks)
