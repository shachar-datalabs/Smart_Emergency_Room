#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="shachar-bigquery-lab"
REGION="us-central1"
APPLY=false

usage() {
  cat <<'EOF'
Usage: scripts/bootstrap_gcp.sh [--project PROJECT_ID] [--region REGION] [--apply]

Without --apply, prints the selected resources and exits without changing GCP.
With --apply, configures the project and idempotently creates one Cloud Storage
bucket plus the smart_er_silver and smart_er_gold BigQuery datasets.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      [[ $# -ge 2 ]] || { echo "Missing value for --project" >&2; exit 2; }
      PROJECT_ID="$2"
      shift 2
      ;;
    --region)
      [[ $# -ge 2 ]] || { echo "Missing value for --region" >&2; exit 2; }
      REGION="$2"
      shift 2
      ;;
    --apply)
      APPLY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

BUCKET_NAME="${PROJECT_ID}-smart-er-raw"

echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Cloud Storage bucket: gs://${BUCKET_NAME}"
echo "BigQuery datasets: smart_er_silver, smart_er_gold"
echo "Compute resources: none"

if [[ "${APPLY}" != "true" ]]; then
  echo "Dry run only. Re-run with --apply after reviewing cost implications."
  exit 0
fi

command -v gcloud >/dev/null 2>&1 || { echo "gcloud is required" >&2; exit 1; }
command -v bq >/dev/null 2>&1 || { echo "bq is required" >&2; exit 1; }

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -n 1)"
if [[ -z "${ACTIVE_ACCOUNT}" ]]; then
  echo "No active gcloud account. Run: gcloud auth login" >&2
  exit 1
fi

gcloud projects describe "${PROJECT_ID}" --format='value(projectId)' >/dev/null
gcloud config set project "${PROJECT_ID}"

if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

for dataset in smart_er_silver smart_er_gold; do
  if ! bq show --project_id="${PROJECT_ID}" "${PROJECT_ID}:${dataset}" >/dev/null 2>&1; then
    bq --project_id="${PROJECT_ID}" --location="${REGION}" mk --dataset "${dataset}"
  fi
done

echo "GCP bootstrap completed successfully."
