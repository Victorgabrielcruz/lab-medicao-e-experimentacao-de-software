from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import load_validated_dataset
from src.analysis.rq3_structure import analyze, render_figures, render_report_markdown

PARTICIPANTS = ("P01", "P02", "P03")
BLOCKS = ("B1", "B2", "B3")


def _row(trial_id, participant, block, treatment, *, complexity, duplication, loc, mi=70.0):
    return {
        "trial_id": trial_id,
        "participant_id": participant,
        "difficulty_block": block,
        "treatment": treatment,
        "mean_cyclomatic_complexity": complexity,
        "duplication_percentage": duplication,
        "loc": loc,
        "maintainability_index": mi,
    }


def _synthetic_rows() -> list[dict]:
    rows = []
    for participant in PARTICIPANTS:
        for block in BLOCKS:
            rows.append(_row(f"{participant}-{block}-ai", participant, block, "ai", complexity=3.0, duplication=0.0, loc=20))
            rows.append(_row(f"{participant}-{block}-manual", participant, block, "manual", complexity=9.0, duplication=5.0, loc=25))
    return rows


def test_metricas_ausentes_excluem_o_par_sem_virar_zero():
    rows = _synthetic_rows()
    # remove a métrica estrutural de um trial manual, mantendo o trial_id (Seção 12)
    for row in rows:
        if row["trial_id"] == "P01-B1-manual":
            row["mean_cyclomatic_complexity"] = None
            row["duplication_percentage"] = None
            row["loc"] = None

    result = analyze(rows)
    assert result.complexity_wilcoxon.n_pairs == 8
    assert result.complexity_wilcoxon.n_missing_pairs == 1
    missing_pair = next(p for p in result.complexity_pairs if p.participant_id == "P01" and p.difficulty_block == "B1")
    assert missing_pair.manual_value is None
    assert not missing_pair.valid


def test_teste_bilateral_e_holm_aplicado_as_duas_metricas():
    result = analyze(_synthetic_rows())
    assert result.complexity_wilcoxon.alternative == "two-sided"
    assert result.duplication_wilcoxon.alternative == "two-sided"
    assert result.complexity_p_holm is not None
    assert result.duplication_p_holm is not None
    # com diferença perfeita e consistente em ambas as métricas, Holm não deve subir acima de 1
    assert result.complexity_p_holm <= 1.0
    assert result.duplication_p_holm <= 1.0
    assert result.complexity_wilcoxon.median_diff == -6.0
    assert result.complexity_wilcoxon.effect_size_r == -1.0


def test_holm_preserva_familia_quando_duplicacao_tem_apenas_empates():
    rows = _synthetic_rows()
    for row in rows:
        row["duplication_percentage"] = 0.0
    result = analyze(rows)
    assert result.duplication_wilcoxon.p_value is None
    assert result.duplication_p_holm is None
    assert result.complexity_p_holm == min(1.0, 2 * result.complexity_wilcoxon.p_value)


def test_loc_e_reportado_mas_nao_testado():
    result = analyze(_synthetic_rows())
    assert result.loc_descriptive["ai"].median == 20
    assert result.loc_descriptive["manual"].median == 25
    assert len(result.loc_pairs) == 9


def test_indice_de_manutenibilidade_e_apenas_descritivo():
    result = analyze(_synthetic_rows())
    assert result.maintainability_descriptive["ai"].median == 70.0
    assert not hasattr(result, "maintainability_wilcoxon")


def test_relatorio_markdown_contem_secoes_esperadas():
    result = analyze(_synthetic_rows())
    report = render_report_markdown(result)
    assert "# RQ3" in report
    assert "Holm" in report
    assert "ai - manual" in report
    assert "## 4. Índice de Manutenibilidade" in report
    assert "## 7. Limitações" in report


def test_figuras_sao_geradas(tmp_path: Path):
    result = analyze(_synthetic_rows())
    figures = render_figures(result, tmp_path)
    assert len(figures) == 3
    assert all(path.is_file() for path in figures)


def test_dataset_oficial_tem_amostra_reduzida_por_lacunas_conhecidas():
    rows = load_validated_dataset()
    result = analyze(rows)
    # cinco trials manuais antigos não têm métricas estruturais coletadas (Seção 12);
    # isso deve reduzir os pares válidos de RQ3 sem lançar exceção nem virar zero.
    assert result.complexity_wilcoxon.n_pairs < 9
    assert result.complexity_wilcoxon.n_missing_pairs > 0
