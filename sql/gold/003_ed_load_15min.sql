CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_gold.ed_load_15min` (
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  active_patients INT64 NOT NULL,
  new_arrivals INT64 NOT NULL,
  admissions INT64 NOT NULL,
  discharges INT64 NOT NULL,
  avg_wait_minutes FLOAT64 NOT NULL,
  high_attention_count INT64 NOT NULL
)
PARTITION BY DATE(window_start)
CLUSTER BY window_start;
