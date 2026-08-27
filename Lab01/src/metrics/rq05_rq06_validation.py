"""Valida as métricas de linguagem primária e issues fechadas (RQ05/RQ06).

Uso:
    python src/metrics/rq05_rq06_validation.py \
      data/raw/repos_raw_<coleta>.csv \
      data/processed/repos_processed_<coleta>.csv

O script compara a base processada ao CSV bruto da mesma coleta, sem alterar
nenhum dos arquivos de entrada. As evidências são salvas em data/processed/ e
reports/drafts/.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from rq05_rq06_language_issues import (
    UNIDENTIFIED_LANGUAGE,
    closed_issues_percentage,
    is_popular_language,
    normalize_language,
)


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"
RAW_COLUMNS = ["id", "name_with_owner", "primary_language", "open_issues", "closed_issues"]
PROCESSED_COLUMNS = RAW_COLUMNS + [
    "language_group", "is_popular_language", "total_issues", "has_issues",
    "closed_issues_percentage",
]


@dataclass
class ValidationResult:
    issues: pd.DataFrame
    observations: pd.DataFrame
    repositories: int
    without_language: int
    without_issues: int

    @property
    def passed(self) -> bool:
        return self.issues.empty


def load(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Carrega o CSV, preservando o identificador como texto."""
    df = pd.read_csv(path, dtype={"id": "string"})
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{path}: colunas ausentes: {', '.join(missing)}")
    return df


def _same(left: pd.Series, right: pd.Series) -> pd.Series:
    """Compara séries considerando dois valores ausentes como equivalentes."""
    both_missing = left.isna() & right.isna()
    both_present = left.notna() & right.notna()
    result = both_missing.copy()
    result.loc[both_present] = left.loc[both_present].eq(right.loc[both_present]).fillna(False)
    return result


def _format(value) -> str:
    return "" if pd.isna(value) else str(value)


def _add_mismatches(
    issues: list[dict], merged: pd.DataFrame, field: str, expected: pd.Series, actual: pd.Series,
    tolerance: float | None = None,
) -> None:
    matches = _same(expected, actual)
    if tolerance is not None:
        both_present = expected.notna() & actual.notna()
        matches.loc[both_present] = pd.Series(
            pd.Series(expected.loc[both_present], dtype="float64").sub(
                pd.Series(actual.loc[both_present], dtype="float64")
            ).abs().le(tolerance),
            index=expected.loc[both_present].index,
        )

    for _, row in merged.loc[~matches].iterrows():
        issues.append({
            "record_type": "inconsistency",
            "id": row["id"],
            "name_with_owner": row["name_with_owner"],
            "field": field,
            "expected": _format(expected.loc[row.name]),
            "actual": _format(actual.loc[row.name]),
            "detail": "valor processado diverge do valor bruto ou da regra definida",
        })


