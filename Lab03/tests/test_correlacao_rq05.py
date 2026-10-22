"""Unidades pareadas, empates, limites e inferência da RQ05 (#170)."""

import hashlib
from itertools import permutations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from pipeline.correlacao_rq05 import (analisar, carregar_dataset, grafico_dispersao,
                                      pares_variantes, spearman)


@pytest.fixture
def dados():
    return pd.DataFrame({
        "id": [4, 3, 2, 1], "full_name": ["o/d", "o/c", "o/b", "o/a"],
        "janela_inicio": ["2025-10-01T00:00:00Z"] * 4,
        "janela_fim_exclusivo": ["2026-10-01T00:00:00Z"] * 4,
        "deployment_frequency": [4., 3., 2., 1.],
        "cfr_a": [0.4, 0.3, 0.2, 0.], "cfr_b": [0.5, None, 0.1, 0.],
        "coleta_incompleta": [False, False, True, False],
        "calculo_parcial": [False, True, False, False],
    })


def test_carregamento_preserva_fonte_zero_hash_e_ordena(dados, tmp_path):
    p = tmp_path / "dados.csv"
    dados.to_csv(p, index=False)
    antes = p.read_bytes()
    d = carregar_dataset(p)
    assert d["id"].tolist() == [1, 2, 3, 4]
    assert d["cfr_b"].isna().sum() == 1 and d.loc[0, "cfr_a"] == 0
    assert d.attrs["csv_sha256"] == hashlib.sha256(antes).hexdigest()
    assert p.read_bytes() == antes


@pytest.mark.parametrize("coluna,valor,erro", [
    ("id", 3, "IDs"), ("id", 0, "IDs"), ("id", 1.5, "IDs"),
    ("full_name", "", "Nome"), ("full_name", "o/c", "duplicado"),
    ("deployment_frequency", -1, "domínio"), ("cfr_a", 1.1, "domínio"),
    ("cfr_b", float("inf"), "domínio"), ("cfr_a", "inválido", "parse"),
    ("cfr_a", True, "parse|domínio"), ("calculo_parcial", "talvez", "booleano"),
    ("coleta_incompleta", None, "booleano"),
    ("janela_inicio", None, "Janela"), ("janela_inicio", "2024-01-01T00:00:00Z", "Janela"),
])
def test_csv_invalido_nao_produz_analise(dados, tmp_path, coluna, valor, erro):
    dados[coluna] = dados[coluna].astype(object)
    dados.loc[0, coluna] = valor
    p = tmp_path / "dados.csv"
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError, match=erro):
        carregar_dataset(p)


def test_contrato_csv_vazio_coluna_ausente_e_fuso(dados, tmp_path):
    p = tmp_path / "dados.csv"
    dados.iloc[:0].to_csv(p, index=False)
    with pytest.raises(ValueError, match="vazio"):
        carregar_dataset(p)
    dados.drop(columns="cfr_b").to_csv(p, index=False)
    with pytest.raises(ValueError, match="Colunas ausentes"):
        carregar_dataset(p)
    dados["janela_inicio"] = "2025-10-01"
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError, match="fuso"):
        carregar_dataset(p)
    dados["janela_inicio"] = "2026-10-01T00:00:00Z"
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError, match="anterior"):
        carregar_dataset(p)


def test_exclusao_por_par_independe_da_outra_variante_e_preserva_zero(dados):
    a, b = pares_variantes(dados, "a"), pares_variantes(dados, "b")
    assert a["id"].tolist() == [1, 2, 3, 4]
    assert b["id"].tolist() == [1, 2, 4] and b.loc[0, "cfr"] == 0
    assert pares_variantes(dados, "a", True)["id"].tolist() == [1, 4]
    with pytest.raises(ValueError, match="Variante"):
        pares_variantes(dados, "c")


