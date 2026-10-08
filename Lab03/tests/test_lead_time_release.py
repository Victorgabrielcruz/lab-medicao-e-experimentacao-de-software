import datetime as dt
import json
import runpy
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import requests
import yaml

from pipeline import compare, lead_time_release as lead_time
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def commit(sha="abc", data="2026-03-02T00:00:00Z"):
    return {"sha": sha, "commit": {"author": {"date": data}, "committer": {"date": "2026-03-14T00:00:00Z"}}}


def comparacao(id=1, commits=None, publicada="2026-03-15T00:00:00Z", **campos):
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


def test_exemplo_enunciado_13_dias_com_commits_desordenados():
    cmp = comparacao(commits=[commit("mais-novo", "2026-03-14T00:00:00Z"),
                             commit("mais-antigo", "2026-03-02T00:00:00Z"),
                             commit("intermediario", "2026-03-10T00:00:00Z")])
    original = deepcopy(cmp)
    resultado = lead_time.calcular_release(cmp)
    assert resultado["lead_time_horas"] == 312  # 15/03 - 02/03 = 13 dias.
    assert resultado["commit_mais_antigo_sha"] == "mais-antigo"
    assert resultado["commit_mais_antigo_author_date"] == "2026-03-02T00:00:00Z"
    assert resultado["commits_considerados"] == 3
    assert not resultado["ignorada"]
    assert cmp == original


def test_mediana_por_release_sem_ponderar_quantidade_de_commits():
    comparacoes = [comparacao(),
                   comparacao(2, [commit(str(i), "2026-03-14T00:00:00Z") for i in range(10)]),
                   comparacao(3, [commit("terceiro", "2026-03-13T00:00:00Z")])]
    resultado = lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)
    assert [r["lead_time_horas"] for r in resultado["releases"]] == [312, 24, 48]
    assert resultado["lead_time_horas"] == 48
    assert resultado["classe_lead_time"] == "High"
    assert resultado["releases_com_lead_time"] == 3


def test_mediana_numero_par_de_releases_sem_arredondar():
    comparacoes = [comparacao(), comparacao(2, [commit(data="2026-03-14T00:00:00Z")])]
    assert lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)["lead_time_horas"] == 168


def test_data_do_autor_e_usada_em_vez_de_committer():
    assert lead_time.calcular_release(comparacao())["lead_time_horas"] == 312


def test_release_sem_commits_novos_e_nula_e_ignorada_na_mediana():
    vazio = comparacao(2, [])
    resultado = lead_time.calcular_release(vazio)
    assert resultado["lead_time_horas"] is None
    assert resultado["ignorada"] and resultado["motivo"] == "sem_commits_novos"
    assert resultado["commits_considerados"] == 0
    repo_resultado = lead_time.calcular_repositorio(repo([vazio, comparacao()]), INICIO, FIM)
    assert repo_resultado["lead_time_horas"] == 312
    assert repo_resultado["releases_ignoradas_por_motivo"] == {"sem_commits_novos": 1}


def test_primeira_release_sem_anterior_e_nula_mesmo_se_houver_commits():
    resultado = lead_time.calcular_release(comparacao(release_anterior=None))
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == "sem_release_anterior"
    assert not resultado["coleta_incompleta"]


def test_primeira_release_na_janela_com_anterior_e_commits_fora_dela():
    resultado = lead_time.calcular_release(comparacao(publicada=JANELA["inicio"],
                                                     commits=[commit(data="2025-09-28T00:00:00Z")]))
    assert resultado["lead_time_horas"] == 72
    assert not resultado["ignorada"]


@pytest.mark.parametrize("motivo", ["sem_release_anterior", "compare_inacessivel", "historico_releases_inacessivel", "compare_incompleto", None])
def test_comparacoes_ignoradas_na_coleta_nao_produzem_metrica(motivo):
    resultado = lead_time.calcular_release(comparacao(ignorada=True, motivo=motivo, detalhe="HTTP 404"))
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == (motivo or "compare_ignorado")
    assert resultado["detalhe"] == "HTTP 404"


def test_coleta_incompleta_nao_calcula_com_minimo_parcial():
    resultado = lead_time.calcular_release(comparacao(coleta_incompleta=True))
    assert resultado["motivo"] == "compare_incompleto"
    assert resultado["lead_time_horas"] is None


@pytest.mark.parametrize("campo", ["total_commits_api", "total_commits_coletados"])
def test_totais_divergentes_detectam_compare_incompleto(campo):
    resultado = lead_time.calcular_release(comparacao(**{campo: 2}))
    assert resultado["motivo"] == "compare_incompleto"
    assert resultado["coleta_incompleta"]


