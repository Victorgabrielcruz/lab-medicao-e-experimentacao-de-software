"""CFR variante (a) a partir dos workflow runs coletados (S01-19)."""

import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

from pipeline.cache import gravar_json
from pipeline.classificacao import classificar_metrica
from pipeline.config import ConfigError, janela_utc, load_config

ARQUIVO_ENTRADA = "workflow_runs.json"
ARQUIVO_SAIDA = "cfr.json"
CONCLUSOES_SUCESSO = frozenset({"success"})
CONCLUSOES_FALHA = frozenset({"failure", "timed_out", "startup_failure"})
log = logging.getLogger(__name__)


def calcular(runs):
    """Conta conclusions e retorna falhas / (falhas + sucessos), ou None.

    Recebe runs já restritos ao default branch, event=push e à janela.
    Conclusions ausentes, nulas ou diferentes das regras são ignoradas.
    A fração é preservada sem arredondamento; não é um percentual.
    """
    falhas = sucessos = ignorados = 0
    for run in runs:
        conclusion = run.get("conclusion")
        if conclusion in CONCLUSOES_FALHA:
            falhas += 1
        elif conclusion in CONCLUSOES_SUCESSO:
            sucessos += 1
        else:
            ignorados += 1
    validos = falhas + sucessos
    return {"falhas": falhas, "sucessos": sucessos, "ignorados": ignorados,
            "runs_validos": validos, "change_failure_rate": falhas / validos if validos else None}


def calcular_repositorio(repo, inicio, fim):
    """Confere o recorte, deduplica IDs e preserva a limitação da coleta."""
    branch = repo.get("default_branch")
    if not isinstance(branch, str) or not branch.strip():
        raise ConfigError(f"Default branch ausente nos runs de {repo['full_name']}.")
    runs, ids = [], set()
    fora_recorte = duplicados = 0
    for run in repo["workflow_runs"]:
        if run.get("head_branch") != branch or run.get("event") != "push":
            fora_recorte += 1
            continue
        try:
            data = dt.datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            if data.tzinfo is None:
                raise ValueError("data sem fuso horário")
        except (KeyError, ValueError, AttributeError) as exc:
            raise ConfigError(f"created_at inválido nos runs de {repo['full_name']}.") from exc
        if not inicio <= data < fim:
            fora_recorte += 1
            continue
        if "id" not in run:
            raise ConfigError(f"Run sem ID em {repo['full_name']}.")
        if run["id"] in ids:
            duplicados += 1
            continue
        ids.add(run["id"])
        runs.append(run)
    contagem = calcular(runs)
    incompleta = bool(repo.get("coleta_incompleta") or
                      any(m.get("coleta_incompleta") for m in repo.get("meses", [])))
    if incompleta:
        log.warning("%s: CFR calculada sobre coleta incompleta; consulte os diagnósticos dos runs.",
                    repo["full_name"])
    return {"id": repo["id"], "full_name": repo["full_name"], "default_branch": branch,
            **contagem, "classe_cfr": classificar_metrica("change_failure_rate", contagem["change_failure_rate"]),
            "runs_fora_recorte": fora_recorte, "runs_duplicados": duplicados,
            "coleta_incompleta": incompleta}


def executar(config, entrada=None, saida=None):
    """Lê o consolidado da S01-18 e grava a CFR por repositório atomicamente."""
    entrada = Path(entrada) if entrada is not None else Path(config["caminhos"]["raw"]) / ARQUIVO_ENTRADA
    saida = Path(saida) if saida is not None else Path(config["caminhos"]["processed"]) / ARQUIVO_SAIDA
    if entrada.resolve() == saida.resolve():
        raise ConfigError("A saída da CFR deve ser diferente do arquivo de workflow runs.")
    if not entrada.is_file():
        raise FileNotFoundError(f"{entrada} não encontrado; execute antes a coleta de workflow_runs (S01-18).")
    dados = json.loads(entrada.read_text(encoding="utf-8"))
    inicio, fim = janela_utc(config)
    janela = {"inicio": inicio.isoformat(timespec="seconds").replace("+00:00", "Z"),
              "fim_exclusivo": fim.isoformat(timespec="seconds").replace("+00:00", "Z")}
    if dados.get("janela") != janela:
        raise ConfigError("A janela dos workflow runs não corresponde à janela configurada para a CFR.")
    lista = [calcular_repositorio(repo, inicio, fim) for repo in dados["repositorios"]]
    gravar_json(saida, {
        "gerado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "origem": str(entrada), "janela": janela, "variante": "a",
        "total_repositorios": len(lista),
        "repositorios_com_cfr": sum(r["change_failure_rate"] is not None for r in lista),
        "repositorios_com_coleta_incompleta": sum(r["coleta_incompleta"] for r in lista),
        "repositorios": lista,
    })
    return saida, lista


def main(argv=None):
    parser = argparse.ArgumentParser(description="CFR variante (a) a partir de workflow runs locais.")
    parser.add_argument("--config", default="config.yaml", help="caminho da configuração")
    parser.add_argument("--entrada", help="JSON dos runs (padrão: caminhos.raw/workflow_runs.json)")
    parser.add_argument("--saida", help="JSON da CFR (padrão: caminhos.processed/cfr.json)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        saida, lista = executar(load_config(args.config), args.entrada, args.saida)
    except (ConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    calculadas = sum(r["change_failure_rate"] is not None for r in lista)
    incompletas = sum(r["coleta_incompleta"] for r in lista)
    print(f"CFR (a): {calculadas}/{len(lista)} repositórios com runs válidos, "
          f"{incompletas} coletas incompletas -> {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
