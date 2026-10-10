import csv
import datetime as dt
import json
import runpy
import sys
from pathlib import Path

import pytest
import yaml

from pipeline import amostra_ouro
from pipeline.config import ConfigError

INICIO = dt.datetime(2025, 10, 1, tzinfo=dt.timezone.utc)
FIM = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
JANELA = {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}


def release(id, dia=1, **campos):
    return {"id": id, "tag_name": f"v1.{id}.0", "name": f"Versão 1.{id}", "draft": False, "prerelease": False,
            "published_at": f"2026-01-{dia:02d}T12:00:00Z", **campos}


def repo(id, releases=None):
    return {"id": id, "full_name": f"org/repo{id}",
            "releases": [release(i, i) for i in range(1, 9)] if releases is None else releases}


def populacao(total=80):
    return [{"id": i, "full_name": f"org/repo{i}"} for i in range(1, total + 1)]


@pytest.fixture
def config(tmp_path):
    return {"api": {"base_url": "https://api.github.com"},
            "janela": {"inicio": dt.date(2025, 10, 1), "fim": dt.date(2026, 9, 30)},
            "inclusao": {"min_releases": 5, "min_runs_validos": 50, "incluir_prereleases": False},
            "runs": {"evento": "push", "somente_default_branch": True,
                     "conclusoes_sucesso": ["success"],
                     "conclusoes_falha": ["failure", "timed_out", "startup_failure"]},
            "caminhos": {"raw": str(tmp_path / "raw"), "processed": str(tmp_path / "processed"),
                         "cache": str(tmp_path / "cache")}}


def gravar_entradas(config, amostra=None, releases=None, janela=JANELA):
    amostra = populacao() if amostra is None else amostra
    releases = [repo(r["id"]) for r in amostra] if releases is None else releases
    for pasta, nome, lista in (("processed", "deployment_frequency.json", amostra), ("raw", "releases.json", releases)):
        caminho = Path(config["caminhos"][pasta]) / nome
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps({"janela": janela, "repositorios": lista}), encoding="utf-8")


