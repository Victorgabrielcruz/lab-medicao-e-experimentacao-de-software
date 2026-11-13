"""G1: frequências binárias; G2: áreas e massas dos testes (#267, #268)."""

import numpy as np
import pytest
from scipy.stats import norm

from hipotese.config import ALFA, CORES_TESTES, TESTE_BINOMIAL, TESTE_Z
from hipotese.exemplo import ExemploSimulado, gerar_exemplo
from hipotese.graficos import CORES_DADOS, construir_g1, construir_g2, regiao_binomial
from hipotese.testes import aplicar_testes
from hipotese import testes as inferencia


def test_g1_normaliza_os_dois_grupos_e_preserva_as_contagens():
    figura = construir_g1([0, 0, 0, 1], [0, 1])
    real, simulado = figura.data
    assert list(real.x) == list(simulado.x) == [0, 1]
    assert list(real.y) == [75, 25]
    assert list(simulado.y) == [50, 50]
    assert np.array_equal(real.customdata, [[3, 4], [1, 4]])
    assert np.array_equal(simulado.customdata, [[1, 2], [1, 2]])
    assert real.xaxis == simulado.xaxis  # Mesmo eixo: barras agrupadas por resultado.
    assert figura.layout.barmode == "group"
    assert real.marker.color == CORES_DADOS["Real"]
    assert simulado.marker.color == CORES_DADOS["Simulado sob H₀"]
    assert all(trace.showlegend and trace.name for trace in figura.data)
    assert "G1" in figura.layout.title.text and "5%" in figura.layout.title.text
    assert "adimensional" in figura.layout.xaxis.title.text
    assert list(figura.layout.xaxis.ticktext) == ["0 · Passou", "1 · Falhou"]
    assert "%" in figura.layout.yaxis.title.text
    assert list(figura.layout.yaxis.range) == [0, 110]


@pytest.mark.parametrize("amostra,frequencias", [([0, 0], [100, 0]), ([1, 1], [0, 100])])
def test_g1_mantem_as_duas_classes_mesmo_sem_sucessos_ou_falhas(amostra, frequencias):
    figura = construir_g1(amostra, amostra)
    for trace in figura.data:
        assert list(trace.x) == [0, 1]
        assert list(trace.y) == frequencias


@pytest.mark.parametrize("amostra", [[], [0, 0.5], [0, 2], [[0, 1]]])
def test_g1_nao_oculta_valores_invalidos_fora_dos_bins(amostra):
    with pytest.raises(ValueError, match="amostras unidimensionais"):
        construir_g1(amostra, [0, 1])


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
