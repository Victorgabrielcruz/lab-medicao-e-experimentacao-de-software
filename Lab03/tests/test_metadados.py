import datetime as dt
import json

import pytest
import requests

from pipeline import metadados
from pipeline.actions import MOTIVO_INACESSIVEL
from pipeline.metadados import (caminho_cache, coletar, coletar_repositorio, contar_contribuidores, executar,
                                idade_dias)

FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)


def _resposta(status=200, corpo=None, link=None):
    resposta = requests.Response()
    resposta.status_code = status
    resposta._content = b"" if corpo is None else json.dumps(corpo).encode()
    if link:
        resposta.headers["Link"] = link
    return resposta


def _link_last(pagina):
    base = "https://api.github.com/repositories/1/contributors?per_page=1"
    return f'<{base}&page=2>; rel="next", <{base}&page={pagina}>; rel="last"'


def _repo_api(full_name="org/repo1", created_at="2020-10-01T12:00:00Z"):
    return {"id": 1, "full_name": full_name, "stargazers_count": 1500, "language": "Go",
            "created_at": created_at, "default_branch": "main"}


class ClienteFalso:
    """Simula /repos/{full_name} e /repos/{full_name}/contributors."""

    def __init__(self, repos, contribuidores):
        self.repos = repos
        self.contribuidores = contribuidores
        self.chamadas = []

    def get(self, path, params=None):
        self.chamadas.append((path, params))
        resposta = self.repos[path.removeprefix("/repos/")]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    def get_resposta(self, path, params=None):
        self.chamadas.append((path, params))
        resposta = self.contribuidores[path.removeprefix("/repos/").removesuffix("/contributors")]
        if resposta.status_code >= 400:
            raise requests.HTTPError(str(resposta.status_code), response=resposta)
        return resposta


def _erro_http(status):
    return requests.HTTPError(str(status), response=_resposta(status, {"message": "Not Found"}))


@pytest.mark.parametrize("resposta, esperado", [
    (_resposta(200, [{"login": "a"}], _link_last(400)), (400, None)),
    (_resposta(200, [{"login": "a"}]), (1, None)),
    (_resposta(200, []), (0, None)),
    (_resposta(204), (0, None)),
])
def test_contar_contribuidores_pelo_link_header(resposta, esperado):
    cliente = ClienteFalso({}, {"org/repo1": resposta})
    assert contar_contribuidores(cliente, "org/repo1") == esperado
    assert cliente.chamadas == [("/repos/org/repo1/contributors", {"per_page": 1, "anon": 1})]


def test_contar_contribuidores_lista_grande_demais():
    corpo = {"message": "The history or contributor list is too large to list contributors for this repository "
                        "via the API."}
    cliente = ClienteFalso({}, {"org/repo1": _resposta(403, corpo)})
    total, obs = contar_contribuidores(cliente, "org/repo1")
    assert total is None
    assert "grande demais" in obs


@pytest.mark.parametrize("resposta", [
    _resposta(403, {"message": "API rate limit exceeded"}),
    _resposta(403),
    _resposta(500, {"message": "erro"}),
])
def test_contar_contribuidores_propaga_outros_erros(resposta):
    with pytest.raises(requests.HTTPError):
        contar_contribuidores(ClienteFalso({}, {"org/repo1": resposta}), "org/repo1")


def test_idade_em_dias_ate_o_fim_da_janela():
    assert idade_dias("2025-10-01T00:00:00Z", FIM) == 365
    assert idade_dias("2026-09-30T23:59:59Z", FIM) == 0


def test_coletar_repositorio():
    cliente = ClienteFalso({"org/repo1": _repo_api()}, {"org/repo1": _resposta(200, [{}], _link_last(42))})
    dados = coletar_repositorio(cliente, "org/repo1", FIM)
    assert {k: v for k, v in dados.items() if k != "coletado_em"} == {
        "id": 1, "full_name": "org/repo1", "estrelas": 1500, "linguagem": "Go",
        "created_at": "2020-10-01T12:00:00Z", "idade_dias": 2190, "idade_anos": 6.0,
        "default_branch": "main", "contribuidores": 42, "contribuidores_obs": None,
    }


def _aprovado(i):
    return {"id": i, "full_name": f"org/repo{i}"}


