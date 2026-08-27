"""Testes da validação de linguagem e issues fechadas (RQ05/RQ06)."""

import sys
import unittest
from pathlib import Path

import pandas as pd

METRICS_DIR = Path(__file__).resolve().parents[1] / "src" / "metrics"
sys.path.insert(0, str(METRICS_DIR))

from rq05_rq06_language_issues import add_metrics  # noqa: E402
from rq05_rq06_validation import validate  # noqa: E402


def raw_row(**changes):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo", "primary_language": "Python",
        "open_issues": 20, "closed_issues": 80,
    }
    row.update(changes)
    return row


def processed_from(raw: pd.DataFrame) -> pd.DataFrame:
    return add_metrics(raw.copy())


class Rq05Rq06ValidationTests(unittest.TestCase):
    def test_valid_dataset_has_no_inconsistencies(self):
        raw = pd.DataFrame([raw_row()])
        result = validate(raw, processed_from(raw))

        self.assertTrue(result.passed)
        self.assertEqual(result.repositories, 1)
        self.assertEqual(result.without_language, 0)
        self.assertEqual(result.without_issues, 0)

    def test_detects_divergent_language_issue_and_percentage_values(self):
        raw = pd.DataFrame([raw_row()])
        processed = processed_from(raw)
        processed.loc[0, "language_group"] = "Rust"
        processed.loc[0, "open_issues"] = 21
        processed.loc[0, "closed_issues_percentage"] = 75

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertTrue({"language_group", "open_issues", "closed_issues_percentage"}.issubset(set(result.issues["field"])))

    def test_records_missing_language_and_no_issues_as_valid_observations(self):
        raw = pd.DataFrame([raw_row(primary_language=None, open_issues=0, closed_issues=0)])
        result = validate(raw, processed_from(raw))

        self.assertTrue(result.passed)
        self.assertEqual(result.without_language, 1)
        self.assertEqual(result.without_issues, 1)
        self.assertEqual(set(result.observations["field"]), {"primary_language", "closed_issues_percentage"})


if __name__ == "__main__":
    unittest.main()