def gravar_config(config, tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(yaml.safe_dump(config), encoding="utf-8")
    return str(caminho)


def ler_csv(caminho):
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def test_sorteia_60_repositorios_distintos_com_random_state_42():
    sorteados = amostra_ouro.sortear_repositorios(populacao())
    assert len(sorteados) == len({r["id"] for r in sorteados}) == 60
    assert sorteados == sorted(sorteados, key=lambda r: r["full_name"].lower())
    assert sorteados == amostra_ouro.sortear_repositorios(populacao())
    assert sorteados != amostra_ouro.sortear_repositorios(populacao(), random_state=7)


def test_sorteio_usa_dataframe_sample_com_random_state_42():
    import pandas as pd
    esperado = pd.DataFrame({"posicao": range(80)}).sample(n=60, random_state=42)["posicao"]
    sorteados = amostra_ouro.sortear_repositorios(populacao())
    assert {r["id"] for r in sorteados} == {i + 1 for i in esperado}


def test_ordem_do_arquivo_de_origem_nao_muda_o_sorteio():
    assert (amostra_ouro.sortear_repositorios(list(reversed(populacao())))
            == amostra_ouro.sortear_repositorios(populacao()))


def test_populacao_menor_que_60_e_recusada():
    with pytest.raises(ConfigError, match="59 repositórios"):
        amostra_ouro.sortear_repositorios(populacao(59))


def test_populacao_de_exatamente_60_entra_inteira():
    assert len(amostra_ouro.sortear_repositorios(populacao(60))) == 60


def test_repositorio_duplicado_na_amostra_e_recusado():
    with pytest.raises(ConfigError, match="duplicado"):
        amostra_ouro.sortear_repositorios(populacao() + [{"id": 1, "full_name": "org/repo1"}])


def test_sorteia_5_releases_distintas_em_ordem_cronologica():
    releases = amostra_ouro.sortear_releases(repo(1), INICIO, FIM)
    assert len(releases) == len({r["release_id"] for r in releases}) == 5
    assert [r["published_at"] for r in releases] == sorted(r["published_at"] for r in releases)
    assert releases == amostra_ouro.sortear_releases(repo(1, list(reversed(repo(1)["releases"]))), INICIO, FIM)


def test_releases_elegiveis_excluem_draft_prerelease_fora_da_janela_e_repetidas():
    lista = [release(1, 1), release(1, 1), release(2, 2, draft=True), release(3, 3, prerelease=True),
             release(4, published_at="2025-09-30T23:59:59Z"), release(5, published_at="2026-10-01T00:00:00Z"),
             release(6, published_at=None), release(7, published_at="2025-10-01T00:00:00Z")]
    assert [r["id"] for r in amostra_ouro.releases_elegiveis(repo(1, lista), INICIO, FIM)] == [7, 1]
    com_pre = amostra_ouro.releases_elegiveis(repo(1, lista), INICIO, FIM, incluir_prereleases=True)
    assert [r["id"] for r in com_pre] == [7, 1, 3]


def test_menos_de_5_releases_elegiveis_e_recusado():
    lista = [release(i, i) for i in range(1, 5)] + [release(9, 9, prerelease=True)]
    with pytest.raises(ConfigError, match="4 releases elegíveis"):
        amostra_ouro.sortear_releases(repo(1, lista), INICIO, FIM)
    assert len(amostra_ouro.sortear_releases(repo(1, lista), INICIO, FIM, incluir_prereleases=True)) == 5


def test_release_sem_id_e_recusada():
    with pytest.raises(ConfigError, match="sem ID"):
        amostra_ouro.releases_elegiveis(repo(1, [release(None)]), INICIO, FIM)


def test_links_diretos_usam_html_url_ou_a_tag_codificada():
    lista = [release(1, 1, html_url="https://github.com/org/repo1/releases/tag/oficial"),
             release(2, 2, tag_name="pkg@1.0/beta"), release(3, 3), release(4, 4), release(5, 5)]
    releases = amostra_ouro.sortear_releases(repo(1, lista), INICIO, FIM)
    assert releases[0]["release_url"] == "https://github.com/org/repo1/releases/tag/oficial"
    assert releases[1]["release_url"] == "https://github.com/org/repo1/releases/tag/pkg%401.0%2Fbeta"
    assert releases[0]["tag_anterior"] is None and releases[0]["compare_url"] is None
    assert releases[1]["compare_url"] == "https://github.com/org/repo1/compare/v1.1.0...pkg%401.0%2Fbeta"
    assert releases[2]["tag_anterior"] == "pkg@1.0/beta"


def test_compare_usa_a_release_elegivel_anterior_mesmo_nao_sorteada():
    releases = amostra_ouro.sortear_releases(repo(1), INICIO, FIM)
    for sorteada in releases:
        numero = sorteada["release_id"]
        esperado = None if numero == 1 else f"https://github.com/org/repo1/compare/v1.{numero - 1}.0...v1.{numero}.0"
        assert sorteada["compare_url"] == esperado


def test_executar_grava_sorteio_e_planilhas_em_branco(config, tmp_path):
    gravar_entradas(config)
    saida, sorteados = amostra_ouro.executar(config, saida=tmp_path / "ouro")
    assert sorted(p.name for p in saida.iterdir()) == [
        "amostra_ouro.json", "rotulador_A_releases.csv", "rotulador_A_repositorios.csv",
        "rotulador_B_releases.csv", "rotulador_B_repositorios.csv",
        "rotulador_C_releases.csv", "rotulador_C_repositorios.csv"]
    sorteio = json.loads((saida / "amostra_ouro.json").read_text(encoding="utf-8"))
    assert sorteio["repositorios"] == sorteados
    assert (sorteio["random_state"], sorteio["total_populacao"]) == (42, 80)
    assert (sorteio["total_repositorios"], sorteio["total_releases"]) == (60, 300)
    assert sorteio["janela"] == JANELA and "gerado_em" not in sorteio
    repositorios = ler_csv(saida / "rotulador_A_repositorios.csv")
    releases = ler_csv(saida / "rotulador_A_releases.csv")
    assert len(repositorios) == 60 and len(releases) == 300
    assert tuple(repositorios[0]) == amostra_ouro.COLUNAS_REPOSITORIOS
    assert tuple(releases[0]) == amostra_ouro.COLUNAS_RELEASES
    primeiro = sorteados[0]
    assert repositorios[0]["repositorio_url"] == f"https://github.com/{primeiro['full_name']}"
    assert repositorios[0]["releases_url"] == f"https://github.com/{primeiro['full_name']}/releases"
    assert releases[0]["release_url"] == primeiro["releases"][0]["release_url"]
    assert releases[0]["nome"] == primeiro["releases"][0]["nome"]
    assert all(l["tipo_projeto"] == l["releases_sao_entregas_reais"] == l["observacoes"] == "" for l in repositorios)
    assert all(l["corretiva"] == l["observacoes"] == "" for l in releases)
    assert all(sum(l["repo_id"] == str(r["repo_id"]) for l in releases) == 5 for r in sorteados)


def test_planilhas_dos_tres_rotuladores_sao_identicas(config, tmp_path):
    gravar_entradas(config)
    saida, _ = amostra_ouro.executar(config, saida=tmp_path / "ouro")
    for tipo in ("repositorios", "releases"):
        conteudos = {(saida / f"rotulador_{letra}_{tipo}.csv").read_bytes() for letra in "ABC"}
        assert len(conteudos) == 1


def test_reexecucao_nao_apaga_rotulos_ja_preenchidos(config, tmp_path):
    gravar_entradas(config)
    saida, _ = amostra_ouro.executar(config, saida=tmp_path / "ouro")
    planilha = saida / "rotulador_B_releases.csv"
    planilha.write_text("rótulos preenchidos", encoding="utf-8")
    sorteio = (saida / "amostra_ouro.json").read_bytes()
    with pytest.raises(ConfigError, match="rotulador_B_releases.csv"):
        amostra_ouro.executar(config, saida=saida)
    assert planilha.read_text(encoding="utf-8") == "rótulos preenchidos"
    amostra_ouro.executar(config, saida=saida, sobrescrever=True)
    assert len(ler_csv(planilha)) == 300
    assert (saida / "amostra_ouro.json").read_bytes() == sorteio


def test_erro_no_sorteio_nao_grava_nada(config, tmp_path):
    gravar_entradas(config, releases=[repo(i, [release(1)]) for i in range(1, 81)])
    with pytest.raises(ConfigError, match="releases elegíveis"):
        amostra_ouro.executar(config, saida=tmp_path / "ouro")
    assert not (tmp_path / "ouro").exists()


def test_repositorio_sorteado_sem_releases_coletadas_e_recusado(config, tmp_path):
    gravar_entradas(config, releases=[])
    with pytest.raises(ConfigError, match="não está em releases.json"):
        amostra_ouro.executar(config, saida=tmp_path / "ouro")


@pytest.mark.parametrize("pasta, nome", [("processed", "deployment_frequency.json"), ("raw", "releases.json")])
def test_entrada_ausente_ou_com_janela_divergente_e_recusada(config, tmp_path, pasta, nome):
    gravar_entradas(config)
    caminho = Path(config["caminhos"][pasta]) / nome
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    caminho.write_text(json.dumps({**dados, "janela": {**JANELA, "inicio": "2025-01-01T00:00:00Z"}}), encoding="utf-8")
    with pytest.raises(ConfigError, match=nome):
        amostra_ouro.executar(config, saida=tmp_path / "ouro")
    caminho.unlink()
    with pytest.raises(FileNotFoundError, match=nome):
        amostra_ouro.executar(config, saida=tmp_path / "ouro")


def test_configuracao_antiga_sem_a_chave_inclui_prereleases(config, tmp_path):
    del config["inclusao"]["incluir_prereleases"]
    lista = [release(i, i, prerelease=True) for i in range(1, 6)]
    gravar_entradas(config, releases=[repo(i, lista) for i in range(1, 81)])
    saida, _ = amostra_ouro.executar(config, saida=tmp_path / "ouro")
    assert json.loads((saida / "amostra_ouro.json").read_text(encoding="utf-8"))["incluir_prereleases"] is True


def test_cli_usa_pasta_padrao_e_relata_totais(config, tmp_path, monkeypatch, capsys):
    gravar_entradas(config)
    monkeypatch.chdir(tmp_path)
    assert amostra_ouro.main(["--config", gravar_config(config, tmp_path)]) == 0
    assert "60 repositórios, 300 releases, 6 planilhas" in capsys.readouterr().out
    assert (tmp_path / "validacao" / "amostra-ouro" / "amostra_ouro.json").is_file()
    assert amostra_ouro.main(["--config", gravar_config(config, tmp_path)]) == 2
    assert "--sobrescrever" in capsys.readouterr().err
    assert amostra_ouro.main(["--config", gravar_config(config, tmp_path), "--sobrescrever"]) == 0


def test_cli_aceita_caminhos_explicitos(config, tmp_path, capsys):
    gravar_entradas(config)
    processed, raw = (Path(config["caminhos"][k]) for k in ("processed", "raw"))
    amostra = processed.rename(tmp_path / "outra") / "deployment_frequency.json"
    releases = raw.rename(tmp_path / "bruto") / "releases.json"
    argumentos = ["--config", gravar_config(config, tmp_path), "--saida", str(tmp_path / "ouro")]
    assert amostra_ouro.main(argumentos) == 2
    assert "pipeline integrado" in capsys.readouterr().err
    assert amostra_ouro.main(argumentos + ["--amostra", str(amostra), "--releases", str(releases)]) == 0


def test_modulo_executavel(config, tmp_path, monkeypatch):
    gravar_entradas(config)
    monkeypatch.setattr(sys, "argv", ["pipeline.amostra_ouro", "--config", gravar_config(config, tmp_path),
                                      "--saida", str(tmp_path / "ouro")])
    monkeypatch.delitem(sys.modules, "pipeline.amostra_ouro")
    with pytest.raises(SystemExit) as saida:
        runpy.run_module("pipeline.amostra_ouro", run_name="__main__")
    assert saida.value.code == 0
