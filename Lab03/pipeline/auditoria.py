"""Confere métricas contra os runs de origem, sem regravar/recalcular saídas."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from pipeline.config import ConfigError, janela_utc
from pipeline.workflow_runs import _data, _iso, fatias_mensais


def _exigir(condicao, mensagem):
    if not condicao:
        raise ConfigError(f"Auditoria: {mensagem}")


def _quantil(lista, p):
    if not lista:
        return None
    a = sorted(lista)
    x = (len(a) - 1) * p
    i = int(x)
    return a[i] + (a[min(i + 1, len(a) - 1)] - a[i]) * (x - i)


def _igual(a, b):
    return a == b if a is None or b is None else math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def validar(config, entrada, saida_cfr, saida_recuperacao):
    entrada = Path(entrada)
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    taxas = json.loads(Path(saida_cfr).read_text(encoding="utf-8"))
    tempos = json.loads(Path(saida_recuperacao).read_text(encoding="utf-8"))
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    for documento in (dados, taxas, tempos):
        _exigir(documento["janela"] == janela, "janela divergente")
    for documento in (taxas, tempos):
        _exigir(Path(documento["origem"]).resolve() == entrada.resolve(), "origem divergente")
    identidades = [(r["id"], r["full_name"], r["default_branch"]) for r in dados["repositorios"]]
    _exigir(len(set(r[0] for r in identidades)) == len(identidades), "IDs de repositórios duplicados")
    for documento in (taxas, tempos):
        _exigir([(r["id"], r["full_name"], r["default_branch"]) for r in documento["repositorios"]]
                == identidades, "identidade/ordem de repositórios divergente")
        _exigir(documento["total_repositorios"] == len(identidades), "total de repositórios divergente")
    total_runs = falhas = sucessos = censurados = recuperados = 0
    for repo, taxa, tempo in zip(dados["repositorios"], taxas["repositorios"], tempos["repositorios"]):
        runs, ids = [], set()
        fora = duplicados = 0
        for run in repo["workflow_runs"]:
            if (run.get("head_branch") != repo["default_branch"] or run.get("event") != "push"
                    or not inicio <= _data(run["created_at"]) < fim):
                fora += 1
            elif run["id"] in ids:
                duplicados += 1
            else:
                ids.add(run["id"])
                runs.append(run)
        _exigir(fora == 0 and duplicados == 0, "consolidado contém runs fora do recorte ou duplicados")
        _exigir(repo.get("total_runs", len(runs)) == len(runs), "total de runs divergente")
        total_runs += len(runs)
        c = Counter(r.get("conclusion") for r in runs)
        n_f = sum(c[x] for x in ("failure", "timed_out", "startup_failure"))
        n_s = c["success"]
        falhas += n_f
        sucessos += n_s
        _exigir(taxa["falhas"] == n_f and taxa["sucessos"] == n_s
                and taxa["runs_validos"] == n_f + n_s, "numerador/denominador da CFR divergente")
        _exigir(_igual(taxa["change_failure_rate"], n_f/(n_f+n_s) if n_f+n_s else None), "CFR divergente")
        ignorados = len(runs) - n_f - n_s
        _exigir(taxa["ignorados"] == ignorados and tempo["runs_ignorados"] == ignorados,
                "conclusions ignoradas divergentes")
        incompleta = bool(repo.get("coleta_incompleta") or any(m.get("coleta_incompleta")
                                                            for m in repo.get("meses", [])))
        for resultado in (taxa, tempo):
            _exigir(resultado["coleta_incompleta"] == incompleta, "diagnóstico de incompletude perdido")
            _exigir(resultado["runs_fora_recorte"] == fora and resultado["runs_duplicados"] == duplicados,
                    "recorte/deduplicação divergente")
        # Reconstrução por workflow independente do identificador de episódios de produção.
        grupos = defaultdict(list)
        for run in runs:
            if run.get("conclusion") in ("success", "failure", "timed_out", "startup_failure"):
                grupos[run["workflow_id"]].append(run)
        esperados = []
        for workflow, lista in grupos.items():
            aberto, n = None, 0
            for run in sorted(lista, key=lambda r: (_data(r["created_at"]), r["id"])):
                if run["conclusion"] != "success":
                    aberto = aberto or run
                    n += 1
                elif aberto:
                    esperados.append((workflow, aberto["id"], run["id"], _iso(_data(aberto["created_at"])),
                                      _iso(_data(run["created_at"])), False, n))
                    aberto, n = None, 0
            if aberto:
                esperados.append((workflow, aberto["id"], None, _iso(_data(aberto["created_at"])),
                                  _iso(fim), True, n))
        observados = [(e["workflow_id"], e["run_falha_id"], e["run_sucesso_id"], e["inicio"], e["fim"],
                       e["censurado"], e["falhas_no_episodio"]) for e in tempo["episodios"]]
        _exigir(sorted(observados, key=str) == sorted(esperados, key=str), "episódios/censura divergentes")
        duracoes = []
        for e in tempo["episodios"]:
            duracao = (_data(e["fim"]) - _data(e["inicio"])).total_seconds() / 3600
            _exigir(duracao >= 0 and _igual(e["duracao_horas"], duracao), "duração divergente")
            if not e["censurado"]:
                duracoes.append(duracao)
        q1, q3 = _quantil(duracoes, .25), _quantil(duracoes, .75)
        _exigir(_igual(tempo["tempo_recuperacao"], _quantil(duracoes, .5))
                and _igual(tempo["q1_horas"], q1) and _igual(tempo["q3_horas"], q3)
                and _igual(tempo["iqr_horas"], q3-q1 if duracoes else None), "mediana/IQR divergentes")
        _exigir(tempo["total_episodios"] == len(esperados)
                and tempo["episodios_recuperados"] == len(duracoes)
                and tempo["episodios_censurados"] == len(esperados)-len(duracoes), "totais de episódios divergentes")
        censurados += tempo["episodios_censurados"]
        recuperados += len(duracoes)
        if "meses" in repo:
            _exigir([(m["inicio"], m["fim_exclusivo"]) for m in repo["meses"]]
                    == [(_iso(a), _iso(b)) for a, b in fatias_mensais(inicio, fim)], "cobertura mensal divergente")
    incompletas = sum(r["coleta_incompleta"] for r in taxas["repositorios"])
    for documento in (taxas, tempos):
        _exigir(documento["repositorios_com_coleta_incompleta"] == incompletas, "total de incompletude divergente")
    _exigir(taxas["repositorios_com_cfr"] == sum(r["change_failure_rate"] is not None for r in taxas["repositorios"]),
            "total de CFR calculadas divergente")
    _exigir(tempos["repositorios_com_tempo_recuperacao"] == sum(r["tempo_recuperacao"] is not None
                                                              for r in tempos["repositorios"]),
            "total de recuperações calculadas divergente")
    _exigir(tempos["total_episodios"] == recuperados + censurados
            and tempos["episodios_censurados"] == censurados, "totais globais de episódios divergentes")
    return {"validado": True, "origem": str(entrada.resolve()), "entrada_sha256": hashlib.sha256(entrada.read_bytes()).hexdigest(),
            "total_repositorios": len(identidades), "runs_no_recorte_deduplicados": total_runs,
            "falhas": falhas, "sucessos": sucessos, "runs_validos": falhas + sucessos,
            "repositorios_com_cfr": sum(r["change_failure_rate"] is not None for r in taxas["repositorios"]),
            "repositorios_com_recuperacao": sum(r["tempo_recuperacao"] is not None for r in tempos["repositorios"]),
            "coletas_incompletas": sum(r["coleta_incompleta"] for r in taxas["repositorios"]),
            "episodios_recuperados": recuperados, "episodios_censurados": censurados}
