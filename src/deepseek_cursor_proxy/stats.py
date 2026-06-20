from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .platform_summary import browser_bridge_token


def fetch_platform_summary(proxy_base_url: str) -> dict[str, Any]:
    request = Request(
        f"{proxy_base_url.rstrip('/')}/v1/platform-summary",
        headers={"X-DeepSeek-Bridge-Token": browser_bridge_token()},
    )
    with urlopen(request, timeout=3) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Local browser bridge returned an unexpected response")
    return payload


def print_platform_summary(summary: dict[str, Any]) -> None:
    print("Live DeepSeek Platform account summary")
    print("  monthly tokens " + str(summary.get("monthly_token_usage", "?")))
    print("  estimated available tokens " + str(
        summary.get("total_available_token_estimation", "?")
    ))
    print("  current token allowance " + str(summary.get("current_token", "?")))
    for wallet in summary.get("normal_wallets", []):
        if isinstance(wallet, dict):
            print("  wallet " + str(wallet.get("currency", "?")) +
                  " " + str(wallet.get("balance", "?")) +
                  " | estimated tokens " + str(wallet.get("token_estimation", "?")))
    for cost in summary.get("monthly_costs", []):
        if isinstance(cost, dict):
            print("  monthly cost " + str(cost.get("currency", "?")) +
                  " " + str(cost.get("amount", "?")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Show the live DeepSeek Platform summary from the browser bridge"
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument(
        "--proxy-url",
        default="http://127.0.0.1:9000",
        help="Local proxy URL used by the browser bridge",
    )
    args = parser.parse_args(argv)

    try:
        summary = fetch_platform_summary(args.proxy_url)
    except (HTTPError, URLError, ValueError, json.JSONDecodeError) as exc:
        message = (
            "No live platform summary yet. Open and refresh "
            "https://platform.deepseek.com/usage with the bridge extension enabled."
        )
        if args.json:
            print(json.dumps({"error": message, "details": str(exc)}, indent=2))
        else:
            print(message)
        return 1

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_platform_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
