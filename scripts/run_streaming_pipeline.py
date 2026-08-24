#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Spark Structured Streaming in the local container.")
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--starting-offsets", choices=("earliest", "latest"), default="earliest")
    parser.add_argument("--output-dir", default=None, help="Host data directory, mounted under /opt/smart-er.")
    parser.add_argument("--topic", default=None)
    args = parser.parse_args()
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
    ]
    if args.output_dir:
        relative = Path(args.output_dir).as_posix().lstrip("./")
        command.extend(["-e", f"STREAM_OUTPUT_DIR=/opt/smart-er/{relative}"])
    if args.topic:
        command.extend(["-e", f"KAFKA_TOPIC={args.topic}"])
    command.extend(
        [
            "spark",
            "/opt/spark/bin/spark-submit",
            "--conf",
            "spark.jars.ivy=/tmp/.ivy2",
            "--packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5",
            "/opt/smart-er/src/streaming/spark_job.py",
            "--seconds",
            str(args.seconds),
            "--starting-offsets",
            args.starting_offsets,
        ],
    )
    subprocess.run(
        command,
        cwd=ROOT,
        env=os.environ.copy(),
        check=True,
    )


if __name__ == "__main__":
    main()
