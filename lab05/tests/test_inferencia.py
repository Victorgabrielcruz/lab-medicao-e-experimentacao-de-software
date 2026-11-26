"""Testes numéricos e falhas de desenho, sem executar o benchmark (#309)."""

from collections import Counter
from itertools import combinations
import json
import math

import numpy as np
import pandas as pd
import pytest

from experimento import config, inferencia
from analisar_dados import main


@pytest.fixture(scope="module")
def dados_reais():
    return pd.read_csv(config.DIR_DADOS / "coleta-completa-01" / "resultados.csv")


def dados_sinteticos(tipo="constante"):
    linhas = []
    for carga in config.CARGAS:
        for i, cfg in enumerate(config.CONFIGURACOES):
            for r in range(1, 31):
                if tipo == "tendencia":
                    vazao = 100 + i * r
                elif tipo == "empates":
                    vazao = 10
                else:
                    vazao = 10 * 2**i * (r * r if tipo == "multiplicativo" else 1)
                linhas.append({
                    "carga": carga.nome, "configuracao": cfg.nome, "repeticao": r,
                    "semente_carga": 2**63 + r, "n_operacoes": carga.n_operacoes,
                    "tempo_total_s": carga.n_operacoes / vazao, "vazao_ops_s": vazao,
                    "data_hora_utc": "2026-11-25T19:42:58+00:00",
                })
    return pd.DataFrame(linhas)


def test_sinais_empates_e_p_valor_exato_conhecido():
    resultado = inferencia.teste_sinais([4, -1, 0, 3, 1, 2])
    assert resultado["ganhos"] == 4
    assert resultado["perdas"] == 1
    assert resultado["empates"] == 1
    assert resultado["n_efetivo"] == 5
    assert resultado["probabilidade"] == 4 / 5
    assert resultado["p_bruto"] == 12 / 32


def test_ic_exato_com_todos_ganhos_e_inversao_do_sentido():
    positivos = inferencia.teste_sinais([1] * 30)
    negativos = inferencia.teste_sinais([-1] * 30)
    assert positivos["p_bruto"] == negativos["p_bruto"] == 2 / 2**30
    assert positivos["ic_inf"] == pytest.approx(0.025 ** (1 / 30))
    assert positivos["ic_sup"] == 1
    assert negativos["ic_inf"] == 0
    assert negativos["ic_sup"] == pytest.approx(1 - positivos["ic_inf"])


def test_todos_empates_nao_inventam_estimativa_de_probabilidade():
    resultado = inferencia.teste_sinais([0] * 30)
    assert resultado["p_bruto"] == 1
    assert resultado["n_efetivo"] == 0
    assert resultado["probabilidade"] is None
    assert resultado["ic_inf"] is resultado["ic_sup"] is None


@pytest.mark.parametrize("valores", [[], [math.nan], [math.inf], [[1, 2]]])
def test_sinais_recusa_entradas_invalidas(valores):
    with pytest.raises(ValueError):
        inferencia.teste_sinais(valores)


def test_holm_na_ordem_original_com_ajuste_monotonico():
    assert inferencia.holm([0.04, 0.001, 0.03, 0.2]).tolist() == pytest.approx([0.09, 0.004, 0.09, 0.2])
    assert inferencia.holm([0.01, 0.01, 0.5]).tolist() == pytest.approx([0.03, 0.03, 0.5])
    assert inferencia.holm([1, 1]).tolist() == [1, 1]


@pytest.mark.parametrize("valores", [[], [-0.1], [1.1], [math.nan]])
def test_holm_recusa_valores_p_invalidos(valores):
    with pytest.raises(ValueError):
        inferencia.holm(valores)


def test_runs_exato_contra_enumeracao_de_todas_as_sequencias():
    sequencias = []
    for positivos in combinations(range(8), 3):
        sequencia = [1 if i in positivos else -1 for i in range(8)]
        runs = 1 + sum(a != b for a, b in zip(sequencia, sequencia[1:]))
        sequencias.append((sequencia, runs))
    frequencias = Counter(r for _, r in sequencias)
    for sequencia, r in sequencias:
        inferior = sum(q for numero, q in frequencias.items() if numero <= r)
        superior = sum(q for numero, q in frequencias.items() if numero >= r)
        esperado = min(1, 2 * min(inferior, superior) / len(sequencias))
        resultado = inferencia.teste_sequencias(sequencia)
        assert resultado["runs"] == r
        assert resultado["p_bruto"] == pytest.approx(esperado)


