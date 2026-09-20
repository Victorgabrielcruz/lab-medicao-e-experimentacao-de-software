"""Valida integridade, consistência e completude do dataset oficial.

Implementa as verificações da Seção 13 da metodologia sobre o dataset já
consolidado (`data/processed/trials.csv`), sem alterar nenhuma fonte bruta.
Achados críticos indicam que o dataset não deve ser usado nas análises de
RQ1-RQ3; achados de aviso/informação documentam lacunas já conhecidas e
toleradas pela metodologia (campos ausentes nunca viram zero).
"""
from __future__ import annotations

import csv
import json
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.collection.allocation import AllocationRow, read_allocation
from src.processing.dataset_builder import DATASET_COLUMNS, BuildResult, build_dataset

ROOT = Path(__file__).resolve().parents[2]

CRITICAL = "critical"
WARNING = "warning"
INFO = "info"

BOOLEAN_FIELDS = ("completed", "censored", "incident_flag", "quality_note_applied")
NUMERIC_FIELDS = (
    "order_position",
    "duration_seconds",
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
)
STRUCTURAL_METRIC_FIELDS = (
    "function_count",
    "mean_cyclomatic_complexity",
    "max_cyclomatic_complexity",
    "duplicated_lines",
    "duplication_percentage",
    "loc",
    "maintainability_index",
)
OUTLIER_FIELDS = ("duration_seconds", "mean_cyclomatic_complexity", "duplication_percentage", "loc")
_PATH_FIELDS = frozenset(
    {
        "trial_record_path",
        "junit_report_path",
        "metrics_record_path",
        "trial_config_path",
        "data_quality_note_path",
        "prompt_log_path",
        "commit_subject",
    }
)
EXPECTED_TRIAL_COUNT = 18
TRIALS_PER_PARTICIPANT = 6
TRIALS_PER_TREATMENT_PER_PARTICIPANT = 3
OBSERVATIONS_PER_KATA = 3
DURATION_LIMIT_SECONDS = 2100


@dataclass(frozen=True)
class Finding:
    """Um achado de validação, no espírito de `ConsolidationError`."""

    severity: str
    rule: str
    trial_id: str | None
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "rule": self.rule,
            "trial_id": self.trial_id or "",
            "message": self.message,
        }


@dataclass(frozen=True)
class PairSummary:
    participant_id: str
    difficulty_block: str
    ai_trial_id: str | None
    manual_trial_id: str | None
    valid: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
    findings: list[Finding]
    row_count: int
    pairs: list[PairSummary]

    @property
    def critical(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == CRITICAL]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == WARNING]

    @property
    def infos(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == INFO]

    @property
    def authorized(self) -> bool:
        """Se o dataset pode seguir para as análises de RQ1-RQ3."""
        return not self.critical


def _typed_value(field_name: str, raw: str | None) -> Any:
    if raw is None or raw == "":
        return None
    if field_name in BOOLEAN_FIELDS:
        return raw == "true"
    if field_name in NUMERIC_FIELDS:
        try:
            return int(raw)
        except ValueError:
            return float(raw)
    return raw


def load_dataset_csv(path: Path) -> list[dict[str, Any]]:
    """Lê o dataset oficial e devolve valores tipados (espelha `_csv_value`)."""
    with Path(path).open(encoding="utf-8", newline="") as file:
        raw_rows = list(csv.DictReader(file))
    rows = []
    for raw_row in raw_rows:
        rows.append({field: _typed_value(field, raw_row.get(field)) for field in DATASET_COLUMNS})
    return rows


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _check_cardinality(rows: list[dict[str, Any]], findings: list[Finding]) -> None:
    ids = [row["trial_id"] for row in rows]
    if len(rows) != EXPECTED_TRIAL_COUNT:
        findings.append(
            Finding(CRITICAL, "cardinality_total", None, f"O dataset deve ter exatamente {EXPECTED_TRIAL_COUNT} trials; encontrados {len(rows)}.")
        )
    for trial_id, count in Counter(ids).items():
        if count > 1:
            findings.append(Finding(CRITICAL, "cardinality_unique_id", trial_id, f"trial_id duplicado {count}x no dataset."))

    by_participant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_participant[row["participant_id"]].append(row)
    for participant_id, participant_rows in sorted(by_participant.items()):
        if len(participant_rows) != TRIALS_PER_PARTICIPANT:
            findings.append(
                Finding(CRITICAL, "cardinality_per_participant", participant_id, f"Esperados {TRIALS_PER_PARTICIPANT} trials; encontrados {len(participant_rows)}.")
            )
        treatment_counts = Counter(row["treatment"] for row in participant_rows)
        for treatment in ("ai", "manual"):
            if treatment_counts.get(treatment, 0) != TRIALS_PER_TREATMENT_PER_PARTICIPANT:
                findings.append(
                    Finding(
                        CRITICAL,
                        "treatment_balance_per_participant",
                        participant_id,
                        f"Esperados {TRIALS_PER_TREATMENT_PER_PARTICIPANT} trials '{treatment}'; encontrados {treatment_counts.get(treatment, 0)}.",
                    )
                )

    by_kata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_kata[row["kata_id"]].append(row)
    for kata_id, kata_rows in sorted(by_kata.items()):
        if len(kata_rows) != OBSERVATIONS_PER_KATA:
            findings.append(
                Finding(CRITICAL, "kata_observations", kata_id, f"Esperadas {OBSERVATIONS_PER_KATA} observações; encontradas {len(kata_rows)}.")
            )
        treatments_present = {row["treatment"] for row in kata_rows}
        missing = {"ai", "manual"} - treatments_present
        if missing:
            findings.append(
                Finding(CRITICAL, "kata_treatment_coverage", kata_id, f"Tratamento(s) ausente(s) no conjunto do grupo: {sorted(missing)}.")
            )


