import csv
from pathlib import Path
import json

import pytest
from streamlit.testing.v1 import AppTest

from hipotese.config import CORES_TESTES, URL_PROJECT, URL_REPOSITORIO
from hipotese.exemplo import gerar_exemplo
from hipotese.simulacao import ARQUIVO

APP = Path(__file__).resolve().parents[1] / "app.py"

SECOES_ESPERADAS = [
    "1. Cenário",
    "2. Os dados",
    "3. Como os testes funcionam",
    "4. Erro tipo I",
    "5. Poder",
    "6. Dados reais",
    "7. Conclusão",
]


def executar():
    app = AppTest.from_file(str(APP)).run(timeout=10)
    assert not app.exception
    return app


def test_secoes_na_ordem_do_roteiro():
    assert [h.value for h in executar().header] == SECOES_ESPERADAS


@pytest.mark.parametrize("url", ["http://127.0.0.1:8502/", "https://lab04.example.org/"])
def test_links_no_topo(monkeypatch, url):
    import streamlit as st

    monkeypatch.setattr(type(st.context), "url", property(lambda _: url))
    topo = executar().markdown[0].value
    assert f"[Dashboard]({url})" in topo
    assert URL_REPOSITORIO in topo
    assert URL_PROJECT in topo


def test_cenario_apresenta_protocolo_e_calibracao_sem_placeholder():
    app = executar()
    texto = "\n".join(elemento.value for elemento in app.markdown)
    for trecho in (
        "pytest-dev/pytest", "H₀: p = 0,05", "H₁: p > 0,05",
        "unicaudal à direita", "243 observações", "10 falhas",
        "0,05 + efeito", "pontos percentuais", "Expectativa registrada antes",
        "ambos", "compara essas expectativas com os resultados",
    ):
        assert trecho in texto
    assert all("#264" not in info.value for info in app.info)
    tabela = app.table[0].value
    assert list(tabela["n (builds)"]) == [243, 243, 20]
    assert tabela.iloc[1]["Correlação de lag 1"] == 0.2740723078825129


def test_dashboard_exibe_os_resultados_calculados_e_a_interpretacao_do_exemplo():
    app = executar()
    exemplo = gerar_exemplo()
    tabela = app.table[1].value
    assert list(tabela["Teste"]) == [r.teste for r in exemplo.resultados]
    for indice, resultado in enumerate(exemplo.resultados):
        linha = tabela.iloc[indice]
        assert linha["p-valor"] == resultado.pvalor
        assert linha["Valor da estatística"] == resultado.estatistica
        assert linha["Efeito observado (p.p.)"] == resultado.efeito_pp
        assert linha["Decisão (α = 0,05)"] == ("Rejeitar H₀" if resultado.rejeita_h0 else "Não rejeitar H₀")
    texto = "\n".join(elemento.value for elemento in app.markdown)
    assert f"{exemplo.resultados[0].falhas} falhas em 243 builds" in texto
    assert "sem correção de continuidade" in texto
    for resultado in exemplo.resultados:
        conclusao = (
            "há evidência de que a taxa de falha ultrapassa 5%" if resultado.rejeita_h0
            else "não há evidência suficiente de que a taxa de falha ultrapassa 5%"
        )
        assert f"**{resultado.teste}:** p-valor = {resultado.pvalor:.6g}" in texto
        assert conclusao in texto
    assert all("#268" not in info.value for info in app.info)


def test_secao_dados_exibe_g1_e_interpreta_as_amostras_em_quatro_frases():
    app = executar()
    assert all("#267" not in info.value for info in app.info)
    texto = next(elemento.value for elemento in app.markdown if "Os dados reais são binários" in elemento.value)
    assert len(texto.split(". ")) == 4
    for trecho in (
        "10 falhas em 243 builds", "4,12%", "assimetria à direita", "não são outliers",
        "n = 243", "p = 5%", "H₀", "semente 42", "não substituem a meta", "rajadas",
    ):
        assert trecho in texto
    graficos = [json.loads(elemento.proto.spec) for elemento in app.get("plotly_chart")]
    assert [figura["layout"]["title"]["text"][:2] for figura in graficos[:3]] == ["G1", "G2", "G2"]
    real, simulado = graficos[0]["data"]
    assert real["customdata"] == [[233, 243], [10, 243]]
    assert simulado["customdata"] == [[231, 243], [12, 243]]


