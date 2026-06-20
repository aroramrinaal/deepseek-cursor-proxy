from __future__ import annotations

import unittest

from deepseek_cursor_proxy.platform_summary import PlatformSummary, PlatformSummaryStore


def sample_response() -> dict[str, object]:
    return {
        "code": 0,
        "data": {
            "biz_code": 0,
            "biz_data": {
                "current_token": 10000000,
                "monthly_usage": "205847368",
                "total_usage": 0,
                "monthly_token_usage": "205847368",
                "total_available_token_estimation": "101177480",
                "normal_wallets": [
                    {"currency": "USD", "balance": "42.49", "token_estimation": "101177480"}
                ],
                "bonus_wallets": [],
                "monthly_costs": [{"currency": "USD", "amount": "5.96"}],
            },
        },
    }


class PlatformSummaryTests(unittest.TestCase):
    def test_extracts_the_platform_usage_summary(self) -> None:
        summary = PlatformSummary.from_response(sample_response())
        self.assertEqual(summary.monthly_token_usage, "205847368")
        self.assertEqual(summary.normal_wallets[0]["balance"], "42.49")

    def test_store_only_retains_the_latest_summary_in_memory(self) -> None:
        store = PlatformSummaryStore()
        self.assertIsNone(store.snapshot())
        store.update(sample_response())
        self.assertEqual(store.snapshot()["monthly_usage"], "205847368")

    def test_rejects_non_success_responses(self) -> None:
        with self.assertRaises(ValueError):
            PlatformSummary.from_response({"code": 1})
