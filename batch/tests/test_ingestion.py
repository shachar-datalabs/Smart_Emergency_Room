from __future__ import annotations

import csv
import gzip
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "batch" / "src"))

from ingestion.mimic_ed import HEADERS, IngestionConfig, ingest, validate_sources  # noqa: E402


ROWS = {
    "edstays": ["100001", "200001", "300001", "2130-01-01 10:00:00", "2130-01-01 12:00:00", "F", "OTHER", "WALK IN", "HOME"],
    "triage": ["100001", "300001", "98.6", "80", "18", "99", "120", "70", "2", "3", "Headache, mild"],
    "vitalsign": ["100001", "300001", "2130-01-01 10:30:00", "98.7", "82", "18", "99", "121", "71", "Sinus", "2"],
}


class IngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp.name)
        for table, header in HEADERS.items():
            with gzip.open(
                self.source_dir / f"{table}.csv.gz", "wt", encoding="utf-8", newline=""
            ) as stream:
                writer = csv.writer(stream)
                writer.writerow(header)
                writer.writerow(ROWS[table])
        self.config = IngestionConfig(
            project="test-project",
            bucket="test-bucket",
            dataset="smart_er_bronze",
            location="us-central1",
            version="2.2",
            source_dir=self.source_dir,
            schema_dir=ROOT / "config" / "schemas" / "mimic_iv_ed_2_2",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_valid_mock_sources(self) -> None:
        results = validate_sources(self.config)
        self.assertEqual(["edstays", "triage", "vitalsign"], [r.table for r in results])
        self.assertTrue(all(result.row_count == 1 for result in results))
        self.assertTrue(all(len(result.sha256) == 64 for result in results))

    def test_rejects_header_mismatch(self) -> None:
        with gzip.open(
            self.source_dir / "triage.csv.gz", "wt", encoding="utf-8", newline=""
        ) as stream:
            csv.writer(stream).writerows((("wrong", "header"), ("1", "2")))
        with self.assertRaisesRegex(ValueError, "Unexpected header"):
            validate_sources(self.config)

    def test_dry_run_never_calls_cloud_runner(self) -> None:
        def forbidden_runner(command):
            self.fail(f"Cloud command called during dry run: {command}")

        results = ingest(self.config, runner=forbidden_runner)
        self.assertEqual(3, len(results))

    def test_raw_object_path_is_versioned(self) -> None:
        self.assertEqual(
            "gs://test-bucket/mimic-iv-ed/2.2/ed/edstays.csv.gz",
            self.config.object_uri("edstays"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
