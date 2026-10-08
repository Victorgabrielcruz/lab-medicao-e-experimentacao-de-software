"""Coleta mensal de workflow runs do default branch, com event=push (S01-18)."""

import datetime as dt
import json
import logging
import math
from pathlib import Path

import requests

from pipeline.actions import MOTIVO_INACESSIVEL, STATUS_INACESSIVEL
from pipeline.cache import gravar_json
from pipeline.config import ConfigError, janela_utc
from pipeline.metadados import ARQUIVO_SAIDA as ARQUIVO_METADADOS

ARQUIVO_SAIDA = "workflow_runs.json"
PER_PAGE = 100
LIMITE_API = 1000
LOG_A_CADA = 100
log = logging.getLogger(__name__)


def _iso(data):
    return data.isoformat(timespec="seconds").replace("+00:00", "Z")


def _data(texto):
    return dt.datetime.fromisoformat(texto.replace("Z", "+00:00"))


def fatias_mensais(inicio, fim):
    """Divide [início, fim) por meses civis, incluindo pontas parciais."""
    atual = inicio
    while atual < fim:
        if atual.month == 12:
            proximo = atual.replace(year=atual.year + 1, month=1, day=1,
                                   hour=0, minute=0, second=0, microsecond=0)
        else:
            proximo = atual.replace(month=atual.month + 1, day=1,
                                   hour=0, minute=0, second=0, microsecond=0)
        limite = min(proximo, fim)
        yield atual, limite
        atual = limite


def _resumo(run):
    campos = ("id", "workflow_id", "name", "head_branch", "event", "status", "conclusion",
              "created_at", "updated_at", "run_started_at", "head_sha", "run_number",
              "run_attempt", "html_url")
    return {campo: run.get(campo) for campo in campos}


def coletar_mes(client, full_name, branch, inicio, fim):
    """Consulta no máximo dez páginas e registra a completude da fatia."""
    path = f"/repos/{full_name}/actions/runs"
    params = {"branch": branch, "event": "push", "per_page": PER_PAGE,
              "created": f"{_iso(inicio)}..{_iso(fim - dt.timedelta(seconds=1))}", "page": 1}
    primeira = client.get(path, params)
    total = primeira["total_count"]
    limite_atingido = total >= LIMITE_API
    if limite_atingido:
        log.warning("%s: mês iniciado em %s atingiu %d runs (limite %d); "
                    "a coleta mensal pode estar truncada.", full_name, _iso(inicio), total, LIMITE_API)
    paginas = math.ceil(min(total, LIMITE_API) / PER_PAGE)
    registros = {run["id"]: run for run in primeira["workflow_runs"][:LIMITE_API]}
    if primeira["workflow_runs"]:
        for pagina in range(2, paginas + 1):
            resposta = client.get(path, {**params, "page": pagina})
            if not resposta["workflow_runs"]:
                break
            for run in resposta["workflow_runs"]:
                if len(registros) >= LIMITE_API:
                    break
                registros.setdefault(run["id"], run)

    incompleta = total > LIMITE_API or len(registros) < min(total, LIMITE_API)
    if incompleta:
        log.warning("%s: coleta incompleta em %s: %d/%d runs recuperados da API.",
                    full_name, _iso(inicio), len(registros), total)
    retidos = [_resumo(run) for run in registros.values()
               if run.get("head_branch") == branch and run.get("event") == "push"
               and inicio <= _data(run["created_at"]) < fim]
    mes = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim), "total_api": total,
           "coletados_api": len(registros), "runs_retidos": len(retidos),
           "limite_atingido": limite_atingido, "coleta_incompleta": incompleta}
    return mes, retidos


def coletar_repositorio(client, repo, inicio, fim):
    branch = repo.get("default_branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ConfigError(f"Default branch ausente nos metadados de {repo['full_name']}.")
    meses, runs = [], {}
    for comeco, limite in fatias_mensais(inicio, fim):
        mes, lista = coletar_mes(client, repo["full_name"], branch, comeco, limite)
        meses.append(mes)
        for run in lista:
            runs.setdefault(run["id"], run)
    ordenados = sorted(runs.values(), key=lambda run: (_data(run["created_at"]), run["id"]))
    return {"id": repo["id"], "full_name": repo["full_name"], "default_branch": branch,
            "total_runs": len(ordenados), "coleta_incompleta": any(m["coleta_incompleta"] for m in meses),
            "meses": meses, "workflow_runs": ordenados}


def carregar_metadados(raw_dir):
    caminho = Path(raw_dir) / ARQUIVO_METADADOS
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa metadados.")
    return json.loads(caminho.read_text(encoding="utf-8"))["repositorios"]


def executar(config, client, repositorios=None):
    """Lê metadados, coleta com o cliente/cache compartilhado e grava o consolidado."""
    regras = config["runs"]
    if regras.get("evento") != "push" or regras.get("somente_default_branch") is not True:
        raise ConfigError("A coleta de runs exige runs.evento=push e runs.somente_default_branch=true.")
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
            log.info("Workflow runs: %d/%d repositórios avaliados", i, len(repositorios))
    saida = raw_dir / ARQUIVO_SAIDA
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "janela": {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)},
        "total_repositorios": len(lista), "total_runs": sum(r["total_runs"] for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "meses_com_limite_atingido": sum(m["limite_atingido"] for r in lista for m in r["meses"]),
        "repositorios": lista, "descartes": descartes,
    })
    return saida, lista, descartes
