from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from src.common.io import read_jsonl, write_jsonl
from src.streaming.event_schema import SPARK_SCHEMA_JSON
from src.streaming.state import StateProcessor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=45)
    parser.add_argument("--starting-offsets", choices=("earliest", "latest"), default="earliest")
    args = parser.parse_args()

    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_timestamp
    from pyspark.sql.types import StructType

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    topic = os.getenv("KAFKA_TOPIC", "patient-events")
    output = Path(os.getenv("STREAM_OUTPUT_DIR", "/opt/smart-er/data/streaming"))
    watermark = os.getenv("WATERMARK_DURATION", "30 minutes")
    output.mkdir(parents=True, exist_ok=True)
    spark = SparkSession.builder.appName("smart-er-streaming").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    schema_json = {"type": "struct", "fields": [dict(field, metadata={}) for field in SPARK_SCHEMA_JSON["fields"]]}
    schema = StructType.fromJson(schema_json)
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", bootstrap)
        .option("subscribe", topic)
        .option("startingOffsets", args.starting_offsets)
        .load()
        .selectExpr("CAST(value AS STRING) AS raw_value", "timestamp AS kafka_timestamp")
    )
    parsed = raw.withColumn("event", from_json(col("raw_value"), schema))
    malformed = parsed.filter(col("event").isNull()).select("raw_value", "kafka_timestamp")
    valid = (
        parsed.filter(col("event").isNotNull())
        .select("event.*")
        .withColumn("event_time_ts", to_timestamp("event_time"))
        .withWatermark("event_time_ts", watermark)
        .dropDuplicates(["event_id"])
    )
    processor = StateProcessor(watermark_minutes=int(watermark.split()[0]))
    state_path = output / "current_ed_state.jsonl"
    event_log_path = output / "accepted_events.jsonl"
    processor.restore(state_path)
    if event_log_path.exists():
        processor.seen.update(event["event_id"] for event in read_jsonl(event_log_path))

    def update_state(batch, batch_id: int) -> None:
        events = [json.loads(value) for value in batch.drop("event_time_ts").toJSON().collect()]
        for event in sorted(events, key=lambda item: item["event_time"]):
            processor.process(event)
        previous_events = list(read_jsonl(event_log_path)) if event_log_path.exists() else []
        known_ids = {event["event_id"] for event in previous_events}
        write_jsonl(
            event_log_path, [*previous_events, *(event for event in events if event["event_id"] not in known_ids)]
        )
        processor.persist(
            state_path,
            output / "quarantine_state.jsonl",
            output / "dq_streaming.json",
        )
        (output / "last_batch.txt").write_text(f"{batch_id}\n", encoding="utf-8")

    malformed_query = (
        malformed.writeStream.format("json")
        .option("path", str(output / "malformed"))
        .option("checkpointLocation", str(output / "checkpoints/malformed"))
        .outputMode("append")
        .start()
    )
    state_query = (
        valid.writeStream.foreachBatch(update_state)
        .option("checkpointLocation", str(output / "checkpoints/state"))
        .start()
    )
    state_query.awaitTermination(args.seconds)
    state_query.stop()
    malformed_query.stop()
    spark.stop()


if __name__ == "__main__":
    main()
