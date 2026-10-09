import datetime as dt
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import requests
import yaml

from pipeline import tempo_recuperacao as tr
from pipeline import workflow_runs
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def run(id=1, conclusion="failure", hora="10:00:00", workflow_id=100, **campos):
    data = campos.get("created_at", f"2026-05-10T{hora}Z")
    return {"id": id, "workflow_id": workflow_id, "conclusion": conclusion,
            "head_branch": "main", "event": "push", "name": "CI",
            "created_at": data, "run_started_at": data, "updated_at": data, **campos}


def repo(runs=None, **campos):
    return {"id": 10, "full_name": "org/projeto", "default_branch": "main",
            "workflow_runs": [run(99, "success", "09:00:00"), run()] if runs is None else runs,
            "coleta_incompleta": False, "meses": [], **campos}


@pytest.fixture
def config(tmp_path):
    return {"api": {"base_url": "https://api.github.com"},
            "janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "inclusao": {"min_releases": 5, "min_runs_validos": 50},
            "runs": {"evento": "push", "somente_default_branch": True,
                     "conclusoes_sucesso": ["success"],
                     "conclusoes_falha": ["failure", "timed_out", "startup_failure"]},
            "caminhos": {"raw": str(tmp_path / "raw"), "processed": str(tmp_path / "processed"),
                         "cache": str(tmp_path / "cache")}}


def gravar_entrada(config, repos=None, caminho=None, janela=JANELA):
    caminho = Path(caminho) if caminho is not None else Path(config["caminhos"]["raw"]) / "workflow_runs.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({"janela": janela, "repositorios": [repo()] if repos is None else repos}),
                       encoding="utf-8")
    return caminho


