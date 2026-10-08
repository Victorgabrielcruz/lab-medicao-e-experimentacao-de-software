import json
from pathlib import Path

import pytest
import requests

from pipeline import tags
from pipeline.__main__ import main
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import janela_utc, load_config
from pipeline.github_api import GitHubClient
from pipeline.tags import coletar_repositorio, executar

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
INICIO, FIM = janela_utc(load_config(CONFIG))
REPO = {"id": 10, "full_name": "org/projeto", "default_branch": "main"}
PATH = "/repos/org/projeto/tags"
DATA = "2025-10-10T12:00:00Z"


def tag(nome="v1.0", sha="abc"):
    return {"name": nome, "commit": {"sha": sha, "url": f"https://api.github.com/repos/org/projeto/commits/{sha}"},
            "node_id": f"tag-{nome}", "zipball_url": f"https://github.com/org/projeto/zipball/{nome}",
            "tarball_url": f"https://github.com/org/projeto/tarball/{nome}"}


def commit(data=DATA):
    # A data do committer está fora da janela: o filtro deve usar só a do autor.
    return {"commit": {"author": {"date": data}, "committer": {"date": "2026-10-02T00:00:00Z"}}}


def resposta(corpo, proxima=None, status=200):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(corpo).encode("utf-8")
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
        self.chamadas.append((url, params))
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


def test_paginacao_segue_next_apos_tag_antiga_e_pagina_curta():
    c, sessao = cliente([resposta([tag("antiga", "old")], proxima=3),
                        resposta(commit("2025-09-30T23:59:59Z")),
                        resposta([tag("v2", "new")]), resposta(commit())])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert [t["name"] for t in dados["tags"]] == ["v2"]
    assert sessao.chamadas == [
        (f"https://api.github.com{PATH}", {"per_page": 100, "page": 1}),
        ("https://api.github.com/repos/org/projeto/commits/old", None),
        (f"https://api.github.com{PATH}", {"per_page": 100, "page": 3}),
        ("https://api.github.com/repos/org/projeto/commits/new", None),
    ]
    assert not dados["coleta_incompleta"]


def test_tags_distintas_no_mesmo_sha_preservadas_duplicatas_por_nome_removidas():
    lista = [tag("v2"), tag("v1"), tag("v1")]
    c, sessao = cliente([resposta(lista, proxima=2), resposta(commit()), resposta([tag("v2")])])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["total_tags"] == 2
    assert [t["name"] for t in dados["tags"]] == ["v1", "v2"]
    assert len([url for url, _ in sessao.chamadas if "/commits/" in url]) == 1
    assert dados["tags"][0] == {
        "name": "v1", "commit_sha": "abc", "commit_author_date": DATA,
        "commit_url": lista[0]["commit"]["url"], "node_id": "tag-v1",
        "zipball_url": "https://github.com/org/projeto/zipball/v1",
        "tarball_url": "https://github.com/org/projeto/tarball/v1",
    }


def test_filtra_por_data_do_autor_com_limites_e_fusos():
    datas = ["2025-10-01T00:00:00Z", "2026-09-30T23:59:59.999999Z",
             "2025-09-30T23:59:59Z", "2026-10-01T00:00:00Z",
             "2025-09-30T21:00:00-03:00", "2026-09-30T21:00:00-03:00"]
    lista = [tag(f"v{i}", f"sha{i}") for i in range(len(datas))]
    c, _ = cliente([resposta(lista)] + [resposta(commit(data)) for data in datas])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert [t["name"] for t in dados["tags"]] == ["v0", "v4", "v1"]
    assert dados["tags_ignoradas"] == []  # Tags fora da janela são filtradas normalmente.
    assert not dados["coleta_incompleta"]


def test_tags_com_barra_usam_sha_para_consultar_commit():
    c, sessao = cliente([resposta([tag("release/v1.0")]), resposta(commit())])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["tags"][0]["name"] == "release/v1.0"
    assert sessao.chamadas[1][0].endswith("/commits/abc")


