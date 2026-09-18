"""Constrói o dataset de uma linha por trial a partir das evidências brutas.

O ponto de partida é sempre a alocação congelada, e não a lista de diretórios
existentes. Assim, um trial ainda sem coleta continua visível no dataset como
valor ausente e no relatório de consolidação, em vez de desaparecer da análise.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from src.collection.allocation import AllocationRow, read_allocation

ROOT = Path(__file__).resolve().parents[2]

DATASET_COLUMNS = [
    "trial_id",
    "participant_id",
    "kata_id",
    "difficulty_block",
    "order_position",
    "treatment",
    "started_at",
    "finished_at",
    "duration_seconds",
    "completed",
    "censored",
    "passed_tests",
    "failed_tests",
    "total_tests",
    "success_rate",
    "function_count",
    "mean_cyclomatic_complexity",
    "max_cyclomatic_complexity",
    "duplicated_lines",
    "duplication_percentage",
    "loc",
    "maintainability_index",
    "prompt_count",
    "perceived_difficulty",
    "incident_flag",
    "issue_number",
    "commit_sha",
    "trial_record_path",
    "junit_report_path",
    "metrics_record_path",
    "trial_config_path",
    "data_quality_note_path",
    "prompt_log_path",
    "commit_subject",
    "quality_note_applied",
]

ERROR_REPORT_COLUMNS = ["severity", "trial_id", "source", "field", "code", "message"]
ISSUE_PATTERN = re.compile(r"(?<!\w)#(\d+)\b")
PROMPT_HEADING_PATTERN = re.compile(
    r"^##\s+(?:prompt\b|confirmação do usuário\b)", re.IGNORECASE | re.MULTILINE
)


@dataclass(frozen=True)
class ConsolidationError:
    """Uma lacuna ou divergência detectada, mantida fora da linha de dados."""

    severity: str
    trial_id: str
    source: str
    field: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "trial_id": self.trial_id,
            "source": self.source,
            "field": self.field,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict[str, Any]]
    errors: list[ConsolidationError]


TraceabilityLookup = Callable[[str], tuple[str | None, str | None, str | None]]


def _report(
    errors: list[ConsolidationError],
    *,
    severity: str,
    trial_id: str,
    source: str,
    field: str,
    code: str,
    message: str,
) -> None:
    errors.append(
        ConsolidationError(
            severity=severity,
            trial_id=trial_id,
            source=source,
            field=field,
            code=code,
            message=message,
        )
    )


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _read_json(
    path: Path,
    *,
    trial_id: str,
    source: str,
    errors: list[ConsolidationError],
) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _report(
            errors,
            severity="error",
            trial_id=trial_id,
            source=source,
            field="",
            code="invalid_json",
            message=f"Não foi possível ler JSON: {error}",
        )
        return None
    if not isinstance(value, dict):
        _report(
            errors,
            severity="error",
            trial_id=trial_id,
            source=source,
            field="",
            code="invalid_json_object",
            message="O arquivo JSON deve conter um objeto no nível superior.",
        )
        return None
    return value


def _read_junit_summary(path: Path) -> tuple[int, int, int] | None:
    """Retorna total, aprovados e falhos usando a mesma convenção do coletor."""
    if not path.is_file():
        return None
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return (0, 0, 0)
    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    return (total, total - failed - skipped, failed)


def _as_nonnegative_number(value: Any, field: str, trial_id: str, errors: list[ConsolidationError]) -> Any:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        _report(
            errors,
            severity="error",
            trial_id=trial_id,
            source="trial.json",
            field=field,
            code="invalid_value",
            message="O valor deve ser numérico e não negativo; foi preservado como ausente.",
        )
        return None
    return value


def _calculate_success_rate(passed: Any, total: Any) -> float | None:
    if passed is None or total is None or total == 0:
        return None
    return round(passed / total * 100, 2)


def _extract_prompt_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    return len(PROMPT_HEADING_PATTERN.findall(path.read_text(encoding="utf-8")))


def git_traceability_lookup(repository_root: Path) -> TraceabilityLookup:
    """Cria leitor de commit/Issue a partir do último commit do código final."""
    repository_root = repository_root.resolve()

    def lookup(trial_id: str) -> tuple[str | None, str | None, str | None]:
        relative_solution = f"Lab02/trials/{trial_id}/src/solution.py"
        try:
            completed = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_root),
                    "log",
                    "-1",
                    "--format=%H%x00%s",
                    "--",
                    relative_solution,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except OSError:
            return (None, None, None)
        if completed.returncode != 0 or not completed.stdout.strip():
            return (None, None, None)
        sha, subject = completed.stdout.rstrip("\n").split("\0", maxsplit=1)
        issue_match = ISSUE_PATTERN.search(subject)
        return (issue_match.group(1) if issue_match else None, sha or None, subject or None)

    return lookup


def _apply_quality_note(
    record: dict[str, Any], note: dict[str, Any] | None, trial_id: str, errors: list[ConsolidationError]
) -> tuple[dict[str, Any], bool]:
    if note is None:
        return record, False
    correction = note.get("corrected_interpretation")
    if note.get("trial_id") != trial_id or not isinstance(correction, dict):
        _report(
            errors,
            severity="warning",
            trial_id=trial_id,
            source="data-quality-note.json",
            field="",
            code="ignored_quality_note",
            message="A nota não possui uma interpretação corrigida compatível com o trial.",
        )
        return record, False
    corrected = dict(record)
    corrected.update(correction)
    _report(
        errors,
        severity="info",
        trial_id=trial_id,
        source="data-quality-note.json",
        field="completed,passed_tests,failed_tests,success_rate",
        code="quality_note_applied",
        message="A interpretação corrigida e rastreável da nota de qualidade foi aplicada.",
    )
    return corrected, True


def _extract_test_values(
    record: dict[str, Any] | None,
    trial_id: str,
    errors: list[ConsolidationError],
) -> dict[str, Any]:
    if record is None:
        return {
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "completed": None,
            "censored": None,
            "passed_tests": None,
            "failed_tests": None,
            "total_tests": None,
            "success_rate": None,
            "incident_flag": None,
        }

    values = {
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
        "duration_seconds": _as_nonnegative_number(record.get("duration_seconds"), "duration_seconds", trial_id, errors),
        "completed": record.get("completed") if isinstance(record.get("completed"), bool) else None,
        "censored": record.get("censored") if isinstance(record.get("censored"), bool) else None,
        "passed_tests": _as_nonnegative_number(record.get("passed_tests"), "passed_tests", trial_id, errors),
        "failed_tests": _as_nonnegative_number(record.get("failed_tests"), "failed_tests", trial_id, errors),
        "total_tests": _as_nonnegative_number(record.get("total_tests"), "total_tests", trial_id, errors),
        "incident_flag": record.get("incident_flag") if isinstance(record.get("incident_flag"), bool) else None,
    }
    values["success_rate"] = _calculate_success_rate(values["passed_tests"], values["total_tests"])

    if values["completed"] is None:
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="completed", code="missing_value", message="Campo obrigatório ausente ou inválido.")
    if values["censored"] is None:
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="censored", code="missing_value", message="Campo obrigatório ausente ou inválido.")
    if all(values[name] is not None for name in ("passed_tests", "failed_tests", "total_tests")) and (
        values["passed_tests"] + values["failed_tests"] != values["total_tests"]
    ):
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="passed_tests,failed_tests,total_tests", code="inconsistent_test_total", message="passed_tests + failed_tests não corresponde a total_tests.")
    if values["completed"] is True and values["failed_tests"] not in (None, 0):
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="completed,failed_tests", code="inconsistent_completion", message="Trial concluído não pode ter testes falhando.")
    if values["censored"] is True and (
        values["duration_seconds"] != 2100 or values["completed"] is not False
    ):
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="censored,duration_seconds,completed", code="inconsistent_censorship", message="Trial censurado deve ter duração de 2100 segundos e não estar concluído.")
    return values


def _extract_metric_values(
    metrics: dict[str, Any] | None,
    trial_id: str,
    errors: list[ConsolidationError],
) -> dict[str, Any]:
    fields = {
        "function_count": None,
        "mean_cyclomatic_complexity": None,
        "max_cyclomatic_complexity": None,
        "duplicated_lines": None,
        "duplication_percentage": None,
        "loc": None,
        "maintainability_index": None,
    }
    if metrics is None:
        return fields
    complexity = metrics.get("complexity") if isinstance(metrics.get("complexity"), dict) else {}
    duplication = metrics.get("duplication") if isinstance(metrics.get("duplication"), dict) else {}
    loc = metrics.get("loc") if isinstance(metrics.get("loc"), dict) else {}
    maintainability = metrics.get("maintainability") if isinstance(metrics.get("maintainability"), dict) else {}
    fields.update(
        {
            "function_count": complexity.get("function_count"),
            "mean_cyclomatic_complexity": complexity.get("mean_cyclomatic_complexity"),
            "max_cyclomatic_complexity": complexity.get("max_cyclomatic_complexity"),
            "duplicated_lines": duplication.get("duplicated_lines"),
            "duplication_percentage": duplication.get("duplication_percentage"),
            "loc": loc.get("loc"),
            "maintainability_index": maintainability.get("maintainability_index"),
        }
    )
    for field, value in tuple(fields.items()):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0):
            _report(errors, severity="error", trial_id=trial_id, source="metrics.json", field=field, code="invalid_metric", message="Métrica deve ser numérica e não negativa; foi preservada como ausente.")
            fields[field] = None
    if complexity.get("missing") is True:
        for field in ("function_count", "mean_cyclomatic_complexity", "max_cyclomatic_complexity"):
            fields[field] = None
    return fields


def consolidate_trial(
    allocation: AllocationRow,
    *,
    raw_trials_root: Path,
    raw_metrics_root: Path,
    trials_root: Path,
    project_root: Path = ROOT,
    traceability_lookup: TraceabilityLookup | None = None,
) -> tuple[dict[str, Any], list[ConsolidationError]]:
    """Consolida uma alocação sem converter lacunas de evidência em zeros."""
    trial_id = allocation.trial_id
    errors: list[ConsolidationError] = []
    raw_dir = Path(raw_trials_root) / trial_id
    metrics_dir = Path(raw_metrics_root) / trial_id
    trial_dir = Path(trials_root) / trial_id
    record_path = raw_dir / "trial.json"
    junit_path = raw_dir / "final_junit.xml"
    metrics_path = metrics_dir / "metrics.json"
    config_path = trial_dir / "trial-config.json"
    quality_path = raw_dir / "data-quality-note.json"
    raw_prompt_path = raw_dir / "prompts.md"
    trial_prompt_path = trial_dir / "prompts.md"
    prompt_path = raw_prompt_path if raw_prompt_path.is_file() else trial_prompt_path

    record = _read_json(record_path, trial_id=trial_id, source="trial.json", errors=errors)
    if record is None:
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="", code="missing_trial_record", message=f"Evidência bruta ausente: {_relative_path(record_path, project_root)}")
    elif record.get("trial_id") != trial_id:
        _report(errors, severity="error", trial_id=trial_id, source="trial.json", field="trial_id", code="mismatched_trial_id", message="O trial_id da evidência bruta não corresponde à alocação congelada.")

    quality_note = _read_json(quality_path, trial_id=trial_id, source="data-quality-note.json", errors=errors)
    corrected_record, quality_note_applied = _apply_quality_note(record or {}, quality_note, trial_id, errors)
    test_values = _extract_test_values(corrected_record if record is not None else None, trial_id, errors)

    if not config_path.is_file():
        _report(errors, severity="warning", trial_id=trial_id, source="trial-config.json", field="", code="missing_trial_config", message=f"Configuração preparada ausente: {_relative_path(config_path, project_root)}")
    else:
        config = _read_json(config_path, trial_id=trial_id, source="trial-config.json", errors=errors)
        if config is not None and config.get("trial_id") != trial_id:
            _report(errors, severity="error", trial_id=trial_id, source="trial-config.json", field="trial_id", code="mismatched_trial_id", message="O trial_id da configuração não corresponde à alocação congelada.")

    try:
        junit_summary = _read_junit_summary(junit_path)
    except (OSError, ET.ParseError, ValueError) as error:
        junit_summary = None
        _report(errors, severity="error", trial_id=trial_id, source="final_junit.xml", field="", code="invalid_junit", message=f"Não foi possível ler o relatório JUnit: {error}")
    if junit_summary is None:
        _report(errors, severity="warning", trial_id=trial_id, source="final_junit.xml", field="", code="missing_junit_report", message=f"Resultado de testes ausente: {_relative_path(junit_path, project_root)}")
    elif not quality_note_applied and all(test_values[name] is not None for name in ("total_tests", "passed_tests", "failed_tests")) and junit_summary != (
        test_values["total_tests"], test_values["passed_tests"], test_values["failed_tests"]
    ):
        _report(errors, severity="error", trial_id=trial_id, source="final_junit.xml", field="total_tests,passed_tests,failed_tests", code="junit_mismatch", message="O resumo do JUnit diverge do registro do trial.")

    metrics = _read_json(metrics_path, trial_id=trial_id, source="metrics.json", errors=errors)
    if metrics is None:
        _report(errors, severity="warning", trial_id=trial_id, source="metrics.json", field="", code="missing_static_metrics", message=f"Métricas estáticas ausentes: {_relative_path(metrics_path, project_root)}")
    elif metrics.get("trial_id") != trial_id:
        _report(errors, severity="error", trial_id=trial_id, source="metrics.json", field="trial_id", code="mismatched_trial_id", message="O trial_id das métricas não corresponde à alocação congelada.")
    metric_values = _extract_metric_values(metrics, trial_id, errors)

    prompt_count = _extract_prompt_count(prompt_path)
    if allocation.treatment == "ai" and prompt_count is None:
        _report(errors, severity="warning", trial_id=trial_id, source="prompts.md", field="prompt_count", code="missing_prompt_log", message="Não há log de prompts exportável para o tratamento IA.")

    issue_number, commit_sha, commit_subject = (None, None, None)
    if traceability_lookup is not None:
        issue_number, commit_sha, commit_subject = traceability_lookup(trial_id)
    if issue_number is None:
        _report(errors, severity="warning", trial_id=trial_id, source="git", field="issue_number", code="missing_issue_link", message="Issue não encontrada no commit que preserva o código final.")
    if commit_sha is None:
        _report(errors, severity="warning", trial_id=trial_id, source="git", field="commit_sha", code="missing_commit_link", message="Commit que preserva o código final não encontrado.")

    _report(errors, severity="warning", trial_id=trial_id, source="participant_feedback", field="perceived_difficulty", code="missing_participant_feedback", message="A dificuldade percebida não foi registrada; o valor permanece ausente.")

    row: dict[str, Any] = {
        "trial_id": trial_id,
        "participant_id": allocation.participant_id,
        "kata_id": allocation.kata_id,
        "difficulty_block": allocation.difficulty_block,
        "order_position": allocation.order_position,
        "treatment": allocation.treatment,
        **test_values,
        **metric_values,
        "prompt_count": prompt_count,
        "perceived_difficulty": None,
        "issue_number": issue_number,
        "commit_sha": commit_sha,
        "trial_record_path": _relative_path(record_path, project_root) if record_path.is_file() else None,
        "junit_report_path": _relative_path(junit_path, project_root) if junit_path.is_file() else None,
        "metrics_record_path": _relative_path(metrics_path, project_root) if metrics_path.is_file() else None,
        "trial_config_path": _relative_path(config_path, project_root) if config_path.is_file() else None,
        "data_quality_note_path": _relative_path(quality_path, project_root) if quality_path.is_file() else None,
        "prompt_log_path": _relative_path(prompt_path, project_root) if prompt_path.is_file() else None,
        "commit_subject": commit_subject,
        "quality_note_applied": quality_note_applied,
    }
    return row, errors


def build_dataset(
    *,
    allocation_path: Path = ROOT / "data" / "metadata" / "allocation.csv",
    raw_trials_root: Path = ROOT / "data" / "raw" / "trials",
    raw_metrics_root: Path = ROOT / "data" / "raw" / "metrics",
    trials_root: Path = ROOT / "trials",
    project_root: Path = ROOT,
    traceability_lookup: TraceabilityLookup | None = None,
) -> BuildResult:
    """Consolida as 18 alocações em ordem canônica e retorna dados + achados."""
    lookup = traceability_lookup or git_traceability_lookup(Path(project_root).parent)
    rows: list[dict[str, Any]] = []
    errors: list[ConsolidationError] = []
    for allocation in read_allocation(Path(allocation_path)):
        row, trial_errors = consolidate_trial(
            allocation,
            raw_trials_root=raw_trials_root,
            raw_metrics_root=raw_metrics_root,
            trials_root=trials_root,
            project_root=project_root,
            traceability_lookup=lookup,
        )
        rows.append(row)
        errors.extend(trial_errors)
    return BuildResult(rows=rows, errors=errors)


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return value


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows({field: _csv_value(row.get(field)) for field in fieldnames} for row in rows)


def write_build_result(result: BuildResult, dataset_path: Path, errors_path: Path) -> None:
    """Grava somente artefatos derivados; dados brutos nunca são modificados."""
    _write_csv(Path(dataset_path), DATASET_COLUMNS, result.rows)
    _write_csv(Path(errors_path), ERROR_REPORT_COLUMNS, (error.as_dict() for error in result.errors))
