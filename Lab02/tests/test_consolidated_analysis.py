"""Verificações dos cálculos e da rastreabilidade da análise consolidada."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.consolidated import analyze, load_trials, run, wilcoxon_exact  # noqa: E402


def test_wilcoxon_exato_e_empates():
    unilateral = wilcoxon_exact([1, 2, 3], "greater")
    assert unilateral["p_value"] == pytest.approx(0.125)
    assert unilateral["rank_biserial"] == pytest.approx(1)
    assert wilcoxon_exact([1, 2, 3], "two-sided")["p_value"] == pytest.approx(0.25)

    tied = wilcoxon_exact([0, 1, -1], "two-sided")
    assert tied["n_ties"] == 1
    assert tied["n_nonzero"] == 2
    assert tied["p_value"] == pytest.approx(1)
    assert tied["rank_biserial"] == pytest.approx(0)

    zeros = wilcoxon_exact([0, 0], "greater")
    assert zeros["p_value"] is None
    assert zeros["rank_biserial"] is None


def test_holm_usa_os_dois_desfechos_estruturais():
    trials = []
    for participant in ("P01", "P02", "P03"):
        for treatment, cc, duplication in (("manual", 2, 0), ("ai", 3, 1)):
            trials.append({"participant_id": participant, "difficulty_block": "B1",
                           "trial_id": f"{participant}-{treatment}", "treatment": treatment,
                           "values": {"mean_cyclomatic_complexity": cc,
                                      "duplication_percentage": duplication}})
    rows, comparisons = analyze(trials)
    for name in ("mean_cyclomatic_complexity", "duplication_percentage"):
        assert comparisons[name]["p_value"] == pytest.approx(0.25)
        assert comparisons[name]["p_holm"] == pytest.approx(0.5)
        exported = next(row for row in rows if row["row_type"] == "comparison"
                        and row["metric"] == name)
        assert exported["p_holm"] == "0.5000"


def test_holm_com_desfecho_todo_empatado_preserva_dois_testes():
    trials = []
    for participant in ("P01", "P02", "P03"):
        for treatment, cc in (("manual", 2), ("ai", 3)):
            trials.append({"participant_id": participant, "difficulty_block": "B1",
                           "trial_id": f"{participant}-{treatment}", "treatment": treatment,
                           "values": {"mean_cyclomatic_complexity": cc,
                                      "duplication_percentage": 0}})
    _, comparisons = analyze(trials)
    raw_p = comparisons["mean_cyclomatic_complexity"]["p_value"]
    assert comparisons["duplication_percentage"]["p_value"] is None
    assert comparisons["mean_cyclomatic_complexity"]["p_holm"] == min(1, 2 * raw_p)


def test_correcao_documentada_e_reexecucao_deterministica(tmp_path: Path):
    metadata = tmp_path / "data/metadata"
    metadata.mkdir(parents=True)
    with (metadata / "allocation.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("trial_id", "participant_id", "kata_id",
                                                    "difficulty_block", "order_position", "treatment"))
        writer.writeheader()
        writer.writerows((
            {"trial_id": "P01-K01-manual", "participant_id": "P01", "kata_id": "K01",
             "difficulty_block": "B1", "order_position": "1", "treatment": "manual"},
            {"trial_id": "P01-K02-ai", "participant_id": "P01", "kata_id": "K02",
             "difficulty_block": "B1", "order_position": "2", "treatment": "ai"},
        ))
    for trial_id, kata, treatment, duration in (("P01-K01-manual", "K01", "manual", 200),
                                                 ("P01-K02-ai", "K02", "ai", 100)):
        raw_dir = tmp_path / "data/raw/trials" / trial_id
        raw_dir.mkdir(parents=True)
        raw = {"trial_id": trial_id, "participant_id": "P01", "kata_id": kata,
               "treatment": treatment, "duration_seconds": duration,
               "completed": True, "censored": False, "total_tests": 5,
               "passed_tests": 5, "failed_tests": 0, "success_rate": 100.0}
        if treatment == "manual":
            raw.update(passed_tests=0, failed_tests=5, success_rate=0.0,
                       attempts=[{"note": "poll", "total_tests": 5,
                                  "passed_tests": 5, "failed_tests": 0}])
            correction = {field: value for field, value in raw.items()
                          if field in ("completed", "censored", "duration_seconds", "total_tests")}
            correction.update(passed_tests=5, failed_tests=0, success_rate=100.0)
            (raw_dir / "data-quality-note.json").write_text(json.dumps({
                "trial_id": trial_id, "corrected_interpretation": correction,
            }), encoding="utf-8")
        failures = 5 if treatment == "manual" else 0
        (raw_dir / "final_junit.xml").write_text(
            f'<testsuite tests="5" failures="{failures}" errors="0" skipped="0"/>',
            encoding="utf-8")
        (raw_dir / "trial.json").write_text(json.dumps(raw), encoding="utf-8")

    trials, warnings = load_trials(tmp_path)
    assert len(trials) == 2
    assert trials[0]["values"]["success_rate"] == 100.0
    assert any("correção auditada" in warning for warning in warnings)
    assert any("relatório final de testes registra 0/5" in warning for warning in warnings)
    rows, comparisons = analyze(trials)
    assert comparisons["duration_seconds"]["n_pairs"] == 1
    assert comparisons["duration_seconds"]["difference"] == 100
    assert comparisons["success_rate"]["n_ties"] == 1
    assert next(row for row in rows if row["row_type"] == "pair"
                and row["metric"] == "duration_seconds")["difference"] == "100.0000"

    run(tmp_path)
    csv_path = tmp_path / "data/processed/statistical-results.csv"
    report_path = tmp_path / "reports/drafts/rq-answers.md"
    first = csv_path.read_bytes(), report_path.read_bytes()
    run(tmp_path)
    assert first == (csv_path.read_bytes(), report_path.read_bytes())


def test_trial_ausente_nao_produz_par_ou_metrica(tmp_path: Path):
    metadata = tmp_path / "data/metadata"
    metadata.mkdir(parents=True)
    (metadata / "allocation.csv").write_text(
        "trial_id,participant_id,kata_id,difficulty_block,treatment\n"
        "P01-K01-manual,P01,K01,B1,manual\n"
        "P01-K02-ai,P01,K02,B1,ai\n", encoding="utf-8")
    metric_dir = tmp_path / "data/raw/metrics/P01-K02-ai"
    metric_dir.mkdir(parents=True)
    (metric_dir / "metrics.json").write_text(json.dumps({
        "trial_id": "P01-K02-ai", "complexity": {"mean_cyclomatic_complexity": 4}
    }), encoding="utf-8")
    trials, warnings = load_trials(tmp_path)
    assert len(trials) == 2
    assert all(not trial["values"] for trial in trials)
    assert len(warnings) == 2
    _, comparisons = analyze(trials)
    assert comparisons["duration_seconds"]["n_pairs"] == 0
    assert comparisons["mean_cyclomatic_complexity"]["n_pairs"] == 0
