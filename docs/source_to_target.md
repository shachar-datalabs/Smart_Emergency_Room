# CDC NHAMCS 2022 source-to-target mapping

| Canonical field | NHAMCS field | Rule / limitation |
|---|---|---|
| `visit_id` | source row number | Deterministic SHA-256-derived technical key |
| `patient_id` | unavailable | NULL; NHAMCS public file is visit-based |
| `arrival_time` | date unavailable | NULL; month, weekday and hour retained separately |
| `age` | `AGE` | Negative missing codes become NULL |
| `sex` | `SEX` | 1→F, 2→M per CDC format |
| `triage_level` | `IMMEDR` | Values 1–5; non-triage/missing codes become NULL |
| `chief_complaint` | `RFV1` | Retained as `RFV_CODE:<code>`; no invented description |
| `temperature` | `TEMPF` | Implied one decimal, Fahrenheit |
| `heart_rate` | `PULSE` | Numeric or NULL |
| `respiratory_rate` | `RESPR` | Numeric or NULL |
| `systolic_bp` | `BPSYS` | Numeric or NULL |
| `diastolic_bp` | `BPDIAS` | Numeric or NULL |
| `spo2` | `POPCT` | Numeric percent or NULL |
| `pain_score` | `PAINSCALE` | 0–10 or flagged |
| `diagnosis_code` | `DIAG1` | Truncated public-use code |
| `diagnosis_description` | unavailable | NULL |
| `disposition` | disposition flags | Deterministic precedence documented in code |
| `admitted_flag` | `ADMITHOS`, `OBSHOS` | True only for explicit hospital admission |
| `waiting_time_minutes` | `WAITTIME` | Direct survey value |
| `length_of_stay_minutes` | `LOV` | Direct survey value |
| `source_record_id` | row number | `2022-NNNNNN` |
| `ingestion_timestamp` | technical | UTC timestamp added at Bronze ingestion |

Raw GCS-ready layout: `raw/nhamcs/2022/ed2022.zip`. The existing cloud bucket
equivalent would be `gs://shachar-bigquery-lab-smart-er-raw/raw/nhamcs/2022/`,
but no upload was performed.