def test_dashboard_interpreta_tambem_um_resultado_com_rejeicao(monkeypatch):
    import numpy as np
    from hipotese import exemplo as modulo_exemplo
    from hipotese.testes import aplicar_testes

    builds = np.array([1] * 40 + [0] * 203)
    exemplo = modulo_exemplo.ExemploSimulado(builds, 0.09, aplicar_testes(builds))
    monkeypatch.setattr(modulo_exemplo, "gerar_exemplo", lambda: exemplo)
    app = executar()
    assert list(app.table[1].value["Decisão (α = 0,05)"]) == ["Rejeitar H₀", "Rejeitar H₀"]
    texto = "\n".join(elemento.value for elemento in app.markdown)
    assert "há evidência de que a taxa de falha ultrapassa 5%" in texto


def test_q3_aparece_na_secao_de_poder_com_tabelas_e_explicacao():
    app = executar()
    subtitulos = [s.value for s in app.subheader]
    assert "Q3 · Quando os dados não se comportam bem (#272)" in subtitulos
    texto = "\n".join(elemento.value for elemento in app.markdown)
    for trecho in (
        "Amostra pequena prejudica a aproximação do Z", "Rajadas afetam os dois",
        "níveis efetivos de erro tipo I diferentes", "±0,43 p.p.",
    ):
        assert trecho in texto
    tabelas = [elemento.value for elemento in app.table]
    tipo_i = next(tabela for tabela in tabelas if {"Situação", "Erro tipo I"} <= set(tabela.columns))
    assert list(tipo_i["Situação"]) == ["Independente"] * 2 + ["Rajadas"] * 2 + ["Amostra pequena"] * 2
    poderes = [tabela for tabela in tabelas if "Z − binomial (p.p.)" in tabela.columns]
    assert len(poderes) == 2
    assert all(list(tabela["Efeito (p.p.)"]) == ["0", "2", "4", "6", "8", "10"] for tabela in poderes)


def test_q1_exibe_taxas_da_situacao_independente_e_comparacao_com_a_margem():
    app = executar()
    tabela = app.table[2].value
    assert list(tabela["Falsos positivos"]) == [655, 396]
    assert list(tabela["Erro tipo I (%)"]) == [6.55, 3.96]
    assert list(tabela["Desvio de 5% (p.p.)"]) == [1.55, -1.04]
    assert list(tabela["Classificação"]) == ["Liberal", "Conservador"]
    texto = "\n".join(elemento.value for elemento in app.markdown)
    for trecho in (
        "10.000 amostras independentes de 243 builds", "efeito zero",
        "5% ± 0,4 p.p.", "4,60% a 5,40%", "incluindo os limites",
        "6,55%", "3,96%", "liberal", "conservador", "6,39%", "3,73%",
    ):
        assert trecho in texto


