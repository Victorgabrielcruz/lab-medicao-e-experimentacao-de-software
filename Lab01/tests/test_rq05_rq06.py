"""Testes das métricas RQ05 e RQ06.

Porte de tests/Metrics.Tests/Program.cs. Os quatro primeiros casos são os
mesmos do teste em C#.

Rodar com pytest ou direto:
    python tests/test_rq05_rq06.py
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "metrics"))

import pandas as pd

from rq05_rq06_language_issues import (
    UNIDENTIFIED_LANGUAGE,
    add_metrics,
    calculate,
)


def test_linguagem_popular_com_issues():
    r = calculate("Python", 20, 80)
    assert r["language_group"] == "Python"
    assert r["is_popular_language"] is True
    assert r["total_issues"] == 100
    assert r["has_issues"] is True
    assert r["closed_issues_percentage"] == 80


def test_nenhuma_issue_fechada():
    r = calculate("Java", 10, 0)
    assert r["is_popular_language"] is True
    assert r["closed_issues_percentage"] == 0


def test_linguagem_fora_do_ranking():
    r = calculate("Rust", 0, 10)
    assert r["is_popular_language"] is False
    assert r["closed_issues_percentage"] == 100


def test_sem_linguagem_e_sem_issues():
    r = calculate(None, 0, 0)
    assert r["language_group"] == UNIDENTIFIED_LANGUAGE
    assert r["is_popular_language"] is False
    assert r["total_issues"] == 0
    assert r["has_issues"] is False
    assert r["closed_issues_percentage"] is None


def test_linguagem_ignora_caixa_e_espacos():
    assert calculate("  typescript  ", 1, 1)["is_popular_language"] is True
    assert calculate("C#", 1, 1)["is_popular_language"] is True
    assert calculate("   ", 1, 1)["language_group"] == UNIDENTIFIED_LANGUAGE


def test_issues_negativas_falham():
    for open_issues, closed_issues in [(-1, 0), (0, -1)]:
        try:
            calculate("Go", open_issues, closed_issues)
        except ValueError:
            continue
        raise AssertionError("esperava ValueError para issues negativas")


def test_add_metrics_no_dataframe():
    df = pd.DataFrame(
        {
            "primary_language": ["Python", None, "Rust"],
            "open_issues": [20, 0, 0],
            "closed_issues": [80, 0, 10],
        }
    )

    resultado = add_metrics(df)

    assert list(resultado["language_group"]) == ["Python", UNIDENTIFIED_LANGUAGE, "Rust"]
    assert list(resultado["is_popular_language"]) == [True, False, False]
    assert list(resultado["total_issues"]) == [100, 0, 10]
    assert resultado["closed_issues_percentage"].iloc[0] == 80
    assert pd.isna(resultado["closed_issues_percentage"].iloc[1])
    assert resultado["closed_issues_percentage"].iloc[2] == 100


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

    for teste in testes:
        teste()
        print(f"OK   {teste.__name__}")

    print(f"\nRQ05/RQ06: {len(testes)} testes passaram.")