def test_runs_constantes_e_zeros_sao_inconclusivos():
    assert inferencia.teste_sequencias([1] * 30)["p_bruto"] is None
    assert inferencia.teste_sequencias([0] * 30)["n"] == 0
    assert inferencia.teste_sequencias([0] * 30)["p_bruto"] is None
    assert inferencia.teste_sequencias([1, 0, -1, 1])["runs"] == 3


def test_diagnosticos_de_tendencia_e_constantes():
    resultado = inferencia.diagnosticar(np.arange(1, 31))
    assert resultado["spearman_diferencas"] == pytest.approx(1)
    assert resultado["lag1_diferencas"] == pytest.approx(1)
    assert resultado["lag1_sinais"] is None
    assert resultado["mediana_primeira_metade"] == 8
    assert resultado["mediana_segunda_metade"] == 23
    assert inferencia.diagnosticar([3] * 30)["spearman_diferencas"] is None


def test_efeitos_e_intervalos_com_valores_constantes_conhecidos():
    resultado = inferencia.analisar(dados_sinteticos(), n_bootstrap=200)
    assert len(resultado.testes) == 9
    assert len(resultado.efeitos) == 63
    assert len(resultado.medianas) == 24
    assert len(resultado.auditoria) == 18
    assert len(resultado.series) == 270
    assert resultado.testes.p_holm.tolist() == pytest.approx([9 * 2 / 2**30] * 9)
    assert resultado.testes.rejeita_condicional.all()
    for carga in config.CARGAS:
        efeitos = resultado.efeitos[resultado.efeitos.carga == carga.nome].set_index(["hipotese", "efeito"])
        for h, razao in (("H1", 4), ("H2", 2), ("H3", 2)):
            assert efeitos.loc[(h, "M3"), "estimativa"] == razao
            assert efeitos.loc[(h, "M3"), "ic_inf"] == razao
            assert efeitos.loc[(h, "M3"), "ic_sup"] == razao
            assert efeitos.loc[(h, "Probabilidade de ganho"), "estimativa"] == 1
            assert efeitos.loc[(h, "Efeito dos sinais (2p−1)"), "estimativa"] == 1
        assert efeitos.loc[("H1", "Diferença M1"), "estimativa"] == pytest.approx(-0.075 * carga.n_operacoes)
        assert efeitos.loc[("H1", "Diferença M2"), "estimativa"] == 30
        assert efeitos.loc[("H1", "Redução M1"), "estimativa"] == 75


def test_bootstrap_preserva_mesmas_rodadas_nas_quatro_configuracoes():
    resultado = inferencia.analisar(dados_sinteticos("multiplicativo"), n_bootstrap=400)
    razoes = resultado.efeitos[resultado.efeitos.efeito == "M3"]
    # Sem reamostragem pareada, as razões seriam variáveis, pois a carga varia muito.
    for _, linha in razoes.iterrows():
        esperado = 4 if linha.hipotese == "H1" else 2
        assert linha.estimativa == esperado
        assert linha.ic_inf == pytest.approx(esperado)
        assert linha.ic_sup == pytest.approx(esperado)


def test_pareamento_nao_depende_da_ordem_das_linhas(dados_reais):
    primeiro = inferencia.analisar(dados_reais, n_bootstrap=400)
    embaralhado = inferencia.analisar(dados_reais.sample(frac=1, random_state=13), n_bootstrap=400)
    pd.testing.assert_frame_equal(primeiro.testes, embaralhado.testes)
    pd.testing.assert_frame_equal(primeiro.efeitos, embaralhado.efeitos)
    pd.testing.assert_frame_equal(primeiro.auditoria, embaralhado.auditoria)


def test_semente_reproduz_ic_e_nova_semente_muda_apenas_reamostragem(dados_reais):
    a = inferencia.analisar(dados_reais, n_bootstrap=400, semente=42)
    b = inferencia.analisar(dados_reais, n_bootstrap=400, semente=42)
    c = inferencia.analisar(dados_reais, n_bootstrap=400, semente=43)
    pd.testing.assert_frame_equal(a.efeitos, b.efeitos)
    pd.testing.assert_frame_equal(a.testes, c.testes)
    assert not a.efeitos.ic_inf.equals(c.efeitos.ic_inf)


def test_alerta_temporal_suspende_conclusao_mesmo_com_p_muito_pequeno():
    resultado = inferencia.analisar(dados_sinteticos("tendencia"), n_bootstrap=200)
    assert resultado.testes.rejeita_condicional.all()
    assert resultado.testes.alerta_temporal.all()
    assert resultado.testes.decisao.str.contains("suspensa").all()
    assert resultado.auditoria[resultado.auditoria.serie == "diferenças em torno da mediana"].alerta.all()


