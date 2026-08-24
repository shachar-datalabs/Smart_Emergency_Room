# Android setup — Smart Emergency Room

1. Open [Looker Studio](https://lookerstudio.google.com/) in Chrome → menu **⋮** → **Desktop site**; rotate to landscape.
2. Tap **Create → Report → BigQuery** and authorize the same Google account if prompted.
3. Select project `shachar-bigquery-lab` → dataset `smart_er_gold` → table `ed_kpis` → **Add**.
4. Tap **Add data → BigQuery** four times and add `ed_load_15min`, `active_patients`, `historical_context`, and `data_quality` from the same project/dataset.
5. Name the report **Smart Emergency Room** and build the one-page layout in `looker_studio_dashboard.md`.

Exact primary source: `shachar-bigquery-lab.smart_er_gold`. Do not select **Custom Query**, BI Engine, or the Google Sheet. The existing Sheet is backup only.

Looker Studio queries BigQuery when the report refreshes and may consume billed bytes. Refresh only during the demo and keep the tables small.
