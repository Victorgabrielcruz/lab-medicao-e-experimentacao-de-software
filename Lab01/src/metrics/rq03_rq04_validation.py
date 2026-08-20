"""Valida as métricas de releases e atividade (RQ03/RQ04).

Uso:
    python src/metrics/rq03_rq04_validation.py \
      data/raw/repos_raw_<coleta>.csv \
      data/processed/repos_processed_<coleta>.csv

O script compara a base processada com o CSV bruto, sem alterar nenhum dos dois.
Ele gera evidências de validação em data/processed/ e reports/drafts/.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from rq03_rq04_releases_activity import RELEASES_CAP


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"
DATE_COLUMNS = ["collected_at", "created_at", "pushed_at", "updated_at", "last_commit_date"]
CHECKED_COLUMNS = [
    "id", "name_with_owner", "releases_count", "releases_no_teto", "total_commits",
    "created_at", "last_commit_date", "pushed_at", "collected_at",
    "days_since_last_commit", "days_since_push", "development_period_days",
]
RAW_COMPARE_COLUMNS = [
    "id", "name_with_owner", "releases_count", "total_commits", "created_at",
    "last_commit_date", "pushed_at", "updated_at", "collected_at",
]
OUTLIER_COLUMNS = [
    "releases_count", "total_commits", "days_since_last_commit", "days_since_push",
    "development_period_days",
]


@dataclass
class ValidationResult:
    issues: pd.DataFrame
    outliers: pd.DataFrame
    repositories: int
    without_commits: int
    releases_at_cap: int

    @property
    def passed(self) -> bool:
        return self.issues.empty


def load(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Carrega CSV e converte as datas usadas nas validações para UTC."""
    df = pd.read_csv(path, dtype={"id": "string"})
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{path}: colunas ausentes: {', '.join(missing)}")

    for column in DATE_COLUMNS:
        df[column] = pd.to_datetime(df[column], utc=True, errors="coerce")
    return df


def _same(left: pd.Series, right: pd.Series) -> pd.Series:
    """Compara séries considerando dois valores ausentes como equivalentes."""
    both_missing = left.isna() & right.isna()
    both_present = left.notna() & right.notna()
    result = both_missing.copy()
    result.loc[both_present] = left.loc[both_present].eq(right.loc[both_present]).fillna(False)
    return result


