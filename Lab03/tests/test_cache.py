import json
from pathlib import Path

import pytest
import requests

from pipeline import actions, cache as modulo_cache
from pipeline.__main__ import main
from pipeline.cache import CacheDisco, gravar_json
from pipeline.github_api import GitHubClient
from pipeline.metadados import contar_contribuidores

CONFIG = Path(__file__).resolve().parents[1] / "config.yaml"


def resposta(corpo=None, status=200, headers=None):
    r = requests.Response()
    r.status_code = status
    r._content = b"" if status == 204 else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    r.encoding = "utf-8"
    r.headers.update(headers or {})
    return r


class Sessao:
    def __init__(self, respostas=()):
        self.headers = {}
        self.respostas = iter(respostas)
        self.chamadas = []

    def get(self, url, params, timeout):
        self.chamadas.append((url, params))
        return next(self.respostas)


def cliente(tmp_path, respostas=()):
    sessao = Sessao(respostas)
    return GitHubClient("token-secreto-de-teste", session=sessao, cache=CacheDisco(tmp_path)), sessao


def test_reexecucao_le_do_disco_sem_rede_e_sem_persistir_token(tmp_path):
    url = "https://api.github.com/repos/org/projeto"
    corpo = {"nome": "medição", "language": None}
    primeiro, sessao = cliente(tmp_path, [resposta(corpo, headers={"Authorization": "segredo"})])
    assert primeiro.get("/repos/org/projeto") == corpo
    assert len(sessao.chamadas) == 1

    outro, sem_rede = cliente(tmp_path)
    assert outro.get("/repos/org/projeto") == corpo
    assert sem_rede.chamadas == []
    arquivo = outro.cache.caminho(url)
    assert "repo-org--projeto" in str(arquivo)
    assert "token-secreto-de-teste" not in arquivo.read_text(encoding="utf-8")
    assert "segredo" not in arquivo.read_text(encoding="utf-8")


def test_endpoint_parametros_pagina_repositorio_e_api_nao_colidem(tmp_path):
    primeiro, _ = cliente(tmp_path, [resposta({"item": i}) for i in range(6)])
    consultas = [
        ("/repos/org/a/actions/runs", {"page": 1, "branch": "main"}),
        ("/repos/org/a/actions/runs", {"page": 2, "branch": "main"}),
        ("/repos/org/a/actions/runs", {"page": 1, "branch": "dev"}),
        ("/repos/org/a/releases", {"page": 1, "branch": "main"}),
        ("/repos/org/b/actions/runs", {"page": 1, "branch": "main"}),
        ("/search/repositories", {"q": "stars:1000..2000", "page": 1}),
    ]
    for i, (path, params) in enumerate(consultas):
        assert primeiro.get(path, params) == {"item": i}

    outro, sem_rede = cliente(tmp_path)
    for i, (path, params) in enumerate(consultas):
        assert outro.get(path, dict(reversed(list(params.items())))) == {"item": i}
    assert sem_rede.chamadas == []
    assert len(list(tmp_path.rglob("*.json"))) == 6
    publico = "https://api.github.com/repos/org/a"
    enterprise = "https://github.example/api/v3/repos/org/a"
    assert outro.cache.caminho(publico) != outro.cache.caminho(enterprise)


def test_retomada_da_paginacao_apos_falha(tmp_path):
    primeira = {"total_count": 101, "workflows": [{"path": ".github/workflows/test.yml"}] * 100}
    segunda = {"total_count": 101, "workflows": [{"path": ".github/workflows/deploy.yml"}]}
    interrompido, _ = cliente(tmp_path, [resposta(primeira), resposta({"message": "erro"}, status=500)])
    with pytest.raises(requests.HTTPError):
        actions.contar_workflows(interrompido, "org/projeto")

    retomado, sessao = cliente(tmp_path, [resposta(segunda)])
    assert actions.contar_workflows(retomado, "org/projeto") == (101, 101)
    assert sessao.chamadas == [("https://api.github.com/repos/org/projeto/actions/workflows",
                               {"per_page": 100, "page": 2})]


def test_cache_preserva_link_para_contagem_de_contribuidores(tmp_path):
    link = '<https://api.github.com/repos/org/projeto/contributors?page=42>; rel="last"'
    primeiro, _ = cliente(tmp_path, [resposta([{"login": "a"}], headers={"Link": link})])
    assert contar_contribuidores(primeiro, "org/projeto") == (42, None)
    outro, sem_rede = cliente(tmp_path)
    assert contar_contribuidores(outro, "org/projeto") == (42, None)
    assert sem_rede.chamadas == []


def test_cache_preserva_resposta_204(tmp_path):
    primeiro, _ = cliente(tmp_path, [resposta(status=204)])
    assert contar_contribuidores(primeiro, "org/projeto") == (0, None)
    outro, sem_rede = cliente(tmp_path)
    assert contar_contribuidores(outro, "org/projeto") == (0, None)
    assert sem_rede.chamadas == []


