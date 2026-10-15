import copy
import datetime as dt
import json
import runpy
import sys
from pathlib import Path

import pytest
import yaml

from pipeline import cfr_b, compare, metricas
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, load_config

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def release(id=1, tag="v2.3.0", data="2026-05-10T00:00:00Z", **campos):
    return {"id": id, "tag_name": tag, "published_at": data,
            "draft": False, "prerelease": False, **campos}


def repo(releases, **campos):
    return {"id": 10, "full_name": "org/projeto", "releases": releases, **campos}


def comparacao(atual, anterior, mensagens=("feat: recurso",), **campos):
    commits = [{"sha": str(i), "commit": {"message": m}} for i, m in enumerate(mensagens)]
    return {"release": atual, "release_anterior": anterior,
            "commits": commits, "total_commits_api": len(commits),
            "total_commits_coletados": len(commits), "ignorada": False,
            "coleta_incompleta": False, **campos}


def compare_repo(releases, **campos):
    return {"id": 10, "full_name": "org/projeto", "comparacoes": [
        comparacao(r, releases[i-1]) if i else comparacao(
            r, None, (), ignorada=True, motivo="sem_release_anterior")
        for i, r in enumerate(releases)], **campos}


@pytest.mark.parametrize("anterior,atual,esperado", [
    ("v2.3.0", "v2.3.1", True), ("2.3.1", "2.3.5", True),
    ("v0.0.0", "0.0.1+build.1", True), ("1.0.1+a", "v1.0.2+b", True),
    ("v2.3.1", "v2.3.1+build", False), ("v2.3.1", "v2.3.0", False),
    ("v2.3.0", "v2.4.1", False), ("v2.3.0", "v3.3.1", False),
    ("v2.3.0", "v2.3.1-rc.1", False), ("v02.3.0", "v2.3.1", False),
    ("v2.3.0", "v2.3.01", False), ("release/2.3.0", "release/2.3.1", False),
    ("1.2.3", "1.2.4+", False), ("1.2.3", "1.2.4+build..1", False),
    ("1.2.3", "1.2.4\n", False), ("1.2.3", None, False), (None, "v2.3.1", None),
])
def test_patch_semver(anterior, atual, esperado):
    assert cfr_b.patch_semver(anterior, atual) is esperado


@pytest.mark.parametrize("mensagem", ["fix: crash ao abrir arquivo", "FIX(parser)!: crash",
                                      'Revert "feat: mudança"', "chore: hotfix de regressao",
                                      "feat: recurso\n\nfix: falha adicional"])
def test_mensagem_identifica_corretiva_sem_patch(mensagem):
    anterior, atual = release(), release(2, "v2.4.0")
    c = comparacao(atual, anterior, (mensagem,))
    resultado = cfr_b.identificar_corretiva(atual, anterior, c)
    assert resultado["corretiva"] is True
    assert resultado["patch_semver"] is False
    assert resultado["commits_corretivos"][0]["sha"] == "0"


@pytest.mark.parametrize("mensagem", ["feat: prefix matching", "docs: fixture", "feat: postfix",
                                      "refactor: fixed path", "chore: hotfixes", "feat: fix_parser"])
def test_substrings_nao_sao_termos_corretivos(mensagem):
    base, atual = release(), release(2, "v2.4.0")
    assert cfr_b.identificar_corretiva(atual, base, comparacao(atual, base, (mensagem,)))["corretiva"] is False


def test_exemplos_enunciado_v230_falha_v240_nao_falha():
    releases = [release(), release(2, "v2.3.1", "2026-05-12T00:00:00Z"),
                release(3, "v2.4.0", "2026-06-01T00:00:00Z"),
                release(4, "v2.5.0", "2026-06-20T00:00:00Z")]
    comparacoes = compare_repo(releases)
    comparacoes["comparacoes"][1] = comparacao(releases[1], releases[0], ("fix: crash ao abrir arquivo",))
    original = copy.deepcopy((releases, comparacoes))
    resultado = cfr_b.calcular_repositorio(repo(releases), INICIO, FIM, comparacoes)
    assert [r["falhou"] for r in resultado["releases"]] == [True, False, False, False]
    assert resultado["releases"][1]["motivo_corretiva"] == "patch_e_mensagem"
    assert resultado["releases_falhas"] == 1 and resultado["releases_avaliadas"] == 4
    assert resultado["change_failure_rate"] == 0.25 and resultado["classe_cfr"] == "High"
    assert not resultado["calculo_parcial"]
    assert (releases, comparacoes) == original


@pytest.mark.parametrize("intervalo,falhou", [(dt.timedelta(days=7), True),
                                             (dt.timedelta(days=7, seconds=1), False),
                                             (dt.timedelta(0), False)])
