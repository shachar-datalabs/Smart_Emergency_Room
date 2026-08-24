#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sinks.bigquery import sync_tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Idempotently synchronize BI Gold snapshots to BigQuery.")
    parser.add_argument(
        "--apply", action="store_true", help="Run small BigQuery load jobs; default is a cost plan only."
    )
    args = parser.parse_args()
    result = sync_tables(
        ROOT,
        os.getenv("GCP_PROJECT", "shachar-bigquery-lab"),
        os.getenv("BIGQUERY_GOLD_DATASET", "smart_er_gold"),
        os.getenv("GCP_REGION", "us-central1"),
        apply=args.apply,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
