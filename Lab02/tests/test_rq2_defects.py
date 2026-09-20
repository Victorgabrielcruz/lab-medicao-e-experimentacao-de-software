from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import load_validated_dataset
from src.analysis.rq2_defects import analyze, render_figures, render_report_markdown

PARTICIPANTS = ("P01", "P02", "P03")
BLOCKS = ("B1", "B2", "B3")


def _row(trial_id, participant, block, treatment, *, success_rate, failed_tests, total_tests=6):
    return {
        "trial_id": trial_id,
        "participant_id": participant,
        "difficulty_block": block,
        "treatment": treatment,
        "success_rate": success_rate,
        "failed_tests": failed_tests,
        "total_tests": total_tests,
    }


def _synthetic_rows() -> list[dict]:
    rows = []
    for participant in PARTICIPANTS:
        for block in BLOCKS:
            rows.append(_row(f"{participant}-{block}-ai", participant, block, "ai", success_rate=100.0, failed_tests=0))
            rows.append(_row(f"{participant}-{block}-manual", participant, block, "manual", success_rate=60.0, failed_tests=2))
    return rows


def test_analyze_direcao_ia_maior_taxa_de_sucesso():
    result = analyze(_synthetic_rows())
    assert result.wilcoxon.n_pairs == 9
    # diferença manual - ai é negativa quando ai tem taxa maior
    assert result.wilcoxon.median_diff == -40.0
    assert result.wilcoxon.p_value is not None and result.wilcoxon.p_value < 0.05


def test_trials_completamente_verdes_sao_contados():
    result = analyze(_synthetic_rows())
    assert result.green["ai"].fully_green == 9
    assert result.green["manual"].fully_green == 0


def test_failed_tests_e_relatado_como_complementar_nao_substitui_taxa():
    rows = _synthetic_rows()
    result = analyze(rows)
    assert result.failed_descriptive["manual"].median == 2
    # a decisão de direção usa success_rate, não failed_tests
    assert result.success_pairs[0].difference is not None


def test_relatorio_markdown_contem_secoes_esperadas():
    result = analyze(_synthetic_rows())
    report = render_report_markdown(result)
    assert "# RQ2" in report
    assert "## 2. Testes falhando" in report
    assert "## 3. Trials completamente verdes" in report


def test_figuras_sao_geradas(tmp_path: Path):
    result = analyze(_synthetic_rows())
    figures = render_figures(result, tmp_path)
    assert len(figures) == 2
    assert all(path.is_file() for path in figures)


def test_dataset_oficial_produz_analise_sem_excecoes():
    rows = load_validated_dataset()
    result = analyze(rows)
    assert result.wilcoxon.n_pairs == 9
