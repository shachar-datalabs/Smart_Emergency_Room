# Smart Emergency Room

Local-first, real-time data engineering platform that simulates an emergency
department using MIMIC-IV-ED data.

## Planned data flow

```text
MIMIC-IV-ED -> Spark Batch -> Clean Parquet -> Patient Simulator -> Kafka
             -> Spark Structured Streaming -> BigQuery -> Looker Studio
```

The project is intentionally developed in small phases. PHASE 0 established
the repository and GCP foundation. PHASE 1 provides reproducible ingestion from
official local MIMIC-IV-ED archives to unchanged GCS Raw objects and minimally
parsed BigQuery Bronze tables. No virtual machines are used.

## Repository layout

```text
batch/       Spark batch jobs and tests
simulator/   Patient event simulator and tests
streaming/   Spark Structured Streaming jobs and tests
kafka/       Kafka configuration
sql/         BigQuery validation and serving SQL
docker/      Container-related files
scripts/     Bootstrap and operational scripts
docs/        Project documentation
config/      Non-secret configuration
```

## PHASE 1 ingestion

Place authorized MIMIC-IV-ED v2.2 files under
`data/mimic-iv-ed/2.2/ed/`, then run a local validation and dry-run:

```bash
python scripts/ingest_mimic_ed.py
```

See [docs/phase1_ingestion.md](docs/phase1_ingestion.md) for the exact Raw and
Bronze layouts, validation behavior, apply command, and cost notes.

## PHASE 0 setup

Prerequisites: Git, Google Cloud CLI (`gcloud`, including `bq`), and access to
the selected GCP project.

Inspect the planned GCP commands without changing cloud resources:

```bash
bash scripts/bootstrap_gcp.sh --project shachar-bigquery-lab
```

After reviewing the output and confirming possible GCP charges, apply it:

```bash
bash scripts/bootstrap_gcp.sh --project shachar-bigquery-lab --apply
```

The script uses `us-central1`, creates `gs://<project-id>-smart-er-raw`, and
creates `smart_er_silver` and `smart_er_gold`. It is idempotent and never
creates a Compute Engine VM.

Run the PHASE 0 checks:

```bash
python scripts/test_phase0.py
```

## Data and secret safety

MIMIC data is credentialed clinical data and must never be committed. Keep raw
and generated datasets under `data/`. Use normal `gcloud` authentication
instead of storing credentials in this repository.

## Current status

PHASE 0 is complete. PHASE 1 ingestion framework is implemented; cloud ingestion
waits for authorized source files and an explicit `--apply` run. PHASE 2 has not
started.
