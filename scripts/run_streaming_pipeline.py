#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Spark Structured Streaming in the local container.")
    parser.add_argument("--seconds", type=int, default=45)
    args = parser.parse_args()
    subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "spark",
            "/opt/spark/bin/spark-submit",
            "--conf",
            "spark.jars.ivy=/tmp/.ivy2",
            "--packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5",
            "/opt/smart-er/src/streaming/spark_job.py",
            "--seconds",
            str(args.seconds),
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
