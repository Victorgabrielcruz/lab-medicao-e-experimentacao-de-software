from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.collection.allocation import generate_allocation, serialize_csv
from src.collection.trial_preparation import TrialPreparationError, prepare_trial


def _fixture_roots(tmp_path: Path, row_index: int = 0):
    rows = generate_allocation()
    row = rows[row_index]
    allocation = tmp_path / "allocation.csv"
    allocation.write_text(serialize_csv(rows), encoding="utf-8")
    katas = tmp_path / "katas"
    source = katas / row.kata_id / "src"
    source.mkdir(parents=True)
    (source / "solution.py").write_text("raise NotImplementedError\n", encoding="utf-8")
    (katas / row.kata_id / "README.md").write_text("# Enunciado\n", encoding="utf-8")
    return row, allocation, katas, tmp_path / "trials", tmp_path / "raw"


def test_prepara_trial_conforme_alocacao_e_registra_hash(tmp_path: Path):
    row, allocation, katas, trials, raw = _fixture_roots(tmp_path)
    target = prepare_trial(
        row.participant_id,
        row.kata_id,
        row.treatment,
        allocation_path=allocation,
        katas_root=katas,
        trials_root=trials,
        raw_root=raw,
    )

    assert target == trials / row.trial_id
    assert (target / "src/solution.py").is_file()
    assert (target / "README.md").is_file()
    config = json.loads((target / "trial-config.json").read_text(encoding="utf-8"))
    assert config["trial_id"] == row.trial_id
    assert config["treatment"] == row.treatment
    assert len(config["source_sha256"]) == 64


def test_recusa_sobrescrever_sem_restore_e_remove_residuos_com_restore(tmp_path: Path):
    row, allocation, katas, trials, raw = _fixture_roots(tmp_path)
    kwargs = dict(
        allocation_path=allocation,
        katas_root=katas,
        trials_root=trials,
        raw_root=raw,
    )
    target = prepare_trial(row.participant_id, row.kata_id, row.treatment, **kwargs)
    (target / "residuo.tmp").write_text("não pode sobreviver", encoding="utf-8")
    (target / "src/solution.py").write_text("alterado", encoding="utf-8")

    with pytest.raises(TrialPreparationError, match="--restore"):
        prepare_trial(row.participant_id, row.kata_id, row.treatment, **kwargs)

    restored = prepare_trial(
        row.participant_id, row.kata_id, row.treatment, restore=True, **kwargs
    )
    assert not (restored / "residuo.tmp").exists()
    assert (restored / "src/solution.py").read_text(encoding="utf-8") == "raise NotImplementedError\n"


def test_recusa_combinacao_fora_da_alocacao(tmp_path: Path):
    row, allocation, katas, trials, raw = _fixture_roots(tmp_path)
    wrong = "manual" if row.treatment == "ai" else "ai"
    with pytest.raises(TrialPreparationError, match="ausente da alocação"):
        prepare_trial(
            row.participant_id,
            row.kata_id,
            wrong,
            allocation_path=allocation,
            katas_root=katas,
            trials_root=trials,
            raw_root=raw,
        )


def test_recusa_restauracao_de_trial_com_evidencia_bruta(tmp_path: Path):
    row, allocation, katas, trials, raw = _fixture_roots(tmp_path)
    evidence = raw / row.trial_id
    evidence.mkdir(parents=True)
    (evidence / "trial.json").write_text("{}", encoding="utf-8")
    with pytest.raises(TrialPreparationError, match="evidência bruta"):
        prepare_trial(
            row.participant_id,
            row.kata_id,
            row.treatment,
            allocation_path=allocation,
            katas_root=katas,
            trials_root=trials,
            raw_root=raw,
            restore=True,
        )
