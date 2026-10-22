"""RQ06: quartis por fator, Kruskal-Wallis e pós-testes Mann-Whitney (#171).

As saídas contêm p-valores brutos; Holm e tamanhos de efeito pertencem à #172.
"""

import hashlib
import io
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from pipeline.dataset_csv import indice, timestamp

FATORES = ("estrelas", "contribuidores", "idade_dias")
METRICAS = ("deployment_frequency", "lead_time_a", "lead_time_b", "cfr_a", "cfr_b", "tempo_recuperacao")
COLUNAS_POSTHOC = ("fator", "metrica", "grupo_1", "grupo_2", "n_1", "n_2", "U_1",
                   "p_valor_bruto", "diferenca_nominal", "alpha", "metodo")
COLUNAS_RESUMOS = ("fator", "metrica", "grupo", "n_grupo", "n", "ausentes_metrica_no_grupo", "q1", "mediana", "q3")
ALPHA = 0.05
MINIMO_GRUPO = 5


def carregar_dataset(caminho):
    """Lê o CSV uma vez e valida identidade, janela e campos usados da RQ06."""
    conteudo = Path(caminho).read_bytes()
    dados = pd.read_csv(io.BytesIO(conteudo))
    obrigatorias = {"id", "full_name", "janela_inicio", "janela_fim_exclusivo", *FATORES, *METRICAS}
    if obrigatorias - set(dados.columns):
        raise ValueError(f"Colunas ausentes para RQ06: {sorted(obrigatorias - set(dados.columns))}")
    if dados.empty:
        raise ValueError("Dataset vazio para RQ06.")
    indice(dados[["id", "full_name"]].to_dict("records"))
    if dados["full_name"].str.lower().duplicated().any():
        raise ValueError("Nome de repositório duplicado.")
    limites = []
    for coluna in ("janela_inicio", "janela_fim_exclusivo"):
        valores = {timestamp(v) for v in dados[coluna]}
        if len(valores) != 1:
            raise ValueError("Janela divergente entre repositórios.")
        limites.append(next(iter(valores)))
    if limites[0] >= limites[1]:
        raise ValueError("Início deve ser anterior ao fim exclusivo.")
    for coluna in (*FATORES, *METRICAS):
        valores = pd.to_numeric(dados[coluna], errors="raise")
        presentes = valores.dropna()
        if (pd.api.types.is_bool_dtype(valores) or not np.isfinite(presentes).all()
                or (presentes < 0).any() or (coluna.startswith("cfr_") and (presentes > 1).any())
                or (coluna in FATORES and (presentes % 1 != 0).any())):
            raise ValueError(f"Valor fora do domínio em {coluna}.")
        dados[coluna] = valores
    dados = dados.sort_values("id").reset_index(drop=True)
    dados.attrs["csv_sha256"] = hashlib.sha256(conteudo).hexdigest()
    return dados


def agrupar_quartis(dados):
    """Calcula cortes na população do fator, sem separar valores empatados por ID."""
    grupos = dados[["id", "full_name"]].copy()
    linhas = []
    for fator in FATORES:
        valores = dados[fator].dropna()
        atribuicao = pd.Series(pd.NA, index=dados.index, dtype="object")
        comuns = {"fator": fator, "n_populacao": len(dados), "n_fator": len(valores),
                  "ausentes_fator": len(dados) - len(valores)}
        if valores.empty:
            linhas.append(comuns | {"grupo": None, "limite_inferior": None, "limite_superior": None,
                                     "inclui_inferior": None, "n_grupo": 0, "grupos_efetivos": 0,
                                     "motivo": "fator_sem_valores"})
        elif valores.nunique() == 1:
            atribuicao.loc[valores.index] = "G1"
            linhas.append(comuns | {"grupo": "G1", "limite_inferior": float(valores.iloc[0]),
                                     "limite_superior": float(valores.iloc[0]), "inclui_inferior": True,
                                     "n_grupo": len(valores), "grupos_efetivos": 1, "motivo": "fator_constante"})
        else:
            codigos, limites = pd.qcut(valores, 4, labels=False, retbins=True, duplicates="drop")
            ocupados = sorted(codigos.dropna().unique())
            for ordem, codigo in enumerate(ocupados):
                rotulo = f"Q{ordem + 1}" if len(ocupados) == 4 else f"G{ordem + 1}"
                mascara = codigos == codigo
                atribuicao.loc[codigos.index[mascara]] = rotulo
                i = int(codigo)
                linhas.append(comuns | {"grupo": rotulo, "limite_inferior": float(limites[i]),
                                         "limite_superior": float(limites[i + 1]), "inclui_inferior": i == 0,
                                         "n_grupo": int(mascara.sum()), "grupos_efetivos": len(ocupados),
                                         "motivo": None if len(ocupados) == 4 else "quartis_reduzidos_por_empates_ou_poucos_valores"})
        grupos[fator] = dados[fator]
        grupos[f"grupo_{fator}"] = atribuicao
    return grupos, pd.DataFrame(linhas)


