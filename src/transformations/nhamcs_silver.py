from __future__ import annotations

import hashlib
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from src.common.io import read_jsonl, write_json, write_jsonl
from src.quality.rules import quality_flags
from src.sources.nhamcs.layout import FIELDS, SEX, TRIAGE, WEEKDAY


def _integer(value: str) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _decimal(value: str, scale: int = 1) -> float | None:
    number = _integer(value)
    return None if number is None else number / scale


def _float(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _disposition(raw: str) -> tuple[str | None, bool]:
    flag = lambda name: FIELDS[name].extract(raw) == "1"
    if flag("admit_hospital") or flag("observation_hospitalized"):
        return "ADMITTED", True
    if flag("died_in_ed"):
        return "DIED_IN_ED", False
    if flag("dead_on_arrival"):
        return "DEAD_ON_ARRIVAL", False
    if flag("transfer_psych") or flag("transfer_other") or flag("transfer_nursing"):
        return "TRANSFERRED", False
    if flag("left_without_seen"):
        return "LEFT_WITHOUT_BEING_SEEN", False
    if flag("left_before_complete"):
        return "LEFT_BEFORE_COMPLETE", False
    if flag("left_ama"):
        return "LEFT_AGAINST_MEDICAL_ADVICE", False
    if flag("observation_discharged"):
        return "OBSERVATION_DISCHARGED", False
    if flag("no_followup") or flag("return_ed") or flag("return_refer"):
        return "DISCHARGED", False
    if flag("other_disposition"):
        return "OTHER", False
    return None, False


def canonicalize(bronze: dict) -> dict:
    raw = bronze["raw_record"]
    get = lambda name: FIELDS[name].extract(raw)
    source_id = f"2022-{bronze['source_row_number']:06d}"
    visit_hash = hashlib.sha256(f"CDC_NHAMCS_ED:{source_id}".encode()).hexdigest()[:20]
    disposition, admitted = _disposition(raw)
    arrival_text = get("arrival_time")
    arrival_hour = int(arrival_text[:2]) if len(arrival_text) == 4 and arrival_text.isdigit() else None
    row = {
        "visit_id": f"NHAMCS-{visit_hash}",
        "patient_id": None,
        "arrival_time": None,
        "arrival_hour": arrival_hour,
        "visit_month": _integer(get("visit_month")),
        "visit_weekday": WEEKDAY.get(get("visit_weekday")),
        "weekend_flag": get("visit_weekday") in {"1", "7"},
        "age": _integer(get("age")),
        "sex": SEX.get(get("sex")),
        "triage_level": _integer(get("triage_level")) if _integer(get("triage_level")) in TRIAGE.values() else None,
        "chief_complaint": f"RFV_CODE:{get('reason_for_visit_code')}" if get("reason_for_visit_code") else None,
        "temperature": _decimal(get("temperature_f"), 10),
        "heart_rate": _decimal(get("heart_rate")),
        "respiratory_rate": _decimal(get("respiratory_rate")),
        "systolic_bp": _decimal(get("systolic_bp")),
        "diastolic_bp": _decimal(get("diastolic_bp")),
        "spo2": _decimal(get("spo2")),
        "pain_score": _decimal(get("pain_score")),
        "diagnosis_code": get("diagnosis_code") or None,
        "diagnosis_description": None,
        "disposition": disposition,
        "admitted_flag": admitted,
        "waiting_time_minutes": _decimal(get("waiting_time_minutes")),
        "length_of_stay_minutes": _decimal(get("length_of_stay_minutes")),
        "source_system": "CDC_NHAMCS_ED",
        "source_record_id": source_id,
        "source_weight": _float(get("patient_weight")),
        "ingestion_timestamp": bronze["ingestion_timestamp"],
    }
    row["data_quality_flags"] = quality_flags(row)
    row["data_quality_status"] = "VALID" if not row["data_quality_flags"] else "FLAGGED"
    return row


def build_silver(bronze_path: Path, silver_path: Path, dq_path: Path) -> dict:
    seen: set[str] = set()
    duplicates = 0
    counters: Counter[str] = Counter()

    def rows():
        nonlocal duplicates
        for bronze in read_jsonl(bronze_path):
            row = canonicalize(bronze)
            if row["visit_id"] in seen:
                duplicates += 1
                row["data_quality_flags"].append("DUPLICATE_VISIT_ID")
                row["data_quality_status"] = "FLAGGED"
            seen.add(row["visit_id"])
            for flag in row["data_quality_flags"]:
                counters[flag] += 1
            counters["FLAGGED" if row["data_quality_flags"] else "VALID"] += 1
            yield row

    count = write_jsonl(silver_path, rows())
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "row_count": count,
        "duplicate_visit_ids": duplicates,
        "null_critical_fields": counters["NULL_VISIT_ID"],
        "invalid_triage": counters["INVALID_TRIAGE"],
        "invalid_vitals": sum(
            value
            for key, value in counters.items()
            if key.startswith("INVALID_") and key not in {"INVALID_TRIAGE", "INVALID_AGE"}
        ),
        "records_flagged": counters["FLAGGED"],
        "records_rejected": 0,
        "flag_counts": dict(sorted(counters.items())),
    }
    write_json(dq_path, report)
    return report