def test_commits_duplicados_por_sha_contados_uma_vez():
    cmp = comparacao(commits=[commit(), commit()])
    resultado = lead_time.calcular_release(cmp)
    assert resultado["lead_time_horas"] == 312
    assert resultado["commits_considerados"] == 1


@pytest.mark.parametrize("sha", [None, "", 42])
def test_commit_sem_sha_registra_motivo(sha):
    resultado = lead_time.calcular_release(comparacao(commits=[commit(sha=sha)]))
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == "commit_sem_sha"


@pytest.mark.parametrize("data", [None, "inválida", "2026-03-02T00:00:00", 42])
def test_data_invalida_de_um_commit_invalida_a_release_inteira(data):
    resultado = lead_time.calcular_release(comparacao(commits=[commit(), commit("bad", data)]))
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == "data_commit_invalida"


@pytest.mark.parametrize("corpo", [{}, {"commit": {}}, {"commit": {"author": None}}])
def test_data_ausente_nao_faz_fallback_para_committer(corpo):
    resultado = lead_time.calcular_release(comparacao(commits=[{"sha": "abc", **corpo}]))
    assert resultado["motivo"] == "data_commit_invalida"


def test_fusos_horarios_e_fracoes_de_hora():
    resultado = lead_time.calcular_release(comparacao(publicada="2026-03-15T00:00:00Z",
                                                     commits=[commit(data="2026-03-14T20:47:30-03:00")]))
    assert resultado["lead_time_horas"] == pytest.approx(12.5 / 60)
    assert resultado["commit_mais_antigo_author_date"] == "2026-03-14T23:47:30Z"


def test_zero_real_e_valido_e_recebe_classe_elite():
    cmp = comparacao(commits=[commit(data="2026-03-15T00:00:00Z")])
    resultado = lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)
    assert resultado["lead_time_horas"] == 0
    assert resultado["classe_lead_time"] == "Elite"
    assert resultado["releases_com_lead_time"] == 1


def test_tempo_negativo_registrado_sem_forcar_zero():
    resultado = lead_time.calcular_release(comparacao(commits=[commit(data="2026-03-16T00:00:00Z")]))
    assert resultado["lead_time_horas"] is None
    assert resultado["motivo"] == "lead_time_negativo"
    assert resultado["commit_mais_antigo_sha"] == "abc"


@pytest.mark.parametrize("publicada", [None, "inválida", "2026-03-15T00:00:00"])
def test_publicacao_invalida_no_calculo_da_release(publicada):
    assert lead_time.calcular_release(comparacao(publicada=publicada))["motivo"] == "data_release_invalida"
    with pytest.raises(ConfigError, match="published_at inválido"):
        lead_time.calcular_repositorio(repo([comparacao(publicada=publicada)]), INICIO, FIM)


def test_recorte_janela_deduplicacao_e_ordenacao_sem_mutar_entrada():
    comparacoes = [comparacao(2, publicada="2026-09-30T23:59:59.999999Z"),
                   comparacao(1, publicada="2025-09-30T21:00:00-03:00", commits=[commit(data="2025-09-30T00:00:00Z")]),
                   comparacao(3, publicada="2025-09-30T23:59:59Z"), comparacao(4, publicada="2026-10-01T00:00:00Z"),
                   comparacao(2)]
    original = deepcopy(comparacoes)
    resultado = lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)
    assert resultado["total_releases"] == 2
    assert resultado["releases_fora_janela"] == 2
    assert resultado["releases_duplicadas"] == 1
    assert [r["release"]["id"] for r in resultado["releases"]] == [1, 2]
    assert comparacoes == original


def test_release_sem_id_recusada():
    cmp = comparacao()
    cmp["release"].pop("id")
    with pytest.raises(ConfigError, match="Release sem ID"):
        lead_time.calcular_repositorio(repo([cmp]), INICIO, FIM)


@pytest.mark.parametrize("comparacoes", [[], [comparacao(commits=[])], [comparacao(release_anterior=None)]])
def test_sem_releases_calculaveis_mediana_e_classe_nulas(comparacoes):
    resultado = lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)
    assert resultado["lead_time_horas"] is None
    assert resultado["classe_lead_time"] is None
    assert resultado["releases_com_lead_time"] == 0


def test_releases_completas_podem_ter_mediana_em_repositorio_parcial_com_alerta(caplog):
    comparacoes = [comparacao(), comparacao(2, ignorada=True, motivo="compare_inacessivel", coleta_incompleta=True)]
    resultado = lead_time.calcular_repositorio(repo(comparacoes), INICIO, FIM)
    assert resultado["lead_time_horas"] == 312
    assert resultado["coleta_incompleta"]
    assert "1/2 releases; 1 ignoradas" in caplog.text
    assert lead_time.calcular_repositorio(repo(coleta_incompleta=True), INICIO, FIM)["coleta_incompleta"]


