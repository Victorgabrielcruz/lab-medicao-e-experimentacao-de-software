"""Coleta paginada de releases publicadas para a integração S01-21."""
from pathlib import Path
import requests
from pipeline import workflow_runs
from pipeline.actions import MOTIVO_INACESSIVEL, STATUS_INACESSIVEL
from pipeline.cache import gravar_json
from pipeline.config import janela_utc

ARQUIVO_SAIDA = "releases.json"


def coletar_repositorio(client, repo, inicio, fim):
    pagina, registros = 1, {}
    while True:
        resposta = client.get_resposta(f"/repos/{repo['full_name']}/releases",
                                       {"per_page": 100, "page": pagina})
        lista = resposta.json()
        for release in lista:
            if release.get("draft") is not False or not release.get("published_at"):
                continue
            if inicio <= workflow_runs._data(release["published_at"]) < fim:
                registros.setdefault(release["id"], {k: release.get(k) for k in
                    ("id", "tag_name", "draft", "prerelease", "published_at", "html_url")})
        # Não parar por data: published_at não precisa seguir a ordem de created_at.
        if not resposta.links.get("next"):
            break
        if not lista:
            raise ValueError("Página vazia de releases com indicação de próxima página")
        pagina += 1
    lista = sorted(registros.values(), key=lambda r: (r["published_at"], r["id"]))
    return {"id": repo["id"], "full_name": repo["full_name"], "releases": lista,
            "total_releases": len(lista), "coleta_incompleta": False, "paginas": pagina}


def executar(config, client, repositorios):
    inicio, fim = janela_utc(config)
    lista, descartes = [], []
    for repo in repositorios:
        try:
            lista.append(coletar_repositorio(client, repo, inicio, fim))
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in STATUS_INACESSIVEL:
                raise
            descartes.append({"id": repo["id"], "full_name": repo["full_name"],
                              "motivo": MOTIVO_INACESSIVEL, "detalhe": f"HTTP {status}"})
    saida = Path(config["caminhos"]["raw"]) / ARQUIVO_SAIDA
    gravar_json(saida, {"janela": {"inicio": workflow_runs._iso(inicio),
                                 "fim_exclusivo": workflow_runs._iso(fim)},
                       "repositorios": lista, "descartes": descartes})
    return saida, lista, descartes
