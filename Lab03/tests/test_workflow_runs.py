import datetime as dt
import json
from pathlib import Path

import pytest
import requests

from pipeline import workflow_runs
from pipeline.__main__ import main
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import ConfigError, janela_utc, load_config
from pipeline.github_api import GitHubClient
from pipeline.workflow_runs import coletar_mes, coletar_repositorio, executar, fatias_mensais

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
UTC = dt.timezone.utc
INICIO = dt.datetime(2025, 10, 1, tzinfo=UTC)
FIM_MES = dt.datetime(2025, 11, 1, tzinfo=UTC)
REPO = {"id": 10, "full_name": "org/projeto", "default_branch": "develop"}


def run(id=1, **alteracoes):
    return {"id": id, "workflow_id": 17, "name": "CI", "head_branch": "develop", "event": "push",
            "status": "completed", "conclusion": "success", "created_at": "2025-10-10T12:00:00Z",
            "updated_at": "2025-10-10T12:01:00Z", "run_started_at": "2025-10-10T12:00:00Z",
            "head_sha": "abc", "run_number": id, "run_attempt": 1,
            "html_url": f"https://github.com/org/projeto/actions/runs/{id}", **alteracoes}


def pagina(runs=(), total=None):
    return {"total_count": len(runs) if total is None else total, "workflow_runs": list(runs)}


class ClienteFalso:
    def __init__(self, paginas):
        self.paginas = iter(paginas)
        self.chamadas = []

    def get(self, path, params):
        self.chamadas.append((path, dict(params)))
        dados = next(self.paginas)
        if isinstance(dados, Exception):
            raise dados
        return dados


def config(tmp_path):
    cfg = load_config(CONFIG)
    cfg["caminhos"] = {"raw": str(tmp_path / "raw"), "cache": str(tmp_path / "cache")}
    return cfg


def erro_http(status):
    r = requests.Response()
    r.status_code = status
    return requests.HTTPError(str(status), response=r)


def test_janela_do_projeto_tem_12_meses_sem_lacunas_ou_sobreposicao():
    inicio, fim = janela_utc(load_config(CONFIG))
    fatias = list(fatias_mensais(inicio, fim))
    assert len(fatias) == 12
    assert fatias[0][0] == INICIO
    assert fatias[-1][1] == dt.datetime(2026, 10, 1, tzinfo=UTC)
    assert all(a[1] == b[0] for a, b in zip(fatias, fatias[1:]))
    assert all(a.day == b.day == 1 for a, b in fatias)


def test_fatias_cobrem_fevereiro_bissexto_e_pontas_parciais():
    inicio = dt.datetime(2028, 1, 15, tzinfo=UTC)
    fim = dt.datetime(2028, 3, 10, tzinfo=UTC)
    fatias = list(fatias_mensais(inicio, fim))
    assert fatias == [(inicio, dt.datetime(2028, 2, 1, tzinfo=UTC)),
                      (dt.datetime(2028, 2, 1, tzinfo=UTC), dt.datetime(2028, 3, 1, tzinfo=UTC)),
                      (dt.datetime(2028, 3, 1, tzinfo=UTC), fim)]
    assert (fatias[1][1] - fatias[1][0]).days == 29
    assert list(fatias_mensais(inicio, inicio)) == []


def test_filtros_branch_push_e_intervalo_inclusivo_da_api():
    c = ClienteFalso([pagina([run()])])
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert c.chamadas == [("/repos/org/projeto/actions/runs", {
        "branch": "develop", "event": "push", "per_page": 100, "page": 1,
        "created": "2025-10-01T00:00:00Z..2025-10-31T23:59:59Z",
    })]
    assert lista == [run()]
    assert mes["total_api"] == mes["coletados_api"] == mes["runs_retidos"] == 1
    assert not mes["limite_atingido"] and not mes["coleta_incompleta"]


def test_filtros_locais_excluem_outro_evento_branch_e_datas_fora_da_fatia():
    c = ClienteFalso([pagina([
        run(1, created_at="2025-10-01T00:00:00Z"),
        run(2, created_at="2025-10-31T23:59:59Z"),
        run(3, event="pull_request"), run(4, head_branch="main"),
        run(5, created_at="2025-09-30T23:59:59Z"),
        run(6, created_at="2025-11-01T00:00:00Z"),
    ])])
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert [r["id"] for r in lista] == [1, 2]
    assert mes["runs_retidos"] == 2
    assert mes["coletados_api"] == 6


@pytest.mark.parametrize("conclusion", ["success", "failure", "timed_out", "startup_failure",
                                        "cancelled", "skipped", "neutral", None])
def test_coleta_preserva_conclusions_para_auditoria(conclusion):
    c = ClienteFalso([pagina([run(conclusion=conclusion)])])
    _, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert lista[0]["conclusion"] == conclusion
    assert lista[0]["workflow_id"] == 17


