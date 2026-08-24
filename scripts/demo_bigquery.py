#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulator.patient_simulator import publish_kafka
from src.sinks.bigquery import read_rows, sync_tables


def main() -> None:
    project = os.getenv("GCP_PROJECT", "shachar-bigquery-lab")
    dataset = os.getenv("BIGQUERY_GOLD_DATASET", "smart_er_gold")
    location = os.getenv("GCP_REGION", "us-central1")
    run_id = uuid.uuid4().hex[:8]
    stream_dir = ROOT / "data/demo_streaming" / run_id
    stream_dir.mkdir(parents=True, exist_ok=True)
    baseline_state = ROOT / "data/gold/current_ed_state_base.jsonl"
    if not baseline_state.exists():
        raise SystemExit("Run the historical pipeline and scripts/run_end_to_end_demo.py first")
    shutil.copyfile(baseline_state, stream_dir / "current_ed_state.jsonl")
    sync_tables(ROOT, project, dataset, location, apply=True)
    before_rows = read_rows(project, dataset, "active_patients")
    before = len(before_rows)
    visit_id = f"DEMO-V-{uuid.uuid4().hex[:10].upper()}"
    topic = f"patient-events-demo-{run_id}"
    patient_id = visit_id.replace("V", "P", 1)
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "ARRIVAL",
        "event_version": 1,
        "patient_id": patient_id,
        "visit_id": visit_id,
        "event_time": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "age": 35,
        "sex": "F",
        "status": "WAITING",
    }
    subprocess.run(["docker", "compose", "up", "-d"], cwd=ROOT, check=True)
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "kafka",
                "/opt/kafka/bin/kafka-topics.sh",
                "--bootstrap-server",
                "localhost:9092",
                "--create",
                "--if-not-exists",
                "--topic",
                topic,
                "--partitions",
                "1",
                "--replication-factor",
                "1",
            ],
            cwd=ROOT,
            check=True,
        )
        streaming = subprocess.Popen(
            [
                sys.executable,
                "scripts/run_streaming_pipeline.py",
                "--seconds",
                "35",
                "--starting-offsets",
                "earliest",
                "--output-dir",
                f"data/demo_streaming/{run_id}",
                "--topic",
                topic,
            ],
            cwd=ROOT,
        )
        time.sleep(12)
        publish_kafka([event], "localhost:9092", topic, 0)
        if streaming.wait(timeout=75) != 0:
            raise RuntimeError("Spark streaming process failed")
        subprocess.run(
            [sys.executable, "scripts/build_streaming_gold.py", "--stream-dir", str(stream_dir)],
            cwd=ROOT,
            check=True,
        )
        sync_tables(ROOT, project, dataset, location, apply=True)
        after_rows = read_rows(project, dataset, "active_patients")
        after = len(after_rows)
        found = any(row.get("visit_id") == visit_id for row in after_rows)
        if after != before + 1 or not found:
            raise RuntimeError(f"E2E assertion failed: before={before}, after={after}, found={found}")
        print(json.dumps({"status": "PASS", "before": before, "after": after, "visit_id": visit_id}, indent=2))
    finally:
        subprocess.run(["docker", "compose", "down"], cwd=ROOT, check=False)


if __name__ == "__main__":
    main()
