from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.paired_stats import (
    build_pairs,
    describe_treatment,
    holm_correction,
    wilcoxon_signed_rank,
)


def _row(trial_id, participant, block, treatment, **fields):
    row = {
        "trial_id": trial_id,
        "participant_id": participant,
        "difficulty_block": block,
        "treatment": treatment,
        "completed": True,
    }
    row.update(fields)
    return row


def test_build_pairs_forma_nove_pares_por_participante_e_bloco():
    rows = [
        _row("P01-K01-ai", "P01", "B1", "ai", duration_seconds=100),
        _row("P01-K02-manual", "P01", "B1", "manual", duration_seconds=200),
    ]
    pairs = build_pairs(rows, "duration_seconds")
    assert len(pairs) == 1
    pair = pairs[0]
    assert pair.valid
    assert pair.ai_value == 100
    assert pair.manual_value == 200
    assert pair.difference == 100


def test_par_com_lado_ausente_nao_e_valido_e_nao_vira_zero():
    rows = [_row("P01-K01-ai", "P01", "B1", "ai", loc=20)]
    pairs = build_pairs(rows, "loc")
    assert len(pairs) == 1
    assert pairs[0].manual_value is None
    assert not pairs[0].valid
    assert pairs[0].difference is None


def test_describe_treatment_reporta_mediana_iqr_e_conclusao():
    rows = [
        _row("P01-K01-ai", "P01", "B1", "ai", duration_seconds=100, completed=True),
        _row("P02-K01-ai", "P02", "B1", "ai", duration_seconds=200, completed=True),
        _row("P03-K02-ai", "P03", "B1", "ai", duration_seconds=None, completed=False),
    ]
    stats = describe_treatment(rows, "duration_seconds", "ai")
    assert stats.n == 3
    assert stats.median == 150
    assert stats.missing == 1
    assert stats.completed == 2
    assert stats.completed_pct == round(2 / 3 * 100, 2)


def test_wilcoxon_detecta_reducao_consistente_com_ia():
    # manual sempre mais lento que ia em todos os 9 pares -> diferença positiva
    rows = []
    for index, (participant, block) in enumerate(
        [(p, b) for p in ("P01", "P02", "P03") for b in ("B1", "B2", "B3")]
    ):
        rows.append(_row(f"{participant}-{block}-ai", participant, block, "ai", duration_seconds=100 + index))
        rows.append(_row(f"{participant}-{block}-manual", participant, block, "manual", duration_seconds=400 + index))

    pairs = build_pairs(rows, "duration_seconds")
    result = wilcoxon_signed_rank(pairs, alternative="greater")

    assert result.n_pairs == 9
    assert result.n_missing_pairs == 0
    assert result.median_diff == 300
    assert result.p_value is not None and result.p_value < 0.05
    assert result.effect_size_r == 1.0
    assert result.ci_low is not None and result.ci_high is not None


def test_wilcoxon_ignora_pares_ausentes_e_reporta_contagem():
    rows = [
        _row("P01-K01-ai", "P01", "B1", "ai", loc=20),
        _row("P01-K02-manual", "P01", "B1", "manual", loc=30),
        _row("P02-K01-ai", "P02", "B1", "ai", loc=None),  # métrica estrutural ausente
        _row("P02-K02-manual", "P02", "B1", "manual", loc=40),
    ]
    pairs = build_pairs(rows, "loc")
    result = wilcoxon_signed_rank(pairs, alternative="two-sided")
    assert result.n_pairs == 1
    assert result.n_missing_pairs == 1


def test_holm_correction_preserva_ordem_e_e_monotonica():
    adjusted = holm_correction([0.01, 0.04])
    assert adjusted[0] == 0.02
    assert adjusted[1] == 0.04

    # Empate no menor p-valor não pode gerar um ajustado menor que o do maior.
    adjusted_equal = holm_correction([0.03, 0.03])
    assert adjusted_equal[0] == adjusted_equal[1] == 0.06
