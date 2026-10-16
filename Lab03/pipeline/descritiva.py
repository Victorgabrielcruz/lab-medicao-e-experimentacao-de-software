"""Estatística descritiva entre repositórios a partir do dataset exportado (#153).

Cada métrica é resumida só pelos valores válidos: nulos ficam fora e o
número de ausentes é reportado, sem imputação por zero. Quartis usam a
interpolação linear do pandas (método 7 de Hyndman e Fan).
"""

import json

import pandas as pd

# Semanas médias por mês civil, para ler a DF (releases/semana) em releases/mês.
SEMANAS_POR_MES = 365.25 / 7 / 12

COLUNAS_RESUMO = ["metrica", "n", "ausentes", "minimo", "q1", "mediana", "q3", "iqr", "maximo", "media"]


def carregar_dataset(caminho):
    """Lê o CSV do contrato lab03-dataset-v1 com listas JSON decodificadas."""
    dados = pd.read_csv(caminho)
    dados["metricas_ausentes"] = dados["metricas_ausentes"].map(json.loads)
    return dados


def resumo(serie, metrica=None):
    """Resumo de uma métrica: n válido, ausentes, quartis, IQR e média."""
    valores = pd.to_numeric(serie, errors="raise").dropna()
    linha = {"metrica": metrica or serie.name, "n": len(valores), "ausentes": int(serie.isna().sum())}
    if valores.empty:
        return linha | {coluna: None for coluna in COLUNAS_RESUMO[3:]}
    q1, mediana, q3 = valores.quantile([0.25, 0.5, 0.75])
    return linha | {
        "minimo": valores.min(), "q1": q1, "mediana": mediana, "q3": q3,
        "iqr": q3 - q1, "maximo": valores.max(), "media": valores.mean(),
    }


def tabela_resumo(dados, metricas):
    """Uma linha de resumo por métrica; `metricas` mapeia rótulo -> coluna."""
    linhas = [resumo(dados[coluna], rotulo) for rotulo, coluna in metricas.items()]
    return pd.DataFrame(linhas, columns=COLUNAS_RESUMO)


def pares_lead_time(dados):
    """Repositórios com as duas variantes de lead time e a diferença (a) - (b), em horas."""
    pares = dados.dropna(subset=["lead_time_a", "lead_time_b"])
    pares = pares[["id", "full_name", "lead_time_a", "lead_time_b"]].copy()
    pares["diferenca"] = pares["lead_time_a"] - pares["lead_time_b"]
    pares["razao"] = pares["lead_time_a"] / pares["lead_time_b"]
    return pares.reset_index(drop=True)


def comparar_variantes(pares):
    """Contagens de (a) maior, igual ou menor que (b) e mediana das diferenças pareadas."""
    return {
        "n_pares": len(pares),
        "a_maior": int((pares["diferenca"] > 0).sum()),
        "iguais": int((pares["diferenca"] == 0).sum()),
        "a_menor": int((pares["diferenca"] < 0).sum()),
        "mediana_diferenca": pares["diferenca"].median() if len(pares) else None,
        "mediana_razao": pares["razao"].median() if len(pares) else None,
    }
