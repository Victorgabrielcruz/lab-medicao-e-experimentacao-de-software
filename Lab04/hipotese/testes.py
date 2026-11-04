"""Testes do par P4 reutilizáveis pelo exemplo e pelas simulações (#266)."""

from dataclasses import dataclass
from math import sqrt
from numbers import Integral

import numpy as np
from scipy.stats import binomtest, norm

from hipotese.config import ALFA, ALTERNATIVA, META_TAXA_FALHA, TESTE_BINOMIAL, TESTE_Z


@dataclass(frozen=True)
class ResultadoTeste:
    teste: str
    nome_estatistica: str
    estatistica: float
    pvalor: float
    n: int
    falhas: int
    proporcao: float
    efeito_pp: float
    rejeita_h0: bool


def _validar_contagens(falhas: int, n: int, meta: float, alfa: float) -> None:
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("n deve ser um inteiro positivo.")
    if isinstance(falhas, bool) or not isinstance(falhas, Integral) or not 0 <= falhas <= n:
        raise ValueError("falhas deve ser um inteiro entre 0 e n.")
    if not 0 < meta < 1:
        raise ValueError("meta deve estar estritamente entre 0 e 1.")
    if not 0 < alfa < 1:
        raise ValueError("alfa deve estar estritamente entre 0 e 1.")


def _contar_falhas(builds) -> tuple[int, int]:
    valores = np.asarray(builds)
    if valores.ndim != 1 or valores.size == 0 or not np.isin(valores, (0, 1)).all():
        raise ValueError("builds deve ser uma sequência unidimensional não vazia de 0 e 1.")
    return int(valores.sum()), int(valores.size)


def teste_z(
    falhas: int, n: int, meta: float = META_TAXA_FALHA,
    alternativa: str = ALTERNATIVA, alfa: float = ALFA,
) -> ResultadoTeste:
    """Z para uma proporção, com variância sob H0 e sem correção de continuidade.

    Z = (p_hat - p0) / sqrt(p0 * (1 - p0) / n).
    Usa a normal padrão do SciPy para calcular a área da cauda.
    """
    _validar_contagens(falhas, n, meta, alfa)
    proporcao = falhas / n
    z = (proporcao - meta) / sqrt(meta * (1 - meta) / n)
    if alternativa == "greater":
        pvalor = norm.sf(z)
    elif alternativa == "less":
        pvalor = norm.cdf(z)
    elif alternativa == "two-sided":
        pvalor = 2 * norm.sf(abs(z))
    else:
        raise ValueError("alternativa deve ser 'greater', 'less' ou 'two-sided'.")
    return ResultadoTeste(
        teste=TESTE_Z, nome_estatistica="Z", estatistica=float(z),
        pvalor=float(pvalor), n=int(n), falhas=int(falhas), proporcao=proporcao,
        efeito_pp=100 * (proporcao - meta), rejeita_h0=bool(pvalor < alfa),
    )


def teste_binomial(
    falhas: int, n: int, meta: float = META_TAXA_FALHA,
    alternativa: str = ALTERNATIVA, alfa: float = ALFA,
) -> ResultadoTeste:
    """Teste exato; ``falhas`` é o evento de interesse, codificado como 1.

    A estatística retornada pelo SciPy é a proporção observada, não um Z.
    O tamanho do efeito é a diferença assinada para a meta, em p.p.
    """
    _validar_contagens(falhas, n, meta, alfa)
    resultado = binomtest(int(falhas), int(n), p=meta, alternative=alternativa)
    return ResultadoTeste(
        teste=TESTE_BINOMIAL, nome_estatistica="Proporção observada (p̂)",
        estatistica=float(resultado.statistic), pvalor=float(resultado.pvalue),
        n=int(n), falhas=int(falhas), proporcao=float(resultado.statistic),
        efeito_pp=100 * (resultado.statistic - meta),
        rejeita_h0=bool(resultado.pvalue < alfa),
    )


def aplicar_testes(
    builds, meta: float = META_TAXA_FALHA,
    alternativa: str = ALTERNATIVA, alfa: float = ALFA,
) -> tuple[ResultadoTeste, ResultadoTeste]:
    """Aplica os dois testes à mesma amostra binária, sem consumir aleatoriedade.

    Para lotes da S02, as funções individuais também recebem diretamente
    as contagens produzidas por ``gerar_lote(contagens=True)``.
    """
    falhas, n = _contar_falhas(builds)
    return (
        teste_z(falhas, n, meta, alternativa, alfa),
        teste_binomial(falhas, n, meta, alternativa, alfa),
    )
