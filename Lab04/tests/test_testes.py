"""Referências numéricas e casos extremos dos testes do par P4 (#266)."""

from math import comb, erfc, isfinite, sqrt

import numpy as np
import pytest

from hipotese import testes as inferencia


def test_binomial_confere_com_soma_das_probabilidades_sob_h0():
    # Referência calculada diretamente para n pequeno, independente da API SciPy.
    esperado = sum(comb(20, k) * 0.05**k * 0.95**(20 - k) for k in range(3, 21))
    resultado = inferencia.teste_binomial(3, 20)
    assert resultado.pvalor == pytest.approx(esperado)
    assert resultado.estatistica == pytest.approx(3 / 20)
    assert resultado.efeito_pp == pytest.approx(10.0)
    assert not resultado.rejeita_h0


@pytest.mark.parametrize("falhas", [0, 20])
def test_binomial_sem_falhas_e_com_todas_as_falhas(falhas):
    resultado = inferencia.teste_binomial(falhas, 20)
    assert resultado.pvalor == pytest.approx(1.0 if falhas == 0 else 0.05**20, rel=1e-12, abs=0)
    assert resultado.rejeita_h0 == (falhas == 20)


@pytest.mark.parametrize("teste", [inferencia.teste_z, inferencia.teste_binomial])
@pytest.mark.parametrize("falhas,n", [(-1, 20), (21, 20), (1.5, 20), (0, 0), (1, 2.5), (True, 20)])
def test_rejeita_contagens_invalidas(teste, falhas, n):
    with pytest.raises(ValueError):
        teste(falhas, n)


@pytest.mark.parametrize("teste", [inferencia.teste_z, inferencia.teste_binomial])
@pytest.mark.parametrize("parametros", [
    {"meta": 0}, {"meta": 1}, {"meta": float("nan")}, {"alfa": 0}, {"alfa": 1},
    {"alternativa": "invalida"},
])
def test_rejeita_parametros_invalidos(teste, parametros):
    with pytest.raises(ValueError):
        teste(2, 20, **parametros)


def test_z_usa_variancia_sob_h0_e_nao_a_variancia_amostral():
    # p_hat=0.28, p0=0.20, n=100: erro padrão sob H0=0.04, logo Z=2.
    resultado = inferencia.teste_z(28, 100, meta=0.2)
    assert resultado.estatistica == pytest.approx(2)
    assert resultado.pvalor == pytest.approx(erfc(2 / sqrt(2)) / 2)
    assert resultado.efeito_pp == pytest.approx(8)
    assert resultado.rejeita_h0


@pytest.mark.parametrize("falhas", [0, 20])
def test_z_permanece_finito_nas_amostras_extremas(falhas):
    resultado = inferencia.teste_z(falhas, 20)
    assert isfinite(resultado.estatistica)
    assert isfinite(resultado.pvalor) and 0 <= resultado.pvalor <= 1
    assert resultado.rejeita_h0 == (falhas == 20)


@pytest.mark.parametrize("teste", [inferencia.teste_z, inferencia.teste_binomial])
def test_alternativa_e_alfa_sao_respeitados(teste):
    direita = teste(3, 20)
    esquerda = teste(3, 20, alternativa="less")
    assert direita.pvalor < esquerda.pvalor
    assert 0 <= teste(3, 20, alternativa="two-sided").pvalor <= 1
    assert not teste(3, 20, alfa=direita.pvalor).rejeita_h0  # Regra estrita p < alfa.
    assert teste(3, 20, alfa=0.1).rejeita_h0


def test_z_bicaudal_e_o_dobro_da_cauda_correspondente():
    direita = inferencia.teste_z(3, 20)
    bicaudal = inferencia.teste_z(3, 20, alternativa="two-sided")
    assert bicaudal.pvalor == pytest.approx(2 * direita.pvalor)


@pytest.mark.parametrize("builds", [[], [[0, 1]], [0, 2], [float("nan")], ["0", "1"]])
def test_aplicar_testes_rejeita_amostras_invalidas(builds):
    with pytest.raises(ValueError):
        inferencia.aplicar_testes(builds)


def test_amostra_e_contagens_produzem_os_mesmos_resultados():
    builds = np.array([0] * 17 + [1] * 3, dtype=np.int8)
    resultados = inferencia.aplicar_testes(builds)
    assert resultados == (inferencia.teste_z(np.int64(3), np.int64(20)), inferencia.teste_binomial(3, 20))
    assert np.array_equal(builds, np.array([0] * 17 + [1] * 3))
    assert resultados[0].efeito_pp == resultados[1].efeito_pp
