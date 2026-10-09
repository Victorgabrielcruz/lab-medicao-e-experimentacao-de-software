import datetime as dt
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import requests
import yaml

from pipeline import compare, lead_time_commit as lead_time
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
PUBLICADA = "2026-03-15T00:00:00Z"


def commit(sha="abc", data="2026-03-02T00:00:00Z"):
    return {"sha": sha, "commit": {"author": {"date": data}, "committer": {"date": "2026-03-14T00:00:00Z"}}}


def comparacao(id=1, commits=None, publicada=PUBLICADA, **campos):
    commits = [commit()] if commits is None else commits
    return {"release": {"id": id, "tag_name": f"v{id}", "published_at": publicada},
            "release_anterior": {"id": id-1, "tag_name": f"v{id-1}", "published_at": "2025-09-15T00:00:00Z"},
            "commits": commits, "total_commits_api": len({c.get("sha") for c in commits}),
            "total_commits_coletados": len({c.get("sha") for c in commits}),
            "ignorada": False, "motivo": None, "coleta_incompleta": False, **campos}


def repo(comparacoes=None, **campos):
    return {"id": 10, "full_name": "org/projeto", "default_branch": "main",
            "comparacoes": [comparacao()] if comparacoes is None else comparacoes,
            "coleta_incompleta": False, **campos}


@pytest.fixture
def exemplo_enunciado():
    return comparacao(commits=[commit("dia-02", "2026-03-02T00:00:00Z"),
                              commit("dia-10", "2026-03-10T00:00:00Z"),
                              commit("dia-14", "2026-03-14T00:00:00Z")])


@pytest.fixture
def config(tmp_path):
    return {"api": {"base_url": "https://api.github.com"}, "janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "inclusao": {"min_releases": 5, "min_runs_validos": 50}, "runs": {"evento": "push", "somente_default_branch": True},
            "caminhos": {"raw": str(tmp_path / "raw"), "processed": str(tmp_path / "processed"), "cache": str(tmp_path / "cache")}}


def gravar_entrada(config, repos=None, caminho=None, **campos):
    caminho = Path(caminho) if caminho is not None else Path(config["caminhos"]["raw"]) / "compare.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps({"janela": JANELA, "definicao_deploy": "release_estavel",
                                   "repositorios": [repo()] if repos is None else repos, **campos}), encoding="utf-8")
    return caminho


def gravar_config(config, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(caminho)


def test_fixture_enunciado_13_5_1_dias_e_mediana_5_dias(exemplo_enunciado):
    original = deepcopy(exemplo_enunciado)
    resultado = lead_time.calcular_repositorio(repo([exemplo_enunciado]), INICIO, FIM)
    assert [c["lead_time_horas"] for c in resultado["releases"][0]["commits"]] == [312, 120, 24]
    assert resultado["lead_time_horas"] == 120
    assert resultado["classe_lead_time"] == "High"
    assert resultado["commits_com_lead_time"] == 3
    assert exemplo_enunciado == original


def test_mediana_de_todos_commits_de_todas_releases(exemplo_enunciado):
    segunda = comparacao(2, [commit("outro", "2026-02-13T00:00:00Z")])  # 30 dias.
    resultado = lead_time.calcular_repositorio(repo([exemplo_enunciado, segunda]), INICIO, FIM)
    assert resultado["lead_time_horas"] == 216  # Mediana de [312, 120, 24, 720] = 9 dias.
    assert resultado["commits_com_lead_time"] == 4
    assert resultado["lead_time_horas"] != (120 + 720) / 2  # Não é mediana das medianas por release.


def test_sha_repetido_na_mesma_release_deduplicado_entre_releases_preservado():
    primeira = comparacao(commits=[commit(), commit()])
    segunda = comparacao(2, [commit()], publicada="2026-03-16T00:00:00Z")
    resultado = lead_time.calcular_repositorio(repo([primeira, segunda]), INICIO, FIM)
    assert resultado["total_commits"] == 2
    assert resultado["lead_time_horas"] == 324  # O mesmo SHA tem 13 e 14 dias nas duas entregas.


def test_data_do_autor_usada_em_vez_de_committer():
    assert lead_time.calcular_commit(commit(), PUBLICADA)["lead_time_horas"] == 312


def test_fusos_e_fracoes_de_hora_sem_arredondamento():
    resultado = lead_time.calcular_commit(commit(data="2026-03-14T20:47:30-03:00"), PUBLICADA)
    assert resultado["lead_time_horas"] == pytest.approx(12.5 / 60)
    assert resultado["author_date"] == "2026-03-14T23:47:30Z"


def test_commit_anterior_a_janela_considerado_na_release_da_janela():
    cmp = comparacao(publicada=JANELA["inicio"], commits=[commit(data="2025-09-28T00:00:00Z")])
    assert lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)["lead_time_horas"] == 72


