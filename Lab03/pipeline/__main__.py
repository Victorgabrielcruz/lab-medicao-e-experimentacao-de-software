"""Ponto de entrada: python -m pipeline --config config.yaml"""

import argparse
import logging
import sys

from pipeline import actions, candidatos, metadados
from pipeline.config import ConfigError, load_config, read_token
from pipeline.github_api import GitHubClient

ETAPAS = ("candidatos", "actions", "metadados")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline", description="Mineração de métricas DORA (Lab03).")
    parser.add_argument("--config", default="config.yaml", help="caminho do arquivo de configuração")
    parser.add_argument("--etapas", nargs="+", choices=ETAPAS, default=list(ETAPAS),
                        help="etapas a executar (padrão: todas)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        config = load_config(args.config)
        token = read_token()
        api = config["api"]
        client = GitHubClient(token, api["base_url"], api.get("timeout_s", 30))

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
    except (ConfigError, FileNotFoundError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
