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

# A API trunca releases.totalCount neste valor; acima disso o numero real e desconhecido.
RELEASES_CAP = 1000

DATE_COLUMNS = ["collected_at", "created_at", "pushed_at", "updated_at", "last_commit_date"]

OUTPUT_COLUMNS = [
    "name_with_owner",
    "releases_count",
    "releases_no_teto",
    "total_commits",
    "created_at",
    "last_commit_date",
    "days_since_last_commit",
    "days_since_push",
    "development_period_days",
]


def latest_raw_csv() -> Path:
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))
    if not files:
        raise FileNotFoundError(f"nenhum repos_raw_*.csv em {RAW_DIR}. Rode o coletor antes.")
    return files[-1]


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for column in DATE_COLUMNS:
        df[column] = pd.to_datetime(df[column], utc=True, errors="coerce")
    return df


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    reference = df["collected_at"]

    df["releases_no_teto"] = df["releases_count"] >= RELEASES_CAP

    df["days_since_last_commit"] = (reference - df["last_commit_date"]).dt.days
    df["days_since_push"] = (reference - df["pushed_at"]).dt.days

    # A API nao entrega o primeiro commit; created_at aproxima o inicio do desenvolvimento.
    df["development_period_days"] = (df["last_commit_date"] - df["created_at"]).dt.days

    # Historico importado e abandonado: ultimo commit anterior a criacao do repositorio.
    df["development_period_days"] = df["development_period_days"].where(
        df["development_period_days"] >= 0
    )

    return df


def summarize(df: pd.DataFrame) -> str:
    def stats(column: str) -> str:
        serie = df[column].dropna()
        if serie.empty:
            return f"{column:<28} sem dados"
        return (
            f"{column:<28} mediana {serie.median():>10.1f} "
            f"| media {serie.mean():>10.1f} | min {serie.min():>8.0f} | max {serie.max():>9.0f}"
        )

    zeradas = int((df["releases_count"] == 0).sum())
    no_teto = int(df["releases_no_teto"].sum())

    return "\n".join([
        f"repositorios .................. {len(df)}",
        f"sem commits (branch ausente) .. {int(df['last_commit_date'].isna().sum())}",
        "",
        "RQ03 - releases",
        "  " + stats("releases_count"),
        f"  {'repositorios com 0 releases':<28} {zeradas} ({zeradas / len(df):.1%})",
        f"  {'no teto de ' + str(RELEASES_CAP):<28} {no_teto}"
        + ("  <- media e maximo subestimados; use a mediana" if no_teto else ""),
        "",
        "RQ04 - atividade",
        "  " + stats("days_since_last_commit"),
        "  " + stats("days_since_push"),
        "  " + stats("development_period_days"),
        "  " + stats("total_commits"),
    ])


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
