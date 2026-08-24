from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from src.cohorts.historical import age_group, build_cohorts
from src.common.io import read_jsonl, write_jsonl
from src.sources.nhamcs.layout import FIELDS
from src.transformations.nhamcs_silver import canonicalize


def record(**values: str) -> str:
    chars = [" "] * 2383
    for name, value in values.items():
        field = FIELDS[name]
        text = str(value).rjust(field.width)
        chars[field.start - 1 : field.start - 1 + field.width] = text
    return "".join(chars)


class HistoricalTests(unittest.TestCase):
    def test_nhamcs_mapping_and_schema(self) -> None:
        bronze = {
            "raw_record": record(
                visit_month="08",
                visit_weekday="2",
                arrival_time="1830",
                waiting_time_minutes="0045",
                length_of_stay_minutes="0180",
                age="046",
                sex="2",
                triage_level="03",
                temperature_f="0986",
                heart_rate="092",
                respiratory_rate="018",
                systolic_bp="128",
                diastolic_bp="076",
                spo2="097",
                pain_score="04",
                reason_for_visit_code="12345",
                diagnosis_code="R509",
                no_followup="1",
                patient_weight="1234.50000",
            ),
            "source_row_number": 1,
            "ingestion_timestamp": datetime.now(UTC).isoformat(),
        }
        row = canonicalize(bronze)
        self.assertEqual(3, row["triage_level"])
        self.assertEqual(98.6, row["temperature"])
        self.assertEqual("M", row["sex"])
        self.assertEqual("DISCHARGED", row["disposition"])
        self.assertEqual([], row["data_quality_flags"])
        required = {
            "visit_id",
            "patient_id",
            "arrival_time",
            "age",
            "sex",
            "triage_level",
            "chief_complaint",
            "temperature",
            "heart_rate",
            "respiratory_rate",
            "systolic_bp",
            "diastolic_bp",
            "spo2",
            "pain_score",
            "diagnosis_code",
            "diagnosis_description",
            "disposition",
            "admitted_flag",
            "waiting_time_minutes",
            "length_of_stay_minutes",
            "source_system",
            "source_record_id",
            "ingestion_timestamp",
        }
        self.assertTrue(required.issubset(row))

    def test_invalid_vitals_are_flagged_not_deleted(self) -> None:
        bronze = {
            "raw_record": record(
                age="025",
                sex="1",
                triage_level="03",
                heart_rate="000",
                spo2="120",
                systolic_bp="060",
                diastolic_bp="080",
            ),
            "source_row_number": 2,
            "ingestion_timestamp": "2026-01-01T00:00:00Z",
        }
        flags = canonicalize(bronze)["data_quality_flags"]
        self.assertIn("INVALID_HEART_RATE", flags)
        self.assertIn("INVALID_SPO2", flags)
        self.assertIn("INVALID_BP_RELATION", flags)

    def test_canonicalization_is_deterministic(self) -> None:
        bronze = {"raw_record": record(age="025"), "source_row_number": 3, "ingestion_timestamp": "x"}
        self.assertEqual(canonicalize(bronze), canonicalize(bronze))

    def test_cohorts_and_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "silver.jsonl"
            output = Path(temporary) / "cohorts.jsonl"
            rows = [
                {
                    "triage_level": 3,
                    "age": 30,
                    "arrival_hour": 10,
                    "waiting_time_minutes": 10,
                    "length_of_stay_minutes": 100,
                    "admitted_flag": False,
                },
                {
                    "triage_level": 3,
                    "age": 31,
                    "arrival_hour": 10,
                    "waiting_time_minutes": 30,
                    "length_of_stay_minutes": 200,
                    "admitted_flag": True,
                },
            ]
            write_jsonl(source, rows)
            build_cohorts(source, output)
            cohorts = {row["cohort_key"]: row for row in read_jsonl(output)}
            exact = cohorts["TRIAGE_AGE_HOUR|3|18-44|10"]
            self.assertEqual(20, exact["median_wait_minutes"])
            self.assertEqual(0.5, exact["admission_rate"])
            self.assertIn("OVERALL|ALL|ALL|ALL", cohorts)

    def test_age_groups(self) -> None:
        self.assertEqual("0-17", age_group(17))
        self.assertEqual("18-44", age_group(18))
        self.assertEqual("75+", age_group(75))