def test_repositorio_sem_tags_mantido_com_totais_zero():
    c, sessao = cliente([resposta([])])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["total_tags"] == 0
    assert dados["tags"] == dados["tags_ignoradas"] == []
    assert not dados["coleta_incompleta"]
    assert len(sessao.chamadas) == 1


def test_pagina_cheia_sem_next_nao_consulta_outra_pagina():
    c, sessao = cliente([resposta([tag(f"v{i}") for i in range(100)]), resposta(commit())])
    assert coletar_repositorio(c, REPO, INICIO, FIM)["total_tags"] == 100
    assert len(sessao.chamadas) == 2  # Uma página, um SHA comum às 100 tags.


def test_link_que_nao_avanca_e_recusado():
    c, _ = cliente([resposta([], proxima=1)])
    with pytest.raises(ValueError, match="não avança"):
        coletar_repositorio(c, REPO, INICIO, FIM)


@pytest.mark.parametrize("corpo", [commit(None), commit("inválida"), commit(42),
                                  commit("2025-10-10T00:00:00"), {"commit": {"author": None}}, {}])
def test_data_ausente_ou_invalida_registrada_sem_usar_committer(corpo, caplog):
    c, _ = cliente([resposta([tag()]), resposta(corpo)])
    dados = coletar_repositorio(c, REPO, INICIO, FIM)
    assert dados["tags"] == []
    assert dados["coleta_incompleta"]
    assert dados["tags_ignoradas"][0]["motivo"] == "data_commit_invalida"
    assert "tag v1.0 ignorada" in caplog.text


@pytest.mark.parametrize("status", [404, 451])
def test_commit_inacessivel_ignora_so_tags_associadas_e_preserva_repositorio(tmp_path, status):
    c, sessao = cliente([resposta([tag("v1", "bad"), tag("v2", "bad"), tag("v3", "good")]),
                        resposta({}, status=status), resposta(commit())])
    _, lista, descartes = executar(config(tmp_path), c, [REPO])
    assert descartes == []
    assert lista[0]["total_tags"] == 1
    assert lista[0]["tags"][0]["name"] == "v3"
    assert lista[0]["coleta_incompleta"]
    assert [t["name"] for t in lista[0]["tags_ignoradas"]] == ["v1", "v2"]
    assert all(t["detalhe"] == f"HTTP {status}" for t in lista[0]["tags_ignoradas"])
    assert len(sessao.chamadas) == 3


@pytest.mark.parametrize("status", [404, 451])
def test_endpoint_tags_inacessivel_descarta_repositorio(tmp_path, status):
    c, _ = cliente([resposta({}, status=status)])
    _, lista, descartes = executar(config(tmp_path), c, [REPO])
    assert lista == []
    assert descartes == [{"id": 10, "full_name": "org/projeto", "motivo": "repositorio_inacessivel",
                          "detalhe": f"HTTP {status}"}]


@pytest.mark.parametrize("status", [403, 500])
@pytest.mark.parametrize("no_commit", [False, True])
def test_erros_propagados_preservam_consolidado_anterior(tmp_path, status, no_commit):
    saida = tmp_path / "raw" / "tags.json"
    gravar_json(saida, {"anterior": True})
    original = saida.read_bytes()
    respostas = ([resposta([tag()])] if no_commit else []) + [resposta({}, status=status)] * 5
    c, _ = cliente(respostas)
    with pytest.raises(requests.HTTPError):
        executar(config(tmp_path), c, [REPO])
    assert saida.read_bytes() == original


