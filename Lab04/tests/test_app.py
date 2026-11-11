import csv
from pathlib import Path
import json

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


def test_links_no_topo():
    topo = executar().markdown[0].value
    assert URL_REPOSITORIO in topo
    assert URL_PROJECT in topo


def test_cenario_apresenta_protocolo_e_calibracao_sem_placeholder():
    app = executar()
    texto = "\n".join(elemento.value for elemento in app.markdown)
    for trecho in (
        "pytest-dev/pytest", "H₀: p = 0,05", "H₁: p > 0,05",
        "unicaudal à direita", "243 observações", "10 falhas",
        "0,05 + efeito", "pontos percentuais", "Expectativa registrada antes",
        "ambos", "não resultados",
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
    for trecho in ("Amostra pequena afeta mais o Z", "Rajadas afetam os dois", "não é poder real", "±0,43 p.p."):
        assert trecho in texto
    tipo_i = app.table[2].value
    assert list(tipo_i["Situação"]) == ["Independente"] * 2 + ["Rajadas"] * 2 + ["Amostra pequena"] * 2
    assert len(app.table) == 5
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
    assert any("Gráfico G3" in info.value for info in app.info)


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
    g4 = json.loads(app.get("plotly_chart")[-1].proto.spec)
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
