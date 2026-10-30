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
