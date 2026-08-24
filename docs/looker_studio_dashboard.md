# Smart Emergency Room — Looker Studio dashboard

Status: **BIGQUERY DATA SOURCES READY — REPORT UI REQUIRES MANUAL CREATION**. Primary source: `shachar-bigquery-lab.smart_er_gold`; the Google Sheet is backup only. Build one 16:9 executive page. Keep “Operational monitoring demo — not medical decision support” visible.

## Header

- Title: **Smart Emergency Room**
- Subtitle: **Real-Time Emergency Department Operations & Historical Context**
- Source note: **Historical source: CDC NHAMCS 2022 | Live stream: simulated**

## KPI cards

Use `ed_kpis`; each field uses `MAX` because the table contains one snapshot row.

| Card | Metric |
|---|---|
| Active Patients | `active_patients` |
| Arrivals | `arrivals` |
| Admissions | `admissions` |
| Discharges | `discharges` |
| Average Wait | `avg_wait_minutes` |
| Patients Above Expected | `patients_above_expected` |
| High Attention | `high_attention_patients` |
| Critical Attention | `critical_attention_patients` |

Format waits as `0.0 min` and counts as integers. Do not sum snapshot metrics.

## ED Load — 15 Minute Windows

- Source: `ed_load_15min`
- Chart: time series
- Dimension: `window_start` (`Date & Time`)
- Metrics: `active_patients` (primary), `new_arrivals`, `high_attention_count`
- Sort: `window_start` ascending
- Aggregation: `MAX` for active/high-attention snapshots; `SUM` for new arrivals

Add a second time-series chart titled **Patient Flow — Arrivals, Admissions & Discharges** using `window_start` as the dimension and `new_arrivals`, `admissions`, and `discharges` as `SUM` metrics.

## Current Attention Levels

- Source: `active_patients`
- Chart: donut or horizontal bar
- Dimension: `attention_level`
- Metric: Record Count
- Order: use optional `Attention Sort Order` from `looker_calculated_fields.md` to display LOW, MEDIUM, HIGH, CRITICAL.

## Active ED Operational Queue

- Source: `active_patients`
- Columns: `visit_id`, `triage_level`, `age`, `sex`, `current_status`, `waiting_minutes`, `expected_wait_minutes`, `wait_vs_expected_minutes`, `attention_score`, `attention_level`, `attention_reason`
- Sort: `attention_score` descending, then `waiting_minutes` descending
- Aggregation: `NONE` for dimensions; `MAX` for numeric visit attributes
- Conditional formatting: CRITICAL dark red/white; HIGH orange/white; MEDIUM amber/dark text; LOW neutral gray.

The table is operational prioritization only and must not imply diagnosis or validated clinical decision support.

## Current vs Historical Context

Use a grouped horizontal bar chart from `active_patients`:

- Dimension: `visit_id`
- Metrics: `waiting_minutes`, `expected_wait_minutes`, `historical_p90_wait_minutes`
- Aggregation: `MAX`
- Sort: `attention_score` descending

Title: **Current vs Historical Context**. Waiting time and ED length of stay are distinct; never substitute LOS fields for wait fields.

## Controls

Add three drop-down controls sourced from `active_patients`: `triage_level`, `attention_level`, and `current_status`. A date control is optional and only useful for the load chart.

Suggested story and colors match the local HTML dashboard: executive cards, load trend, explainable attention, active queue, then historical comparison.
