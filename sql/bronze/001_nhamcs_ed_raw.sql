-- Prepared only; not executed under the zero-cost policy.
CREATE TABLE IF NOT EXISTS `shachar-bigquery-lab.smart_er_bronze.nhamcs_ed_raw` (
  raw_record STRING NOT NULL,
  source_system STRING NOT NULL,
  source_year INT64 NOT NULL,
  source_filename STRING NOT NULL,
  source_row_number INT64 NOT NULL,
  ingestion_timestamp TIMESTAMP NOT NULL
)
PARTITION BY DATE(ingestion_timestamp)
CLUSTER BY source_year, source_filename
OPTIONS(description = 'Faithful CDC NHAMCS ED fixed-width Bronze records');
