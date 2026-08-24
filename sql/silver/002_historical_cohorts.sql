-- Small dimension-style aggregate; partitioning is unnecessary.
CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_silver.historical_cohorts` (
  cohort_key STRING NOT NULL,
  match_level STRING NOT NULL,
  triage_level STRING,
  age_group STRING,
  arrival_hour STRING,
  patient_count INT64 NOT NULL,
  avg_wait_minutes FLOAT64,
  median_wait_minutes FLOAT64,
  p90_wait_minutes FLOAT64,
  avg_los_minutes FLOAT64,
  admission_rate FLOAT64
)
CLUSTER BY match_level, triage_level;