def _check_allocation_consistency(
    rows: list[dict[str, Any]], allocation_rows: list[AllocationRow], findings: list[Finding]
) -> None:
    allocation_by_id = {row.trial_id: row for row in allocation_rows}
    dataset_ids = {row["trial_id"] for row in rows}
    for trial_id in allocation_by_id:
        if trial_id not in dataset_ids:
            findings.append(Finding(CRITICAL, "allocation_missing_row", trial_id, "Trial da alocação congelada não aparece no dataset."))

    for row in rows:
        trial_id = row["trial_id"]
        allocation = allocation_by_id.get(trial_id)
        if allocation is None:
            findings.append(Finding(CRITICAL, "allocation_unknown_trial", trial_id, "trial_id não existe na alocação congelada."))
            continue
        expected = {
            "participant_id": allocation.participant_id,
            "kata_id": allocation.kata_id,
            "difficulty_block": allocation.difficulty_block,
            "order_position": allocation.order_position,
            "treatment": allocation.treatment,
        }
        for field_name, expected_value in expected.items():
            if row.get(field_name) != expected_value:
                findings.append(
                    Finding(
                        CRITICAL,
                        "allocation_mismatch",
                        trial_id,
                        f"'{field_name}'={row.get(field_name)!r} diverge da alocação congelada ({expected_value!r}).",
                    )
                )


def _check_row_rules(row: dict[str, Any], findings: list[Finding]) -> None:
    trial_id = row["trial_id"]
    duration = row.get("duration_seconds")
    censored = row.get("censored")
    completed = row.get("completed")
    passed = row.get("passed_tests")
    failed = row.get("failed_tests")
    total = row.get("total_tests")
    success_rate = row.get("success_rate")

    if duration is not None and not (0 <= duration <= DURATION_LIMIT_SECONDS):
        findings.append(Finding(CRITICAL, "duration_range", trial_id, f"duration_seconds={duration} fora de [0, {DURATION_LIMIT_SECONDS}]."))

    if censored is True:
        if duration != DURATION_LIMIT_SECONDS:
            findings.append(Finding(CRITICAL, "censored_duration", trial_id, f"censored=true exige duration_seconds={DURATION_LIMIT_SECONDS}; encontrado {duration!r}."))
        if completed is not False:
            findings.append(Finding(CRITICAL, "censored_completed", trial_id, f"censored=true exige completed=false; encontrado {completed!r}."))

    if completed is True:
        if failed is not None and failed != 0:
            findings.append(Finding(CRITICAL, "completed_failed_tests", trial_id, f"completed=true exige failed_tests=0; encontrado {failed!r}."))
        if success_rate is not None and success_rate != 100:
            findings.append(Finding(CRITICAL, "completed_success_rate", trial_id, f"completed=true exige success_rate=100; encontrado {success_rate!r}."))

    if passed is not None and failed is not None and total is not None and passed + failed != total:
        findings.append(Finding(CRITICAL, "tests_sum", trial_id, f"passed_tests({passed}) + failed_tests({failed}) != total_tests({total})."))

    if success_rate is not None and not (0 <= success_rate <= 100):
        findings.append(Finding(CRITICAL, "success_rate_range", trial_id, f"success_rate={success_rate} fora de [0, 100]."))

    for field_name in STRUCTURAL_METRIC_FIELDS:
        value = row.get(field_name)
        if value is not None and value < 0:
            findings.append(Finding(CRITICAL, "structural_metric_negative", trial_id, f"'{field_name}'={value} é negativo."))

    if row.get("issue_number") is None:
        findings.append(Finding(CRITICAL, "missing_issue_link", trial_id, "Trial sem Issue vinculada."))
    if row.get("commit_sha") is None:
        findings.append(Finding(CRITICAL, "missing_commit_link", trial_id, "Trial sem commit vinculado."))