def test_retomada_em_commit_com_paginas_e_commits_cacheados_e_reexecucao_sem_rede(tmp_path):
    cfg = config(tmp_path)
    cache_dir = tmp_path / "cache"
    c, _ = cliente([resposta([tag("v1", "a"), tag("v2", "b")], proxima=2),
                    resposta(commit()), requests.Timeout("interrupção")], CacheDisco(cache_dir))
    with pytest.raises(requests.Timeout):
        executar(cfg, c, [REPO])
    assert not (tmp_path / "raw" / "tags.json").exists()
    assert len(list(cache_dir.rglob("*.json"))) == 2

    c, sessao = cliente([resposta(commit()), resposta([tag("v3", "c")]), resposta(commit())],
                        CacheDisco(cache_dir))
    caminho, lista, _ = executar(cfg, c, [REPO])
    assert sessao.chamadas == [
        ("https://api.github.com/repos/org/projeto/commits/b", None),
        (f"https://api.github.com{PATH}", {"per_page": 100, "page": 2}),
        ("https://api.github.com/repos/org/projeto/commits/c", None),
    ]
    assert lista[0]["total_tags"] == 3
    assert len(list(cache_dir.rglob("*.json"))) == 5
    assert json.loads(caminho.read_text())["total_tags"] == 3
    c, sessao = cliente([], CacheDisco(cache_dir))
    _, nova_lista, _ = executar(cfg, c, [REPO])
    assert nova_lista == lista
    assert sessao.chamadas == []


def test_consolidado_le_metadados_registra_totais_janela_e_incompletude(tmp_path, monkeypatch, caplog):
    gravar_json(tmp_path / "raw" / "metadados.json", {"repositorios": [REPO]})
    c, _ = cliente([resposta([tag("v1"), tag("v2", "bad")]), resposta(commit()), resposta(commit(None))])
    monkeypatch.setattr(tags, "LOG_A_CADA", 1)
    with caplog.at_level("INFO"):
        caminho, lista, _ = executar(config(tmp_path), c)
    dados = json.loads(caminho.read_text())
    assert dados["janela"] == {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}
    assert dados["data_referencia"] == "commit.author.date"
    assert dados["total_avaliados"] == dados["total_repositorios"] == dados["total_tags"] == 1
    assert dados["total_tags_ignoradas"] == dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["repositorios"] == lista
    assert "Tags: 1/1 repositórios avaliados" in caplog.text


def configurar_cli(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(CONFIG.read_text(encoding="utf-8")
                       .replace("raw: data/raw", f"raw: {tmp_path.as_posix()}/raw")
                       .replace("cache: data/cache", f"cache: {tmp_path.as_posix()}/cache"), encoding="utf-8")
    return caminho


def test_cli_executa_apenas_tags_com_cache_e_mostra_totais(tmp_path, monkeypatch, capsys):
    cfg_path = configurar_cli(tmp_path)
    gravar_json(tmp_path / "raw" / "metadados.json", {"repositorios": [REPO]})
    sessao = Sessao([resposta([tag()]), resposta(commit())])
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    monkeypatch.setattr("pipeline.__main__.GitHubClient", lambda token, base, timeout, cache:
                        GitHubClient(token, base, timeout, cache=cache, session=sessao))
    for nome in ("candidatos", "actions", "metadados", "releases", "compare", "workflow_runs"):
        monkeypatch.setattr(f"pipeline.{nome}.executar", lambda *args: pytest.fail("etapa não solicitada"))
    assert main(["--config", str(cfg_path), "--etapas", "tags"]) == 0
    assert "Tags: 1 repositórios, 1 tags na janela, 0 coletas incompletas" in capsys.readouterr().out
    assert (tmp_path / "raw" / "tags.json").is_file()
    assert len(list((tmp_path / "cache").rglob("*.json"))) == 2
    assert main(["--config", str(cfg_path), "--etapas", "tags"]) == 0
    assert len(sessao.chamadas) == 2


def test_cli_sem_metadados_informa_dependencia(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    assert main(["--config", str(configurar_cli(tmp_path)), "--etapas", "tags"]) == 2
    assert "execute antes a etapa metadados" in capsys.readouterr().err
