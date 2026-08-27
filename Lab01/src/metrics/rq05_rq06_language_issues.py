"""Implementação das métricas RQ05 e RQ06.

Porte de src/metrics/Rq05Rq06Processor.cs. Os valores calculados são os mesmos,
a única diferença é que a linguagem normalizada vai para a coluna
`language_group` em vez de sobrescrever `primary_language`, preservando o dado
bruto para auditoria.

Uso:
    python src/metrics/rq05_rq06_language_issues.py [caminho/do/csv]
"""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

UNIDENTIFIED_LANGUAGE = "Sem linguagem identificada"

# GitHub Octoverse 2025, ranking por contribuidores (agosto de 2025).
# Fonte única do laboratório para "linguagens mais populares", usada na RQ05 e
# na RQ07. Trocar esta lista muda o resultado das duas.
POPULAR_LANGUAGES = {
    "typescript",
    "python",
    "javascript",
    "java",
    "c#",
    "php",
    "shell",
    "c++",
    "hcl",
    "go",
}

PILOT_COLUMNS = [
    "name_with_owner",
    "primary_language",
    "language_group",
    "is_popular_language",
    "open_issues",
    "closed_issues",
    "total_issues",
    "has_issues",
    "closed_issues_percentage",
]


def normalize_language(primary_language) -> str:
    """Linguagem primária tratada. Vazio ou nulo vira categoria própria."""
    if primary_language is None or pd.isna(primary_language):
        return UNIDENTIFIED_LANGUAGE

    language = str(primary_language).strip()
    return language if language else UNIDENTIFIED_LANGUAGE


def is_popular_language(language: str) -> bool:
    """Verifica se a linguagem está entre as mais populares da fonte adotada."""
    if language == UNIDENTIFIED_LANGUAGE:
        return False

    return language.lower() in POPULAR_LANGUAGES


def closed_issues_percentage(open_issues: int, closed_issues: int):
    """Percentual de issues fechadas. Retorna None quando não há issues."""
    if open_issues < 0:
        raise ValueError(f"open_issues negativo: {open_issues}")

    if closed_issues < 0:
        raise ValueError(f"closed_issues negativo: {closed_issues}")

    total = open_issues + closed_issues

    if total == 0:
        return None

    return closed_issues / total * 100


def calculate(primary_language, open_issues: int, closed_issues: int) -> dict:
    """Calcula as métricas RQ05 e RQ06 de um repositório."""
    language = normalize_language(primary_language)
    total = open_issues + closed_issues

    return {
        "language_group": language,
        "is_popular_language": is_popular_language(language),
        "total_issues": total,
        "has_issues": total > 0,
        "closed_issues_percentage": closed_issues_percentage(open_issues, closed_issues),
    }


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas das RQ05 e RQ06 ao dataset."""
    if (df["open_issues"] < 0).any() or (df["closed_issues"] < 0).any():
        raise ValueError("Existe repositório com quantidade negativa de issues.")

    df["language_group"] = df["primary_language"].map(normalize_language)
    df["is_popular_language"] = df["language_group"].map(is_popular_language)
    df["total_issues"] = df["open_issues"] + df["closed_issues"]
    df["has_issues"] = df["total_issues"] > 0

    # Sem issues fica vazio, nunca zero: ausência não é o mesmo que nada fechado.
    df["closed_issues_percentage"] = (
        df["closed_issues"] / df["total_issues"] * 100
    ).where(df["has_issues"])

    return df


def latest_raw_csv() -> Path:
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))

    if not files:
        raise FileNotFoundError(f"Nenhum arquivo repos_raw_*.csv encontrado em {RAW_DIR}")

    return files[-1]


def summarize(df: pd.DataFrame) -> str:
    populares = int(df["is_popular_language"].sum())
    sem_issues = int((~df["has_issues"]).sum())
    percentuais = df["closed_issues_percentage"].dropna()

    linhas = [
        f"repositorios .................. {len(df)}",
        f"sem linguagem identificada .... {int((df['language_group'] == UNIDENTIFIED_LANGUAGE).sum())}",
        "",
        "RQ05 - linguagem primaria",
        f"  em linguagem popular         {populares} ({populares / len(df):.1%})",
        "  top 5 linguagens:",
    ]

    for linguagem, quantidade in df["language_group"].value_counts().head(5).items():
        linhas.append(f"    {linguagem:<28} {quantidade}")

    linhas += [
        "",
        "RQ06 - issues fechadas",
        f"  sem issues                   {sem_issues}",
        f"  percentual fechadas          mediana {percentuais.median():.1f} "
        f"| media {percentuais.mean():.1f}",
    ]

    return "\n".join(linhas)


def save_pilot(df: pd.DataFrame, output: Path) -> Path:
    """Exporta a visão específica de RQ05/RQ06 a partir de métricas já calculadas."""
    output.parent.mkdir(parents=True, exist_ok=True)
    df[PILOT_COLUMNS].to_csv(output, index=False)
    return output


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_raw_csv()
    print(f"Entrada: {source}\n")

    df = add_metrics(pd.read_csv(source))
    print(summarize(df))

    output = PROCESSED_DIR / "pilot_rq05_rq06.csv"
    save_pilot(df, output)
    print(f"\nSaída: {output}")


if __name__ == "__main__":
    main()
