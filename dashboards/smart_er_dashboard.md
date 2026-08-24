# Smart Emergency Room dashboard specification

The BI surface consumes the three Gold outputs. It is an operational demo, not
a medical diagnostic or validated clinical decision-support product.

## Executive row

Six scorecards from `ed_kpis`: active patients, average wait, patients above
expected wait, high-attention patients, admissions, and discharges.

## ED load trend

Time-series chart from `ed_load_15min`, with `window_start` on the x-axis and
active patients/new arrivals/admissions/discharges as selectable metrics.

## Active operational queue

Table from `current_ed_state`: visit, triage, waiting minutes, expected wait,
wait difference, current status, latest SpO2/heart rate, attention level, and
explicit attention reasons. Color attention levels consistently: LOW gray,
MEDIUM amber, HIGH orange, CRITICAL red.

## Historical context

Distribution cards for matched cohort level and a comparison plot of current
wait versus cohort median and p90. Include a visible note that NHAMCS is
visit-level survey data and simulated patients are unrelated synthetic records.