@pytest.mark.parametrize("status", [403, 404, 429, 500])
def test_erros_http_nao_sao_cacheados(tmp_path, status):
    c, sessao = cliente(tmp_path, [resposta({"message": "erro"}, status), resposta({"ok": True})])
    with pytest.raises(requests.HTTPError):
        c.get("/repos/org/projeto")
    assert not list(tmp_path.rglob("*.json"))
    assert c.get("/repos/org/projeto") == {"ok": True}
    assert len(sessao.chamadas) == 2


def test_resposta_incompleta_volta_a_api(tmp_path):
    c, sessao = cliente(tmp_path, [resposta({"incomplete_results": True}),
                                 resposta({"incomplete_results": False})])
    assert c.get("/search/repositories")["incomplete_results"]
    assert not list(tmp_path.rglob("*.json"))
    assert not c.get("/search/repositories")["incomplete_results"]
    assert len(sessao.chamadas) == 2


def test_corpo_nao_json_nao_e_cacheado(tmp_path):
    r = resposta()
    r._content = b"<html>indisponivel</html>"
    c, _ = cliente(tmp_path, [r])
    assert c.get_resposta("/repos/org/projeto").content == r.content
    assert not list(tmp_path.rglob("*.json"))
    c.cache.gravar("https://api.github.com/repos/org/projeto", resposta(status=500))
    assert not list(tmp_path.rglob("*.json"))


@pytest.mark.parametrize("conteudo", [b'{"versao":', b"[]", b"{}", b"\xff"])
def test_cache_corrompido_e_recuperado(tmp_path, conteudo, caplog):
    c, sessao = cliente(tmp_path, [resposta({"ok": True})])
    arquivo = c.cache.caminho("https://api.github.com/repos/org/projeto")
    arquivo.parent.mkdir(parents=True)
    arquivo.write_bytes(conteudo)
    assert c.get("/repos/org/projeto") == {"ok": True}
    assert len(sessao.chamadas) == 1
    assert "Cache inválido" in caplog.text
    assert c.cache.ler("https://api.github.com/repos/org/projeto").json() == {"ok": True}


def test_escrita_interrompida_preserva_arquivo_anterior(tmp_path, monkeypatch):
    arquivo = tmp_path / "repo.json"
    gravar_json(arquivo, {"versao": "anterior"})

    def escrita_falha(dados, destino, **kwargs):
        destino.write('{"parcial":')
        raise OSError("disco cheio")

    monkeypatch.setattr(modulo_cache.json, "dump", escrita_falha)
    with pytest.raises(OSError, match="disco cheio"):
        gravar_json(arquivo, {"versao": "nova"})
    assert json.loads(arquivo.read_text(encoding="utf-8")) == {"versao": "anterior"}
    assert list(tmp_path.iterdir()) == [arquivo]


def test_limpar_cache_pelo_cli_sem_token_preserva_dados(tmp_path, monkeypatch, capsys):
    cache_dir = tmp_path / "cache"
    c, _ = cliente(cache_dir, [resposta({"id": 1})])
    c.get("/repos/org/projeto")
    gravar_json(cache_dir / "metadados" / "org__projeto.json", {"id": 1})
    preservados = [cache_dir / "anotacoes.json", cache_dir / "metadados" / "README.md",
                   tmp_path / "raw" / "repositorios.json", tmp_path / "processed" / "dataset.csv"]
    for arquivo in preservados:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text("preservar", encoding="utf-8")
    config = tmp_path / "config.yaml"
    config.write_text(CONFIG.read_text(encoding="utf-8").replace("cache: data/cache",
                      f"cache: {cache_dir.as_posix()}"), encoding="utf-8")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    assert main(["--config", str(config), "--limpar-cache"]) == 0
    assert "2 arquivos removidos" in capsys.readouterr().out
    assert not list((cache_dir / "respostas").rglob("*.json"))
    assert not list((cache_dir / "metadados").rglob("*.json"))
    assert all(a.read_text(encoding="utf-8") == "preservar" for a in preservados)
    assert c.cache.limpar() == 0
    assert CacheDisco(tmp_path / "inexistente").limpar() == 0


def test_limpeza_recusa_area_fora_do_cache(tmp_path, monkeypatch):
    raiz = tmp_path / "cache"
    fora = tmp_path / "externo"
    gravar_json(fora / "preservar.json", {"id": 1})
    resolver = Path.resolve

    def resolver_falso(path, *args, **kwargs):
        if path == raiz / "respostas":
            return fora
        return resolver(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolver_falso)
    with pytest.raises(ValueError, match="fora do diretório"):
        CacheDisco(raiz).limpar()
    assert (fora / "preservar.json").is_file()


def test_cli_habilita_cache_nas_etapas(tmp_path, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_text(CONFIG.read_text(encoding="utf-8").replace("cache: data/cache",
                      f"cache: {tmp_path.as_posix()}/cache"), encoding="utf-8")
    monkeypatch.setenv("GITHUB_TOKEN", "token-falso")

    def etapa(config, client):
        assert isinstance(client.cache, CacheDisco)
        assert client.cache.diretorio == tmp_path / "cache"
        return Path("actions.json"), [], []

    monkeypatch.setattr(actions, "executar", etapa)
    assert main(["--config", str(config), "--etapas", "actions"]) == 0
