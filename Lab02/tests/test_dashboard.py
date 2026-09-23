"""Contrato de exportação e bloqueio de datasets não autorizados."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dashboard import figures  # noqa: E402
from src.analysis.data_loading import DatasetNotAuthorizedError  # noqa: E402


def _rows() -> list[dict]:
    rows = []
    for participant in ("P01", "P02", "P03"):
        for block in ("B1", "B2", "B3"):
            for treatment in ("ai", "manual"):
                trial_id = f"{participant}-{block}-{treatment}"
                rows.append({"trial_id": trial_id, "participant_id": participant,
                             "difficulty_block": block, "kata_id": "K01", "treatment": treatment,
                             "duration_seconds": 2100 if trial_id == "P01-B1-ai" else 100,
                             "censored": trial_id == "P01-B1-ai", "completed": trial_id != "P01-B1-ai",
                             "success_rate": 0 if trial_id == "P01-B1-ai" else 100,
                             "passed_tests": 0 if trial_id == "P01-B1-ai" else 5,
                             "total_tests": 5,
                             "mean_cyclomatic_complexity": None if participant == "P01" else 3,
                             "duplication_percentage": None if participant == "P01" else 0,
                             "loc": None if participant == "P01" else 20})
    return rows


def test_exporta_todos_os_trials_e_pares_com_censura_e_ausencia(tmp_path: Path):
    paths = figures.render_dashboard(_rows(), tmp_path)
    assert len(paths) == 12
    assert all(path.stat().st_size > 0 for path in paths)
    with (tmp_path / "trial-points.csv").open(encoding="utf-8", newline="") as file:
        trials = list(csv.DictReader(file))
    with (tmp_path / "paired-points.csv").open(encoding="utf-8", newline="") as file:
        pairs = list(csv.DictReader(file))
    assert len(trials) == 18
    assert len({row["trial_id"] for row in trials}) == 18
    assert len(pairs) == 9 * len(figures.METRICS)
    assert next(row for row in trials if row["trial_id"] == "P01-B1-ai")["censored"] == "True"
    assert next(row for row in pairs if row["metric"] == "loc" and row["participant_id"] == "P01")["ai_value"] == ""
    assert "12/18 com métricas estruturais" in (tmp_path / "index.html").read_text(encoding="utf-8")


def test_validacao_falha_antes_de_criar_saida(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def reject(_dataset):
        raise DatasetNotAuthorizedError("dataset inválido")

    monkeypatch.setattr(figures, "load_validated_dataset", reject)
    output = tmp_path / "dashboard"
    with pytest.raises(DatasetNotAuthorizedError):
        figures.generate(tmp_path / "trials.csv", output)
    assert not output.exists()
