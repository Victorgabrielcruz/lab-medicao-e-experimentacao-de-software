"""Q1: erro tipo I na situação independente, usando o CSV da S02 (#270)."""

import csv
from dataclasses import dataclass
from fractions import Fraction
from math import isclose
from pathlib import Path

import numpy as np
from scipy.stats import binom

from hipotese.cenario import carregar_resumo, configuracoes_simulacao
from hipotese.config import ALFA, MARGEM_ERRO_TIPO_I_PP, META_TAXA_FALHA, N_REPETICOES, SEMENTE
from hipotese.simulacao import ARQUIVO, TESTES, pvalores


@dataclass(frozen=True)
class ResultadoErroTipoI:
    teste: str
    n: int
    repeticoes: int
    rejeicoes: int
    taxa_erro: float
    desvio_pp: float
    classificacao: str
    taxa_teorica: float
    primeira_contagem_rejeitada: int


def classificar_erro_tipo_i(rejeicoes: int, repeticoes: int) -> str:
    """Compara com alfa ± margem; inclui as duas fronteiras sem arredondar."""
    if repeticoes <= 0 or not 0 <= rejeicoes <= repeticoes:
        raise ValueError("As rejeições devem estar entre zero e o total positivo de repetições.")
    # Frações evitam classificar 4,6%/5,4% fora da margem por arredondamento binário.
    taxa = Fraction(rejeicoes, repeticoes)
    nominal = Fraction(str(ALFA))
    margem = Fraction(str(MARGEM_ERRO_TIPO_I_PP)) / 100
    if taxa < nominal - margem:
        return "Conservador"
    if taxa > nominal + margem:
        return "Liberal"
    return "Dentro da margem"


def analisar_erro_tipo_i(caminho: Path = ARQUIVO) -> list[ResultadoErroTipoI]:
    """Seleciona efeito zero e a referência independente, sem novo Monte Carlo.

    A probabilidade teórica soma as massas Binomial(n, p₀) nas contagens
    rejeitadas pelas funções dos testes; ajuda a interpretar a discretização.
    """
    n_esperado = configuracoes_simulacao(carregar_resumo())["Independente"]["n"]
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        linhas = [linha for linha in csv.DictReader(arquivo)
                  if linha["situacao"] == "Independente" and float(linha["efeito"]) == 0]
    por_teste = {}
    for linha in linhas:
        nome = linha["teste"]
        if nome not in TESTES or nome in por_teste:
            raise ValueError("Q1 requer exatamente uma linha para cada um dos dois testes.")
        if (
            int(linha["n"]) != n_esperado
            or float(linha["correlacao"]) != 0
            or float(linha["taxa_verdadeira"]) != META_TAXA_FALHA
            or int(linha["repeticoes"]) != N_REPETICOES
            or int(linha["semente"]) != SEMENTE
        ):
            raise ValueError("A configuração de Q1 difere do protocolo independente sob H₀.")
        por_teste[nome] = linha
    if set(por_teste) != set(TESTES):
        raise ValueError("Q1 requer exatamente uma linha para cada um dos dois testes.")

    resultados = []
    for nome, teste in TESTES.items():
        linha = por_teste[nome]
        rejeicoes, repeticoes = int(linha["rejeicoes"]), int(linha["repeticoes"])
        classificacao = classificar_erro_tipo_i(rejeicoes, repeticoes)
        taxa = rejeicoes / repeticoes
        if not isclose(taxa, float(linha["proporcao_rejeicao"]), rel_tol=0, abs_tol=1e-12):
            raise ValueError("A proporção de rejeição não corresponde às contagens do CSV.")
        k = np.arange(n_esperado + 1)
        rejeita = pvalores(k, n_esperado, teste) < ALFA
        resultados.append(ResultadoErroTipoI(
            teste=nome, n=n_esperado, repeticoes=repeticoes, rejeicoes=rejeicoes,
            taxa_erro=taxa, desvio_pp=100 * (taxa - ALFA), classificacao=classificacao,
            taxa_teorica=float(binom.pmf(k, n_esperado, META_TAXA_FALHA)[rejeita].sum()),
            primeira_contagem_rejeitada=int(k[rejeita][0]),
        ))
    return resultados