def _format(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def _add_mismatches(
    issues: list[dict],
    merged: pd.DataFrame,
    field: str,
    expected: pd.Series,
    actual: pd.Series,
) -> None:
    mismatches = ~_same(expected, actual)
    for _, row in merged.loc[mismatches].iterrows():
        issues.append({
            "record_type": "inconsistency",
            "id": row["id"],
            "name_with_owner": row["name_with_owner"],
            "field": field,
            "expected": _format(expected.loc[row.name]),
            "actual": _format(actual.loc[row.name]),
            "detail": "valor processado diverge do valor bruto ou da fórmula definida",
        })


def _outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica outliers por IQR; eles são registrados, não removidos."""
    rows: list[dict] = []
    for column in OUTLIER_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(values) < 4:
            continue

        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[column] < lower) | (df[column] > upper)

        for _, row in df.loc[mask].iterrows():
            rows.append({
                "record_type": "outlier",
                "id": row["id"],
                "name_with_owner": row["name_with_owner"],
                "field": column,
                "expected": "",
                "actual": _format(row[column]),
                "detail": f"IQR: limite inferior {lower:.2f}; limite superior {upper:.2f}",
            })
    return pd.DataFrame(rows)


def validate(raw: pd.DataFrame, processed: pd.DataFrame) -> ValidationResult:
    """Valida preservação dos dados e fórmulas de RQ03/RQ04 por identificador."""
    raw = raw.copy()
    processed = processed.copy()
    for frame in [raw, processed]:
        for column in DATE_COLUMNS:
            frame[column] = pd.to_datetime(frame[column], utc=True, errors="coerce")

    issues: list[dict] = []

    if raw["id"].duplicated().any() or processed["id"].duplicated().any():
        raise ValueError("Há IDs duplicados na base bruta ou processada.")

    raw_ids = set(raw["id"])
    processed_ids = set(processed["id"])
    for repository_id in sorted(raw_ids - processed_ids):
        issues.append({
            "record_type": "inconsistency", "id": repository_id, "name_with_owner": "",
            "field": "id", "expected": "presente no processado", "actual": "ausente",
            "detail": "repositório do CSV bruto não chegou ao dataset processado",
        })
    for repository_id in sorted(processed_ids - raw_ids):
        issues.append({
            "record_type": "inconsistency", "id": repository_id, "name_with_owner": "",
            "field": "id", "expected": "presente no bruto", "actual": "ausente",
            "detail": "repositório processado não existe no CSV bruto",
        })

    merged = raw[RAW_COMPARE_COLUMNS].merge(processed, on="id", suffixes=("_raw", "_processed"), how="inner")
    merged = merged.rename(columns={"name_with_owner_raw": "name_with_owner"})

    # RQ03: contagem original de releases e marcação do teto da API.
    _add_mismatches(
        issues, merged, "releases_count", merged["releases_count_raw"], merged["releases_count_processed"]
    )
    _add_mismatches(
        issues,
        merged,
        "releases_no_teto",
        merged["releases_count_raw"] >= RELEASES_CAP,
        merged["releases_no_teto"],
    )

    # RQ04: created_at é o proxy documentado do primeiro commit.
    _add_mismatches(
        issues, merged, "created_at", merged["created_at_raw"], merged["created_at_processed"]
    )
    missing_created = merged["created_at_processed"].isna()
    for _, row in merged.loc[missing_created].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "created_at", "expected": "data de criação (proxy do primeiro commit)",
            "actual": "ausente", "detail": "não é possível calcular o período de desenvolvimento",
        })

    for column in ["last_commit_date", "total_commits"]:
        _add_mismatches(
            issues, merged, column, merged[f"{column}_raw"], merged[f"{column}_processed"]
        )

    expected_days_since_commit = (merged["collected_at_processed"] - merged["last_commit_date_processed"]).dt.days
    expected_days_since_push = (merged["collected_at_processed"] - merged["pushed_at_processed"]).dt.days
    expected_development = (merged["last_commit_date_processed"] - merged["created_at_processed"]).dt.days
    expected_development = expected_development.where(expected_development >= 0)

    _add_mismatches(
        issues, merged, "days_since_last_commit", expected_days_since_commit, merged["days_since_last_commit"]
    )
    _add_mismatches(issues, merged, "days_since_push", expected_days_since_push, merged["days_since_push"])
    _add_mismatches(
        issues, merged, "development_period_days", expected_development, merged["development_period_days"]
    )

    # Datas futuras não invalidam a coleta, mas são inconsistências que exigem revisão.
    for field in ["last_commit_date_processed", "pushed_at_processed"]:
        future = merged[field].notna() & (merged[field] > merged["collected_at_processed"])
        for _, row in merged.loc[future].iterrows():
            issues.append({
                "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
                "field": field.removesuffix("_processed"), "expected": "data <= collected_at",
                "actual": _format(row[field]), "detail": "data futura em relação à referência da coleta",
            })

    without_commits = int(merged["last_commit_date_processed"].isna().sum())
    releases_at_cap = int((merged["releases_count_raw"] >= RELEASES_CAP).sum())
    issue_frame = pd.DataFrame(issues)
    outlier_frame = _outliers(merged.rename(columns={
        "releases_count_raw": "releases_count",
        "total_commits_raw": "total_commits",
    }))
    return ValidationResult(issue_frame, outlier_frame, len(merged), without_commits, releases_at_cap)


def evidence_path(processed_path: Path, output_dir: Path = PROCESSED_DIR) -> Path:
    suffix = processed_path.stem.removeprefix("repos_processed_")
    return output_dir / f"validation_rq03_rq04_{suffix}.csv"


def report_path(processed_path: Path, output_dir: Path = REPORTS_DIR) -> Path:
    suffix = processed_path.stem.removeprefix("repos_processed_")
    return output_dir / f"validation_rq03_rq04_{suffix}.md"


def save_evidence(
    result: ValidationResult,
    processed_path: Path,
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> tuple[Path, Path]:
    """Registra inconsistências e outliers em CSV e um resumo em Markdown."""
    csv_path = evidence_path(processed_path, processed_dir)
    markdown_path = report_path(processed_path, reports_dir)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    evidence = pd.concat([result.issues, result.outliers], ignore_index=True)
    if evidence.empty:
        evidence = pd.DataFrame(columns=["record_type", "id", "name_with_owner", "field", "expected", "actual", "detail"])
    evidence.to_csv(csv_path, index=False)

    status = "APROVADA na amostra atual" if result.passed else "COM PENDÊNCIAS"
    markdown_path.write_text(
        "# Validação RQ03/RQ04\n\n"
        f"- Repositórios validados: **{result.repositories}**\n"
        f"- Status: **{status}**\n"
        f"- Inconsistências encontradas: **{len(result.issues)}**\n"
        f"- Outliers registrados (IQR): **{len(result.outliers)}**\n"
        f"- Repositórios sem último commit: **{result.without_commits}**\n"
        f"- Releases no teto da API ({RELEASES_CAP}): **{result.releases_at_cap}**\n\n"
        "## Regra do período de desenvolvimento\n\n"
        "A API não fornece o primeiro commit de forma viável para a coleta completa. "
        "Por isso, `created_at` é usado como proxy e a métrica é calculada como "
        "`last_commit_date - created_at`. Valores negativos ficam ausentes e são "
        "tratados como histórico importado ou inconsistente.\n\n"
        "Os outliers são evidências para revisão; eles não são removidos automaticamente.\n"
        "\nEsta execução não substitui a validação da coleta completa: a mesma rotina "
        "deve ser reexecutada quando houver 1.000 repositórios processados.\n",
        encoding="utf-8",
    )
    return csv_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida RQ03 e RQ04 contra os dados brutos.")
    parser.add_argument("raw", type=Path, help="CSV bruto da coleta")
    parser.add_argument("processed", type=Path, help="CSV processado pelo pipeline")
    args = parser.parse_args()

    result = validate(
        load(args.raw, RAW_COMPARE_COLUMNS),
        load(args.processed, CHECKED_COLUMNS),
    )
    evidence, report = save_evidence(result, args.processed)
    print(f"Repositórios validados: {result.repositories}")
    print(f"Inconsistências: {len(result.issues)}")
    print(f"Outliers registrados: {len(result.outliers)}")
    print(f"Sem último commit: {result.without_commits}")
    print(f"Evidências: {evidence}")
    print(f"Relatório: {report}")
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
