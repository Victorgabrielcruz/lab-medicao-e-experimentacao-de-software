"""Coleta de metadados dos repositórios aprovados no filtro de Actions.

Os metadados são os fatores das análises: estrelas, linguagem principal, idade e
default branch (GET /repos/{owner}/{repo}) e número de contribuidores. Este vem
do Link header de /contributors com per_page=1: o número da página rel="last" é
o total. O parâmetro anon=1 inclui os autores sem conta vinculada; sem ele, o
GitHub só associa a usuários os primeiros 500 e-mails de autor, e a contagem de
repositórios grandes trava perto de 400. Repositórios grandes demais fazem o
GitHub responder 403 nesse endpoint; nesse caso o total fica nulo e o motivo é
registrado.

Cada repositório é salvo em <caminhos.cache>/metadados/<owner>__<repo>.json.
Numa reexecução, os que já estão no cache não são consultados de novo.
"""

import datetime as dt
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests

from pipeline.actions import ARQUIVO_SAIDA as ARQUIVO_ACTIONS
from pipeline.actions import MOTIVO_INACESSIVEL, STATUS_INACESSIVEL
from pipeline.config import janela_utc

ARQUIVO_SAIDA = "metadados.json"
SUBDIR_CACHE = "metadados"
LISTA_GRANDE_DEMAIS = "too large"
LOG_A_CADA = 100

log = logging.getLogger(__name__)


def contar_contribuidores(client, full_name):
    """Devolve (total, observação). O total é None quando a API não informa."""
    try:
        resposta = client.get_resposta(f"/repos/{full_name}/contributors", {"per_page": 1, "anon": 1})
    except requests.HTTPError as exc:
        resposta = exc.response
        if resposta is not None and resposta.status_code == 403 and LISTA_GRANDE_DEMAIS in _mensagem(resposta):
            return None, "lista de contribuidores grande demais para a API"
        raise

    if resposta.status_code == 204:  # repositório sem commits
        return 0, None
    ultima = resposta.links.get("last", {}).get("url")
    if ultima:
        return int(parse_qs(urlparse(ultima).query)["page"][0]), None
    return len(resposta.json()), None


def _mensagem(resposta):
    try:
        return resposta.json().get("message", "")
    except ValueError:
        return ""


def idade_dias(created_at, referencia):
    """Dias completos entre a criação do repositório e a referência (fim da janela)."""
    criado = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return (referencia - criado).days


def coletar_repositorio(client, full_name, referencia):
    repo = client.get(f"/repos/{full_name}")
    contribuidores, observacao = contar_contribuidores(client, full_name)
    dias = idade_dias(repo["created_at"], referencia)
    return {
        "id": repo["id"],
        "full_name": repo["full_name"],
        "estrelas": repo["stargazers_count"],
        "linguagem": repo.get("language"),
        "created_at": repo["created_at"],
        "idade_dias": dias,
        "idade_anos": round(dias / 365.25, 2),
        "default_branch": repo["default_branch"],
        "contribuidores": contribuidores,
        "contribuidores_obs": observacao,
        "coletado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }


def caminho_cache(cache_dir, full_name):
    return Path(cache_dir) / SUBDIR_CACHE / f"{full_name.replace('/', '__')}.json"


def coletar(repositorios, buscar, cache_dir):
    """Devolve (metadados, descartes), consultando a API só para quem não está no cache.

    `buscar(full_name)` deve devolver o dicionário de metadados do repositório.
    Erros HTTP diferentes de 404 e 451 são propagados; o que já foi salvo no
    cache continua lá para a próxima execução.
    """
    metadados, descartes, consultados, do_cache = [], [], 0, 0
    for i, repo in enumerate(repositorios, 1):
        caminho = caminho_cache(cache_dir, repo["full_name"])
        if caminho.is_file():
            metadados.append(json.loads(caminho.read_text(encoding="utf-8")))
            do_cache += 1
            continue
        consultados += 1
        try:
            dados = buscar(repo["full_name"])
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in STATUS_INACESSIVEL:
                raise
            descartes.append({"id": repo["id"], "full_name": repo["full_name"],
                              "motivo": MOTIVO_INACESSIVEL, "detalhe": f"HTTP {status}"})
            continue
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        metadados.append(dados)
        if consultados % LOG_A_CADA == 0:
            log.info("Metadados: %d/%d repositórios", i, len(repositorios))
    log.info("Metadados: %d consultados na API, %d lidos do cache", consultados, do_cache)
    return metadados, descartes


def carregar_aprovados(raw_dir):
    caminho = Path(raw_dir) / ARQUIVO_ACTIONS
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa actions.")
    return json.loads(caminho.read_text(encoding="utf-8"))["repositorios"]


def executar(config, client, repositorios=None):
    """Executa a etapa e grava o consolidado em <caminhos.raw>/metadados.json.

    Sem `repositorios`, lê os aprovados da etapa anterior (actions.json).
    """
    raw_dir = Path(config["caminhos"]["raw"])
    if repositorios is None:
        repositorios = carregar_aprovados(raw_dir)
    _, fim = janela_utc(config)

    metadados, descartes = coletar(
        repositorios, lambda nome: coletar_repositorio(client, nome, fim), config["caminhos"]["cache"],
    )

    saida = raw_dir / ARQUIVO_SAIDA
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "referencia_idade": fim.isoformat(),
        "total_repositorios": len(metadados),
        "sem_contribuidores": sum(m["contribuidores"] is None for m in metadados),
        "repositorios": metadados,
        "descartes": descartes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida, metadados, descartes
