# Phase 3 — Real-time pipeline

Implemented and locally integration-tested with Kafka 3.9.1 and Spark 3.5.5 in
Docker. The simulator is deterministic and synthetic. Spark uses an explicit
schema, event time, a 30-minute watermark, event-ID deduplication, malformed
quarantine, checkpoints and stateful `foreachBatch` updates to local JSONL.
Terminal admission/discharge events remove visits from active state.
