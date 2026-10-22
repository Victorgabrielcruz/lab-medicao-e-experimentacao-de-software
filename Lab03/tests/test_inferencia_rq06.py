"""Holm, famílias planejadas e tamanhos de efeito da RQ06 (#172)."""

import numpy as np
import pandas as pd
import pytest

from pipeline import comparacao_rq06 as base
from pipeline.inferencia_rq06 import analisar, aplicar_holm, cliff_delta, epsilon_quadrado, magnitude_delta


@pytest.fixture
def dados():
    n = 40
    d = pd.DataFrame({"id": np.arange(1, n+1), "full_name": [f"org/r{i}" for i in range(n)]})
    for i, fator in enumerate(base.FATORES):
        d[fator] = np.arange(1, n+1) * (i+1)
    for metrica in base.METRICAS:
        d[metrica] = np.arange(n) / (n-1) if metrica.startswith("cfr") else np.arange(n, dtype=float)
    return d


def test_holm_valores_conhecidos_ordem_original_e_limites():
    r = aplicar_holm([.01, .04, .03])
    assert r["p_valor_holm"].tolist() == pytest.approx([.03, .06, .06])
    assert r["rejeita_holm"].tolist() == [True, False, False]
    r = aplicar_holm([0, 1, .02])
    assert r["p_valor_holm"].tolist() == pytest.approx([0, 1, .04])
    assert aplicar_holm([.05])["rejeita_holm"].iloc[0]  # Regra de fronteira do statsmodels.


def test_holm_p_ausente_mantem_familia_sem_virar_um_observado():
    r = aplicar_holm([.02, None, .04])
    assert r["p_valor_holm"].iloc[[0, 2]].tolist() == pytest.approx([.06, .08])
    assert pd.isna(r.loc[1, "p_valor_holm"]) and pd.isna(r.loc[1, "rejeita_holm"])
    assert aplicar_holm([None, np.nan])["p_valor_holm"].isna().all()
    assert aplicar_holm([]).empty


@pytest.mark.parametrize("p", [[-0.01], [1.01], [np.inf], [True], [[.1, .2]], ['texto']])
def test_p_valor_invalido_rejeitado(p):
    with pytest.raises(ValueError):
        aplicar_holm(p)


@pytest.mark.parametrize("alpha", [0, 1, -1, True, np.nan, '0.05'])
def test_alpha_invalido(dados, alpha):
    with pytest.raises(ValueError):
        aplicar_holm([.01], alpha=alpha)
    with pytest.raises(ValueError):
        analisar(dados, alpha=alpha)


@pytest.mark.parametrize("H,n,esperado", [(14, 15, 1), (0, 20, 0), (5, 11, .5),
    (None, 0, None), (0, 1, None)])
def test_epsilon_convencao_h_sobre_n_menos_um(H, n, esperado):
    assert epsilon_quadrado(H, n) == esperado


@pytest.mark.parametrize("H,n", [(np.nan, 10), (-1, 10), (10, 10), (True, 10),
    ('texto', 10), (1, -1), (1, 2.5), (1, True)])
def test_epsilon_dominio(H, n):
    with pytest.raises(ValueError):
        epsilon_quadrado(H, n)


def test_epsilon_tolerancia_so_para_ruido_numerico():
    assert epsilon_quadrado(9 + 5e-13, 10) == 1
    assert epsilon_quadrado(-5e-13, 10) == 0


@pytest.mark.parametrize("a,b", [([1, 2, 2], [2, 3]), ([5, 6], [0, 1, 2]),
                                ([1, 1], [1, 1]), ([0, 1], [3, 4])])
def test_delta_por_contagem_independente_incluindo_empates_e_inversao(a, b):
    ganhos = sum(x > y for x in a for y in b)
    perdas = sum(x < y for x in a for y in b)
    empates = sum(x == y for x in a for y in b)
    U = ganhos + .5 * empates
    d = cliff_delta(U, len(a), len(b))
    assert d == pytest.approx((ganhos - perdas) / (len(a) * len(b)))
    assert cliff_delta(len(a)*len(b)-U, len(b), len(a)) == pytest.approx(-d)


def test_delta_nao_estimavel_e_contagens_numpy():
    assert cliff_delta(None, 5, 5) is None and cliff_delta(0, 0, 5) is None
    assert cliff_delta(2_500_000_000, np.int32(50_000), np.int32(50_000)) == 1


@pytest.mark.parametrize("U,n1,n2", [(np.nan, 5, 5), (-1, 5, 5), (26, 5, 5),
    (True, 5, 5), ('texto', 5, 5), (0, -1, 5), (0, 5, True), (0, 1.5, 5)])
def test_delta_dominio(U, n1, n2):
    with pytest.raises(ValueError):
        cliff_delta(U, n1, n2)


@pytest.mark.parametrize("valor,classe", [(0, 'desprezivel'), (.146999, 'desprezivel'),
    (.147, 'pequeno'), (-.147, 'pequeno'), (.329999, 'pequeno'), (.33, 'medio'),
    (-.33, 'medio'), (.473999, 'medio'), (.474, 'grande'), (-1, 'grande'), (None, None)])
