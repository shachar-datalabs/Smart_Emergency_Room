#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io import write_json
from src.common.structured_logging import configure_logging, log_event
from src.gold.build import build_gold
from src.simulator.patient_simulator import generate_events
from src.streaming.state import StateProcessor


def main() -> None:
    configure_logging()
    logger = logging.getLogger("demo")
    cohort_path = ROOT / "data/silver/historical_cohorts.jsonl"
    if not cohort_path.exists():
        raise SystemExit("Run python scripts/run_historical_pipeline.py first")
    events = generate_events(12, 42, datetime(2026, 8, 24, 18, 0, tzinfo=UTC))
    processor = StateProcessor(watermark_minutes=30)
    for event in events:
        processor.process(event)
    processor.persist(
        ROOT / "data/gold/current_ed_state_base.jsonl",
        ROOT / "data/gold/quarantine_events.jsonl",
        ROOT / "data/gold/dq_streaming.json",
    )
    kpis = build_gold(processor.current_rows(), events, cohort_path, ROOT / "data/gold")
    evidence = {
        "flow": "simulator -> event contract -> state processor -> context -> gold",
        "events": len(events),
        "active_states": len(processor.active),
        "completed_states": len(processor.completed),
        "streaming_dq": processor.stats,
        "kpis": kpis,
    }
    write_json(ROOT / "data/gold/e2e_evidence.json", evidence)
    from scripts.build_dashboard import main as build_dashboard

    build_dashboard()
    log_event(
        logger,
        "end_to_end_demo",
        "demo_completed",
        records_processed=len(events),
        records_rejected=processor.stats["records_rejected"],
        active_states=len(processor.active),
    )


if __name__ == "__main__":
    main()
