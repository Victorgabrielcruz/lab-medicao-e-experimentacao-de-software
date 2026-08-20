"""Testes da validação de releases e atividade (RQ03/RQ04)."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

METRICS_DIR = Path(__file__).resolve().parents[1] / "src" / "metrics"
sys.path.insert(0, str(METRICS_DIR))

from rq03_rq04_validation import save_evidence, validate  # noqa: E402


def base_row(**changes):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo", "releases_count": 1000,
        "releases_no_teto": True, "total_commits": 25,
        "created_at": "2020-01-01T00:00:00Z", "last_commit_date": "2020-01-11T00:00:00Z",
        "pushed_at": "2020-01-10T00:00:00Z", "updated_at": "2020-01-10T00:00:00Z",
        "collected_at": "2020-01-21T00:00:00Z", "days_since_last_commit": 10,
        "days_since_push": 11, "development_period_days": 10,
    }
    row.update(changes)
    return row


class Rq03Rq04ValidationTests(unittest.TestCase):
    def test_valid_dataset_has_no_inconsistencies_and_registers_evidence(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([base_row()])

        result = validate(raw, processed)

        self.assertTrue(result.passed)
        self.assertEqual(result.repositories, 1)
        self.assertEqual(result.releases_at_cap, 1)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            processed_path = output_dir / "repos_processed_test.csv"
            evidence, report = save_evidence(result, processed_path, output_dir, output_dir)
            self.assertTrue(evidence.exists())
            self.assertTrue(report.exists())
            self.assertIn("APROVADA", report.read_text(encoding="utf-8"))

    def test_detects_formula_and_raw_value_divergences(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([
            base_row(releases_count=3, releases_no_teto=False, days_since_last_commit=5)
        ])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("releases_count", set(result.issues["field"]))
        self.assertIn("releases_no_teto", set(result.issues["field"]))
        self.assertIn("days_since_last_commit", set(result.issues["field"]))

    def test_records_repository_without_last_commit_without_creating_false_metric_error(self):
        raw = pd.DataFrame([base_row(total_commits=pd.NA, last_commit_date=pd.NA, development_period_days=pd.NA,
                                     days_since_last_commit=pd.NA)])
        processed = raw.copy()

        result = validate(raw, processed)

        self.assertTrue(result.passed)
        self.assertEqual(result.without_commits, 1)


if __name__ == "__main__":
    unittest.main()
