import pandas as pd
import pytest

from pipeline.classes_dora import REFERENCIA_GERAL, SEM_CLASSE, classe_geral, combinacoes_geral, distribuicao


def _dados():
    return pd.DataFrame({
        "classe_deployment_frequency": ["Elite", "Low", "High"],
        "classe_lead_time_a": ["Low", "Low", None],
        "classe_lead_time_b": ["High", "Low", None],
        "classe_cfr_a": ["Elite", "Medium", "Elite"],
        "classe_cfr_b": ["Low", "Low", None],
        "classe_tempo_recuperacao": ["Medium", None, None],
    })


def test_classe_geral_mediana_arredondada_para_baixo_ignorando_ausentes():
    geral = classe_geral(_dados(), list(REFERENCIA_GERAL.values()))
    # Notas: [4, 3, 4, 2] -> 3,5 -> High; [1, 1, 2] -> 1 -> Low; [3, 4] -> 3,5 -> High.
    assert geral.tolist() == ["High", "Low", "High"]


def test_combinacoes_cobrem_as_quatro_variantes():
    combinacoes = combinacoes_geral()
    assert list(combinacoes) == ["LT (a) + CFR (a)", "LT (a) + CFR (b)", "LT (b) + CFR (a)", "LT (b) + CFR (b)"]
    assert combinacoes["LT (b) + CFR (a)"] == list(REFERENCIA_GERAL.values())
    # Notas: [4, 1, 1, 2] -> 1,5 -> Low; [1, 1, 1] -> Low; [3] -> High.
    assert classe_geral(_dados(), combinacoes["LT (a) + CFR (b)"]).tolist() == ["Low", "Low", "High"]


def test_distribuicao_conta_sem_classe_e_percentuais():
    tabela = distribuicao({"Recuperação": _dados()["classe_tempo_recuperacao"]}).iloc[0]
    assert tabela["n"] == 1
    assert (tabela["Medium"], tabela[SEM_CLASSE], tabela["Elite"]) == (1, 2, 0)
    assert tabela["Medium (%)"] == pytest.approx(100 / 3)


def test_distribuicao_recusa_classe_desconhecida():
    with pytest.raises(ValueError, match="desconhecidas"):
        distribuicao({"x": pd.Series(["Elite", "Ótimo"])})