def validate(raw: pd.DataFrame, processed: pd.DataFrame) -> ValidationResult:
    """Valida RQ05/RQ06, por identificador, contra os dados brutos da coleta."""
    raw = raw.copy()
    processed = processed.copy()
    issues: list[dict] = []
    observations: list[dict] = []

    if raw["id"].duplicated().any() or processed["id"].duplicated().any():
        raise ValueError("Há IDs duplicados na base bruta ou processada.")

    raw_ids, processed_ids = set(raw["id"]), set(processed["id"])
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

    merged = raw[RAW_COLUMNS].merge(processed, on="id", suffixes=("_raw", "_processed"), how="inner")
    merged = merged.rename(columns={"name_with_owner_raw": "name_with_owner"})

    _add_mismatches(
        issues, merged, "primary_language", merged["primary_language_raw"], merged["primary_language_processed"]
    )
    _add_mismatches(issues, merged, "open_issues", merged["open_issues_raw"], merged["open_issues_processed"])
    _add_mismatches(issues, merged, "closed_issues", merged["closed_issues_raw"], merged["closed_issues_processed"])

    expected_language = merged["primary_language_raw"].map(normalize_language)
    expected_popular = expected_language.map(is_popular_language)
    expected_total = merged["open_issues_raw"] + merged["closed_issues_raw"]
    expected_has_issues = expected_total > 0
    expected_percentage = pd.Series(
        [closed_issues_percentage(opened, closed) for opened, closed in zip(
            merged["open_issues_raw"], merged["closed_issues_raw"]
        )],
        index=merged.index,
        dtype="Float64",
    )

    _add_mismatches(issues, merged, "language_group", expected_language, merged["language_group"])
    _add_mismatches(issues, merged, "is_popular_language", expected_popular, merged["is_popular_language"])
    _add_mismatches(issues, merged, "total_issues", expected_total, merged["total_issues"])
    _add_mismatches(issues, merged, "has_issues", expected_has_issues, merged["has_issues"])
    _add_mismatches(
        issues, merged, "closed_issues_percentage", expected_percentage, merged["closed_issues_percentage"], 0.000001
    )

    invalid_percentage = merged["closed_issues_percentage"].notna() & ~merged["closed_issues_percentage"].between(0, 100)
    for _, row in merged.loc[invalid_percentage].iterrows():
        issues.append({
            "record_type": "inconsistency", "id": row["id"], "name_with_owner": row["name_with_owner"],
            "field": "closed_issues_percentage", "expected": "valor entre 0 e 100",
            "actual": _format(row["closed_issues_percentage"]), "detail": "percentual fora do intervalo válido",
        })

    without_language = expected_language.eq(UNIDENTIFIED_LANGUAGE)
    without_issues = ~expected_has_issues
    for mask, field, detail in [
        (without_language, "primary_language", "linguagem ausente; categoria normalizada aplicada"),
        (without_issues, "closed_issues_percentage", "repositório sem issues; percentual permanece ausente"),
    ]:
        for _, row in merged.loc[mask].iterrows():
            observations.append({
                "record_type": "observation", "id": row["id"], "name_with_owner": row["name_with_owner"],
                "field": field, "expected": "", "actual": "", "detail": detail,
            })

    return ValidationResult(
        pd.DataFrame(issues),
        pd.DataFrame(observations),
        len(merged),
        int(without_language.sum()),
        int(without_issues.sum()),
    )


def save_evidence(result: ValidationResult, processed_path: Path) -> tuple[Path, Path]:
    """Salva CSV de evidências e relatório Markdown da execução."""
    suffix = processed_path.stem.removeprefix("repos_processed_")
    csv_path = PROCESSED_DIR / f"validation_rq05_rq06_{suffix}.csv"
    report_path = REPORTS_DIR / f"validation_rq05_rq06_{suffix}.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    evidence = pd.concat([result.issues, result.observations], ignore_index=True)
    if evidence.empty:
        evidence = pd.DataFrame(columns=["record_type", "id", "name_with_owner", "field", "expected", "actual", "detail"])
    evidence.to_csv(csv_path, index=False)

    status = "APROVADAS na amostra atual" if result.passed else "COM PENDÊNCIAS"
    report_path.write_text(
        "# Validação RQ05/RQ06\n\n"
        f"- Repositórios validados: **{result.repositories}**\n"
        f"- Status: **{status}**\n"
        f"- Inconsistências encontradas: **{len(result.issues)}**\n"
        f"- Repositórios sem linguagem primária: **{result.without_language}**\n"
        f"- Repositórios sem issues: **{result.without_issues}**\n\n"
        "Repositórios sem linguagem recebem `Sem linguagem identificada`. Repositórios "
        "sem issues mantêm `closed_issues_percentage` ausente, sem divisão por zero.\n\n"
        "Esta execução deve ser repetida quando a coleta completa de 1.000 repositórios "
        "estiver disponível.\n",
        encoding="utf-8",
    )
    return csv_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida RQ05 e RQ06 contra os dados brutos.")
    parser.add_argument("raw", type=Path, help="CSV bruto da coleta")
    parser.add_argument("processed", type=Path, help="CSV processado pelo pipeline")
    args = parser.parse_args()

    result = validate(load(args.raw, RAW_COLUMNS), load(args.processed, PROCESSED_COLUMNS))
    evidence, report = save_evidence(result, args.processed)
    print(f"Repositórios validados: {result.repositories}")
    print(f"Inconsistências: {len(result.issues)}")
    print(f"Sem linguagem: {result.without_language}")
    print(f"Sem issues: {result.without_issues}")
    print(f"Evidências: {evidence}")
    print(f"Relatório: {report}")


if __name__ == "__main__":
    main()
