"""Testes das métricas RQ05 e RQ06.

Porte de tests/Metrics.Tests/Program.cs. Os quatro primeiros casos de
CalculoTest são os mesmos do teste que existia em C#.

    python3 -m unittest discover -s tests
"""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "metrics"))

import pandas as pd

from rq05_rq06_language_issues import (
    UNIDENTIFIED_LANGUAGE,
    add_metrics,
    calculate,
)


class CalculoTest(unittest.TestCase):
    """Regras de um repositório isolado."""

    def test_linguagem_popular_com_issues(self):
        resultado = calculate("Python", 20, 80)

        self.assertEqual(resultado["language_group"], "Python")
        self.assertTrue(resultado["is_popular_language"])
        self.assertEqual(resultado["total_issues"], 100)
        self.assertTrue(resultado["has_issues"])
        self.assertEqual(resultado["closed_issues_percentage"], 80)

    def test_nenhuma_issue_fechada(self):
        resultado = calculate("Java", 10, 0)

        self.assertTrue(resultado["is_popular_language"])
        self.assertEqual(resultado["closed_issues_percentage"], 0)

    def test_linguagem_fora_do_ranking(self):
        resultado = calculate("Rust", 0, 10)

        self.assertFalse(resultado["is_popular_language"])
        self.assertEqual(resultado["closed_issues_percentage"], 100)

    def test_sem_linguagem_e_sem_issues(self):
        resultado = calculate(None, 0, 0)

        self.assertEqual(resultado["language_group"], UNIDENTIFIED_LANGUAGE)
        self.assertFalse(resultado["is_popular_language"])
        self.assertEqual(resultado["total_issues"], 0)
        self.assertFalse(resultado["has_issues"])
        self.assertIsNone(resultado["closed_issues_percentage"])

    def test_linguagem_ignora_caixa_e_espacos(self):
        self.assertTrue(calculate("  typescript  ", 1, 1)["is_popular_language"])
        self.assertTrue(calculate("C#", 1, 1)["is_popular_language"])
        self.assertEqual(calculate("   ", 1, 1)["language_group"], UNIDENTIFIED_LANGUAGE)

    def test_issues_negativas_falham(self):
        for open_issues, closed_issues in [(-1, 0), (0, -1)]:
            with self.subTest(open_issues=open_issues, closed_issues=closed_issues):
                with self.assertRaises(ValueError):
                    calculate("Go", open_issues, closed_issues)


class AddMetricsTest(unittest.TestCase):
    """Aplicação sobre o DataFrame, que é como o pipeline usa."""

    def setUp(self):
        self.df = add_metrics(
            pd.DataFrame(
                {
                    "primary_language": ["Python", None, "Rust"],
                    "open_issues": [20, 0, 0],
                    "closed_issues": [80, 0, 10],
                }
            )
        )

    def test_normaliza_linguagem_ausente(self):
        self.assertEqual(
            list(self.df["language_group"]),
            ["Python", UNIDENTIFIED_LANGUAGE, "Rust"],
        )

    def test_marca_linguagem_popular(self):
        self.assertEqual(list(self.df["is_popular_language"]), [True, False, False])

    def test_soma_total_de_issues(self):
        self.assertEqual(list(self.df["total_issues"]), [100, 0, 10])

    def test_percentual_vazio_quando_nao_ha_issues(self):
        percentuais = self.df["closed_issues_percentage"]

        self.assertEqual(percentuais.iloc[0], 80)
        self.assertTrue(pd.isna(percentuais.iloc[1]))
        self.assertEqual(percentuais.iloc[2], 100)

    def test_preserva_a_coluna_bruta(self):
        self.assertEqual(self.df["primary_language"].iloc[0], "Python")
        self.assertTrue(pd.isna(self.df["primary_language"].iloc[1]))
        self.assertEqual(self.df["primary_language"].iloc[2], "Rust")

    def test_issues_negativas_falham(self):
        df = pd.DataFrame(
            {
                "primary_language": ["Go"],
                "open_issues": [-1],
                "closed_issues": [0],
            }
        )

        with self.assertRaises(ValueError):
            add_metrics(df)


if __name__ == "__main__":
    unittest.main()
