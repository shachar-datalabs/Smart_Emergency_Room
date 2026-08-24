#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io import read_jsonl
from src.gold.build import build_gold


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Gold from the latest persisted Spark state.")
    parser.add_argument("--stream-dir", type=Path, default=ROOT / "data/streaming")
    args = parser.parse_args()
    states = list(read_jsonl(args.stream_dir / "current_ed_state.jsonl"))
    events = list(read_jsonl(args.stream_dir / "accepted_events.jsonl"))
    if not events:
        raise SystemExit("No accepted streaming events found")
    build_gold(states, events, ROOT / "data/silver/historical_cohorts.jsonl", ROOT / "data/gold")
    shutil.copyfile(args.stream_dir / "dq_streaming.json", ROOT / "data/gold/dq_streaming.json")


if __name__ == "__main__":
    main()
