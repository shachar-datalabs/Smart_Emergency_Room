# Android setup — Smart Emergency Room

The data is already in [Smart Emergency Room - Looker Data](https://docs.google.com/spreadsheets/d/1UWjWKcKPLMPaaq_PGcRD1MjrhUlEZr3uf-470MomPWQ/edit); do not edit it.

1. Open [Looker Studio](https://lookerstudio.google.com/) in Chrome. If editing controls are hidden, open Chrome menu → **Desktop site** and rotate to landscape.
2. Tap **Create → Report → Google Sheets**.
3. Select **Smart Emergency Room - Looker Data**, choose `ED_KPIS`, then **Add**.
4. Use **Resource → Manage added data sources → Add a data source** and add the same Sheet four more times, selecting `ED_LOAD_15MIN`, `ACTIVE_PATIENTS`, `HISTORICAL_CONTEXT`, and `DATA_QUALITY`.
5. Name the report **Smart Emergency Room** and build the single page using `looker_studio_dashboard.md`.

Only the report UI remains manual. Tabs, headers, types, metrics, categories, percentages, timestamps, and attention reasons are prepared.
