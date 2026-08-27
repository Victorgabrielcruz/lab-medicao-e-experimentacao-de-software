"""Testes da análise integrada da RQ07 (S03-02)."""

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "src" / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

from rq07_analysis import (  # noqa: E402
    analyze,
    identify_outliers,
    load,
    prepare,
    report_text,
    save_figures,
)


def rows():
    return pd.DataFrame({
        "id": ["1", "2", "3", "4", "5"],
        "name_with_owner": ["a/a", "b/b", "c/c", "d/d", "e/e"],
        "stargazer_count": [10, 20, 30, 40, 50],
        "language_group": ["Python", "JavaScript", "Rust", "Go", "Sem linguagem identificada"],
        "is_popular_language": [True, True, False, True, False],
        "age_years": [1, 2, 3, 4, 5],
        "accepted_pull_requests": [10, 30, 5, 20, 1000],
        "releases_count": [1, 3, 1, 2, 100],
        "days_since_push": [2, 4, 20, 6, 100],
        "total_issues": [2, 4, 8, 10, 20],
        "closed_issues_percentage": [50, 75, 25, 80, 90],
    })


class Rq07AnalysisTests(unittest.TestCase):
    def test_prepares_categories_and_excludes_missing_language_from_comparison(self):
        prepared, excluded = prepare(rows())

        self.assertEqual(excluded, 1)
        self.assertEqual(prepared.loc[0, "language_category"], "Popular")
        self.assertEqual(prepared.loc[2, "language_category"], "Não popular")
        self.assertTrue(pd.isna(prepared.loc[4, "language_category"]))

    def test_calculates_group_statistics_and_correlations_for_rq01_to_rq06(self):
        result = analyze(rows())

        popular_prs = result.group_statistics[
            (result.group_statistics["grupo"] == "Popular")
            & (result.group_statistics["metrica"] == "accepted_pull_requests")
        ].iloc[0]
        self.assertEqual(popular_prs["n"], 3)
        self.assertEqual(popular_prs["mediana"], 20)
        self.assertEqual(set(result.correlations["metrica"]), {
            "age_years", "accepted_pull_requests", "releases_count", "days_since_push",
            "total_issues", "closed_issues_percentage",
        })

    def test_identifies_iqr_outlier(self):
        df = rows()
        df.loc[4, "accepted_pull_requests"] = 10000
        outliers = identify_outliers(prepare(df)[0])

        self.assertIn("e/e", set(outliers["name_with_owner"]))
        self.assertIn("accepted_pull_requests", set(outliers["metrica"]))

    def test_load_rejects_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.csv"
            rows().drop(columns=["releases_count"]).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                load(path)

    def test_writes_svg_visualizations_and_report_text(self):
        result = analyze(rows())
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            import rq07_analysis as module
            original = module.FIGURES_DIR
            module.FIGURES_DIR = temp
            try:
                figures = save_figures(result, "test")
            finally:
                module.FIGURES_DIR = original

            self.assertTrue(figures[0].exists())
            self.assertTrue(figures[1].exists())
            self.assertIn("<svg", figures[0].read_text(encoding="utf-8"))
            text = report_text(result, Path("repos_rq07_consolidated_test.csv"), temp / "stats.csv", temp / "outliers.csv", figures)
            self.assertIn("Comparação por popularidade da linguagem", text)


if __name__ == "__main__":
    unittest.main()
