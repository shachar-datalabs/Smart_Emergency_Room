# Phase 4 — Context, Gold and BI

Implemented and locally tested. Active simulated visits are matched to NHAMCS
cohorts, enriched with expected/p90 wait and admission rate, then scored using
transparent rules. Gold outputs include current state, KPIs and 15-minute load.
BigQuery DDL and a dashboard specification are prepared but not cloud-executed.

The attention score is an educational operational monitoring signal. It is not
validated clinical decision support, does not diagnose patients and must not be
used to replace professional triage or medical judgment.
