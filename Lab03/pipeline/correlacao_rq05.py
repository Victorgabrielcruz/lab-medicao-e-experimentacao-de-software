"""RQ05: frequência de deploy versus CFR, por repositório e variante (#170)."""

import hashlib
import io
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

METRICAS = ("deployment_frequency", "cfr_a", "cfr_b")
INDICADORES = ("coleta_incompleta", "calculo_parcial")
COLUNAS = ("id", "full_name", "janela_inicio", "janela_fim_exclusivo", *METRICAS, *INDICADORES)
PERMUTACOES = 99_999
SEMENTE = 170


def carregar_dataset(caminho):
    """Valida os campos usados da exportação; preserva zero e rejeita dados inválidos."""
    conteudo = Path(caminho).read_bytes()
    dados = pd.read_csv(io.BytesIO(conteudo))
    faltantes = set(COLUNAS) - set(dados.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes para RQ05: {sorted(faltantes)}")
    if dados.empty:
        raise ValueError("Dataset vazio para RQ05.")
    ids = pd.to_numeric(dados["id"], errors="raise")
    if (pd.api.types.is_bool_dtype(ids) or not np.isfinite(ids).all()
            or (ids <= 0).any() or (ids % 1 != 0).any() or ids.duplicated().any()):
        raise ValueError("IDs devem ser inteiros positivos e únicos.")
    dados["id"] = ids.astype("int64")
    if not dados["full_name"].map(lambda v: isinstance(v, str) and bool(v.strip()) and "/" in v).all():
        raise ValueError("Nome de repositório inválido.")
    if dados["full_name"].str.lower().duplicated().any():
        raise ValueError("Repositório duplicado no CSV.")
    limites = []
    for coluna in ("janela_inicio", "janela_fim_exclusivo"):
        valores = dados[coluna].drop_duplicates()
        if len(valores) != 1 or pd.isna(valores.iloc[0]):
            raise ValueError("Janela ausente ou divergente entre repositórios.")
        data = pd.Timestamp(valores.iloc[0])
        if data.tzinfo is None:
            raise ValueError("Janela deve informar fuso horário.")
        limites.append(data)
    if limites[0] >= limites[1]:
        raise ValueError("Janela deve ter início anterior ao fim exclusivo.")
    for coluna in METRICAS:
        valores = pd.to_numeric(dados[coluna], errors="raise")
        presentes = valores.dropna()
        if (pd.api.types.is_bool_dtype(valores) or not np.isfinite(presentes).all()
                or (presentes < 0).any() or (coluna.startswith("cfr") and (presentes > 1).any())):
            raise ValueError(f"Valor fora do domínio em {coluna}.")
        dados[coluna] = valores
    for coluna in INDICADORES:
        if not pd.api.types.is_bool_dtype(dados[coluna]):
            raise ValueError(f"Indicador booleano inválido em {coluna}.")
    dados = dados.sort_values("id").reset_index(drop=True)
    dados.attrs["csv_sha256"] = hashlib.sha256(conteudo).hexdigest()
    return dados


def pares_variantes(dados, variante, sem_indicadores=False):
    """Exclusão por par DF/CFR; nulo em outra métrica não elimina um repositório."""
    if variante not in ("a", "b"):
        raise ValueError("Variante da CFR deve ser a ou b.")
    universo = dados.loc[~dados[list(INDICADORES)].any(axis=1)] if sem_indicadores else dados
    coluna = f"cfr_{variante}"
    pares = universo.dropna(subset=["deployment_frequency", coluna])
    pares = pares[["id", "full_name", "deployment_frequency", coluna, *INDICADORES]].copy()
    pares = pares.rename(columns={coluna: "cfr"}).sort_values("id").reset_index(drop=True)
    pares["variante"] = variante
    pares.attrs["n_universo"] = len(universo)
    return pares


def spearman(x, y, *, permutacoes=PERMUTACOES, semente=SEMENTE):
    """rho/p assintótico do SciPy e verificação bilateral por permutação de pares."""
    if type(permutacoes) is not int or permutacoes < 1:
        raise ValueError("Permutações deve ser um inteiro positivo.")
    if type(semente) is not int or semente < 0:
        raise ValueError("Semente deve ser um inteiro não negativo.")
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise ValueError("As duas métricas devem ser vetores pareados de mesmo tamanho.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Spearman requer pares finitos, sem nulos.")
    ret = {"n": len(x), "rho": None, "p_valor": None, "p_permutacao": None,
           "permutacoes_solicitadas": permutacoes, "permutacoes_realizadas": 0,
           "semente": semente, "metodo_permutacao": None, "motivo": None}
    if len(x) < 3:
        return ret | {"motivo": "menos_de_tres_pares"}
    if np.unique(x).size < 2 or np.unique(y).size < 2:
        return ret | {"motivo": "variavel_constante"}
    resultado = stats.spearmanr(x, y, alternative="two-sided", nan_policy="raise")
    # Spearman é Pearson dos ranks médios. Permutar ranks preserva os empates
    # e evita recalcular a ordenação em cada uma das 99.999 permutações.
    rx, ry = stats.rankdata(x, method="average"), stats.rankdata(y, method="average")
    rx, ry = rx - rx.mean(), ry - ry.mean()
    denominador = np.linalg.norm(rx) * np.linalg.norm(ry)

    def estatistica(y_permutado, axis=-1):
        return np.sum(rx * y_permutado, axis=axis) / denominador

    perm = stats.permutation_test(
        (ry,), estatistica, permutation_type="pairings", vectorized=True,
        n_resamples=permutacoes, batch=256, alternative="two-sided",
        rng=np.random.default_rng(semente),
    )
    return ret | {"rho": float(resultado.statistic), "p_valor": float(resultado.pvalue),
                  "p_permutacao": float(perm.pvalue), "permutacoes_realizadas": len(perm.null_distribution),
                  "metodo_permutacao": "exata" if math.factorial(len(x)) <= permutacoes else "aleatoria"}


def analisar(dados, *, permutacoes=PERMUTACOES, semente=SEMENTE):
    """Análise principal e sensibilidade sem indicadores globais de incompletude."""
    linhas, tabelas = [], []
    for sem_indicadores in (False, True):
        recorte = "sem_indicadores" if sem_indicadores else "principal"
        for variante in ("a", "b"):
            pares = pares_variantes(dados, variante, sem_indicadores)
            resultado = spearman(pares["deployment_frequency"], pares["cfr"],
                                 permutacoes=permutacoes, semente=semente)
            linhas.append({"recorte": recorte, "variante": variante, "x": "deployment_frequency",
                           "y": f"cfr_{variante}", "n_universo": pares.attrs["n_universo"],
                           "excluidos_por_nulos": pares.attrs["n_universo"] - len(pares),
                           "fora_do_recorte": len(dados) - pares.attrs["n_universo"],
                           **resultado})
            tabelas.append(pares.assign(recorte=recorte))
    return pd.DataFrame(linhas), pd.concat(tabelas, ignore_index=True)


def grafico_dispersao(pares, resumo):
    """Dois painéis com os mesmos pares da análise principal; CFR zero preservada."""
    import matplotlib.pyplot as plt

    fig, eixos = plt.subplots(1, 2, figsize=(9, 3.7), sharey=True, layout="constrained")
    principais = pares.loc[pares["recorte"] == "principal"]
    for ax, variante in zip(eixos, ("a", "b")):
        p = principais.loc[principais["variante"] == variante]
        r = resumo.loc[(resumo["recorte"] == "principal") & (resumo["variante"] == variante)].iloc[0]
        ax.scatter(p["deployment_frequency"], p["cfr"], s=15, color="#333333", alpha=0.5, edgecolors="none")
        # O CSV atual tem DF > 0. Em outra execução, symlog mantém zeros visíveis.
        escala = "log" if not p.empty and p["deployment_frequency"].gt(0).all() else "symlog"
        ax.set_xscale(escala, **({"linthresh": 0.1} if escala == "symlog" else {}))
        ax.set_ylim(-0.035, 1.035)
        ax.set_xlabel(f"Frequência de deploy (releases/semana, {escala})")
        ax.set_title(f"CFR ({variante}) — {'runs' if variante == 'a' else 'releases corretivas'}")
        texto = (f"ρ = {r['rho']:.3f}\np = {r['p_valor']:.3g}\nn = {int(r['n'])}"
                 if pd.notna(r["rho"]) else f"Não estimável\nn = {int(r['n'])}")
        ax.text(0.04, 0.96, texto, transform=ax.transAxes, va="top", fontsize=9,
                bbox={"facecolor": "white", "alpha": 0.9, "edgecolor": "none"})
        ax.grid(True, color="#dddddd", linewidth=0.5)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)
    eixos[0].set_ylabel("Taxa de falha de mudanças (fração)")
    return fig
