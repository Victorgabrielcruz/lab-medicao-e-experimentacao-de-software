import hashlib
import io
import json
import runpy
import sys
import tarfile
from pathlib import Path

import pytest

from pipeline import avaliacao_snapshot as snap
from pipeline.config import ConfigError
from test_avaliacao_heuristica import JANELA, entradas


def pacote(tmp_path, manifesto, modo="completo", erro=None):
    pasta = tmp_path / "snapshot"
    pasta.mkdir()
    rels = [{"id": r["release_id"], "tag_name": r["tag_name"], "published_at": r["published_at"],
             "draft": False, "prerelease": False} for r in manifesto["repositorios"][0]["releases"]]
    rels.insert(1, {"id": 2, "tag_name": "v2.4.0", "published_at": "2026-05-12T00:00:00Z", "draft": False, "prerelease": False})
    repo = {"id": 10, "full_name": "org/projeto", "releases": rels}
    contexto = {"releases": repo, "janela": JANELA, "api": "https://api.github.com", "versao_compare": 1}
    digest = hashlib.sha256(json.dumps(contexto, sort_keys=True).encode()).hexdigest()
    nome_rel = "raw/amostra-final-500/checkpoints/ctx/10.json"
    nome_cp = f"raw/amostra-final-500/checkpoints/compare/{digest}/10.json"
    if modo == "compare_antigo":
        nome_cp = nome_cp.replace(digest, "antigo")
    comparacoes = []
    for n, atual in enumerate(rels):
        commits = [{"sha": "a", "commit": {"message": "fix: defeito", "campo_descartado": "não usado"}}] if n == 0 else []
        comparacoes.append({"release": atual, "release_anterior": rels[n-1] if n else None,
                            "commits": commits, "total_commits_api": len(commits),
                            "total_commits_coletados": len(commits)})
    cp = {"id": 10, "full_name": "org/projeto", "comparacoes": comparacoes}
    fontes = {nome_cp: cp, nome_rel: {"aprovados": {"releases": repo}}}
    if modo == "sem_compare":
        fontes.pop(nome_cp)
    dados = {n: json.dumps(v).encode() for n, v in fontes.items()}
    arquivo = pasta / "snapshot.tar.gz.part001"
    with tarfile.open(arquivo, "w:gz") as tar:
        for n, b in dados.items():
            if erro == "membro_ausente" and n == nome_rel:
                continue
            info = tarfile.TarInfo(n)
            info.size = len(b)
            tar.addfile(info, io.BytesIO(b))
            if erro == "membro_duplicado" and n == nome_rel:
                tar.addfile(info, io.BytesIO(b))
    m = {"contexto": {"janela": JANELA, "api": "https://api.github.com"}, "contexto_sha256": "ctx",
         "ids_amostra": [10], "capturado_em_utc": "2026-10-20T11:34:10Z", "processamento_final_completo": False,
         "pacotes": [{"nome": "snapshot-500", "partes": [{"arquivo": arquivo.name, "bytes": arquivo.stat().st_size,
                                                        "sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest()}],
                      "arquivos": {n: {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} for n, b in dados.items()}}]}
    if erro == "parte_corrompida":
        m["pacotes"][0]["partes"][0]["sha256"] = "0" * 64
    if erro == "checkpoint_corrompido":
        m["pacotes"][0]["arquivos"][nome_rel]["sha256"] = "0" * 64
    if erro == "parte_insegura":
        m["pacotes"][0]["partes"][0]["arquivo"] = "../snapshot.tar.gz.part001"
    if erro == "releases_ausentes_manifesto":
        m["pacotes"][0]["arquivos"].pop(nome_rel)
    if erro == "populacao_divergente":
        m["ids_amostra"] = []
    (pasta / "manifesto.json").write_text(json.dumps(m))
    return pasta


@pytest.mark.parametrize("modo,n", [("completo", 3), ("sem_compare", 1), ("compare_antigo", 1)])
def test_snapshot_verificado_reduzido_e_sem_rede(entradas, tmp_path, monkeypatch, modo, n):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto, modo)
    antes = {p: p.read_bytes() for p in [*fonte.iterdir(), *amostra.iterdir()]}
    monkeypatch.setattr("requests.sessions.Session.request", lambda *a, **k: pytest.fail("Acesso à rede"))
    out = tmp_path / "out"
    r = snap.executar(fonte, pasta=amostra, saida=out)
    assert r["cobertura"]["avaliadas"] == n
    assert r["avaliacao_completa"] is (n == 3)
    p = json.loads((out / "entrada_snapshot.json").read_text())
    assert p["origens_snapshot"]["novas_consultas_api"] == 0
    assert p["origens_snapshot"]["repositorios_com_compare_compativel"] == ([10] if n == 3 else [])
    assert len(p["repositorios"][0]["releases"]) == 3
    assert p["origens_snapshot"]["limite_exemplos_commits_corretivos"] == 5
    for rel in p["repositorios"][0]["releases"]:
        assert "commits_corretivos" not in rel
        assert len(rel["exemplos_commits_corretivos"]) <= rel["total_commits_corretivos"]
    assert all(p.read_bytes() == b for p, b in antes.items())
    # A segunda execução preserva bytes e hashes com os mesmos caminhos de entrada.
    r2 = snap.executar(fonte, pasta=amostra, saida=out)
    assert r2 == r


def test_resumo_de_sinais_nao_muda_a_decisao_com_muitos_commits(entradas, tmp_path, monkeypatch):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    calcular = snap.cfr_b.calcular_repositorio
    def muitos(*args, **kwargs):
        r = calcular(*args, **kwargs)
        r["releases"][0]["commits_corretivos"] = [{"sha": str(i), "termo": "fix"} for i in range(20)]
        return r
    monkeypatch.setattr(snap.cfr_b, "calcular_repositorio", muitos)
    p = snap.carregar(fonte, amostra)
    rel = p["repositorios"][0]["releases"][0]
    assert rel["corretiva"] is True and rel["total_commits_corretivos"] == 20
    assert len(rel["exemplos_commits_corretivos"]) == 5


@pytest.mark.parametrize("erro", ["parte_corrompida", "checkpoint_corrompido", "membro_ausente",
                                 "membro_duplicado", "parte_insegura", "releases_ausentes_manifesto", "populacao_divergente"])
def test_snapshot_invalido_nao_produz_resultados(entradas, tmp_path, erro):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto, erro=erro)
    with pytest.raises(ConfigError):
        snap.executar(fonte, pasta=amostra, saida=tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_snapshot_recusa_saida_dentro_do_pacote(entradas, tmp_path):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    with pytest.raises(ConfigError, match="invadir"):
        snap.executar(fonte, pasta=amostra, saida=fonte / "out")


def test_gerar_cfr_b_preserva_sequencia_completa_e_agregados(entradas, tmp_path):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    destino = tmp_path / "processed/cfr_b.json"
    r = snap.gerar_cfr_b(fonte, pasta=amostra, saida=destino)
    assert r["total_repositorios"] == 1 and r["total_releases"] == 4
    assert not r["processamento_final_completo"]
    repo = r["repositorios"][0]
    assert repo["total_releases"] == len(repo["releases"]) == 4
    assert [x["release_id"] for x in repo["releases"]] == [1, 2, 3, 4]
    assert [x["corretiva"] for x in repo["releases"]] == [True, False, True, False]
    assert repo["releases"][2]["patch_semver"] is True
    assert "commits_corretivos" in repo["releases"][0]
    assert r["repositorios_com_cfr"] == 1 and repo["change_failure_rate"] is not None
    # O arquivo da #161 serve diretamente para avaliar os três pares sorteados.
    avaliacao = snap.av.executar(destino, pasta=amostra, saida=tmp_path / "avaliacao")
    assert avaliacao["avaliacao_completa"] and avaliacao["cobertura"]["avaliadas"] == 3
    assert snap.main(["--pacote", str(fonte), "--pasta", str(amostra), "--cfr-b", str(destino)]) == 0
    for invalido in [fonte / "manifesto.json", amostra / "amostra_ouro.json"]:
        with pytest.raises(ConfigError, match="sobrescrever"):
            snap.gerar_cfr_b(fonte, pasta=amostra, saida=invalido)


@pytest.mark.filterwarnings("ignore:.*found in sys.modules.*:RuntimeWarning")
def test_cli_snapshot_e_entrypoint(entradas, tmp_path, monkeypatch):
    amostra, _, manifesto, *_ = entradas
    fonte = pacote(tmp_path, manifesto)
    args = ["--pacote", str(fonte), "--pasta", str(amostra), "--saida", str(tmp_path / "out")]
    assert snap.main(args) == 0
    (fonte / "manifesto.json").unlink()
    assert snap.main(args) == 2
    monkeypatch.setattr(sys, "argv", ["avaliacao_snapshot", *args])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("pipeline.avaliacao_snapshot", run_name="__main__")
    assert exc.value.code == 2
