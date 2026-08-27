"""Valida a análise integrada da RQ07 contra o dataset consolidado.

Uso:
    python src/analysis/rq07_validation.py \
      data/processed/repos_rq07_consolidated_<coleta>.csv \
      data/processed/rq07_statistics_<coleta>.csv

O script recalcula, a partir do dataset consolidado, as mesmas estatísticas de
grupo, correlações e outliers produzidos por `rq07_analysis.py` (reutilizando
a função `analyze`, sem reimplementar nenhuma regra) e compara o resultado com
os artefatos já gerados, sem alterar nenhum dos arquivos de entrada. Segue o
mesmo padrão de `src/metrics/rq01_rq02_validation.py`,
`rq03_rq04_validation.py` e `rq05_rq06_validation.py`.

O caminho do CSV de outliers é derivado do CSV de estatísticas informado
(`rq07_statistics_<coleta>.csv` -> `rq07_analysis_outliers_<coleta>.csv`),
seguindo a mesma convenção de nomes usada por `rq07_analysis.run`.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from rq07_analysis import REQUIRED_COLUMNS, analyze


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "drafts"

STATISTICS_COLUMNS = ["tipo", "grupo", "metrica", "descricao", "n", "media", "mediana", "q1", "q3", "pearson", "spearman"]
OUTLIERS_COLUMNS = ["id", "name_with_owner", "metrica"]

# Tolerância de ponto flutuante ao comparar estatísticas e correlações recalculadas.
FLOAT_TOLERANCE = 1e-6


@dataclass
class ValidationResult:
    issues: pd.DataFrame
    repositories: int
    excluded_without_language: int
    outliers_recomputed: int

    @property
    def passed(self) -> bool:
        return self.issues.empty


def load_consolidated(path: Path) -> pd.DataFrame:
    """Carrega o dataset consolidado da RQ07, conferindo as colunas mínimas."""
    df = pd.read_csv(path, dtype={"id": "string"})
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path}: colunas ausentes: {', '.join(missing)}")
    return df


def load_statistics(path: Path) -> pd.DataFrame:
    """Carrega o CSV de estatísticas (grupo + correlação) gerado por rq07_analysis."""
    df = pd.read_csv(path)
    missing = [column for column in ["tipo", "metrica", "n"] if column not in df.columns]
    if missing:
        raise ValueError(f"{path}: colunas ausentes: {', '.join(missing)}")
    return df


def load_outliers(path: Path) -> pd.DataFrame:
    """Carrega o CSV de outliers gerado por rq07_analysis (pode estar vazio)."""
    df = pd.read_csv(path, dtype={"id": "string"})
    missing = [column for column in OUTLIERS_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"{path}: colunas ausentes: {', '.join(missing)}")
    return df


def outliers_path_for(statistics_path: Path) -> Path:
    """Deriva o caminho do CSV de outliers a partir do CSV de estatísticas informado."""
    return statistics_path.with_name(
        statistics_path.name.replace("rq07_statistics_", "rq07_analysis_outliers_", 1)
    )


def _close(expected, actual) -> bool:
    expected_missing, actual_missing = pd.isna(expected), pd.isna(actual)
    if expected_missing and actual_missing:
        return True
    if expected_missing or actual_missing:
        return False
    return math.isclose(float(expected), float(actual), abs_tol=FLOAT_TOLERANCE)


def _check_group_statistics(issues: list[dict], expected: pd.DataFrame, actual: pd.DataFrame) -> None:
    actual_group = actual.loc[actual["tipo"] == "grupo"]
    for _, row in expected.iterrows():
        match = actual_group.loc[
            (actual_group["grupo"] == row["grupo"]) & (actual_group["metrica"] == row["metrica"])
        ]
        label = f"group_statistics[{row['grupo']}/{row['metrica']}]"
        if match.empty:
            issues.append({
                "record_type": "inconsistency", "id": "", "name_with_owner": "", "field": label,
                "expected": "presente no CSV de estatísticas", "actual": "ausente",
                "detail": "combinação grupo/métrica recalculada não encontrada no artefato gerado",
            })
            continue
        found = match.iloc[0]
        for field in ["n", "media", "mediana", "q1", "q3"]:
            if not _close(row[field], found[field]):
                issues.append({
                    "record_type": "inconsistency", "id": "", "name_with_owner": "", "field": f"{label}.{field}",
                    "expected": row[field], "actual": found[field],
                    "detail": "valor recalculado diverge do artefato gerado por rq07_analysis",
                })


def _check_correlations(issues: list[dict], expected: pd.DataFrame, actual: pd.DataFrame) -> None:
    actual_correlation = actual.loc[actual["tipo"] == "correlacao"]
    for _, row in expected.iterrows():
        match = actual_correlation.loc[actual_correlation["metrica"] == row["metrica"]]
        label = f"correlations[{row['metrica']}]"
        if match.empty:
            issues.append({
                "record_type": "inconsistency", "id": "", "name_with_owner": "", "field": label,
                "expected": "presente no CSV de estatísticas", "actual": "ausente",
                "detail": "métrica de correlação recalculada não encontrada no artefato gerado",
            })
            continue
        found = match.iloc[0]
        for field in ["n", "pearson", "spearman"]:
            if not _close(row[field], found[field]):
                issues.append({
                    "record_type": "inconsistency", "id": "", "name_with_owner": "", "field": f"{label}.{field}",
                    "expected": row[field], "actual": found[field],
                    "detail": "valor recalculado diverge do artefato gerado por rq07_analysis",
                })


def _check_outliers(
    issues: list[dict], expected: pd.DataFrame, actual: pd.DataFrame, consolidated_ids: set,
) -> None:
    expected_keys = set(zip(expected["id"], expected["metrica"])) if not expected.empty else set()
    actual_keys = set(zip(actual["id"], actual["metrica"])) if not actual.empty else set()

    for repository_id, metric in sorted(expected_keys - actual_keys, key=str):
        issues.append({
            "record_type": "inconsistency", "id": repository_id, "name_with_owner": "",
            "field": f"outliers[{metric}]", "expected": "sinalizado", "actual": "ausente",
            "detail": "outlier recalculado a partir do consolidado não está no CSV de outliers gerado",
        })
    for repository_id, metric in sorted(actual_keys - expected_keys, key=str):
        issues.append({
            "record_type": "inconsistency", "id": repository_id, "name_with_owner": "",
            "field": f"outliers[{metric}]", "expected": "ausente", "actual": "sinalizado",
            "detail": "CSV de outliers sinaliza um caso que não é reproduzido a partir do consolidado",
        })

    if not actual.empty:
        for repository_id in sorted(set(actual["id"]) - consolidated_ids, key=str):
            issues.append({
                "record_type": "inconsistency", "id": repository_id, "name_with_owner": "",
                "field": "outliers[id]", "expected": "presente no consolidado", "actual": "ausente",
                "detail": "id sinalizado como outlier não existe no dataset consolidado",
            })


def validate(consolidated: pd.DataFrame, statistics: pd.DataFrame, outliers: pd.DataFrame) -> ValidationResult:
    """Reproduz a análise da RQ07 a partir do consolidado e confere os artefatos gerados."""
    if consolidated["id"].duplicated().any():
        raise ValueError("Há IDs duplicados no dataset consolidado.")

    expected = analyze(consolidated)
    issues: list[dict] = []

    _check_group_statistics(issues, expected.group_statistics, statistics)
    _check_correlations(issues, expected.correlations, statistics)
    _check_outliers(issues, expected.outliers, outliers, set(consolidated["id"]))

    return ValidationResult(
        pd.DataFrame(issues),
        expected.repositories,
        expected.excluded_without_language,
        len(expected.outliers),
    )


def save_evidence(result: ValidationResult, statistics_path: Path) -> tuple[Path, Path]:
    """Salva o CSV de evidências e o relatório Markdown da validação da RQ07."""
    suffix = statistics_path.stem.removeprefix("rq07_statistics_")
    csv_path = PROCESSED_DIR / f"validation_rq07_{suffix}.csv"
    report_path = REPORTS_DIR / f"validation_rq07_{suffix}.md"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    evidence = result.issues
    if evidence.empty:
        evidence = pd.DataFrame(columns=["record_type", "id", "name_with_owner", "field", "expected", "actual", "detail"])
    evidence.to_csv(csv_path, index=False)

    status = "APROVADA na amostra atual" if result.passed else "COM PENDÊNCIAS"
    report_path.write_text(
        "# Validação RQ07\n\n"
        f"- Repositórios analisados: **{result.repositories}**\n"
        f"- Status: **{status}**\n"
        f"- Inconsistências encontradas: **{len(result.issues)}**\n"
        f"- Sem linguagem identificada (excluídos da comparação): **{result.excluded_without_language}**\n"
        f"- Outliers recalculados: **{result.outliers_recomputed}**\n\n"
        "## Regras validadas\n\n"
        "- Estatísticas de grupo (`n`, `media`, `mediana`, `q1`, `q3`) por métrica e categoria "
        "de linguagem (`Popular`/`Não popular`) reproduzem o artefato `rq07_statistics_<coleta>.csv`.\n"
        "- Correlações de Pearson e Spearman entre estrelas e as métricas de RQ01-06 reproduzem "
        "o mesmo artefato.\n"
        "- Outliers por IQR (cercas de Tukey) recalculados a partir do consolidado reproduzem "
        "`rq07_analysis_outliers_<coleta>.csv`, sem casos ausentes nem adicionais.\n"
        "- Todo `id` sinalizado como outlier existe no dataset consolidado.\n\n"
        "Esta validação não recalcula nenhuma regra nova: ela reaproveita a função `analyze` de "
        "`src/analysis/rq07_analysis.py`, a exemplo do que `rq05_rq06_validation.py` já faz com "
        "`rq05_rq06_language_issues.py`.\n",
        encoding="utf-8",
    )
    return csv_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida a análise da RQ07 contra o dataset consolidado.")
    parser.add_argument(
        "consolidated", type=Path,
        help="Dataset consolidado da RQ07 (data/processed/repos_rq07_consolidated_<coleta>.csv)",
    )
    parser.add_argument(
        "statistics", type=Path,
        help="CSV de estatísticas gerado por rq07_analysis.py (data/processed/rq07_statistics_<coleta>.csv)",
    )
    args = parser.parse_args()

    outliers_path = outliers_path_for(args.statistics)
    result = validate(
        load_consolidated(args.consolidated),
        load_statistics(args.statistics),
        load_outliers(outliers_path),
    )
    evidence, report = save_evidence(result, args.statistics)
    print(f"Repositórios analisados: {result.repositories}")
    print(f"Inconsistências: {len(result.issues)}")
    print(f"Sem linguagem: {result.excluded_without_language}")
    print(f"Outliers recalculados: {result.outliers_recomputed}")
    print(f"Evidências: {evidence}")
    print(f"Relatório: {report}")
    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
