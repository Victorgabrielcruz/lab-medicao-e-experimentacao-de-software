import shutil
import json

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


def test_coleta_completa_revalidada_sem_republicar_relatorios():
    pasta = config.DIR_DADOS / "coleta-completa-01"
    antes = {p: p.read_bytes() for p in pasta.rglob("*") if p.is_file()}
    coleta = painel.carregar_coleta_completa(pasta)
    assert len(coleta.dados) == 360
    assert len(coleta.resumo["grupos"]) == 12
    assert {g["n"] for g in coleta.resumo["grupos"]} == {30}
    assert coleta.validacao["status"] == "aprovada"
    assert coleta.validacao["outliers_observacoes_unicas"] == 23
    assert coleta.validacao["observacoes_excluidas"] == 0
    assert all(p.read_bytes() == conteudo for p, conteudo in antes.items())


@pytest.mark.parametrize("falha", ["manifesto_ausente", "reprovada", "nao_publicada", "hash_manifesto", "csv_alterado"])
def test_coleta_completa_exige_validacao_e_integridade(tmp_path, falha):
    pasta = tmp_path / "coleta-completa-01"
    shutil.copytree(config.DIR_DADOS / "coleta-completa-01", pasta)
    caminho = pasta / "validacao" / "manifesto.json"
    manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    if falha == "manifesto_ausente":
        caminho.unlink()
    elif falha == "csv_alterado":
        with (pasta / "resultados.csv").open("ab") as arquivo:
            arquivo.write(b"\n")
    else:
        if falha == "reprovada":
            manifesto["status"] = "reprovada"
        elif falha == "nao_publicada":
            manifesto["publicado_para_analise_exploratoria"] = False
        else:
            manifesto["entradas_sha256"]["resultados.csv"] = "0" * 64
        caminho.write_text(json.dumps(manifesto), encoding="utf-8")
    with pytest.raises((OSError, ValueError)):
        painel.carregar_coleta_completa(pasta)


def test_grafico_de_comparacao_usa_mediana_e_quartis_assimetricos():
    dados = pd.DataFrame([
        {"configuracao": cfg.nome, "carga": "escrita", "tempo_total_s": valor}
        for cfg in config.CONFIGURACOES for valor in (1, 2, 100)
    ])
    figura = painel.comparar_configuracoes(dados, "tempo_total_s", "Tempo (s)", "escrita")
    pontos, = figura.data
    assert list(pontos.y) == [2] * 4
    assert list(pontos.error_y.array) == [49] * 4
    assert list(pontos.error_y.arrayminus) == [0.5] * 4
    assert list(pontos.x) == [c.nome for c in config.CONFIGURACOES]


def test_boxplot_usa_quartis_inclusivos_e_preserva_extremo_fora_dos_bigodes():
    valores = list(range(1, 30)) + [100]
    dados = pd.DataFrame([
        {"configuracao": cfg.nome, "carga": "escrita", "tempo_total_s": valor}
        for cfg in config.CONFIGURACOES for valor in valores
    ])
    figura = painel.distribuicao(dados, "tempo_total_s", "Tempo (s)", "escrita")
    for caixa in figura.data:
        assert list(caixa.q1) == [8.25]
        assert list(caixa.median) == [15.5]
        assert list(caixa.q3) == [22.75]
        assert list(caixa.lowerfence) == [1]
        assert list(caixa.upperfence) == [29]
        assert list(caixa.y[0]) == valores  # O extremo 100 permanece visível.


def test_descritiva_das_duas_metricas_em_todos_os_grupos():
    dados = pd.read_csv(config.DIR_DADOS / "coleta-completa-01" / "resultados.csv")
    tabela = painel.descritiva_completa(dados)
    assert len(tabela) == 24
    assert not tabela.duplicated(["Métrica", "Carga", "Configuração"]).any()
    assert set(tabela["n"]) == {30}
    assert set(tabela.Unidade) == {"s", "operações/s"}
    # Confere DP amostral e quartis de n=30 com uma implementação independente.
    import statistics
    for _, linha in tabela.iterrows():
        coluna = painel.METRICAS[linha["Métrica"]][0]
        valores = dados[(dados.carga == linha["Carga"]) & (dados.configuracao == linha["Configuração"])][coluna].tolist()
        q1, _, q3 = statistics.quantiles(valores, n=4, method="inclusive")
        assert linha["Média"] == pytest.approx(statistics.mean(valores))
        assert linha["Mediana"] == pytest.approx(statistics.median(valores))
        assert linha["DP"] == pytest.approx(statistics.stdev(valores))
        assert linha["Q1"] == pytest.approx(q1)
        assert linha["Q3"] == pytest.approx(q3)
