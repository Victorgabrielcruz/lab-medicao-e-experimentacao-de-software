import csv

import numpy as np
import pytest
from scipy.stats import binom

from hipotese.cenario import carregar_resumo, configuracoes_simulacao
from hipotese.config import ALFA, EFEITOS, META_TAXA_FALHA, N_REPETICOES, TESTE_BINOMIAL, TESTE_Z
from hipotese.gerador import INDEPENDENTE
from hipotese.simulacao import (ARQUIVO, ResultadoConfiguracao, TESTES, gerador_configuracao, gravar, pvalores,
                                simular, simular_configuracao)
from hipotese import testes

INDEP = {"n": 60, "situacao": INDEPENDENTE, "correlacao": 0.0}


@pytest.mark.parametrize("teste", [testes.teste_z, testes.teste_binomial])
def test_pvalores_iguais_aos_testes_da_s01(teste):
    falhas = np.array([0, 3, 3, 7, 12, 60])
    esperados = [teste(int(k), 60).pvalor for k in falhas]
    assert pvalores(falhas, 60, teste) == pytest.approx(esperados)


def test_mesma_configuracao_reproduz_o_resultado():
    a = simular_configuracao("Independente", INDEP, 0.02, 0, 1, repeticoes=500)
    b = simular_configuracao("Independente", INDEP, 0.02, 0, 1, repeticoes=500)
    assert a == b


def test_resultado_nao_depende_da_ordem_das_configuracoes():
    configuracoes = {"A": INDEP, "B": {**INDEP, "n": 30}}
    completo = simular(configuracoes, efeitos=(0.0, 0.04), repeticoes=300)
    isolado = simular_configuracao("B", configuracoes["B"], 0.04, 1, 1, repeticoes=300)
    assert [r for r in completo if (r.situacao, r.efeito) == ("B", 0.04)] == isolado


def test_configuracoes_tem_fluxos_diferentes():
    a = gerador_configuracao(0, 0).random(5)
    b = gerador_configuracao(0, 1).random(5)
    assert not np.allclose(a, b)


def _tamanho_exato(teste, n):
    """Probabilidade exata de rejeitar H0 verdadeira: soma de P(X = k) nas contagens rejeitadas."""
    k = np.arange(n + 1)
    rejeita = pvalores(k, n, teste) < ALFA
    return float(binom.pmf(k, n, META_TAXA_FALHA)[rejeita].sum())


@pytest.mark.parametrize("nome", [TESTE_Z, TESTE_BINOMIAL])
def test_erro_tipo_i_simulado_bate_com_o_valor_exato(nome):
    params = {"n": 243, "situacao": INDEPENDENTE, "correlacao": 0.0}
    resultado = next(r for r in simular_configuracao("Independente", params, 0.0, 0, 0) if r.teste == nome)
    exato = _tamanho_exato(TESTES[nome], 243)
    assert resultado.repeticoes == N_REPETICOES
    assert abs(resultado.proporcao_rejeicao - exato) < 4 * resultado.erro_padrao


def test_proporcao_e_erro_padrao():
    resultado = simular_configuracao("Independente", INDEP, 0.0, 0, 0, repeticoes=400)[0]
    p = resultado.rejeicoes / 400
    assert resultado.proporcao_rejeicao == p
    assert resultado.erro_padrao == pytest.approx((p * (1 - p) / 400) ** 0.5)
    assert resultado.taxa_verdadeira == META_TAXA_FALHA


def test_gravar_uma_linha_por_teste_e_configuracao(tmp_path):
    resultados = simular({"A": INDEP}, efeitos=(0.0, 0.1), repeticoes=100)
    caminho = tmp_path / "sim.csv"
    gravar(resultados, caminho)
    with open(caminho, encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == 2 * len(TESTES)
    assert list(linhas[0]) == list(ResultadoConfiguracao.__dataclass_fields__)
    assert {l["teste"] for l in linhas} == {TESTE_Z, TESTE_BINOMIAL}


def test_csv_versionado_reproduz_com_a_semente():
    """O CSV usado pelo dashboard é o que a semente fixa gera."""
    resultados = simular(configuracoes_simulacao(carregar_resumo()))
    with open(ARQUIVO, encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    assert len(linhas) == len(resultados) == 3 * len(EFEITOS) * len(TESTES)
    for linha, resultado in zip(linhas, resultados):
        assert (linha["situacao"], linha["teste"], int(linha["rejeicoes"])) == (
            resultado.situacao, resultado.teste, resultado.rejeicoes)
