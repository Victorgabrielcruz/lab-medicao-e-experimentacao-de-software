"""Integração entre a coleta, o protocolo e o gerador da #264."""

import csv

import pytest

from hipotese.cenario import RESUMO, carregar_amostras_g1, carregar_resumo, configuracoes_simulacao
from hipotese.config import ALTERNATIVA, EFEITOS, META_TAXA_FALHA, gerador
from hipotese.gerador import gerar_builds, taxa_com_efeito


def test_calibracao_corresponde_a_amostra_real():
    resumo = carregar_resumo()
    with (RESUMO.parent / "ci_pytest.csv").open(encoding="utf-8", newline="") as arquivo:
        valores = [int(linha["falhou"]) for linha in csv.DictReader(arquivo)]
    media = sum(valores) / len(valores)
    acf = sum((a - media) * (b - media) for a, b in zip(valores, valores[1:])) / sum(
        (valor - media) ** 2 for valor in valores
    )
    configuracoes = configuracoes_simulacao(resumo)
    assert configuracoes["Independente"]["n"] == len(valores)
    assert configuracoes["Rajadas"]["n"] == len(valores)
    assert configuracoes["Rajadas"]["correlacao"] == pytest.approx(acf)
    assert ALTERNATIVA == "greater"
    assert len(EFEITOS) >= 5 and EFEITOS[0] == 0
    assert all(a < b for a, b in zip(EFEITOS, EFEITOS[1:]))


def test_todas_as_configuracoes_e_efeitos_podem_ser_usados_no_gerador():
    configuracoes = configuracoes_simulacao(carregar_resumo())
    assert configuracoes["Amostra pequena"]["n"] * META_TAXA_FALHA < 5
    assert configuracoes["Independente"]["n"] * META_TAXA_FALHA >= 10
    assert taxa_com_efeito(EFEITOS[0]) == META_TAXA_FALHA
    for parametros in configuracoes.values():
        for efeito in EFEITOS:
            builds = gerar_builds(gerador(), taxa_falha=taxa_com_efeito(efeito), **parametros)
            assert builds.shape == (parametros["n"],)
            assert set(builds) <= {0, 1}


def test_g1_usa_o_csv_real_e_uma_amostra_fixa_sob_h0():
    import numpy as np
    from hipotese.exemplo import gerar_exemplo

    exemplo_antes = gerar_exemplo().builds.copy()
    reais, simulados = carregar_amostras_g1()
    with (RESUMO.parent / "ci_pytest.csv").open(encoding="utf-8", newline="") as arquivo:
        valores_csv = [int(linha["falhou"]) for linha in csv.DictReader(arquivo)]
    assert np.array_equal(reais, valores_csv)
    assert reais.size == simulados.size == 243
    assert reais.sum() == 10
    # Resultado da amostra Bernoulli(0,05) com a semente 42, sem novos sorteios.
    assert simulados.sum() == 12
    outros_reais, outros_simulados = carregar_amostras_g1()
    assert np.array_equal(reais, outros_reais)
    assert np.array_equal(simulados, outros_simulados)
    assert np.array_equal(gerar_exemplo().builds, exemplo_antes)
