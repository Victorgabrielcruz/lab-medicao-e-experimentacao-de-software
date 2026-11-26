"""Testes pareados, efeitos e auditoria temporal do plano da #305 (#309).

Os valores-p e IC são condicionais à independência entre rodadas. Diagnósticos
sem alerta não comprovam esse pressuposto; alertas suspendem conclusões.
"""

import math
import platform
from dataclasses import dataclass
from numbers import Integral

import numpy as np
import pandas as pd
import scipy
from scipy.stats import binomtest, rankdata

from experimento import config
from experimento.validacao import COMPARACOES

N_BOOTSTRAP = 10_000
NIVEL_IC = 0.95


@dataclass(frozen=True)
class Analise:
    testes: pd.DataFrame
    efeitos: pd.DataFrame
    medianas: pd.DataFrame
    auditoria: pd.DataFrame
    diagnosticos: pd.DataFrame
    series: pd.DataFrame
    parametros: dict

    def como_dict(self):
        resultado = {"parametros": self.parametros}
        for nome in ("testes", "efeitos", "medianas", "auditoria", "diagnosticos", "series"):
            tabela = getattr(self, nome).astype(object)
            resultado[nome] = tabela.where(pd.notna(tabela), None).to_dict("records")
        return resultado


def _vetor(valores):
    vetor = np.asarray(valores, dtype=float)
    if vetor.ndim != 1 or len(vetor) == 0 or not np.isfinite(vetor).all():
        raise ValueError("Esperado vetor não vazio de valores finitos.")
    return vetor


def holm(pvalores):
    """Ajuste step-down, monotônico e devolvido na ordem original."""
    p = _vetor(pvalores)
    if np.any((p < 0) | (p > 1)):
        raise ValueError("Valores-p devem estar entre zero e um.")
    ordem = np.argsort(p, kind="stable")
    ajustados = np.minimum(1, np.maximum.accumulate(p[ordem] * np.arange(len(p), 0, -1)))
    resultado = np.empty_like(p)
    resultado[ordem] = ajustados
    return resultado


def teste_sinais(diferencas):
    """H0: P(d > 0 | d != 0) = 0,5; bilateral, com empates reportados."""
    d = _vetor(diferencas)
    ganhos, perdas = int(np.sum(d > 0)), int(np.sum(d < 0))
    n = ganhos + perdas
    resultado = {"n_pares": len(d), "ganhos": ganhos, "perdas": perdas,
                 "empates": len(d) - n, "n_efetivo": n,
                 "p_bruto": 1.0, "probabilidade": None, "ic_inf": None, "ic_sup": None}
    if n:
        teste = binomtest(ganhos, n, p=0.5, alternative="two-sided")
        intervalo = teste.proportion_ci(confidence_level=NIVEL_IC, method="exact")
        resultado.update(p_bruto=float(teste.pvalue), probabilidade=ganhos / n,
                         ic_inf=float(intervalo.low), ic_sup=float(intervalo.high))
    return resultado


def teste_sequencias(sinais):
    """Runs exato condicional às contagens; p bilateral = 2 × menor cauda.

    Zeros são removidos somente deste diagnóstico. Série sem dois sinais é
    inconclusiva, sem valor-p artificial. Contagens usam a distribuição combinatória.
    """
    s = _vetor(sinais)
    s = np.sign(s[s != 0])
    a, b = int(np.sum(s > 0)), int(np.sum(s < 0))
    r = int(1 + np.sum(s[1:] != s[:-1])) if len(s) else 0
    resultado = {"n": len(s), "positivos": a, "negativos": b, "runs": r, "p_bruto": None}
    if not a or not b:
        return resultado

    def c(n, k):
        return math.comb(n, k) if 0 <= k <= n else 0

    contagens = {}
    for numero in range(2, a + b + 1):
        k = numero // 2
        contagens[numero] = (2 * c(a - 1, k - 1) * c(b - 1, k - 1) if numero % 2 == 0
                            else c(a - 1, k) * c(b - 1, k - 1) + c(a - 1, k - 1) * c(b - 1, k))
    total = c(a + b, a)
    inferior = sum(q for numero, q in contagens.items() if numero <= r)
    superior = sum(q for numero, q in contagens.items() if numero >= r)
    resultado["p_bruto"] = min(1.0, 2 * min(inferior, superior) / total)
    return resultado


def _correlacao(x, y):
    if len(x) < 2 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def diagnosticar(diferencas):
    d = _vetor(diferencas)
    sinais = np.sign(d)
    metade = len(d) // 2
    return {
        "spearman_diferencas": _correlacao(rankdata(d), np.arange(len(d))),
        "lag1_diferencas": _correlacao(d[:-1], d[1:]),
        "lag1_sinais": _correlacao(sinais[:-1], sinais[1:]),
        "mediana_primeira_metade": float(np.median(d[:metade])) if metade else None,
        "mediana_segunda_metade": float(np.median(d[metade:])),
    }


