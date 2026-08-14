"""Análise das métricas RQ01 e RQ02."""

from pathlib import Path
import sys

import pandas as pd

from src.metrics.rq01_rq02_age_pullrequests import (
    calculate_metrics,
    load_data,
)


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"


def latest_raw_csv() -> Path:
    """Retorna o dataset bruto mais recente."""

    files = sorted(RAW_DIR.glob("repos_raw_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"Nenhum arquivo repos_raw_*.csv encontrado em {RAW_DIR}"
        )

    return files[-1]


def analyze_rq01(df: pd.DataFrame) -> None:
    """Exibe a análise da RQ01."""

    age = df["age_years"]

    print("\n" + "=" * 60)
    print("RQ01 — Sistemas populares são maduros/antigos?")
    print("=" * 60)

    print(f"Repositórios analisados: {len(df)}")
    print(f"Média: {age.mean():.2f} anos")
    print(f"Mediana: {age.median():.2f} anos")
    print(f"1º quartil: {age.quantile(0.25):.2f} anos")
    print(f"3º quartil: {age.quantile(0.75):.2f} anos")
    print(f"Mínimo: {age.min():.2f} anos")
    print(f"Máximo: {age.max():.2f} anos")
    print(f"Desvio padrão: {age.std():.2f} anos")

    print("\nDistribuição por faixa:")

    ranges = {
        "Até 2 anos": (age <= 2).sum(),
        "Mais de 2 até 5 anos": ((age > 2) & (age <= 5)).sum(),
        "Mais de 5 até 10 anos": ((age > 5) & (age <= 10)).sum(),
        "Mais de 10 anos": (age > 10).sum(),
    }

    for label, count in ranges.items():
        percentage = count / len(df) * 100
        print(f"  {label}: {count} ({percentage:.1f}%)")


def analyze_rq02(df: pd.DataFrame) -> None:
    """Exibe a análise da RQ02."""

    prs = df["accepted_pull_requests"]

    print("\n" + "=" * 60)
    print("RQ02 — Sistemas populares recebem muita contribuição externa?")
    print("=" * 60)

    print(f"Repositórios analisados: {len(df)}")
    print(f"Média: {prs.mean():.2f} PRs")
    print(f"Mediana: {prs.median():.2f} PRs")
    print(f"1º quartil: {prs.quantile(0.25):.2f} PRs")
    print(f"3º quartil: {prs.quantile(0.75):.2f} PRs")
    print(f"Mínimo: {prs.min():.0f} PRs")
    print(f"Máximo: {prs.max():.0f} PRs")
    print(f"Desvio padrão: {prs.std():.2f} PRs")

    zero_prs = (prs == 0).sum()
    zero_percentage = zero_prs / len(df) * 100

    print("\nRepositórios sem Pull Requests aceitas:")
    print(f"  Quantidade: {zero_prs}")
    print(f"  Percentual: {zero_percentage:.1f}%")

    print("\nDistribuição por faixa:")

    ranges = {
        "0 PRs": (prs == 0).sum(),
        "1–99 PRs": ((prs >= 1) & (prs < 100)).sum(),
        "100–999 PRs": ((prs >= 100) & (prs < 1000)).sum(),
        "1.000–9.999 PRs": ((prs >= 1000) & (prs < 10000)).sum(),
        "10.000+ PRs": (prs >= 10000).sum(),
    }

    for label, count in ranges.items():
        percentage = count / len(df) * 100
        print(f"  {label}: {count} ({percentage:.1f}%)")


def main() -> None:
    """Executa a análise das RQ01 e RQ02."""

    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    else:
        input_file = latest_raw_csv()

    print(f"Dataset: {input_file}")

    df = load_data(input_file)
    df = calculate_metrics(df)

    analyze_rq01(df)
    analyze_rq02(df)

    print("\n" + "=" * 60)
    print("Análise concluída.")
    print("=" * 60)


if __name__ == "__main__":
    main()