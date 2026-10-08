import datetime as dt
import json
from pathlib import Path

import pytest
import requests

from pipeline import releases
from pipeline.__main__ import main
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import janela_utc, load_config
from pipeline.github_api import GitHubClient
from pipeline.releases import coletar_repositorio, executar

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
INICIO, FIM = janela_utc(load_config(CONFIG))
REPO = {"id": 10, "full_name": "org/projeto", "default_branch": "main"}
PATH = "/repos/org/projeto/releases"


def release(id=1, **alteracoes):
    return {"id": id, "tag_name": f"v1.0.{id}", "draft": False, "prerelease": False,
            "published_at": "2025-10-10T12:00:00Z", "created_at": "2025-09-01T00:00:00Z",
            "target_commitish": "main", "html_url": f"https://github.com/org/projeto/releases/{id}",
            "name": f"Release {id}", "body": "Correção de um defeito.", **alteracoes}


def resposta(corpo, proxima=None, status=200):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    r.encoding = "utf-8"
    if proxima:
        r.headers["Link"] = (f'<https://api.github.com{PATH}?per_page=100&page={proxima}>; rel="next", '
                             f'<https://api.github.com{PATH}?per_page=100&page=9>; rel="last"')
    return r


class Sessao:
    def __init__(self, respostas):
        self.headers = {}
        self.respostas = iter(respostas)
        self.chamadas = []

    def get(self, url, params, timeout):
        self.chamadas.append((url, dict(params)))
        r = next(self.respostas)
        if isinstance(r, Exception):
            raise r
        return r


def cliente(respostas, cache=None):
    sessao = Sessao(respostas)
    return GitHubClient("token-falso", session=sessao, cache=cache, sleep=lambda _: None), sessao


def config(tmp_path):
    cfg = load_config(CONFIG)
    cfg["caminhos"] = {"raw": str(tmp_path / "raw"), "cache": str(tmp_path / "cache")}
    return cfg


def test_paginacao_segue_next_mesmo_em_pagina_curta_antiga_e_deduplica():
    antiga = release(9, published_at="2025-09-30T23:59:59Z")
    c, sessao = cliente([resposta([antiga, release(3)], proxima=3),
                        resposta([release(3), release(2), release(1)])])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert sessao.chamadas == [(f"https://api.github.com{PATH}", {"per_page": 100, "page": 1}),
                              (f"https://api.github.com{PATH}", {"per_page": 100, "page": 3})]
    assert [r["id"] for r in dados["releases"]] == [1, 2, 3]
    assert dados["total_releases"] == dados["total_releases_estaveis"] == 3
    assert dados["total_prereleases"] == 0


def test_janela_inclui_primeiro_e_ultimo_instante_com_fuso_e_usa_publicacao():
    lista = [release(1, published_at="2025-10-01T00:00:00Z"),
             release(2, published_at="2026-09-30T23:59:59.999999Z"),
             release(3, published_at="2025-09-30T23:59:59Z"),
             release(4, published_at="2026-10-01T00:00:00Z"),
             release(5, published_at="2025-09-30T21:00:00-03:00"),
             release(6, published_at="2026-09-30T21:00:00-03:00")]
    c, _ = cliente([resposta(lista)])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert [r["id"] for r in dados["releases"]] == [1, 5, 2]


def test_exclui_drafts_e_sem_publicacao_preserva_prereleases_e_campos():
    estavel, previa = release(1), release(2, prerelease=True)
    sem_data = release(5)
    sem_data.pop("published_at")
    c, _ = cliente([resposta([estavel, previa, release(3, draft=True),
                             release(4, published_at=None), sem_data])])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["releases"] == [estavel, previa]
    assert dados["total_releases"] == 2
    assert dados["total_releases_estaveis"] == dados["total_prereleases"] == 1


@pytest.mark.parametrize("publicacao", ["inválida", "2025-10-10T12:00:00", 42])
def test_publicacao_invalida_e_ignorada_com_aviso(publicacao, caplog):
    c, _ = cliente([resposta([release(published_at=publicacao)])])
    assert coletar_repositorio(c, REPO, INICIO, FIM)["releases"] == []
    assert "published_at inválido" in caplog.text


def test_pagina_cheia_sem_next_nao_faz_chamada_adicional():
    c, sessao = cliente([resposta([release(i) for i in range(100)])])
    assert coletar_repositorio(c, REPO, INICIO, FIM)["total_releases"] == 100
    assert len(sessao.chamadas) == 1


def test_repositorio_sem_releases_e_mantido_com_totais_zero():
    c, sessao = cliente([resposta([])])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["releases"] == []
    assert dados["total_releases"] == dados["total_releases_estaveis"] == dados["total_prereleases"] == 0
    assert len(sessao.chamadas) == 1


def test_link_que_nao_avanca_e_recusado():
    c, _ = cliente([resposta([release()], proxima=1)])
    with pytest.raises(ValueError, match="não avança"):
        coletar_repositorio(c, REPO, INICIO, FIM)


