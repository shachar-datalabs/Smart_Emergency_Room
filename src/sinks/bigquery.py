from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from src.bi.looker_export import build_tables
from src.common.io import write_jsonl

TABLE_MAP = {
    "ED_KPIS": "ed_kpis",
    "ED_LOAD_15MIN": "ed_load_15min",
    "ACTIVE_PATIENTS": "active_patients",
    "HISTORICAL_CONTEXT": "historical_context",
    "DATA_QUALITY": "data_quality",
}

SCHEMAS = {
    "ed_kpis": "snapshot_time:TIMESTAMP,active_patients:INTEGER,arrivals:INTEGER,admissions:INTEGER,discharges:INTEGER,avg_wait_minutes:FLOAT,median_wait_minutes:FLOAT,patients_above_expected:INTEGER,high_attention_patients:INTEGER,critical_attention_patients:INTEGER",
    "ed_load_15min": "window_start:TIMESTAMP,window_end:TIMESTAMP,active_patients:INTEGER,new_arrivals:INTEGER,admissions:INTEGER,discharges:INTEGER,avg_wait_minutes:FLOAT,high_attention_count:INTEGER",
    "active_patients": "visit_id:STRING,patient_id:STRING,arrival_time:TIMESTAMP,last_event_time:TIMESTAMP,triage_level:INTEGER,current_status:STRING,age:INTEGER,sex:STRING,heart_rate:FLOAT,systolic_bp:FLOAT,diastolic_bp:FLOAT,spo2:FLOAT,waiting_minutes:FLOAT,time_in_ed_minutes:FLOAT,expected_wait_minutes:FLOAT,historical_p90_wait_minutes:FLOAT,wait_vs_expected_minutes:FLOAT,wait_ratio:FLOAT,attention_score:INTEGER,attention_level:STRING,attention_reason:STRING,historical_cohort:STRING,last_update_timestamp:TIMESTAMP",
    "historical_context": "cohort_key:STRING,match_level:STRING,triage_level:STRING,age_group:STRING,arrival_hour:STRING,patient_count:INTEGER,avg_wait_minutes:FLOAT,median_wait_minutes:FLOAT,p90_wait_minutes:FLOAT,avg_los_minutes:FLOAT,median_los_minutes:FLOAT,p90_los_minutes:FLOAT,admission_rate:FLOAT",
    "data_quality": "check_name:STRING,status:STRING,record_count:INTEGER,description:STRING,generated_at:TIMESTAMP",
}


def prepare_rows(root: Path) -> dict[str, list[dict[str, Any]]]:
    tables = build_tables(root / "data/gold", root / "data/silver/historical_cohorts.jsonl")
    historical = tables["HISTORICAL_CONTEXT"]
    for row in historical:
        row["triage_level"] = str(row["triage_level"]) if row["triage_level"] is not None else None
        row["arrival_hour"] = str(row["arrival_hour"]) if row["arrival_hour"] is not None else None
    return {TABLE_MAP[source]: rows for source, rows in tables.items()}


def stage_rows(root: Path) -> dict[str, Path]:
    destination = root / "data/bigquery"
    paths: dict[str, Path] = {}
    for table, rows in prepare_rows(root).items():
        path = destination / f"{table}.jsonl"
        write_jsonl(path, rows)
        paths[table] = path
    return paths


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError(f"Required command not found: {command[0]}")
    if os.name == "nt" and Path(executable).suffix.lower() in {".cmd", ".bat"}:
        sdk_root = Path(executable).resolve().parents[1]
        sdk_python = sdk_root / "platform/bundledpython/python.exe"
        bq_script = sdk_root / "bin/bootstrapping/bq.py"
        if not sdk_python.exists() or not bq_script.exists():
            raise FileNotFoundError("Google Cloud SDK bundled bq runtime is incomplete")
        command = [str(sdk_python), "-S", str(bq_script), *command[1:]]
    else:
        command = [executable, *command[1:]]
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        outputs = [part.strip() for part in (exc.stdout, exc.stderr) if part and part.strip()]
        detail = "\n".join(outputs) or "no CLI output"
        raise RuntimeError(f"Command failed ({exc.returncode}): {detail}") from exc


def verify_dataset(project: str, dataset: str, location: str) -> None:
    result = _run(["bq", "show", "--format=json", f"{project}:{dataset}"])
    metadata = json.loads(result.stdout)
    actual = metadata.get("location", "").lower()
    if actual != location.lower():
        raise ValueError(f"Dataset {project}:{dataset} is in {actual}, expected {location}")


def sync_tables(root: Path, project: str, dataset: str, location: str, *, apply: bool) -> dict[str, Any]:
    verify_dataset(project, dataset, location)
    paths = stage_rows(root)
    plan = {
        "project": project,
        "dataset": dataset,
        "location": location,
        "mode": "replace",
        "query_bytes_processed": 0,
        "tables": {
            table: {
                "rows": sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line),
                "bytes": path.stat().st_size,
            }
            for table, path in paths.items()
        },
    }
    if not apply:
        return plan

    for table, path in paths.items():
        print(f"Loading BigQuery table: {table}", flush=True)
        _run(
            [
                "bq",
                "load",
                f"--location={location}",
                "--replace",
                "--source_format=NEWLINE_DELIMITED_JSON",
                f"{project}:{dataset}.{table}",
                str(path),
                SCHEMAS[table],
            ]
        )

    plan["applied"] = True
    return plan


def read_rows(project: str, dataset: str, table: str, max_rows: int = 1000) -> list[dict[str, Any]]:
    result = _run(["bq", "head", "--format=json", f"--max_rows={max_rows}", f"{project}:{dataset}.{table}"])
    return json.loads(result.stdout or "[]")
