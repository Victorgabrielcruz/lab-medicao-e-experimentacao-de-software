import shutil

import pandas as pd
import pytest

from experimento import config, painel


@pytest.mark.parametrize("coluna", ["tempo_total_s", "vazao_ops_s"])
def test_descritiva_amostral_e_quartis_com_valores_conhecidos(coluna):
    dados = pd.DataFrame({"configuracao": ["DELETE-FULL"] * 3, "carga": ["leitura"] * 3,
                          coluna: [1.0, 2.0, 3.0]})
    linha = painel.descritiva(dados, coluna).iloc[0]
    assert linha["n"] == 3
    assert linha["Mediana"] == linha["Média"] == 2
    assert linha["DP"] == 1
    assert linha["Q1"] == 1.5
    assert linha["Q3"] == 2.5
    assert linha["IQR"] == 1
    assert linha["CV (%)"] == 50
    assert (linha["Mínimo"], linha["Máximo"]) == (1, 3)


def test_m3_usa_razao_das_medianas_e_preserva_orientacao():
    # Mediana das razões de WAL-FULL / DELETE-FULL seria 2, não 4.
    valores = {"DELETE-FULL": [1, 2, 100], "DELETE-NORMAL": [1, 1, 1],
               "WAL-FULL": [2, 8, 300], "WAL-NORMAL": [3, 3, 3]}
    dados = pd.DataFrame([
        {"carga": carga.nome, "configuracao": cfg, "vazao_ops_s": valor}
        for carga in config.CARGAS for cfg, serie in valores.items() for valor in serie
    ])
    resultado = painel.comparacoes(dados)
    assert len(resultado) == 9
    for carga in config.CARGAS:
        tabela = resultado[resultado.Carga == carga.nome].set_index("Comparação")
        assert tabela.loc["H1", "M3 (×)"] == 4
        assert tabela.loc["H2", "M3 (×)"] == 3 / 8
        assert tabela.loc["H3", "M3 (×)"] == 0.5
        assert tabela.loc["H1", "Ganho de vazão (%)"] == 300
        assert tabela.loc["H3", "Ganho de vazão (%)"] == -50


@pytest.mark.parametrize("alteracao", ["fator", "semente"])
def test_leitura_recusa_fatores_ou_pareamento_inconsistentes(tmp_path, alteracao):
    shutil.copytree(config.DIR_DADOS / "piloto", tmp_path / "piloto")
    pasta = tmp_path / "piloto"
    dados = pd.read_csv(pasta / "resultados.csv")
    if alteracao == "fator":
        dados.loc[0, "journal_mode"] = "WAL"
    else:
        dados.loc[0, "semente_carga"] = 1
    dados.to_csv(pasta / "resultados.csv", index=False)
    with pytest.raises(ValueError, match="Fatores|semente"):
        painel.carregar_piloto(pasta)
