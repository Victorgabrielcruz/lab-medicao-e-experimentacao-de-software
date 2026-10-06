"""Ponto de entrada: python -m pipeline --config config.yaml"""

import argparse
import sys

from pipeline.config import ConfigError, load_config, read_token


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="pipeline", description="Mineração de métricas DORA (Lab03).")
    parser.add_argument("--config", default="config.yaml", help="caminho do arquivo de configuração")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        config = load_config(args.config)
        read_token()
    except ConfigError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    print(f"Configuração carregada de {args.config} (API: {config['api']['base_url']}).")
    print("Nenhuma etapa do pipeline implementada ainda.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
