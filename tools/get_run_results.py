import re
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tubetext_client import CONSOLE_RUN_URL, TubeTextError, get_dataset_items, get_run, to_int


class GetRunResultsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        token = (self.runtime.credentials or {}).get("apify_api_token", "").strip()
        run_id = str(tool_parameters.get("run_id") or "").strip()
        if not run_id:
            raise ValueError("Enter the 'Run ID' returned by an earlier TubeText call.")
        if not re.fullmatch(r"[A-Za-z0-9]{8,32}", run_id):
            raise ValueError("'Run ID' should look like 'aBcD1234eFgH5678' (letters and digits only).")
        limit = to_int(tool_parameters.get("limit"), 100, 1, 10000)
        offset = to_int(tool_parameters.get("offset"), 0, 0, 10_000_000)
        try:
            run = get_run(token, run_id)
            items = get_dataset_items(token, run["defaultDatasetId"], limit, offset)
        except TubeTextError as e:
            raise ValueError(str(e)) from None
        yield self.create_json_message({
            "count": len(items),
            "offset": offset,
            "items": items,
            "runId": run_id,
            "runStatus": run.get("status"),
            "runUrl": CONSOLE_RUN_URL.format(run_id=run_id),
        })
