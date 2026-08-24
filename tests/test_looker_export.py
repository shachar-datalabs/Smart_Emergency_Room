from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.bi.looker_export import SHEET_ORDER, build_tables, write_csvs

ROOT = Path(__file__).resolve().parents[1]


class LookerExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tables = build_tables(ROOT / "data/gold", ROOT / "data/silver/historical_cohorts.jsonl")

    def test_exact_sheet_names_and_required_columns(self) -> None:
        self.assertEqual(SHEET_ORDER, list(self.tables))
        required = {
            "ED_KPIS": {"snapshot_time", "active_patients", "critical_attention_patients"},
            "ED_LOAD_15MIN": {"window_start", "window_end", "active_patients"},
            "ACTIVE_PATIENTS": {"visit_id", "attention_level", "attention_reason", "historical_cohort"},
            "HISTORICAL_CONTEXT": {"cohort_key", "median_wait_minutes", "median_los_minutes", "admission_rate"},
            "DATA_QUALITY": {"check_name", "status", "record_count", "generated_at"},
        }
        for name, fields in required.items():
            self.assertTrue(fields.issubset(self.tables[name][0]), name)

    def test_types_and_timestamps_are_looker_ready(self) -> None:
        kpi = self.tables["ED_KPIS"][0]
        self.assertIsInstance(kpi["active_patients"], int)
        self.assertIsInstance(kpi["avg_wait_minutes"], float)
        datetime.fromisoformat(kpi["snapshot_time"])
        for row in self.tables["ED_LOAD_15MIN"]:
            datetime.fromisoformat(row["window_start"])
        self.assertIsInstance(self.tables["HISTORICAL_CONTEXT"][0]["admission_rate"], float)

    def test_flattened_values_have_no_nested_json(self) -> None:
        for rows in self.tables.values():
            for row in rows:
                self.assertFalse(any(isinstance(value, (dict, list)) for value in row.values()))

    def test_csv_round_trip_has_one_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_csvs(self.tables, output)
            for name in SHEET_ORDER:
                with (output / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                self.assertEqual(len(self.tables[name]) + 1, len(rows))
                self.assertEqual(1, sum(row == rows[0] for row in rows))
                json.dumps(rows)


if __name__ == "__main__":
    unittest.main()
