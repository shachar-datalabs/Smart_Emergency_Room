# Data dictionary

## Silver `clean_ed_visits`

One row per sampled NHAMCS ED visit. Identifiers and provenance are technical;
patient identity is not present. Clinical numeric fields remain nullable.
`data_quality_flags` preserves every detected issue and
`data_quality_status` is `VALID` or `FLAGGED`.

## Silver `historical_cohorts`

Aggregates at four fallback levels: triage+age group+arrival hour,
triage+age group, triage, and overall. Metrics are count, mean/median/p90 wait,
mean length of visit, and admission rate. They are unweighted demo aggregates;
formal national estimates require CDC survey weights and survey-design methods.

## Event v1

Every event has UUID `event_id`, type, version, synthetic patient/visit IDs and
UTC `event_time`. Optional fields contain triage, demographics, vitals, pain and
status. Valid types are ARRIVAL, TRIAGE, VITALS_UPDATE, STATUS_UPDATE, ADMISSION
and DISCHARGE.

## Gold

`current_ed_state` is one row per active simulated visit enriched with cohort
metrics and explainable operational attention. `ed_kpis` is a current snapshot.
`ed_load_15min` is event-time-windowed operational load.
