"""Tempo de recuperação por episódios de falha de cada workflow (S01-20)."""

import argparse
import datetime as dt
import json
import logging
import statistics
import sys
from pathlib import Path

from pipeline.cache import gravar_json
from pipeline.cfr import CONCLUSOES_FALHA, CONCLUSOES_SUCESSO
from pipeline.classificacao import classificar_metrica
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_ENTRADA = "workflow_runs.json"
ARQUIVO_SAIDA = "tempo_recuperacao.json"
log = logging.getLogger(__name__)


def _iso(data):
    return data.astimezone(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _data_run(run):
    try:
        data = dt.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        if data.tzinfo is None:
            raise ValueError("data sem fuso horário")
    except (KeyError, ValueError, AttributeError) as exc:
        raise ConfigError(f"created_at inválido no run {run.get('id')}.") from exc
    return data


def _id(run, campo):
    valor = run.get(campo)
    if not isinstance(valor, int) or isinstance(valor, bool) or valor < 1:
        raise ConfigError(f"{campo} ausente ou inválido no run {run.get('id')}.")
    return valor


def _episodio(workflow_id, primeira, fim, sucesso, falhas):
    run_falha, inicio = primeira
    return {"workflow_id": workflow_id, "run_falha_id": run_falha["id"],
            "run_sucesso_id": sucesso["id"] if sucesso is not None else None,
            "inicio": _iso(inicio), "fim": _iso(fim),
            "duracao_horas": (fim - inicio).total_seconds() / 3600,
            "censurado": sucesso is None, "falhas_no_episodio": falhas}


def identificar_episodios(runs, fim):
    """Da primeira falha ao próximo sucesso do mesmo workflow, por created_at.

    Recebe runs já filtrados por branch/evento/início da janela. Conclusions
    ignoradas não iniciam nem encerram episódios. Falhas consecutivas mantêm
    o início original. Runs em/após fim não recuperam episódios da janela.
    """
    ordenados = []
    for run in runs:
        conclusion = run.get("conclusion")
        if conclusion not in CONCLUSOES_FALHA | CONCLUSOES_SUCESSO:
            continue
        data = _data_run(run)
        if data >= fim:
            continue
        ordenados.append((data, _id(run, "id"), _id(run, "workflow_id"), run))
    ordenados.sort(key=lambda item: (item[0], item[1]))
    abertos, episodios, ids = {}, [], set()
    for data, id_run, workflow_id, run in ordenados:
        if id_run in ids:
            continue
        ids.add(id_run)
        if run["conclusion"] in CONCLUSOES_FALHA:
            if workflow_id not in abertos:
                abertos[workflow_id] = [(run, data), 0]
            abertos[workflow_id][1] += 1
        elif workflow_id in abertos:
            primeira, falhas = abertos.pop(workflow_id)
            episodios.append(_episodio(workflow_id, primeira, data, run, falhas))
    for workflow_id, (primeira, falhas) in abertos.items():
        episodios.append(_episodio(workflow_id, primeira, fim, None, falhas))
    return sorted(episodios, key=lambda e: (e["inicio"], e["workflow_id"], e["run_falha_id"]))


def resumir(episodios):
    """Mediana e IQR em horas, somente dos episódios com recuperação observada."""
    duracoes = [e["duracao_horas"] for e in episodios if not e["censurado"]]
    mediana = statistics.median(duracoes) if duracoes else None
    if len(duracoes) > 1:
        q1, _, q3 = statistics.quantiles(duracoes, n=4, method="inclusive")
    else:
        q1 = q3 = mediana
    return {"total_episodios": len(episodios), "episodios_recuperados": len(duracoes),
            "episodios_censurados": len(episodios) - len(duracoes),
            "tempo_recuperacao": mediana, "q1_horas": q1, "q3_horas": q3,
            "iqr_horas": q3 - q1 if mediana is not None else None}


def calcular_repositorio(repo, inicio, fim):
    """Confere o recorte, identifica episódios e mantém o diagnóstico da coleta."""
    branch = repo.get("default_branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ConfigError(f"Default branch ausente nos runs de {repo['full_name']}.")
    runs, ids = [], set()
    fora_recorte = duplicados = ignorados = 0
    for run in repo["workflow_runs"]:
        if run.get("head_branch") != branch or run.get("event") != "push":
            fora_recorte += 1
            continue
        data = _data_run(run)
        if not inicio <= data < fim:
            fora_recorte += 1
            continue
        id_run = _id(run, "id")
        if id_run in ids:
            duplicados += 1
            continue
        ids.add(id_run)
        if run.get("conclusion") not in CONCLUSOES_FALHA | CONCLUSOES_SUCESSO:
            ignorados += 1
        runs.append(run)
    episodios = identificar_episodios(runs, fim)
    resumo = resumir(episodios)
    incompleta = bool(repo.get("coleta_incompleta") or
                      any(m.get("coleta_incompleta") for m in repo.get("meses", [])))
    if incompleta:
        log.warning("%s: tempo de recuperação calculado sobre coleta incompleta; "
                    "episódios e censuras podem estar incompletos.", repo["full_name"])
    return {"id": repo["id"], "full_name": repo["full_name"], "default_branch": branch,
            **resumo, "classe_tempo_recuperacao": classificar_metrica("tempo_recuperacao", resumo["tempo_recuperacao"]),
            "runs_fora_recorte": fora_recorte, "runs_duplicados": duplicados, "runs_ignorados": ignorados,
            "coleta_incompleta": incompleta, "episodios": episodios}


def executar(config, entrada=None, saida=None):
    """Lê o consolidado da S01-18 e grava episódios e estatísticas por repositório."""
    entrada = Path(entrada) if entrada is not None else Path(config["caminhos"]["raw"]) / ARQUIVO_ENTRADA
    saida = Path(saida) if saida is not None else Path(config["caminhos"]["processed"]) / ARQUIVO_SAIDA
    if entrada.resolve() == saida.resolve():
        raise ConfigError("A saída do tempo de recuperação deve ser diferente do arquivo de workflow runs.")
    if not entrada.is_file():
        raise FileNotFoundError(f"{entrada} não encontrado; execute antes a coleta de workflow_runs (S01-18).")
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    inicio, fim = janela_utc(config)
    janela = {"inicio": _iso(inicio), "fim_exclusivo": _iso(fim)}
    if dados.get("janela") != janela:
        raise ConfigError("A janela dos workflow runs não corresponde à janela configurada para a recuperação.")
    lista = [calcular_repositorio(repo, inicio, fim) for repo in dados["repositorios"]]
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origem": str(entrada), "janela": janela,
        "total_repositorios": len(lista),
        "repositorios_com_tempo_recuperacao": sum(r["tempo_recuperacao"] is not None for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "total_episodios": sum(r["total_episodios"] for r in lista),
        "episodios_censurados": sum(r["episodios_censurados"] for r in lista),
        "repositorios": lista,
    })
    return saida, lista


def main(argv=None):
    parser = argparse.ArgumentParser(description="Tempo de recuperação a partir de workflow runs locais.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--entrada", help="JSON dos runs (padrão: caminhos.raw/workflow_runs.json)")
    parser.add_argument("--saida", help="JSON da recuperação (padrão: caminhos.processed/tempo_recuperacao.json)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        saida, lista = executar(load_config(args.config), args.entrada, args.saida)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    recuperados = sum(r["episodios_recuperados"] for r in lista)
    censurados = sum(r["episodios_censurados"] for r in lista)
    print(f"Tempo de recuperação: {len(lista)} repositórios, {recuperados} episódios recuperados, "
          f"{censurados} censurados -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
