from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from src.common.io import read_jsonl, write_json
from src.streaming.event_schema import parse_time

SHEET_ORDER = ["ED_KPIS", "ED_LOAD_15MIN", "ACTIVE_PATIENTS", "HISTORICAL_CONTEXT", "DATA_QUALITY"]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _status(count: int, *, warning: bool = False) -> str:
    if count == 0:
        return "PASS"
    return "WARN" if warning else "FAIL"


def build_tables(gold_dir: Path, cohort_path: Path) -> dict[str, list[dict[str, Any]]]:
    kpis = _read_json(gold_dir / "ed_kpis.json")
    active = sorted(
        read_jsonl(gold_dir / "current_ed_state.jsonl"),
        key=lambda row: (-row["attention_score"], -row["waiting_minutes"]),
    )
    historical_dq = _read_json(gold_dir / "dq_historical.json")
    streaming_dq = _read_json(gold_dir / "dq_streaming.json")

    ed_kpis = [
        {
            "snapshot_time": kpis["as_of"],
            "active_patients": int(kpis["active_patients"]),
            "arrivals": int(kpis["arrivals"]),
            "admissions": int(kpis["admissions"]),
            "discharges": int(kpis["discharges"]),
            "avg_wait_minutes": float(kpis["avg_wait_minutes"]),
            "median_wait_minutes": float(kpis["median_wait_minutes"]),
            "patients_above_expected": int(kpis["patients_above_expected_wait"]),
            "high_attention_patients": int(kpis["high_attention_patients"]),
            "critical_attention_patients": sum(row["attention_level"] == "CRITICAL" for row in active),
        }
    ]

    load_fields = [
        "window_start",
        "window_end",
        "active_patients",
        "new_arrivals",
        "admissions",
        "discharges",
        "avg_wait_minutes",
        "high_attention_count",
    ]
    ed_load = [
        {field: row.get(field) for field in load_fields}
        for row in sorted(read_jsonl(gold_dir / "ed_load_15min.jsonl"), key=lambda row: row["window_start"])
    ]
    for row in ed_load:
        if parse_time(row["window_end"]) <= parse_time(row["window_start"]):
            raise ValueError(f"Invalid ED_LOAD_15MIN window: {row}")

    active_fields = [
        "visit_id",
        "patient_id",
        "arrival_time",
        "last_event_time",
        "triage_level",
        "current_status",
        "age",
        "sex",
        "heart_rate",
        "systolic_bp",
        "diastolic_bp",
        "spo2",
        "waiting_minutes",
        "time_in_ed_minutes",
        "expected_wait_minutes",
        "historical_p90_wait_minutes",
        "wait_vs_expected_minutes",
        "wait_ratio",
        "attention_score",
        "attention_level",
        "attention_reason",
        "historical_cohort",
        "last_update_timestamp",
    ]
    active_rows = []
    for row in active:
        flattened = {field: row.get(field) for field in active_fields}
        flattened["attention_reason"] = "; ".join(row.get("attention_reason", []))
        flattened["historical_cohort"] = row.get("historical_cohort_key")
        flattened["attention_level"] = str(row.get("attention_level", "LOW")).upper()
        flattened["current_status"] = str(row.get("current_status", "UNKNOWN")).upper()
        active_rows.append(flattened)

    cohort_fields = [
        "cohort_key",
        "match_level",
        "triage_level",
        "age_group",
        "arrival_hour",
        "patient_count",
        "avg_wait_minutes",
        "median_wait_minutes",
        "p90_wait_minutes",
        "avg_los_minutes",
        "median_los_minutes",
        "p90_los_minutes",
        "admission_rate",
    ]
    historical = [{field: row.get(field) for field in cohort_fields} for row in read_jsonl(cohort_path)]

    generated_at = historical_dq["generated_at"]
    checks = [
        ("processed_historical_records", "PASS", historical_dq["row_count"], "NHAMCS rows processed"),
        (
            "quality_flagged_records",
            _status(historical_dq["records_flagged"], warning=True),
            historical_dq["records_flagged"],
            "Records retained with one or more quality flags",
        ),
        (
            "rejected_historical_records",
            _status(historical_dq["records_rejected"]),
            historical_dq["records_rejected"],
            "Historical records rejected",
        ),
        (
            "duplicate_visits",
            _status(historical_dq["duplicate_visit_ids"]),
            historical_dq["duplicate_visit_ids"],
            "Duplicate canonical visit identifiers",
        ),
        (
            "invalid_triage",
            _status(historical_dq["invalid_triage"]),
            historical_dq["invalid_triage"],
            "Visits with an invalid triage category",
        ),
        (
            "invalid_vitals",
            _status(historical_dq["invalid_vitals"], warning=True),
            historical_dq["invalid_vitals"],
            "Vital checks flagged; records remain auditable",
        ),
        ("processed_stream_events", "PASS", streaming_dq["records_processed"], "Synthetic events processed"),
        (
            "duplicate_events",
            _status(streaming_dq["duplicate_event_ids"], warning=True),
            streaming_dq["duplicate_event_ids"],
            "Duplicate event identifiers ignored",
        ),
        (
            "malformed_events",
            _status(streaming_dq["malformed_events"]),
            streaming_dq["malformed_events"],
            "Events with malformed JSON",
        ),
        (
            "late_events",
            _status(streaming_dq["late_events"], warning=True),
            streaming_dq["late_events"],
            "Events later than the configured watermark",
        ),
        (
            "rejected_stream_events",
            _status(streaming_dq["records_rejected"]),
            streaming_dq["records_rejected"],
            "Stream events quarantined or rejected",
        ),
    ]
    dq = [
        {
            "check_name": name,
            "status": status,
            "record_count": int(count),
            "description": description,
            "generated_at": generated_at,
        }
        for name, status, count, description in checks
    ]
    return dict(zip(SHEET_ORDER, [ed_kpis, ed_load, active_rows, historical, dq], strict=True))


def write_csvs(tables: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in SHEET_ORDER:
        rows = tables[name]
        if not rows:
            raise ValueError(f"{name} has no rows")
        with (output_dir / f"{name}.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def export_looker_source(root: Path) -> dict[str, Any]:
    tables = build_tables(root / "data/gold", root / "data/silver/historical_cohorts.jsonl")
    output_dir = root / "exports/looker"
    write_csvs(tables, output_dir)
    build_source = root / "data/looker_workbook_source.json"
    columns = {name: list(tables[name][0]) for name in SHEET_ORDER}
    write_json(build_source, {"sheet_order": SHEET_ORDER, "columns": columns, "tables": tables})
    manifest = {
        "package": "Smart_Emergency_Room_Looker_Source",
        "sheet_order": SHEET_ORDER,
        "rows": {name: len(tables[name]) for name in SHEET_ORDER},
        "columns": columns,
        "workbook_source": "data/looker_workbook_source.json",
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest
