"""Ponto de entrada: python -m pipeline --config config.yaml"""

import argparse
import logging
import sys
from pathlib import Path

from pipeline import actions, candidatos, metadados, workflow_runs
from pipeline.cache import CacheDisco, gravar_json
from pipeline.config import ConfigError, load_config, read_token
from pipeline.github_api import GitHubClient

ETAPAS = ("candidatos", "actions", "metadados", "workflow_runs")


def _limite_positivo(valor):
    try:
        limite = int(valor)
    except ValueError:
        raise argparse.ArgumentTypeError("o limite do piloto deve ser um inteiro positivo") from None
    if limite < 1:
        raise argparse.ArgumentTypeError("o limite do piloto deve ser um inteiro positivo")
    return limite


def preparar_piloto(config, limite):
    """Reaproveita a busca existente, preservando dados completos e o cache."""
    raw_original = Path(config["caminhos"]["raw"])
    candidatos_existentes = actions.carregar_candidatos(raw_original)
    selecionados = candidatos_existentes[:limite]
    raw_piloto = raw_original / f"piloto-{limite}"
    gravar_json(raw_piloto / candidatos.ARQUIVO_SAIDA, {
        "origem": str(raw_original / candidatos.ARQUIVO_SAIDA),
        "criterio": "primeiros candidatos na ordem da busca existente; piloto de validação",
        "limite_candidatos": limite,
        "total_candidatos_origem": len(candidatos_existentes),
        "total_candidatos": len(selecionados),
        "candidatos": selecionados,
    })
    return {**config, "caminhos": {**config["caminhos"], "raw": str(raw_piloto)}}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline", description="Mineração de métricas DORA (Lab03).")
    parser.add_argument("--config", default="config.yaml", help="caminho do arquivo de configuração")
    parser.add_argument("--etapas", nargs="+", choices=ETAPAS, default=list(ETAPAS),
                        help="etapas a executar (padrão: todas)")
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--limpar-cache", action="store_true",
                       help="remove o cache configurado e encerra, sem executar a coleta")
    modos.add_argument("--piloto", type=_limite_positivo, metavar="N",
                       help="usa até N candidatos da busca existente e salva a coleta em raw/piloto-N")
    args = parser.parse_args(argv)
    if args.piloto is not None and args.etapas != list(ETAPAS):
        parser.error("use --piloto sem --etapas; o piloto executa actions, metadados e workflow_runs")
    return args


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = load_config(args.config)
        cache = CacheDisco(config["caminhos"]["cache"])
        if args.limpar_cache:
            removidos = cache.limpar()
            print(f"Cache limpo: {removidos} arquivos removidos de {cache.diretorio}")
            return 0
        token = read_token()
        if args.piloto is not None:
            config = preparar_piloto(config, args.piloto)
            args.etapas = ["actions", "metadados", "workflow_runs"]
            print(f"Piloto: até {args.piloto} candidatos da busca existente, "
                  f"cache compartilhado, saída em {config['caminhos']['raw']}")
        api = config["api"]
        client = GitHubClient(token, api["base_url"], api.get("timeout_s", 30), cache=cache)

        if "candidatos" in args.etapas:
            saida, fatias, lista = candidatos.executar(config, client)
            truncadas = sum(f["truncada"] for f in fatias)
            print(f"Candidatos: {len(lista)} repositórios em {len(fatias)} fatias "
                  f"({truncadas} truncadas) -> {saida}")

        if "actions" in args.etapas:
            saida, aprovados, descartes = actions.executar(config, client)
            print(f"Actions: {len(aprovados)} com GitHub Actions, {len(descartes)} descartados -> {saida}")

        if "metadados" in args.etapas:
            saida, lista, descartes = metadados.executar(config, client)
            sem = sum(m["contribuidores"] is None for m in lista)
            print(f"Metadados: {len(lista)} repositórios ({sem} sem contagem de contribuidores, "
                  f"{len(descartes)} inacessíveis) -> {saida}")

        if "workflow_runs" in args.etapas:
            saida, lista, descartes = workflow_runs.executar(config, client)
            total = sum(r["total_runs"] for r in lista)
            incompletas = sum(r["coleta_incompleta"] for r in lista)
            print(f"Workflow runs: {len(lista)} repositórios, {total} runs, "
                  f"{incompletas} coletas incompletas, {len(descartes)} inacessíveis -> {saida}")
    except (ConfigError, FileNotFoundError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
