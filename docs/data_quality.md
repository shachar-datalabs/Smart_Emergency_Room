# Data quality

Historical rules validate unique technical visit IDs, nullable source fields,
triage 1–5, non-negative age, vital ranges, pain 0–10 and systolic pressure above
diastolic pressure. Records are retained and flagged rather than silently
deleted. `data/gold/dq_historical.json` contains machine-readable counts.

Streaming checks cover JSON parsing, required fields, event version/type,
event-time parsing, triage range, duplicate IDs, watermark-late events and state
updates without an arrival. Invalid records go to quarantine. Spark separately
writes malformed JSON and persists checkpoints. `dq_streaming.json` reports
processed, rejected, duplicate, malformed, missing and late counts.

Pipeline code writes outputs through temporary files followed by atomic rename.
Failures are logged and never converted into silent success.
