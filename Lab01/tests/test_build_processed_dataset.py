"""Testes do pipeline integrado das RQs 01–06."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "src" / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

from build_processed_dataset import build, calculate_metrics, normalize  # noqa: E402


def raw_row(**overrides):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo", "url": "https://github.com/owner/repo",
        "owner": "owner", "stargazer_count": "100", "is_archived": "false",
        "collected_at": "2026-08-18T12:00:00Z", "created_at": "2024-08-18T12:00:00Z",
        "merged_pull_requests": "20", "total_pull_requests": "25", "releases_count": "5",
        "updated_at": "2026-08-18T12:00:00Z", "pushed_at": "2026-08-16T12:00:00Z",
        "default_branch": "main", "total_commits": "100", "last_commit_date": "2026-08-17T12:00:00Z",
        "primary_language": "Python", "open_issues": "20", "closed_issues": "80",
    }
    row.update(overrides)
    return row


class ProcessedDatasetTests(unittest.TestCase):
    def test_calculates_all_rq_metrics_and_normalizes_missing_values(self):
        raw = pd.DataFrame([
            raw_row(),
            raw_row(id="repo-2", primary_language="", open_issues="0", closed_issues="0", last_commit_date=""),
        ])

        result = calculate_metrics(normalize(raw))

        first, second = result.iloc[0], result.iloc[1]
        self.assertAlmostEqual(first["age_years"], 730 / 365.25)
        self.assertEqual(first["accepted_pull_requests"], 20)
        self.assertEqual(first["days_since_last_commit"], 1)
        self.assertEqual(first["days_since_push"], 2)
        self.assertEqual(first["development_period_days"], 729)
        self.assertTrue(first["is_popular_language"])
        self.assertEqual(first["total_issues"], 100)
        self.assertAlmostEqual(first["closed_issues_percentage"], 80.0)
        self.assertEqual(second["primary_language"], "Sem linguagem identificada")
        self.assertFalse(second["has_issues"])
        self.assertTrue(pd.isna(second["closed_issues_percentage"]))
        self.assertTrue(pd.isna(second["days_since_last_commit"]))

    def test_reexecution_produces_the_same_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "repos_raw_test.csv"
            first_output = root / "first.csv"
            second_output = root / "second.csv"
            pd.DataFrame([raw_row(), raw_row(id="repo-2", releases_count="1000")]).to_csv(source, index=False)

            build(source, first_output)
            build(source, second_output)

            self.assertEqual(first_output.read_bytes(), second_output.read_bytes())
            result = pd.read_csv(first_output)
            self.assertTrue(result.loc[1, "releases_no_teto"])

    def test_rejects_invalid_required_date(self):
        raw = pd.DataFrame([raw_row(created_at="não é uma data")])
        with self.assertRaisesRegex(ValueError, "created_at: data inválida"):
            normalize(raw)


if __name__ == "__main__":
    unittest.main()
