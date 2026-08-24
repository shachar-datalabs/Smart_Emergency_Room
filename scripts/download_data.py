#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.sources.nhamcs.download import download_nhamcs

if __name__ == "__main__":
    path = download_nhamcs(ROOT / "data/raw/nhamcs/2022")
    print(f"NHAMCS ED 2022 ready: {path} ({path.stat().st_size} bytes)")