def gravar_config(config, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(caminho)


def test_exemplo_oficial_usa_inicio_da_falha_e_termino_do_sucesso():
    runs = [run(9, "success", "09:00:00"),
            run(1, created_at="2026-05-10T09:55:00Z", run_started_at="2026-05-10T10:00:00Z"),
            run(2, "timed_out", "10:30:00"),
            run(3, "success", "11:10:00", run_started_at="2026-05-10T11:15:00Z",
                updated_at="2026-05-10T11:20:00Z")]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["episodios"] == [{"workflow_id": 100, "run_falha_id": 1,
        "run_sucesso_id": 3, "inicio": "2026-05-10T10:00:00Z", "fim": "2026-05-10T11:20:00Z",
        "duracao_horas": 4/3, "censurado": False, "falhas_no_episodio": 2}]
    assert r["tempo_recuperacao"] == 4/3
    assert r["iqr_horas"] == r["proporcao_censurados"] == 0
    assert r["classe_tempo_recuperacao"] == "High"


@pytest.mark.parametrize("conclusion", ["failure", "timed_out", "startup_failure"])
def test_falha_so_abre_apos_sucesso_observado(conclusion):
    runs = [run(1, conclusion), run(2, "success", "11:00:00")]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["episodios"] == []
    assert r["historico_inicial_nao_observado"] == [{"workflow_id": 100, "run_falha_ids": [1],
        "run_sucesso_id": 2, "censura_esquerda": True, "duracao_horas": None}]
    assert r["tempo_recuperacao"] is r["proporcao_censurados"] is None
    e = tr.identificar_episodios([run(9, "success", "09:00:00"), *runs], FIM)
    assert len(e) == 1 and e[0]["duracao_horas"] == 1


@pytest.mark.parametrize("conclusion", ["cancelled", "skipped", "neutral", "action_required", "stale",
                                       "unknown", "SUCCESS", "", None])
def test_conclusions_ignoradas_nao_abrem_nem_recuperam(conclusion):
    runs = [run(9, "success", "09:00:00"), run(1), run(2, conclusion, "10:30:00")]
    e = tr.identificar_episodios(runs, FIM)
    assert len(e) == 1 and e[0]["censurado"] and e[0]["falhas_no_episodio"] == 1
    e = tr.identificar_episodios([*runs, run(3, "success", "11:20:00")], FIM)
    assert e[0]["duracao_horas"] == 4/3
    assert tr.identificar_episodios([run(2, conclusion)], FIM) == []


def test_workflows_independentes_e_ordenacao_por_inicio():
    runs = [run(9, "success", "09:00:00"), run(8, "success", "09:00:00", workflow_id=200),
            run(1), run(2, hora="10:20:00", workflow_id=200),
            run(3, "success", "11:00:00", workflow_id=200), run(4, "success", "11:20:00")]
    esperado = tr.identificar_episodios(runs, FIM)
    assert [(e["workflow_id"], e["duracao_horas"]) for e in esperado] == [(100, 4/3), (200, 2/3)]
    assert tr.identificar_episodios(list(reversed(runs)) + [runs[2]], FIM) == esperado
    assert tr.identificar_episodios(runs[:-1], FIM)[0]["censurado"]


def test_episodios_multiplos_quartis_e_proporcao():
    runs = [run(9, "success", "09:00:00"), run(1), run(2, "success", "11:00:00"),
            run(3, hora="12:00:00"), run(4, "startup_failure", "13:00:00"),
            run(5, "success", "14:00:00"), run(6, hora="15:00:00")]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["tempo_recuperacao"] == 1.5
    assert (r["q1_horas"], r["q3_horas"], r["iqr_horas"]) == (1.25, 1.75, .5)
    assert (r["total_episodios"], r["episodios_recuperados"], r["episodios_censurados"]) == (3, 2, 1)
    assert r["proporcao_censurados"] == 1/3
    assert r["episodios"][1]["falhas_no_episodio"] == 2


@pytest.mark.parametrize("termino", ["2026-10-01T00:00:00Z", "2026-10-01T00:05:00Z"])
def test_sucesso_criado_dentro_mas_terminado_fora_e_censurado(termino):
    runs = [run(9, "success", created_at="2026-09-30T21:00:00Z"),
            run(1, created_at="2026-09-30T21:55:00Z", run_started_at="2026-09-30T22:00:00Z"),
            run(2, "success", created_at="2026-09-30T23:50:00Z", updated_at=termino)]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["episodios"][0]["duracao_horas"] == 2
    assert r["episodios"][0]["censurado"] and r["episodios"][0]["run_sucesso_id"] is None
    assert r["proporcao_censurados"] == 1 and r["tempo_recuperacao"] is None
    assert r["runs_fora_recorte"] == 0


@pytest.mark.parametrize("campo,valor", [
    ("run_started_at", None), ("run_started_at", "inválido"),
    ("run_started_at", "2026-05-10T10:00:00"), ("updated_at", None),
    ("updated_at", "inválido"), ("updated_at", "2026-05-10T08:00:00Z"),
    ("run_started_at", "2026-05-10T08:00:00Z")])
def test_timestamp_invalido_nao_produz_estimativa_nem_fallback(campo, valor):
    runs = [run(9, "success", "09:00:00"), run(1), run(2, "success", "11:00:00", **{campo: valor})]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["episodios"] == [] and r["tempo_recuperacao"] is None
    assert r["dados_temporais_incompletos"]
    assert r["workflows_com_dados_temporais_invalidos"][0]["runs_invalidos"][0]["run_id"] == 2


def test_timestamp_ausente_preserva_outro_workflow_valido():
    runs = [run(9, "success", "09:00:00"), run(1), run(2, "success", "11:00:00"),
            run(3, workflow_id=200)]
    del runs[-1]["run_started_at"]
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["tempo_recuperacao"] == 1 and r["dados_temporais_incompletos"]


def test_falha_inicial_aberta_nao_inventa_inicio_apos_sucesso():
    r = tr.calcular_repositorio(repo([run(1), run(2, "timed_out", "11:00:00")]), INICIO, FIM)
    assert r["episodios"] == [] and r["historico_inicial_nao_observado"][0]["run_falha_ids"] == [1, 2]
    assert r["historico_inicial_nao_observado"][0]["run_sucesso_id"] is None


def test_recorte_nao_usa_sucesso_anterior_fora_da_janela():
    runs = [run(9, "success", created_at="2025-09-30T23:59:59Z"),
            run(1, created_at="2025-10-01T00:00:00Z"),
            run(2, "success", created_at="2025-10-01T01:20:00Z"),
            run(3, head_branch="dev"), run(4, event="pull_request"), run(5, "skipped")]
    original = deepcopy(runs)
    r = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert r["tempo_recuperacao"] is None and len(r["historico_inicial_nao_observado"]) == 1
    assert r["runs_fora_recorte"] == 3 and r["runs_ignorados"] == 1 and runs == original


def test_fuso_horario_e_inicio_atrasado_fora_janela():
    runs = [run(9, "success", "09:00:00", head_branch="master"),
            run(1, head_branch="master", run_started_at="2026-05-10T07:00:00-03:00"),
            run(2, "success", "11:00:00", head_branch="master"),
            run(3, head_branch="master", created_at="2026-09-30T23:59:00Z", run_started_at="2026-10-01T00:01:00Z")]
    r = tr.calcular_repositorio(repo(runs, default_branch="master"), INICIO, FIM)
    assert r["tempo_recuperacao"] == 1 and r["episodios"][0]["inicio"] == "2026-05-10T10:00:00Z"
    assert r["runs_iniciados_fora_janela"] == [3] and r["dados_temporais_incompletos"]


def test_mediana_iqr_e_sem_episodios():
    assert tr.resumir([])["proporcao_censurados"] is None
    r = tr.resumir([{"duracao_horas": h, "censurado": False} for h in [8,2,1,4]]
                   + [{"duracao_horas": 1000, "censurado": True}])
    assert (r["tempo_recuperacao"], r["q1_horas"], r["q3_horas"], r["iqr_horas"]) == (3,1.75,5,3.25)
    assert r["proporcao_censurados"] == .2


@pytest.mark.parametrize("branch", [None, "", "  ", 12])
def test_default_branch_invalido(branch):
    with pytest.raises(ConfigError, match="Default branch ausente"):
        tr.calcular_repositorio(repo(default_branch=branch), INICIO, FIM)


@pytest.mark.parametrize("campo", ["id", "workflow_id"])
@pytest.mark.parametrize("valor", [None, 0, -1, True, "100"])
def test_ids_invalidos_nao_sao_agrupados_silenciosamente(campo, valor):
    with pytest.raises(ConfigError, match=f"{campo} ausente ou inválido"):
        tr.calcular_repositorio(repo([run(**{campo: valor})]), INICIO, FIM)


@pytest.mark.parametrize("data", [None, "inválido", "2026-05-10T10:00:00"])
def test_created_at_invalido(data):
    with pytest.raises(ConfigError, match="created_at inválido"):
        tr.calcular_repositorio(repo([run(created_at=data)]), INICIO, FIM)


def test_created_at_ausente():
    registro = run()
    del registro["created_at"]
    with pytest.raises(ConfigError, match="created_at inválido"):
        tr.identificar_episodios([registro], FIM)


@pytest.mark.parametrize("campos", [{"coleta_incompleta": True},
                                    {"meses": [{"coleta_incompleta": True}]}])
def test_coleta_incompleta_preserva_marca_e_alerta(campos, caplog):
    resultado = tr.calcular_repositorio(repo([run(9, "success", "09:00:00"), run(1), run(2, "success", "11:00:00")], **campos), INICIO, FIM)
    assert resultado["coleta_incompleta"] is True
    assert resultado["tempo_recuperacao"] == 1
    assert "org/projeto: tempo de recuperação calculado sobre coleta incompleta" in caplog.text


def test_executar_consolida_episodios_recuperados_e_censurados(config):
    entrada = gravar_entrada(config, [repo([run(9, "success", "09:00:00"), run(1), run(2, "success", "11:20:00")]),
        repo([run(9, "success", "09:00:00"), run(3)], id=11, full_name="org/censurado", coleta_incompleta=True)])
    original = entrada.read_bytes()
    saida, lista = tr.executar(config)
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert saida == Path(config["caminhos"]["processed"]) / "tempo_recuperacao.json"
    assert dados["origem"] == str(entrada)
    assert dados["janela"] == JANELA
    assert dados["total_repositorios"] == dados["total_episodios"] == 2
    assert dados["repositorios_com_tempo_recuperacao"] == dados["episodios_censurados"] == 1
    assert dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["repositorios"] == lista
    assert entrada.read_bytes() == original


def test_consolidado_sem_repositorios(config):
    gravar_entrada(config, [])
    saida, lista = tr.executar(config)
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert lista == []
    assert dados["total_episodios"] == dados["total_repositorios"] == 0


@pytest.mark.parametrize("janela", [None, {}, {**JANELA, "inicio": "2024-10-01T00:00:00Z"}])
def test_janela_da_entrada_deve_corresponder_a_configuracao(config, janela):
    gravar_entrada(config, janela=janela)
    with pytest.raises(ConfigError, match="janela dos workflow runs"):
        tr.executar(config)
    assert not Path(config["caminhos"]["processed"]).exists()


def test_entrada_ausente(config):
    with pytest.raises(FileNotFoundError, match="execute antes a coleta de workflow_runs"):
        tr.executar(config)


def test_saida_nao_pode_sobrescrever_entrada(config):
    entrada = gravar_entrada(config)
    original = entrada.read_bytes()
    with pytest.raises(ConfigError, match="saída do tempo de recuperação deve ser diferente"):
        tr.executar(config, entrada, entrada.parent / "." / entrada.name)
    assert entrada.read_bytes() == original


def test_cli_entrada_absoluta_do_piloto_sem_token_e_sem_rede(config, tmp_path, monkeypatch, capsys):
    entrada = gravar_entrada(config, caminho=tmp_path / "coleta" / "piloto-100" / "workflow_runs.json")
    saida = tmp_path / "processed" / "piloto-100" / "tempo_recuperacao.json"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    def rede_proibida(*args, **kwargs):
        pytest.fail("O cálculo não deve acessar a rede")
    monkeypatch.setattr(requests.Session, "request", rede_proibida)
    assert tr.main(["--config", gravar_config(config, tmp_path),
                    "--entrada", str(entrada), "--saida", str(saida)]) == 0
    assert "1 censurados" in capsys.readouterr().out
    assert json.loads(saida.read_text(encoding="utf-8"))["episodios_censurados"] == 1


def test_cli_padrao_usa_config_local(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    gravar_config(config, tmp_path)
    monkeypatch.chdir(tmp_path)
    assert tr.main([]) == 0


@pytest.mark.parametrize("erro", ["entrada_ausente", "config_ausente", "json_invalido", "janela_invalida"])
def test_cli_erros_retornam_codigo_dois(config, tmp_path, capsys, erro):
    caminho_config = gravar_config(config, tmp_path)
    if erro == "config_ausente":
        caminho_config = str(tmp_path / "inexistente.yaml")
    elif erro == "json_invalido":
        gravar_entrada(config).write_text("{parcial", encoding="utf-8")
    elif erro == "janela_invalida":
        gravar_entrada(config, janela={})
    assert tr.main(["--config", caminho_config]) == 2
    assert "erro:" in capsys.readouterr().err


def test_entrypoint_executa_cli(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    monkeypatch.setattr(sys, "argv", ["pipeline.tempo_recuperacao", "--config", gravar_config(config, tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(tr.__file__, run_name="__main__")
    assert exc.value.code == 0


def test_integracao_com_coletor_mensal_episodio_atravessa_meses(config):
    registros = [run(9, "success", created_at="2025-10-31T22:00:00Z"), run(1, created_at="2025-10-31T23:00:00Z"),
                 run(2, "success", created_at="2025-11-01T00:20:00Z")]
    class ClienteFalso:
        chamadas = 0
        def get(self, path, params):
            self.chamadas += 1
            assert path == "/repos/org/projeto/actions/runs"
            assert params["branch"] == "main" and params["event"] == "push"
            assert params["page"] == 1
            mes = params["created"][:7]
            selecionados = [r for r in registros if r["created_at"].startswith(mes)]
            return {"total_count": len(selecionados), "workflow_runs": selecionados}
    cliente = ClienteFalso()
    workflow_runs.executar(config, cliente, [{"id": 10, "full_name": "org/projeto", "default_branch": "main"}])
    _, lista = tr.executar(config)
    assert cliente.chamadas == 12
    assert lista[0]["tempo_recuperacao"] == 4 / 3
    assert lista[0]["total_episodios"] == 1
    assert lista[0]["coleta_incompleta"] is False
