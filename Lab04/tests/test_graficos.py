"""G2: áreas e massas devem corresponder aos testes, inclusive na fronteira (#268)."""

import numpy as np
import pytest
from scipy.stats import norm

from hipotese.config import ALFA, CORES_TESTES, TESTE_BINOMIAL, TESTE_Z
from hipotese.exemplo import ExemploSimulado, gerar_exemplo
from hipotese.graficos import construir_g2, regiao_binomial
from hipotese.testes import aplicar_testes
from hipotese import testes as inferencia


@pytest.mark.parametrize("n", [1, 20, 243])
def test_rejeicao_binomial_corresponde_a_decisao_para_cada_contagem(n):
    k, massas, rejeicao = regiao_binomial(n)
    decisoes = [inferencia.teste_binomial(int(falhas), n).rejeita_h0 for falhas in k]
    assert np.array_equal(rejeicao, decisoes)
    assert massas.sum() == pytest.approx(1)
    assert massas[rejeicao].sum() <= ALFA
    if n == 1:
        assert not rejeicao.any()  # p = alfa não rejeita.


def test_sombras_reproduzem_os_pvalores_do_mesmo_exemplo():
    exemplo = gerar_exemplo()
    normal, binomial = construir_g2(exemplo)
    z, exato = exemplo.resultados
    # Integral numérica da área desenhada, independente do cálculo por sf.
    cauda = normal.data[1]
    assert cauda.x[0] == z.estatistica
    assert np.trapezoid(cauda.y, cauda.x) == pytest.approx(z.pvalor, abs=5e-6)
    assert np.trapezoid(normal.data[2].y, normal.data[2].x) == pytest.approx(ALFA, abs=5e-6)
    # No exato, a massa da própria observação precisa ser incluída.
    assert min(binomial.data[1].customdata) == exato.falhas
    assert sum(binomial.data[1].y) / 100 == pytest.approx(exato.pvalor)
    assert normal.data[4].x[0] == pytest.approx(norm.isf(ALFA))


def test_titulos_unidades_e_cores_vem_do_protocolo():
    normal, binomial = construir_g2(gerar_exemplo())
    assert normal.data[0].line.color == CORES_TESTES[TESTE_Z]
    assert binomial.data[0].marker.line.color == CORES_TESTES[TESTE_BINOMIAL]
    for figura in (normal, binomial):
        assert "G2" in figura.layout.title.text and "H₀" in figura.layout.title.text
        assert figura.layout.xaxis.title.text
        assert figura.layout.yaxis.title.text
        assert all(trace.name for trace in figura.data)


@pytest.mark.parametrize("falhas", [0, 40, 243])
def test_g2_funciona_quando_as_caudas_se_sobrepoem_em_qualquer_ordem(falhas):
    builds = np.array([1] * falhas + [0] * (243 - falhas))
    exemplo = ExemploSimulado(builds, 0.09, aplicar_testes(builds))
    normal, binomial = construir_g2(exemplo)
    assert np.isfinite(normal.data[0].y).all()
    assert sum(binomial.data[1].y) / 100 == pytest.approx(exemplo.resultados[1].pvalor, rel=1e-10, abs=0)
    assert normal.data[1].x[0] == exemplo.resultados[0].estatistica
