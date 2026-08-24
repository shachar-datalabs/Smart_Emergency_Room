#!/usr/bin/env python3
"""CLI for MIMIC-IV-ED raw-to-Bronze ingestion."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "batch" / "src"))

from ingestion.mimic_ed import IngestionConfig, ingest, write_manifest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and ingest MIMIC-IV-ED files into GCS Raw and BigQuery Bronze."
    )
    parser.add_argument("--project", default="shachar-bigquery-lab")
    parser.add_argument("--bucket", default="shachar-bigquery-lab-smart-er-raw")
    parser.add_argument("--dataset", default="smart_er_bronze")
    parser.add_argument("--location", default="us-central1")
    parser.add_argument("--version", default="2.2")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "data" / "mimic-iv-ed" / "2.2" / "ed",
    )
    parser.add_argument("--apply", action="store_true", help="Create/load GCP resources.")
    parser.add_argument(
        "--replace", action="store_true",
        help="Replace existing Bronze tables. Without this flag, existing tables are protected.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "ingestion_runs" / "latest.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = IngestionConfig(
        project=args.project,
        bucket=args.bucket,
        dataset=args.dataset,
        location=args.location,
        version=args.version,
        source_dir=args.source_dir,
        schema_dir=ROOT / "config" / "schemas" / "mimic_iv_ed_2_2",
        apply=args.apply,
        replace=args.replace,
    )
    try:
        results = ingest(config)
        write_manifest(args.manifest, config, results)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "no command output").strip()
        logging.error("Cloud command failed with exit code %s: %s", exc.returncode, detail)
        return 1
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        logging.error("Ingestion failed: %s", exc)
        return 1
    logging.info("Ingestion %s", "completed" if args.apply else "dry run completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
