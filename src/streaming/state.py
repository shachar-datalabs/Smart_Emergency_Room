from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.common.io import write_json, write_jsonl
from src.streaming.event_schema import parse_time, validate_event

TERMINAL = {"ADMISSION", "DISCHARGE"}


class StateProcessor:
    def __init__(self, watermark_minutes: int = 30):
        self.watermark = timedelta(minutes=watermark_minutes)
        self.seen: set[str] = set()
        self.active: dict[str, dict] = {}
        self.completed: list[dict] = []
        self.max_event_time: datetime | None = None
        self.stats = {
            "records_processed": 0,
            "records_rejected": 0,
            "duplicate_event_ids": 0,
            "malformed_events": 0,
            "late_events": 0,
            "missing_fields": 0,
        }
        self.quarantine: list[dict] = []

    def process(self, value: str | dict) -> bool:
        event, errors = validate_event(value)
        if errors:
            self.stats["records_rejected"] += 1
            self.stats["malformed_events"] += "MALFORMED_JSON" in errors
            self.stats["missing_fields"] += any(error.startswith("MISSING_") for error in errors)
            self.quarantine.append({"value": value, "errors": errors})
            return False
        assert event is not None
        if event["event_id"] in self.seen:
            self.stats["duplicate_event_ids"] += 1
            return False
        event_time = parse_time(event["event_time"])
        if self.max_event_time and event_time < self.max_event_time - self.watermark:
            self.stats["late_events"] += 1
            self.stats["records_rejected"] += 1
            self.quarantine.append({"value": event, "errors": ["LATE_EVENT"]})
            return False
        self.seen.add(event["event_id"])
        self.max_event_time = max(self.max_event_time or event_time, event_time)
        self.stats["records_processed"] += 1
        visit_id = event["visit_id"]
        state = self.active.get(visit_id)
        if state is None:
            if event["event_type"] != "ARRIVAL":
                self.stats["records_rejected"] += 1
                self.quarantine.append({"value": event, "errors": ["STATE_WITHOUT_ARRIVAL"]})
                return False
            state = {
                "visit_id": visit_id,
                "patient_id": event["patient_id"],
                "arrival_time": event["event_time"],
                "last_event_time": event["event_time"],
                "triage_level": None,
                "age": event.get("age"),
                "sex": event.get("sex"),
                "heart_rate": None,
                "respiratory_rate": None,
                "systolic_bp": None,
                "diastolic_bp": None,
                "spo2": None,
                "pain_score": None,
                "current_status": event.get("status", "WAITING"),
                "event_count": 0,
                "_vitals_time": None,
                "_triage_time": None,
            }
            self.active[visit_id] = state
        state["event_count"] += 1
        if event_time >= parse_time(state["last_event_time"]):
            state["last_event_time"] = event["event_time"]
            if event.get("status"):
                state["current_status"] = event["status"]
        triage_time = parse_time(state["_triage_time"]) if state["_triage_time"] else None
        if event.get("triage_level") is not None and (triage_time is None or event_time >= triage_time):
            state["triage_level"] = event["triage_level"]
            state["_triage_time"] = event["event_time"]
        vital_time = parse_time(state["_vitals_time"]) if state["_vitals_time"] else None
        vital_fields = ("heart_rate", "respiratory_rate", "systolic_bp", "diastolic_bp", "spo2", "pain_score")
        if any(event.get(field) is not None for field in vital_fields) and (
            vital_time is None or event_time >= vital_time
        ):
            for field in vital_fields:
                if event.get(field) is not None:
                    state[field] = event[field]
            state["_vitals_time"] = event["event_time"]
        if event["event_type"] in TERMINAL:
            state["current_status"] = event["event_type"]
            self.completed.append(self.active.pop(visit_id))
        return True

    def current_rows(self, reference_time: datetime | None = None) -> list[dict]:
        now = reference_time or self.max_event_time or datetime.now(UTC)
        rows = []
        for state in self.active.values():
            row = {key: value for key, value in state.items() if not key.startswith("_")}
            arrival = parse_time(row["arrival_time"])
            last = parse_time(row["last_event_time"])
            row["waiting_minutes"] = round(max(0, (now - arrival).total_seconds() / 60), 2)
            row["time_in_ed_minutes"] = row["waiting_minutes"]
            row["last_update_timestamp"] = last.isoformat().replace("+00:00", "Z")
            rows.append(row)
        return sorted(rows, key=lambda row: row["visit_id"])

    def persist(self, state_path: Path, quarantine_path: Path, dq_path: Path) -> None:
        write_jsonl(state_path, self.current_rows())
        write_jsonl(quarantine_path, self.quarantine)
        write_json(dq_path, self.stats)
