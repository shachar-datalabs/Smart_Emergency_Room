from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from src.common.io import write_jsonl


def ingest_bronze(source: Path, destination: Path) -> int:
    ingestion_time = datetime.now(UTC).isoformat()

    def rows():
        with source.open("r", encoding="ascii", errors="strict") as stream:
            for index, line in enumerate(stream, start=1):
                raw = line.rstrip("\r\n")
                if not raw:
                    continue
                yield {
                    "raw_record": raw,
                    "source_system": "CDC_NHAMCS_ED",
                    "source_year": 2022,
                    "source_filename": source.name,
                    "source_row_number": index,
                    "ingestion_timestamp": ingestion_time,
                }

    return write_jsonl(destination, rows())
