# GCP deployment preparation

Prepared targets use project `shachar-bigquery-lab`, region `us-central1`, the
existing Phase 0 Raw bucket, and logical datasets `smart_er_bronze`,
`smart_er_silver`, `smart_er_gold`.

No Phase 1–4 deployment command is automatically executed. Uploading NHAMCS,
creating Bronze, loading tables or querying BigQuery may incur charges. DDL is
versioned under `sql/`; local paths map directly to future GCS/BigQuery sinks.

Recommended future production write behavior:

- GCS Raw: generation-protected upload under `raw/nhamcs/2022/`.
- Historical tables: batch load into staging, validate, then transactional swap.
- Current state: MERGE by `visit_id` and remove terminal visits.
- KPI/load: append event-time snapshots, partitioned by timestamp/date.
