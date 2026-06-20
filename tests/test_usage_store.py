from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from deepseek_cursor_proxy.usage_store import UsageStore


class UsageStoreTests(unittest.TestCase):
    def test_records_and_summarizes_usage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = UsageStore(Path(temp_dir) / "usage.sqlite3")
            try:
                store.record(
                    {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                        "prompt_cache_hit_tokens": 6,
                        "prompt_cache_miss_tokens": 4,
                        "completion_tokens_details": {"reasoning_tokens": 3},
                    },
                    model="deepseek-v4-pro",
                    streamed=True,
                    elapsed_ms=234,
                )
                self.assertEqual(
                    store.summary(),
                    {
                        "requests": 1,
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "reasoning_tokens": 3,
                        "total_tokens": 15,
                        "cache_hit_tokens": 6,
                        "cache_miss_tokens": 4,
                        "elapsed_ms": 234,
                    },
                )
            finally:
                store.close()