@pytest.mark.parametrize("y,rho", [([0, 1, 2, 3], 1.), ([3, 2, 1, 0], -1.)])
def test_monotonicidade_com_permutacao_exata(y, rho):
    r = spearman([1, 2, 3, 4], y, permutacoes=24)
    assert r["rho"] == pytest.approx(rho)
    assert r["p_permutacao"] == pytest.approx(2 / 24)
    assert r["metodo_permutacao"] == "exata" and r["permutacoes_realizadas"] == 24


def test_empates_conferidos_por_enumeracao_independente():
    x, y = [1, 1, 2, 3], [0, 1, 1, 0]
    r = spearman(x, y, permutacoes=24)
    nula = np.array([stats.spearmanr(x, p).statistic for p in permutations(y)])
    limite = 1e-12
    p = min(1., 2 * min(np.mean(nula <= r["rho"] + limite), np.mean(nula >= r["rho"] - limite)))
    assert r["p_permutacao"] == pytest.approx(p)
    # Pearson nos valores não é a correlação de postos com empates.
    rx, ry = pd.Series(x).rank(), pd.Series(y).rank()
    assert r["rho"] == pytest.approx(np.corrcoef(rx, ry)[0, 1])


def test_permutacao_aleatoria_reproduzivel_e_p_nunca_zero():
    r = spearman(np.arange(15), np.arange(15), permutacoes=99, semente=170)
    assert r == spearman(np.arange(15), np.arange(15), permutacoes=99, semente=170)
    assert r["metodo_permutacao"] == "aleatoria" and r["permutacoes_realizadas"] == 99
    assert r["p_permutacao"] >= 2 / 100


@pytest.mark.parametrize("x,y,motivo", [([], [], "menos_de_tres_pares"),
    ([1, 2], [2, 1], "menos_de_tres_pares"), ([1, 1, 1], [1, 2, 3], "variavel_constante"),
    ([1, 2, 3], [0, 0, 0], "variavel_constante")])
def test_correlacao_nao_estimavel_nao_vira_zero(x, y, motivo):
    r = spearman(x, y)
    assert r["rho"] is None and r["p_valor"] is None and r["p_permutacao"] is None
    assert r["n"] == len(x) and r["motivo"] == motivo


@pytest.mark.parametrize("x,y,opcoes", [([1], [1, 2], {}), ([[1, 2]], [[1, 2]], {}),
    ([1, np.nan], [2, 3], {}), ([1, np.inf], [2, 3], {}),
    ([1], [2], {"permutacoes": 0}), ([1], [2], {"permutacoes": True}),
    ([1], [2], {"semente": -1}), ([1], [2], {"semente": True})])
def test_pares_e_parametros_invalidos(x, y, opcoes):
    with pytest.raises(ValueError):
        spearman(x, y, **opcoes)


def test_analise_distingue_principal_sensibilidade_nulos_e_flags(dados):
    antes = dados.copy(deep=True)
    r, pares = analisar(dados, permutacoes=24)
    assert r["n"].tolist() == [4, 3, 2, 2]
    assert r["n_universo"].tolist() == [4, 4, 2, 2]
    assert r["excluidos_por_nulos"].tolist() == [0, 1, 0, 0]
    assert r["fora_do_recorte"].tolist() == [0, 0, 2, 2]
    assert pares.groupby(["recorte", "variante"]).size().sum() == 11
    pd.testing.assert_frame_equal(dados, antes)


def test_grafico_usa_pares_do_calculo_mantem_zero_e_escala_log(dados):
    r, pares = analisar(dados, permutacoes=24)
    fig = grafico_dispersao(pares, r)
    for ax, n in zip(fig.axes, (4, 3)):
        pontos = ax.collections[0].get_offsets()
        assert len(pontos) == n and min(pontos[:, 1]) == 0
        assert ax.get_xscale() == "log" and ax.get_yscale() == "linear"
    plt.close(fig)
    dados.loc[3, "deployment_frequency"] = 0
    dados["cfr_a"] = 0
    r, pares = analisar(dados, permutacoes=24)
    fig = grafico_dispersao(pares, r)
    assert all(ax.get_xscale() == "symlog" for ax in fig.axes)
    assert "Não estimável" in fig.axes[0].texts[0].get_text()
    plt.close(fig)
