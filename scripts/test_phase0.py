"""Dependency-free checks for the PHASE 0 repository foundation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PhaseZeroTests(unittest.TestCase):
    def test_required_directories_exist(self) -> None:
        required = (
            "batch/src", "batch/tests", "simulator/src", "simulator/tests",
            "streaming/src", "streaming/tests", "kafka", "sql/silver",
            "sql/gold", "docker", "scripts", "docs", "config",
        )
        missing = [path for path in required if not (ROOT / path).is_dir()]
        self.assertEqual([], missing, f"Missing directories: {missing}")

    def test_required_files_exist(self) -> None:
        for path in ("README.md", ".gitignore", "requirements.txt", "scripts/bootstrap_gcp.sh"):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_gitignore_protects_sensitive_data(self) -> None:
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        required = {
            "data/", "*.csv", "*.csv.gz", "*.parquet", ".env",
            "credentials/", "*.key", "*.pem", "service-account*.json",
            "__pycache__/", ".pytest_cache/",
        }
        self.assertFalse(required.difference(rules))

    def test_bootstrap_is_safe_by_default(self) -> None:
        script = (ROOT / "scripts/bootstrap_gcp.sh").read_text(encoding="utf-8")
        guard = script.index('if [[ "${APPLY}" != "true" ]]')
        first_mutation = script.index('gcloud config set project')
        self.assertLess(guard, first_mutation)
        self.assertIn("Dry run only", script[guard:first_mutation])
        self.assertNotIn("compute instances", script.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
