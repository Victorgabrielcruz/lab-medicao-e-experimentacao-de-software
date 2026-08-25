"""Testes do consolidador do dataset da RQ07 (S03-01)."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "src" / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

from consolidate_rq07_dataset import (  # noqa: E402
    consolidate,
    load,
    output_for,
    run,
)


def processed_row(**overrides):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo", "url": "https://github.com/owner/repo",
        "owner": "owner", "stargazer_count": 100, "is_archived": False,
        "collected_at": "2026-08-18T12:00:00Z", "created_at": "2024-08-18T12:00:00Z",
        "merged_pull_requests": 20, "total_pull_requests": 25, "releases_count": 5,
        "updated_at": "2026-08-18T12:00:00Z", "pushed_at": "2026-08-16T12:00:00Z",
        "default_branch": "main", "total_commits": 100, "last_commit_date": "2026-08-17T12:00:00Z",
        "primary_language": "Python", "open_issues": 20, "closed_issues": 80,
        "age_years": 2.0, "accepted_pull_requests": 20, "releases_no_teto": False,
        "days_since_last_commit": 1, "days_since_push": 2, "development_period_days": 729,
        "language_group": "Python", "is_popular_language": True,
        "total_issues": 100, "has_issues": True, "closed_issues_percentage": 80.0,
    }
    row.update(overrides)
    return row


class ConsolidateRq07DatasetTests(unittest.TestCase):
    def test_consolidates_a_valid_dataset_without_issues(self):
        df = pd.DataFrame([
            processed_row(),
            processed_row(
                id="repo-2", name_with_owner="owner/repo2", primary_language="",
                language_group="Sem linguagem identificada", open_issues=0, closed_issues=0,
                total_issues=0, has_issues=False, closed_issues_percentage=None,
                days_since_last_commit=None, days_since_push=None, development_period_days=None,
            ),
        ])

        result = consolidate(df)

        self.assertTrue(result.passed)
        self.assertEqual(result.repositories, 2)
        self.assertEqual(result.duplicated_ids, [])
        self.assertEqual(result.missing_columns, [])
        self.assertEqual(result.without_language, 1)
        self.assertEqual(result.without_issues, 1)
        self.assertEqual(result.missing_value_counts["closed_issues_percentage"], 1)

    def test_detects_duplicated_ids(self):
        df = pd.DataFrame([processed_row(), processed_row(name_with_owner="owner/repo-dup")])

        result = consolidate(df)

        self.assertFalse(result.passed)
        self.assertEqual(result.duplicated_ids, ["repo-1"])

    def test_detects_missing_required_columns(self):
        df = pd.DataFrame([processed_row()]).drop(columns=["age_years"])

        result = consolidate(df)

        self.assertFalse(result.passed)
        self.assertEqual(result.missing_columns, ["age_years"])

    def test_run_writes_consolidated_csv_and_report_and_fails_on_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "repos_processed_test.csv"
            pd.DataFrame([processed_row(), processed_row(id="repo-2")]).to_csv(source, index=False)

            import consolidate_rq07_dataset as module
            module.PROCESSED_DIR = root
            module.REPORTS_DIR = root / "drafts"

            result, output, report = run(source)

            self.assertTrue(result.passed)
            self.assertEqual(output, output_for(source))
            self.assertTrue(output.exists())
            self.assertTrue(report.exists())
            self.assertEqual(len(pd.read_csv(output)), 2)

            duplicated_source = root / "repos_processed_dup.csv"
            pd.DataFrame([processed_row(), processed_row()]).to_csv(duplicated_source, index=False)
            with self.assertRaisesRegex(ValueError, "IDs duplicados"):
                run(duplicated_source)

    def test_load_preserves_id_as_text(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "repos_processed_test.csv"
            pd.DataFrame([processed_row(id="007")]).to_csv(source, index=False)

            df = load(source)

            self.assertEqual(df.loc[0, "id"], "007")
            self.assertEqual(df["id"].dtype, "string")


if __name__ == "__main__":
    unittest.main()
