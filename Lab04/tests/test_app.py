from pathlib import Path

from streamlit.testing.v1 import AppTest

from hipotese.config import URL_PROJECT, URL_REPOSITORIO

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
    app = AppTest.from_file(str(APP)).run()
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
    assert len(app.info) == 6
    tabela = app.table[0].value
    assert list(tabela["n (builds)"]) == [243, 243, 20]
    assert tabela.iloc[1]["Correlação de lag 1"] == 0.2740723078825129
