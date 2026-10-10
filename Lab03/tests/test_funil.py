import datetime as dt
import json
import runpy
import sys
from pathlib import Path

import pytest
import requests
import yaml

from pipeline import funil
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
INCLUSAO = {"min_releases": 5, "min_runs_validos": 50}


def runs(n, conclusion="success", inicio_id=1):
    return [{"id": inicio_id + i, "conclusion": conclusion, "head_branch": "main", "event": "push",
             "created_at": "2026-03-10T12:00:00Z"} for i in range(n)]


def releases(n, inicio_id=1, **campos):
    return [{"id": inicio_id + i, "tag_name": f"v{inicio_id + i}", "draft": False, "prerelease": False,
             "published_at": "2026-02-01T00:00:00Z", **campos} for i in range(n)]


def repo(id):
    return {"id": id, "full_name": f"org/repo{id}"}


def descarte(id, motivo, detalhe="HTTP 404"):
    return {**repo(id), "motivo": motivo, "detalhe": detalhe}


def coleta():
    """Fixture de uma execução completa com descartes em todas as etapas.

    1 a 3: incluídos (3 no limite exato: 5 releases e 50 runs válidos).
    4: sem Actions; 5: inacessível em metadados; 6: inacessível nos runs;
    7: inacessível nas releases; 8: poucas releases; 9: poucos runs válidos;
    10: poucas releases e poucos runs.
    """
    rel = {i: releases(8) for i in (1, 2)}
    rel.update({3: releases(5), 8: releases(4), 9: releases(6), 10: releases(1)})
    rns = {i: runs(60) for i in (1, 2, 8)}
    rns.update({3: runs(30) + runs(20, "failure", 100) + runs(5, "cancelled", 200),
                9: runs(49), 10: runs(3)})
    finais = (1, 2, 3, 8, 9, 10)
    return {
        "candidatos": {"candidatos": [repo(i) for i in range(1, 11)]},
        "actions": {"repositorios": [repo(i) for i in range(1, 11) if i != 4],
                    "descartes": [descarte(4, "sem_github_actions", "nenhum workflow")]},
        "metadados": {"repositorios": [{**repo(i), "default_branch": "main"} for i in range(1, 11) if i not in (4, 5)],
                      "descartes": [descarte(5, "repositorio_inacessivel")]},
        "workflow_runs": {"janela": JANELA, "descartes": [descarte(6, "repositorio_inacessivel")],
                          "repositorios": [{**repo(i), "default_branch": "main", "coleta_incompleta": False,
                                            "meses": [], "workflow_runs": rns.get(i, runs(60))}
                                           for i in (1, 2, 3, 7, 8, 9, 10)]},
        "releases": {"janela": JANELA, "descartes": [descarte(7, "repositorio_inacessivel")],
                     "repositorios": [{**repo(i), "releases": rel[i]} for i in finais]},
    }


@pytest.fixture
def config(tmp_path):
    return {"api": {"base_url": "https://api.github.com"},
            "janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "inclusao": dict(INCLUSAO),
            "runs": {"evento": "push", "somente_default_branch": True,
                     "conclusoes_sucesso": ["success"],
                     "conclusoes_falha": ["failure", "timed_out", "startup_failure"]},
            "caminhos": {"raw": str(tmp_path / "raw"), "processed": str(tmp_path / "processed"),
                         "cache": str(tmp_path / "cache")}}


def gravar_coleta(pasta, dados=None):
    dados = coleta() if dados is None else dados
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, _, arquivo, _ in funil.ETAPAS:
        (pasta / arquivo).write_text(json.dumps(dados[nome]), encoding="utf-8")
    return pasta


