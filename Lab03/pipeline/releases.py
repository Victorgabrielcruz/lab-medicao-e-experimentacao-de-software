"""Coleta paginada de releases publicadas na janela de observação (S01-10)."""

import datetime as dt
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import requests

from pipeline.actions import MOTIVO_INACESSIVEL, STATUS_INACESSIVEL
from pipeline.cache import gravar_json
from pipeline.config import janela_utc
from pipeline.metadados import ARQUIVO_SAIDA as ARQUIVO_METADADOS

ARQUIVO_SAIDA = "releases.json"
PER_PAGE = 100
LOG_A_CADA = 100
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _data_publicacao(release):
    texto = release.get("published_at")
    if texto is None:
        return None
    try:
        data = dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))
        if data.tzinfo is not None:
            return data
    except (AttributeError, ValueError):
        pass
    log.warning("Release %s com published_at inválido: %r", release.get("id"), texto)
    return None


def coletar_repositorio(client, repo, inicio, fim):
    """Percorre todos os links next; a API não filtra por published_at.

    Não interrompe ao encontrar uma release antiga: a ordem da API não garante
    que as publicações seguintes estejam fora da janela. Pré-releases são
    preservadas para as variantes e contadas separadamente das estáveis.
    """
    path = f"/repos/{repo['full_name']}/releases"
    pagina, registros = 1, {}
    while True:
        resposta = client.get_resposta(path, {"per_page": PER_PAGE, "page": pagina})
        for release in resposta.json():
            if release.get("draft") is not False:
                continue
            publicada = _data_publicacao(release)
            if publicada is None or not inicio <= publicada < fim:
                continue
            campos = ("id", "tag_name", "draft", "prerelease", "published_at",
                      "created_at", "target_commitish", "html_url", "name", "body")
            registros.setdefault(release["id"], {campo: release.get(campo) for campo in campos})
        proxima = resposta.links.get("next", {}).get("url")
        if not proxima:
            break
        nova_pagina = int(parse_qs(urlsplit(proxima).query)["page"][0])
        if nova_pagina <= pagina:
            raise ValueError(f"Paginação de releases não avança em {repo['full_name']}.")
        pagina = nova_pagina

    ordenadas = sorted(registros.values(), key=lambda r: (_data_publicacao(r), r["id"]))
    prereleases = sum(r["prerelease"] is True for r in ordenadas)
    return {
        "id": repo["id"], "full_name": repo["full_name"],
        "default_branch": repo.get("default_branch"),
        "total_releases": len(ordenadas), "total_prereleases": prereleases,
        "total_releases_estaveis": sum(r["prerelease"] is False for r in ordenadas),
        "releases": ordenadas,
    }


def carregar_metadados(raw_dir):
    caminho = Path(raw_dir) / ARQUIVO_METADADOS
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa metadados.")
    return json.loads(caminho.read_text(encoding="utf-8"))["repositorios"]


def executar(config, client, repositorios=None):
    """Usa o cliente/cache compartilhado e grava o consolidado atomicamente."""
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
            log.info("Releases: %d/%d repositórios avaliados", i, len(repositorios))
    saida = raw_dir / ARQUIVO_SAIDA
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)},
        "total_avaliados": len(repositorios), "total_repositorios": len(lista),
        "total_releases": sum(r["total_releases"] for r in lista),
        "total_releases_estaveis": sum(r["total_releases_estaveis"] for r in lista),
        "total_prereleases": sum(r["total_prereleases"] for r in lista),
        "repositorios": lista, "descartes": descartes,
    })
    return saida, lista, descartes
