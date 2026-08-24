-- Replace/synchronize by visit_id in a future production deployment.
CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.current_ed_state` (
  visit_id STRING NOT NULL,
  patient_id STRING NOT NULL,
  arrival_time TIMESTAMP NOT NULL,
  last_event_time TIMESTAMP NOT NULL,
  triage_level INT64,
  age INT64,
  sex STRING,
  heart_rate FLOAT64,
  respiratory_rate FLOAT64,
  systolic_bp FLOAT64,
  diastolic_bp FLOAT64,
  spo2 FLOAT64,
  pain_score FLOAT64,
  current_status STRING NOT NULL,
  waiting_minutes FLOAT64 NOT NULL,
  time_in_ed_minutes FLOAT64 NOT NULL,
  event_count INT64 NOT NULL,
  last_update_timestamp TIMESTAMP NOT NULL,
  historical_cohort_key STRING,
  historical_match_level STRING,
  expected_wait_minutes FLOAT64,
  historical_p90_wait_minutes FLOAT64,
  historical_admission_rate FLOAT64,
  wait_vs_expected_minutes FLOAT64,
  wait_ratio FLOAT64,
  attention_score INT64 NOT NULL,
  attention_level STRING NOT NULL,
  attention_reason ARRAY<STRING> NOT NULL
)
PARTITION BY DATE(last_update_timestamp)
CLUSTER BY triage_level, current_status, attention_level;
