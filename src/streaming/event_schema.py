from __future__ import annotations

import json
from datetime import datetime, timezone

UTC = timezone.utc  # noqa: UP017 - Spark image uses Python 3.8.

EVENT_TYPES = {"ARRIVAL", "TRIAGE", "VITALS_UPDATE", "STATUS_UPDATE", "ADMISSION", "DISCHARGE"}
REQUIRED = {"event_id", "event_type", "event_version", "patient_id", "visit_id", "event_time"}


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))  # noqa: FURB162 - Python 3.8 Spark image.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def validate_event(value: str | dict) -> tuple[dict | None, list[str]]:
    if isinstance(value, str):
        try:
            event = json.loads(value)
        except json.JSONDecodeError:
            return None, ["MALFORMED_JSON"]
    elif isinstance(value, dict):
        event = value.copy()
    else:
        return None, ["INVALID_EVENT_TYPE"]
    missing = sorted(field for field in REQUIRED if event.get(field) in (None, ""))
    errors = [f"MISSING_{field.upper()}" for field in missing]
    if event.get("event_type") not in EVENT_TYPES:
        errors.append("UNKNOWN_EVENT_TYPE")
    if event.get("event_version") != 1:
        errors.append("UNSUPPORTED_EVENT_VERSION")
    try:
        parse_time(event.get("event_time", ""))
    except (TypeError, ValueError):
        errors.append("INVALID_EVENT_TIME")
    triage = event.get("triage_level")
    if triage is not None and triage not in range(1, 6):
        errors.append("INVALID_TRIAGE")
    return (event if not errors else None), errors


SPARK_SCHEMA_JSON = {
    "type": "struct",
    "fields": [
        {"name": "event_id", "type": "string", "nullable": False},
        {"name": "event_type", "type": "string", "nullable": False},
        {"name": "event_version", "type": "integer", "nullable": False},
        {"name": "patient_id", "type": "string", "nullable": False},
        {"name": "visit_id", "type": "string", "nullable": False},
        {"name": "event_time", "type": "string", "nullable": False},
        {"name": "triage_level", "type": "integer", "nullable": True},
        {"name": "age", "type": "integer", "nullable": True},
        {"name": "sex", "type": "string", "nullable": True},
        {"name": "heart_rate", "type": "double", "nullable": True},
        {"name": "respiratory_rate", "type": "double", "nullable": True},
        {"name": "systolic_bp", "type": "double", "nullable": True},
        {"name": "diastolic_bp", "type": "double", "nullable": True},
        {"name": "spo2", "type": "double", "nullable": True},
        {"name": "pain_score", "type": "double", "nullable": True},
        {"name": "status", "type": "string", "nullable": True},
    ],
}
