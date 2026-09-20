from __future__ import annotations

import copy
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.collection.allocation import read_allocation
from src.processing.dataset_builder import DATASET_COLUMNS, BuildResult
from src.validation.dataset_validator import load_dataset_csv, validate_dataset
from src.validation.report import render_report_markdown

MISSING_ROOT = ROOT / "tests" / "_does-not-exist"


def _base_rows() -> list[dict]:
    """18 linhas internamente consistentes, alinhadas à alocação congelada real."""
    rows = []
    for allocation in read_allocation(ROOT / "data/metadata/allocation.csv"):
        rows.append(
            {
                "trial_id": allocation.trial_id,
                "participant_id": allocation.participant_id,
                "kata_id": allocation.kata_id,
                "difficulty_block": allocation.difficulty_block,
                "order_position": allocation.order_position,
                "treatment": allocation.treatment,
                "started_at": "2026-09-15T10:00:00-03:00",
                "finished_at": "2026-09-15T10:05:00-03:00",
                "duration_seconds": 300,
                "completed": True,
                "censored": False,
                "passed_tests": 5,
                "failed_tests": 0,
                "total_tests": 5,
                "success_rate": 100.0,
                "function_count": 2,
                "mean_cyclomatic_complexity": 3.0,
                "max_cyclomatic_complexity": 5,
                "duplicated_lines": 0,
                "duplication_percentage": 0.0,
                "loc": 20,
                "maintainability_index": 80.0,
                "prompt_count": 1 if allocation.treatment == "ai" else None,
                "perceived_difficulty": None,
                "incident_flag": False,
                "issue_number": "1",
                "commit_sha": "a" * 40,
                "trial_record_path": None,
                "junit_report_path": None,
                "metrics_record_path": None,
                "trial_config_path": None,
                "data_quality_note_path": None,
                "prompt_log_path": None,
                "commit_subject": None,
                "quality_note_applied": False,
            }
        )
    return rows


def _validate(rows: list[dict], *, rebuild_rows: list[dict] | None = None):
    rebuild = BuildResult(rows=copy.deepcopy(rebuild_rows if rebuild_rows is not None else rows), errors=[])
    return validate_dataset(
        rows,
        allocation_path=ROOT / "data/metadata/allocation.csv",
        raw_trials_root=MISSING_ROOT,
        raw_metrics_root=MISSING_ROOT,
        trials_root=MISSING_ROOT,
        katas_root=MISSING_ROOT,
        project_root=ROOT,
        rebuild=rebuild,
    )


def _mutate(rows: list[dict], trial_id: str, **changes) -> list[dict]:
    updated = copy.deepcopy(rows)
    for row in updated:
        if row["trial_id"] == trial_id:
            row.update(changes)
    return updated


def test_dataset_consistente_nao_gera_erros_criticos():
    result = _validate(_base_rows())
    assert result.authorized
    assert result.critical == []
    assert len(result.pairs) == 9
    assert all(pair.valid for pair in result.pairs)


def test_cardinalidade_detecta_duplicata_e_total_incorreto():
    rows = _base_rows()
    rows.append(copy.deepcopy(rows[0]))
    result = _validate(rows, rebuild_rows=rows)
    codes = {finding.rule for finding in result.critical}
    assert "cardinality_total" in codes
    assert "cardinality_unique_id" in codes
    assert not result.authorized


def test_censurado_exige_duracao_maxima_e_nao_concluido():
    rows = _mutate(_base_rows(), "P01-K01-ai", censored=True, completed=False, duration_seconds=300, failed_tests=5, success_rate=0.0)
    result = _validate(rows)
    assert any(f.rule == "censored_duration" and f.trial_id == "P01-K01-ai" for f in result.critical)


def test_concluido_exige_zero_falhas_e_taxa_cem():
    rows = _mutate(_base_rows(), "P01-K01-ai", failed_tests=1, passed_tests=4, success_rate=80.0)
    result = _validate(rows)
    codes = {(f.rule, f.trial_id) for f in result.critical}
    assert ("completed_failed_tests", "P01-K01-ai") in codes
    assert ("completed_success_rate", "P01-K01-ai") in codes


def test_soma_de_testes_e_faixa_da_taxa_de_sucesso():
    rows = _mutate(_base_rows(), "P01-K01-ai", passed_tests=3, failed_tests=1, total_tests=5, success_rate=150.0, completed=False)
    result = _validate(rows)
    codes = {f.rule for f in result.critical}
    assert "tests_sum" in codes
    assert "success_rate_range" in codes


