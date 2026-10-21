"""Estatística descritiva entre repositórios a partir do dataset exportado (#153).

Cada métrica é resumida só pelos valores válidos: nulos ficam fora e o
número de ausentes é reportado, sem imputação por zero. Quartis usam a
interpolação linear do pandas (método 7 de Hyndman e Fan).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

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


def pares_variantes(dados, coluna_a, coluna_b):
    """Repositórios com as duas variantes, a diferença (a) - (b) e a razão (a) / (b).

    A razão fica nula quando (b) é zero, para não produzir infinito.
    """
    pares = dados.dropna(subset=[coluna_a, coluna_b])
    pares = pares[["id", "full_name", coluna_a, coluna_b]].copy()
    pares["diferenca"] = pares[coluna_a] - pares[coluna_b]
    pares["razao"] = (pares[coluna_a] / pares[coluna_b]).where(pares[coluna_b] != 0)
    return pares.reset_index(drop=True)


def pares_lead_time(dados):
    """Repositórios com as duas variantes de lead time e a diferença (a) - (b), em horas."""
    return pares_variantes(dados, "lead_time_a", "lead_time_b")


def episodios_recuperacao(tempo_recuperacao):
    """Contagem de episódios por repositório a partir de `tempo_recuperacao.json`.

    Censurados são episódios à direita (sem sucesso até o fim da janela);
    sequências com censura à esquerda (`historico_inicial_nao_observado`)
    ficam fora dos episódios e são contadas à parte.
    """
    linhas = [{
        "id": r["id"],
        "full_name": r["full_name"],
        "total_episodios": r["total_episodios"],
        "episodios_recuperados": r["episodios_recuperados"],
        "episodios_censurados": r["episodios_censurados"],
        "proporcao_censurados": r["proporcao_censurados"],
        "sequencias_censura_esquerda": len(r["historico_inicial_nao_observado"]),
    } for r in tempo_recuperacao["repositorios"]]
    return pd.DataFrame(linhas).sort_values("id").reset_index(drop=True)


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


def exportar_episodios(entrada, saida):
    """Grava o CSV de episódios por repositório e um JSON com o SHA-256 da origem."""
    entrada, saida = Path(entrada), Path(saida)
    episodios = episodios_recuperacao(json.loads(entrada.read_text(encoding="utf-8")))
    saida.parent.mkdir(parents=True, exist_ok=True)
    episodios.to_csv(saida, index=False, lineterminator="\n")
    origem = {"origem": entrada.name, "origem_sha256": hashlib.sha256(entrada.read_bytes()).hexdigest(),
              "repositorios": len(episodios)}
    saida.with_suffix(".json").write_text(json.dumps(origem, indent=2) + "\n", encoding="utf-8")
    return episodios


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exporta episódios de recuperação por repositório (#168).")
    parser.add_argument("--tempo-recuperacao", required=True, help="processed/.../tempo_recuperacao.json")
    parser.add_argument("--saida", required=True, help="CSV de saída; o JSON de origem vai ao lado")
    args = parser.parse_args(argv)
    episodios = exportar_episodios(args.tempo_recuperacao, args.saida)
    print(f"{len(episodios)} repositórios gravados em {args.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
