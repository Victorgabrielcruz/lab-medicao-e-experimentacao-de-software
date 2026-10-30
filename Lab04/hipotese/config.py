"""Parâmetros compartilhados por simulação, testes e dashboard.

Toda geração de números aleatórios deve partir de ``gerador()`` para que os
resultados sejam reproduzíveis com um único comando.
"""

import numpy as np

SEMENTE = 42
ALFA = 0.05
N_REPETICOES = 10_000

# Par P4: taxa de builds com falha frente a uma meta de 5%.
META_TAXA_FALHA = 0.05

TESTE_Z = "Z para proporção"
TESTE_BINOMIAL = "Binomial exato"

# Mesma cor para cada teste em todos os gráficos (exigência do roteiro).
CORES_TESTES = {
    TESTE_Z: "#1f77b4",
    TESTE_BINOMIAL: "#d95f02",
}

URL_REPOSITORIO = "https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/tree/main/Lab04"
URL_PROJECT = "https://github.com/users/Victorgabrielcruz/projects/7"
# Preenchido quando o dashboard for publicado (#277).
URL_DASHBOARD = None


def gerador(semente: int = SEMENTE) -> np.random.Generator:
    """Retorna um gerador NumPy com a semente fixa do laboratório."""
    return np.random.default_rng(semente)