def test_zero_real_valido_e_classe_elite():
    cmp = comparacao(commits=[commit(data=PUBLICADA)])
    resultado = lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)
    assert resultado["lead_time_horas"] == 0
    assert resultado["classe_lead_time"] == "Elite"
    assert not resultado["calculo_parcial"]


def test_primeira_release_sem_anterior_e_sem_commits_nao_geram_valores_artificiais():
    resultado = lead_time.calcular_repositorio(repo([comparacao(release_anterior=None), comparacao(2, [])]), INICIO, FIM)
    assert resultado["lead_time_horas"] is None and resultado["classe_lead_time"] is None
    assert resultado["commits_com_lead_time"] == 0
    assert resultado["releases_ignoradas_por_motivo"] == {"sem_release_anterior": 1, "sem_commits_novos": 1}
    assert not resultado["calculo_parcial"]


@pytest.mark.parametrize("motivo", ["sem_release_anterior", "compare_inacessivel", "historico_releases_inacessivel", None])
def test_compare_ignorado_nao_calculado_e_motivo_preservado(motivo):
    resultado = lead_time.calcular_release(comparacao(ignorada=True, motivo=motivo, detalhe="HTTP 404"))
    assert resultado["commits"] == [] and resultado["ignorada"]
    assert resultado["motivo"] == (motivo or "compare_ignorado")
    assert resultado["detalhe"] == "HTTP 404"


def test_compare_incompleto_exclui_os_commits_parciais():
    resultado = lead_time.calcular_release(comparacao(coleta_incompleta=True))
    assert resultado["motivo"] == "compare_incompleto"
    assert resultado["commits"] == []


@pytest.mark.parametrize("campo", ["total_commits_api", "total_commits_coletados"])
def test_total_divergente_sinaliza_coleta_incompleta(campo):
    resultado = lead_time.calcular_release(comparacao(**{campo: 2}))
    assert resultado["motivo"] == "compare_incompleto" and resultado["coleta_incompleta"]


@pytest.mark.parametrize("sha", [None, "", 42])
def test_sha_invalido_registrado(sha):
    assert lead_time.calcular_commit(commit(sha), PUBLICADA)["motivo"] == "commit_sem_sha"
    assert lead_time.calcular_release(comparacao(commits=[commit(sha)]))["motivo"] == "commit_sem_sha"


@pytest.mark.parametrize("data", [None, "inválida", "2026-03-02T00:00:00", 42])
def test_data_invalida_ignora_so_commit_e_sinaliza_mediana_parcial(data, caplog):
    cmp = comparacao(commits=[commit(), commit("bad", data)])
    resultado = lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)
    assert resultado["lead_time_horas"] == 312
    assert resultado["commits_com_lead_time"] == resultado["commits_ignorados"] == 1
    assert resultado["commits_ignorados_por_motivo"] == {"data_commit_invalida": 1}
    assert resultado["calculo_parcial"] and not resultado["coleta_incompleta"]
    assert "cálculo parcial=True" in caplog.text


@pytest.mark.parametrize("corpo", [{}, {"commit": {}}, {"commit": {"author": None}}])
def test_author_ausente_ignorado_sem_fallback(corpo):
    resultado = lead_time.calcular_commit({"sha": "abc", **corpo}, PUBLICADA)
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == "data_commit_invalida"


