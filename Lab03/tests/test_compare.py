import json
from pathlib import Path

import pytest
import requests

from pipeline import compare
from pipeline.__main__ import main
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import ConfigError, janela_utc, load_config
from pipeline.github_api import GitHubClient
from pipeline.compare import coletar_comparacao, coletar_repositorio, executar

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"
INICIO, FIM = janela_utc(load_config(CONFIG))
REPO = {"id": 10, "full_name": "org/projeto", "default_branch": "main"}
PATH = "/repos/org/projeto/compare/v0...v1"


def release(id=1, **alteracoes):
    return {"id": id, "tag_name": f"v{id}", "draft": False, "prerelease": False,
            "published_at": f"2025-10-{id or 1:02d}T00:00:00Z",
            "html_url": f"https://github.com/org/projeto/releases/{id}", **alteracoes}


ANTERIOR = release(0, published_at="2025-09-30T23:59:59Z")


def commit(id=1):
    return {"sha": f"sha{id}", "html_url": f"https://github.com/org/projeto/commit/sha{id}",
            "commit": {"author": {"date": "2025-09-15T10:00:00Z"},
                       "committer": {"date": "2025-10-02T12:00:00Z"}, "message": "fix: exemplo"},
            "parents": [{"sha": f"pai{id}"}]}


def pagina(commits=(), total=None, status="ahead"):
    return {"status": status, "total_commits": len(commits) if total is None else total,
            "commits": list(commits)}


def resposta(corpo, proxima=None, status=200):
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(corpo).encode("utf-8")
    if proxima:
        r.headers["Link"] = f'<https://api.github.com{PATH}?per_page=100&page={proxima}>; rel="next"'
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


