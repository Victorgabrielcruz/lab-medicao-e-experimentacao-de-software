"""Exemplo único da S01-05 compartilhado pelo dashboard e pelo futuro G2 (#266)."""

from dataclasses import dataclass

import numpy as np

from hipotese.cenario import carregar_resumo, configuracoes_simulacao
from hipotese.config import EFEITO_EXEMPLO, gerador
from hipotese.gerador import gerar_builds, taxa_com_efeito
from hipotese.testes import ResultadoTeste, aplicar_testes


@dataclass(frozen=True)
class ExemploSimulado:
    builds: np.ndarray
    taxa_verdadeira: float
    resultados: tuple[ResultadoTeste, ResultadoTeste]


def gerar_exemplo() -> ExemploSimulado:
    """Gera uma amostra independente com a semente fixa, sem procurar significância."""
    parametros = configuracoes_simulacao(carregar_resumo())["Independente"]
    taxa = taxa_com_efeito(EFEITO_EXEMPLO)
    builds = gerar_builds(gerador(), taxa_falha=taxa, **parametros)
    return ExemploSimulado(builds=builds, taxa_verdadeira=taxa, resultados=aplicar_testes(builds))
