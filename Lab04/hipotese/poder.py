"""Poder exato dos dois testes com builds independentes (bônus, #278).

Com builds independentes, o número de falhas segue uma binomial. Cada teste
rejeita H₀ a partir de uma contagem mínima de falhas, então o poder é a
probabilidade de a contagem atingir esse mínimo quando a taxa verdadeira é
``meta + efeito``. O cálculo é exato e instantâneo, o que permite atualizar o
gráfico interativo sem rodar uma nova simulação de Monte Carlo.
"""

from numbers import Integral

import numpy as np
import pandas as pd
from scipy.stats import binom, norm

from hipotese.config import ALFA, META_TAXA_FALHA, TESTE_BINOMIAL, TESTE_Z

TESTES = (TESTE_Z, TESTE_BINOMIAL)


def _validar(n: int, alfa: float, meta: float) -> None:
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("n deve ser um inteiro positivo.")
    if not 0 < alfa < 1:
        raise ValueError("alfa deve estar estritamente entre 0 e 1.")
    if not 0 < meta < 1:
        raise ValueError("meta deve estar estritamente entre 0 e 1.")


def pvalores_por_contagem(n: int, meta: float = META_TAXA_FALHA) -> dict[str, np.ndarray]:
    """p-valor unicaudal à direita de cada contagem de 0 a ``n`` falhas, para os dois testes.

    Reproduz, de forma vetorizada, ``teste_z`` e ``teste_binomial`` de ``hipotese.testes``.
    """
    _validar(n, ALFA, meta)
    contagens = np.arange(n + 1)
    z = (contagens / n - meta) / np.sqrt(meta * (1 - meta) / n)
    return {
        TESTE_Z: norm.sf(z),
        TESTE_BINOMIAL: binom.sf(contagens - 1, n, meta),
    }


def contagem_minima_rejeicao(teste: str, n: int, alfa: float = ALFA, meta: float = META_TAXA_FALHA) -> int:
    """Menor número de falhas com p-valor < α; ``n + 1`` quando nenhuma contagem rejeita H₀."""
    _validar(n, alfa, meta)
    rejeita = pvalores_por_contagem(n, meta)[teste] < alfa
    return int(np.argmax(rejeita)) if rejeita.any() else n + 1


def poder_exato(teste: str, n: int, efeito: float, alfa: float = ALFA, meta: float = META_TAXA_FALHA) -> float:
    """Proporção esperada de rejeições com taxa verdadeira ``meta + efeito`` e builds independentes.

    Com efeito zero, o valor é o erro tipo I exato do teste.
    """
    taxa = meta + efeito
    if efeito < 0 or taxa > 1:
        raise ValueError("o efeito deve ser não negativo e manter a taxa verdadeira até 1.")
    minimo = contagem_minima_rejeicao(teste, n, alfa, meta)
    return float(binom.sf(minimo - 1, n, taxa))


def curva_poder(n: int, efeitos, alfa: float = ALFA, meta: float = META_TAXA_FALHA) -> pd.DataFrame:
    """Poder exato dos dois testes em cada efeito, no formato longo (efeito, teste, poder)."""
    efeitos = np.asarray(efeitos, dtype=float)
    if efeitos.ndim != 1 or efeitos.size == 0 or (efeitos < 0).any() or (meta + efeitos > 1).any():
        raise ValueError("efeitos deve ser uma sequência não vazia de valores entre 0 e 1 − meta.")
    linhas = []
    for teste in TESTES:
        minimo = contagem_minima_rejeicao(teste, n, alfa, meta)
        poderes = binom.sf(minimo - 1, n, meta + efeitos)
        linhas.append(pd.DataFrame({"efeito": efeitos, "teste": teste, "poder": poderes}))
    return pd.concat(linhas, ignore_index=True)
