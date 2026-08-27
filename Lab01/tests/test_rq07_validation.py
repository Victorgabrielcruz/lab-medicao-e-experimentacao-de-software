"""Testes da validação da análise integrada da RQ07."""

import sys
import unittest
from pathlib import Path

import pandas as pd

ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "src" / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

from rq07_analysis import analyze  # noqa: E402
from rq07_validation import outliers_path_for, validate  # noqa: E402


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


def statistics_from(result) -> pd.DataFrame:
    """Reproduz o CSV de estatísticas exatamente como `rq07_analysis.run` grava."""
    return pd.concat(
        [result.group_statistics.assign(tipo="grupo"), result.correlations.assign(tipo="correlacao")],
        ignore_index=True, sort=False,
    )


class Rq07ValidationTests(unittest.TestCase):
    def test_valid_artifacts_have_no_inconsistencies(self):
        consolidated = rows()
        result = analyze(consolidated)

        validation = validate(consolidated, statistics_from(result), result.outliers)

        self.assertTrue(validation.passed)
        self.assertEqual(validation.repositories, 5)
        self.assertEqual(validation.excluded_without_language, 1)
        self.assertEqual(validation.outliers_recomputed, len(result.outliers))

    def test_detects_divergent_group_statistic(self):
        consolidated = rows()
        result = analyze(consolidated)
        statistics = statistics_from(result)
        statistics.loc[
            (statistics["tipo"] == "grupo") & (statistics["metrica"] == "accepted_pull_requests")
            & (statistics["grupo"] == "Popular"),
            "mediana",
        ] = 999

        validation = validate(consolidated, statistics, result.outliers)

        self.assertFalse(validation.passed)
        self.assertTrue(any("group_statistics" in field for field in validation.issues["field"]))

    def test_detects_missing_group_statistic_row(self):
        consolidated = rows()
        result = analyze(consolidated)
        statistics = statistics_from(result)
        statistics = statistics.loc[
            ~((statistics["tipo"] == "grupo") & (statistics["metrica"] == "releases_count") & (statistics["grupo"] == "Popular"))
        ]

        validation = validate(consolidated, statistics, result.outliers)

        self.assertFalse(validation.passed)
        self.assertTrue(any("group_statistics[Popular/releases_count]" in field for field in validation.issues["field"]))

    def test_detects_divergent_correlation(self):
        consolidated = rows()
        result = analyze(consolidated)
        statistics = statistics_from(result)
        statistics.loc[(statistics["tipo"] == "correlacao") & (statistics["metrica"] == "age_years"), "pearson"] = 0

        validation = validate(consolidated, statistics, result.outliers)

        self.assertFalse(validation.passed)
        self.assertTrue(any("correlations[age_years]" in field for field in validation.issues["field"]))

    def test_detects_missing_and_extra_outliers(self):
        consolidated = rows()
        result = analyze(consolidated)
        # Remove um outlier real e adiciona um sinalizado indevidamente.
        outliers = result.outliers.iloc[0:0].copy() if result.outliers.empty else result.outliers.iloc[1:].copy()
        spurious = pd.DataFrame([{
            "id": "2", "name_with_owner": "b/b", "language_category": "Popular",
            "metrica": "releases_count", "descricao": "Releases", "valor": 3,
            "limite_inferior": 0, "limite_superior": 2,
        }])
        outliers = pd.concat([outliers, spurious], ignore_index=True)

        validation = validate(consolidated, statistics_from(result), outliers)

        self.assertFalse(validation.passed)
        fields = set(validation.issues["field"])
        self.assertTrue(any(field.startswith("outliers[") for field in fields))

    def test_detects_outlier_id_not_in_consolidated(self):
        consolidated = rows()
        result = analyze(consolidated)
        outliers = pd.concat([result.outliers, pd.DataFrame([{
            "id": "999", "name_with_owner": "ghost/ghost", "language_category": "Popular",
            "metrica": "releases_count", "descricao": "Releases", "valor": 500,
            "limite_inferior": 0, "limite_superior": 10,
        }])], ignore_index=True)

        validation = validate(consolidated, statistics_from(result), outliers)

        self.assertFalse(validation.passed)
        self.assertIn("outliers[id]", set(validation.issues["field"]))

    def test_rejects_duplicated_ids_in_consolidated(self):
        consolidated = pd.concat([rows(), rows().iloc[[0]]], ignore_index=True)
        result = analyze(rows())

        with self.assertRaisesRegex(ValueError, "duplicados"):
            validate(consolidated, statistics_from(result), result.outliers)

    def test_outliers_path_for_derives_name_from_statistics_path(self):
        statistics_path = Path("data/processed/rq07_statistics_2026-01-01T000000Z.csv")
        expected = Path("data/processed/rq07_analysis_outliers_2026-01-01T000000Z.csv")

        self.assertEqual(outliers_path_for(statistics_path), expected)


if __name__ == "__main__":
    unittest.main()
