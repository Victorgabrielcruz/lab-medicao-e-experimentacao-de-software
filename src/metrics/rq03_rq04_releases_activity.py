"""RQ03 (releases) e RQ04 (atividade) - Integrante B.

Uso:
    python src/metrics/rq03_rq04_releases_activity.py [caminho/do/csv]

Sem argumento, usa o CSV mais recente de data/raw/.
"""

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

DATE_COLUMNS = [
    "collected_at",
    "created_at",
    "pushed_at",
    "updated_at",
    "first_commit_date",
    "last_commit_date",
]


def latest_raw_csv() -> Path:
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))
    if not files:
        raise FileNotFoundError(f"nenhum repos_raw_*.csv em {RAW_DIR}. Rode o coletor antes.")
    return files[-1]


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for column in DATE_COLUMNS:
        # CSV coletado antes de first_commit_date existir: cria a coluna vazia.
        serie = df[column] if column in df.columns else pd.Series(pd.NaT, index=df.index)
        df[column] = pd.to_datetime(serie, utc=True, errors="coerce")
    return df


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    reference = df["collected_at"]

    df["days_since_last_commit"] = (reference - df["last_commit_date"]).dt.days
    df["days_since_push"] = (reference - df["pushed_at"]).dt.days

    # first_commit_date pode nao ter sido coletado; created_at e a aproximacao.
    start = df["first_commit_date"].fillna(df["created_at"])
    df["development_start"] = start
    df["development_start_source"] = df["first_commit_date"].notna().map(
        {True: "first_commit", False: "created_at"}
    )
    df["development_period_days"] = (df["last_commit_date"] - start).dt.days

    # Historico importado de outro sistema: primeiro commit anterior a criacao do repo.
    df["development_period_days"] = df["development_period_days"].where(
        df["development_period_days"] >= 0
    )

    return df


def summarize(df: pd.DataFrame) -> str:
    total = len(df)
    sem_commits = int(df["last_commit_date"].isna().sum())
    fonte = df["development_start_source"].value_counts().to_dict()

    def stats(column: str) -> str:
        serie = df[column].dropna()
        if serie.empty:
            return f"{column:<28} sem dados"
        return (
            f"{column:<28} mediana {serie.median():>10.1f} "
            f"| media {serie.mean():>10.1f} | min {serie.min():>8.0f} | max {serie.max():>9.0f}"
        )

    linhas = [
        f"repositorios .................. {total}",
        f"sem commits (branch ausente) .. {sem_commits}",
        f"origem do inicio do periodo ... {fonte}",
        "",
        "RQ03 - releases",
        "  " + stats("releases_count"),
        f"  {'repositorios com 0 releases':<28} "
        f"{int((df['releases_count'] == 0).sum())} ({(df['releases_count'] == 0).mean():.1%})",
        "",
        "RQ04 - atividade",
        "  " + stats("days_since_last_commit"),
        "  " + stats("days_since_push"),
        "  " + stats("development_period_days"),
        "  " + stats("total_commits"),
    ]
    return "\n".join(linhas)


OUTPUT_COLUMNS = [
    "name_with_owner",
    "releases_count",
    "total_commits",
    "first_commit_date",
    "last_commit_date",
    "development_start",
    "development_start_source",
    "days_since_last_commit",
    "days_since_push",
    "development_period_days",
]


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_raw_csv()
    print(f"entrada: {source}\n")

    df = add_metrics(load(source))
    print(summarize(df))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "pilot_rq03_rq04.csv"
    df[OUTPUT_COLUMNS].to_csv(output, index=False)
    print(f"\nsaida: {output}")


if __name__ == "__main__":
    main()
