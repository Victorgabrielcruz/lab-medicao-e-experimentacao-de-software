"""Commits entre releases estáveis consecutivas pelo endpoint compare (#140)."""

import datetime as dt
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import requests

from pipeline import releases
from pipeline.actions import STATUS_INACESSIVEL
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, janela_utc

ARQUIVO_SAIDA = "compare.json"
PER_PAGE = 100
LIMITE_SEM_PAGINACAO = 250
LOG_A_CADA = 100
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _release(release):
    return {campo: release.get(campo) for campo in ("id", "tag_name", "published_at", "html_url")}


def _commit(commit):
    dados = commit["commit"]
    return {"sha": commit["sha"], "html_url": commit.get("html_url"),
            "commit": {campo: dados.get(campo) for campo in ("author", "committer", "message")},
            "parents": [{"sha": pai["sha"]} for pai in commit.get("parents", [])]}


def coletar_comparacao(client, full_name, base, head):
    """Sempre pagina; 250 é o limite da consulta sem parâmetros de paginação."""
    path = f"/repos/{full_name}/compare/{quote(base, safe='')}...{quote(head, safe='')}"
    pagina, registros, paginas, totais = 1, {}, [], []
    status = None
    while True:
        resposta = client.get_resposta(path, {"per_page": PER_PAGE, "page": pagina})
        dados = resposta.json()
        if pagina == 1:
            status = dados["status"]
        totais.append(dados["total_commits"])
        paginas.append({"pagina": pagina, "commits_api": len(dados["commits"])})
        for commit in dados["commits"]:
            registros.setdefault(commit["sha"], _commit(commit))
        proxima = resposta.links.get("next", {}).get("url")
        if not proxima:
            break
        nova_pagina = int(parse_qs(urlsplit(proxima).query)["page"][0])
        if nova_pagina <= pagina:
            raise ValueError(f"Paginação do compare não avança em {full_name}: {base}...{head}.")
        pagina = nova_pagina

    superado = max(totais) > LIMITE_SEM_PAGINACAO
    incompleta = len(set(totais)) != 1 or len(registros) != totais[0]
    if superado:
        log.info("%s: %s...%s tem %d commits; limite sem paginação de %d tratado em %d páginas.",
                 full_name, base, head, totais[0], LIMITE_SEM_PAGINACAO, len(paginas))
    if incompleta:
        log.warning("%s: compare incompleto %s...%s: %d/%d commits únicos.",
                    full_name, base, head, len(registros), totais[0])
    return {"status": status, "total_commits_api": totais[0], "total_commits_coletados": len(registros),
            "limite_sem_paginacao": LIMITE_SEM_PAGINACAO, "limite_250_superado": superado,
            "paginas": paginas, "coleta_incompleta": incompleta, "commits": list(registros.values())}


def _ignorada(atual, anterior, motivo, detalhe):
    return {"release": _release(atual), "release_anterior": _release(anterior) if anterior else None,
            "ignorada": True, "motivo": motivo, "detalhe": detalhe,
            "commits": [], "total_commits_coletados": 0, "coleta_incompleta": motivo != "sem_release_anterior"}


def _coletar_release(client, full_name, anterior, atual):
    if anterior is None:
        return _ignorada(atual, None, "sem_release_anterior", "Primeira release estável do histórico.")
    try:
        dados = coletar_comparacao(client, full_name, anterior["tag_name"], atual["tag_name"])
    except requests.HTTPError as exc:
        status = getattr(exc.response, "status_code", None)
        if status not in STATUS_INACESSIVEL:
            raise
        log.warning("%s: release %s ignorada no compare (HTTP %s).", full_name, atual["tag_name"], status)
        return _ignorada(atual, anterior, "compare_inacessivel", f"HTTP {status}")
    incompleta = dados["coleta_incompleta"]
    return {"release": _release(atual), "release_anterior": _release(anterior), "ignorada": incompleta,
            "motivo": "compare_incompleto" if incompleta else None, **dados}


def coletar_repositorio(client, repo, inicio, fim):
    """Mantém a sequência cronológica mesmo quando um compare responde 404."""
    retidas = {}
    for release in repo["releases"]:
        data = releases._data_publicacao(release)
        if (release.get("draft") is False and release.get("prerelease") is False
                and data is not None and inicio <= data < fim):
            retidas.setdefault(release["id"], release)
    atuais = sorted(retidas.values(), key=lambda r: (releases._data_publicacao(r), r["id"]))
    comparacoes, anterior = [], None
    if atuais:
        try:
            historico = releases.coletar_repositorio(
                client, repo, dt.datetime.min.replace(tzinfo=dt.timezone.utc), inicio,
            )["releases"]
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in STATUS_INACESSIVEL:
                raise
            comparacoes = [_ignorada(r, None, "historico_releases_inacessivel", f"HTTP {status}") for r in atuais]
            log.warning("%s: histórico de releases inacessível (HTTP %s).", repo["full_name"], status)
        else:
            estaveis = [r for r in historico if r.get("prerelease") is False]
            anterior = estaveis[-1] if estaveis else None
            for atual in atuais:
                comparacoes.append(_coletar_release(client, repo["full_name"], anterior, atual))
                anterior = atual
    ignoradas = [c for c in comparacoes if c["ignorada"]]
    return {"id": repo["id"], "full_name": repo["full_name"], "default_branch": repo.get("default_branch"),
            "total_releases": len(atuais), "total_comparacoes": sum(not c["ignorada"] for c in comparacoes),
            "total_releases_ignoradas": len(ignoradas),
            "releases_ignoradas_por_motivo": {motivo: sum(c["motivo"] == motivo for c in ignoradas)
                                             for motivo in sorted({c["motivo"] for c in ignoradas})},
            "total_releases_ignoradas_404": sum(c.get("detalhe") == "HTTP 404" for c in ignoradas),
            "comparacoes_acima_250": sum(c.get("limite_250_superado", False) for c in comparacoes),
            "coleta_incompleta": any(c["coleta_incompleta"] for c in comparacoes), "comparacoes": comparacoes}


def carregar_releases(raw_dir, inicio, fim):
    caminho = Path(raw_dir) / releases.ARQUIVO_SAIDA
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa releases.")
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if dados.get("janela") != {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}:
        raise ConfigError("A janela das releases não corresponde à janela configurada para o compare.")
    return dados["repositorios"]


def executar(config, client, repositorios=None):
    """Lê releases da S01-10 e grava commits/diagnósticos atomicamente."""
    raw_dir = Path(config["caminhos"]["raw"])
    inicio, fim = janela_utc(config)
    if repositorios is None:
        repositorios = carregar_releases(raw_dir, inicio, fim)
    lista = []
    for i, repo in enumerate(repositorios, 1):
        lista.append(coletar_repositorio(client, repo, inicio, fim))
        if i % LOG_A_CADA == 0:
            log.info("Compare: %d/%d repositórios avaliados", i, len(repositorios))
    return gravar_consolidado(config, lista, inicio, fim)


def gravar_consolidado(config, lista, inicio, fim):
    """Consolida também registros retomados sem repetir a coleta por repositório."""
    saida = Path(config["caminhos"]["raw"]) / ARQUIVO_SAIDA
    contagens = ("total_releases", "total_comparacoes", "total_releases_ignoradas", "total_releases_ignoradas_404", "comparacoes_acima_250")
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}, "definicao_deploy": "release_estavel",
        "limite_sem_paginacao": LIMITE_SEM_PAGINACAO, "total_repositorios": len(lista),
        **{campo: sum(r[campo] for r in lista) for campo in contagens},
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista), "repositorios": lista,
    })
    return saida, lista
