#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common.io import read_jsonl


def main() -> None:
    gold = ROOT / "data/gold"
    kpis = json.loads((gold / "ed_kpis.json").read_text(encoding="utf-8"))
    states = list(read_jsonl(gold / "current_ed_state.jsonl"))
    cards = [
        ("Active Patients", kpis["active_patients"]),
        ("Average Wait", f"{kpis['avg_wait_minutes']} min"),
        ("Above Expected", kpis["patients_above_expected_wait"]),
        ("High Attention", kpis["high_attention_patients"]),
        ("Admissions", kpis["admissions"]),
        ("Discharges", kpis["discharges"]),
    ]
    rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(value))}</td>"
            for value in (
                state["visit_id"],
                state.get("triage_level"),
                state["waiting_minutes"],
                state["expected_wait_minutes"],
                state["wait_vs_expected_minutes"],
                state["current_status"],
                state["attention_level"],
                ", ".join(state["attention_reason"]),
            )
        )
        + "</tr>"
        for state in states
    )
    card_html = "".join(
        f'<section class="card"><span>{html.escape(label)}</span><strong>{value}</strong></section>'
        for label, value in cards
    )
    document = f"""<!doctype html><html><head><meta charset="utf-8"><title>Smart Emergency Room</title>
<style>body{{font:15px system-ui;background:#f4f7fb;color:#17233c;margin:32px}}h1{{margin-bottom:4px}}.note{{color:#68748a}}.provenance{{background:#eaf4ff;border-left:4px solid #2878c8;padding:14px 16px;border-radius:8px;line-height:1.5}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:24px 0}}.card{{background:white;padding:18px;border-radius:12px;box-shadow:0 2px 10px #ccd4e4}}.card span{{display:block;color:#68748a}}.card strong{{font-size:28px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border-bottom:1px solid #e5e9f2;text-align:left}}th{{background:#17233c;color:white}}</style></head>
<body><h1>Smart Emergency Room</h1><p class="note">Educational operational analytics demo - not medical decision support. Snapshot as of {html.escape(kpis["as_of"])}</p>
<p class="provenance"><strong>Data provenance:</strong> Historical benchmarks are calculated from 16,025 real, anonymized CDC NHAMCS 2022 emergency-department visit records. Active patients, the event stream, current-state KPIs, identifiers and vital signs are deterministic synthetic demo data. No live hospital data is used.</p>
<div class="cards">{card_html}</div><h2>Active operational queue</h2><table><thead><tr><th>Visit</th><th>Triage</th><th>Wait</th><th>Expected</th><th>Difference</th><th>Status</th><th>Attention</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
    destinations = (
        gold / "smart_er_dashboard.html",
        ROOT / "dashboards/smart_er_dashboard.html",
    )
    for destination in destinations:
        destination.write_text(document, encoding="utf-8")
        print(f"Dashboard generated: {destination}")


if __name__ == "__main__":
    main()
