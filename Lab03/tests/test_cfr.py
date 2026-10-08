import datetime as dt
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import requests
import yaml

from pipeline import cfr
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def run(id=1, conclusion="success", **campos):
    return {"id": id, "conclusion": conclusion, "head_branch": "main", "event": "push",
            "created_at": "2026-05-10T12:00:00Z", **campos}


def repo(runs=None, **campos):
    return {"id": 10, "full_name": "org/projeto", "default_branch": "main",
            "workflow_runs": [run()] if runs is None else runs, "coleta_incompleta": False,
            "meses": [], **campos}


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


@pytest.mark.parametrize("conclusion", ["failure", "timed_out", "startup_failure"])
def test_cada_conclusion_de_falha(conclusion):
    assert cfr.calcular([run(conclusion=conclusion)]) == {
        "falhas": 1, "sucessos": 0, "ignorados": 0, "runs_validos": 1, "change_failure_rate": 1.0}


def test_success_conta_como_sucesso():
    assert cfr.calcular([run()]) == {
        "falhas": 0, "sucessos": 1, "ignorados": 0, "runs_validos": 1, "change_failure_rate": 0.0}


@pytest.mark.parametrize("conclusion", ["cancelled", "skipped", "neutral", "action_required", "stale",
                                       "unknown", "SUCCESS", "", None])
def test_conclusions_ignoradas_nao_entram_no_denominador(conclusion):
    resultado = cfr.calcular([run(conclusion=conclusion), run(2, "failure"), run(3)])
    assert resultado == {"falhas": 1, "sucessos": 1, "ignorados": 1,
                         "runs_validos": 2, "change_failure_rate": 0.5}


def test_conclusion_ausente_e_ignorada():
    resultado = cfr.calcular([{"id": 1}])
    assert resultado["ignorados"] == 1
    assert resultado["change_failure_rate"] is None


@pytest.mark.parametrize("runs", [[], [run(conclusion=None)], [run(conclusion="cancelled")]])
def test_sem_runs_validos_e_nulo_e_nao_zero(runs):
    resultado = cfr.calcular(runs)
    assert resultado["runs_validos"] == 0
    assert resultado["change_failure_rate"] is None


def test_mistura_das_tres_falhas_sucessos_e_ignorados():
    runs = [run(i, conclusion) for i, conclusion in enumerate(
        ["failure", "timed_out", "startup_failure", "success", "success", "cancelled", None])]
    assert cfr.calcular(iter(runs)) == {"falhas": 3, "sucessos": 2, "ignorados": 2,
                                       "runs_validos": 5, "change_failure_rate": 0.6}


def test_fracao_sem_arredondamento():
    resultado = cfr.calcular([run(1, "failure"), run(2), run(3)])
    assert resultado["change_failure_rate"] == 1 / 3


def test_recorte_default_branch_push_janela_e_deduplicacao():
    runs = [run(1, "failure", created_at="2025-10-01T00:00:00Z"),
            run(2, created_at="2026-09-30T23:59:59Z"),
            run(3, "timed_out", head_branch="dev"),
            run(4, "startup_failure", event="pull_request"),
            run(5, "failure", created_at="2025-09-30T23:59:59Z"),
            run(6, "failure", created_at="2026-10-01T00:00:00Z"),
            run(2), run(7, "skipped")]
    original = deepcopy(runs)
    resultado = cfr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert resultado["falhas"] == resultado["sucessos"] == 1
    assert resultado["ignorados"] == 1
    assert resultado["change_failure_rate"] == 0.5
    assert resultado["classe_cfr"] == "Low"
    assert resultado["runs_fora_recorte"] == 4
    assert resultado["runs_duplicados"] == 1
    assert runs == original


def test_branch_nao_precisa_se_chamar_main_e_datas_com_offset_sao_aceitas():
    resultado = cfr.calcular_repositorio(repo([run(head_branch="master", created_at="2025-09-30T21:00:00-03:00")],
                                            default_branch="master"), INICIO, FIM)
    assert resultado["runs_validos"] == 1
    assert resultado["change_failure_rate"] == 0


@pytest.mark.parametrize("branch", [None, "", "  ", 12])
def test_default_branch_invalido(branch):
    with pytest.raises(ConfigError, match="Default branch ausente"):
        cfr.calcular_repositorio(repo(default_branch=branch), INICIO, FIM)


@pytest.mark.parametrize("data", [None, "inválido", "2026-02-01T00:00:00"])
def test_data_invalida_nao_e_silenciosamente_ignorada(data):
    with pytest.raises(ConfigError, match="created_at inválido"):
        cfr.calcular_repositorio(repo([run(created_at=data)]), INICIO, FIM)


def test_data_ausente():
    registro = run()
    del registro["created_at"]
    with pytest.raises(ConfigError, match="created_at inválido"):
        cfr.calcular_repositorio(repo([registro]), INICIO, FIM)


def test_id_ausente():
    registro = run()
    del registro["id"]
    with pytest.raises(ConfigError, match="Run sem ID"):
        cfr.calcular_repositorio(repo([registro]), INICIO, FIM)