@pytest.mark.parametrize("total", [999, 1000, 1001, 2000])
def test_paginacao_para_no_limite_e_emite_alerta(total, caplog):
    quantidade = min(total, 1000)
    runs = [run(i) for i in range(quantidade)]
    c = ClienteFalso([pagina(runs[i:i+100], total) for i in range(0, quantidade, 100)])
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert len(lista) == quantidade
    assert len(c.chamadas) == 10
    assert [params["page"] for _, params in c.chamadas] == list(range(1, 11))
    assert mes["limite_atingido"] == (total >= 1000)
    assert mes["coleta_incompleta"] == (total > 1000)
    assert ("atingiu" in caplog.text) == (total >= 1000)


def test_paginas_repetidas_deduplicadas_e_sinalizadas_como_incompletas():
    primeiros = [run(i) for i in range(100)]
    c = ClienteFalso([pagina(primeiros, 101), pagina([run(99)], 101)])
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert len(lista) == mes["coletados_api"] == 100
    assert mes["coleta_incompleta"]


@pytest.mark.parametrize("primeira_vazia", [False, True])
def test_pagina_vazia_antes_do_total_esperado_sinaliza_incompletude(primeira_vazia):
    paginas = [pagina([], 250)] if primeira_vazia else [pagina([run()], 250), pagina([], 250)]
    c = ClienteFalso(paginas)
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert mes["coleta_incompleta"]
    assert len(lista) == (0 if primeira_vazia else 1)
    assert len(c.chamadas) == (1 if primeira_vazia else 2)


def test_mes_sem_runs_exige_uma_consulta_e_e_completo():
    c = ClienteFalso([pagina()])
    mes, lista = coletar_mes(c, REPO["full_name"], "develop", INICIO, FIM_MES)
    assert lista == []
    assert mes["coletados_api"] == 0
    assert not mes["coleta_incompleta"]
    assert len(c.chamadas) == 1


def test_repositorio_ordenado_por_data_e_id_sem_duplicatas():
    c = ClienteFalso([
        pagina([run(3, created_at="2025-10-20T00:00:00Z"), run(2), run(1), run(1)]),
        pagina([run(4, created_at="2025-11-10T00:00:00Z")]),
    ])
    fim = dt.datetime(2025, 12, 1, tzinfo=UTC)
    dados = coletar_repositorio(c, REPO, INICIO, fim)
    assert [r["id"] for r in dados["workflow_runs"]] == [1, 2, 3, 4]
    assert dados["total_runs"] == 4
    assert len(dados["meses"]) == 2
    assert dados["coleta_incompleta"]  # A API indicou 4 registros, mas havia só 3 IDs no mês.


@pytest.mark.parametrize("branch", [None, "", " ", 42])
def test_default_branch_ausente_impede_coleta(branch):
    c = ClienteFalso([])
    with pytest.raises(ConfigError, match="Default branch ausente"):
        coletar_repositorio(c, {**REPO, "default_branch": branch}, INICIO, FIM_MES)
    assert c.chamadas == []


