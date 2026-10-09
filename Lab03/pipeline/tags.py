"""Coleta de tags com commit.author.date para a variante de deploy RQ07 (#139)."""

import datetime as dt
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import requests

from pipeline.actions import MOTIVO_INACESSIVEL, STATUS_INACESSIVEL
from pipeline.cache import gravar_json
from pipeline.config import janela_utc
from pipeline.metadados import ARQUIVO_SAIDA as ARQUIVO_METADADOS

ARQUIVO_SAIDA = "tags.json"
PER_PAGE = 100
LOG_A_CADA = 100
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _data(texto):
    try:
        data = dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is not None:
            return data
    except (AttributeError, ValueError):
        pass
    return None


def coletar_commit(client, full_name, sha):
    """Obtém a data do autor pelo SHA; indisponibilidade fica registrada na tag."""
    try:
        dados = client.get(f"/repos/{full_name}/commits/{quote(sha, safe='')}")
    except requests.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status not in STATUS_INACESSIVEL:
            raise
        return None, {"motivo": "commit_inacessivel", "detalhe": f"HTTP {status}"}
    texto = (dados.get("commit", {}).get("author") or {}).get("date")
    if _data(texto) is None:
        return None, {"motivo": "data_commit_invalida", "detalhe": "commit.author.date ausente ou inválida"}
    return texto, None


def coletar_repositorio(client, repo, inicio, fim):
    """Segue todos os links next e filtra pela data do autor, sem inferir ordem."""
    full_name = repo["full_name"]
    path = f"/repos/{full_name}/tags"
    pagina, vistas, commits, retidas, ignoradas = 1, set(), {}, [], []
    while True:
        resposta = client.get_resposta(path, {"per_page": PER_PAGE, "page": pagina})
        for tag in resposta.json():
            nome, sha = tag["name"], tag["commit"]["sha"]
            if nome in vistas:
                continue
            vistas.add(nome)
            if sha not in commits:
                commits[sha] = coletar_commit(client, full_name, sha)
            texto, erro = commits[sha]
            if erro is not None:
                ignoradas.append({"name": nome, "commit_sha": sha, **erro})
                log.warning("%s: tag %s ignorada: %s", full_name, nome, erro["detalhe"])
                continue
            if not inicio <= _data(texto) < fim:
                continue
            retidas.append({
                "name": nome, "commit_sha": sha, "commit_author_date": texto,
                "commit_url": tag["commit"].get("url"), "node_id": tag.get("node_id"),
                "zipball_url": tag.get("zipball_url"), "tarball_url": tag.get("tarball_url"),
            })
        proxima = resposta.links.get("next", {}).get("url")
        if not proxima:
            break
        nova_pagina = int(parse_qs(urlsplit(proxima).query)["page"][0])
        if nova_pagina <= pagina:
            raise ValueError(f"Paginação de tags não avança em {full_name}.")
        pagina = nova_pagina

    retidas.sort(key=lambda t: (_data(t["commit_author_date"]), t["name"]))
    return {
        "id": repo["id"], "full_name": full_name, "default_branch": repo.get("default_branch"),
        "total_tags": len(retidas), "tags": retidas, "tags_ignoradas": ignoradas,
        "coleta_incompleta": bool(ignoradas),
    }


def carregar_metadados(raw_dir):
    caminho = Path(raw_dir) / ARQUIVO_METADADOS
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa metadados.")
    return json.loads(caminho.read_text(encoding="utf-8"))["repositorios"]


def executar(config, client, repositorios=None):
    """Usa o cache de páginas/commits e grava o consolidado atomicamente."""
    raw_dir = Path(config["caminhos"]["raw"])
    if repositorios is None:
        repositorios = carregar_metadados(raw_dir)
    inicio, fim = janela_utc(config)
    lista, descartes = [], []
    for i, repo in enumerate(repositorios, 1):
        try:
            lista.append(coletar_repositorio(client, repo, inicio, fim))
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in STATUS_INACESSIVEL:
                raise
            descartes.append({"id": repo["id"], "full_name": repo["full_name"],
                              "motivo": MOTIVO_INACESSIVEL, "detalhe": f"HTTP {status}"})
        if i % LOG_A_CADA == 0:
            log.info("Tags: %d/%d repositórios avaliados", i, len(repositorios))
    saida = raw_dir / ARQUIVO_SAIDA
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)},
        "data_referencia": "commit.author.date",
        "total_avaliados": len(repositorios), "total_repositorios": len(lista),
        "total_tags": sum(r["total_tags"] for r in lista),
        "total_tags_ignoradas": sum(len(r["tags_ignoradas"]) for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "repositorios": lista, "descartes": descartes,
    })
    return saida, lista, descartes
