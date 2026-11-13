"""Poder exato do gráfico interativo do bônus (#278)."""

import numpy as np
import pytest

from hipotese import poder
from hipotese.config import ALFA, TESTE_BINOMIAL, TESTE_Z
from hipotese.graficos import construir_poder_interativo
from hipotese.q3 import carregar_resultados
from hipotese import testes as inferencia


@pytest.mark.parametrize("n", [1, 20, 243, 250])
def test_pvalores_vetorizados_coincidem_com_os_testes_da_s01(n):
    pvalores = poder.pvalores_por_contagem(n)
    for falhas in range(n + 1):
        assert pvalores[TESTE_Z][falhas] == pytest.approx(inferencia.teste_z(falhas, n).pvalor, rel=1e-9, abs=1e-15)
        assert pvalores[TESTE_BINOMIAL][falhas] == pytest.approx(inferencia.teste_binomial(falhas, n).pvalor, rel=1e-9, abs=1e-15)


@pytest.mark.parametrize(("teste", "n", "minimo"), [
    (TESTE_Z, 243, 18), (TESTE_BINOMIAL, 243, 19),
    (TESTE_Z, 20, 3), (TESTE_BINOMIAL, 20, 4),
    (TESTE_Z, 250, 19), (TESTE_BINOMIAL, 250, 19),
])
def test_contagem_minima_de_rejeicao(teste, n, minimo):
    assert poder.contagem_minima_rejeicao(teste, n) == minimo


def test_sem_contagem_que_rejeite_o_poder_e_zero():
    # Com 1 build, o binomial exato nunca chega a p-valor < 5%.
    assert poder.contagem_minima_rejeicao(TESTE_BINOMIAL, 1) == 2
    assert poder.poder_exato(TESTE_BINOMIAL, 1, 0.5) == 0.0


@pytest.mark.parametrize("situacao", ["Independente", "Amostra pequena"])
def test_poder_exato_coincide_com_a_simulacao_independente(situacao):
    simulacao = carregar_resultados()
    linhas = simulacao[simulacao["situacao"] == situacao]
    for linha in linhas.itertuples():
        exato = poder.poder_exato(linha.teste, int(linha.n), float(linha.efeito))
        assert abs(exato - linha.proporcao_rejeicao) <= 4 * max(linha.erro_padrao, 1e-3)


def test_poder_cresce_com_o_efeito_e_cai_com_alfa_menor():
    curva = poder.curva_poder(243, np.linspace(0, 0.1, 11))
    for teste in poder.TESTES:
        assert np.all(np.diff(curva.loc[curva["teste"] == teste, "poder"]) >= 0)
        assert poder.poder_exato(teste, 243, 0.04, alfa=0.01) < poder.poder_exato(teste, 243, 0.04, alfa=ALFA)


@pytest.mark.parametrize("argumentos", [
    {"teste": TESTE_Z, "n": 0, "efeito": 0.04},
    {"teste": TESTE_Z, "n": 243, "efeito": -0.01},
    {"teste": TESTE_Z, "n": 243, "efeito": 0.96},
    {"teste": TESTE_Z, "n": 243, "efeito": 0.04, "alfa": 0},
])
def test_valida_os_parametros(argumentos):
    with pytest.raises(ValueError):
        poder.poder_exato(**argumentos)


def test_grafico_interativo_marca_o_efeito_escolhido_e_o_alfa():
    curva = poder.curva_poder(243, np.linspace(0, 0.15, 31))
    figura = construir_poder_interativo(curva, 243, 0.04, ALFA)
    marcadores = [traco for traco in figura.data if traco.mode == "markers"]
    assert [m.x[0] for m in marcadores] == [4.0, 4.0]
    for marcador in marcadores:
        teste = marcador.legendgroup
        assert marcador.y[0] == pytest.approx(100 * poder.poder_exato(teste, 243, 0.04))
    assert any(forma.y0 == 5 for forma in figura.layout.shapes)
    assert "243 builds" in figura.layout.title.text
