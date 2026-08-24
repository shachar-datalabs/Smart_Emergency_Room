#!/usr/bin/env python3
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.cohorts.historical import build_cohorts
from src.common.structured_logging import configure_logging, log_event
from src.ingestion.nhamcs_bronze import ingest_bronze
from src.sources.nhamcs.download import download_nhamcs
from src.transformations.nhamcs_silver import build_silver


def main() -> None:
    configure_logging()
    logger = logging.getLogger("historical_pipeline")
    started = time.monotonic()
    raw = download_nhamcs(ROOT / "data/raw/nhamcs/2022")
    bronze = ROOT / "data/bronze/nhamcs_ed_raw.jsonl"
    silver = ROOT / "data/silver/clean_ed_visits.jsonl"
    cohorts = ROOT / "data/silver/historical_cohorts.jsonl"
    dq = ROOT / "data/gold/dq_historical.json"
    bronze_count = ingest_bronze(raw, bronze)
    report = build_silver(bronze, silver, dq)
    cohort_count = build_cohorts(silver, cohorts)
    log_event(
        logger,
        "historical_pipeline",
        "pipeline_completed",
        records_processed=bronze_count,
        records_rejected=report["records_rejected"],
        records_flagged=report["records_flagged"],
        cohorts=cohort_count,
        duration_seconds=round(time.monotonic() - started, 3),
    )


if __name__ == "__main__":
    main()
