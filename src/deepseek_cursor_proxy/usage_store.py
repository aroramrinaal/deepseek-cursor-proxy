from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any


USAGE_FIELDS = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "prompt_cache_hit_tokens",
    "prompt_cache_miss_tokens",
)


def _count(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def reasoning_tokens(usage: dict[str, Any]) -> int:
    details = usage.get("completion_tokens_details")
    if not isinstance(details, dict):
        return 0
    return _count(details.get("reasoning_tokens"))


class UsageStore:
    """Small local ledger for successful requests routed through this proxy."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self.path.chmod(0o600)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY,
                created_at REAL NOT NULL,
                model TEXT NOT NULL,
                streamed INTEGER NOT NULL,
                elapsed_ms INTEGER NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                reasoning_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cache_hit_tokens INTEGER NOT NULL,
                cache_miss_tokens INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def record(
        self,
        usage: dict[str, Any] | None,
        *,
        model: str,
        streamed: bool,
        elapsed_ms: int,
    ) -> None:
        if not isinstance(usage, dict):
            return
        values = {field: _count(usage.get(field)) for field in USAGE_FIELDS}
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO usage_events(
                    created_at, model, streamed, elapsed_ms, prompt_tokens,
                    completion_tokens, reasoning_tokens, total_tokens,
                    cache_hit_tokens, cache_miss_tokens
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    model,
                    int(streamed),
                    max(0, elapsed_ms),
                    values["prompt_tokens"],
                    values["completion_tokens"],
                    reasoning_tokens(usage),
                    values["total_tokens"],
                    values["prompt_cache_hit_tokens"],
                    values["prompt_cache_miss_tokens"],
                ),
            )
            self._conn.commit()

    def summary(self, *, since: float | None = None) -> dict[str, int]:
        query = """
            SELECT
                COUNT(*),
                COALESCE(SUM(prompt_tokens), 0),
                COALESCE(SUM(completion_tokens), 0),
                COALESCE(SUM(reasoning_tokens), 0),
                COALESCE(SUM(total_tokens), 0),
                COALESCE(SUM(cache_hit_tokens), 0),
                COALESCE(SUM(cache_miss_tokens), 0),
                COALESCE(SUM(elapsed_ms), 0)
            FROM usage_events
        """
        params: tuple[float, ...] = ()
        if since is not None:
            query += " WHERE created_at >= ?"
            params = (since,)
        with self._lock:
            row = self._conn.execute(query, params).fetchone()
        assert row is not None
        keys = (
            "requests",
            "prompt_tokens",
            "completion_tokens",
            "reasoning_tokens",
            "total_tokens",
            "cache_hit_tokens",
            "cache_miss_tokens",
            "elapsed_ms",
        )
        return dict(zip(keys, (int(value) for value in row), strict=True))

    @staticmethod
    def start_of_today() -> float:
        now = datetime.now().astimezone()
        return now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