def comparar_grupos(amostras, *, minimo_grupo=MINIMO_GRUPO):
    """Teste global; pequenos grupos ou KW constante ficam explicitamente não estimáveis."""
    if type(minimo_grupo) is not int or minimo_grupo < 5:
        raise ValueError("Mínimo por grupo deve ser inteiro >= 5 para a aproximação assintótica.")
    valores = [np.asarray(v, dtype=float) for v in amostras]
    if any(v.ndim != 1 or not np.isfinite(v).all() for v in valores):
        raise ValueError("Grupos devem ser vetores finitos sem nulos.")
    resultado = {"teste": None, "estatistica": None, "p_valor_bruto": None,
                 "minimo_grupo": minimo_grupo, "motivo": None}
    if len(valores) < 2:
        return resultado | {"motivo": "menos_de_dois_grupos"}
    if any(len(v) < minimo_grupo for v in valores):
        return resultado | {"motivo": "grupo_abaixo_do_minimo"}
    if len(valores) == 2:
        ret = stats.mannwhitneyu(*valores, alternative="two-sided", method="asymptotic",
                                 use_continuity=True, nan_policy="raise")
        teste = "mann_whitney_direto"
    else:
        if np.unique(np.concatenate(valores)).size == 1:
            return resultado | {"motivo": "todos_os_valores_iguais"}
        ret = stats.kruskal(*valores, nan_policy="raise")
        teste = "kruskal_wallis"
    return resultado | {"teste": teste, "estatistica": float(ret.statistic), "p_valor_bruto": float(ret.pvalue)}


def analisar(dados, *, alpha=ALPHA):
    """18 testes planejados (3 fatores x 6 variantes); pós-testes se p bruto < alpha."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not 0 < alpha < 1:
        raise ValueError("Alpha deve estar entre 0 e 1.")
    grupos, cortes = agrupar_quartis(dados)
    globais, resumos, pos_testes = [], [], []
    for fator in FATORES:
        coluna = grupos[f"grupo_{fator}"]
        rotulos = cortes.loc[(cortes["fator"] == fator) & cortes["grupo"].notna(), "grupo"].tolist()
        for metrica in METRICAS:
            amostras = []
            for rotulo in rotulos:
                serie = dados.loc[coluna == rotulo, metrica].dropna()
                amostras.append(serie.to_numpy())
                q = serie.quantile([.25, .5, .75]) if len(serie) else pd.Series([np.nan] * 3, index=[.25, .5, .75])
                resumos.append({"fator": fator, "metrica": metrica, "grupo": rotulo,
                                "n_grupo": int((coluna == rotulo).sum()), "n": len(serie),
                                "ausentes_metrica_no_grupo": int((coluna == rotulo).sum()) - len(serie),
                                "q1": q.loc[.25], "mediana": q.loc[.5], "q3": q.loc[.75]})
            resultado = comparar_grupos(amostras)
            p = resultado["p_valor_bruto"]
            diferenca = p < alpha if p is not None else None
            executar_pos = resultado["teste"] == "kruskal_wallis" and diferenca is True
            validos_fator = coluna.notna()
            globais.append({"fator": fator, "metrica": metrica, "n_populacao": len(dados),
                            "ausentes_fator": int((~validos_fator).sum()),
                            "ausentes_metrica_com_fator": int((validos_fator & dados[metrica].isna()).sum()),
                            "n": sum(map(len, amostras)), "grupos": len(amostras),
                            "menor_grupo": min(map(len, amostras), default=0), **resultado,
                            "alpha": alpha, "diferenca_nominal": diferenca, "poshoc_executado": executar_pos,
                            "motivo_poshoc": ("p_bruto_menor_alpha" if executar_pos else "comparacao_direta" if resultado["teste"] == "mann_whitney_direto"
                                              else "teste_nao_estimavel" if p is None else "sem_diferenca_nominal")})
            if executar_pos:
                for i, j in combinations(range(len(amostras)), 2):
                    a, b = amostras[i], amostras[j]
                    r = stats.mannwhitneyu(a, b, alternative="two-sided", method="asymptotic",
                                           use_continuity=True, nan_policy="raise")
                    pos_testes.append({"fator": fator, "metrica": metrica, "grupo_1": rotulos[i],
                                       "grupo_2": rotulos[j], "n_1": len(a), "n_2": len(b),
                                       "U_1": float(r.statistic), "p_valor_bruto": float(r.pvalue),
                                       "diferenca_nominal": bool(r.pvalue < alpha), "alpha": alpha,
                                       "metodo": "assintotico_bilateral_empates_continuidade"})
    return {"grupos": grupos, "cortes": cortes, "resumos": pd.DataFrame(resumos, columns=COLUNAS_RESUMOS),
            "globais": pd.DataFrame(globais), "pares": pd.DataFrame(pos_testes, columns=COLUNAS_POSTHOC)}
