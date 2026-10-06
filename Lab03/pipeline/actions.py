"""Filtro de repositórios sem GitHub Actions.

Para cada candidato, consulta o endpoint de workflows e descarta os que não têm
nenhum workflow definido pelo próprio repositório (.github/workflows/). O
total_count do endpoint não basta: ele inclui workflows dinâmicos criados pelo
GitHub (Dependabot, Dependency Graph, CodeQL, Pages, Copilot), cujo path começa
com "dynamic/" e que aparecem mesmo em repositórios que não usam Actions.

Repositórios que deixaram de existir ou foram bloqueados desde a busca (404 e
451) também são descartados. Cada descarte guarda o motivo para a tabela do
funil de seleção.
"""

import datetime as dt
import json
import logging
from pathlib import Path

import requests

from pipeline.candidatos import ARQUIVO_SAIDA as ARQUIVO_CANDIDATOS

ARQUIVO_SAIDA = "actions.json"
MOTIVO_SEM_ACTIONS = "sem_github_actions"
MOTIVO_INACESSIVEL = "repositorio_inacessivel"
STATUS_INACESSIVEL = (404, 451)
LOG_A_CADA = 100
PER_PAGE = 100
PREFIXO_PROPRIO = ".github/workflows/"

log = logging.getLogger(__name__)


def contar_workflows(client, full_name):
    """Devolve (total_count, workflows próprios) do repositório.

    Uma requisição basta para quase todos os repositórios; as páginas seguintes só
    são pedidas quando há mais de 100 workflows.
    """
    total, proprios, pagina = 0, 0, 1
    while True:
        resposta = client.get(f"/repos/{full_name}/actions/workflows", {"per_page": PER_PAGE, "page": pagina})
        total = resposta["total_count"]
        proprios += sum(w["path"].startswith(PREFIXO_PROPRIO) for w in resposta["workflows"])
        if not resposta["workflows"] or pagina * PER_PAGE >= total:
            return total, proprios
        pagina += 1


def filtrar(candidatos, contar):
    """Separa os candidatos em (aprovados, descartes).

    `contar(full_name)` deve devolver (total_count, workflows próprios).
    Erros HTTP diferentes de 404 e 451 são propagados.
    """
    aprovados, descartes = [], []
    for i, repo in enumerate(candidatos, 1):
        try:
            total, proprios = contar(repo["full_name"])
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status not in STATUS_INACESSIVEL:
                raise
            descartes.append(_descarte(repo, MOTIVO_INACESSIVEL, f"HTTP {status}"))
        else:
            if proprios == 0:
                detalhe = f"nenhum workflow em {PREFIXO_PROPRIO} (total_count = {total})"
                descartes.append(_descarte(repo, MOTIVO_SEM_ACTIONS, detalhe))
            else:
                aprovados.append({**repo, "total_workflows": total, "workflows_proprios": proprios})
        if i % LOG_A_CADA == 0:
            log.info("Actions: %d/%d avaliados, %d aprovados", i, len(candidatos), len(aprovados))
    return aprovados, descartes


def _descarte(repo, motivo, detalhe):
    return {"id": repo["id"], "full_name": repo["full_name"], "motivo": motivo, "detalhe": detalhe}


def carregar_candidatos(raw_dir):
    caminho = Path(raw_dir) / ARQUIVO_CANDIDATOS
    if not caminho.is_file():
        raise FileNotFoundError(f"{caminho} não encontrado; execute antes a etapa candidatos.")
    return json.loads(caminho.read_text(encoding="utf-8"))["candidatos"]


def executar(config, client, candidatos=None):
    """Executa a etapa e grava o resultado em <caminhos.raw>/actions.json.

    Sem `candidatos`, lê a saída da etapa anterior (candidatos.json).
    """
    raw_dir = Path(config["caminhos"]["raw"])
    if candidatos is None:
        candidatos = carregar_candidatos(raw_dir)

    aprovados, descartes = filtrar(candidatos, lambda nome: contar_workflows(client, nome))

    motivos = {}
    for d in descartes:
        motivos[d["motivo"]] = motivos.get(d["motivo"], 0) + 1

    saida = raw_dir / ARQUIVO_SAIDA
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps({
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "total_avaliados": len(candidatos),
        "total_aprovados": len(aprovados),
        "descartes_por_motivo": motivos,
        "repositorios": aprovados,
        "descartes": descartes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida, aprovados, descartes