def test_g3_exibe_as_seis_taxas_sob_h0_e_a_referencia_de_5_por_cento():
    app = executar()
    graficos = [json.loads(elemento.proto.spec) for elemento in app.get("plotly_chart")]
    g3 = next(figura for figura in graficos if figura["layout"]["title"]["text"].startswith("G3"))
    situacoes = ["Independente", "Rajadas", "Amostra pequena"]
    with ARQUIVO.open(encoding="utf-8", newline="") as arquivo:
        taxas = {(linha["situacao"], linha["teste"]): 100 * float(linha["proporcao_rejeicao"])
                 for linha in csv.DictReader(arquivo) if float(linha["efeito"]) == 0}
    assert len(g3["data"]) == 2
    assert {barra["name"] for barra in g3["data"]} == set(CORES_TESTES)
    for barra in g3["data"]:
        assert barra["x"] == situacoes
        assert barra["y"] == [taxas[situacao, barra["name"]] for situacao in situacoes]
        assert barra["marker"]["color"] == CORES_TESTES[barra["name"]]
    layout = g3["layout"]
    assert layout["barmode"] == "group"
    assert "categoria" in layout["xaxis"]["title"]["text"]
    assert "%" in layout["yaxis"]["title"]["text"]
    referencia, = layout["shapes"]
    assert referencia["y0"] == referencia["y1"] == 5
    assert referencia["line"]["dash"] == "dash" and referencia["showlegend"]
    assert referencia["name"] == "Referência: 5%"
    assert all("#273" not in info.value for info in app.info)

    texto = next(elemento.value for elemento in app.markdown if "Nenhuma das taxas ficou perto" in elemento.value)
    assert "±0,43 p.p." in texto
    for trecho in (
        "Independente**: o Z ficou liberal (6,55%) e o binomial exato ficou conservador (3,96%)",
        "Rajadas**: o Z ficou liberal (11,83%) e o binomial exato ficou liberal (8,60%)",
        "Amostra pequena**: o Z ficou liberal (7,35%) e o binomial exato ficou conservador (1,49%)",
    ):
        assert trecho in texto


def test_q1_interpreta_taxas_dentro_da_margem_sem_rotulos_fixos(monkeypatch):
    from dataclasses import replace
    from hipotese import erro_tipo_i

    resultados = [replace(r, rejeicoes=500, taxa_erro=0.05, desvio_pp=0,
                         classificacao="Dentro da margem") for r in erro_tipo_i.analisar_erro_tipo_i()]
    monkeypatch.setattr(erro_tipo_i, "analisar_erro_tipo_i", lambda: resultados)
    app = executar()
    assert list(app.table[2].value["Classificação"]) == ["Dentro da margem", "Dentro da margem"]
    texto = next(elemento.value for elemento in app.markdown if "O Z teve" in elemento.value)
    assert "liberal" not in texto and "conservador" not in texto
    assert texto.count("dentro da faixa") == 2


def test_q2_exibe_os_seis_efeitos_e_as_taxas_independentes():
    app = executar()
    tabela = app.table[3].value
    assert list(tabela["Efeito (p.p.)"]) == [0, 2, 4, 6, 8, 10]
    assert list(tabela["Medida"]) == ["Erro tipo I"] + ["Poder"] * 5
    assert list(tabela["Z para proporção (%)"]) == [6.55, 43.58, 83.4, 97.59, 99.67, 99.98]
    assert list(tabela["Binomial exato (%)"]) == [3.96, 34.28, 76.73, 96.16, 99.47, 99.97]


def test_g4_exibe_os_dois_testes_por_situacao_com_os_valores_do_csv():
    app = executar()
    g4 = next(
        spec for spec in (json.loads(grafico.proto.spec) for grafico in app.get("plotly_chart"))
        if spec["layout"]["title"]["text"].startswith("G4")
    )
    assert g4["layout"]["title"]["text"].startswith("G4")
    assert len(g4["data"]) == 6
    with ARQUIVO.open(encoding="utf-8", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))
    for indice, situacao in enumerate(("Independente", "Rajadas", "Amostra pequena")):
        assert g4["layout"]["annotations"][indice]["text"].startswith(situacao)
        curvas = g4["data"][2 * indice:2 * indice + 2]
        assert {curva["name"] for curva in curvas} == set(CORES_TESTES)
        for curva in curvas:
            esperado = sorted(
                (100 * float(linha["efeito"]), 100 * float(linha["proporcao_rejeicao"]))
                for linha in linhas if linha["situacao"] == situacao and linha["teste"] == curva["name"]
            )
            assert list(zip(curva["x"], curva["y"])) == esperado
            assert curva["line"]["color"] == CORES_TESTES[curva["name"]]


