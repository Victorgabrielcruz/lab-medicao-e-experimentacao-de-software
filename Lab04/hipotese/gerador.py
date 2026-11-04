"""Geração dos dados simulados do par P4: builds de CI que falham ou passam.

Cada build é uma observação binária (1 = falhou). A taxa de falha verdadeira é
``META_TAXA_FALHA + efeito``: com efeito zero, H0 é verdadeira.

Situações simuladas:

- ``independente``: cada build falha com a mesma probabilidade, sem depender
  das anteriores (Bernoulli i.i.d.). É a situação em que os pressupostos dos
  dois testes valem.
- ``rajadas``: as falhas vêm em sequência, como no CI real, em que uma build
  quebrada costuma ser seguida de outras até a correção. Uma cadeia de Markov
  mantém a mesma taxa média de falha, mas com correlação ``correlacao`` entre
  builds consecutivas, o que viola a independência assumida pelos testes.

Amostras pequenas são simuladas apenas pelo parâmetro ``n``.
"""

import numpy as np

from hipotese.config import META_TAXA_FALHA

INDEPENDENTE = "independente"
RAJADAS = "rajadas"
SITUACOES = (INDEPENDENTE, RAJADAS)

CORRELACAO_PADRAO = 0.5


def taxa_com_efeito(efeito: float, meta: float = META_TAXA_FALHA) -> float:
    """Taxa de falha verdadeira para um tamanho de efeito (diferença absoluta para a meta)."""
    taxa = meta + efeito
    if not 0 <= taxa <= 1:
        raise ValueError(f"taxa de falha fora de [0, 1]: {taxa}")
    return taxa


def _validar(n: int, taxa_falha: float, situacao: str, correlacao: float) -> None:
    if n < 1:
        raise ValueError("n deve ser pelo menos 1")
    if not 0 <= taxa_falha <= 1:
        raise ValueError(f"taxa de falha fora de [0, 1]: {taxa_falha}")
    if situacao not in SITUACOES:
        raise ValueError(f"situação desconhecida: {situacao!r}; use uma de {SITUACOES}")
    if not 0 <= correlacao < 1:
        raise ValueError("a correlação deve estar em [0, 1)")


def _transicoes(taxa_falha: float, correlacao: float) -> tuple[float, float]:
    """P(falha | anterior falhou) e P(falha | anterior passou) com taxa estacionária ``taxa_falha``."""
    return (
        taxa_falha + correlacao * (1 - taxa_falha),
        taxa_falha * (1 - correlacao),
    )


def gerar_builds(
    rng: np.random.Generator,
    n: int,
    taxa_falha: float,
    situacao: str = INDEPENDENTE,
    correlacao: float = CORRELACAO_PADRAO,
) -> np.ndarray:
    """Gera um conjunto de ``n`` builds (0 = passou, 1 = falhou)."""
    return gerar_lote(rng, n, taxa_falha, 1, situacao, correlacao, contagens=False)[0]


def gerar_lote(
    rng: np.random.Generator,
    n: int,
    taxa_falha: float,
    repeticoes: int,
    situacao: str = INDEPENDENTE,
    correlacao: float = CORRELACAO_PADRAO,
    contagens: bool = True,
) -> np.ndarray:
    """Gera ``repeticoes`` conjuntos de ``n`` builds de uma vez.

    Com ``contagens=True`` devolve só o número de falhas de cada conjunto
    (forma ``(repeticoes,)``), que é tudo de que os dois testes precisam.
    Com ``contagens=False`` devolve as builds (forma ``(repeticoes, n)``).
    """
    _validar(n, taxa_falha, situacao, correlacao)

    if situacao == INDEPENDENTE:
        if contagens:
            return rng.binomial(n, taxa_falha, size=repeticoes)
        return (rng.random((repeticoes, n)) < taxa_falha).astype(np.int8)

    apos_falha, apos_sucesso = _transicoes(taxa_falha, correlacao)
    builds = np.empty((repeticoes, n), dtype=np.int8)
    builds[:, 0] = rng.random(repeticoes) < taxa_falha
    for i in range(1, n):
        prob = np.where(builds[:, i - 1] == 1, apos_falha, apos_sucesso)
        builds[:, i] = rng.random(repeticoes) < prob
    return builds.sum(axis=1) if contagens else builds
