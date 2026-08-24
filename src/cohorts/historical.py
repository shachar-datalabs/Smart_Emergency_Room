from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path

from src.common.io import read_jsonl, write_jsonl


def age_group(age: int | None) -> str:
    if age is None:
        return "UNKNOWN"
    if age < 18:
        return "0-17"
    if age < 45:
        return "18-44"
    if age < 65:
        return "45-64"
    if age < 75:
        return "65-74"
    return "75+"


def diagnosis_group(code: str | None) -> str:
    return code[0].upper() if code else "UNKNOWN"


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * fraction)))
    return round(ordered[index], 2)


def build_cohorts(silver_path: Path, destination: Path) -> int:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in read_jsonl(silver_path):
        triage = row["triage_level"] or "ALL"
        age = age_group(row["age"])
        hour = row["arrival_hour"] if row["arrival_hour"] is not None else "ALL"
        keys = [
            ("TRIAGE_AGE_HOUR", triage, age, hour),
            ("TRIAGE_AGE", triage, age, "ALL"),
            ("TRIAGE", triage, "ALL", "ALL"),
            ("OVERALL", "ALL", "ALL", "ALL"),
        ]
        for key in keys:
            groups[key].append(row)

    def aggregates():
        for key in sorted(groups, key=lambda item: tuple(map(str, item))):
            level, triage, age, hour = key
            records = groups[key]
            waits = [r["waiting_time_minutes"] for r in records if r["waiting_time_minutes"] is not None]
            stays = [r["length_of_stay_minutes"] for r in records if r["length_of_stay_minutes"] is not None]
            admitted = sum(bool(r["admitted_flag"]) for r in records)
            yield {
                "cohort_key": f"{level}|{triage}|{age}|{hour}",
                "match_level": level,
                "triage_level": triage,
                "age_group": age,
                "arrival_hour": hour,
                "patient_count": len(records),
                "avg_wait_minutes": round(statistics.fmean(waits), 2) if waits else None,
                "median_wait_minutes": round(statistics.median(waits), 2) if waits else None,
                "p90_wait_minutes": _percentile(waits, 0.9),
                "avg_los_minutes": round(statistics.fmean(stays), 2) if stays else None,
                "median_los_minutes": round(statistics.median(stays), 2) if stays else None,
                "p90_los_minutes": _percentile(stays, 0.9),
                "admission_rate": round(admitted / len(records), 6),
            }

    return write_jsonl(destination, aggregates())
