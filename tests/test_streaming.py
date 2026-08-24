from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime

from src.simulator.patient_simulator import generate_events
from src.streaming.state import StateProcessor


def base_event(event_id: str, event_type: str, event_time: str, **values) -> dict:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "event_version": 1,
        "patient_id": "P1",
        "visit_id": "V1",
        "event_time": event_time,
        **values,
    }


class StreamingTests(unittest.TestCase):
    def test_simulator_is_deterministic(self) -> None:
        base = datetime(2026, 1, 1, tzinfo=UTC)
        self.assertEqual(generate_events(3, 42, base), generate_events(3, 42, base))

    def test_arrival_triage_vitals_and_terminal(self) -> None:
        processor = StateProcessor()
        self.assertTrue(processor.process(base_event("1", "ARRIVAL", "2026-01-01T00:00:00Z", age=40, status="WAITING")))
        self.assertTrue(processor.process(base_event("2", "TRIAGE", "2026-01-01T00:05:00Z", triage_level=2)))
        self.assertTrue(
            processor.process(base_event("3", "VITALS_UPDATE", "2026-01-01T00:10:00Z", heart_rate=90, spo2=97))
        )
        state = processor.active["V1"]
        self.assertEqual(2, state["triage_level"])
        self.assertEqual(90, state["heart_rate"])
        processor.process(base_event("4", "DISCHARGE", "2026-01-01T01:00:00Z"))
        self.assertNotIn("V1", processor.active)
        self.assertEqual("DISCHARGE", processor.completed[0]["current_status"])

    def test_duplicate_event(self) -> None:
        processor = StateProcessor()
        event = base_event("same", "ARRIVAL", "2026-01-01T00:00:00Z")
        self.assertTrue(processor.process(event))
        self.assertFalse(processor.process(event))
        self.assertEqual(1, processor.stats["duplicate_event_ids"])

    def test_out_of_order_vitals_do_not_replace_newer(self) -> None:
        processor = StateProcessor(watermark_minutes=60)
        processor.process(base_event("1", "ARRIVAL", "2026-01-01T00:00:00Z"))
        processor.process(base_event("2", "VITALS_UPDATE", "2026-01-01T00:20:00Z", heart_rate=100))
        processor.process(base_event("3", "VITALS_UPDATE", "2026-01-01T00:10:00Z", heart_rate=70))
        self.assertEqual(100, processor.active["V1"]["heart_rate"])

    def test_late_event_is_quarantined(self) -> None:
        processor = StateProcessor(watermark_minutes=30)
        processor.process(base_event("1", "ARRIVAL", "2026-01-01T02:00:00Z"))
        self.assertFalse(processor.process(base_event("2", "TRIAGE", "2026-01-01T01:00:00Z", triage_level=3)))
        self.assertEqual(1, processor.stats["late_events"])

    def test_malformed_and_missing_events(self) -> None:
        processor = StateProcessor()
        self.assertFalse(processor.process("not-json"))
        self.assertFalse(processor.process(json.dumps({"event_type": "ARRIVAL"})))
        self.assertEqual(2, processor.stats["records_rejected"])
        self.assertEqual(1, processor.stats["malformed_events"])
        self.assertEqual(1, processor.stats["missing_fields"])