def test_metrica_estrutural_negativa_e_critica():
    rows = _mutate(_base_rows(), "P01-K01-ai", loc=-1)
    result = _validate(rows)
    assert any(f.rule == "structural_metric_negative" and f.trial_id == "P01-K01-ai" for f in result.critical)


def test_falta_de_issue_ou_commit_e_critica():
    rows = _mutate(_base_rows(), "P01-K01-ai", issue_number=None, commit_sha=None)
    result = _validate(rows)
    codes = {f.rule for f in result.critical}
    assert "missing_issue_link" in codes
    assert "missing_commit_link" in codes


def test_lacunas_conhecidas_da_metodologia_sao_avisos_nao_criticos():
    rows = _mutate(_base_rows(), "P01-K01-ai", loc=None, function_count=None, mean_cyclomatic_complexity=None, max_cyclomatic_complexity=None, duplicated_lines=None, duplication_percentage=None, maintainability_index=None, prompt_count=None)
    result = _validate(rows)
    warning_codes = {f.rule for f in result.warnings if f.trial_id == "P01-K01-ai"}
    assert "missing_structural_metrics" in warning_codes
    assert "missing_prompt_count" in warning_codes
    assert result.authorized


def test_divergencia_entre_dataset_e_fontes_brutas_e_critica():
    """Reproduz o defeito real encontrado no dataset oficial: uma linha ficou
    obsoleta em relação às evidências brutas depois de um merge desatualizado."""
    rows = _base_rows()
    stale_row = copy.deepcopy(rows)
    stale_row = _mutate(stale_row, "P02-K01-ai", duration_seconds=None, loc=None, issue_number=None, commit_sha=None, completed=None, passed_tests=None, failed_tests=None, total_tests=None, success_rate=None)

    result = _validate(stale_row, rebuild_rows=rows)

    assert not result.authorized
    mismatched_fields = {f.message.split("'")[1] for f in result.critical if f.rule == "raw_correspondence_mismatch" and f.trial_id == "P02-K01-ai"}
    assert "duration_seconds" in mismatched_fields
    assert "loc" in mismatched_fields


def test_outlier_e_reportado_sem_bloquear_a_autorizacao():
    rows = _mutate(_base_rows(), "P01-K01-ai", duration_seconds=2000)
    result = _validate(rows, rebuild_rows=rows)
    assert any(f.rule == "outlier_detected" and f.trial_id == "P01-K01-ai" for f in result.infos)
    assert not any(f.trial_id == "P01-K01-ai" and f.severity == "critical" for f in result.findings)
    assert result.authorized


def test_par_invalido_quando_falta_um_tratamento_no_bloco():
    rows = [row for row in _base_rows() if row["trial_id"] != "P01-K02-manual"]
    result = _validate(rows, rebuild_rows=rows)
    invalid_pairs = [pair for pair in result.pairs if not pair.valid]
    assert len(invalid_pairs) == 1
    assert invalid_pairs[0].participant_id == "P01"
    assert invalid_pairs[0].difficulty_block == "B1"
    assert any(f.rule == "invalid_pair" for f in result.warnings)


def test_load_dataset_csv_tipa_valores_corretamente(tmp_path: Path):
    dataset_path = tmp_path / "trials.csv"
    with dataset_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        row = {field: "" for field in DATASET_COLUMNS}
        row.update(
            {
                "trial_id": "P01-K01-ai",
                "duration_seconds": "300",
                "success_rate": "100.0",
                "completed": "true",
                "censored": "false",
                "issue_number": "70",
            }
        )
        writer.writerow(row)

    rows = load_dataset_csv(dataset_path)
    assert len(rows) == 1
    assert rows[0]["duration_seconds"] == 300
    assert rows[0]["success_rate"] == 100.0
    assert rows[0]["completed"] is True
    assert rows[0]["censored"] is False
    assert rows[0]["issue_number"] == "70"
    assert rows[0]["loc"] is None


def test_relatorio_markdown_reflete_veredito_e_secoes():
    result = _validate(_base_rows())
    report = render_report_markdown(result, dataset_path="data/processed/trials.csv")
    assert "AUTORIZADO" in report
    assert "## 1. Erros críticos" in report
    assert "## 4. Pares válidos por participante e bloco de dificuldade" in report


def test_dataset_oficial_do_repositorio_esta_autorizado():
    """Regressão: o dataset em data/processed/trials.csv deve validar sem
    erros críticos. Isso já pegou uma consolidação obsoleta em produção."""
    rows = load_dataset_csv(ROOT / "data/processed/trials.csv")
    result = validate_dataset(rows, project_root=ROOT)
    assert result.row_count == 18
    assert result.critical == []
    assert result.authorized
