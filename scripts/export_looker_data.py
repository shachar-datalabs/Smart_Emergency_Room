#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bi.looker_export import export_looker_source

if __name__ == "__main__":
    print(json.dumps(export_looker_source(ROOT), indent=2))
