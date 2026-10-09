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
    _exigir(tempos.get("versao_metrica") == "rq04-updated-at-run-started-at-v2", "versão de recuperação não conforme RQ04")
    _exigir(tempos.get("formula") == "success.updated_at - first_failure.run_started_at", "fórmula de recuperação divergente")
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
        esperados, iniciais, invalidos, fora_inicio = [], [], {}, []
        for workflow, lista in sorted(grupos.items()):
            registros, erros = [], []
            for run in lista:
                try:
                    comeco = _data(run.get("run_started_at"))
                    termino = _data(run.get("updated_at")) if run["conclusion"] == "success" else None
                    if (comeco.tzinfo is None or comeco < _data(run["created_at"])
                            or (termino is not None and (termino.tzinfo is None or termino < comeco))):
                        raise ValueError("timestamp inválido")
                    if comeco >= fim:
                        fora_inicio.append(run["id"])
                    else:
                        registros.append((comeco, run["id"], run, termino))
                except (ValueError, AttributeError, TypeError):
                    erros.append(run["id"])
            if erros:
                invalidos[workflow] = sorted(erros)
                continue
            sucesso_anterior = False
            aberto, n, prefixo = None, 0, []
            for comeco, _, run, termino in sorted(registros, key=lambda r: (r[0], r[1])):
                if run["conclusion"] != "success":
                    if sucesso_anterior:
                        aberto = aberto or (run, comeco)
                        n += 1
                    else:
                        prefixo.append(run["id"])
                else:
                    if prefixo:
                        iniciais.append({"workflow_id": workflow, "run_falha_ids": prefixo,
                                         "run_sucesso_id": run["id"] if termino < fim else None,
                                         "censura_esquerda": True, "duracao_horas": None})
                        prefixo = []
                    if aberto:
                        if termino >= fim:
                            break
                        esperados.append((workflow, aberto[0]["id"], run["id"], _iso(aberto[1]),
                                          _iso(termino), False, n))
                        aberto, n = None, 0
                    if termino < fim:
                        sucesso_anterior = True
            if aberto:
                esperados.append((workflow, aberto[0]["id"], None, _iso(aberto[1]), _iso(fim), True, n))
            if prefixo:
                iniciais.append({"workflow_id": workflow, "run_falha_ids": prefixo,
                                 "run_sucesso_id": None, "censura_esquerda": True, "duracao_horas": None})
        _exigir(tempo["historico_inicial_nao_observado"] == iniciais, "censuras à esquerda divergentes")
        diag_invalidos = tempo["workflows_com_dados_temporais_invalidos"]
        _exigir(len(diag_invalidos) == len(invalidos) and
                {r["workflow_id"]: sorted(x["run_id"] for x in r["runs_invalidos"]) for r in diag_invalidos}
                == invalidos, "diagnósticos temporais divergentes")
        _exigir(tempo["runs_iniciados_fora_janela"] == sorted(fora_inicio)
                and tempo["dados_temporais_incompletos"] == bool(invalidos or fora_inicio),
                "incompletude temporal perdida")
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
        _exigir(_igual(tempo["proporcao_censurados"], (len(esperados)-len(duracoes))/len(esperados) if esperados else None),
                "proporção de censurados divergente")
        mediana = _quantil(duracoes, .5)
        classe = None if mediana is None else ("Elite" if mediana < 1 else "High" if mediana < 24 else "Medium" if mediana < 168 else "Low")
        _exigir(tempo["classe_tempo_recuperacao"] == classe, "classe de recuperação divergente")
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
    _exigir(tempos["total_sequencias_com_censura_esquerda"] == sum(len(r["historico_inicial_nao_observado"]) for r in tempos["repositorios"]), "total de censuras à esquerda divergente")
    _exigir(tempos["repositorios_com_dados_temporais_incompletos"] == sum(r["dados_temporais_incompletos"] for r in tempos["repositorios"]), "total de incompletude temporal divergente")
    return {"validado": True, "versao_recuperacao": tempos["versao_metrica"],
            "sequencias_com_censura_esquerda": tempos["total_sequencias_com_censura_esquerda"],
            "repositorios_com_dados_temporais_incompletos": tempos["repositorios_com_dados_temporais_incompletos"],
            "origem": str(entrada.resolve()), "entrada_sha256": hashlib.sha256(entrada.read_bytes()).hexdigest(),
            "total_repositorios": len(identidades), "runs_no_recorte_deduplicados": total_runs,
            "falhas": falhas, "sucessos": sucessos, "runs_validos": falhas + sucessos,
            "repositorios_com_cfr": sum(r["change_failure_rate"] is not None for r in taxas["repositorios"]),
            "repositorios_com_recuperacao": sum(r["tempo_recuperacao"] is not None for r in tempos["repositorios"]),
            "coletas_incompletas": sum(r["coleta_incompleta"] for r in taxas["repositorios"]),
            "episodios_recuperados": recuperados, "episodios_censurados": censurados}


def hash_compare(dados):
    """Ignora apenas o instante de gravação; os dados/diagnósticos definem a entrada."""
    conteudo = {k: v for k, v in dados.items() if k != "gerado_em"}
    return hashlib.sha256(json.dumps(conteudo, sort_keys=True).encode()).hexdigest()