def test_empates_preservados_nos_efeitos_e_json_sem_nan():
    resultado = inferencia.analisar(dados_sinteticos("empates"), n_bootstrap=200)
    assert resultado.testes.p_holm.tolist() == [1] * 9
    assert resultado.testes.empates.tolist() == [30] * 9
    assert resultado.testes.decisao.eq("Sem pares informativos").all()
    assert resultado.efeitos[resultado.efeitos.efeito == "M3"].estimativa.eq(1).all()
    assert resultado.efeitos[resultado.efeitos.efeito == "Diferença M1"].estimativa.eq(0).all()
    texto = json.dumps(resultado.como_dict(), allow_nan=False)
    assert 'null' in texto


@pytest.mark.parametrize("falha", ["ausente", "duplicada", "rodada", "semente", "semente_float", "ambiente", "nan", "zero", "vazao", "volume", "configuracao"])
def test_desenho_invalido_nao_chega_a_inferencia(dados_reais, falha):
    dados = dados_reais.copy()
    if falha == "ausente":
        dados = dados.iloc[:-1]
    elif falha == "duplicada":
        dados.iloc[-1] = dados.iloc[0]
    elif falha == "rodada":
        dados.loc[0, "repeticao"] = 31
    elif falha == "semente":
        dados.loc[0, "semente_carga"] = 1
    elif falha == "semente_float":
        dados["semente_carga"] = dados.semente_carga.astype(float)
    elif falha == "ambiente":
        dados.loc[0, "data_hora_utc"] = "outro momento"
    elif falha in ("nan", "zero"):
        dados.loc[0, "tempo_total_s"] = math.nan if falha == "nan" else 0
    elif falha == "vazao":
        dados.loc[0, "vazao_ops_s"] = 1
    elif falha == "volume":
        dados.loc[0, "n_operacoes"] = 1
    else:
        dados.loc[0, "configuracao"] = "OUTRA"
    with pytest.raises(ValueError):
        inferencia.analisar(dados, n_bootstrap=10)


def test_piloto_nao_e_usado_nem_misturado(dados_reais):
    piloto = pd.read_csv(config.DIR_DADOS / "piloto" / "resultados.csv")
    for dados in (piloto, pd.concat([dados_reais, piloto])):
        with pytest.raises(ValueError, match="360"):
            inferencia.analisar(dados, n_bootstrap=10)


@pytest.mark.parametrize("argumentos", [{"n_bootstrap": 0}, {"n_bootstrap": 1.5}, {"semente": -1}])
def test_parametros_invalidos(dados_reais, argumentos):
    with pytest.raises(ValueError):
        inferencia.analisar(dados_reais, **argumentos)


def test_coleta_real_mantem_familia_e_escopo_condicional(dados_reais):
    resultado = inferencia.analisar(dados_reais)
    assert resultado.parametros["familia_testes"] == 9
    assert resultado.parametros["n_bootstrap"] == 10_000
    assert "não comprova independência" in resultado.parametros["escopo"]
    assert resultado.testes.rejeita_condicional.sum() == 7
    leitura = resultado.testes[resultado.testes.carga == "leitura"].set_index("hipotese")
    assert leitura.loc["H2", "ganhos"] == 16
    assert leitura.loc["H3", "ganhos"] == 12
    assert leitura.loc["H2", "p_holm"] == pytest.approx(0.8555355519056321)
    assert leitura.loc["H3", "p_holm"] == pytest.approx(0.72318921610713)
    assert not resultado.testes.alerta_temporal.any()
    assert resultado.auditoria.p_bruto.isna().sum() == 7


def test_cli_gera_json_reproduzivel_sem_sobrescrever(tmp_path):
    saida = tmp_path / "analise.json"
    main(["--saida", str(saida)])
    original = saida.read_bytes()
    relatorio = json.loads(original)
    assert len(relatorio["testes"]) == 9
    assert len(relatorio["efeitos"]) == 63
    assert relatorio["origem"]["sha256_csv"] == "595eba4d16b1c8fbe4550a2d2f2d545c13932b49d10e6e3ff93f8b5a9214eacc"
    with pytest.raises(SystemExit) as erro:
        main(["--saida", str(saida)])
    assert erro.value.code == 2
    assert saida.read_bytes() == original
