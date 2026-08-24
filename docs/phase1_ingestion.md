# PHASE 1: MIMIC-IV-ED Raw and Bronze ingestion

PHASE 1 implements only this path:

```text
Official local CSV.GZ -> GCS Raw (unchanged bytes) -> BigQuery Bronze
```

It does not create Silver/Gold models, joins, dashboards, APIs, streaming jobs,
or compute resources.

## Official source files

After PhysioNet access is approved, download MIMIC-IV-ED through an authorized
method and place these exact files locally:

```text
data/mimic-iv-ed/2.2/ed/edstays.csv.gz
data/mimic-iv-ed/2.2/ed/triage.csv.gz
data/mimic-iv-ed/2.2/ed/vitalsign.csv.gz
```

The `data/` directory and all CSV/Parquet files are ignored by Git. Never place
PhysioNet credentials, cookies, or the source data elsewhere in the repository.
The pipeline does not download MIMIC automatically.

Schema and column order follow the official [MIMIC-IV-ED v2.2 documentation](https://physionet.org/content/mimic-iv-ed/2.2/).

## GCS Raw layout

```text
gs://shachar-bigquery-lab-smart-er-raw/
└── mimic-iv-ed/
    └── 2.2/
        └── ed/
            ├── edstays.csv.gz
            ├── triage.csv.gz
            └── vitalsign.csv.gz
```

Files are copied byte-for-byte. The local SHA-256 is stored as object metadata
and verified together with object size after upload.

## BigQuery Bronze layout

Dataset: `shachar-bigquery-lab.smart_er_bronze`, location `us-central1`.

Tables: `edstays`, `triage`, `vitalsign`. Each native table mirrors its source
columns. Bronze only parses CSV fields into explicit BigQuery types, maps empty
fields to NULL, and removes the header row. No clinical or business cleaning is
performed.

## Execution

First validate locally and print the cloud plan (no GCP changes):

```bash
python scripts/ingest_mimic_ed.py
```

After reviewing the manifest and expected costs, ingest once:

```bash
python scripts/ingest_mimic_ed.py --apply
```

Existing tables are protected by default. To intentionally reload them:

```bash
python scripts/ingest_mimic_ed.py --apply --replace
```

The run manifest is written beneath `data/ingestion_runs/` and is not committed.

## Validation

Before upload the pipeline checks file presence, gzip integrity, exact headers,
non-empty row counts, schema alignment, byte size, and SHA-256. After upload it
checks object size and stored SHA-256 metadata. After each BigQuery load it
checks table location and metadata row count without running a billed full-table
COUNT query.

## Costs

Local validation and dry-run have no GCP cost. Applying creates one BigQuery
dataset if absent, stores three source objects, and runs three BigQuery load
jobs. No continuously running compute is created.
