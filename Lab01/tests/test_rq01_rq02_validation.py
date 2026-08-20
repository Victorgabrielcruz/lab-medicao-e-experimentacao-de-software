"""Testes da validação de idade e Pull Requests aceitas (RQ01/RQ02)."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

METRICS_DIR = Path(__file__).resolve().parents[1] / "src" / "metrics"
sys.path.insert(0, str(METRICS_DIR))

from rq01_rq02_validation import save_evidence, validate  # noqa: E402


EXPECTED_AGE_YEARS = (
    (pd.Timestamp("2025-01-01T00:00:00Z") - pd.Timestamp("2015-01-01T00:00:00Z")).total_seconds()
    / (365.25 * 24 * 60 * 60)
)


def base_row(**changes):
    row = {
        "id": "repo-1", "name_with_owner": "owner/repo",
        "created_at": "2015-01-01T00:00:00Z", "collected_at": "2025-01-01T00:00:00Z",
        "merged_pull_requests": 40, "total_pull_requests": 50,
        "age_years": EXPECTED_AGE_YEARS, "accepted_pull_requests": 40,
    }
    row.update(changes)
    return row


class Rq01Rq02ValidationTests(unittest.TestCase):
    def test_valid_dataset_has_no_inconsistencies_and_registers_evidence(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([base_row()])

        result = validate(raw, processed)

        self.assertTrue(result.passed)
        self.assertEqual(result.repositories, 1)

        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            processed_path = output_dir / "repos_processed_test.csv"
            evidence, report = save_evidence(result, processed_path, output_dir, output_dir)
            self.assertTrue(evidence.exists())
            self.assertTrue(report.exists())
            self.assertIn("APROVADA", report.read_text(encoding="utf-8"))

    def test_detects_age_formula_divergence(self):
        raw = pd.DataFrame([base_row()])
        # age_years deveria ser ~10, não 1: fórmula divergente.
        processed = pd.DataFrame([base_row(age_years=1.0)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("age_years", set(result.issues["field"]))

    def test_detects_negative_age(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([base_row(age_years=-1.0)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("age_years", set(result.issues["field"]))

    def test_detects_created_at_before_github_founding(self):
        age = (
            (pd.Timestamp("2025-01-01T00:00:00Z") - pd.Timestamp("2005-01-01T00:00:00Z")).total_seconds()
            / (365.25 * 24 * 60 * 60)
        )
        raw = pd.DataFrame([base_row(created_at="2005-01-01T00:00:00Z")])
        processed = pd.DataFrame([base_row(created_at="2005-01-01T00:00:00Z", age_years=age)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("created_at", set(result.issues["field"]))

    def test_detects_accepted_pull_requests_diverging_from_merged(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([base_row(accepted_pull_requests=35)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("accepted_pull_requests", set(result.issues["field"]))

    def test_detects_accepted_pull_requests_exceeding_total(self):
        raw = pd.DataFrame([base_row(merged_pull_requests=60, total_pull_requests=50)])
        processed = pd.DataFrame([base_row(merged_pull_requests=60, total_pull_requests=50,
                                            accepted_pull_requests=60)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("accepted_pull_requests", set(result.issues["field"]))

    def test_detects_missing_required_fields(self):
        raw = pd.DataFrame([base_row()])
        processed = pd.DataFrame([base_row(age_years=pd.NA)])

        result = validate(raw, processed)

        self.assertFalse(result.passed)
        self.assertIn("age_years", set(result.issues["field"]))

    def test_registers_outliers_without_removing_them(self):
        rows = [base_row(id=f"repo-{i}", name_with_owner=f"owner/repo-{i}",
                          accepted_pull_requests=40, merged_pull_requests=40) for i in range(6)]
        # Um repositório com PRs aceitas muito acima do restante da amostra.
        rows.append(base_row(id="repo-outlier", name_with_owner="owner/repo-outlier",
                              accepted_pull_requests=5000, merged_pull_requests=5000,
                              total_pull_requests=5000))
        raw = pd.DataFrame(rows)
        processed = pd.DataFrame(rows)

        result = validate(raw, processed)

        self.assertTrue(result.passed)
        self.assertIn("accepted_pull_requests", set(result.outliers["field"]))
        # Outliers são só evidência: todos os 7 registros continuam validados.
        self.assertEqual(result.repositories, 7)


if __name__ == "__main__":
    unittest.main()