def test_limite_temporal_exato_e_publicacao_simultanea(intervalo, falhou):
    data = dt.datetime(2026, 5, 10, tzinfo=dt.timezone.utc)
    releases = [release(), release(2, "v2.3.1", (data+intervalo).isoformat())]
    resultado = cfr_b.calcular_repositorio(repo(releases), INICIO, FIM)
    assert resultado["releases"][0]["falhou"] is falhou


def test_considera_corretiva_nao_imediata_sem_contar_falha_duas_vezes():
    releases = [release(), release(2, "v2.4.0", "2026-05-11T00:00:00Z"),
                release(3, "v2.4.1", "2026-05-12T00:00:00Z"),
                release(4, "v2.4.2", "2026-05-13T00:00:00Z")]
    resultado = cfr_b.calcular_repositorio(repo(releases), INICIO, FIM)
    assert resultado["releases"][0]["releases_corretivas_posteriores"] == [3, 4]
    assert resultado["releases_falhas"] == 3 and resultado["change_failure_rate"] == 3/4


def test_censura_comeca_no_limite_inclusive_e_corretiva_censurada_pode_ser_evidencia():
    releases = [release(1, "v2.3.0", "2026-09-23T23:59:59Z"),
                release(2, "v2.3.1", "2026-09-24T00:00:00Z"),
                release(3, "v2.3.2", "2026-09-30T23:59:59Z")]
    resultado = cfr_b.calcular_repositorio(repo(releases), INICIO, FIM)
    assert [r["falhou"] for r in resultado["releases"]] == [True, None, None]
    assert resultado["releases_censuradas"] == 2 and resultado["releases_avaliadas"] == 1
    assert resultado["change_failure_rate"] == 1


def test_sem_denominador_nulo_e_nao_zero():
    resultado = cfr_b.calcular_repositorio(repo([release(data="2026-09-30T00:00:00Z")]), INICIO, FIM)
    assert resultado["releases_censuradas"] == 1
    assert resultado["change_failure_rate"] is resultado["classe_cfr"] is None
    assert cfr_b.calcular_repositorio(repo([]), INICIO, FIM)["change_failure_rate"] is None


def test_compare_ausente_nao_equivale_a_nao_corretiva():
    releases = [release(1, "v1.0.0", "2026-09-23T00:00:00Z"),
                release(2, "v2.0.0", "2026-09-25T00:00:00Z")]
    resultado = cfr_b.calcular_repositorio(repo(releases), INICIO, FIM)
    assert resultado["releases"][1]["corretiva"] is None
    assert resultado["releases"][0]["falhou"] is None
    assert resultado["releases_indeterminadas"] == 1
    assert resultado["coleta_incompleta"] and resultado["calculo_parcial"]
    assert resultado["change_failure_rate"] is None


@pytest.mark.parametrize("campos", [{"ignorada": True, "motivo": "compare_inacessivel"},
                                    {"coleta_incompleta": True}, {"total_commits_api": 2},
                                    {"total_commits_coletados": 2},
                                    {"commits": [{"sha": "a", "commit": {"message": None}}]},
                                    {"commits": [{"sha": "a", "commit": None}]},
                                    {"commits": [{"sha": "a", "commit": {"message": ""}}]},
                                    {"commits": [{"commit": {"message": "feat: recurso"}}]}])
def test_negativo_exige_compare_completo_e_mensagens_validas(campos):
    base, atual = release(), release(2, "v2.4.0")
    assert cfr_b.identificar_corretiva(atual, base, comparacao(atual, base, **campos))["corretiva"] is None


def test_commit_positivo_em_compare_parcial_e_patch_sem_compare_sao_evidencias():
    base, atual = release(), release(2, "v2.4.0")
    c = comparacao(atual, base, ("hotfix: crash",), coleta_incompleta=True, total_commits_api=300)
    assert cfr_b.identificar_corretiva(atual, base, c)["corretiva"] is True
    assert cfr_b.identificar_corretiva(release(2, "v2.3.1"), base)["corretiva"] is True
    assert cfr_b.identificar_corretiva(atual, base, comparacao(atual, base, ()))["corretiva"] is False


def test_base_historica_e_historico_inacessivel():
    releases = [release(), release(2, "v2.3.1", "2026-05-12T00:00:00Z")]
    c = compare_repo(releases)
    c["comparacoes"][0] = comparacao(releases[0], release(0, "v2.2.0", "2025-09-30T00:00:00Z"))
    assert cfr_b.calcular_repositorio(repo(releases), INICIO, FIM, c)["releases"][0]["corretiva"] is False
    c["comparacoes"] = [comparacao(r, None, (), ignorada=True, motivo="historico_releases_inacessivel") for r in releases]
    assert cfr_b.calcular_repositorio(repo(releases), INICIO, FIM, c)["releases"][0]["falhou"] is True


