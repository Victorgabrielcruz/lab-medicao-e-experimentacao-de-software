"""Ponto de entrada do experimento: ``python executar.py``.

Registra o ambiente e mostra o plano de execução. O benchmark é ligado aqui
pelo script de coleta (S01-05).
"""

import sys

from experimento.ambiente import salvar_ambiente
from experimento.config import DIR_DADOS, N_AQUECIMENTO, N_REPETICOES, combinacoes, total_execucoes


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ambiente = salvar_ambiente(DIR_DADOS / "ambiente.json")
    print(f"SQLite {ambiente['sqlite_version']} · Python {ambiente['python_version']} · {ambiente['sistema']}")
    print(f"{len(combinacoes())} combinações × ({N_REPETICOES} repetições + {N_AQUECIMENTO} de aquecimento)"
          f" = {total_execucoes()} execuções")
    for configuracao, carga in combinacoes():
        print(f"  {configuracao.nome:<14} {carga.nome:<8} {carga.n_operacoes:>6} operações")


if __name__ == "__main__":
    main()
