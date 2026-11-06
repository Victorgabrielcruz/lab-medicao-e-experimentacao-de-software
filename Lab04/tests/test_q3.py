import pandas as pd
import pytest

from hipotese import q3
from hipotese.config import ALFA, TESTE_BINOMIAL, TESTE_Z


@pytest.fixture(scope="module")
def resultados():
    return q3.carregar_resultados()


@pytest.mark.parametrize("proporcao, esperado", [
    (0.0655, q3.LIBERAL), (0.0396, q3.CONSERVADOR), (0.0510, q3.PROXIMO), (0.0460, q3.PROXIMO),
])
def test_classificacao_usa_a_margem_de_monte_carlo(proporcao, esperado):
    assert q3.classificar_erro_tipo_i(proporcao) == esperado


def test_margem_de_monte_carlo_de_0_43_pp():
    assert 100 * q3.MARGEM_MONTE_CARLO == pytest.approx(0.427, abs=1e-3)


def test_erro_tipo_i_por_situacao_e_teste(resultados):
    tabela = q3.erro_tipo_i(resultados)
    assert len(tabela) == 6
    linha = tabela[(tabela["situacao"] == "Rajadas") & (tabela["teste"] == TESTE_Z)].iloc[0]
    assert linha["desvio_pp"] == pytest.approx(100 * (linha["proporcao_rejeicao"] - ALFA))


def test_poder_tem_diferenca_z_menos_binomial(resultados):
    tabela = q3.poder(resultados, "Amostra pequena")
    assert list(tabela["efeito"]) == sorted(resultados["efeito"].unique())
    assert tabela["diferenca_pp"].tolist() == pytest.approx(
        (100 * (tabela[TESTE_Z] - tabela[TESTE_BINOMIAL])).tolist())


def test_contagem_minima_e_erro_exato_com_n_20():
    assert q3.contagem_minima_rejeicao(TESTE_Z, 20) == 3
    assert q3.contagem_minima_rejeicao(TESTE_BINOMIAL, 20) == 4
    assert q3.erro_tipo_i_exato(TESTE_Z, 20) == pytest.approx(0.0755, abs=1e-4)
    assert q3.erro_tipo_i_exato(TESTE_BINOMIAL, 20) == pytest.approx(0.0159, abs=1e-4)


def test_inflacao_variancia():
    assert q3.inflacao_variancia(0) == 1
    assert q3.inflacao_variancia(0.5) == pytest.approx(3)
    with pytest.raises(ValueError):
        q3.inflacao_variancia(1)


def test_conclusoes_do_dashboard_valem_nos_resultados(resultados):
    """As frases da Q3 no dashboard dependem destes fatos da simulação."""
    tipo_i = q3.erro_tipo_i(resultados).set_index(["situacao", "teste"])["classificacao"]
    assert tipo_i[("Amostra pequena", TESTE_Z)] == q3.LIBERAL
    assert tipo_i[("Amostra pequena", TESTE_BINOMIAL)] == q3.CONSERVADOR
    assert tipo_i[("Rajadas", TESTE_Z)] == tipo_i[("Rajadas", TESTE_BINOMIAL)] == q3.LIBERAL
    for situacao in q3.VIOLACOES:
        assert (q3.poder(resultados, situacao)["diferenca_pp"] > 0).all()
    # Erro simulado com n = 20 próximo do exato (4 erros-padrão).
    pequena = resultados[(resultados["situacao"] == "Amostra pequena") & (resultados["efeito"] == 0)]
    for linha in pequena.itertuples():
        assert abs(linha.proporcao_rejeicao - q3.erro_tipo_i_exato(linha.teste, 20)) < 4 * linha.erro_padrao