def test_fonte_releases_incompleta_nao_produz_negativos():
    releases = [release(), release(2, "v2.3.1", "2026-05-12T00:00:00Z")]
    resultado = cfr_b.calcular_repositorio(repo(releases, coleta_incompleta=True), INICIO, FIM)
    assert resultado["releases"][0]["falhou"] is True
    assert resultado["releases"][1]["falhou"] is None
    assert resultado["calculo_parcial"] and resultado["releases_indeterminadas"] == 1


def test_recorte_ordem_deduplicacao_e_fuso_horario():
    releases = [release(1, "v1.0.0", "2025-09-30T21:00:00-03:00"),
                release(2, "v1.0.1", "2025-10-02T00:00:00Z")]
    dados = releases[::-1] + [releases[0], release(3, draft=True), release(4, prerelease=True),
                             release(5, data="2026-10-01T00:00:00Z"),
                             release(6, data="2025-09-30T23:59:59Z")]
    resultado = cfr_b.calcular_repositorio(repo(dados), INICIO, FIM)
    assert resultado["total_releases"] == 2 and resultado["releases_duplicadas"] == 1
    assert resultado["releases_fora_recorte"] == 4
    assert resultado["releases"][0]["published_at"] == JANELA["inicio"]
    assert resultado["releases"][0]["falhou"] is True


@pytest.mark.parametrize("campo,valor", [("published_at", None), ("published_at", "errada"),
                                        ("published_at", "2026-05-10T00:00:00"), ("id", None)])
def test_metadados_essenciais_invalidos_recusados(campo, valor):
    with pytest.raises(ConfigError):
        cfr_b.calcular_repositorio(repo([release(**{campo: valor})]), INICIO, FIM)


def test_duplicata_divergente_recusada():
    with pytest.raises(ConfigError, match="duplicada divergente"):
        cfr_b.calcular_repositorio(repo([release(), release(tag="v3.0.0")]), INICIO, FIM)


@pytest.mark.parametrize("alteracao", ["nome", "id", "release", "data", "base", "historico", "duplicado", "extra"])
def test_compare_de_outra_identidade_ou_sequencia_e_recusado(alteracao):
    releases = [release(), release(2, "v2.4.0", "2026-05-12T00:00:00Z")]
    c = copy.deepcopy(compare_repo(releases))
    if alteracao == "nome": c["full_name"] = "org/outro"
    elif alteracao == "id": c["id"] = 99
    elif alteracao == "release": c["comparacoes"][0]["release"]["tag_name"] = "outra"
    elif alteracao == "data": c["comparacoes"][0]["release"]["published_at"] = "2026-05-11T00:00:00Z"
    elif alteracao == "base": c["comparacoes"][1]["release_anterior"] = None
    elif alteracao == "historico": c["comparacoes"][0]["release_anterior"] = release(0)
    elif alteracao == "duplicado": c["comparacoes"] *= 2
    else: c["comparacoes"].append(comparacao(release(99), None))
    with pytest.raises(ConfigError):
        cfr_b.calcular_repositorio(repo(releases), INICIO, FIM, c)


@pytest.fixture
def config(tmp_path):
    cfg = load_config(Path(__file__).resolve().parents[1] / "config.yaml")
    cfg["caminhos"] = {k: str(tmp_path/k) for k in ("raw", "processed", "cache")}
    return cfg


def gravar_entradas(config):
    raw = Path(config["caminhos"]["raw"])
    releases = [release(), release(2, "v2.3.1", "2026-05-12T00:00:00Z")]
    gravar_json(raw/"releases.json", {"janela": JANELA, "repositorios": [repo(releases)]})
    c = compare_repo(releases)
    c.update(total_releases=2, total_comparacoes=1, total_releases_ignoradas=1,
             total_releases_ignoradas_404=0, comparacoes_acima_250=0, coleta_incompleta=False)
    compare.gravar_consolidado(config, [c], INICIO, FIM)
    return raw


def test_arquivos_reais_do_coletor_e_consolidacao_sem_rede(config, monkeypatch):
    raw = gravar_entradas(config)
    originais = {p: p.read_bytes() for p in raw.glob("*.json")}
    def sem_rede(*args, **kwargs): pytest.fail("CFR(b) deve ser offline")
    monkeypatch.setattr("requests.sessions.Session.request", sem_rede)
    saida, lista = cfr_b.executar(config)
    dados = json.loads(saida.read_text())
    assert dados["versao_heuristica"] == cfr_b.VERSAO_HEURISTICA
    assert dados["validacao_manual_pendente"] and dados["variante"] == "b"
    assert dados["repositorios_com_cfr"] == 1
    assert lista[0]["change_failure_rate"] == 0.5
    linhas = metricas.consolidar({"cfr_b": lista})
    assert linhas[0]["cfr_b"] == 0.5 and linhas[0]["classe_cfr_b"] == "Low"
    assert all(p.read_bytes() == b for p, b in originais.items())
    cfr_b.executar(config)
    assert json.loads(saida.read_text())["repositorios"] == dados["repositorios"]


