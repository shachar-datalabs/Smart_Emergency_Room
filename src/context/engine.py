from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.cohorts.historical import age_group
from src.common.io import read_jsonl
from src.streaming.event_schema import parse_time


class ContextEngine:
    def __init__(self, cohort_path: Path):
        self.cohorts = {row["cohort_key"]: row for row in read_jsonl(cohort_path)}

    def _match(self, state: dict) -> dict:
        triage = state.get("triage_level") or "ALL"
        age = age_group(state.get("age"))
        arrival_hour = parse_time(state["arrival_time"]).hour
        candidates = [
            f"TRIAGE_AGE_HOUR|{triage}|{age}|{arrival_hour}",
            f"TRIAGE_AGE|{triage}|{age}|ALL",
            f"TRIAGE|{triage}|ALL|ALL",
            "OVERALL|ALL|ALL|ALL",
        ]
        return next(self.cohorts[key] for key in candidates if key in self.cohorts)

    def enrich(self, state: dict, active_count: int, now: datetime | None = None) -> dict:
        cohort = self._match(state)
        current_time = now or datetime.now(UTC)
        expected = cohort.get("median_wait_minutes") or cohort.get("avg_wait_minutes") or 0
        wait = state.get("waiting_minutes", 0)
        ratio = round(wait / expected, 3) if expected else None
        reasons: list[str] = []
        score = 0
        if state.get("triage_level") == 1:
            score += 40
            reasons.append("TRIAGE_LEVEL_1")
        elif state.get("triage_level") == 2:
            score += 25
            reasons.append("TRIAGE_LEVEL_2")
        if ratio is not None and ratio >= 2:
            score += 30
            reasons.append("WAIT_AT_LEAST_2X_EXPECTED")
        elif ratio is not None and ratio >= 1.25:
            score += 15
            reasons.append("WAIT_ABOVE_EXPECTED")
        abnormal = (
            (state.get("spo2") is not None and state["spo2"] < 92)
            or (state.get("heart_rate") is not None and not 45 <= state["heart_rate"] <= 130)
            or (state.get("systolic_bp") is not None and not 80 <= state["systolic_bp"] <= 200)
        )
        if abnormal:
            score += 20
            reasons.append("SYNTHETIC_VITAL_FLAG")
        stale = (current_time - parse_time(state["last_event_time"])).total_seconds() / 60
        if stale > 30:
            score += 15
            reasons.append("NO_UPDATE_OVER_30_MIN")
        if active_count >= 20:
            score += 10
            reasons.append("HIGH_ED_LOAD")
        level = "CRITICAL" if score >= 70 else "HIGH" if score >= 45 else "MEDIUM" if score >= 20 else "LOW"
        return {
            **state,
            "historical_cohort_key": cohort["cohort_key"],
            "historical_match_level": cohort["match_level"],
            "expected_wait_minutes": expected,
            "historical_p90_wait_minutes": cohort.get("p90_wait_minutes"),
            "historical_admission_rate": cohort.get("admission_rate"),
            "wait_vs_expected_minutes": round(wait - expected, 2),
            "wait_ratio": ratio,
            "attention_score": score,
            "attention_level": level,
            "attention_reason": reasons or ["NO_OPERATIONAL_ALERT"],
        }
