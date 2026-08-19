"""Transforma um CSV bruto do coletor em uma base única para as RQs 01–06.

Uso:
    python src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv

Sem argumento, processa o CSV bruto mais recente em data/raw/.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
RELEASES_CAP = 1000
UNIDENTIFIED_LANGUAGE = "Sem linguagem identificada"
POPULAR_LANGUAGES = {
    "TypeScript", "Python", "JavaScript", "Java", "C#",
    "PHP", "Shell", "C++", "HCL", "Go",
}

RAW_COLUMNS = [
    "id", "name_with_owner", "url", "owner", "stargazer_count", "is_archived",
    "collected_at", "created_at", "merged_pull_requests", "total_pull_requests",
    "releases_count", "updated_at", "pushed_at", "default_branch", "total_commits",
    "last_commit_date", "primary_language", "open_issues", "closed_issues",
]
REQUIRED_DATES = ["collected_at", "created_at"]
OPTIONAL_DATES = ["updated_at", "pushed_at", "last_commit_date"]
REQUIRED_NUMBERS = [
    "stargazer_count", "merged_pull_requests", "total_pull_requests", "releases_count",
    "open_issues", "closed_issues",
]
OPTIONAL_NUMBERS = ["total_commits"]
DERIVED_COLUMNS = [
    "age_years", "accepted_pull_requests", "releases_no_teto",
    "days_since_last_commit", "days_since_push", "development_period_days",
    "is_popular_language", "total_issues", "has_issues", "closed_issues_percentage",
]


def latest_raw_csv() -> Path:
    """Retorna o CSV bruto mais recente, sem considerar os JSONs por página."""
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV bruto encontrado em {RAW_DIR}.")
    return files[-1]


def output_for(source: Path) -> Path:
    """Gera um nome de saída determinístico a partir do arquivo de entrada."""
    name = source.name.replace("repos_raw_", "repos_processed_", 1)
    return PROCESSED_DIR / name


def _raise_invalid(column: str, mask: pd.Series, reason: str) -> None:
    if mask.any():
        examples = ", ".join(mask[mask].index.astype(str).tolist()[:5])
        raise ValueError(f"{column}: {reason}. Linhas: {examples}")


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos, datas, valores ausentes e duplicidades do CSV bruto."""
    missing_columns = [column for column in RAW_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")

    df = df[RAW_COLUMNS].copy()
    _raise_invalid("id", df["id"].isna() | df["id"].astype(str).str.strip().eq(""), "identificador ausente")

    duplicates = df.duplicated(subset="id", keep="first")
    if duplicates.any():
        print(f"Aviso: {int(duplicates.sum())} registro(s) duplicado(s) removido(s) por id.")
        df = df.loc[~duplicates].copy()

    for column in REQUIRED_DATES + OPTIONAL_DATES:
        original = df[column]
        parsed = pd.to_datetime(original, utc=True, errors="coerce")
        invalid = original.notna() & original.astype(str).str.strip().ne("") & parsed.isna()
        _raise_invalid(column, invalid, "data inválida")
        if column in REQUIRED_DATES:
            _raise_invalid(column, parsed.isna(), "data obrigatória ausente")
        df[column] = parsed

    for column in REQUIRED_NUMBERS + OPTIONAL_NUMBERS:
        original = df[column]
        parsed = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & original.astype(str).str.strip().ne("") & parsed.isna()
        _raise_invalid(column, invalid, "valor numérico inválido")
        if column in REQUIRED_NUMBERS:
            _raise_invalid(column, parsed.isna(), "valor obrigatório ausente")
        _raise_invalid(column, parsed.dropna() < 0, "valor negativo")
        df[column] = parsed.astype("Int64")

    normalized_boolean = (
        df["is_archived"].astype(str).str.strip().str.lower().map({"true": True, "false": False})
    )
    _raise_invalid("is_archived", normalized_boolean.isna(), "booleano inválido")
    df["is_archived"] = normalized_boolean.astype(bool)

    df["primary_language"] = df["primary_language"].fillna("").astype(str).str.strip()
    df.loc[df["primary_language"].eq(""), "primary_language"] = UNIDENTIFIED_LANGUAGE
    return df


def calculate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as métricas derivadas das RQs 01–06 ao dataset normalizado."""
    df = df.copy()

    # RQ01 e RQ02
    df["age_years"] = (df["collected_at"] - df["created_at"]).dt.total_seconds() / 31_557_600
    _raise_invalid("age_years", df["age_years"] < 0, "idade negativa")
    df["accepted_pull_requests"] = df["merged_pull_requests"]

    # RQ03 e RQ04
    df["releases_no_teto"] = df["releases_count"] >= RELEASES_CAP
    df["days_since_last_commit"] = (df["collected_at"] - df["last_commit_date"]).dt.days.astype("Int64")
    df["days_since_push"] = (df["collected_at"] - df["pushed_at"]).dt.days.astype("Int64")
    df["development_period_days"] = (df["last_commit_date"] - df["created_at"]).dt.days.astype("Int64")
    df.loc[df["development_period_days"] < 0, "development_period_days"] = pd.NA

    # RQ05 e RQ06
    df["is_popular_language"] = df["primary_language"].isin(POPULAR_LANGUAGES)
    df["total_issues"] = df["open_issues"] + df["closed_issues"]
    df["has_issues"] = df["total_issues"] > 0
    df["closed_issues_percentage"] = pd.Series(pd.NA, index=df.index, dtype="Float64")
    has_issues = df["has_issues"]
    df.loc[has_issues, "closed_issues_percentage"] = (
        df.loc[has_issues, "closed_issues"] / df.loc[has_issues, "total_issues"] * 100
    )

    _raise_invalid(
        "closed_issues_percentage",
        df["closed_issues_percentage"].notna()
        & ~df["closed_issues_percentage"].between(0, 100),
        "percentual fora do intervalo de 0 a 100",
    )
    return df


def save(df: pd.DataFrame, output: Path) -> Path:
    """Salva a base processada com datas UTC e ordem de colunas documentada."""
    output.parent.mkdir(parents=True, exist_ok=True)
    result = df[RAW_COLUMNS + DERIVED_COLUMNS].copy()
    for column in REQUIRED_DATES + OPTIONAL_DATES:
        result[column] = result[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    result.to_csv(output, index=False, float_format="%.6f")
    return output


def build(source: Path, output: Path | None = None) -> Path:
    """Executa o pipeline completo e retorna o caminho do CSV processado."""
    destination = output or output_for(source)
    df = normalize(pd.read_csv(source, dtype={"id": "string"}))
    df = calculate_metrics(df)
    return save(df, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera a base processada das RQs 01–06.")
    parser.add_argument("source", nargs="?", type=Path, help="CSV bruto do coletor")
    parser.add_argument("--output", type=Path, help="Caminho do CSV processado")
    args = parser.parse_args()

    source = args.source or latest_raw_csv()
    output = build(source, args.output)
    print(f"Entrada: {source}")
    print(f"Saída: {output}")
    print(f"Registros processados: {len(pd.read_csv(output))}")


if __name__ == "__main__":
    main()