def test_intervalo_negativo_ignorado_individualmente_sem_converter_em_zero():
    cmp = comparacao(commits=[commit(), commit("futuro", "2026-03-16T00:00:00Z")])
    resultado = lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)
    assert resultado["lead_time_horas"] == 312
    assert resultado["commits_ignorados_por_motivo"] == {"lead_time_negativo": 1}
    futuro = resultado["releases"][0]["commits"][1]
    assert futuro["lead_time_horas"] is None and futuro["author_date"] == "2026-03-16T00:00:00Z"


def test_todos_commits_invalidos_mediana_nula_e_release_ignorada():
    resultado = lead_time.calcular_repositorio(repo([comparacao(commits=[commit(data=None)])]), INICIO, FIM)
    assert resultado["lead_time_horas"] is None and resultado["classe_lead_time"] is None
    assert resultado["commits_ignorados"] == resultado["releases_ignoradas"] == 1
    assert resultado["releases_ignoradas_por_motivo"] == {"sem_commits_validos": 1}


@pytest.mark.parametrize("publicada", [None, "inválida", "2026-03-15T00:00:00"])
def test_data_release_invalida(publicada):
    assert lead_time.calcular_commit(commit(), publicada)["motivo"] == "data_release_invalida"
    assert lead_time.calcular_release(comparacao(publicada=publicada))["motivo"] == "data_release_invalida"
    with pytest.raises(ConfigError, match="published_at inválido"):
        lead_time.calcular_repositorio(repo([comparacao(publicada=publicada)]), INICIO, FIM)


def test_janela_limites_deduplicacao_e_ordenacao_de_releases():
    comparacoes = [comparacao(2, publicada="2026-09-30T23:59:59.999999Z"),
                   comparacao(1, [commit(data="2025-09-30T00:00:00Z")], publicada="2025-09-30T21:00:00-03:00"),
                   comparacao(3, publicada="2025-09-30T23:59:59Z"), comparacao(4, publicada="2026-10-01T00:00:00Z"), comparacao(2)]
    original = deepcopy(comparacoes)
    resultado = lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)
    assert resultado["total_releases"] == 2
    assert resultado["releases_fora_janela"] == 2 and resultado["releases_duplicadas"] == 1
    assert [r["release"]["id"] for r in resultado["releases"]] == [1, 2]
    assert comparacoes == original


def test_release_sem_id_recusada():
    cmp = comparacao()
    cmp["release"].pop("id")
    with pytest.raises(ConfigError, match="Release sem ID"):
        lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)


def test_repositorio_sem_releases_e_nulo():
    resultado = lead_time.calcular_repositorio(repo([]), INICIO, FIM)
    assert resultado["lead_time_horas"] is None and resultado["total_commits"] == 0
    assert not resultado["calculo_parcial"]


def test_coleta_incompleta_no_repositorio_preservada_com_mediana_parcial():
    resultado = lead_time.calcular_repositorio(repo(coleta_incompleta=True), INICIO, FIM)
    assert resultado["lead_time_horas"] == 312
    assert resultado["coleta_incompleta"] and resultado["calculo_parcial"]


def test_compatibilidade_com_saida_real_do_compare(exemplo_enunciado):
    anterior = {"id": 0, "tag_name": "v0", "draft": False, "prerelease": False, "published_at": "2025-09-30T00:00:00Z"}
    atual = {**anterior, "id": 1, "tag_name": "v1", "published_at": PUBLICADA}

    class Cliente:
        def get_resposta(self, path, params):
            r = requests.Response()
            r.status_code = 200
            corpo = [anterior, atual] if path.endswith("/releases") else {"status": "ahead", "total_commits": 3, "commits": exemplo_enunciado["commits"]}
            r._content = json.dumps(corpo).encode()
            return r

    coletado = compare.coletar_repositorio(Cliente(), {**repo(), "releases": [atual]}, INICIO, FIM)
    assert lead_time.calcular_repositorio(coletado, INICIO, FIM)["lead_time_horas"] == 120


