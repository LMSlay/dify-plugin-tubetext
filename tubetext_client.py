"""Small Apify API client shared by all TubeText tools.

Every tool starts one TubeText Actor run on the user's own Apify account, waits
for it to finish and reads the run's dataset. Nothing is stored by the plugin.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import requests

API_BASE = "https://api.apify.com/v2"
CONSOLE_RUN_URL = "https://console.apify.com/view/runs/{run_id}"
USER_AGENT = "tubetext-dify-plugin/0.1"

# Each HTTP call waits at most this long; Apify's waitForFinish is capped at 60 s.
HTTP_TIMEOUT = 75
WAIT_STEP = 60
PAGE_SIZE = 1000
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}

ACTORS = {
    "tiktok_shop": "tubetext~tiktok-shop-product-scraper",
    "aliexpress": "tubetext~aliexpress-search-scraper",
    "youtube_transcript": "tubetext~youtube-transcript-fast",
    "tiktok_transcript": "tubetext~tiktok-transcript",
}


class TubeTextError(Exception):
    """A message that is safe to show to the user (never contains the token)."""


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT}


def _raise_for_apify(resp: requests.Response) -> None:
    if resp.status_code < 400:
        return
    try:
        err = resp.json().get("error", {})
    except ValueError:
        err = {}
    err_type = err.get("type", "")
    message = err.get("message", "") or resp.text[:300]
    if resp.status_code == 401 or err_type in {"token-not-valid", "user-or-token-not-found"}:
        raise TubeTextError(
            "Apify did not accept the API token. Copy a valid token from Apify Console > "
            "Settings > API & Integrations and update the TubeText credentials."
        )
    if resp.status_code == 402 or "not-enough-usage" in err_type or "insufficient" in message.lower():
        raise TubeTextError(
            "Your Apify account has no remaining usage credit for this run. "
            f"Add credit or upgrade your Apify plan, then retry. Apify said: {message}"
        )
    if resp.status_code == 404:
        raise TubeTextError(f"Apify could not find the requested Actor or run. Apify said: {message}")
    if resp.status_code == 400:
        raise TubeTextError(f"Apify rejected the input. Check the tool parameters. Apify said: {message}")
    if resp.status_code == 429:
        raise TubeTextError("Apify is rate limiting this token. Wait a minute and retry.")
    raise TubeTextError(f"Apify returned HTTP {resp.status_code}. Apify said: {message}")


# Errors raised before the request reaches Apify, so retrying cannot start a run twice.
SAFE_TO_RETRY = (requests.exceptions.SSLError, requests.exceptions.ConnectTimeout, requests.exceptions.ProxyError)


def _request(method: str, url: str, token: str, **kwargs: Any) -> Any:
    for attempt in range(3):
        try:
            resp = requests.request(method, url, headers=_headers(token), timeout=HTTP_TIMEOUT, **kwargs)
            break
        except SAFE_TO_RETRY as e:
            if attempt == 2:
                raise TubeTextError(f"Could not reach the Apify API ({type(e).__name__}). Retry in a moment.") from None
            time.sleep(1 + attempt * 2)
        except requests.RequestException as e:
            raise TubeTextError(f"Could not reach the Apify API ({type(e).__name__}). Retry in a moment.") from None
    _raise_for_apify(resp)
    return resp.json()


def validate_token(token: str) -> str:
    if not token or not token.strip():
        raise TubeTextError("Enter your Apify API token.")
    data = _request("GET", f"{API_BASE}/users/me", token.strip())
    return data.get("data", {}).get("username", "")


def start_run(token: str, actor: str, actor_input: dict[str, Any], wait: int = 0) -> dict[str, Any]:
    data = _request(
        "POST",
        f"{API_BASE}/acts/{actor}/runs",
        token,
        params={"waitForFinish": max(0, min(WAIT_STEP, wait))},
        json=actor_input,
    )
    return data["data"]


def wait_for_run(token: str, run: dict[str, Any], max_wait_seconds: int) -> dict[str, Any]:
    deadline = time.monotonic() + max_wait_seconds
    while run.get("status") not in TERMINAL_STATUSES:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        wait = int(max(1, min(WAIT_STEP, remaining)))
        data = _request("GET", f"{API_BASE}/actor-runs/{run['id']}", token, params={"waitForFinish": wait})
        run = data["data"]
    return run


def get_run(token: str, run_id: str) -> dict[str, Any]:
    return _request("GET", f"{API_BASE}/actor-runs/{run_id}", token)["data"]


def get_dataset_items(token: str, dataset_id: str, limit: int, offset: int = 0) -> list[dict[str, Any]]:
    """Read up to ``limit`` items, following Apify's pagination."""
    items: list[dict[str, Any]] = []
    while len(items) < limit:
        page = min(PAGE_SIZE, limit - len(items))
        batch = _request(
            "GET",
            f"{API_BASE}/datasets/{dataset_id}/items",
            token,
            params={"clean": "true", "format": "json", "offset": offset, "limit": page},
        )
        if not batch:
            break
        items.extend(batch)
        offset += len(batch)
        if len(batch) < page:
            break
    return items


def run_actors(
    token: str,
    jobs: list[tuple[str, dict[str, Any], int]],
    max_wait_seconds: int,
) -> tuple[list[tuple[str, dict[str, Any]]], list[dict[str, Any]]]:
    """Start one run per job (they run in parallel on Apify), wait for all of them
    within one shared time budget and return ``(actor_key, item)`` pairs plus run metadata."""
    deadline = time.monotonic() + max_wait_seconds
    # Start every run first (no waiting) so they run in parallel, then wait for each.
    started = [(key, start_run(token, ACTORS[key], actor_input), max_items) for key, actor_input, max_items in jobs]
    pairs: list[tuple[str, dict[str, Any]]] = []
    runs: list[dict[str, Any]] = []
    for key, run, max_items in started:
        run = wait_for_run(token, run, max(0, int(deadline - time.monotonic())))
        status = run.get("status")
        meta = {
            "actor": ACTORS[key].replace("~", "/"),
            "runId": run["id"],
            "runStatus": status,
            "runUrl": CONSOLE_RUN_URL.format(run_id=run["id"]),
        }
        if status not in TERMINAL_STATUSES:
            meta["note"] = (
                f"Still {status} after {max_wait_seconds} s. The run keeps going on Apify; "
                "fetch its results later with the 'Get Run Results' tool and this runId."
            )
            runs.append(meta)
            continue
        items = get_dataset_items(token, run["defaultDatasetId"], max_items)
        if status != "SUCCEEDED":
            meta["note"] = f"The run ended with status {status}; partial results are returned. See runUrl for the log."
            if not items and len(jobs) == 1:
                raise TubeTextError(
                    f"The Apify run ended with status {status} and returned no results. "
                    f"Open {meta['runUrl']} to see the log."
                )
        pairs.extend((key, item) for item in items)
        runs.append(meta)
    return pairs, runs


def split_list(value: Any, allow_commas: bool = True) -> list[str]:
    """Accept a JSON array, newline-separated text or (optionally) comma-separated text."""
    if value is None:
        return []
    if isinstance(value, list):
        parts = [str(v) for v in value]
    else:
        text = str(value).strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except ValueError:
                pass
        pattern = r"[\n\r,]+" if allow_commas else r"[\n\r]+"
        parts = re.split(pattern, text)
    return [p.strip() for p in parts if p and p.strip()]


def pick(item: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {f: item.get(f) for f in fields if item.get(f) is not None}


def to_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return default
    return max(low, min(high, n))
