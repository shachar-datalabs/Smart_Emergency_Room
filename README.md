# Smart Emergency Room

Local-first, real-time data engineering platform that simulates an emergency
department using MIMIC-IV-ED data.

## Planned data flow

```text
MIMIC-IV-ED -> Spark Batch -> Clean Parquet -> Patient Simulator -> Kafka
             -> Spark Structured Streaming -> BigQuery -> Looker Studio
```

The project is intentionally developed in small phases. PHASE 0 only creates
the repository foundation and a safe, reproducible GCP bootstrap. No patient
data, virtual machines, or other compute resources are created.

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

PHASE 0 repository scaffolding is complete. PHASE 1 must not begin until
explicitly approved.
