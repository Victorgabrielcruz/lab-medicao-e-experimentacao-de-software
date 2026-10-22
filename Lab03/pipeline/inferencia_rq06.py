"""Holm e tamanhos de efeito sobre os grupos fixos da RQ06 (#172)."""

from itertools import combinations
from numbers import Real

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from pipeline import comparacao_rq06 as base

COLUNAS_PARES = ("fator", "metrica", "grupo_1", "grupo_2", "n_1", "n_2", "U_1",
                 "p_valor_bruto", "cliff_delta", "magnitude_delta", "motivo", "executado_na_171")


def _alpha(alpha):
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise ValueError("Alpha deve estar entre 0 e 1.")


def _contagem(n):
    if not isinstance(n, (int, np.integer)) or isinstance(n, (bool, np.bool_)) or n < 0:
        raise ValueError("Tamanho de amostra deve ser inteiro não negativo.")


def aplicar_holm(p_valores, *, alpha=base.ALPHA):
    """Mantém a família planejada; ausentes ficam nulos na saída, nunca p=1 observado."""
    _alpha(alpha)
    p = np.asarray(p_valores, dtype=float)
    if (p.ndim != 1 or any(isinstance(v, (bool, np.bool_)) for v in p_valores)
            or np.isinf(p).any() or ((p < 0) | (p > 1)).any()):
        raise ValueError("P-valores devem ser unidimensionais em [0,1] ou ausentes.")
    validos = ~np.isnan(p)
    ajustados = np.full(p.shape, np.nan)
    rejeita = pd.array([pd.NA] * len(p), dtype="boolean")
    if len(p):
        # Hipóteses não estimáveis ocupam uma posição conservadora na família.
        # O 1 auxiliar não é exposto como p observado/corrigido dessas hipóteses.
        r, corrigidos, _, _ = multipletests(np.where(validos, p, 1.), alpha=alpha, method="holm")
        ajustados[validos] = corrigidos[validos]
        rejeita[validos] = r[validos]
    return pd.DataFrame({"p_valor_holm": ajustados, "rejeita_holm": rejeita})


def epsilon_quadrado(H, n):
    """Convenção explícita do enunciado: ε² = H/(n-1), usando n efetivamente testado."""
    _contagem(n)
    if H is None or n <= 1:
        return None
    if (not isinstance(H, Real) or isinstance(H, (bool, np.bool_))
            or not np.isfinite(H) or H < -1e-12 or H > n - 1 + 1e-12):
        raise ValueError("H fora do domínio para epsilon quadrado.")
    return float(np.clip(H / (n - 1), 0., 1.))


def cliff_delta(U_1, n_1, n_2):
    """δ = 2*U1/(n1*n2)-1; positivo significa valores maiores no primeiro grupo."""
    _contagem(n_1)
    _contagem(n_2)
    if U_1 is None or not n_1 or not n_2:
        return None
    produto = int(n_1) * int(n_2)
    if (not isinstance(U_1, Real) or isinstance(U_1, (bool, np.bool_)) or not np.isfinite(U_1)
            or U_1 < -1e-12 or U_1 > produto + 1e-12):
        raise ValueError("U fora do domínio para Cliff's delta.")
    return float(np.clip(2 * U_1 / produto - 1, -1., 1.))


def magnitude_delta(delta):
    """Cortes do enunciado; a magnitude usa |δ|, mantendo o sinal em outra coluna."""
    if delta is None:
        return None
    if (not isinstance(delta, Real) or isinstance(delta, (bool, np.bool_))
            or not np.isfinite(delta) or abs(delta) > 1):
        raise ValueError("Cliff's delta deve estar em [-1,1].")
    valor = abs(delta)
    return ("desprezivel" if valor < .147 else "pequeno" if valor < .33
            else "medio" if valor < .474 else "grande")


