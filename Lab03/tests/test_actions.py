import json
import logging

import pytest
import requests

from pipeline import actions
from pipeline.actions import MOTIVO_INACESSIVEL, MOTIVO_SEM_ACTIONS, contar_workflows, executar, filtrar


def _repo(i):
    return {"id": i, "full_name": f"org/repo{i}", "html_url": f"https://github.com/org/repo{i}",
            "estrelas": 1000 + i, "linguagem": "Python"}


def _erro_http(status):
    resposta = requests.Response()
    resposta.status_code = status
    return requests.HTTPError(f"{status}", response=resposta)


DINAMICO = "dynamic/dependabot/dependabot-updates"


def _workflows(*paths):
    return [{"path": p} for p in paths]


class WorkflowsFalso:
    """Simula /repos/{full_name}/actions/workflows paginado.

    Cada resposta é uma lista de paths de workflows ou uma exceção.
    """

    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    def get(self, path, params):
        self.chamadas.append((path, params))
        full_name = path.removeprefix("/repos/").removesuffix("/actions/workflows")
        resposta = self.respostas[full_name]
        if isinstance(resposta, Exception):
            raise resposta
        inicio = (params["page"] - 1) * params["per_page"]
        return {"total_count": len(resposta),
                "workflows": _workflows(*resposta[inicio:inicio + params["per_page"]])}


def test_contar_workflows_separa_proprios_de_dinamicos():
    cliente = WorkflowsFalso({"org/repo1": [".github/workflows/ci.yml", DINAMICO]})
    assert contar_workflows(cliente, "org/repo1") == (2, 1)
    assert cliente.chamadas == [("/repos/org/repo1/actions/workflows", {"per_page": 100, "page": 1})]


def test_contar_workflows_pagina_acima_de_100():
    paths = [f".github/workflows/w{i}.yml" for i in range(150)] + [DINAMICO]
    cliente = WorkflowsFalso({"org/repo1": paths})
    assert contar_workflows(cliente, "org/repo1") == (151, 150)
    assert [p["page"] for _, p in cliente.chamadas] == [1, 2]


def test_contar_workflows_sem_nenhum():
    assert contar_workflows(WorkflowsFalso({"org/repo1": []}), "org/repo1") == (0, 0)


def test_filtrar_descarta_sem_workflows_proprios():
    cliente = WorkflowsFalso({
        "org/repo1": [".github/workflows/ci.yml", ".github/workflows/release.yml"],
        "org/repo2": [],
        "org/repo3": [DINAMICO, "dynamic/github-code-scanning/codeql"],
        "org/repo4": [".github/workflows/ci.yml", DINAMICO],
    })
    aprovados, descartes = filtrar([_repo(i) for i in range(1, 5)], lambda n: contar_workflows(cliente, n))

    assert [r["full_name"] for r in aprovados] == ["org/repo1", "org/repo4"]
    assert aprovados[1] == {**_repo(4), "total_workflows": 2, "workflows_proprios": 1}
    assert descartes == [
        {"id": 2, "full_name": "org/repo2", "motivo": MOTIVO_SEM_ACTIONS,
         "detalhe": "nenhum workflow em .github/workflows/ (total_count = 0)"},
        {"id": 3, "full_name": "org/repo3", "motivo": MOTIVO_SEM_ACTIONS,
         "detalhe": "nenhum workflow em .github/workflows/ (total_count = 2)"},
    ]


@pytest.mark.parametrize("status", [404, 451])
def test_filtrar_descarta_repositorio_inacessivel(status):
    cliente = WorkflowsFalso({"org/repo1": _erro_http(status), "org/repo2": [".github/workflows/ci.yml"]})
    aprovados, descartes = filtrar([_repo(1), _repo(2)], lambda n: contar_workflows(cliente, n))

    assert [r["id"] for r in aprovados] == [2]
    assert descartes[0]["motivo"] == MOTIVO_INACESSIVEL
    assert descartes[0]["detalhe"] == f"HTTP {status}"


@pytest.mark.parametrize("status", [403, 500])
def test_filtrar_propaga_outros_erros(status):
    cliente = WorkflowsFalso({"org/repo1": _erro_http(status)})
    with pytest.raises(requests.HTTPError):
        filtrar([_repo(1)], lambda n: contar_workflows(cliente, n))


def test_filtrar_registra_progresso(monkeypatch, caplog):
    monkeypatch.setattr(actions, "LOG_A_CADA", 2)
    with caplog.at_level(logging.INFO):
        filtrar([_repo(i) for i in range(1, 5)], lambda n: (1, 1))
    assert "Actions: 4/4 avaliados, 4 aprovados" in caplog.text


def _config(tmp_path):
    return {"caminhos": {"raw": str(tmp_path / "raw")}}


def test_executar_le_candidatos_e_grava_funil(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "candidatos.json").write_text(json.dumps({"candidatos": [_repo(1), _repo(2), _repo(3)]}),
                                         encoding="utf-8")
    cliente = WorkflowsFalso({"org/repo1": [".github/workflows/ci.yml"], "org/repo2": [DINAMICO],
                              "org/repo3": _erro_http(404)})

    saida, aprovados, descartes = executar(_config(tmp_path), cliente)

    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert saida.name == actions.ARQUIVO_SAIDA
    assert dados["total_avaliados"] == 3
    assert dados["total_aprovados"] == 1
    assert dados["descartes_por_motivo"] == {MOTIVO_SEM_ACTIONS: 1, MOTIVO_INACESSIVEL: 1}
    assert [r["id"] for r in dados["repositorios"]] == [1]
    assert [d["id"] for d in dados["descartes"]] == [2, 3]


def test_executar_com_lista_recebida(tmp_path):
    saida, aprovados, descartes = executar(_config(tmp_path), WorkflowsFalso({"org/repo1": [".github/workflows/ci.yml"]}),
                                            [_repo(1)])
    assert saida.is_file()
    assert len(aprovados) == 1 and descartes == []


def test_executar_sem_candidatos_json(tmp_path):
    with pytest.raises(FileNotFoundError, match="etapa candidatos"):
        executar(_config(tmp_path), WorkflowsFalso({}))
