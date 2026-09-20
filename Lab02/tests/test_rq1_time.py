from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import load_validated_dataset
from src.analysis.rq1_time import analyze, render_figures, render_report_markdown

PARTICIPANTS = ("P01", "P02", "P03")
BLOCKS = ("B1", "B2", "B3")


def _row(trial_id, participant, block, treatment, *, duration, completed, censored):
    return {
        "trial_id": trial_id,
        "participant_id": participant,
        "difficulty_block": block,
        "treatment": treatment,
        "duration_seconds": duration,
        "completed": completed,
        "censored": censored,
    }


def _synthetic_rows() -> list[dict]:
    rows = []
    for participant in PARTICIPANTS:
        for block in BLOCKS:
            rows.append(_row(f"{participant}-{block}-ai", participant, block, "ai", duration=300, completed=True, censored=False))
            rows.append(_row(f"{participant}-{block}-manual", participant, block, "manual", duration=600, completed=True, censored=False))
    return rows


def test_analyze_produz_nove_pares_e_direcao_esperada():
    result = analyze(_synthetic_rows())
    assert len(result.pairs) == 9
    assert result.wilcoxon.n_pairs == 9
    assert result.wilcoxon.median_diff == 300
    assert result.wilcoxon.p_value is not None and result.wilcoxon.p_value < 0.05


def test_trials_censurados_mantem_2100_segundos_no_resumo():
    rows = _synthetic_rows()
    rows[1]["censored"] = True
    rows[1]["completed"] = False
    rows[1]["duration_seconds"] = 2100
    result = analyze(rows)
    manual_censoring = result.censoring["manual"]
    assert manual_censoring.censored == 1
    # a duração censurada continua entrando na estatística principal (não é descartada)
    assert 2100 in [pair.manual_value for pair in result.pairs]


def test_analise_de_sensibilidade_exclui_pares_nao_concluidos():
    rows = _synthetic_rows()
    rows[1]["completed"] = False  # P01-B1 manual não concluiu
    result = analyze(rows)
    assert result.wilcoxon.n_pairs == 9
    assert result.wilcoxon_completed_only.n_pairs == 8


def test_relatorio_markdown_contem_secoes_esperadas():
    result = analyze(_synthetic_rows())
    report = render_report_markdown(result)
    assert "# RQ1" in report
    assert "## 4. Análise de sensibilidade" in report
    assert "## 6. Limitações" in report


def test_figuras_sao_geradas(tmp_path: Path):
    result = analyze(_synthetic_rows())
    figures = render_figures(result, tmp_path)
    assert len(figures) == 2
    assert all(path.is_file() for path in figures)


def test_dataset_oficial_produz_analise_sem_excecoes():
    rows = load_validated_dataset()
    result = analyze(rows)
    assert result.wilcoxon.n_pairs == 9
    assert result.wilcoxon.n_missing_pairs == 0
