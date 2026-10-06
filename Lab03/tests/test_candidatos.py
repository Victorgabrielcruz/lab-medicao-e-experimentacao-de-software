import json
import logging
import re

import pytest

from pipeline import candidatos
from pipeline.candidatos import SEARCH_LIMIT, coletar, com_intervalo, executar, montar_query, validar_busca
from pipeline.config import ConfigError
from pipeline.github_api import GitHubClient


def _repo(i, estrelas, linguagem="Python"):
    return {"id": i, "full_name": f"org/repo{i}", "html_url": f"https://github.com/org/repo{i}",
            "stargazers_count": estrelas, "language": linguagem}


class SearchFalsa:
    """Simula /search/repositories respeitando stars:lo..hi, language e o limite de 1000."""

    def __init__(self, repos):
        self.repos = repos
        self.queries = []

    def __call__(self, query, pagina):
        self.queries.append((query, pagina))
        lo, hi = map(int, re.search(r"stars:(\d+)\.\.(\d+)", query).groups())
        lang = re.search(r'language:"([^"]+)"', query)
        achados = [r for r in self.repos
                   if lo <= r["stargazers_count"] <= hi and (not lang or r["language"] == lang.group(1))]
        achados.sort(key=lambda r: -r["stargazers_count"])
        visiveis = achados[:SEARCH_LIMIT]
        inicio = (pagina - 1) * 100
        return {"total_count": len(achados), "incomplete_results": False, "items": visiveis[inicio:inicio + 100]}


def test_montar_query():
    assert montar_query(10, 20, ["fork:false"], "C++") == 'stars:10..20 fork:false language:"C++"'
    assert montar_query(10, 20, []) == "stars:10..20"


def test_fatia_pequena_nao_e_dividida():
    api = SearchFalsa([_repo(i, 100 + i) for i in range(250)])
    fatias, lista = coletar(api, 0, 10_000, [])
    assert len(fatias) == 1
    assert len(lista) == 250
    assert [p for _, p in api.queries] == [1, 2, 3]


def test_divide_faixas_ate_caber_no_limite():
    repos = [_repo(i, 1000 + i) for i in range(3500)]
    api = SearchFalsa(repos)
    fatias, lista = coletar(api, 1000, 100_000, [])
    assert all(f["total_count"] <= SEARCH_LIMIT and not f["truncada"] for f in fatias)
    assert len(fatias) > 1
    assert {r["id"] for r in lista} == {r["id"] for r in repos}
    assert sum(f["coletados"] for f in fatias) == len(repos)


def test_faixa_de_um_valor_acima_do_limite_e_truncada_com_alerta(caplog):
    api = SearchFalsa([_repo(i, 500) for i in range(1200)])
    with caplog.at_level(logging.WARNING):
        fatias, lista = coletar(api, 500, 500, [])
    assert fatias[0]["truncada"] is True
    assert len(lista) == SEARCH_LIMIT
    assert "limite 1000" in caplog.text


def test_resultados_incompletos_geram_alerta(caplog):
    def api(query, pagina):
        return {"total_count": 1, "incomplete_results": True, "items": [_repo(1, 10)]}

    with caplog.at_level(logging.WARNING):
        fatias, _ = coletar(api, 0, 10, [])
    assert fatias[0]["incompleta"] is True
    assert "incompletos" in caplog.text


def test_remove_duplicatas_entre_fatias_de_linguagem():
    repos = [_repo(1, 50, "Python"), _repo(2, 60, "Go")]
    api = SearchFalsa(repos)

    def api_com_repeticao(query, pagina):
        resposta = api(query, pagina)
        resposta["items"] = resposta["items"] + [_repo(1, 50, "Python")]
        return resposta

    fatias, lista = coletar(api_com_repeticao, 0, 100, [], ["Python", "Go"])
    assert len(fatias) == 2
    assert [r["full_name"] for r in lista] == ["org/repo2", "org/repo1"]


def test_lista_ordenada_e_resumida():
    _, lista = coletar(SearchFalsa([_repo(1, 10), _repo(2, 30)]), 0, 100, [])
    assert lista[0] == {"id": 2, "full_name": "org/repo2", "html_url": "https://github.com/org/repo2",
                        "estrelas": 30, "linguagem": "Python"}


def test_com_intervalo_espera_entre_chamadas():
    esperas, tempo = [], [0.0]
    chamar = com_intervalo(lambda x: x, 2.0, sleep=esperas.append, relogio=lambda: tempo[0])
    assert chamar(1) == 1
    tempo[0] = 0.5
    chamar(2)
    tempo[0] = 10.0
    chamar(3)
    assert esperas == [1.5]


@pytest.mark.parametrize("busca", [
    {"estrelas_min": 10, "estrelas_max": 5},
    {"estrelas_min": -1, "estrelas_max": 5},
    {"estrelas_min": "10", "estrelas_max": 50},
    {"estrelas_min": 1, "estrelas_max": 5, "linguagens": "Python"},
])
def test_validar_busca_invalida(busca):
    with pytest.raises(ConfigError):
        validar_busca(busca)


class ClienteFalso:
    def __init__(self, api):
        self.api = api
        self.chamadas = []

    def get(self, path, params):
        self.chamadas.append((path, params))
        return self.api(params["q"], params["page"])


def test_executar_grava_arquivo(tmp_path):
    config = {
        "janela": {"inicio": "2025-10-01"},
        "busca": {"estrelas_min": 0, "estrelas_max": 100, "qualificadores": ["fork:false"], "intervalo_s": 0},
        "caminhos": {"raw": str(tmp_path / "raw")},
    }
    cliente = ClienteFalso(SearchFalsa([_repo(1, 10), _repo(2, 20)]))
    saida, fatias, lista = executar(config, cliente)

    path, params = cliente.chamadas[0]
    assert path == "/search/repositories"
    assert params["q"] == "stars:0..100 fork:false pushed:>=2025-10-01"
    assert params["per_page"] == 100

    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert saida.name == candidatos.ARQUIVO_SAIDA
    assert dados["total_candidatos"] == 2
    assert dados["fatias_truncadas"] == 0
    assert [c["id"] for c in dados["candidatos"]] == [2, 1]


def test_github_client_monta_requisicao():
    class Resposta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    class Sessao:
        def __init__(self):
            self.headers = {}

        def get(self, url, params, timeout):
            self.chamada = (url, params, timeout)
            return Resposta()

    sessao = Sessao()
    cliente = GitHubClient("tkn", "https://api.github.com/", 5, session=sessao)
    assert cliente.get("/rate_limit", {"a": 1}) == {"ok": True}
    assert sessao.chamada == ("https://api.github.com/rate_limit", {"a": 1}, 5)
    assert sessao.headers["Authorization"] == "Bearer tkn"
