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
    return {"id": id, "workflow_id": workflow_id, "conclusion": conclusion,
            "head_branch": "main", "event": "push", "name": "CI",
            "created_at": f"2026-05-10T{hora}Z", **campos}


def repo(runs=None, **campos):
    return {"id": 10, "full_name": "org/projeto", "default_branch": "main",
            "workflow_runs": [run()] if runs is None else runs,
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


def test_cenario_de_1h20_da_primeira_falha_ate_o_sucesso():
    runs = [run(1), run(2, "timed_out", "10:30:00"), run(3, "success", "11:20:00")]
    resultado = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert resultado["episodios"] == [{"workflow_id": 100, "run_falha_id": 1,
        "run_sucesso_id": 3, "inicio": "2026-05-10T10:00:00Z", "fim": "2026-05-10T11:20:00Z",
        "duracao_horas": 4 / 3, "censurado": False, "falhas_no_episodio": 2}]
    assert resultado["tempo_recuperacao"] == 80 / 60
    assert resultado["total_episodios"] == resultado["episodios_recuperados"] == 1
    assert resultado["episodios_censurados"] == 0
    assert resultado["iqr_horas"] == 0
    assert resultado["classe_tempo_recuperacao"] == "High"


@pytest.mark.parametrize("conclusion", ["failure", "timed_out", "startup_failure"])
def test_cada_tipo_de_falha_abre_episodio(conclusion):
    episodios = tr.identificar_episodios([run(1, conclusion), run(2, "success", "11:00:00")], FIM)
    assert len(episodios) == 1
    assert episodios[0]["duracao_horas"] == 1
    assert episodios[0]["censurado"] is False


@pytest.mark.parametrize("conclusion", ["cancelled", "skipped", "neutral", "action_required", "stale",
                                       "unknown", "SUCCESS", "", None])
def test_conclusions_ignoradas_nao_abrem_nem_recuperam(conclusion):
    registro = run(2, conclusion, "10:30:00")
    assert tr.identificar_episodios([registro], FIM) == []
    episodios = tr.identificar_episodios([run(1), registro, run(3, "success", "11:20:00")], FIM)
    assert len(episodios) == 1
    assert episodios[0]["duracao_horas"] == 4 / 3
    assert episodios[0]["falhas_no_episodio"] == 1
    assert tr.identificar_episodios([run(1), registro], FIM)[0]["censurado"] is True


def test_conclusion_ausente_nao_altera_episodio():
    registro = run(2, hora="10:30:00")
    del registro["conclusion"]
    resultado = tr.calcular_repositorio(repo([run(1), registro, run(3, "success", "11:00:00")]), INICIO, FIM)
    assert resultado["tempo_recuperacao"] == 1
    assert resultado["runs_ignorados"] == 1


def test_workflows_intercalados_nao_compartilham_episodios_mesmo_com_nome_igual():
    runs = [run(1, workflow_id=100), run(2, hora="10:20:00", workflow_id=200),
            run(3, "success", "11:00:00", workflow_id=200),
            run(4, "success", "11:20:00", workflow_id=100)]
    episodios = tr.identificar_episodios(runs, FIM)
    assert [(e["workflow_id"], e["run_falha_id"], e["run_sucesso_id"]) for e in episodios] == [
        (100, 1, 4), (200, 2, 3)]
    assert [e["duracao_horas"] for e in episodios] == [4 / 3, 2 / 3]


def test_sucesso_de_outro_workflow_nao_recupera_falha():
    episodios = tr.identificar_episodios([run(1), run(2, "success", "11:00:00", workflow_id=200)], FIM)
    assert len(episodios) == 1
    assert episodios[0]["workflow_id"] == 100
    assert episodios[0]["censurado"] is True


def test_sucessos_sem_falha_anterior_nao_criam_episodios():
    assert tr.identificar_episodios([run(1, "success"), run(2, "success", "11:00:00")], FIM) == []


def test_varios_episodios_no_mesmo_workflow_e_falhas_consecutivas():
    runs = [run(1, "success", "09:00:00"), run(2), run(3, "success", "11:00:00"),
            run(4, hora="12:00:00"), run(5, "startup_failure", "13:00:00"),
            run(6, "success", "14:00:00"), run(7, "success", "15:00:00")]
    episodios = tr.identificar_episodios(runs, FIM)
    assert [e["duracao_horas"] for e in episodios] == [1, 2]
    assert [e["falhas_no_episodio"] for e in episodios] == [1, 2]
    assert tr.resumir(episodios) == {"total_episodios": 2, "episodios_recuperados": 2,
        "episodios_censurados": 0, "tempo_recuperacao": 1.5,
        "q1_horas": 1.25, "q3_horas": 1.75, "iqr_horas": 0.5}


def test_entrada_fora_de_ordem_e_ids_duplicados_nao_alteram_resultado():
    r1, r2 = run(1), run(2, "success", "11:20:00")
    esperado = tr.identificar_episodios([r1, r2], FIM)
    assert tr.identificar_episodios([r2, r1, deepcopy(r1), deepcopy(r2)], FIM) == esperado
    resultado = tr.calcular_repositorio(repo([r2, r1, deepcopy(r1), deepcopy(r2)]), INICIO, FIM)
    assert resultado["episodios"] == esperado
    assert resultado["runs_duplicados"] == 2


def test_mesma_data_usa_id_para_desempate_e_pode_ter_duracao_zero():
    episodios = tr.identificar_episodios([run(2, "success"), run(1)], FIM)
    assert len(episodios) == 1
    assert episodios[0]["duracao_horas"] == 0
    assert episodios[0]["censurado"] is False
    resultado = tr.calcular_repositorio(repo([run(2, "success"), run(1)]), INICIO, FIM)
    assert resultado["classe_tempo_recuperacao"] == "Elite"


def test_censura_usa_primeira_falha_ate_fim_exclusivo_da_janela():
    episodios = tr.identificar_episodios([
        run(1, created_at="2026-09-30T22:00:00Z"),
        run(2, "timed_out", created_at="2026-09-30T23:00:00Z")], FIM)
    assert episodios == [{"workflow_id": 100, "run_falha_id": 1, "run_sucesso_id": None,
        "inicio": "2026-09-30T22:00:00Z", "fim": "2026-10-01T00:00:00Z",
        "duracao_horas": 2, "censurado": True, "falhas_no_episodio": 2}]
    assert tr.resumir(episodios)["tempo_recuperacao"] is None


@pytest.mark.parametrize("data", ["2026-10-01T00:00:00Z", "2026-10-01T00:00:01Z"])
def test_sucesso_no_fim_ou_depois_nao_recupera_episodio(data):
    runs = [run(1, created_at="2026-09-30T23:00:00Z"), run(2, "success", created_at=data)]
    episodios = tr.identificar_episodios(runs, FIM)
    assert len(episodios) == 1
    assert episodios[0]["censurado"] is True
    assert episodios[0]["duracao_horas"] == 1
    resultado = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert resultado["runs_fora_recorte"] == 1
    assert resultado["tempo_recuperacao"] is None


def test_censurados_nao_entram_na_mediana_ou_iqr():
    episodios = [{"duracao_horas": 1, "censurado": False},
                 {"duracao_horas": 1000, "censurado": True}]
    assert tr.resumir(episodios) == {"total_episodios": 2, "episodios_recuperados": 1,
        "episodios_censurados": 1, "tempo_recuperacao": 1, "q1_horas": 1, "q3_horas": 1, "iqr_horas": 0}


def test_mediana_e_quartis_inclusivos():
    episodios = [{"duracao_horas": h, "censurado": False} for h in [8, 2, 1, 4]]
    resumo = tr.resumir(episodios)
    assert resumo["tempo_recuperacao"] == 3
    assert resumo["q1_horas"] == 1.75
    assert resumo["q3_horas"] == 5
    assert resumo["iqr_horas"] == 3.25


@pytest.mark.parametrize("runs", [[], [run(conclusion="success")], [run()], [run(conclusion=None)]])
def test_sem_recuperacoes_estatisticas_e_classe_ficam_nulas(runs):
    resultado = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    for campo in ("tempo_recuperacao", "q1_horas", "q3_horas", "iqr_horas", "classe_tempo_recuperacao"):
        assert resultado[campo] is None
    assert resultado["episodios_recuperados"] == 0


def test_recorte_branch_evento_inicio_inclusivo_e_dados_preservados():
    runs = [run(1, created_at="2025-10-01T00:00:00Z"),
            run(2, "success", created_at="2025-10-01T01:20:00Z"),
            run(3, head_branch="dev"), run(4, event="pull_request"),
            run(5, created_at="2025-09-30T23:59:59Z"), run(6, "skipped")]
    original = deepcopy(runs)
    resultado = tr.calcular_repositorio(repo(runs), INICIO, FIM)
    assert resultado["tempo_recuperacao"] == 4 / 3
    assert resultado["runs_fora_recorte"] == 3
    assert resultado["runs_ignorados"] == 1
    assert runs == original


def test_datas_com_fuso_normalizadas_e_branch_diferente_de_main():
    runs = [run(1, head_branch="master", created_at="2025-09-30T21:00:00-03:00"),
            run(2, "success", head_branch="master", created_at="2025-10-01T01:20:00Z")]
    resultado = tr.calcular_repositorio(repo(runs, default_branch="master"), INICIO, FIM)
    assert resultado["episodios"][0]["inicio"] == "2025-10-01T00:00:00Z"
    assert resultado["tempo_recuperacao"] == 4 / 3


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
    resultado = tr.calcular_repositorio(repo([run(1), run(2, "success", "11:00:00")], **campos), INICIO, FIM)
    assert resultado["coleta_incompleta"] is True
    assert resultado["tempo_recuperacao"] == 1
    assert "org/projeto: tempo de recuperação calculado sobre coleta incompleta" in caplog.text


def test_executar_consolida_episodios_recuperados_e_censurados(config):
    entrada = gravar_entrada(config, [repo([run(1), run(2, "success", "11:20:00")]),
        repo([run(3)], id=11, full_name="org/censurado", coleta_incompleta=True)])
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
    registros = [run(1, created_at="2025-10-31T23:00:00Z"),
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