def _horas_release(comparacao):
    if (comparacao.get("ignorada") or comparacao.get("coleta_incompleta")
            or comparacao.get("release_anterior") is None):
        return None
    commits = {}
    for commit in comparacao.get("commits", []):
        sha = commit.get("sha")
        if not isinstance(sha, str) or not sha:
            return None
        commits.setdefault(sha, commit)
    if not commits or any(comparacao.get(k) is not None and comparacao[k] != len(commits)
                          for k in ("total_commits_api", "total_commits_coletados")):
        return None
    datas = []
    for commit in commits.values():
        try:
            data = _data(((commit.get("commit") or {}).get("author") or {}).get("date"))
        except (AttributeError, ValueError, TypeError):
            return None
        if data.tzinfo is None:
            return None
        datas.append(data)
    horas = (_data(comparacao["release"]["published_at"]) - min(datas)).total_seconds() / 3600
    return horas if horas >= 0 else None


def validar_lead_time(config, entrada, saida, conferir_classificacao=True):
    """Confere RQ02a com os commits de origem, sem chamar o cálculo de produção."""
    from pipeline.classificacao import classificar_metrica
    entrada = Path(entrada)
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    metrica = json.loads(Path(saida).read_text(encoding="utf-8"))
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    for documento in (dados, metrica):
        _exigir(documento["janela"] == janela, "janela de lead time divergente")
        _exigir(documento["definicao_deploy"] == "release_estavel", "política de lead time divergente")
    _exigir(Path(metrica["origem"]).resolve() == entrada.resolve(), "origem de lead time divergente")
    if conferir_classificacao:
        _exigir(metrica.get("versao_classificacao") == "lab03-enunciado-cortes-v2", "versão de classificação divergente")
    _exigir(metrica["variante"] == "a" and metrica["unidade"] == "horas", "variante/unidade divergente")
    identidades = [(r["id"], r["full_name"], r.get("default_branch")) for r in dados["repositorios"]]
    _exigir(len({r[0] for r in identidades}) == len(identidades), "IDs de compare duplicados")
    _exigir([(r["id"], r["full_name"], r.get("default_branch")) for r in metrica["repositorios"]]
            == identidades, "identidades de lead time divergentes")
    totais = valores = incompletas = calculados = 0
    for repo, resultado in zip(dados["repositorios"], metrica["repositorios"]):
        comparacoes, ids = [], set()
        for c in repo["comparacoes"]:
            r = c["release"]
            _exigir(inicio <= _data(r["published_at"]) < fim and r["id"] not in ids,
                    "compare fora da janela ou duplicado")
            ids.add(r["id"])
            comparacoes.append(c)
        comparacoes.sort(key=lambda c: (_data(c["release"]["published_at"]), c["release"]["id"]))
        _exigir([r["release"] for r in resultado["releases"]] == [c["release"] for c in comparacoes],
                "releases de lead time divergentes")
        horas = [_horas_release(c) for c in comparacoes]
        for h, release in zip(horas, resultado["releases"]):
            _exigir(_igual(release["lead_time_horas"], h), "lead time por release divergente")
            _exigir(release["ignorada"] == (h is None), "descarte de lead time divergente")
        validos = [h for h in horas if h is not None]
        mediana = _quantil(validos, .5)
        _exigir(_igual(resultado["lead_time_horas"], mediana), "mediana de lead time divergente")
        if conferir_classificacao:
            _exigir(resultado["classe_lead_time"] == classificar_metrica("lead_time", mediana),
                    "classe de lead time divergente")
        _exigir(resultado["total_releases"] == len(horas)
                and resultado["releases_com_lead_time"] == len(validos)
                and resultado["releases_ignoradas"] == len(horas)-len(validos), "contagens de lead time divergentes")
        incompleta = bool(repo.get("coleta_incompleta") or any(c.get("coleta_incompleta") for c in comparacoes)
                     or any(c.get(k) is not None and c[k] != len({r.get("sha") for r in c.get("commits", [])})
                            for c in comparacoes if not c.get("ignorada")
                            for k in ("total_commits_api", "total_commits_coletados")))
        _exigir(resultado["coleta_incompleta"] == incompleta, "incompletude de lead time perdida")
        totais += len(horas)
        valores += len(validos)
        incompletas += incompleta
        calculados += mediana is not None
    for campo, valor in (("total_repositorios", len(identidades)), ("total_releases", totais),
                         ("releases_com_lead_time", valores), ("releases_ignoradas", totais-valores),
                         ("repositorios_com_coleta_incompleta", incompletas), ("repositorios_com_lead_time", calculados)):
        _exigir(metrica[campo] == valor, f"total de lead time divergente: {campo}")
    return {"origem": str(entrada.resolve()), "entrada_semantica_sha256": hash_compare(dados),
            "versao_classificacao": metrica.get("versao_classificacao"),
            "total_repositorios": len(identidades), "releases_com_lead_time": valores,
            "repositorios_com_lead_time": calculados, "coletas_incompletas": incompletas}
