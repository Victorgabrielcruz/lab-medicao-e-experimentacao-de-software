"""Distribuição das classes DORA de referência (C1) entre repositórios (#169).

Usa as classes por métrica já gravadas no dataset (contrato
`lab03-enunciado-cortes-v2`) e calcula a classe geral pela mediana das notas,
arredondada para baixo e ignorando ausentes (`classificacao.nota_geral`).
"""

from itertools import product

import pandas as pd

from pipeline.classificacao import CLASSES, nota_geral

SEM_CLASSE = "Sem classe"
ORDEM = [*CLASSES, SEM_CLASSE]

# Combinação de referência da classe geral: lead time (b) por commit e CFR (a) por runs.
REFERENCIA_GERAL = {
    "deployment_frequency": "classe_deployment_frequency",
    "lead_time": "classe_lead_time_b",
    "change_failure_rate": "classe_cfr_a",
    "tempo_recuperacao": "classe_tempo_recuperacao",
}


def classe_geral(dados, colunas):
    """Classe geral de cada repositório a partir das colunas de classe indicadas."""
    def linha(registro):
        return nota_geral([None if pd.isna(registro[c]) else registro[c] for c in colunas])
    return dados.apply(linha, axis=1)


def combinacoes_geral():
    """As quatro combinações das variantes de lead time e CFR, com rótulo legível."""
    combinacoes = {}
    for lt, cfr in product("ab", "ab"):
        colunas = REFERENCIA_GERAL | {"lead_time": f"classe_lead_time_{lt}", "change_failure_rate": f"classe_cfr_{cfr}"}
        combinacoes[f"LT ({lt}) + CFR ({cfr})"] = list(colunas.values())
    return combinacoes


def distribuicao(series):
    """Contagem e percentual por classe, na ordem Elite, High, Medium, Low e sem classe.

    `series` mapeia o rótulo da linha a uma série de classes (nulos = sem classe).
    """
    linhas = []
    for rotulo, serie in series.items():
        contagem = serie.fillna(SEM_CLASSE).value_counts().reindex(ORDEM, fill_value=0)
        desconhecidas = set(serie.dropna()) - set(CLASSES)
        if desconhecidas:
            raise ValueError(f"{rotulo}: classes desconhecidas {sorted(desconhecidas)}")
        linhas.append({"metrica": rotulo, "n": int(serie.notna().sum()),
                       **{c: int(contagem[c]) for c in ORDEM},
                       **{f"{c} (%)": 100 * contagem[c] / len(serie) for c in ORDEM}})
    return pd.DataFrame(linhas)
