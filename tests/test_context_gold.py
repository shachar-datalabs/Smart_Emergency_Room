from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from src.common.io import read_jsonl, write_jsonl
from src.context.engine import ContextEngine
from src.gold.build import build_gold


class ContextGoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cohorts = self.root / "cohorts.jsonl"
        write_jsonl(
            self.cohorts,
            [
                {
                    "cohort_key": "TRIAGE|2|ALL|ALL",
                    "match_level": "TRIAGE",
                    "median_wait_minutes": 20,
                    "avg_wait_minutes": 22,
                    "p90_wait_minutes": 60,
                    "admission_rate": 0.3,
                },
                {
                    "cohort_key": "OVERALL|ALL|ALL|ALL",
                    "match_level": "OVERALL",
                    "median_wait_minutes": 30,
                    "avg_wait_minutes": 35,
                    "p90_wait_minutes": 90,
                    "admission_rate": 0.1,
                },
            ],
        )
        self.state = {
            "visit_id": "V1",
            "patient_id": "P1",
            "arrival_time": "2026-01-01T00:00:00Z",
            "last_event_time": "2026-01-01T00:10:00Z",
            "triage_level": 2,
            "age": 40,
            "heart_rate": 90,
            "systolic_bp": 120,
            "spo2": 97,
            "waiting_minutes": 50,
            "current_status": "WAITING",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_context_fallback_and_explainable_attention(self) -> None:
        enriched = ContextEngine(self.cohorts).enrich(self.state, 1, datetime(2026, 1, 1, 0, 50, tzinfo=UTC))
        self.assertEqual("TRIAGE", enriched["historical_match_level"])
        self.assertEqual(20, enriched["expected_wait_minutes"])
        self.assertIn("WAIT_AT_LEAST_2X_EXPECTED", enriched["attention_reason"])
        self.assertGreaterEqual(enriched["attention_score"], 45)

    def test_gold_outputs(self) -> None:
        events = [
            {"event_type": "ARRIVAL", "event_time": "2026-01-01T00:00:00Z"},
            {"event_type": "DISCHARGE", "event_time": "2026-01-01T00:30:00Z"},
        ]
        kpis = build_gold([self.state], events, self.cohorts, self.root / "gold")
        self.assertEqual(1, kpis["active_patients"])
        self.assertTrue((self.root / "gold/current_ed_state.jsonl").exists())
        self.assertGreaterEqual(len(list(read_jsonl(self.root / "gold/ed_load_15min.jsonl"))), 1)
