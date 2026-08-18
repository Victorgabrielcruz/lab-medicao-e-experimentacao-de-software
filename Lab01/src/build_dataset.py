"""Monta o dataset processado com todas as métricas das RQ01 a RQ06.

Lê o CSV bruto mais recente de data/raw, aplica os módulos de métrica de cada
integrante e grava data/processed/repos_processed_<timestamp>.csv.

Este é o único arquivo que produz o dataset oficial. Os pilotos individuais em
data/processed/pilot_*.csv continuam servindo para conferência de cada dupla de
RQs, mas a análise da Sprint 3 e a RQ07 devem usar a saída daqui.

Uso:
    python src/build_dataset.py [caminho/do/csv]
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

sys.path.insert(0, str(ROOT / "src" / "metrics"))

import rq01_rq02_age_pullrequests as rq01_rq02  # noqa: E402
import rq03_rq04_releases_activity as rq03_rq04  # noqa: E402
import rq05_rq06_language_issues as rq05_rq06  # noqa: E402

DATE_COLUMNS = [
    "collected_at",
    "created_at",
    "pushed_at",
    "updated_at",
    "last_commit_date",
]

# Ordem das colunas no dataset final: identificação, dados brutos e, por
# último, as métricas derivadas agrupadas por RQ.
OUTPUT_COLUMNS = [
    "id",
    "name_with_owner",
    "url",
    "owner",
    "stargazer_count",
    "is_archived",
    "collected_at",
    # RQ01 e RQ02
    "created_at",
    "age_years",
    "merged_pull_requests",
    "total_pull_requests",
    "accepted_pull_requests",
    # RQ03 e RQ04
    "releases_count",
    "releases_no_teto",
    "updated_at",
    "pushed_at",
    "default_branch",
    "total_commits",
    "last_commit_date",
    "days_since_last_commit",
    "days_since_push",
    "development_period_days",
    # RQ05 e RQ06
    "primary_language",
    "language_group",
    "is_popular_language",
    "open_issues",
    "closed_issues",
    "total_issues",
    "has_issues",
    "closed_issues_percentage",
]


def latest_raw_csv() -> Path:
    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))

    if not files:
        raise SystemExit(f"Nenhum arquivo repos_raw_*.csv encontrado em {RAW_DIR}")

    return files[-1]


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    for column in DATE_COLUMNS:
        # CSV coletado antes de uma coluna existir: cria vazia em vez de falhar.
        serie = df[column] if column in df.columns else pd.Series(pd.NaT, index=df.index)
        df[column] = pd.to_datetime(serie, utc=True, errors="coerce")

    return df


def validate(df: pd.DataFrame) -> None:
    if df["id"].duplicated().any():
        duplicados = int(df["id"].duplicated().sum())
        raise SystemExit(f"{duplicados} repositorio(s) duplicado(s) no CSV bruto.")

    faltando = [c for c in OUTPUT_COLUMNS if c not in df.columns]

    if faltando:
        raise SystemExit(f"Colunas ausentes apos as metricas: {faltando}")


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else latest_raw_csv()
    print(f"Entrada: {source}")

    df = load(source)

    df = rq01_rq02.calculate_metrics(df)
    df = rq03_rq04.add_metrics(df)
    df = rq05_rq06.add_metrics(df)

    validate(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    output = PROCESSED_DIR / f"repos_processed_{carimbo}.csv"

    df[OUTPUT_COLUMNS].to_csv(output, index=False)

    print(f"Saída: {output}")
    print(f"Repositórios: {len(df)} | colunas: {len(OUTPUT_COLUMNS)}")
    print()
    print("Métricas por RQ:")
    print(f"  RQ01 idade mediana ................ {df['age_years'].median():.1f} anos")
    print(f"  RQ02 PRs aceitas mediana .......... {df['accepted_pull_requests'].median():.0f}")
    print(f"  RQ03 releases mediana ............. {df['releases_count'].median():.0f}")
    print(f"  RQ04 dias desde o push mediana .... {df['days_since_push'].median():.0f}")
    print(f"  RQ05 em linguagem popular ......... {int(df['is_popular_language'].sum())} de {len(df)}")
    print(f"  RQ06 issues fechadas mediana ...... {df['closed_issues_percentage'].median():.1f}%")


if __name__ == "__main__":
    main()
