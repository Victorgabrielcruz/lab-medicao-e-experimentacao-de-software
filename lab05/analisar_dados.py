"""Reproduz a análise da #309 sem executar benchmark nem alterar os dados."""

import argparse
import json
from pathlib import Path

from experimento import config
from experimento.inferencia import analisar
from experimento.painel import carregar_coleta_completa


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diretorio", type=Path, default=config.DIR_DADOS / "coleta-completa-01")
    parser.add_argument("--saida", type=Path, help="JSON novo; sem esta opção, imprime em stdout.")
    args = parser.parse_args(argv)
    try:
        coleta = carregar_coleta_completa(args.diretorio)
        resultado = analisar(coleta.dados).como_dict()
        resultado["origem"] = {"coleta": args.diretorio.name,
                               "sha256_csv": coleta.validacao["entradas_sha256"]["resultados.csv"]}
        texto = json.dumps(resultado, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.saida:
            # Reserva exclusiva protege entradas e relatórios já existentes.
            with args.saida.open("x", encoding="utf-8") as arquivo:
                arquivo.write(texto)
            print(f"Análise salva em {args.saida}")
        else:
            print(texto, end="")
    except (OSError, ValueError) as erro:
        parser.error(str(erro))


if __name__ == "__main__":
    main()
