from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.collection.allocation import AllocationRow
from src.processing.dataset_builder import (
    DATASET_COLUMNS,
    build_dataset,
    consolidate_trial,
    write_build_result,
)


def allocation(trial_id: str = "P01-K01-ai") -> AllocationRow:
    return AllocationRow(
        trial_id=trial_id,
        participant_id="P01",
        kata_id="K01",
        difficulty_block="B1",
        order_position=1,
        treatment="ai",
    )


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_consolida_dados_e_metricas_sem_perder_rastreabilidade(tmp_path: Path):
    trial = allocation()
    raw_trials = tmp_path / "data/raw/trials"
    raw_metrics = tmp_path / "data/raw/metrics"
    trials = tmp_path / "trials"
    write_json(
        raw_trials / trial.trial_id / "trial.json",
        {
            "trial_id": trial.trial_id,
            "started_at": "2026-09-15T10:00:00-03:00",
            "finished_at": "2026-09-15T10:03:00-03:00",
            "duration_seconds": 180,
            "completed": True,
            "censored": False,
            "passed_tests": 4,
            "failed_tests": 0,
            "total_tests": 4,
            "incident_flag": False,
        },
    )
    (raw_trials / trial.trial_id / "final_junit.xml").write_text(
        '<testsuites><testsuite tests="4" failures="0" errors="0" skipped="0" /></testsuites>',
        encoding="utf-8",
    )
    (raw_trials / trial.trial_id / "prompts.md").write_text(
        "## Prompt 1\n\ntexto\n\n## Prompt 2\n\ntexto\n", encoding="utf-8"
    )
    write_json(
        raw_metrics / trial.trial_id / "metrics.json",
        {
            "trial_id": trial.trial_id,
            "complexity": {
                "function_count": 2,
                "mean_cyclomatic_complexity": 3.5,
                "max_cyclomatic_complexity": 5,
                "missing": False,
            },
            "duplication": {"duplicated_lines": 2, "duplication_percentage": 4.5},
            "loc": {"loc": 20},
            "maintainability": {"maintainability_index": 81.25},
        },
    )
    write_json(trials / trial.trial_id / "trial-config.json", {"trial_id": trial.trial_id})

    row, errors = consolidate_trial(
        trial,
        raw_trials_root=raw_trials,
        raw_metrics_root=raw_metrics,
        trials_root=trials,
        project_root=tmp_path,
        traceability_lookup=lambda _: ("42", "a" * 40, "feat #42: preserva trial"),
    )

    assert row["success_rate"] == 100.0
    assert row["mean_cyclomatic_complexity"] == 3.5
    assert row["prompt_count"] == 2
    assert row["issue_number"] == "42"
    assert row["commit_sha"] == "a" * 40
    assert row["trial_record_path"] == "data/raw/trials/P01-K01-ai/trial.json"
    assert row["metrics_record_path"] == "data/raw/metrics/P01-K01-ai/metrics.json"
    assert not [item for item in errors if item.severity == "error"]


def test_ausencias_continuam_vazias_e_sao_relatas(tmp_path: Path):
    row, errors = consolidate_trial(
        allocation(),
        raw_trials_root=tmp_path / "data/raw/trials",
        raw_metrics_root=tmp_path / "data/raw/metrics",
        trials_root=tmp_path / "trials",
        project_root=tmp_path,
        traceability_lookup=lambda _: (None, None, None),
    )

    assert row["duration_seconds"] is None
    assert row["success_rate"] is None
    assert row["loc"] is None
    assert row["prompt_count"] is None
    assert row["issue_number"] is None
    assert {item.code for item in errors} >= {
        "missing_trial_record",
        "missing_static_metrics",
        "missing_prompt_log",
        "missing_issue_link",
        "missing_commit_link",
    }


def test_nota_de_qualidade_substitui_apenas_a_interpretacao_documentada(tmp_path: Path):
    trial = allocation("P01-K02-manual")
    trial = AllocationRow(
        trial_id=trial.trial_id,
        participant_id="P01",
        kata_id="K02",
        difficulty_block="B1",
        order_position=4,
        treatment="manual",
    )
    raw_trials = tmp_path / "data/raw/trials"
    write_json(
        raw_trials / trial.trial_id / "trial.json",
        {
            "trial_id": trial.trial_id,
            "duration_seconds": 885,
            "completed": True,
            "censored": False,
            "passed_tests": 0,
            "failed_tests": 5,
            "total_tests": 5,
            "incident_flag": False,
        },
    )
    write_json(
        raw_trials / trial.trial_id / "data-quality-note.json",
        {
            "trial_id": trial.trial_id,
            "corrected_interpretation": {
                "completed": True,
                "censored": False,
                "duration_seconds": 885,
                "passed_tests": 5,
                "failed_tests": 0,
                "total_tests": 5,
            },
        },
    )

    row, errors = consolidate_trial(
        trial,
        raw_trials_root=raw_trials,
        raw_metrics_root=tmp_path / "data/raw/metrics",
        trials_root=tmp_path / "trials",
        project_root=tmp_path,
        traceability_lookup=lambda _: ("70", "b" * 40, "fix #70"),
    )

    assert row["quality_note_applied"] is True
    assert row["passed_tests"] == 5
    assert row["failed_tests"] == 0
    assert row["success_rate"] == 100.0
    assert "quality_note_applied" in {item.code for item in errors}


def test_dataset_real_tem_dezoito_trials_unicos_e_csv_reexecutavel(tmp_path: Path):
    result = build_dataset()
    dataset_path = tmp_path / "trials.csv"
    errors_path = tmp_path / "consolidation-errors.csv"
    write_build_result(result, dataset_path, errors_path)

    assert len(result.rows) == 18
    assert len({row["trial_id"] for row in result.rows}) == 18
    assert all(set(DATASET_COLUMNS) == set(row) for row in result.rows)
    p01_k02 = next(row for row in result.rows if row["trial_id"] == "P01-K02-manual")
    assert (p01_k02["passed_tests"], p01_k02["failed_tests"], p01_k02["success_rate"]) == (5, 0, 100.0)
    p02_k01 = next(row for row in result.rows if row["trial_id"] == "P02-K01-ai")
    assert p02_k01["duration_seconds"] is None
    assert p02_k01["loc"] is None

    with dataset_path.open(encoding="utf-8", newline="") as file:
        csv_rows = list(csv.DictReader(file))
    assert len(csv_rows) == 18
    assert csv_rows[0]["trial_id"] == "P01-K01-ai"
    assert csv_rows[6]["trial_id"] == "P02-K06-manual"
    assert csv_rows[11]["duration_seconds"] == ""
    assert errors_path.is_file()