def test_consolidado_le_metadados_e_registra_janela_totais_e_descartes(tmp_path, caplog, monkeypatch):
    cfg = config(tmp_path)
    repos = [REPO, {**REPO, "id": 11, "full_name": "org/inacessivel"}]
    gravar_json(tmp_path / "raw" / "metadados.json", {"repositorios": repos})
    c, _ = cliente([resposta([release(), release(2, prerelease=True)]), resposta({}, status=404)])
    monkeypatch.setattr(releases, "LOG_A_CADA", 1)
    with caplog.at_level("INFO"):
        caminho, lista, descartes = executar(cfg, c)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert dados["janela"] == {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
    assert dados["total_avaliados"] == dados["total_releases"] == 2
    assert dados["total_repositorios"] == dados["total_releases_estaveis"] == dados["total_prereleases"] == 1
    assert dados["repositorios"] == lista
    assert dados["descartes"] == descartes == [{"id": 11, "full_name": "org/inacessivel",
                                                "motivo": "repositorio_inacessivel", "detalhe": "HTTP 404"}]
    assert "Releases: 2/2 repositórios avaliados" in caplog.text


@pytest.mark.parametrize("status", [404, 451])
def test_inacessiveis_registrados_com_motivo(tmp_path, status):
    c, _ = cliente([resposta({}, status=status)])
    _, lista, descartes = executar(config(tmp_path), c, [REPO])
    assert lista == []
    assert descartes[0]["detalhe"] == f"HTTP {status}"


@pytest.mark.parametrize("status", [403, 500])
def test_demais_erros_propagados_preservam_consolidado_anterior(tmp_path, status):
    cfg = config(tmp_path)
    saida = tmp_path / "raw" / "releases.json"
    gravar_json(saida, {"anterior": True})
    original = saida.read_bytes()
    c, _ = cliente([resposta({}, status=status) for _ in range(5)])
    with pytest.raises(requests.HTTPError):
        executar(cfg, c, [REPO])
    assert saida.read_bytes() == original


def test_retomada_por_pagina_e_reexecucao_sem_rede_preservam_link_e_corpo(tmp_path):
    cfg = config(tmp_path)
    cache_dir = tmp_path / "cache"
    primeira = resposta([release(), release(9, draft=True)], proxima=2)
    interrompido, _ = cliente([primeira, requests.Timeout("interrupção")], CacheDisco(cache_dir))
    with pytest.raises(requests.Timeout):
        executar(cfg, interrompido, [REPO])
    assert not (tmp_path / "raw" / "releases.json").exists()
    assert len(list(cache_dir.rglob("*.json"))) == 1
    url = requests.Request("GET", f"https://api.github.com{PATH}",
                           params={"per_page": 100, "page": 1}).prepare().url
    salva = CacheDisco(cache_dir).ler(url)
    assert salva.json()[1]["draft"] is True  # Resposta original preservada para auditoria.
    assert "next" in salva.links

    retomado, sessao = cliente([resposta([release(2, prerelease=True)])], CacheDisco(cache_dir))
    _, lista, _ = executar(cfg, retomado, [REPO])
    assert sessao.chamadas == [(f"https://api.github.com{PATH}", {"per_page": 100, "page": 2})]
    assert lista[0]["total_releases"] == 2
    sem_rede, sessao = cliente([], CacheDisco(cache_dir))
    _, nova_lista, _ = executar(cfg, sem_rede, [REPO])
    assert nova_lista == lista
    assert sessao.chamadas == []


def test_cli_executa_apenas_releases_com_cache_e_mostra_totais(tmp_path, monkeypatch, capsys):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(CONFIG.read_text(encoding="utf-8")
                        .replace("raw: data/raw", f"raw: {tmp_path.as_posix()}/raw")
                        .replace("cache: data/cache", f"cache: {tmp_path.as_posix()}/cache"), encoding="utf-8")
    gravar_json(tmp_path / "raw" / "metadados.json", {"repositorios": [REPO]})
    sessao = Sessao([resposta([release()])])
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    monkeypatch.setattr("pipeline.__main__.GitHubClient", lambda token, base, timeout, cache:
                        GitHubClient(token, base, timeout, cache=cache, session=sessao))
    for nome in ("candidatos", "actions", "metadados", "tags", "workflow_runs"):
        monkeypatch.setattr(f"pipeline.{nome}.executar", lambda *args: pytest.fail("etapa não solicitada"))
    assert main(["--config", str(cfg_path), "--etapas", "releases"]) == 0
    assert "Releases: 1 repositórios, 1 releases publicadas (1 estáveis)" in capsys.readouterr().out
    assert (tmp_path / "raw" / "releases.json").is_file()
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 1
    assert main(["--config", str(cfg_path), "--etapas", "releases"]) == 0
    assert len(sessao.chamadas) == 1


def test_cli_sem_metadados_informa_dependencia(tmp_path, monkeypatch, capsys):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(CONFIG.read_text(encoding="utf-8")
                        .replace("raw: data/raw", f"raw: {tmp_path.as_posix()}/raw"), encoding="utf-8")
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    assert main(["--config", str(cfg_path), "--etapas", "releases"]) == 2
    assert "execute antes a etapa metadados" in capsys.readouterr().err