def test_magnitude_delta_fronteiras_do_enunciado(valor, classe):
    assert magnitude_delta(valor) == classe


@pytest.mark.parametrize("valor", [1.01, np.nan, np.inf, True, 'texto'])
def test_magnitude_delta_invalida(valor):
    with pytest.raises(ValueError):
        magnitude_delta(valor)


def test_familias_18_e_108_antes_de_qualquer_selecao(dados):
    dados["deployment_frequency"] = np.tile(np.arange(10), 4)  # Sem diferença global.
    antes = dados.copy(deep=True)
    r = analisar(dados)
    assert r["familias"]["testes_planejados"].tolist() == [18, 108]
    assert r["familias"]["testes_estimaveis"].tolist() == [18, 108]
    pares = r["pares"]
    df = pares[pares["metrica"] == "deployment_frequency"]
    assert len(df) == 18 and not df["executado_na_171"].any() and not df["relatar_diferenca"].any()
    assert pares["n_familia"].eq(108).all() and len(pares) == 108
    assert pares[["fator", "metrica", "grupo_1", "grupo_2"]].duplicated().sum() == 0
    pd.testing.assert_frame_equal(dados, antes)


def test_efeitos_usam_n_apos_exclusao_e_preservam_resultados_171(dados):
    dados.loc[0, "lead_time_a"] = np.nan
    original = base.analisar(dados)
    r = analisar(dados)
    pd.testing.assert_frame_equal(r["base"]["globais"], original["globais"])
    pd.testing.assert_frame_equal(r["globais"][original["globais"].columns], original["globais"])
    for linha in r["globais"].itertuples():
        assert linha.epsilon2 == pytest.approx(linha.estatistica / (linha.n-1))
        assert linha.n == (39 if linha.metrica == "lead_time_a" else 40)
    bruto = original["pares"].set_index(["fator", "metrica", "grupo_1", "grupo_2"])
    novo = r["pares"].set_index(bruto.index.names)
    np.testing.assert_allclose(novo.loc[bruto.index, 'p_valor_bruto'], bruto['p_valor_bruto'])
    np.testing.assert_allclose(novo.loc[bruto.index, 'U_1'], bruto['U_1'])


def test_pares_requerem_global_e_par_corrigidos(dados, monkeypatch):
    original = aplicar_holm
    def sem_globais(p, *, alpha):
        r = original(p, alpha=alpha)
        if len(p) == 18:
            r['rejeita_holm'] = pd.array([False]*18, dtype='boolean')
        return r
    monkeypatch.setattr('pipeline.inferencia_rq06.aplicar_holm', sem_globais)
    r = analisar(dados)
    assert r['pares']['rejeita_holm'].any() and not r['pares']['relatar_diferenca'].any()


def test_dois_grupos_delta_na_familia_global_sem_duplicar_hipotese(dados):
    dados['estrelas'] = [1]*20 + [2]*20
    r = analisar(dados)
    est = r['globais'][r['globais']['fator'] == 'estrelas']
    assert est['teste'].eq('mann_whitney_direto').all() and est['epsilon2'].isna().all()
    assert est['grupo_1'].eq('G1').all() and est['grupo_2'].eq('G2').all()
    assert est['n_1'].eq(20).all() and est['n_2'].eq(20).all()
    assert est['cliff_delta'].eq(-1).all()
    assert len(r['pares']) == 72 and not r['pares']['fator'].eq('estrelas').any()


def test_nao_estimaveis_nao_diminuem_familia_e_nao_viram_p_zero(dados):
    dados.loc[:8, 'lead_time_a'] = np.nan  # Q1 abaixo do mínimo em cada fator.
    r = analisar(dados)
    assert r['familias']['testes_planejados'].tolist() == [18, 108]
    g = r['globais'][r['globais']['metrica'] == 'lead_time_a']
    assert g['p_valor_holm'].isna().all() and g['epsilon2'].isna().all()
    pares = r['pares'][(r['pares']['metrica']=='lead_time_a') & (r['pares']['grupo_1']=='Q1')]
    assert len(pares) == 9 and pares['p_valor_holm'].isna().all()
    assert pares['cliff_delta'].isna().all() and not pares['relatar_diferenca'].any()


def test_constante_global_e_todos_fatores_ausentes(dados):
    dados['lead_time_a'] = 0
    r = analisar(dados)
    g = r['globais'][r['globais']['metrica']=='lead_time_a']
    assert g['p_valor_holm'].isna().all() and g['epsilon2'].isna().all()
    pares = r['pares'][r['pares']['metrica']=='lead_time_a']
    assert pares['cliff_delta'].eq(0).all() and pares['p_valor_bruto'].eq(1).all()
    assert not pares['relatar_diferenca'].any()
    dados[list(base.FATORES)] = np.nan
    r = analisar(dados)
    assert len(r['globais']) == 18 and r['globais']['p_valor_holm'].isna().all()
    assert r['familias']['testes_estimaveis'].tolist() == [0, 0] and r['pares'].empty
