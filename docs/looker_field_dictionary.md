# Looker Studio field dictionary

Looker Studio may default numeric fields to `SUM`; use the aggregation below. `NONE` means dimension.

## ED_KPIS

| Field | Type | Aggregation | Meaning |
|---|---|---|---|
| snapshot_time | Date & Time | MAX | UTC timestamp of the current snapshot |
| active_patients | Number | MAX | Currently active ED visits |
| arrivals | Number | MAX | Arrivals in the simulated run |
| admissions | Number | MAX | Admissions in the simulated run |
| discharges | Number | MAX | Discharges in the simulated run |
| avg_wait_minutes | Number | MAX | Average current operational wait, minutes |
| median_wait_minutes | Number | MAX | Median current operational wait, minutes |
| patients_above_expected | Number | MAX | Active visits above matched expected wait |
| high_attention_patients | Number | MAX | Active HIGH or CRITICAL visits |
| critical_attention_patients | Number | MAX | Active CRITICAL visits |

## ED_LOAD_15MIN

| Field | Type | Aggregation | Meaning |
|---|---|---|---|
| window_start | Date & Time | NONE | Inclusive UTC 15-minute window start |
| window_end | Date & Time | NONE | Exclusive UTC 15-minute window end |
| active_patients | Number | MAX | Active visits at window end |
| new_arrivals | Number | SUM | ARRIVAL events within the window |
| admissions | Number | SUM | ADMISSION events within the window |
| discharges | Number | SUM | DISCHARGE events within the window |
| avg_wait_minutes | Number | MAX | Gold snapshot average wait carried by the demo output |
| high_attention_count | Number | MAX | Gold snapshot HIGH/CRITICAL count carried by the demo output |

## ACTIVE_PATIENTS

| Field | Type | Aggregation | Meaning |
|---|---|---|---|
| visit_id | Text | NONE / COUNT DISTINCT | Synthetic visit identifier |
| patient_id | Text | NONE / COUNT DISTINCT | Synthetic patient identifier |
| arrival_time | Date & Time | MAX | Visit arrival time, UTC |
| last_event_time | Date & Time | MAX | Latest accepted event time, UTC |
| triage_level | Number | NONE | Simulated triage category, 1–5 |
| current_status | Text | NONE | Normalized operational status |
| age | Number | MAX | Simulated age in years |
| sex | Text | NONE | Simulated sex category |
| heart_rate | Number | MAX | Latest simulated heart rate, bpm |
| systolic_bp | Number | MAX | Latest simulated systolic pressure, mmHg |
| diastolic_bp | Number | MAX | Latest simulated diastolic pressure, mmHg |
| spo2 | Number | MAX | Latest simulated oxygen saturation, percent |
| waiting_minutes | Number | MAX | Current operational waiting time |
| time_in_ed_minutes | Number | MAX | Current elapsed time since arrival |
| expected_wait_minutes | Number | MAX | Median wait of matched historical cohort |
| historical_p90_wait_minutes | Number | MAX | Historical cohort 90th-percentile wait |
| wait_vs_expected_minutes | Number | MAX | Current wait minus expected wait |
| wait_ratio | Number | MAX | Current wait divided by expected wait |
| attention_score | Number | MAX | Explainable operational score; not clinical advice |
| attention_level | Text | NONE | LOW, MEDIUM, HIGH, or CRITICAL category |
| attention_reason | Text | NONE | Flattened semicolon-separated scoring reasons |
| historical_cohort | Text | NONE | Cohort key used for matching |
| last_update_timestamp | Date & Time | MAX | Last accepted state update, UTC |

## HISTORICAL_CONTEXT

| Field | Type | Aggregation | Meaning |
|---|---|---|---|
| cohort_key | Text | NONE | Unique historical cohort key |
| match_level | Text | NONE | Cohort specificity/fallback level |
| triage_level | Text/Number | NONE | Triage category or ALL fallback |
| age_group | Text | NONE | Canonical age band or ALL |
| arrival_hour | Text/Number | NONE | Arrival hour or ALL |
| patient_count | Number | MAX | Historical visits in cohort |
| avg_wait_minutes | Number | MAX | Historical average wait |
| median_wait_minutes | Number | MAX | Historical median wait |
| p90_wait_minutes | Number | MAX | Historical 90th-percentile wait |
| avg_los_minutes | Number | MAX | Historical average ED length of stay |
| median_los_minutes | Number | MAX | Historical median ED length of stay |
| p90_los_minutes | Number | MAX | Historical 90th-percentile ED length of stay |
| admission_rate | Percent | MAX | Admitted visits divided by cohort visits |

## DATA_QUALITY

| Field | Type | Aggregation | Meaning |
|---|---|---|---|
| check_name | Text | NONE | Stable check name |
| status | Text | NONE | PASS, WARN, or FAIL |
| record_count | Number | MAX | Records associated with check |
| description | Text | NONE | Human-readable explanation |
| generated_at | Date & Time | MAX | UTC DQ generation timestamp |
