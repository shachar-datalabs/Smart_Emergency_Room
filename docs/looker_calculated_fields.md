# Looker Studio calculated fields

No calculated field is required for the six KPI cards or operational table; those values are prepared upstream. The following optional fields are copy-paste ready.

## Attention Sort Order

```text
CASE
  WHEN attention_level = "LOW" THEN 1
  WHEN attention_level = "MEDIUM" THEN 2
  WHEN attention_level = "HIGH" THEN 3
  WHEN attention_level = "CRITICAL" THEN 4
  ELSE 0
END
```

- Data type: Number
- Purpose: logical LOW → CRITICAL ordering for the attention chart.

## Wait Variance Category

```text
CASE
  WHEN wait_vs_expected_minutes <= 0 THEN "At or below expected"
  WHEN wait_ratio >= 2 THEN "At least 2x expected"
  ELSE "Above expected"
END
```

- Data type: Text
- Purpose: optional presentation grouping. It is operational context, not a clinical label.
