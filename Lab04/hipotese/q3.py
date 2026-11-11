"""Q3 — o que muda quando os dados não se comportam bem (#272).

Compara o erro tipo I e o poder dos dois testes nas situações que violam
pressupostos (rajadas e amostra pequena) com a situação independente, a
partir de ``data/simulacao.csv`` (#269), sem simular de novo.
"""

from math import sqrt

import numpy as np
import pandas as pd
from scipy.stats import binom

from hipotese.config import ALFA, META_TAXA_FALHA, N_REPETICOES, TESTE_BINOMIAL, TESTE_Z
from hipotese.simulacao import ARQUIVO, TESTES, pvalores

REFERENCIA = "Independente"
VIOLACOES = ("Rajadas", "Amostra pequena")

# Meia-largura de 95% de uma proporção estimada com N_REPETICOES quando o valor real é ALFA.
MARGEM_MONTE_CARLO = 1.96 * sqrt(ALFA * (1 - ALFA) / N_REPETICOES)

LIBERAL, CONSERVADOR, PROXIMO = "liberal", "conservador", "próximo de 5%"


def carregar_resultados(caminho=ARQUIVO) -> pd.DataFrame:
    return pd.read_csv(caminho)


def classificar_erro_tipo_i(proporcao: float, alfa: float = ALFA, margem: float = MARGEM_MONTE_CARLO) -> str:
    """Liberal acima de α + margem, conservador abaixo de α − margem."""
    if proporcao > alfa + margem:
        return LIBERAL
    if proporcao < alfa - margem:
        return CONSERVADOR
    return PROXIMO


def erro_tipo_i(resultados: pd.DataFrame) -> pd.DataFrame:
    """Erro tipo I (efeito zero) por situação e teste, com desvio de α em p.p. e classificação."""
    sob_h0 = resultados[resultados["efeito"] == 0].copy()
    sob_h0["desvio_pp"] = 100 * (sob_h0["proporcao_rejeicao"] - ALFA)
    sob_h0["classificacao"] = sob_h0["proporcao_rejeicao"].map(classificar_erro_tipo_i)
    colunas = ["situacao", "n", "correlacao", "teste", "proporcao_rejeicao", "erro_padrao", "desvio_pp",
               "classificacao"]
    return sob_h0[colunas].reset_index(drop=True)


def poder(resultados: pd.DataFrame, situacao: str) -> pd.DataFrame:
    """Proporção de rejeições por efeito para os dois testes e a diferença Z − binomial, em p.p."""
    dados = resultados[resultados["situacao"] == situacao]
    tabela = dados.pivot(index="efeito", columns="teste", values="proporcao_rejeicao")[[TESTE_Z, TESTE_BINOMIAL]]
    tabela["diferenca_pp"] = 100 * (tabela[TESTE_Z] - tabela[TESTE_BINOMIAL])
    return tabela.reset_index()


def contagem_minima_rejeicao(teste: str, n: int, alfa: float = ALFA) -> int:
    """Menor número de falhas em ``n`` builds com p-valor < α."""
    contagens = np.arange(n + 1)
    rejeita = pvalores(contagens, n, TESTES[teste]) < alfa
    return int(contagens[rejeita].min())


def erro_tipo_i_exato(teste: str, n: int, meta: float = META_TAXA_FALHA, alfa: float = ALFA) -> float:
    """Erro tipo I exato sob independência: P(X ≥ contagem mínima de rejeição | p = meta)."""
    return float(binom.sf(contagem_minima_rejeicao(teste, n, alfa) - 1, n, meta))


def inflacao_variancia(correlacao: float) -> float:
    """Fator aproximado pelo qual a dependência de lag 1 multiplica a variância do número de falhas.

    Para a cadeia de Markov do gerador, a autocorrelação de lag k é ρ^k, e a
    variância da soma de n builds tende a n·p(1−p)·(1+ρ)/(1−ρ).
    """
    if not 0 <= correlacao < 1:
        raise ValueError("a correlação deve estar em [0, 1)")
    return (1 + correlacao) / (1 - correlacao)