def test_compatibilidade_com_saida_real_da_coleta_compare():
    anterior = {"id": 1, "tag_name": "v1", "draft": False, "prerelease": False, "published_at": "2025-09-30T00:00:00Z"}
    atual = {**anterior, "id": 2, "tag_name": "v2", "published_at": "2025-10-01T00:00:00Z"}

    class Cliente:
        def get_resposta(self, path, params):
            resposta = requests.Response()
            resposta.status_code = 200
            if path.endswith("/releases"):
                corpo = [atual, anterior]
            else:
                assert path.endswith("/compare/v1...v2")
                corpo = {"status": "ahead", "total_commits": 1, "commits": [commit(data="2025-09-28T00:00:00Z")]}
            resposta._content = json.dumps(corpo).encode()
            return resposta

    coletado = compare.coletar_repositorio(Cliente(), {**repo(), "releases": [atual]}, INICIO, FIM)
    resultado = lead_time.calcular_repositorio(coletado, INICIO, FIM)
    assert resultado["lead_time_horas"] == 72
    assert resultado["releases_ignoradas"] == 0


def test_consolidado_metricas_contagens_e_entrada_preservada(config):
    entrada = gravar_entrada(config, [repo(), repo([comparacao(commits=[])], id=11, full_name="org/sem-commits"),
                                    repo(coleta_incompleta=True, id=12, full_name="org/parcial")])
    original = entrada.read_bytes()
    caminho, lista = lead_time.executar(config)
    dados = json.loads(caminho.read_text())
    assert caminho == Path(config["caminhos"]["processed"]) / "lead_time_release.json"
    assert dados["origem"] == str(entrada)
    assert dados["variante"] == "a" and dados["unidade"] == "horas"
    assert dados["janela"] == JANELA and dados["definicao_deploy"] == "release_estavel"
    assert dados["total_repositorios"] == dados["total_releases"] == 3
    assert dados["repositorios_com_lead_time"] == dados["releases_com_lead_time"] == 2
    assert dados["releases_ignoradas"] == dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["repositorios"] == lista and lista[1]["lead_time_horas"] is None
    assert entrada.read_bytes() == original


def test_consolidado_vazio(config):
    gravar_entrada(config, [])
    caminho, lista = lead_time.executar(config)
    assert lista == []
    assert json.loads(caminho.read_text())["total_releases"] == 0


@pytest.mark.parametrize("janela", [None, {}, {**JANELA, "inicio": "2024-10-01T00:00:00Z"}])
def test_janela_da_entrada_deve_corresponder_a_configuracao(config, janela):
    gravar_entrada(config, janela=janela)
    with pytest.raises(ConfigError, match="janela do compare"):
        lead_time.executar(config)


@pytest.mark.parametrize("definicao", [None, "tag", "release_com_prerelease"])
def test_definicao_de_deploy_incompativel_recusada(config, definicao):
    gravar_entrada(config, definicao_deploy=definicao)
    with pytest.raises(ConfigError, match="definicao_deploy=release_estavel"):
        lead_time.executar(config)


def test_arquivo_compare_ausente(config):
    with pytest.raises(FileNotFoundError, match="execute antes a etapa compare"):
        lead_time.executar(config)


def test_saida_nao_pode_sobrescrever_entrada(config):
    entrada = gravar_entrada(config)
    original = entrada.read_bytes()
    with pytest.raises(ConfigError, match="saída de lead time deve ser diferente"):
        lead_time.executar(config, entrada, entrada.parent / "." / entrada.name)
    assert entrada.read_bytes() == original


def test_cli_piloto_sem_token_ou_rede(config, tmp_path, monkeypatch, capsys):
    entrada = gravar_entrada(config, caminho=tmp_path / "raw" / "piloto-100" / "compare.json")
    saida = tmp_path / "processed" / "piloto-100" / "lead_time_release.json"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(requests.Session, "request", lambda *args, **kwargs: pytest.fail("cálculo não deve acessar rede"))
    assert lead_time.main(["--config", gravar_config(config, tmp_path), "--entrada", str(entrada), "--saida", str(saida)]) == 0
    assert "Lead time (RQ02a): 1/1 repositórios com métrica" in capsys.readouterr().out
    assert json.loads(saida.read_text())["repositorios"][0]["lead_time_horas"] == 312


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
    monkeypatch.setattr(sys, "argv", ["pipeline.lead_time_release", "--config", gravar_config(config, tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(lead_time.__file__, run_name="__main__")
    assert exc.value.code == 0
