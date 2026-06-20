from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import threading
import time
from typing import Any

from .config import default_app_dir


BRIDGE_TOKEN_FILE_NAME = "browser_bridge.json"


def bridge_token_path() -> Path:
    return default_app_dir() / BRIDGE_TOKEN_FILE_NAME


def browser_bridge_token() -> str:
    """Return the local-only bridge token, creating it without platform credentials."""
    path = bridge_token_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        token = payload.get("token") if isinstance(payload, dict) else None
        if isinstance(token, str) and token:
            return token
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    token = secrets.token_urlsafe(32)
    path.write_text(json.dumps({"token": token}) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return token


def _string(value: Any) -> str:
    return str(value) if value is not None else "0"


def _items(value: Any, fields: tuple[str, ...]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            result.append({field: _string(item.get(field)) for field in fields})
    return result


@dataclass(frozen=True)
class PlatformSummary:
    received_at: float
    current_token: str
    monthly_usage: str
    total_usage: str
    monthly_token_usage: str
    total_available_token_estimation: str
    normal_wallets: list[dict[str, str]]
    bonus_wallets: list[dict[str, str]]
    monthly_costs: list[dict[str, str]]

    @classmethod
    def from_response(cls, payload: dict[str, Any]) -> "PlatformSummary":
        if payload.get("code") != 0:
            raise ValueError("DeepSeek platform summary response was not successful")
        data = payload.get("data")
        if not isinstance(data, dict) or data.get("biz_code") != 0:
            raise ValueError("DeepSeek platform summary business response was not successful")
        business = data.get("biz_data")
        if not isinstance(business, dict):
            raise ValueError("DeepSeek platform summary did not contain usage data")
        return cls(
            received_at=time.time(),
            current_token=_string(business.get("current_token")),
            monthly_usage=_string(business.get("monthly_usage")),
            total_usage=_string(business.get("total_usage")),
            monthly_token_usage=_string(business.get("monthly_token_usage")),
            total_available_token_estimation=_string(
                business.get("total_available_token_estimation")
            ),
            normal_wallets=_items(
                business.get("normal_wallets"),
                ("currency", "balance", "token_estimation"),
            ),
            bonus_wallets=_items(
                business.get("bonus_wallets"),
                ("currency", "balance", "token_estimation"),
            ),
            monthly_costs=_items(business.get("monthly_costs"), ("currency", "amount")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "received_at": self.received_at,
            "current_token": self.current_token,
            "monthly_usage": self.monthly_usage,
            "total_usage": self.total_usage,
            "monthly_token_usage": self.monthly_token_usage,
            "total_available_token_estimation": self.total_available_token_estimation,
            "normal_wallets": self.normal_wallets,
            "bonus_wallets": self.bonus_wallets,
            "monthly_costs": self.monthly_costs,
        }


class PlatformSummaryStore:
    """In-memory latest snapshot received from the optional browser bridge."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._summary: PlatformSummary | None = None

    def update(self, payload: dict[str, Any]) -> PlatformSummary:
        summary = PlatformSummary.from_response(payload)
        with self._lock:
            self._summary = summary
        return summary

    def snapshot(self) -> dict[str, Any] | None:
        with self._lock:
            return self._summary.to_dict() if self._summary is not None else None


def main(argv: list[str] | None = None) -> int:
    del argv
    print(browser_bridge_token())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
