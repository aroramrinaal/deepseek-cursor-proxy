from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import sys
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


DEEPSEEK_BLUE = "\033[38;2;77;107;254m"
RESET = "\033[0m"


def format_tokens(value: Any) -> str:
    try:
        return f"{int(Decimal(str(value))):,}"
    except (InvalidOperation, TypeError, ValueError):
        return "?"


def format_amount(value: Any) -> str:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return "?"
    return f"{amount:,.4f}".rstrip("0").rstrip(".")


def row(label: str, value: str) -> str:
    return f"  {label:<22}{value}"


def render_platform_summary(summary: dict[str, Any], *, color: bool) -> str:
    heading = "DeepSeek Platform"
    if color:
        heading = f"{DEEPSEEK_BLUE}{heading}{RESET}"
    lines = [heading, "Live account usage"]
    lines.extend(
        [
            row("Monthly tokens", f"{format_tokens(summary.get('monthly_token_usage'))} tokens"),
            row("Available estimate", f"{format_tokens(summary.get('total_available_token_estimation'))} tokens"),
            row("Current allowance", f"{format_tokens(summary.get('current_token'))} tokens"),
        ]
    )
    for wallet in summary.get("normal_wallets", []):
        if isinstance(wallet, dict):
            currency = str(wallet.get("currency", "?"))
            lines.append(row(f"Wallet ({currency})", format_amount(wallet.get("balance"))))
            lines.append(row("  Estimated capacity", f"{format_tokens(wallet.get('token_estimation'))} tokens"))
    for wallet in summary.get("bonus_wallets", []):
        if isinstance(wallet, dict) and format_amount(wallet.get("balance")) != "0":
            currency = str(wallet.get("currency", "?"))
            lines.append(row(f"Bonus ({currency})", format_amount(wallet.get("balance"))))
    for cost in summary.get("monthly_costs", []):
        if isinstance(cost, dict):
            lines.append(row(f"Monthly spend ({cost.get('currency', '?')})", format_amount(cost.get("amount"))))
    return "\n".join(lines)


def print_platform_summary(summary: dict[str, Any]) -> None:
    print(render_platform_summary(summary, color=sys.stdout.isatty()))


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