def test_consolidado_contagens_intervalos_e_entrada_preservada(config, exemplo_enunciado):
    entrada = gravar_entrada(config, [repo([exemplo_enunciado]), repo([], id=11),
                                    repo([comparacao(commits=[commit(data=None)])], id=12)])
    original = entrada.read_bytes()
    caminho, lista = lead_time.executar(config)
    dados = json.loads(caminho.read_text())
    assert caminho == Path(config["caminhos"]["processed"]) / "lead_time_commit.json"
    assert dados["variante"] == "b" and dados["unidade"] == "horas"
    assert dados["formula"] == "published_at - commit.author.date"
    assert dados["origem"] == str(entrada) and dados["janela"] == JANELA
    assert dados["total_repositorios"] == 3 and dados["repositorios_com_lead_time"] == 1
    assert dados["total_commits"] == 4 and dados["commits_com_lead_time"] == 3
    assert dados["commits_ignorados"] == dados["repositorios_com_calculo_parcial"] == 1
    assert dados["repositorios"] == lista and entrada.read_bytes() == original


def test_consolidado_vazio(config):
    gravar_entrada(config, [])
    caminho, lista = lead_time.executar(config)
    assert lista == [] and json.loads(caminho.read_text())["total_commits"] == 0


@pytest.mark.parametrize("janela", [None, {}, {**JANELA, "inicio": "2024-10-01T00:00:00Z"}])
def test_janela_divergente_recusada(config, janela):
    gravar_entrada(config, janela=janela)
    with pytest.raises(ConfigError, match="janela do compare"):
        lead_time.executar(config)


@pytest.mark.parametrize("definicao", [None, "tag", "release_com_prerelease"])
def test_definicao_de_deploy_incompativel_recusada(config, definicao):
    gravar_entrada(config, definicao_deploy=definicao)
    with pytest.raises(ConfigError, match="definicao_deploy=release_estavel"):
        lead_time.executar(config)


def test_entrada_ausente(config):
    with pytest.raises(FileNotFoundError, match="execute antes a etapa compare"):
        lead_time.executar(config)


def test_saida_nao_pode_sobrescrever_entrada(config):
    entrada = gravar_entrada(config)
    original = entrada.read_bytes()
    with pytest.raises(ConfigError, match="saída de lead time deve ser diferente"):
        lead_time.executar(config, entrada, entrada)
    assert entrada.read_bytes() == original


def test_cli_piloto_sem_token_sem_rede(config, tmp_path, monkeypatch, capsys, exemplo_enunciado):
    entrada = gravar_entrada(config, [repo([exemplo_enunciado])], caminho=tmp_path / "raw" / "piloto-100" / "compare.json")
    saida = tmp_path / "processed" / "piloto-100" / "lead_time_commit.json"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(requests.Session, "request", lambda *args, **kwargs: pytest.fail("cálculo não deve acessar rede"))
    assert lead_time.main(["--config", gravar_config(config, tmp_path), "--entrada", str(entrada), "--saida", str(saida)]) == 0
    assert "Lead time (RQ02b): 1/1 repositórios com métrica, 3 intervalos válidos" in capsys.readouterr().out
    assert json.loads(saida.read_text())["repositorios"][0]["lead_time_horas"] == 120


def test_cli_sem_argumentos_usa_config_local(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    gravar_config(config, tmp_path)
    monkeypatch.chdir(tmp_path)
    assert lead_time.main([]) == 0


@pytest.mark.parametrize("erro", ["entrada_ausente", "config_ausente", "json_invalido", "janela_invalida"])
def test_cli_reporta_erros_com_codigo_dois(config, tmp_path, capsys, erro):
    cfg_path = gravar_config(config, tmp_path)
    if erro == "config_ausente":
        cfg_path = str(tmp_path / "ausente.yaml")
    elif erro == "json_invalido":
        gravar_entrada(config).write_text("{parcial", encoding="utf-8")
    elif erro == "janela_invalida":
        gravar_entrada(config, janela={})
    assert lead_time.main(["--config", cfg_path]) == 2
    assert "erro:" in capsys.readouterr().err


def test_entrypoint_executa_cli(config, tmp_path, monkeypatch):
    gravar_entrada(config)
    monkeypatch.setattr(sys, "argv", ["pipeline.lead_time_commit", "--config", gravar_config(config, tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(lead_time.__file__, run_name="__main__")
    assert exc.value.code == 0
