"""Agrupamento fixo, validade das entradas e testes da RQ06 (#171)."""

import hashlib
import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from pipeline.comparacao_rq06 import (COLUNAS_POSTHOC, COLUNAS_RESUMOS, FATORES,
                                     METRICAS, agrupar_quartis, analisar, carregar_dataset, comparar_grupos)


@pytest.fixture
def dados():
    n = 40
    d = pd.DataFrame({"id": np.arange(1, n+1), "full_name": [f"org/r{i}" for i in range(1, n+1)],
                      "janela_inicio": ["2025-10-01T00:00:00Z"] * n,
                      "janela_fim_exclusivo": ["2026-10-01T00:00:00Z"] * n})
    for i, c in enumerate(FATORES):
        d[c] = np.arange(1, n+1) * (i+1)
    for c in METRICAS:
        d[c] = np.arange(n) / (n-1) if c.startswith("cfr") else np.arange(n, dtype=float)
    return d


def test_csv_hash_ordem_e_fonte_intacta(dados, tmp_path):
    p = tmp_path / "dados.csv"
    dados.iloc[::-1].to_csv(p, index=False)
    antes = p.read_bytes()
    d = carregar_dataset(p)
    assert d["id"].tolist() == dados["id"].tolist()
    assert d.attrs["csv_sha256"] == hashlib.sha256(antes).hexdigest()
    assert d.loc[0, "cfr_b"] == 0 and p.read_bytes() == antes


@pytest.mark.parametrize("coluna,valor", [("id", 2), ("id", 0), ("id", 1.5),
    ("full_name", None), ("full_name", "org/r2"), ("full_name", "sem_barra"),
    ("estrelas", -1), ("contribuidores", 2.5), ("idade_dias", float("inf")),
    ("lead_time_a", -1), ("lead_time_b", "texto"), ("cfr_a", 1.01),
    ("cfr_b", float("inf")), ("tempo_recuperacao", True),
    ("janela_inicio", "2024-01-01T00:00:00Z"), ("janela_inicio", "2025-10-01"),
    ("janela_inicio", None)])
def test_csv_invalido_rejeitado(dados, tmp_path, coluna, valor):
    dados[coluna] = dados[coluna].astype(object)
    dados.loc[0, coluna] = valor
    p = tmp_path / "dados.csv"
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError):
        carregar_dataset(p)


def test_csv_vazio_coluna_ausente_booleano_e_janela_invertida(dados, tmp_path):
    p = tmp_path / "dados.csv"
    dados.iloc[:0].to_csv(p, index=False)
    with pytest.raises(ValueError, match="vazio"):
        carregar_dataset(p)
    dados.drop(columns="estrelas").to_csv(p, index=False)
    with pytest.raises(ValueError, match="Colunas ausentes"):
        carregar_dataset(p)
    dados["cfr_b"] = True
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError, match="domínio"):
        carregar_dataset(p)
    dados["cfr_b"] = 0.5
    dados["janela_inicio"] = "2026-10-01T00:00:00Z"
    dados.to_csv(p, index=False)
    with pytest.raises(ValueError, match="anterior"):
        carregar_dataset(p)


def test_cortes_quartis_na_populacao_e_intervalos_fechados_a_direita(dados):
    grupos, cortes = agrupar_quartis(dados)
    c = cortes[cortes["fator"] == "estrelas"]
    assert c["limite_superior"].tolist() == [10.75, 20.5, 30.25, 40]
    assert c["inclui_inferior"].tolist() == [True, False, False, False]
    assert c["n_grupo"].tolist() == [10] * 4
    assert grupos.loc[0, "grupo_estrelas"] == "Q1" and grupos.loc[39, "grupo_estrelas"] == "Q4"


def test_empates_nao_separados_por_id_e_cortes_repetidos_nao_criam_quartis_ficticios(dados):
    dados["estrelas"] = [1] * 20 + [2] * 20
    g, c = agrupar_quartis(dados)
    c = c[c["fator"] == "estrelas"]
    assert c["grupo"].tolist() == ["G1", "G2"] and c["grupos_efetivos"].tolist() == [2, 2]
    assert g.groupby("estrelas")["grupo_estrelas"].nunique().eq(1).all()
    baralhado = dados.sample(frac=1, random_state=171)
    g2, _ = agrupar_quartis(baralhado)
    pd.testing.assert_series_equal(g.set_index("id")["grupo_estrelas"].sort_index(),
                                   g2.set_index("id")["grupo_estrelas"].sort_index())


def test_fator_ausente_constante_e_intervalos_vazios(dados):
    dados["estrelas"] = np.nan
    dados["contribuidores"] = 1
    dados["idade_dias"] = np.nan
    dados.loc[:1, "idade_dias"] = [1, 2]
    g, c = agrupar_quartis(dados)
    assert g["grupo_estrelas"].isna().all()
    assert set(g["grupo_contribuidores"]) == {"G1"}
    assert c.loc[c["fator"] == "estrelas", "motivo"].iloc[0] == "fator_sem_valores"
    assert c.loc[c["fator"] == "contribuidores", "motivo"].iloc[0] == "fator_constante"
    assert c.loc[c["fator"] == "idade_dias", "n_grupo"].tolist() == [1, 1]


