from __future__ import annotations

import argparse
import json
import logging
import random
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.common.io import write_jsonl
from src.common.structured_logging import configure_logging, log_event


def generate_events(
    patients: int,
    seed: int,
    base_time: datetime,
    terminal_fraction: float = 0.6,
) -> list[dict]:
    rng = random.Random(seed)
    events: list[dict] = []
    for index in range(patients):
        patient_id = f"SIM-P{index + 1:05d}"
        visit_id = f"SIM-V{index + 1:05d}"
        arrival = base_time + timedelta(minutes=index * 2)
        age = rng.randint(1, 94)
        sex = rng.choice(["F", "M"])
        triage = rng.choices([1, 2, 3, 4, 5], weights=[4, 14, 38, 30, 14])[0]
        vital = {
            "heart_rate": rng.randint(55, 115),
            "respiratory_rate": rng.randint(12, 24),
            "systolic_bp": rng.randint(95, 155),
            "diastolic_bp": rng.randint(55, 95),
            "spo2": rng.randint(92, 100),
            "pain_score": rng.randint(0, 10),
        }
        sequence = [
            ("ARRIVAL", arrival, {"age": age, "sex": sex, "status": "WAITING"}),
            (
                "TRIAGE",
                arrival + timedelta(minutes=rng.randint(3, 15)),
                {"triage_level": triage, **vital, "status": "TRIAGED"},
            ),
            ("VITALS_UPDATE", arrival + timedelta(minutes=rng.randint(20, 45)), {**vital}),
            ("STATUS_UPDATE", arrival + timedelta(minutes=rng.randint(30, 70)), {"status": "IN_TREATMENT"}),
        ]
        if index < round(patients * terminal_fraction):
            terminal = "ADMISSION" if rng.random() < 0.25 else "DISCHARGE"
            sequence.append((terminal, arrival + timedelta(minutes=rng.randint(90, 240)), {"status": terminal}))
        for event_type, event_time, values in sequence:
            events.append(
                {
                    "event_id": str(uuid.UUID(int=rng.getrandbits(128))),
                    "event_type": event_type,
                    "event_version": 1,
                    "patient_id": patient_id,
                    "visit_id": visit_id,
                    "event_time": event_time.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                    **values,
                }
            )
    return sorted(events, key=lambda event: (event["event_time"], event["event_id"]))


def publish_kafka(events: list[dict], bootstrap: str, topic: str, rate: float) -> None:
    try:
        from kafka import KafkaProducer
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt to use Kafka output") from exc
    producer = KafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
    )
    delay = 0 if rate <= 0 else 1 / rate
    try:
        for event in events:
            producer.send(topic, key=event["visit_id"].encode(), value=event).get(timeout=15)
            if delay:
                time.sleep(delay)
    finally:
        producer.flush(timeout=15)
        producer.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patients", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rate", type=float, default=10)
    parser.add_argument("--base-time", default=None)
    parser.add_argument("--output", type=Path, default=Path("data/sample/patient_events.jsonl"))
    parser.add_argument("--kafka", action="store_true")
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--topic", default="patient-events")
    args = parser.parse_args()
    configure_logging()
    logger = logging.getLogger("simulator")
    base = datetime.fromisoformat(args.base_time) if args.base_time else datetime.now(UTC)
    events = generate_events(args.patients, args.seed, base)
    write_jsonl(args.output, events)
    if args.kafka:
        publish_kafka(events, args.bootstrap, args.topic, args.rate)
    log_event(
        logger,
        "patient_simulator",
        "events_generated",
        records_processed=len(events),
        records_rejected=0,
        patients=args.patients,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
