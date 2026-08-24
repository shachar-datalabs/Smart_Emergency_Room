#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bi.looker_export import SHEET_ORDER


def main() -> None:
    output = ROOT / "exports/looker"
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if manifest["sheet_order"] != SHEET_ORDER:
        raise ValueError("Manifest sheet order is invalid")

    checked_rows: dict[str, int] = {}
    forbidden = ("private key", "client_secret", "password=", "token=")
    for name in SHEET_ORDER:
        path = output / f"{name}.csv"
        content = path.read_text(encoding="utf-8")
        if any(marker in content.lower() for marker in forbidden):
            raise ValueError(f"Potential secret in {path.name}")
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        if not rows or rows.count(rows[0]) != 1:
            raise ValueError(f"Duplicate or missing header in {path.name}")
        if rows[0] != manifest["columns"][name]:
            raise ValueError(f"Column mismatch in {path.name}")
        checked_rows[name] = len(rows) - 1

    workbook = output / "Smart_Emergency_Room_Looker_Source.xlsx"
    with zipfile.ZipFile(workbook) as archive:
        if archive.testzip() is not None:
            raise ValueError("Workbook ZIP integrity failed")
        xml = ElementTree.fromstring(archive.read("xl/workbook.xml"))
        namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet_names = [item.attrib["name"] for item in xml.findall("x:sheets/x:sheet", namespace)]
    if sheet_names != SHEET_ORDER:
        raise ValueError(f"Workbook sheets invalid: {sheet_names}")
    if checked_rows != manifest["rows"]:
        raise ValueError("CSV row counts do not match manifest")
    print(json.dumps({"status": "PASS", "sheets": sheet_names, "rows": checked_rows}, indent=2))


if __name__ == "__main__":
    main()