def preparar_blocos(dados):
    """Exige a coleta completa, um ambiente e as mesmas sementes exatas em cada rodada."""
    campos = {"carga", "configuracao", "repeticao", "semente_carga", "n_operacoes",
              "tempo_total_s", "vazao_ops_s", "data_hora_utc"}
    if not campos <= set(dados.columns):
        raise ValueError("Colunas obrigatórias ausentes para o pareamento.")
    if dados[list(campos)].isna().any().any():
        raise ValueError("Campos ausentes na análise.")
    if len(dados) != len(config.combinacoes()) * config.N_REPETICOES:
        raise ValueError("A inferência exige 360 medições da coleta completa; não usar o piloto.")
    if set(dados.carga) != {c.nome for c in config.CARGAS}:
        raise ValueError("Cargas fora do protocolo.")
    if set(dados.configuracao) != {c.nome for c in config.CONFIGURACOES}:
        raise ValueError("Configurações fora do protocolo.")
    if dados.duplicated(["carga", "configuracao", "repeticao"]).any():
        raise ValueError("Pares duplicados.")
    for campo in ("repeticao", "semente_carga"):
        if not all(isinstance(v, Integral) and not isinstance(v, bool) for v in dados[campo]):
            raise ValueError(f"{campo} deve conter inteiros exatos, sem conversão por float.")
    for campo in ("data_hora_utc", "sistema", "maquina", "sqlite_version", "python_version"):
        if campo in dados and dados[campo].nunique(dropna=False) != 1:
            raise ValueError("Não misturar coletas ou ambientes na inferência.")
    valores = dados[["tempo_total_s", "vazao_ops_s", "n_operacoes"]].to_numpy(dtype=float)
    if not np.isfinite(valores).all() or (valores <= 0).any():
        raise ValueError("Métricas e contagens devem ser positivas e finitas.")
    if not np.allclose(valores[:, 1], valores[:, 2] / valores[:, 0], rtol=1e-12, atol=0):
        raise ValueError("Vazão inconsistente com tempo e operações.")
    blocos = {}
    configuracoes = [c.nome for c in config.CONFIGURACOES]
    rodadas = list(range(1, config.N_REPETICOES + 1))
    for carga in config.CARGAS:
        grupo = dados[dados.carga == carga.nome]
        if not grupo.n_operacoes.eq(carga.n_operacoes).all():
            raise ValueError("Volume de operações diferente do protocolo.")
        if any(set(g.repeticao) != set(rodadas) for _, g in grupo.groupby("configuracao")):
            raise ValueError("Rodadas ausentes ou inesperadas.")
        if grupo.groupby("repeticao").semente_carga.nunique().ne(1).any():
            raise ValueError("Sementes incompatíveis entre configurações da mesma rodada.")
        blocos[carga.nome] = tuple(
            grupo.pivot(index="repeticao", columns="configuracao", values=metrica)
            .loc[rodadas, configuracoes].to_numpy(dtype=float)
            for metrica in ("tempo_total_s", "vazao_ops_s")
        )
    return blocos


def _intervalo(amostras):
    return tuple(float(v) for v in np.quantile(amostras, [0.025, 0.975], method="linear"))


