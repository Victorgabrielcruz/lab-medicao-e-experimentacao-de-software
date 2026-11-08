from pathlib import Path
import json

from streamlit.testing.v1 import AppTest

from hipotese.config import URL_PROJECT, URL_REPOSITORIO
from hipotese.exemplo import gerar_exemplo

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
    assert len(app.info) == 4
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
    assert len(app.get("plotly_chart")) == 3


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
    assert [figura["layout"]["title"]["text"][:2] for figura in graficos] == ["G1", "G2", "G2"]
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
