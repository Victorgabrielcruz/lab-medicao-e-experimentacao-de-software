import json
from pathlib import Path

import pytest
import requests

from pipeline.__main__ import main, parse_args, preparar_piloto
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import load_config
from pipeline.github_api import GitHubClient

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def candidatos():
    return [{"id": i, "full_name": f"org/repo{i}", "estrelas": 1000 - i,
             "html_url": f"https://github.com/org/repo{i}", "linguagem": "Python"}
            for i in range(1, 4)]


def configurar(tmp_path):
    caminho = tmp_path / "config.yaml"
    caminho.write_text(CONFIG.read_text(encoding="utf-8")
                       .replace("raw: data/raw", f"raw: {tmp_path.as_posix()}/raw")
                       .replace("cache: data/cache", f"cache: {tmp_path.as_posix()}/cache"), encoding="utf-8")
    return caminho


@pytest.mark.parametrize("limite,esperado", [(2, 2), (10, 3)])
def test_preparacao_limita_e_preserva_busca_saidas_e_cache(tmp_path, limite, esperado):
    cfg = load_config(configurar(tmp_path))
    raw = tmp_path / "raw"
    fonte = raw / "candidatos.json"
    gravar_json(fonte, {"candidatos": candidatos(), "total_candidatos": 3})
    gravar_json(raw / "actions.json", {"anterior": True})
    original = fonte.read_bytes()
    piloto = preparar_piloto(cfg, limite)
    dados = json.loads((raw / f"piloto-{limite}" / "candidatos.json").read_text(encoding="utf-8"))
    assert dados["total_candidatos"] == esperado
    assert dados["candidatos"] == candidatos()[:limite]
    assert dados["total_candidatos_origem"] == 3
    assert fonte.read_bytes() == original
    assert json.loads((raw / "actions.json").read_text()) == {"anterior": True}
    assert piloto["caminhos"]["cache"] == cfg["caminhos"]["cache"]
    assert Path(cfg["caminhos"]["raw"]) == raw


@pytest.mark.parametrize("valor", ["0", "-1", "abc"])
def test_cli_recusa_limite_invalido(valor):
    with pytest.raises(SystemExit) as erro:
        parse_args(["--piloto", valor])
    assert erro.value.code == 2


@pytest.mark.parametrize("extras", [["--limpar-cache"], ["--etapas", "workflow_runs"]])
def test_cli_recusa_combinacoes_ambiguas(extras):
    with pytest.raises(SystemExit) as erro:
        parse_args(["--piloto", "100", *extras])
    assert erro.value.code == 2


def test_piloto_sem_busca_existente_exibe_dependencia(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    assert main(["--config", str(configurar(tmp_path)), "--piloto", "100"]) == 2
    assert "execute antes a etapa candidatos" in capsys.readouterr().err


def resposta(corpo):
    r = requests.Response()
    r.status_code = 200
    r._content = json.dumps(corpo).encode()
    return r


def test_piloto_integra_coleta_limitada_sem_busca_reutilizando_cache(tmp_path, monkeypatch, capsys):
    cfg_path = configurar(tmp_path)
    gravar_json(tmp_path / "raw" / "candidatos.json", {"candidatos": candidatos()})
    cache = CacheDisco(tmp_path / "cache")
    for i in (1, 2):
        url = requests.Request("GET", f"https://api.github.com/repos/org/repo{i}/actions/workflows",
                               params={"per_page": 100, "page": 1}).prepare().url
        workflows = [{"path": ".github/workflows/ci.yml"}] if i == 1 else []
        cache.gravar(url, resposta({"total_count": len(workflows), "workflows": workflows}))

    class Sessao:
        def __init__(self):
            self.headers = {}
            self.chamadas = []

        def get(self, url, params, timeout):
            self.chamadas.append(url)
            assert url.startswith("https://api.github.com/repos/org/repo1")
            if url.endswith("/contributors"):
                return resposta([{"login": "autor"}])
            if url.endswith("/actions/runs"):
                return resposta({"total_count": 0, "workflow_runs": []})
            if url.endswith("/releases"):
                return resposta([])
            if url.endswith("/tags"):
                return resposta([{"name": "v1.0", "commit": {"sha": "abc"}}])
            if url.endswith("/commits/abc"):
                return resposta({"commit": {"author": {"date": "2025-10-10T00:00:00Z"}}})
            assert url.endswith("/repos/org/repo1")
            return resposta({"id": 1, "full_name": "org/repo1", "stargazers_count": 999,
                             "created_at": "2020-01-01T00:00:00Z", "default_branch": "main"})

    sessao = Sessao()
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")
    monkeypatch.setattr("pipeline.candidatos.executar", lambda *args: pytest.fail("busca não deve ser repetida"))
    monkeypatch.setattr("pipeline.__main__.GitHubClient", lambda token, base, timeout, cache:
                        GitHubClient(token, base, timeout, cache=cache, session=sessao))
    assert main(["--config", str(cfg_path), "--piloto", "2"]) == 0
    pasta = tmp_path / "raw" / "piloto-2"
    actions = json.loads((pasta / "actions.json").read_text())
    runs = json.loads((pasta / "workflow_runs.json").read_text())
    releases = json.loads((pasta / "releases.json").read_text())
    tags = json.loads((pasta / "tags.json").read_text())
    assert actions["total_avaliados"] == 2
    assert actions["total_aprovados"] == runs["total_repositorios"] == releases["total_repositorios"] == 1
    assert tags["total_repositorios"] == tags["total_tags"] == 1
    assert len(sessao.chamadas) == 17  # Metadados, releases, tags/commit e 12 meses; Actions no cache.
    assert "cache compartilhado" in capsys.readouterr().out
    assert not (tmp_path / "raw" / "workflow_runs.json").exists()
    assert not (tmp_path / "raw" / "releases.json").exists()
    assert not (tmp_path / "raw" / "tags.json").exists()

    sessao.chamadas.clear()
    assert main(["--config", str(cfg_path), "--piloto", "2"]) == 0
    assert sessao.chamadas == []
