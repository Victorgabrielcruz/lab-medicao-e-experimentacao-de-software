"""Valida as métricas de idade e Pull Requests aceitas (RQ01/RQ02).

Uso:
    python src/metrics/rq01_rq02_validation.py \
      data/raw/repos_raw_<coleta>.csv \
      data/processed/repos_processed_<coleta>.csv

O script compara a base processada com o CSV bruto, sem alterar nenhum dos dois.
Ele gera evidências de validação em data/processed/ e reports/drafts/, seguindo o
mesmo formato usado pela validação de RQ03/RQ04 (src/metrics/rq03_rq04_validation.py).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"

# GitHub foi fundado em 2008-04-10; nenhum repositório pode ter sido criado antes disso.
GITHUB_FOUNDED_AT = pd.Timestamp("2008-04-10T00:00:00Z")

# Tolerância de ponto flutuante para reproduzir a fórmula de age_years.
AGE_YEARS_TOLERANCE = 1e-6

DATE_COLUMNS = ["collected_at", "created_at"]
CHECKED_COLUMNS = [
    "id", "name_with_owner", "created_at", "collected_at", "age_years",
    "accepted_pull_requests", "merged_pull_requests", "total_pull_requests",
]
RAW_COMPARE_COLUMNS = [
    "id", "name_with_owner", "created_at", "collected_at",
    "merged_pull_requests", "total_pull_requests",
]
OUTLIER_COLUMNS = ["age_years", "accepted_pull_requests"]

# Amostra fixa para conferência manual, reproduzível entre execuções.
MANUAL_SAMPLE_SIZE = 10
MANUAL_SAMPLE_SEED = 42


@dataclass
class ValidationResult:
    issues: pd.DataFrame
    outliers: pd.DataFrame
    manual_sample: pd.DataFrame
    repositories: int

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


def _same(left: pd.Series, right: pd.Series, tolerance: float = 0.0) -> pd.Series:
    """Compara séries considerando dois valores ausentes como equivalentes."""
    both_missing = left.isna() & right.isna()
    both_present = left.notna() & right.notna()
    result = both_missing.copy()
    if tolerance:
        close = (left.loc[both_present] - right.loc[both_present]).abs() <= tolerance
        result.loc[both_present] = close.fillna(False)
    else:
        result.loc[both_present] = left.loc[both_present].eq(right.loc[both_present]).fillna(False)
    return result


def _format(value) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def _add_mismatches(
    issues: list[dict],
    merged: pd.DataFrame,
    field: str,
    expected: pd.Series,
    actual: pd.Series,
    tolerance: float = 0.0,
    detail: str = "valor processado diverge do valor bruto ou da fórmula definida",
) -> None:
    mismatches = ~_same(expected, actual, tolerance)
    for _, row in merged.loc[mismatches].iterrows():
        issues.append({
            "record_type": "inconsistency",
            "id": row["id"],
            "name_with_owner": row["name_with_owner"],
            "field": field,
            "expected": _format(expected.loc[row.name]),
            "actual": _format(actual.loc[row.name]),
            "detail": detail,
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


def _manual_sample(merged: pd.DataFrame) -> pd.DataFrame:
    """Seleciona uma amostra fixa e reproduzível para conferência manual."""
    size = min(MANUAL_SAMPLE_SIZE, len(merged))
    if size == 0:
        return merged.iloc[0:0][
            ["id", "name_with_owner", "created_at_processed", "collected_at_processed",
             "age_years", "merged_pull_requests_raw", "total_pull_requests_raw",
             "accepted_pull_requests"]
        ]
    sample = merged.sample(n=size, random_state=MANUAL_SAMPLE_SEED).sort_values("id")
    return sample[
        ["id", "name_with_owner", "created_at_processed", "collected_at_processed",
         "age_years", "merged_pull_requests_raw", "total_pull_requests_raw",
         "accepted_pull_requests"]
    ]


def validate(raw: pd.DataFrame, processed: pd.DataFrame) -> ValidationResult:
    """Valida completude, faixa de valores e fórmulas de RQ01/RQ02 por identificador."""
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

    # Completude: created_at, collected_at, age_years e accepted_pull_requests obrigatórios.
    for field in ["created_at_processed", "collected_at_processed", "age_years", "accepted_pull_requests"]:
        missing = merged[field].isna()
        for _, row in merged.loc[missing].iterrows():
            issues.append({
                "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
                "field": field.removesuffix("_processed"), "expected": "valor presente",
                "actual": "ausente", "detail": "campo obrigatório de RQ01/RQ02 ausente na base processada",
            })

    # created_at preservado entre bruto e processado.
    _add_mismatches(
        issues, merged, "created_at", merged["created_at_raw"], merged["created_at_processed"]
    )

    # RQ01: faixa de valores da idade. Idade negativa ou anterior à fundação do GitHub é inválida.
    negative_age = merged["age_years"].notna() & (merged["age_years"] < 0)
    for _, row in merged.loc[negative_age].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "age_years", "expected": ">= 0", "actual": _format(row["age_years"]),
            "detail": "idade negativa: created_at posterior a collected_at",
        })

    created_before_github = merged["created_at_processed"].notna() & (
        merged["created_at_processed"] < GITHUB_FOUNDED_AT
    )
    for _, row in merged.loc[created_before_github].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "created_at", "expected": f">= {GITHUB_FOUNDED_AT.date()}",
            "actual": _format(row["created_at_processed"]),
            "detail": "data de criação anterior à fundação do GitHub",
        })

    # RQ01: reproduz a fórmula de age_years a partir das datas brutas (conferência de amostra).
    expected_age_years = (
        (merged["collected_at_processed"] - merged["created_at_raw"]).dt.total_seconds()
        / (365.25 * 24 * 60 * 60)
    )
    _add_mismatches(
        issues, merged, "age_years", expected_age_years, merged["age_years"],
        tolerance=AGE_YEARS_TOLERANCE,
        detail="age_years não corresponde a (collected_at - created_at) em anos",
    )

    # RQ02: PRs aceitas devem ser exatamente as PRs MERGED e nunca superar o total de PRs.
    _add_mismatches(
        issues, merged, "accepted_pull_requests",
        merged["merged_pull_requests_raw"], merged["accepted_pull_requests"],
        detail="accepted_pull_requests diverge de merged_pull_requests (estado MERGED)",
    )

    exceeds_total = (
        merged["accepted_pull_requests"].notna()
        & merged["total_pull_requests_raw"].notna()
        & (merged["accepted_pull_requests"] > merged["total_pull_requests_raw"])
    )
    for _, row in merged.loc[exceeds_total].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "accepted_pull_requests", "expected": "<= total_pull_requests",
            "actual": _format(row["accepted_pull_requests"]),
            "detail": f"PRs aceitas ({_format(row['accepted_pull_requests'])}) maior que o total "
                      f"({_format(row['total_pull_requests_raw'])})",
        })

    negative_prs = merged["accepted_pull_requests"].notna() & (merged["accepted_pull_requests"] < 0)
    for _, row in merged.loc[negative_prs].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "accepted_pull_requests", "expected": ">= 0", "actual": _format(row["accepted_pull_requests"]),
            "detail": "quantidade negativa de Pull Requests aceitas",
        })

    issue_frame = pd.DataFrame(issues)
    outlier_frame = _outliers(merged)
    manual_sample = _manual_sample(merged)
    return ValidationResult(issue_frame, outlier_frame, manual_sample, len(merged))


def evidence_path(processed_path: Path, output_dir: Path = PROCESSED_DIR) -> Path:
    suffix = processed_path.stem.removeprefix("repos_processed_")
    return output_dir / f"validation_rq01_rq02_{suffix}.csv"


def report_path(processed_path: Path, output_dir: Path = REPORTS_DIR) -> Path:
    suffix = processed_path.stem.removeprefix("repos_processed_")
    return output_dir / f"validation_rq01_rq02_{suffix}.md"


def _sample_table(sample: pd.DataFrame) -> str:
    if sample.empty:
        return "Nenhum registro disponível para amostragem manual.\n"
    lines = ["| id | idade (anos) | PRs aceitas | PRs merged | PRs total |", "|---|---|---|---|---|"]
    for _, row in sample.iterrows():
        lines.append(
            f"| {row['name_with_owner']} | {row['age_years']:.2f} | "
            f"{_format(row['accepted_pull_requests'])} | {_format(row['merged_pull_requests_raw'])} | "
            f"{_format(row['total_pull_requests_raw'])} |"
        )
    return "\n".join(lines) + "\n"


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
    if result.repositories >= 1000:
        coverage_note = (
            "Esta execução cobre a base completa de 1.000 repositórios da coleta oficial.\n"
        )
    else:
        coverage_note = (
            "Esta execução não substitui a validação da coleta completa: a mesma rotina "
            "deve ser reexecutada quando houver 1.000 repositórios processados.\n"
        )
    markdown_path.write_text(
        "# Validação RQ01/RQ02\n\n"
        f"- Repositórios validados: **{result.repositories}**\n"
        f"- Status: **{status}**\n"
        f"- Inconsistências encontradas: **{len(result.issues)}**\n"
        f"- Outliers registrados (IQR): **{len(result.outliers)}**\n\n"
        "## Regras validadas\n\n"
        "- `age_years` reproduz `(collected_at - created_at)` em anos, com created_at "
        f"nunca anterior à fundação do GitHub ({GITHUB_FOUNDED_AT.date()}).\n"
        "- `accepted_pull_requests` é sempre igual a `merged_pull_requests` (estado `MERGED`) "
        "e nunca ultrapassa `total_pull_requests`.\n"
        "- Ausência de `created_at`, `collected_at`, `age_years` ou `accepted_pull_requests` "
        "é tratada como inconsistência de completude.\n\n"
        "Os outliers são evidências para revisão; eles não são removidos automaticamente.\n\n"
        "## Amostra para conferência manual\n\n"
        f"Amostra fixa e reproduzível (seed {MANUAL_SAMPLE_SEED}) para revisão humana:\n\n"
        f"{_sample_table(result.manual_sample)}\n"
        f"{coverage_note}",
        encoding="utf-8",
    )
    return csv_path, markdown_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida RQ01 e RQ02 contra os dados brutos.")
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
    print(f"Evidências: {evidence}")
    print(f"Relatório: {report}")
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
