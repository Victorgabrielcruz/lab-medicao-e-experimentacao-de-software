"""Implementação das métricas RQ01 e RQ02."""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def latest_raw_csv() -> Path:
    """Retorna o CSV bruto mais recente."""
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo repos_raw_*.csv encontrado em {RAW_DIR}"
        )

    return files[-1]


def load_data(path: Path) -> pd.DataFrame:
    """Carrega o dataset bruto."""
    df = pd.read_csv(path)

    df["created_at"] = pd.to_datetime(
        df["created_at"],
        utc=True,
        errors="coerce",
    )

    df["collected_at"] = pd.to_datetime(
        df["collected_at"],
        utc=True,
        errors="coerce",
    )

    return df


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as métricas RQ01 e RQ02."""

    # RQ01 - idade do repositório em anos
    df["age_years"] = (
        (df["collected_at"] - df["created_at"])
        .dt.total_seconds()
        / (365.25 * 24 * 60 * 60)
    )

    # RQ02 - quantidade de Pull Requests aceitas
    # A API já fornece somente PRs com estado MERGED.
    df["accepted_pull_requests"] = df["merged_pull_requests"]

    return df


def validate_data(df: pd.DataFrame) -> None:
    """Valida os resultados das métricas."""

    if df["created_at"].isna().any():
        raise ValueError("Existem registros com created_at inválido.")

    if df["collected_at"].isna().any():
        raise ValueError("Existem registros com collected_at inválido.")

    if (df["age_years"] < 0).any():
        raise ValueError("Existe repositório com idade negativa.")

    if (df["accepted_pull_requests"] < 0).any():
        raise ValueError(
            "Existe repositório com quantidade negativa de Pull Requests."
        )


def save_metrics(df: pd.DataFrame) -> Path:
    """Salva as métricas calculadas."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output = PROCESSED_DIR / "pilot_rq01_rq02.csv"

    columns = [
        "name_with_owner",
        "created_at",
        "collected_at",
        "age_years",
        "accepted_pull_requests",
    ]

    df[columns].to_csv(output, index=False)

    return output


def main() -> None:
    """Executa o pipeline das métricas RQ01 e RQ02."""

    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = latest_raw_csv()

    print(f"Entrada: {input_file}")

    df = load_data(input_file)
    df = add_metrics(df)

    validate_data(df)

    output = save_metrics(df)

    print(f"Saída: {output}")
    print(f"Registros processados: {len(df)}")


if __name__ == "__main__":
    main()