def test_secao_6_aplica_os_testes_ao_csv_real_e_interpreta_o_efeito():
    app = executar()
    tabela = next(t.value for t in app.table if "Conclusão" in t.value.columns)
    assert list(tabela["Teste"]) == ["Z para proporção", "Binomial exato"]
    assert list(tabela["Estatística"]) == ["Z", "Proporção observada (p̂)"]
    assert list(tabela["Valor da estatística"]) == pytest.approx([-0.6328321262, 10 / 243])
    assert list(tabela["p-valor"]) == pytest.approx([0.7365783625, 0.7772541895])
    assert list(tabela["Efeito (p.p.)"]) == [-0.88, -0.88]
    assert list(tabela["Conclusão"]) == ["Não rejeitar H₀", "Não rejeitar H₀"]
    assert all("#275" not in info.value for info in app.info)
    texto = "\n".join(elemento.value for elemento in app.markdown)
    for trecho in ("10 falhas em 243 builds (4,12%)", "não comprova que a meta seja cumprida",
                   "−0,88 p.p.", "0,88 falha a menos por 100 builds", "custo de uma falha"):
        assert trecho in texto


def test_secao_6_apresenta_conclusoes_distintas_quando_so_o_z_rejeita(monkeypatch):
    import numpy as np
    from hipotese import cenario

    # Com 18 falhas em 243 builds, o Z rejeita e o binomial ainda não.
    monkeypatch.setattr(cenario, "carregar_builds_reais", lambda: np.array([1] * 18 + [0] * 225))
    app = executar()
    tabela = next(t.value for t in app.table if "Conclusão" in t.value.columns)
    assert list(tabela["Conclusão"]) == ["Rejeitar H₀", "Não rejeitar H₀"]
    texto = "\n".join(elemento.value for elemento in app.markdown)
    assert "Apenas o teste Z para proporção encontrou evidência" in texto
    assert "2,41 falhas a mais por 100 builds" in texto


def test_dashboard_final_apresenta_recomendacao_e_limitacao_sem_placeholders():
    app = executar()
    assert not app.info
    texto = "\n".join(elemento.value for elemento in app.markdown)
    assert "**Expectativa e resultado.**" in texto
    assert "prefira o **binomial exato**" in texto
    assert "leve em conta a dependência" in texto
    assert "A coleta cobre um único workflow" in texto


def _grafico_bonus(app):
    return next(
        spec for spec in (json.loads(grafico.proto.spec) for grafico in app.get("plotly_chart"))
        if spec["layout"]["title"]["text"].startswith("Poder interativo")
    )


def test_bonus_fica_na_secao_5_com_controles_de_amostra_efeito_e_alfa():
    app = executar()
    assert [s.label for s in app.slider] == ["Tamanho da amostra (builds)", "Efeito (p.p. acima de 5%)"]
    assert [s.value for s in app.slider] == [243, 4.0]
    assert app.select_slider[0].value == 0.05
    subtitulos = [s.value for s in app.subheader]
    assert subtitulos.index("Bônus · Poder interativo (#278)") == subtitulos.index(
        "Q3 · Quando os dados não se comportam bem (#272)"
    ) + 1
    grafico = _grafico_bonus(app)
    curvas = [traco for traco in grafico["data"] if traco["mode"] == "lines"]
    assert {curva["name"] for curva in curvas} == set(CORES_TESTES)
    for curva in curvas:
        assert curva["line"]["color"] == CORES_TESTES[curva["name"]]
    assert grafico["layout"]["xaxis"]["title"]["text"].endswith("(p.p.)")
    assert grafico["layout"]["yaxis"]["title"]["text"].endswith("(%)")


def test_bonus_atualiza_o_poder_ao_mudar_amostra_efeito_e_alfa():
    app = executar()
    padrao = [m.value for m in app.metric]
    assert padrao[:2] == ["83,64%", "77,10%"]
    app.slider(key="bonus_n").set_value(250).run(timeout=10)
    assert not app.exception
    assert app.metric[0].value == app.metric[1].value == "81,00%"
    assert "os dois testes rejeitam H₀ a partir de **19 falhas**" in "\n".join(m.value for m in app.markdown)
    app.slider(key="bonus_efeito").set_value(8.0)
    app.select_slider(key="bonus_alfa").set_value(0.01)
    app.run(timeout=10)
    assert not app.exception
    titulo = _grafico_bonus(app)["layout"]["title"]["text"]
    assert "250 builds" in titulo and "α = 1%" in titulo
    assert [m.value for m in app.metric] != padrao