def gravar_config(config, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(caminho)


@pytest.mark.parametrize("n_releases,n_runs,motivo", [
    (5, 50, None), (100, 1000, None),
    (4, 50, funil.MOTIVO_RELEASES), (5, 49, funil.MOTIVO_RUNS), (0, 0, funil.MOTIVO_AMBOS),
])
def test_motivo_exclusao_nos_limites(n_releases, n_runs, motivo):
    assert funil.motivo_exclusao(n_releases, n_runs, INCLUSAO) == motivo


def test_conta_releases_publicadas_sem_drafts_fora_da_janela_e_duplicadas():
    repo_releases = {"full_name": "org/r", "releases": [
        *releases(3),
        {"id": 10, "tag_name": "v10", "draft": True, "published_at": None},
        {"id": 11, "tag_name": "v11", "published_at": "2026-01-01T00:00:00Z"},
        {"id": 12, "tag_name": "v12", "draft": False, "published_at": "2025-09-30T23:59:59Z"},
        {"id": 13, "tag_name": "v13", "draft": False, "published_at": "2026-10-01T00:00:00Z"},
        {"id": 14, "tag_name": "v14", "draft": False, "published_at": "2025-10-01T00:00:00Z"},
        {"id": 1, "tag_name": "v1", "draft": False, "published_at": "2026-02-01T00:00:00Z"},
        {"tag_name": "sem-id", "draft": False, "published_at": "2026-09-30T23:59:59-00:00"},
    ]}
    assert funil.contar_releases(repo_releases, INICIO, FIM) == {
        "releases_publicadas": 5, "releases_draft": 2, "releases_fora_janela": 2, "releases_duplicadas": 1}


def test_prerelease_conta_como_release_publicada():
    repo_releases = {"full_name": "org/r", "releases": releases(5, prerelease=True)}
    assert funil.contar_releases(repo_releases, INICIO, FIM)["releases_publicadas"] == 5


def test_repositorio_sem_releases():
    assert funil.contar_releases({"full_name": "org/r"}, INICIO, FIM)["releases_publicadas"] == 0


@pytest.mark.parametrize("data", [None, "ontem", "2026-02-01T00:00:00"])
def test_published_at_invalido_nao_e_ignorado(data):
    with pytest.raises(ConfigError, match="published_at"):
        funil.contar_releases({"full_name": "org/r", "releases": [
            {"id": 1, "draft": False, "published_at": data}]}, INICIO, FIM)


def test_release_sem_id_e_sem_tag():
    with pytest.raises(ConfigError, match="tag_name"):
        funil.contar_releases({"full_name": "org/r", "releases": [
            {"draft": False, "published_at": "2026-02-01T00:00:00Z"}]}, INICIO, FIM)


def test_funil_completo_quantidades_por_etapa_e_motivos(config):
    resultado = funil.montar_funil(coleta(), config)
    resumo = [(e["etapa"], e["entrada"], e["descartados"], e["restantes"], e["motivos"])
              for e in resultado["etapas"]]
    assert resumo == [
        ("candidatos", 10, 0, 10, {}),
        ("actions", 10, 1, 9, {"sem_github_actions": 1}),
        ("metadados", 9, 1, 8, {"repositorio_inacessivel": 1}),
        ("workflow_runs", 8, 1, 7, {"repositorio_inacessivel": 1}),
        ("releases", 7, 1, 6, {"repositorio_inacessivel": 1}),
        ("inclusao", 6, 3, 3, {funil.MOTIVO_AMBOS: 1, funil.MOTIVO_RELEASES: 1, funil.MOTIVO_RUNS: 1}),
    ]
    assert [r["full_name"] for r in resultado["amostra"]] == ["org/repo1", "org/repo2", "org/repo3"]
    assert resultado["total_amostra"] == 3
    assert resultado["criterio"] == INCLUSAO
    por_id = {d["id"]: (d["etapa"], d["motivo"]) for d in resultado["descartes"]}
    assert por_id == {4: ("actions", "sem_github_actions"), 5: ("metadados", "repositorio_inacessivel"),
                      6: ("workflow_runs", "repositorio_inacessivel"),
                      7: ("releases", "repositorio_inacessivel"),
                      8: ("inclusao", funil.MOTIVO_RELEASES), 9: ("inclusao", funil.MOTIVO_RUNS),
                      10: ("inclusao", funil.MOTIVO_AMBOS)}


def test_cada_etapa_soma_restantes_e_descartados(config):
    etapas = funil.montar_funil(coleta(), config)["etapas"]
    for anterior, atual in zip(etapas, etapas[1:]):
        assert atual["entrada"] == anterior["restantes"]
        assert atual["entrada"] == atual["descartados"] + atual["restantes"]
        assert sum(atual["motivos"].values()) == atual["descartados"]


def test_incluido_no_limite_conta_apenas_runs_validos(config):
    amostra = {r["id"]: r for r in funil.montar_funil(coleta(), config)["amostra"]}
    assert amostra[3]["releases_publicadas"] == 5
    assert amostra[3]["runs_validos"] == 50  # os 5 cancelled não contam
    assert amostra[3]["coleta_runs_incompleta"] is False


def test_detalhe_do_descarte_por_criterio(config):
    descartes = {d["id"]: d for d in funil.montar_funil(coleta(), config)["descartes"]}
    assert descartes[9]["detalhe"] == "6 releases (mínimo 5), 49 runs válidos (mínimo 50)"


def test_runs_fora_do_recorte_e_drafts_nao_salvam_repositorio(config):
    dados = coleta()
    repo1 = dados["workflow_runs"]["repositorios"][0]
    repo1["workflow_runs"] = runs(49) + [{**r, "head_branch": "dev"} for r in runs(20, inicio_id=500)]
    dados["releases"]["repositorios"][1]["releases"] = releases(4) + releases(3, 50, draft=True)
    resultado = funil.montar_funil(dados, config)
    motivos = {d["id"]: d["motivo"] for d in resultado["descartes"] if d["etapa"] == "inclusao"}
    assert motivos[1] == funil.MOTIVO_RUNS
    assert motivos[2] == funil.MOTIVO_RELEASES


def test_criterio_vem_da_configuracao(config):
    config["inclusao"] = {"min_releases": 1, "min_runs_validos": 1}
    assert funil.montar_funil(coleta(), config)["total_amostra"] == 6


def test_coleta_de_runs_incompleta_e_mantida_na_amostra(config):
    dados = coleta()
    dados["workflow_runs"]["repositorios"][0]["coleta_incompleta"] = True
    amostra = funil.montar_funil(dados, config)["amostra"]
    assert amostra[0]["coleta_runs_incompleta"] is True


def test_candidatos_duplicados_contam_uma_vez(config):
    dados = coleta()
    dados["candidatos"]["candidatos"].append(repo(1))
    assert funil.montar_funil(dados, config)["etapas"][0]["entrada"] == 10


def test_repositorios_ja_descartados_sao_ignorados_nas_etapas_seguintes(config):
    dados = coleta()
    dados["releases"]["repositorios"].append({**repo(4), "releases": releases(10)})
    assert funil.montar_funil(dados, config)["etapas"][-2]["entrada"] == 7


def test_repositorio_ausente_em_uma_etapa(config):
    dados = coleta()
    dados["releases"]["repositorios"].pop(0)
    with pytest.raises(ConfigError, match="etapa releases"):
        funil.montar_funil(dados, config)


def test_repositorio_aprovado_e_descartado(config):
    dados = coleta()
    dados["actions"]["descartes"].append(descarte(1, "sem_github_actions"))
    with pytest.raises(ConfigError, match="aprovado e descartado"):
        funil.montar_funil(dados, config)


@pytest.mark.parametrize("etapa", ["workflow_runs", "releases"])
def test_janela_das_coletas_deve_corresponder_a_configuracao(config, etapa):
    dados = coleta()
    dados[etapa]["janela"] = {"inicio": "2025-01-01T00:00:00Z", "fim_exclusivo": "2026-01-01T00:00:00Z"}
    with pytest.raises(ConfigError, match=etapa):
        funil.montar_funil(dados, config)


def test_tabela_markdown(config):
    tabela = funil.tabela_markdown(funil.montar_funil(coleta(), config))
    assert "| Etapa | Entrada | Descartados | Restantes | Motivos de descarte |" in tabela
    assert "| Busca na Search API | 10 | 0 | 10 | — |" in tabela
    assert "| Usa GitHub Actions | 10 | 1 | 9 | `sem_github_actions`: 1 |" in tabela
    assert ("| Critério mínimo de inclusão | 6 | 3 | 3 | `releases_e_runs_insuficientes`: 1; "
            "`releases_insuficientes`: 1; `runs_validos_insuficientes`: 1 |") in tabela
    assert "Amostra final: **3** repositórios." in tabela
    assert "5 releases publicadas e 50 runs válidos" in tabela


def test_executar_grava_json_e_tabela(config):
    gravar_coleta(config["caminhos"]["raw"])
    caminho, tabela, resultado = funil.executar(config)
    assert caminho == Path(config["caminhos"]["processed"]) / "funil.json"
    salvo = json.loads(caminho.read_text(encoding="utf-8"))
    assert salvo["total_amostra"] == 3
    assert salvo["origem"] == config["caminhos"]["raw"]
    assert len(salvo["descartes"]) == 7
    assert tabela.read_text(encoding="utf-8") == funil.tabela_markdown(resultado)


def test_executar_alerta_coleta_incompleta_na_amostra(config, caplog):
    dados = coleta()
    dados["workflow_runs"]["repositorios"][0]["coleta_incompleta"] = True
    gravar_coleta(config["caminhos"]["raw"], dados)
    funil.executar(config)
    assert "1 repositórios da amostra têm coleta de runs incompleta" in caplog.text


@pytest.mark.parametrize("arquivo,mensagem", [("releases.json", "S01-10"), ("actions.json", "etapa actions")])
def test_arquivo_ausente(config, arquivo, mensagem):
    pasta = gravar_coleta(config["caminhos"]["raw"])
    (pasta / arquivo).unlink()
    with pytest.raises(FileNotFoundError, match=mensagem):
        funil.executar(config)


def test_saida_nao_pode_ser_a_pasta_raw(config):
    gravar_coleta(config["caminhos"]["raw"])
    with pytest.raises(ConfigError, match="diferente"):
        funil.executar(config, saida=config["caminhos"]["raw"])


def test_cli_piloto_sem_token_sem_rede(config, tmp_path, monkeypatch, capsys):
    raw = gravar_coleta(tmp_path / "raw" / "piloto-100")
    saida = tmp_path / "processed" / "piloto-100"
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    def rede_proibida(*args, **kwargs):
        pytest.fail("o funil não deve acessar a rede")
    monkeypatch.setattr(requests.Session, "request", rede_proibida)
    codigo = funil.main(["--config", gravar_config(config, tmp_path), "--raw", str(raw), "--saida", str(saida)])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "| Critério mínimo de inclusão | 6 | 3 | 3 |" in out
    assert "Funil: 10 candidatos -> 3 na amostra" in out
    assert (saida / "funil.json").is_file() and (saida / "funil.md").is_file()


@pytest.mark.parametrize("erro", ["arquivo_ausente", "config_ausente", "json_invalido", "janela_invalida"])
def test_cli_reporta_erros_com_codigo_dois(config, tmp_path, capsys, erro):
    caminho_config = gravar_config(config, tmp_path)
    pasta = gravar_coleta(config["caminhos"]["raw"])
    if erro == "arquivo_ausente":
        (pasta / "releases.json").unlink()
    elif erro == "config_ausente":
        caminho_config = str(tmp_path / "inexistente.yaml")
    elif erro == "json_invalido":
        (pasta / "metadados.json").write_text("{parcial", encoding="utf-8")
    else:
        dados = coleta()
        dados["releases"]["janela"] = {}
        gravar_coleta(pasta, dados)
    assert funil.main(["--config", caminho_config]) == 2
    assert "erro:" in capsys.readouterr().err


def test_entrypoint_executa_cli(config, tmp_path, monkeypatch):
    gravar_coleta(config["caminhos"]["raw"])
    monkeypatch.setattr(sys, "argv", ["pipeline.funil", "--config", gravar_config(config, tmp_path)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(funil.__file__, run_name="__main__")
    assert exc.value.code == 0
