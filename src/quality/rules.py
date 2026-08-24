from __future__ import annotations


def quality_flags(row: dict) -> list[str]:
    flags: list[str] = []
    if row["age"] is not None and not 0 <= row["age"] <= 120:
        flags.append("INVALID_AGE")
    if row["triage_level"] is not None and row["triage_level"] not in range(1, 6):
        flags.append("INVALID_TRIAGE")
    ranges = {
        "temperature": (80.0, 115.0),
        "heart_rate": (1.0, 300.0),
        "respiratory_rate": (1.0, 100.0),
        "systolic_bp": (1.0, 300.0),
        "diastolic_bp": (1.0, 200.0),
        "spo2": (50.0, 100.0),
        "pain_score": (0.0, 10.0),
    }
    for field, (low, high) in ranges.items():
        value = row[field]
        if value is not None and not low <= value <= high:
            flags.append(f"INVALID_{field.upper()}")
    if row["systolic_bp"] is not None and row["diastolic_bp"] is not None and row["systolic_bp"] <= row["diastolic_bp"]:
        flags.append("INVALID_BP_RELATION")
    if not row.get("visit_id"):
        flags.append("NULL_VISIT_ID")
    return flags
