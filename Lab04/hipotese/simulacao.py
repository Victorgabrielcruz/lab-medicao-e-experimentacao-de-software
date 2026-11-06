"""Motor de simulação Monte Carlo da S02 (#269).

Para cada configuração (situação × tamanho do efeito), gera ``N_REPETICOES``
conjuntos de builds, aplica os dois testes ao **mesmo** conjunto e calcula a
proporção de p-valores abaixo de ``ALFA``. Com efeito zero essa proporção é o
erro tipo I (Q1); com efeito positivo, o poder (Q2). As situações de rajadas e
de amostra pequena servem à Q3.

Os resultados vão para ``data/simulacao.csv``, lido pelo dashboard sem
recalcular. Para regenerar, a partir de ``Lab04``::

    .venv/Scripts/python -m hipotese.simulacao
"""

import argparse
import csv
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path

import numpy as np

from hipotese.cenario import carregar_resumo, configuracoes_simulacao
from hipotese.config import (ALFA, ALTERNATIVA, EFEITOS, META_TAXA_FALHA, N_REPETICOES, SEMENTE, TESTE_BINOMIAL,
                             TESTE_Z)
from hipotese.gerador import gerar_lote, taxa_com_efeito
from hipotese.testes import teste_binomial, teste_z

ARQUIVO = Path(__file__).resolve().parents[1] / "data" / "simulacao.csv"
TESTES = {TESTE_Z: teste_z, TESTE_BINOMIAL: teste_binomial}


@dataclass(frozen=True)
class ResultadoConfiguracao:
    situacao: str
    n: int
    correlacao: float
    efeito: float
    taxa_verdadeira: float
    teste: str
    repeticoes: int
    rejeicoes: int
    proporcao_rejeicao: float
    erro_padrao: float
    semente: int
    indice_situacao: int
    indice_efeito: int


def gerador_configuracao(indice_situacao: int, indice_efeito: int, semente: int = SEMENTE) -> np.random.Generator:
    """Gerador independente por configuração, derivado da semente do laboratório.

    Cada configuração tem seu próprio fluxo de números, então o resultado de uma
    não depende da ordem em que as outras são simuladas.
    """
    sequencia = np.random.SeedSequence(semente, spawn_key=(indice_situacao, indice_efeito))
    return np.random.default_rng(sequencia)


def pvalores(falhas: np.ndarray, n: int, teste, meta: float = META_TAXA_FALHA,
             alternativa: str = ALTERNATIVA) -> np.ndarray:
    """p-valor de cada contagem, calculado pelas mesmas funções dos testes da S01.

    As contagens são inteiros entre 0 e ``n``, então basta calcular o p-valor
    uma vez por contagem distinta e reaproveitá-lo.
    """
    distintas, posicoes = np.unique(falhas, return_inverse=True)
    por_contagem = np.array([teste(int(k), n, meta, alternativa).pvalor for k in distintas])
    return por_contagem[posicoes]


def simular_configuracao(
    situacao: str, parametros: dict, efeito: float, indice_situacao: int, indice_efeito: int,
    repeticoes: int = N_REPETICOES, semente: int = SEMENTE, alfa: float = ALFA,
) -> list[ResultadoConfiguracao]:
    """Rejeições de cada teste em ``repeticoes`` conjuntos de uma configuração."""
    taxa = taxa_com_efeito(efeito)
    rng = gerador_configuracao(indice_situacao, indice_efeito, semente)
    falhas = gerar_lote(rng, taxa_falha=taxa, repeticoes=repeticoes, **parametros)
    resultados = []
    for nome, teste in TESTES.items():
        rejeicoes = int((pvalores(falhas, parametros["n"], teste) < alfa).sum())
        proporcao = rejeicoes / repeticoes
        resultados.append(ResultadoConfiguracao(
            situacao=situacao, n=parametros["n"], correlacao=float(parametros["correlacao"]),
            efeito=efeito, taxa_verdadeira=taxa, teste=nome, repeticoes=repeticoes,
            rejeicoes=rejeicoes, proporcao_rejeicao=proporcao,
            erro_padrao=sqrt(proporcao * (1 - proporcao) / repeticoes),
            semente=semente, indice_situacao=indice_situacao, indice_efeito=indice_efeito,
        ))
    return resultados


def simular(configuracoes: dict[str, dict], efeitos=EFEITOS, repeticoes: int = N_REPETICOES,
            semente: int = SEMENTE) -> list[ResultadoConfiguracao]:
    """Todas as combinações de situação × efeito, na ordem do protocolo."""
    resultados = []
    for i, (situacao, parametros) in enumerate(configuracoes.items()):
        for j, efeito in enumerate(efeitos):
            resultados.extend(simular_configuracao(situacao, parametros, efeito, i, j, repeticoes, semente))
    return resultados


def gravar(resultados: list[ResultadoConfiguracao], caminho: Path = ARQUIVO) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, list(ResultadoConfiguracao.__dataclass_fields__), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(asdict(r) for r in resultados)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Executa as simulações Monte Carlo da S02 (#269).")
    parser.add_argument("--repeticoes", type=int, default=N_REPETICOES)
    parser.add_argument("--saida", type=Path, default=ARQUIVO)
    args = parser.parse_args(argv)
    resultados = simular(configuracoes_simulacao(carregar_resumo()), repeticoes=args.repeticoes)
    gravar(resultados, args.saida)
    print(f"{len(resultados)} linhas gravadas em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
