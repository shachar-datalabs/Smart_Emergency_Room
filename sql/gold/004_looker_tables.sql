-- Reference DDL only. The idempotent demo uses small replace load jobs, not queries.
CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.active_patients` (
  visit_id STRING, patient_id STRING, arrival_time TIMESTAMP, last_event_time TIMESTAMP,
  triage_level INT64, current_status STRING, age INT64, sex STRING,
  heart_rate FLOAT64, systolic_bp FLOAT64, diastolic_bp FLOAT64, spo2 FLOAT64,
  waiting_minutes FLOAT64, time_in_ed_minutes FLOAT64, expected_wait_minutes FLOAT64,
  historical_p90_wait_minutes FLOAT64, wait_vs_expected_minutes FLOAT64, wait_ratio FLOAT64,
  attention_score INT64, attention_level STRING, attention_reason STRING,
  historical_cohort STRING, last_update_timestamp TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.historical_context` (
  cohort_key STRING, match_level STRING, triage_level STRING, age_group STRING,
  arrival_hour STRING, patient_count INT64, avg_wait_minutes FLOAT64,
  median_wait_minutes FLOAT64, p90_wait_minutes FLOAT64, avg_los_minutes FLOAT64,
  median_los_minutes FLOAT64, p90_los_minutes FLOAT64, admission_rate FLOAT64
);

CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.data_quality` (
  check_name STRING, status STRING, record_count INT64, description STRING, generated_at TIMESTAMP
);