def test_executar_le_metadados_e_grava_consolidado(tmp_path, monkeypatch, caplog):
    cfg = config(tmp_path)
    gravar_json(tmp_path / "raw" / "metadados.json", {"repositorios": [REPO]})
    c = ClienteFalso([pagina([run()])] + [pagina() for _ in range(11)])
    monkeypatch.setattr(workflow_runs, "LOG_A_CADA", 1)
    with caplog.at_level("INFO"):
        caminho, lista, descartes = executar(cfg, c)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert caminho == tmp_path / "raw" / "workflow_runs.json"
    assert dados["total_repositorios"] == dados["total_runs"] == 1
    assert dados["repositorios_com_coleta_incompleta"] == dados["meses_com_limite_atingido"] == 0
    assert dados["janela"] == {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
    assert dados["repositorios"] == lista
    assert dados["descartes"] == descartes == []
    assert len(lista[0]["meses"]) == len(c.chamadas) == 12
    assert "1/1 repositórios avaliados" in caplog.text


def test_consolidado_sinaliza_truncamento_e_nunca_excede_1000_por_mes(tmp_path):
    runs = [run(i) for i in range(1001)]
    paginas = [pagina(runs[i:i+100], 1001) for i in range(0, 900, 100)]
    # Mesmo que a última página exceda per_page, o coletor respeita o teto.
    paginas.append(pagina(runs[900:], 1001))
    c = ClienteFalso(paginas + [pagina() for _ in range(11)])
    caminho, lista, _ = executar(config(tmp_path), c, [REPO])
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["total_runs"] == lista[0]["total_runs"] == 1000
    assert dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["meses_com_limite_atingido"] == 1
    assert lista[0]["meses"][0]["total_api"] == 1001
    assert lista[0]["coleta_incompleta"]


@pytest.mark.parametrize("status", [404, 451])
def test_repositorio_inacessivel_e_registrado_sem_impedir_demais(tmp_path, status):
    segundo = {**REPO, "id": 11, "full_name": "org/outro"}
    c = ClienteFalso([erro_http(status)] + [pagina() for _ in range(12)])
    _, lista, descartes = executar(config(tmp_path), c, [REPO, segundo])
    assert len(lista) == 1 and lista[0]["full_name"] == "org/outro"
    assert descartes == [{"id": 10, "full_name": "org/projeto", "motivo": "repositorio_inacessivel",
                          "detalhe": f"HTTP {status}"}]


@pytest.mark.parametrize("status", [403, 500])
def test_outros_erros_sao_propagados_sem_sobrescrever_consolidado(tmp_path, status):
    caminho = tmp_path / "raw" / "workflow_runs.json"
    gravar_json(caminho, {"anterior": True})
    with pytest.raises(requests.HTTPError):
        executar(config(tmp_path), ClienteFalso([erro_http(status)]), [REPO])
    assert json.loads(caminho.read_text(encoding="utf-8")) == {"anterior": True}


def test_metadados_ausentes_informam_etapa_previa(tmp_path):
    with pytest.raises(FileNotFoundError, match="execute antes a etapa metadados"):
        executar(config(tmp_path), ClienteFalso([]))


@pytest.mark.parametrize("regras", [{"evento": "pull_request", "somente_default_branch": True},
                                   {"evento": "push", "somente_default_branch": False}])
def test_configuracao_diferente_das_definicoes_e_recusada(tmp_path, regras):
    cfg = config(tmp_path)
    cfg["runs"] = regras
    with pytest.raises(ConfigError, match="runs.evento=push"):
        executar(cfg, ClienteFalso([]), [])


class Sessao:
    def __init__(self, paginas):
        self.headers = {}
        self.paginas = iter(paginas)
        self.chamadas = []

    def get(self, url, params, timeout):
        self.chamadas.append((url, dict(params)))
        dados = next(self.paginas)
        if isinstance(dados, Exception):
            raise dados
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps(dados).encode()
        return r


def test_reexecucao_retoma_paginas_e_meses_do_cache_apos_interrupcao(tmp_path):
    cfg = config(tmp_path)
    cache = CacheDisco(tmp_path / "cache")
    primeira = pagina([run(i) for i in range(1, 101)], 101)
    segunda = pagina([run(101)], 101)
    sessao = Sessao([primeira, segunda, requests.Timeout("interrupção")])
    c = GitHubClient("token-falso", session=sessao, cache=cache)
    with pytest.raises(requests.Timeout):
        executar(cfg, c, [REPO])
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 2
    assert not (tmp_path / "raw" / "workflow_runs.json").exists()

    restante = Sessao([pagina([run(102, created_at="2025-11-10T00:00:00Z")])] +
                     [pagina() for _ in range(10)])
    c = GitHubClient("token-falso", session=restante, cache=CacheDisco(tmp_path / "cache"))
    caminho, lista, _ = executar(cfg, c, [REPO])
    assert lista[0]["total_runs"] == 102
    assert len(restante.chamadas) == 11
    assert restante.chamadas[0][1]["created"].startswith("2025-11-01")
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 13
    assert json.loads(caminho.read_text(encoding="utf-8"))["total_runs"] == 102

    sem_rede = Sessao([])
    c = GitHubClient("token-falso", session=sem_rede, cache=CacheDisco(tmp_path / "cache"))
    _, segunda_lista, _ = executar(cfg, c, [REPO])
    assert segunda_lista == lista
    assert sem_rede.chamadas == []


def test_cli_executa_so_workflow_runs(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    monkeypatch.setattr("pipeline.metadados.executar", lambda *args: pytest.fail("etapa não solicitada"))
    monkeypatch.setattr(workflow_runs, "executar", lambda config, client:
                        (Path("workflow_runs.json"), [{"total_runs": 5, "coleta_incompleta": True}], []))
    assert main(["--config", str(CONFIG), "--etapas", "workflow_runs"]) == 0
    assert "Workflow runs: 1 repositórios, 5 runs, 1 coletas incompletas" in capsys.readouterr().out


def test_cli_padrao_executa_as_quatro_etapas_na_ordem(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    chamadas = []

    def etapa(nome, resultado):
        def executar_falso(config, client):
            chamadas.append(nome)
            return resultado
        return executar_falso

    monkeypatch.setattr("pipeline.candidatos.executar", etapa("candidatos", (Path("candidatos.json"), [], [])))
    monkeypatch.setattr("pipeline.actions.executar", etapa("actions", (Path("actions.json"), [], [])))
    monkeypatch.setattr("pipeline.metadados.executar", etapa("metadados", (Path("metadados.json"), [], [])))
    monkeypatch.setattr(workflow_runs, "executar", etapa("workflow_runs", (Path("workflow_runs.json"), [], [])))
    assert main(["--config", str(CONFIG)]) == 0
    assert chamadas == ["candidatos", "actions", "metadados", "workflow_runs"]