def analisar(dados, *, n_bootstrap=N_BOOTSTRAP, semente=config.SEMENTE):
    if not isinstance(n_bootstrap, Integral) or isinstance(n_bootstrap, bool) or n_bootstrap < 1:
        raise ValueError("Número de reamostragens deve ser inteiro positivo.")
    if not isinstance(semente, Integral) or isinstance(semente, bool) or semente < 0:
        raise ValueError("Semente deve ser inteiro não negativo.")
    blocos = preparar_blocos(dados)
    testes, efeitos, medianas, auditoria, diagnosticos, series = [], [], [], [], [], []
    nomes = [c.nome for c in config.CONFIGURACOES]
    for indice_carga, carga in enumerate(config.CARGAS):
        tempos, vazoes = blocos[carga.nome]
        rng = np.random.default_rng(np.random.SeedSequence([semente, indice_carga]))
        # Uma rodada inteira nas quatro configurações e nas duas métricas por índice.
        indices = rng.integers(0, config.N_REPETICOES, size=(n_bootstrap, config.N_REPETICOES))
        boot_tempo = np.median(tempos[indices], axis=1)
        boot_vazao = np.median(vazoes[indices], axis=1)
        for metrica, matriz, amostras, unidade in (
            ("M1", tempos, boot_tempo, "s"), ("M2", vazoes, boot_vazao, "operações/s"),
        ):
            for i, nome in enumerate(nomes):
                inferior, superior = _intervalo(amostras[:, i])
                medianas.append(dict(carga=carga.nome, configuracao=nome, metrica=metrica,
                                     unidade=unidade, estimativa=float(np.median(matriz[:, i])),
                                     ic_inf=inferior, ic_sup=superior))
        for hipotese, tratamento, referencia in COMPARACOES:
            t, r = nomes.index(tratamento), nomes.index(referencia)
            chave = dict(carga=carga.nome, hipotese=hipotese)
            d = vazoes[:, t] - vazoes[:, r]
            sinais = teste_sinais(d)
            testes.append({**chave, "tratamento": tratamento, "referencia": referencia,
                           **{k: v for k, v in sinais.items() if k not in ("probabilidade", "ic_inf", "ic_sup")}})
            diagnosticos.append({**chave, **diagnosticar(d)})
            for i, valor in enumerate(d, 1):
                series.append({**chave, "rodada": i, "diferenca_m2": float(valor), "sinal": int(np.sign(valor))})
            for tipo, sequencia in (("sinais", np.sign(d)), ("diferenças em torno da mediana", d - np.median(d))):
                auditoria.append({**chave, "serie": tipo, **teste_sequencias(sequencia)})

            def efeito(nome, unidade, estimativa, intervalo, metodo="bootstrap pareado percentil"):
                inferior, superior = intervalo
                efeitos.append({**chave, "efeito": nome, "unidade": unidade,
                                "estimativa": estimativa, "ic_inf": inferior, "ic_sup": superior,
                                "metodo_ic": metodo})

            p, inferior, superior = sinais["probabilidade"], sinais["ic_inf"], sinais["ic_sup"]
            efeito("Probabilidade de ganho", "proporção", p, (inferior, superior), "binomial exato")
            efeito("Efeito dos sinais (2p−1)", "adimensional", None if p is None else 2 * p - 1,
                   (None if inferior is None else 2 * inferior - 1,
                    None if superior is None else 2 * superior - 1), "transformação do IC binomial exato")
            for nome, unidade, vetor in (
                ("Diferença M1", "s", tempos[:, t] - tempos[:, r]),
                ("Redução M1", "%", 100 * (1 - tempos[:, t] / tempos[:, r])),
                ("Diferença M2", "operações/s", d),
            ):
                efeito(nome, unidade, float(np.median(vetor)), _intervalo(np.median(vetor[indices], axis=1)))
            razao = float(np.median(vazoes[:, t]) / np.median(vazoes[:, r]))
            boot_razao = boot_vazao[:, t] / boot_vazao[:, r]
            efeito("M3", "×", razao, _intervalo(boot_razao))
            efeito("Ganho M2", "%", 100 * (razao - 1), _intervalo(100 * (boot_razao - 1)))

    # Família confirmatória planejada: exatamente nove testes, nunca por filtro do painel.
    for linha, ajustado in zip(testes, holm([t["p_bruto"] for t in testes])):
        linha["p_holm"] = float(ajustado)
        linha["rejeita_condicional"] = bool(ajustado < config.ALFA)
    # Família diagnóstica separada: 18 posições. Diagnósticos indefinidos recebem 1
    # apenas no ajuste conservador, mas continuam sem valor-p na apresentação.
    for linha, ajustado in zip(auditoria, holm([a["p_bruto"] if a["p_bruto"] is not None else 1 for a in auditoria])):
        linha["p_holm"] = None if linha["p_bruto"] is None else float(ajustado)
        linha["alerta"] = linha["p_holm"] is not None and ajustado < config.ALFA
    for linha in testes:
        alerta = any(a["alerta"] for a in auditoria if (a["carga"], a["hipotese"]) == (linha["carga"], linha["hipotese"]))
        linha["alerta_temporal"] = alerta
        linha["decisao"] = ("Conclusão confirmatória suspensa: alerta temporal" if alerta
                            else "Sem pares informativos" if linha["n_efetivo"] == 0
                            else "Rejeitar H0 (condicional)" if linha["rejeita_condicional"]
                            else "Não rejeitar H0 (condicional)")
    parametros = {
        "alfa": config.ALFA, "nivel_ic": NIVEL_IC, "n_bootstrap": int(n_bootstrap),
        "semente": int(semente), "familia_testes": 9, "familia_diagnosticos": 18,
        "metodo": "sinais pareados, binomial exato bilateral; Holm nas nove comparações",
        "bootstrap": "percentil; mesmos índices de rodadas nas quatro configurações por carga; SeedSequence([semente, índice_carga])",
        "escopo": "Valores-p e IC condicionais à independência entre rodadas; diagnóstico sem alerta não comprova independência. IC marginais, sem ajuste simultâneo.",
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "pandas": pd.__version__,
    }
    return Analise(*(pd.DataFrame(t) for t in (testes, efeitos, medianas, auditoria, diagnosticos, series)), parametros)