def test_coletar_salva_por_repositorio_e_reaproveita_cache(tmp_path):
    chamadas = []

    def buscar(nome):
        chamadas.append(nome)
        return {"full_name": nome, "contribuidores": 3}

    metas, descartes = coletar([_aprovado(1), _aprovado(2)], buscar, tmp_path)
    assert chamadas == ["org/repo1", "org/repo2"]
    assert caminho_cache(tmp_path, "org/repo1") == tmp_path / "metadados" / "org__repo1.json"
    assert json.loads(caminho_cache(tmp_path, "org/repo2").read_text(encoding="utf-8"))["full_name"] == "org/repo2"

    metas2, _ = coletar([_aprovado(1), _aprovado(2), _aprovado(3)], buscar, tmp_path)
    assert chamadas == ["org/repo1", "org/repo2", "org/repo3"]
    assert [m["full_name"] for m in metas2] == ["org/repo1", "org/repo2", "org/repo3"]
    assert descartes == []


def test_coletar_retoma_depois_de_erro(tmp_path):
    def buscar_falha_no_2(nome):
        if nome == "org/repo2":
            raise _erro_http(500)
        return {"full_name": nome}

    with pytest.raises(requests.HTTPError):
        coletar([_aprovado(1), _aprovado(2)], buscar_falha_no_2, tmp_path)
    assert caminho_cache(tmp_path, "org/repo1").is_file()

    chamadas = []
    coletar([_aprovado(1), _aprovado(2)], lambda n: chamadas.append(n) or {"full_name": n}, tmp_path)
    assert chamadas == ["org/repo2"]


@pytest.mark.parametrize("status", [404, 451])
def test_coletar_descarta_inacessivel_sem_gravar_cache(tmp_path, status):
    def buscar(nome):
        raise _erro_http(status)

    metas, descartes = coletar([_aprovado(1)], buscar, tmp_path)
    assert metas == []
    assert descartes == [{"id": 1, "full_name": "org/repo1", "motivo": MOTIVO_INACESSIVEL, "detalhe": f"HTTP {status}"}]
    assert not caminho_cache(tmp_path, "org/repo1").exists()


def test_coletar_registra_progresso(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(metadados, "LOG_A_CADA", 2)
    with caplog.at_level("INFO"):
        coletar([_aprovado(i) for i in range(1, 3)], lambda n: {"full_name": n}, tmp_path)
    assert "Metadados: 2/2 repositórios" in caplog.text
    assert "2 consultados na API, 0 lidos do cache" in caplog.text


def _config(tmp_path):
    return {"janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "caminhos": {"raw": str(tmp_path / "raw"), "cache": str(tmp_path / "cache")}}


def test_executar_le_actions_e_grava_consolidado(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "actions.json").write_text(json.dumps({"repositorios": [_aprovado(1), _aprovado(2), _aprovado(3)]}),
                                      encoding="utf-8")
    grande = _resposta(403, {"message": "contributor list is too large"})
    cliente = ClienteFalso(
        {"org/repo1": _repo_api("org/repo1"), "org/repo2": _repo_api("org/repo2"), "org/repo3": _erro_http(404)},
        {"org/repo1": _resposta(200, [{}], _link_last(7)), "org/repo2": grande},
    )

    saida, lista, descartes = executar(_config(tmp_path), cliente)

    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert saida.name == metadados.ARQUIVO_SAIDA
    assert dados["referencia_idade"] == "2026-10-01T00:00:00+00:00"
    assert dados["total_repositorios"] == 2
    assert dados["sem_contribuidores"] == 1
    assert [m["contribuidores"] for m in dados["repositorios"]] == [7, None]
    assert [d["full_name"] for d in dados["descartes"]] == ["org/repo3"]
    assert (tmp_path / "cache" / "metadados" / "org__repo1.json").is_file()


def test_executar_com_lista_recebida(tmp_path):
    cliente = ClienteFalso({"org/repo1": _repo_api()}, {"org/repo1": _resposta(204)})
    saida, lista, _ = executar(_config(tmp_path), cliente, [_aprovado(1)])
    assert saida.is_file()
    assert lista[0]["contribuidores"] == 0


def test_executar_sem_actions_json(tmp_path):
    with pytest.raises(FileNotFoundError, match="etapa actions"):
        executar(_config(tmp_path), ClienteFalso({}, {}))