def test_compare_opcional_ausente_nao_bloqueia_patch_e_filtro_de_amostra(config):
    raw = gravar_entradas(config)
    (raw/"compare.json").unlink()
    _, lista = cfr_b.executar(config, ids={10})
    assert lista[0]["change_failure_rate"] == 0.5 and lista[0]["coleta_incompleta"]
    assert cfr_b.executar(config, ids=set())[1] == []
    with pytest.raises(ConfigError, match="selecionado ausente"):
        cfr_b.executar(config, ids={99})
    with pytest.raises(FileNotFoundError):
        cfr_b.executar(config, compares=raw/"inexistente.json")


@pytest.mark.parametrize("arquivo", ["releases.json", "compare.json"])
def test_janelas_divergentes_e_saida_sobre_entrada_recusadas(config, arquivo):
    raw = gravar_entradas(config)
    with pytest.raises(ConfigError, match="diferente"):
        cfr_b.executar(config, saida=raw/arquivo)
    dados = json.loads((raw/arquivo).read_text())
    dados["janela"]["inicio"] = "2025-01-01T00:00:00Z"
    gravar_json(raw/arquivo, dados)
    with pytest.raises(ConfigError, match="Janela divergente"):
        cfr_b.executar(config)


def test_contrato_compare_e_repos_duplicados(config):
    raw = gravar_entradas(config)
    dados = json.loads((raw/"compare.json").read_text())
    dados["definicao_deploy"] = "tag"
    gravar_json(raw/"compare.json", dados)
    with pytest.raises(ConfigError, match="release_estavel"):
        cfr_b.executar(config)
    dados["definicao_deploy"] = "release_estavel"
    dados["repositorios"] *= 2
    gravar_json(raw/"compare.json", dados)
    with pytest.raises(ConfigError, match="duplicado"):
        cfr_b.executar(config)


def test_amostra_elegivel_filtra_candidatos_e_preserva_entrada(config):
    raw = gravar_entradas(config)
    dados = json.loads((raw/"releases.json").read_text())
    dados["repositorios"].append(repo([], id=20, full_name="org/excluido"))
    gravar_json(raw/"releases.json", dados)
    amostra = raw/"amostra.json"
    gravar_json(amostra, {"janela": JANELA, "repositorios": [{"id": 10, "full_name": "Org/Projeto"}]})
    original = amostra.read_bytes()
    saida, lista = cfr_b.executar(config, amostra=amostra)
    assert [r["id"] for r in lista] == [10]
    assert amostra.read_bytes() == original
    assert json.loads(saida.read_text())["origens"]["amostra"] == str(amostra)
    with pytest.raises(ConfigError, match="diferente"):
        cfr_b.executar(config, amostra=amostra, saida=amostra)
    with pytest.raises(ConfigError, match="somente ids"):
        cfr_b.executar(config, amostra=amostra, ids={10})
    gravar_json(amostra, {"janela": JANELA, "repositorios": [{"id": 10, "full_name": "org/outro"}]})
    with pytest.raises(ConfigError, match="Identidade divergente"):
        cfr_b.executar(config, amostra=amostra)


def test_cli_sucesso_e_erros(config, tmp_path, capsys, monkeypatch):
    gravar_entradas(config)
    path = tmp_path/"config.yaml"
    path.write_text(yaml.safe_dump(config))
    args = ["--config", str(path)]
    assert cfr_b.main(args) == 0
    assert "1/1" in capsys.readouterr().out
    raw = Path(config["caminhos"]["raw"])
    assert cfr_b.main(args + ["--entrada", str(raw/"faltante.json")]) == 2
    assert "erro:" in capsys.readouterr().err
    (raw/"releases.json").write_text("nao json")
    assert cfr_b.main(args) == 2
    assert cfr_b.main(["--config", str(tmp_path/"config-inexistente")]) == 2
    gravar_entradas(config)
    # Exercita o ponto de entrada python -m, sem criar subprocesso ou conexão.
    monkeypatch.delitem(sys.modules, "pipeline.cfr_b", raising=False)
    monkeypatch.setattr(sys, "argv", ["pipeline.cfr_b", *args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("pipeline.cfr_b", run_name="__main__")
    assert exc.value.code == 0
