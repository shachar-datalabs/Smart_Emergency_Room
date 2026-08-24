from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.common.io import write_json, write_jsonl
from src.context.engine import ContextEngine
from src.streaming.event_schema import parse_time


def build_gold(states: list[dict], events: list[dict], cohorts: Path, output: Path) -> dict:
    now = max((parse_time(event["event_time"]) for event in events), default=datetime.now(UTC))
    engine = ContextEngine(cohorts)
    enriched = [engine.enrich(state, len(states), now) for state in states]
    write_jsonl(output / "current_ed_state.jsonl", enriched)
    waits = [row["waiting_minutes"] for row in enriched]
    kpis = {
        "as_of": now.isoformat().replace("+00:00", "Z"),
        "active_patients": len(enriched),
        "arrivals": sum(event["event_type"] == "ARRIVAL" for event in events),
        "discharges": sum(event["event_type"] == "DISCHARGE" for event in events),
        "admissions": sum(event["event_type"] == "ADMISSION" for event in events),
        "avg_wait_minutes": round(statistics.fmean(waits), 2) if waits else 0,
        "median_wait_minutes": round(statistics.median(waits), 2) if waits else 0,
        "patients_above_expected_wait": sum(row["wait_vs_expected_minutes"] > 0 for row in enriched),
        "high_attention_patients": sum(row["attention_level"] in {"HIGH", "CRITICAL"} for row in enriched),
    }
    write_json(output / "ed_kpis.json", kpis)
    windows: dict[datetime, list[dict]] = defaultdict(list)
    for event in events:
        event_time = parse_time(event["event_time"])
        start = event_time.replace(minute=(event_time.minute // 15) * 15, second=0, microsecond=0)
        windows[start].append(event)
    load_rows = []
    for start, window_events in sorted(windows.items()):
        end = start + timedelta(minutes=15)
        if end <= start:
            raise ValueError(f"Invalid 15-minute window: {start.isoformat()} -> {end.isoformat()}")
        active_at_end = sum(
            event["event_type"] == "ARRIVAL" for event in events if parse_time(event["event_time"]) < end
        ) - sum(
            event["event_type"] in {"ADMISSION", "DISCHARGE"}
            for event in events
            if parse_time(event["event_time"]) < end
        )
        load_rows.append(
            {
                "window_start": start.isoformat().replace("+00:00", "Z"),
                "window_end": end.isoformat().replace("+00:00", "Z"),
                "active_patients": max(0, active_at_end),
                "new_arrivals": sum(e["event_type"] == "ARRIVAL" for e in window_events),
                "admissions": sum(e["event_type"] == "ADMISSION" for e in window_events),
                "discharges": sum(e["event_type"] == "DISCHARGE" for e in window_events),
                "avg_wait_minutes": kpis["avg_wait_minutes"],
                "high_attention_count": kpis["high_attention_patients"],
            }
        )
    write_jsonl(output / "ed_load_15min.jsonl", load_rows)
    return kpis