@pytest.mark.parametrize("campos", [{"coleta_incompleta": True},
                                    {"meses": [{"coleta_incompleta": True}]}])
def test_cfr_de_coleta_incompleta_mantem_alerta_e_diagnostico(campos, caplog):
    resultado = cfr.calcular_repositorio(repo([run(1, "failure"), run(2)], **campos), INICIO, FIM)
    assert resultado["change_failure_rate"] == 0.5
    assert resultado["coleta_incompleta"] is True
    assert "org/projeto: CFR calculada sobre coleta incompleta" in caplog.text


def test_repositorio_sem_runs_validos_nao_recebe_classe():
    resultado = cfr.calcular_repositorio(repo([]), INICIO, FIM)
    assert resultado["change_failure_rate"] is None
    assert resultado["classe_cfr"] is None
    assert resultado["coleta_incompleta"] is False


def test_executar_consolidado_contagens_cfr_nula_e_classificacao(config):
    entrada = gravar_entrada(config, [repo([run(1, "failure"), run(2), run(3), run(4)]),
                                    repo([run(conclusion="skipped")], id=11, full_name="org/sem-validos"),
                                    repo([run()], id=12, full_name="org/parcial", coleta_incompleta=True)])
    original = entrada.read_bytes()
    saida, lista = cfr.executar(config)
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert saida == Path(config["caminhos"]["processed"]) / "cfr.json"
    assert dados["origem"] == str(entrada)
    assert dados["janela"] == JANELA
    assert dados["variante"] == "a"
    assert dados["total_repositorios"] == 3
    assert dados["repositorios_com_cfr"] == 2
    assert dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["repositorios"] == lista
    assert lista[0]["change_failure_rate"] == 0.25
    assert lista[0]["classe_cfr"] == "High"
    assert lista[1]["change_failure_rate"] is None
    assert dt.datetime.fromisoformat(dados["gerado_em"]).tzinfo is not None
    assert entrada.read_bytes() == original


def test_executar_lista_vazia(config):
    gravar_entrada(config, [])
    saida, lista = cfr.executar(config)
    assert lista == []
    dados = json.loads(saida.read_text(encoding="utf-8"))
    assert dados["total_repositorios"] == dados["repositorios_com_cfr"] == 0


@pytest.mark.parametrize("janela", [None, {}, {**JANELA, "inicio": "2024-10-01T00:00:00Z"}])
def test_janela_da_coleta_deve_corresponder_a_configuracao(config, janela):
    gravar_entrada(config, janela=janela)
    with pytest.raises(ConfigError, match="janela dos workflow runs"):
        cfr.executar(config)
    assert not Path(config["caminhos"]["processed"]).exists()


def test_arquivo_de_runs_ausente(config):
    with pytest.raises(FileNotFoundError, match="execute antes a coleta de workflow_runs"):
        cfr.executar(config)


def test_nao_permite_sobrescrever_entrada(config):
    entrada = gravar_entrada(config)
    original = entrada.read_bytes()
    with pytest.raises(ConfigError, match="saída da CFR deve ser diferente"):
        cfr.executar(config, entrada, entrada.parent / "." / entrada.name)
    assert entrada.read_bytes() == original


def test_cli_entrada_do_piloto_saida_separada_sem_token_sem_rede(config, tmp_path, monkeypatch, capsys):
    entrada = gravar_entrada(config, caminho=tmp_path / "coleta" / "piloto-100" / "workflow_runs.json")
    saida = tmp_path / "resultados" / "piloto-100" / "cfr.json"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    def rede_proibida(*args, **kwargs):
        pytest.fail("CFR não deve acessar a rede")
    monkeypatch.setattr(requests.Session, "request", rede_proibida)
    codigo = cfr.main(["--config", gravar_config(config, tmp_path),
                       "--entrada", str(entrada), "--saida", str(saida)])
    assert codigo == 0
    assert "CFR (a): 1/1 repositórios" in capsys.readouterr().out
    assert json.loads(saida.read_text(encoding="utf-8"))["repositorios"][0]["change_failure_rate"] == 0


def test_cli_sem_argumentos_usa_config_local(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    gravar_config(config, tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cfr.main([]) == 0


@pytest.mark.parametrize("erro", ["entrada_ausente", "config_ausente", "json_invalido", "janela_invalida"])
def test_cli_reporta_erros_com_codigo_dois(config, tmp_path, capsys, erro):
    caminho_config = gravar_config(config, tmp_path)
    if erro == "config_ausente":
        caminho_config = str(tmp_path / "inexistente.yaml")
    elif erro == "json_invalido":
        entrada = gravar_entrada(config)
        entrada.write_text("{parcial", encoding="utf-8")
    elif erro == "janela_invalida":
        gravar_entrada(config, janela={})
    assert cfr.main(["--config", caminho_config]) == 2
    assert "erro:" in capsys.readouterr().err


def test_entrypoint_executa_cli(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    monkeypatch.setattr(sys, "argv", ["pipeline.cfr", "--config", gravar_config(config, tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(cfr.__file__, run_name="__main__")
    assert exc.value.code == 0