def test_kruskal_com_empates_calculado_independentemente():
    # Três grupos de cinco valores empatados: H bruto=12,5; correção=25/28.
    r = comparar_grupos([[0]*5, [1]*5, [2]*5])
    assert r["teste"] == "kruskal_wallis"
    assert r["estatistica"] == pytest.approx(14)
    assert r["p_valor_bruto"] == pytest.approx(math.exp(-7))  # Qui-quadrado, df=2.


def test_mann_whitney_direto_orientacao_u_e_simetria_do_p():
    a, b = [0, 0, 1, 1, 2], [1, 1, 2, 3, 3]
    u = sum(float(x > y) + .5 * float(x == y) for x in a for y in b)
    r, inverso = comparar_grupos([a, b]), comparar_grupos([b, a])
    assert r["teste"] == "mann_whitney_direto" and r["estatistica"] == u
    assert inverso["estatistica"] == 25 - u
    assert r["p_valor_bruto"] == inverso["p_valor_bruto"]


@pytest.mark.parametrize("amostras,motivo", [([], "menos_de_dois_grupos"),
    ([[1]*5], "menos_de_dois_grupos"), ([[1]*5, []], "grupo_abaixo_do_minimo"),
    ([[1]*4, [2]*5, [3]*5], "grupo_abaixo_do_minimo"),
    ([[1]*5]*4, "todos_os_valores_iguais")])
def test_nao_estimavel_preserva_motivo_sem_p_zero(amostras, motivo):
    r = comparar_grupos(amostras)
    assert r["motivo"] == motivo and r["estatistica"] is None and r["p_valor_bruto"] is None


@pytest.mark.parametrize("amostras,minimo", [([[np.nan]], 5), ([[np.inf]], 5), ([[[1]]], 5),
    ([[1]*5, [2]*5], 4), ([[1]*5, [2]*5], True)])
def test_grupos_invalidos_nao_entram_no_teste(amostras, minimo):
    with pytest.raises(ValueError):
        comparar_grupos(amostras, minimo_grupo=minimo)


def test_minimo_mais_restritivo_e_reportado_corretamente():
    r = comparar_grupos([[1]*8, [2]*8], minimo_grupo=10)
    assert r["motivo"] == "grupo_abaixo_do_minimo" and r["minimo_grupo"] == 10


def test_18_testes_e_todos_os_seis_pares_quando_ha_diferenca(dados):
    antes = dados.copy(deep=True)
    r = analisar(dados)
    assert len(r["globais"]) == 18 and len(r["resumos"]) == 72
    assert r["globais"]["poshoc_executado"].all() and len(r["pares"]) == 18 * 6
    for (fator, metrica), pares in r["pares"].groupby(["fator", "metrica"]):
        assert len(pares) == 6 and pares[["grupo_1", "grupo_2"]].duplicated().sum() == 0
        for _, linha in pares.iterrows():
            g = r["grupos"][f"grupo_{fator}"]
            a, b = [dados.loc[g == rotulo, metrica].to_numpy() for rotulo in (linha["grupo_1"], linha["grupo_2"])]
            u = sum(float(x > y) + .5 * float(x == y) for x in a for y in b)
            assert linha["U_1"] == u and linha["n_1"] == len(a) and linha["n_2"] == len(b)
    pd.testing.assert_frame_equal(dados, antes)


def test_sem_diferenca_nao_dispara_pos_teste_e_exclusao_por_metrica(dados):
    dados["deployment_frequency"] = np.tile(np.arange(10), 4)
    dados.loc[0, "lead_time_a"] = np.nan
    r = analisar(dados)
    globais = r["globais"]
    df = globais[globais["metrica"] == "deployment_frequency"]
    assert df["p_valor_bruto"].eq(1).all() and not df["poshoc_executado"].any()
    assert not (r["pares"]["metrica"] == "deployment_frequency").any()
    lt = globais[globais["metrica"] == "lead_time_a"]
    assert lt["n"].eq(39).all() and lt["ausentes_metrica_com_fator"].eq(1).all()
    assert globais[globais["metrica"] == "cfr_a"]["n"].eq(40).all()
    assert r["cortes"]["n_grupo"].eq(10).all()  # Sem recortar os quartis pela métrica.


def test_dois_grupos_usam_mann_whitney_direto_sem_poshoc(dados):
    dados["estrelas"] = [1] * 20 + [2] * 20
    r = analisar(dados)
    est = r["globais"][r["globais"]["fator"] == "estrelas"]
    assert est["teste"].eq("mann_whitney_direto").all()
    assert est["motivo_poshoc"].eq("comparacao_direta").all()
    assert not (r["pares"]["fator"] == "estrelas").any()


def test_sem_dados_validos_mantem_esquemas_e_exclusoes(dados):
    dados[list(FATORES)] = np.nan
    r = analisar(dados)
    assert len(r["globais"]) == 18 and r["globais"]["n"].eq(0).all()
    assert r["globais"]["ausentes_fator"].eq(40).all()
    assert list(r["pares"].columns) == list(COLUNAS_POSTHOC) and r["pares"].empty
    assert list(r["resumos"].columns) == list(COLUNAS_RESUMOS) and r["resumos"].empty


@pytest.mark.parametrize("alpha", [0, 1, -1, True, None, np.nan])
def test_alpha_invalido(dados, alpha):
    with pytest.raises(ValueError, match="Alpha"):
        analisar(dados, alpha=alpha)
