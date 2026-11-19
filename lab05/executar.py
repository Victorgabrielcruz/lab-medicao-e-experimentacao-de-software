"""Ponto de entrada do benchmark local do SQLite (#303)."""

import argparse
import sys
from pathlib import Path

from experimento.benchmark import coletar
from experimento.config import DIR_DADOS, N_AQUECIMENTO, N_REPETICOES, SEMENTE


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diretorio", type=Path, default=DIR_DADOS, help="Diretório de saída (padrão: lab05/data).")
    parser.add_argument("--repeticoes", type=int, default=N_REPETICOES)
    parser.add_argument("--aquecimentos", type=int, default=N_AQUECIMENTO)
    parser.add_argument("--semente", type=int, default=SEMENTE)
    args = parser.parse_args(argv)
    if args.repeticoes < 1 or args.aquecimentos < 0:
        parser.error("--repeticoes deve ser positivo e --aquecimentos não negativo.")
    print("Executando benchmark; a coleta completa pode levar vários minutos.", flush=True)
    try:
        caminho = coletar(args.diretorio, repeticoes=args.repeticoes,
                          aquecimentos=args.aquecimentos, semente=args.semente)
    except FileExistsError:
        parser.error("Já existe uma coleta nesse diretório. Use --diretorio com outro caminho.")
    print(f"Medições salvas em {caminho}")


if __name__ == "__main__":
    main()
