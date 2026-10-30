import numpy as np
import pytest

from hipotese.config import META_TAXA_FALHA, gerador
from hipotese.gerador import (
    INDEPENDENTE,
    RAJADAS,
    SITUACOES,
    gerar_builds,
    gerar_lote,
    taxa_com_efeito,
)


def autocorrelacao_lag1(builds):
    anteriores, seguintes = builds[:, :-1].ravel(), builds[:, 1:].ravel()
    return np.corrcoef(anteriores, seguintes)[0, 1]


def test_efeito_zero_e_a_meta():
    assert taxa_com_efeito(0) == META_TAXA_FALHA
    assert taxa_com_efeito(0.03) == pytest.approx(META_TAXA_FALHA + 0.03)


def test_efeito_que_leva_a_taxa_para_fora_de_0_1_falha():
    with pytest.raises(ValueError):
        taxa_com_efeito(1)


@pytest.mark.parametrize("situacao", SITUACOES)
def test_builds_sao_binarias_com_tamanho_n(situacao):
    builds = gerar_builds(gerador(), 40, 0.05, situacao)
    assert builds.shape == (40,)
    assert set(np.unique(builds)) <= {0, 1}


@pytest.mark.parametrize("situacao", SITUACOES)
def test_mesma_semente_reproduz_o_lote(situacao):
    a = gerar_lote(gerador(), 30, 0.05, 200, situacao)
    b = gerar_lote(gerador(), 30, 0.05, 200, situacao)
    assert np.array_equal(a, b)


@pytest.mark.parametrize("situacao", SITUACOES)
def test_contagens_ficam_entre_0_e_n_com_media_n_vezes_taxa(situacao):
    n, taxa = 50, 0.08
    contagens = gerar_lote(gerador(), n, taxa, 20_000, situacao)
    assert contagens.shape == (20_000,)
    assert contagens.min() >= 0 and contagens.max() <= n
    assert contagens.mean() == pytest.approx(n * taxa, rel=0.05)


def test_independente_nao_tem_autocorrelacao():
    builds = gerar_lote(gerador(), 50, 0.2, 2_000, INDEPENDENTE, contagens=False)
    assert abs(autocorrelacao_lag1(builds)) < 0.02


def test_rajadas_tem_a_autocorrelacao_pedida():
    builds = gerar_lote(gerador(), 50, 0.2, 2_000, RAJADAS, correlacao=0.6, contagens=False)
    assert autocorrelacao_lag1(builds) == pytest.approx(0.6, abs=0.03)


def test_rajadas_tem_mais_variancia_que_a_binomial():
    n, taxa = 50, 0.05
    contagens = gerar_lote(gerador(), n, taxa, 20_000, RAJADAS)
    assert contagens.var() > 1.5 * n * taxa * (1 - taxa)


@pytest.mark.parametrize(
    "argumentos",
    [
        {"n": 0, "taxa_falha": 0.05},
        {"n": 10, "taxa_falha": 1.2},
        {"n": 10, "taxa_falha": 0.05, "situacao": "outra"},
        {"n": 10, "taxa_falha": 0.05, "situacao": RAJADAS, "correlacao": 1},
    ],
)
def test_parametros_invalidos_falham(argumentos):
    with pytest.raises(ValueError):
        gerar_lote(gerador(), repeticoes=5, **argumentos)
