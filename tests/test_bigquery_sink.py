from __future__ import annotations

import unittest

from src.sinks.bigquery import SCHEMAS, TABLE_MAP


class BigQuerySinkTests(unittest.TestCase):
    def test_exact_looker_table_contract(self) -> None:
        self.assertEqual(
            {"ed_kpis", "ed_load_15min", "active_patients", "historical_context", "data_quality"},
            set(TABLE_MAP.values()),
        )
        self.assertEqual(set(TABLE_MAP.values()), set(SCHEMAS))
        self.assertIn("critical_attention_patients:INTEGER", SCHEMAS["ed_kpis"])
        self.assertIn("window_end:TIMESTAMP", SCHEMAS["ed_load_15min"])