def test_supera_250_sem_truncar_com_paginacao_e_registro(caplog):
    commits = [commit(i) for i in range(301)]
    respostas = [resposta(pagina(commits[i:i+100], 301), proxima=(i // 100 + 2 if i < 300 else None))
                 for i in range(0, 301, 100)]
    c, sessao = cliente(respostas)
    with caplog.at_level("INFO"):
        dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert dados["commits"] == commits
    assert dados["total_commits_api"] == dados["total_commits_coletados"] == 301
    assert dados["limite_sem_paginacao"] == 250 and dados["limite_250_superado"]
    assert not dados["coleta_incompleta"]
    assert [p["pagina"] for p in dados["paginas"]] == [1, 2, 3, 4]
    assert sum(p["commits_api"] for p in dados["paginas"]) == 301
    assert [params for _, params in sessao.chamadas] == [{"per_page": 100, "page": i} for i in range(1, 5)]
    assert "limite sem paginação de 250 tratado em 4 páginas" in caplog.text


@pytest.mark.parametrize("total,superado", [(249, False), (250, False), (251, True)])
def test_limite_sem_paginacao_registrado_na_fronteira(total, superado):
    commits = [commit(i) for i in range(total)]
    respostas = [resposta(pagina(commits[i:i+100], total), proxima=(i // 100 + 2 if i + 100 < total else None))
                 for i in range(0, total, 100)]
    c, _ = cliente(respostas)
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert dados["limite_250_superado"] == superado
    assert dados["total_commits_coletados"] == total
    assert not dados["coleta_incompleta"]


def test_link_next_seguido_mesmo_em_pagina_curta():
    c, sessao = cliente([resposta(pagina([commit(1)], 2), proxima=3), resposta(pagina([commit(2)], 2))])
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert [params["page"] for _, params in sessao.chamadas] == [1, 3]
    assert dados["total_commits_coletados"] == 2
    assert not dados["coleta_incompleta"]


def test_deduplica_sha_em_paginas_e_nao_inclui_commit_base():
    primeira = pagina([commit(2)], 2)
    primeira["base_commit"] = commit(1)
    c, _ = cliente([resposta(primeira, proxima=2), resposta(pagina([commit(2), commit(3)], 2))])
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert [c["sha"] for c in dados["commits"]] == ["sha2", "sha3"]
    assert not dados["coleta_incompleta"]
    assert dados["commits"][0]["commit"]["author"]["date"].startswith("2025-09")  # Antes da janela.


@pytest.mark.parametrize("segunda", [pagina(), pagina([commit(1)], 2)])
def test_pagina_vazia_ou_duplicada_sinaliza_incompletude(segunda, caplog):
    c, _ = cliente([resposta(pagina([commit(1)], 2), proxima=2), resposta(segunda)])
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert dados["coleta_incompleta"]
    assert dados["total_commits_coletados"] == 1
    assert "compare incompleto" in caplog.text


def test_sem_next_com_total_maior_nao_finge_coleta_completa():
    c, _ = cliente([resposta(pagina([commit()], 300))])
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert dados["coleta_incompleta"] and dados["limite_250_superado"]


def test_comparacao_identica_sem_commits_e_valida():
    c, sessao = cliente([resposta(pagina(status="identical"))])
    dados = coletar_comparacao(c, REPO["full_name"], "v0", "v1")
    assert dados["commits"] == [] and dados["total_commits_coletados"] == 0
    assert dados["status"] == "identical" and not dados["coleta_incompleta"]
    assert len(sessao.chamadas) == 1


def test_refs_com_barras_e_caracteres_especiais_codificadas():
    c, sessao = cliente([resposta(pagina())])
    coletar_comparacao(c, REPO["full_name"], "release/v1+build", "release/v2#tag")
    assert sessao.chamadas[0][0].endswith("/compare/release%2Fv1%2Bbuild...release%2Fv2%23tag")


def test_link_que_nao_avanca_e_recusado():
    c, _ = cliente([resposta(pagina(), proxima=1)])
    with pytest.raises(ValueError, match="não avança"):
        coletar_comparacao(c, REPO["full_name"], "v0", "v1")


def test_primeira_release_da_janela_compara_com_anterior_fora_dela():
    historico = [release(8, published_at="2025-08-01T00:00:00Z"), ANTERIOR,
                 release(9, published_at="2025-09-30T23:59:59.5Z", prerelease=True)]
    repo = {**REPO, "releases": [release(2), release(1), release(1),
                                release(3, prerelease=True), release(4, draft=True),
                                release(5, published_at="2026-10-01T00:00:00Z"), release(6, published_at=None)]}
    c, sessao = cliente([resposta(historico), resposta(pagina([commit()])), resposta(pagina([commit(2)]))])
    dados = coletar_repositorio(c, repo, INICIO, FIM)
    assert [c["release"]["tag_name"] for c in dados["comparacoes"]] == ["v1", "v2"]
    assert dados["comparacoes"][0]["release_anterior"]["published_at"] == ANTERIOR["published_at"]
    assert dados["total_releases"] == dados["total_comparacoes"] == 2
    assert dados["total_releases_ignoradas"] == 0
    assert [url.rsplit("/", 1)[1] for url, _ in sessao.chamadas[1:]] == ["v0...v1", "v1...v2"]


def test_historico_de_releases_paginado_para_recuperar_anterior_fora_da_janela():
    link = '<https://api.github.com/repos/org/projeto/releases?per_page=100&page=2>; rel="next"'
    primeira = resposta([release(1)])
    primeira.headers["Link"] = link
    c, sessao = cliente([primeira, resposta([ANTERIOR]), resposta(pagina())])
    dados = coletar_repositorio(c, {**REPO, "releases": [release()]}, INICIO, FIM)
    assert dados["comparacoes"][0]["release_anterior"]["tag_name"] == "v0"
    assert [params["page"] for _, params in sessao.chamadas] == [1, 2, 1]


def test_primeira_release_do_historico_ignorada_proxima_comparada():
    c, sessao = cliente([resposta([]), resposta(pagina())])
    dados = coletar_repositorio(c, {**REPO, "releases": [release(1), release(2)]}, INICIO, FIM)
    assert dados["total_releases_ignoradas"] == 1
    assert dados["releases_ignoradas_por_motivo"] == {"sem_release_anterior": 1}
    assert dados["comparacoes"][0]["release_anterior"] is None
    assert dados["total_comparacoes"] == 1 and not dados["coleta_incompleta"]
    assert sessao.chamadas[1][0].endswith("/compare/v1...v2")


@pytest.mark.parametrize("lista", [[], [release(1, prerelease=True)]])
def test_sem_releases_estaveis_nao_consulta_api(lista):
    c, sessao = cliente([])
    dados = coletar_repositorio(c, {**REPO, "releases": lista}, INICIO, FIM)
    assert dados["total_releases"] == dados["total_comparacoes"] == dados["total_releases_ignoradas"] == 0
    assert sessao.chamadas == []


@pytest.mark.parametrize("pagina_erro", [1, 2])
def test_404_ignora_release_e_continua_par_consecutivo_sem_saltar_base(pagina_erro, caplog):
    respostas = [resposta([ANTERIOR])]
    if pagina_erro == 2:
        respostas.append(resposta(pagina([commit()], 2), proxima=2))
    respostas += [resposta({}, status=404), resposta(pagina([commit(3)]))]
    c, sessao = cliente(respostas)
    dados = coletar_repositorio(c, {**REPO, "releases": [release(1), release(2)]}, INICIO, FIM)
    assert dados["total_releases_ignoradas"] == dados["total_releases_ignoradas_404"] == 1
    assert dados["releases_ignoradas_por_motivo"] == {"compare_inacessivel": 1}
    assert dados["total_comparacoes"] == 1 and dados["coleta_incompleta"]
    assert dados["comparacoes"][0]["commits"] == []
    assert dados["comparacoes"][1]["release_anterior"]["tag_name"] == "v1"
    assert sessao.chamadas[-1][0].endswith("/compare/v1...v2")
    assert "release v1 ignorada no compare (HTTP 404)" in caplog.text


def test_compare_451_tambem_registrado():
    c, _ = cliente([resposta([ANTERIOR]), resposta({}, status=451)])
    dados = coletar_repositorio(c, {**REPO, "releases": [release()]}, INICIO, FIM)
    assert dados["total_releases_ignoradas"] == 1
    assert dados["total_releases_ignoradas_404"] == 0
    assert dados["comparacoes"][0]["detalhe"] == "HTTP 451"


@pytest.mark.parametrize("status", [404, 451])
def test_historico_inacessivel_registra_todas_as_releases_ignoradas(status):
    c, _ = cliente([resposta({}, status=status)])
    dados = coletar_repositorio(c, {**REPO, "releases": [release(1), release(2)]}, INICIO, FIM)
    assert dados["total_releases_ignoradas"] == 2
    assert dados["releases_ignoradas_por_motivo"] == {"historico_releases_inacessivel": 2}
    assert dados["coleta_incompleta"]


def test_compare_incompleto_ignorado_com_commits_parciais_para_auditoria():
    c, _ = cliente([resposta([ANTERIOR]), resposta(pagina([commit()], 2))])
    dados = coletar_repositorio(c, {**REPO, "releases": [release()]}, INICIO, FIM)
    assert dados["total_releases_ignoradas"] == 1 and dados["total_comparacoes"] == 0
    assert dados["comparacoes"][0]["motivo"] == "compare_incompleto"
    assert dados["comparacoes"][0]["total_commits_coletados"] == 1
    assert dados["comparacoes"][0]["commits"] == [commit()]


@pytest.mark.parametrize("status", [403, 500])
@pytest.mark.parametrize("historico", [False, True])
def test_demais_erros_propagados_preservam_saida_anterior(tmp_path, status, historico):
    saida = tmp_path / "raw" / "compare.json"
    gravar_json(saida, {"anterior": True})
    original = saida.read_bytes()
    respostas = ([] if historico else [resposta([ANTERIOR])]) + [resposta({}, status=status)] * 5
    c, _ = cliente(respostas)
    with pytest.raises(requests.HTTPError):
        executar(config(tmp_path), c, [{**REPO, "releases": [release()]}])
    assert saida.read_bytes() == original


def test_consolidado_conta_ignoradas_e_continua_outro_repositorio(tmp_path, monkeypatch, caplog):
    cfg = config(tmp_path)
    repos = [{**REPO, "releases": [release()]}, {**REPO, "id": 11, "full_name": "org/outro", "releases": [release()]}]
    gravar_json(tmp_path / "raw" / "releases.json", {"janela": {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}, "repositorios": repos})
    c, _ = cliente([resposta([ANTERIOR]), resposta({}, status=404), resposta([ANTERIOR]), resposta(pagina([commit()]))])
    monkeypatch.setattr(compare, "LOG_A_CADA", 1)
    with caplog.at_level("INFO"):
        caminho, lista = executar(cfg, c)
    dados = json.loads(caminho.read_text())
    assert dados["total_repositorios"] == dados["total_releases"] == 2
    assert dados["total_releases_ignoradas"] == dados["total_releases_ignoradas_404"] == dados["total_comparacoes"] == 1
    assert dados["repositorios_com_coleta_incompleta"] == 1
    assert dados["comparacoes_acima_250"] == 0 and dados["limite_sem_paginacao"] == 250
    assert dados["repositorios"] == lista
    assert dados["definicao_deploy"] == "release_estavel"
    assert "Compare: 2/2 repositórios avaliados" in caplog.text


def test_retomada_por_pagina_e_reexecucao_reusam_historico_e_compare(tmp_path):
    cfg, repo = config(tmp_path), {**REPO, "releases": [release()]}
    cache_dir = tmp_path / "cache"
    c, _ = cliente([resposta([ANTERIOR]), resposta(pagina([commit()], 2), proxima=2), requests.Timeout("interrupção")], CacheDisco(cache_dir))
    with pytest.raises(requests.Timeout):
        executar(cfg, c, [repo])
    assert not (tmp_path / "raw" / "compare.json").exists()
    assert len(list(cache_dir.rglob("*.json"))) == 2
    c, sessao = cliente([resposta(pagina([commit(2)], 2))], CacheDisco(cache_dir))
    _, lista = executar(cfg, c, [repo])
    assert sessao.chamadas == [(f"https://api.github.com{PATH}", {"per_page": 100, "page": 2})]
    assert lista[0]["comparacoes"][0]["total_commits_coletados"] == 2
    c, sessao = cliente([], CacheDisco(cache_dir))
    _, nova_lista = executar(cfg, c, [repo])
    assert nova_lista == lista and sessao.chamadas == []


def test_consolidado_conta_comparacoes_acima_250(tmp_path):
    commits = [commit(i) for i in range(251)]
    respostas = [resposta([ANTERIOR])] + [
        resposta(pagina(commits[i:i+100], 251), proxima=(i // 100 + 2 if i < 200 else None))
        for i in range(0, 251, 100)]
    c, _ = cliente(respostas)
    caminho, lista = executar(config(tmp_path), c, [{**REPO, "releases": [release()]}])
    assert lista[0]["comparacoes_acima_250"] == 1
    assert json.loads(caminho.read_text())["comparacoes_acima_250"] == 1


def test_404_nao_cacheado_e_comparacao_volta_a_ser_consultada(tmp_path):
    cfg, repo = config(tmp_path), {**REPO, "releases": [release()]}
    cache_dir = tmp_path / "cache"
    c, _ = cliente([resposta([ANTERIOR]), resposta({}, status=404)], CacheDisco(cache_dir))
    _, lista = executar(cfg, c, [repo])
    assert lista[0]["total_releases_ignoradas_404"] == 1
    c, sessao = cliente([resposta(pagina([commit()]))], CacheDisco(cache_dir))
    _, lista = executar(cfg, c, [repo])
    assert lista[0]["total_releases_ignoradas"] == 0
    assert lista[0]["total_comparacoes"] == 1
    assert sessao.chamadas == [(f"https://api.github.com{PATH}", {"per_page": 100, "page": 1})]


def configurar_cli(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(CONFIG.read_text(encoding="utf-8")
                       .replace("raw: data/raw", f"raw: {tmp_path.as_posix()}/raw")
                       .replace("cache: data/cache", f"cache: {tmp_path.as_posix()}/cache"), encoding="utf-8")
    return caminho


def test_cli_executa_apenas_compare_com_cache_e_mostra_totais(tmp_path, monkeypatch, capsys):
    cfg_path = configurar_cli(tmp_path)
    gravar_json(tmp_path / "raw" / "releases.json", {"janela": {"inicio": "2025-10-01T00:00:00Z", "fim_exclusivo": "2026-10-01T00:00:00Z"}, "repositorios": [{**REPO, "releases": [release()]}]})
    sessao = Sessao([resposta([ANTERIOR]), resposta(pagina([commit()]))])
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    monkeypatch.setattr("pipeline.__main__.GitHubClient", lambda token, base, timeout, cache:
                        GitHubClient(token, base, timeout, cache=cache, session=sessao))
    for nome in ("candidatos", "actions", "metadados", "releases", "tags", "workflow_runs"):
        monkeypatch.setattr(f"pipeline.{nome}.executar", lambda *args: pytest.fail("etapa não solicitada"))
    assert main(["--config", str(cfg_path), "--etapas", "compare"]) == 0
    assert "Compare: 1 repositórios, 1 comparações completas, 0 releases ignoradas" in capsys.readouterr().out
    assert (tmp_path / "raw" / "compare.json").is_file()
    assert main(["--config", str(cfg_path), "--etapas", "compare"]) == 0
    assert len(sessao.chamadas) == 2


def test_cli_sem_releases_informa_dependencia(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    assert main(["--config", str(configurar_cli(tmp_path)), "--etapas", "compare"]) == 2
    assert "execute antes a etapa releases" in capsys.readouterr().err


def test_janela_divergente_recusada_antes_de_consultar_api(tmp_path):
    gravar_json(tmp_path / "raw" / "releases.json", {"janela": {}, "repositorios": []})
    c, sessao = cliente([])
    with pytest.raises(ConfigError, match="janela das releases"):
        executar(config(tmp_path), c)
    assert sessao.chamadas == []
