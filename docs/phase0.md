# PHASE 0 foundation

This phase establishes a local-first repository and a reproducible, guarded
GCP bootstrap. It does not process MIMIC data or create compute resources.

## GCP decisions

- Default project: `shachar-bigquery-lab` (the existing configured project)
- Region: `us-central1`
- Raw bucket: `gs://<project-id>-smart-er-raw`
- BigQuery datasets: `smart_er_silver`, `smart_er_gold`
- Bootstrap defaults to dry-run and requires `--apply` for cloud changes
- No Compute Engine, GKE, Dataproc, Dataflow, Composer, or managed Kafka

Cloud Storage and BigQuery are usage-billed services. Review current Google
Cloud pricing and obtain explicit approval before running with `--apply`.

If `gcloud auth list` shows no active account, run `gcloud auth login`.