def _check_known_gaps(row: dict[str, Any], findings: list[Finding]) -> None:
    """Lacunas toleradas pela metodologia: relatadas, nunca preenchidas."""
    trial_id = row["trial_id"]
    if row.get("loc") is None:
        findings.append(Finding(WARNING, "missing_structural_metrics", trial_id, "Métricas estruturais (LOC/complexidade/duplicação) ausentes."))
    if row.get("perceived_difficulty") is None:
        findings.append(Finding(WARNING, "missing_perceived_difficulty", trial_id, "Dificuldade percebida não registrada."))
    if row.get("treatment") == "ai" and row.get("prompt_count") is None:
        findings.append(Finding(WARNING, "missing_prompt_count", trial_id, "Log de prompts não exportável para o tratamento IA."))


def _check_tool_versions(raw_metrics_root: Path, rows: list[dict[str, Any]], project_root: Path, findings: list[Finding]) -> None:
    versions_by_trial: dict[str, Any] = {}
    for row in rows:
        rel = row.get("metrics_record_path")
        if not rel:
            continue
        full_path = Path(project_root) / rel
        if not full_path.is_file():
            continue
        try:
            data = json.loads(full_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tool_versions = data.get("tool_versions")
        if tool_versions:
            versions_by_trial[row["trial_id"]] = tool_versions
    distinct = {json.dumps(value, sort_keys=True) for value in versions_by_trial.values()}
    if len(distinct) > 1:
        findings.append(
            Finding(CRITICAL, "tool_version_consistency", None, f"Versões de ferramentas divergentes entre trials: {versions_by_trial}.")
        )


def _check_acceptance_tests_unmodified(katas_root: Path, repository_root: Path, findings: list[Finding]) -> None:
    katas_root = Path(katas_root)
    if not katas_root.is_dir():
        return
    for kata_dir in sorted(path for path in katas_root.iterdir() if path.is_dir()):
        tests_dir = kata_dir / "tests"
        if not tests_dir.is_dir():
            continue
        relative = _relative_path(tests_dir, repository_root)
        try:
            result = subprocess.run(
                ["git", "-C", str(repository_root), "log", "--oneline", "--", relative],
                capture_output=True,
                text=True,
                check=True,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            findings.append(Finding(WARNING, "acceptance_tests_git_unavailable", kata_dir.name, f"Não foi possível consultar o histórico git de {relative}: {error}"))
            continue
        commit_count = len([line for line in result.stdout.splitlines() if line.strip()])
        if commit_count == 0:
            findings.append(Finding(WARNING, "acceptance_tests_no_history", kata_dir.name, f"Nenhum commit encontrado para {relative}."))
        elif commit_count > 1:
            findings.append(
                Finding(
                    CRITICAL,
                    "acceptance_tests_modified",
                    kata_dir.name,
                    f"{relative} tem {commit_count} commits; esperado exatamente 1 (testes não devem mudar após o congelamento).",
                )
            )


def _normalize(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    return value


def _check_raw_correspondence(rows: list[dict[str, Any]], rebuild: BuildResult, findings: list[Finding]) -> None:
    rebuilt_by_id = {row["trial_id"]: row for row in rebuild.rows}
    comparable_fields = [field for field in DATASET_COLUMNS if field not in _PATH_FIELDS]
    for row in rows:
        trial_id = row["trial_id"]
        expected = rebuilt_by_id.get(trial_id)
        if expected is None:
            findings.append(Finding(CRITICAL, "raw_correspondence_unknown_trial", trial_id, "trial_id não é reconstruível a partir das fontes brutas e da alocação."))
            continue
        for field_name in comparable_fields:
            actual = _normalize(row.get(field_name))
            want = _normalize(expected.get(field_name))
            if actual != want:
                findings.append(
                    Finding(
                        CRITICAL,
                        "raw_correspondence_mismatch",
                        trial_id,
                        f"'{field_name}' no dataset ({actual!r}) diverge do recalculado a partir das fontes brutas ({want!r}).",
                    )
                )

    for error in rebuild.errors:
        if error.severity == "error":
            findings.append(
                Finding(CRITICAL, f"raw_evidence_{error.code}", error.trial_id, error.message)
            )


def _detect_outliers(rows: list[dict[str, Any]], findings: list[Finding]) -> list[dict[str, Any]]:
    outliers: list[dict[str, Any]] = []
    for field_name in OUTLIER_FIELDS:
        pairs = [(row["trial_id"], row[field_name]) for row in rows if row.get(field_name) is not None]
        values = sorted(value for _, value in pairs)
        if len(values) < 4:
            continue
        q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
        iqr = q3 - q1
        if iqr == 0:
            # Sem dispersão na maioria dos valores: qualquer desvio do valor
            # comum já é notável, então o intervalo colapsa nesse ponto.
            low = high = statistics.median(values)
        else:
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        for trial_id, value in pairs:
            if value < low or value > high:
                record = {"trial_id": trial_id, "field": field_name, "value": value, "low": round(low, 2), "high": round(high, 2)}
                outliers.append(record)
                findings.append(
                    Finding(
                        INFO,
                        "outlier_detected",
                        trial_id,
                        f"'{field_name}'={value} fora de [{low:.2f}, {high:.2f}] (IQR); mantido sem remoção automática.",
                    )
                )
    return outliers


def _build_pairs(rows: list[dict[str, Any]], findings: list[Finding]) -> list[PairSummary]:
    by_key: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_key[(row["participant_id"], row["difficulty_block"])][row["treatment"]] = row

    pairs: list[PairSummary] = []
    for (participant_id, block), treatments in sorted(by_key.items()):
        ai_row = treatments.get("ai")
        manual_row = treatments.get("manual")
        reasons: list[str] = []
        if ai_row is None:
            reasons.append("trial 'ai' ausente no par")
        if manual_row is None:
            reasons.append("trial 'manual' ausente no par")
        for row, label in ((ai_row, "ai"), (manual_row, "manual")):
            if row is not None and row.get("duration_seconds") is None:
                reasons.append(f"duration_seconds ausente ({label})")
        valid = not reasons
        pairs.append(
            PairSummary(
                participant_id=participant_id,
                difficulty_block=block,
                ai_trial_id=ai_row["trial_id"] if ai_row else None,
                manual_trial_id=manual_row["trial_id"] if manual_row else None,
                valid=valid,
                reasons=tuple(reasons),
            )
        )
        if not valid:
            findings.append(Finding(WARNING, "invalid_pair", f"{participant_id}-{block}", "; ".join(reasons)))
    return pairs


def validate_dataset(
    rows: list[dict[str, Any]],
    *,
    allocation_path: Path = ROOT / "data" / "metadata" / "allocation.csv",
    raw_trials_root: Path = ROOT / "data" / "raw" / "trials",
    raw_metrics_root: Path = ROOT / "data" / "raw" / "metrics",
    trials_root: Path = ROOT / "trials",
    katas_root: Path = ROOT / "katas",
    project_root: Path = ROOT,
    repository_root: Path | None = None,
    rebuild: BuildResult | None = None,
) -> ValidationResult:
    """Executa todas as regras da Seção 13 sobre `rows` (dataset oficial)."""
    findings: list[Finding] = []
    repository_root = repository_root or Path(project_root).parent

    _check_cardinality(rows, findings)
    allocation_rows = read_allocation(Path(allocation_path))
    _check_allocation_consistency(rows, allocation_rows, findings)

    for row in rows:
        _check_row_rules(row, findings)
        _check_known_gaps(row, findings)

    _check_tool_versions(raw_metrics_root, rows, project_root, findings)
    _check_acceptance_tests_unmodified(katas_root, repository_root, findings)

    if rebuild is None:
        rebuild = build_dataset(
            allocation_path=allocation_path,
            raw_trials_root=raw_trials_root,
            raw_metrics_root=raw_metrics_root,
            trials_root=trials_root,
            project_root=project_root,
        )
    _check_raw_correspondence(rows, rebuild, findings)

    _detect_outliers(rows, findings)
    pairs = _build_pairs(rows, findings)

    return ValidationResult(findings=findings, row_count=len(rows), pairs=pairs)
