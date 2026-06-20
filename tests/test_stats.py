from __future__ import annotations

import unittest

from deepseek_cursor_proxy.stats import format_amount, format_tokens, render_platform_summary


class StatsFormattingTests(unittest.TestCase):
    def test_formats_tokens_with_grouping(self) -> None:
        self.assertEqual(format_tokens("205870311"), "205,870,311")
        self.assertEqual(format_tokens(10000000), "10,000,000")

    def test_formats_amounts_without_insignificant_precision(self) -> None:
        self.assertEqual(format_amount("42.4942701664000000"), "42.4943")
        self.assertEqual(format_amount("5.9646920938000000"), "5.9647")

    def test_renders_a_compact_account_readout(self) -> None:
        output = render_platform_summary(
            {
                "monthly_token_usage": "205870311",
                "total_available_token_estimation": "101176833",
                "current_token": "10000000",
                "normal_wallets": [
                    {"currency": "USD", "balance": "42.4942701664000000", "token_estimation": "101176833"}
                ],
                "bonus_wallets": [],
                "monthly_costs": [{"currency": "USD", "amount": "5.9646920938000000"}],
            },
            color=False,
        )
        self.assertIn("205,870,311 tokens", output)
        self.assertIn("42.4943", output)
        self.assertNotIn("42.4942701664000000", output)
