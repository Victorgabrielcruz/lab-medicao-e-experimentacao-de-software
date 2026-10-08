"""Subdivide meses saturados sem alterar o coletor mensal do piloto (#149)."""
import datetime as dt
import math
from pipeline import workflow_runs as wr
from pipeline.config import ConfigError


def coletar_intervalo(client, nome, branch, inicio, fim):
    params = {"branch": branch, "event": "push", "per_page": wr.PER_PAGE, "page": 1,
              "created": f"{wr._iso(inicio)}..{wr._iso(fim - dt.timedelta(seconds=1))}"}
    path = f"/repos/{nome}/actions/runs"
    primeira = client.get(path, params)
    total = primeira["total_count"]
    if total > wr.LIMITE_API and (fim - inicio).total_seconds() > 1:
        segundos = int((fim - inicio).total_seconds()) // 2
        meio = inicio + dt.timedelta(seconds=segundos)
        esquerda, runs_e = coletar_intervalo(client, nome, branch, inicio, meio)
        direita, runs_d = coletar_intervalo(client, nome, branch, meio, fim)
        registros = {r["id"]: r for r in runs_e + runs_d}
        filhos = esquerda + direita
        return [{"inicio": wr._iso(inicio), "fim_exclusivo": wr._iso(fim),
                 "total_api": total, "subdividido": True,
                 "coleta_incompleta": len(registros) != total or any(f["coleta_incompleta"] for f in filhos),
                 "fatias": filhos}], list(registros.values())
    registros = {r["id"]: r for r in primeira["workflow_runs"][:wr.LIMITE_API]}
    for pagina in range(2, math.ceil(min(total, wr.LIMITE_API) / wr.PER_PAGE) + 1):
        lista = client.get(path, {**params, "page": pagina})["workflow_runs"]
        if not lista:
            break
        for run in lista:
            registros.setdefault(run["id"], run)
    retidos = [wr._resumo(r) for r in registros.values()
               if r.get("head_branch") == branch and r.get("event") == "push"
               and inicio <= wr._data(r["created_at"]) < fim]
    return [{"inicio": wr._iso(inicio), "fim_exclusivo": wr._iso(fim), "total_api": total,
             "coletados_api": len(registros), "runs_retidos": len(retidos),
             "limite_atingido": total >= wr.LIMITE_API, "subdividido": False,
             "coleta_incompleta": total > wr.LIMITE_API or len(registros) < total}], retidos


def coletar_repositorio(client, repo, inicio, fim, anterior=None):
    branch = repo.get("default_branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ConfigError(f"Default branch ausente em {repo['full_name']}")
    meses, runs = [], {}
    for comeco, limite in wr.fatias_mensais(inicio, fim):
        mes_antigo = next((m for m in (anterior or {}).get("meses", [])
                          if m["inicio"] == wr._iso(comeco)
                          and m["fim_exclusivo"] == wr._iso(limite)
                          and not m["coleta_incompleta"]), None)
        if mes_antigo is not None:
            lista = [r for r in anterior["workflow_runs"]
                     if comeco <= wr._data(r["created_at"]) < limite]
            meses.append(mes_antigo)
        else:
            fatias, lista = coletar_intervalo(client, repo["full_name"], branch, comeco, limite)
            if len(fatias) == 1:
                mes = fatias[0]
            else:
                raise AssertionError("intervalo raiz deve ter um diagnóstico")
            meses.append(mes)
        for run in lista:
            runs.setdefault(run["id"], run)
    ordenados = sorted(runs.values(), key=lambda r: (wr._data(r["created_at"]), r["id"]))
    return {"id": repo["id"], "full_name": repo["full_name"], "default_branch": branch,
            "total_runs": len(ordenados), "coleta_incompleta": any(m["coleta_incompleta"] for m in meses),
            "meses": meses, "workflow_runs": ordenados}
