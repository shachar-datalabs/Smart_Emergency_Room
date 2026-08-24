CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.ed_kpis` (
  as_of TIMESTAMP NOT NULL,
  active_patients INT64 NOT NULL,
  arrivals INT64 NOT NULL,
  discharges INT64 NOT NULL,
  admissions INT64 NOT NULL,
  avg_wait_minutes FLOAT64 NOT NULL,
  median_wait_minutes FLOAT64 NOT NULL,
  patients_above_expected_wait INT64 NOT NULL,
  high_attention_patients INT64 NOT NULL
)
PARTITION BY DATE(as_of);
