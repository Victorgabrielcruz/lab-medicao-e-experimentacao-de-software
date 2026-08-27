"""Consolida a base processada (RQ01-06) para a análise integrada da RQ07.

Uso:
    python src/analysis/consolidate_rq07_dataset.py data/processed/repos_processed_<coleta>.csv

Sem argumento, usa o CSV processado (RQ01-06) mais recente em data/processed/.

Este script não recalcula nenhuma métrica: ele apenas confere que a base já
gerada por `build_processed_dataset.py` está íntegra (uma linha por
repositório, sem duplicidade, com todas as colunas de RQ01-06) e grava um
artefato explícito, pronto para ser consumido por `rq07_analysis.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"

# Colunas mínimas exigidas para a análise integrada da RQ07 (RQ01-06).
REQUIRED_COLUMNS = [
    "id", "name_with_owner", "primary_language",
    "age_years", "accepted_pull_requests",
    "releases_count", "releases_no_teto",
    "days_since_last_commit", "days_since_push", "development_period_days",
    "language_group", "is_popular_language",
    "total_issues", "has_issues", "closed_issues_percentage",
]

# Colunas em que valores ausentes são esperados e documentados (não são erro).
MISSING_VALUE_COLUMNS = [
    "days_since_last_commit", "days_since_push", "development_period_days",
    "closed_issues_percentage",
]


@dataclass
class ConsolidationResult:
    repositories: int
    duplicated_ids: list[str]
    missing_columns: list[str]
    missing_value_counts: dict[str, int]
    without_language: int
    without_issues: int

    @property
    def passed(self) -> bool:
        return not self.duplicated_ids and not self.missing_columns


def latest_processed_csv() -> Path:
    """Retorna o CSV processado (RQ01-06) mais recente, ignorando pilotos e evidências."""
    candidates = sorted(PROCESSED_DIR.glob("repos_processed_*.csv"))
    if not candidates:
        raise FileNotFoundError(f"Nenhum CSV processado encontrado em {PROCESSED_DIR}.")
    return candidates[-1]


def load(path: Path) -> pd.DataFrame:
    """Carrega o CSV processado, preservando o identificador como texto."""
    return pd.read_csv(path, dtype={"id": "string"})


def consolidate(df: pd.DataFrame) -> ConsolidationResult:
    """Verifica que a base processada está íntegra e pronta para a análise da RQ07."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    duplicated_ids: list[str] = []
    if "id" in df.columns:
        duplicated_ids = sorted(df.loc[df["id"].duplicated(keep=False), "id"].dropna().unique().tolist())

    missing_value_counts = {
        column: int(df[column].isna().sum())
        for column in MISSING_VALUE_COLUMNS
        if column in df.columns
    }

    without_language = (
        int((df["language_group"] == "Sem linguagem identificada").sum())
        if "language_group" in df.columns else 0
    )
    without_issues = (
        int((~df["has_issues"].astype(bool)).sum())
        if "has_issues" in df.columns else 0
    )

    return ConsolidationResult(
        repositories=len(df),
        duplicated_ids=duplicated_ids,
        missing_columns=missing_columns,
        missing_value_counts=missing_value_counts,
        without_language=without_language,
        without_issues=without_issues,
    )


def output_for(source: Path) -> Path:
    """Gera um nome de saída determinístico a partir do CSV processado de origem."""
    suffix = source.stem.removeprefix("repos_processed_")
    return PROCESSED_DIR / f"repos_rq07_consolidated_{suffix}.csv"


def save_consolidated(df: pd.DataFrame, output: Path) -> Path:
    """Grava a base consolidada, artefato oficial de entrada para a análise da RQ07."""
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return output


def save_report(result: ConsolidationResult, source: Path, output: Path) -> Path:
    """Grava o relatório de consolidação em Markdown, em reports/drafts/."""
    suffix = source.stem.removeprefix("repos_processed_")
    report_path = REPORTS_DIR / f"consolidation_rq07_{suffix}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    status = "PRONTA para a análise da RQ07" if result.passed else "COM PENDÊNCIAS — corrigir antes da RQ07"
    lines = [
        "# Consolidação do dataset para a RQ07\n\n",
        f"- Base processada de origem: `{source.name}`\n",
        f"- Base consolidada gerada: `{output.name}`\n",
        f"- Repositórios: **{result.repositories}**\n",
        f"- Status: **{status}**\n",
        f"- IDs duplicados: **{len(result.duplicated_ids)}**\n",
        "- Colunas obrigatórias ausentes: **{}**{}\n".format(
            len(result.missing_columns),
            f" ({', '.join(result.missing_columns)})" if result.missing_columns else "",
        ),
        f"- Repositórios sem linguagem primária: **{result.without_language}**\n",
        f"- Repositórios sem issues: **{result.without_issues}**\n\n",
        "## Valores ausentes por coluna (esperados, documentados)\n\n",
    ]
    for column, count in result.missing_value_counts.items():
        lines.append(f"- `{column}`: {count}\n")
    lines.append(
        "\nOs valores ausentes acima são esperados e documentados em "
        "`docs/dataset/raw-dataset.md` e `docs/methodology.md`: repositórios sem "
        "commit/push não têm métricas temporais de atividade e repositórios "
        "sem issues não têm `closed_issues_percentage`. Nenhum valor ausente "
        "foi convertido em zero.\n\n"
        "Este dataset reaproveita as métricas já validadas em "
        "`docs/validation/rq01-rq02-validation.md`, `docs/validation/rq03-rq04-validation.md` e "
        "`docs/validation/rq05-rq06-validation.md`, sem recalcular nenhuma regra de "
        "métrica.\n"
    )
    report_path.write_text("".join(lines), encoding="utf-8")
    return report_path


def run(source: Path) -> tuple[ConsolidationResult, Path, Path]:
    """Executa a consolidação fim a fim e retorna o resultado e os artefatos gerados."""
    df = load(source)
    result = consolidate(df)
    if result.missing_columns:
        raise ValueError(f"Colunas obrigatórias ausentes na base processada: {', '.join(result.missing_columns)}")
    if result.duplicated_ids:
        raise ValueError(f"IDs duplicados na base processada: {', '.join(result.duplicated_ids[:10])}")

    output = save_consolidated(df, output_for(source))
    report = save_report(result, source, output)
    return result, output, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolida a base processada (RQ01-06) para a análise da RQ07."
    )
    parser.add_argument("source", nargs="?", type=Path, help="CSV processado (RQ01-06)")
    args = parser.parse_args()

    source = args.source or latest_processed_csv()
    result, output, report = run(source)

    print(f"Repositórios consolidados: {result.repositories}")
    print(f"IDs duplicados: {len(result.duplicated_ids)}")
    print(f"Sem linguagem: {result.without_language}")
    print(f"Sem issues: {result.without_issues}")
    print(f"Dataset consolidado: {output}")
    print(f"Relatório: {report}")


if __name__ == "__main__":
    main()
