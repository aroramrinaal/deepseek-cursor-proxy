from __future__ import annotations

import argparse
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import default_usage_path
from .usage_store import UsageStore


def fetch_balance(api_key: str, base_url: str) -> dict[str, Any]:
    request = Request(
        f"{base_url.rstrip('/')}/user/balance",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("DeepSeek returned an unexpected balance response")
    return payload


def format_count(value: int) -> str:
    return f"{value:,}"


def print_summary(label: str, summary: dict[str, int]) -> None:
    print(f"{label}: {format_count(summary['requests'])} request(s), "
          f"{format_count(summary['total_tokens'])} total tokens")
    print("  input " + format_count(summary["prompt_tokens"]) +
          " | output " + format_count(summary["completion_tokens"]) +
          " | reasoning " + format_count(summary["reasoning_tokens"]))
    print("  cache hit " + format_count(summary["cache_hit_tokens"]) +
          " | cache miss " + format_count(summary["cache_miss_tokens"]) +
          " | model time " + f"{summary['elapsed_ms'] / 1000:.1f}s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show token usage recorded by deepseek-cursor-proxy"
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--no-balance", action="store_true", help="Do not request the live DeepSeek balance"
    )
    parser.add_argument(
        "--base-url", default="https://api.deepseek.com", help="DeepSeek API base URL"
    )
    args = parser.parse_args(argv)

    store = UsageStore(default_usage_path())
    try:
        result: dict[str, Any] = {
            "today": store.summary(since=store.start_of_today()),
            "all_time": store.summary(),
            "ledger_path": str(store.path),
        }
    finally:
        store.close()

    key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("DEEPSEEK_KEY")
    balance_error: str | None = None
    if not args.no_balance:
        if key:
            try:
                result["balance"] = fetch_balance(key, args.base_url)
            except (HTTPError, URLError, ValueError, json.JSONDecodeError) as exc:
                balance_error = str(exc)
        else:
            balance_error = "Set DEEPSEEK_API_KEY to include live balance."

    if args.json:
        if balance_error:
            result["balance_error"] = balance_error
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    print("DeepSeek via Cursor proxy")
    print_summary("Today", result["today"])
    print_summary("All time", result["all_time"])
    if "balance" in result:
        balance = result["balance"]
        available = "available" if balance.get("is_available") else "unavailable"
        print(f"Live DeepSeek balance: {available}")
        for info in balance.get("balance_infos", []):
            if isinstance(info, dict):
                print(
                    "  " + str(info.get("currency", "?")) +
                    " total " + str(info.get("total_balance", "?")) +
                    " | topped up " + str(info.get("topped_up_balance", "?")) +
                    " | granted " + str(info.get("granted_balance", "?"))
                )
    elif balance_error:
        print(f"Live balance: not checked ({balance_error})")
    print(f"Ledger: {result['ledger_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
