# Phase 1 — Data foundation

Implemented and locally tested with the official public CDC NHAMCS ED 2022
fixed-width file. The downloader verifies SHA-256. Bronze stores every complete
raw record plus provenance. Silver maps to a source-independent canonical ED
schema and retains flagged records. No data was uploaded to GCP.