def analisar(dados, *, alpha=base.ALPHA):
    """Corrige globais e todos os contrastes planejados, antes de selecionar o relato."""
    _alpha(alpha)
    bruto = base.analisar(dados, alpha=alpha)
    globais = bruto["globais"].copy(deep=True)
    globais = pd.concat([globais, aplicar_holm(globais["p_valor_bruto"], alpha=alpha)], axis=1)
    globais["familia_holm"] = "globais"
    globais["n_familia"] = len(globais)
    globais["poshoc_elegivel_holm"] = (globais["teste"].eq("kruskal_wallis")
                                        & globais["rejeita_holm"].fillna(False))
    globais["epsilon2"] = [epsilon_quadrado(r.estatistica, r.n) if r.teste == "kruskal_wallis" else None
                            for r in globais.itertuples(index=False)]
    # Delta de comparações diretas com dois grupos pertence à família global;
    # não repetimos a mesma hipótese na família de pós-testes.
    globais["cliff_delta"] = np.nan
    globais["magnitude_delta"] = pd.Series([None] * len(globais), dtype="object")
    for coluna in ("grupo_1", "grupo_2"):
        globais[coluna] = pd.Series([None] * len(globais), dtype="object")
    for coluna in ("n_1", "n_2"):
        globais[coluna] = pd.array([pd.NA] * len(globais), dtype="Int64")
    linhas = []
    for i, r in globais.iterrows():
        fator, metrica = r["fator"], r["metrica"]
        grupo = bruto["grupos"][f"grupo_{fator}"]
        rotulos = bruto["cortes"].loc[(bruto["cortes"]["fator"] == fator)
                                      & bruto["cortes"]["grupo"].notna(), "grupo"].tolist()
        amostras = [dados.loc[grupo == g, metrica].dropna().to_numpy() for g in rotulos]
        if r["teste"] == "mann_whitney_direto":
            delta = cliff_delta(r["estatistica"], len(amostras[0]), len(amostras[1]))
            globais.at[i, "cliff_delta"] = delta
            globais.at[i, "magnitude_delta"] = magnitude_delta(delta)
            globais.loc[i, ["grupo_1", "grupo_2"]] = rotulos
            globais.loc[i, ["n_1", "n_2"]] = list(map(len, amostras))
        if len(amostras) < 3:
            continue
        # Incluir todos os pares evita definir a correção pelo resultado nominal.
        for a, b in combinations(range(len(amostras)), 2):
            x, y = amostras[a], amostras[b]
            teste = base.comparar_grupos([x, y])
            delta = cliff_delta(teste["estatistica"], len(x), len(y))
            linhas.append({"fator": fator, "metrica": metrica, "grupo_1": rotulos[a], "grupo_2": rotulos[b],
                           "n_1": len(x), "n_2": len(y), "U_1": teste["estatistica"],
                           "p_valor_bruto": teste["p_valor_bruto"], "cliff_delta": delta,
                           "magnitude_delta": magnitude_delta(delta), "motivo": teste["motivo"],
                           "executado_na_171": bool(r["poshoc_executado"])})
    pares = pd.DataFrame(linhas, columns=COLUNAS_PARES)
    pares = pd.concat([pares, aplicar_holm(pares["p_valor_bruto"], alpha=alpha)], axis=1)
    pares["familia_holm"] = "pares"
    pares["n_familia"] = len(pares)
    pares["alpha"] = alpha
    por_chave = globais.set_index(["fator", "metrica"])["rejeita_holm"]
    pares["global_rejeita_holm"] = pd.array([por_chave.loc[(r.fator, r.metrica)]
                                            for r in pares.itertuples(index=False)], dtype="boolean")
    pares["relatar_diferenca"] = (pares["global_rejeita_holm"] & pares["rejeita_holm"]).fillna(False)
    familias = pd.DataFrame([
        {"familia": nome, "testes_planejados": len(tabela),
         "testes_estimaveis": int(tabela["p_valor_bruto"].notna().sum()),
         "testes_nao_estimaveis": int(tabela["p_valor_bruto"].isna().sum()),
         "rejeicoes_holm": int(tabela["rejeita_holm"].sum()), "alpha": alpha, "metodo": "holm"}
        for nome, tabela in (("globais", globais), ("pares", pares))
    ])
    return {"base": bruto, "globais": globais, "pares": pares, "familias": familias}
