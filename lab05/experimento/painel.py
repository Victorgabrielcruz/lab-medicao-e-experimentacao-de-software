"""Leitura e visualizações exploratórias do piloto, sem executar a coleta (#305)."""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from experimento import config
from resumir_piloto import resumir

METRICAS = {
    "Tempo total (M1)": ("tempo_total_s", "Tempo total (s)", "Menor é melhor"),
    "Vazão (M2)": ("vazao_ops_s", "Vazão (operações/s)", "Maior é melhor"),
}
CORES = {"DELETE-FULL": "#64748b", "DELETE-NORMAL": "#c88d27",
         "WAL-FULL": "#268c95", "WAL-NORMAL": "#245ba8"}
COMPARACOES = (
    ("H1", "WAL-FULL", "DELETE-FULL"),
    ("H2", "WAL-NORMAL", "WAL-FULL"),
    ("H3", "DELETE-NORMAL", "DELETE-FULL"),
)


@dataclass(frozen=True)
class Piloto:
    dados: pd.DataFrame
    ambiente: dict
    execucao: dict
    resumo: dict


def carregar_piloto(diretorio: Path) -> Piloto:
    """Recalcula e valida o resumo da #304; não lê os resumos publicados."""
    diretorio = Path(diretorio)
    resumo = resumir(diretorio)
    dados = pd.read_csv(diretorio / "resultados.csv")
    ambiente = json.loads((diretorio / "ambiente.json").read_text(encoding="utf-8"))
    execucao = json.loads((diretorio / "execucao.json").read_text(encoding="utf-8"))
    # As colunas abaixo sustentam os gráficos de fatores e o pareamento exibido.
    for cfg in config.CONFIGURACOES:
        grupo = dados[dados.configuracao == cfg.nome]
        if not (grupo.journal_mode.eq(cfg.journal_mode).all()
                and grupo.synchronous.eq(cfg.synchronous).all()):
            raise ValueError("Fatores do CSV não correspondem à configuração declarada.")
    if dados.groupby(["carga", "repeticao"]).semente_carga.nunique().ne(1).any():
        raise ValueError("As configurações não compartilham a semente da carga na rodada.")
    return Piloto(dados, ambiente, execucao, resumo)


def descritiva(dados: pd.DataFrame, coluna: str) -> pd.DataFrame:
    """Resumo por grupo; quartis lineares equivalem à interpolação inclusiva."""
    linhas = []
    for (carga, cfg), grupo in dados.groupby(["carga", "configuracao"], sort=False):
        valores = grupo[coluna]
        q1, q3 = valores.quantile([0.25, 0.75])
        linhas.append({
            "Carga": carga, "Configuração": cfg, "n": len(valores),
            "Mediana": valores.median(), "Q1": q1, "Q3": q3, "IQR": q3 - q1,
            "Média": valores.mean(), "DP": valores.std(ddof=1),
            "Mínimo": valores.min(), "Máximo": valores.max(),
            "CV (%)": 100 * valores.std(ddof=1) / valores.mean(),
        })
    return pd.DataFrame(linhas).sort_values(["Carga", "Configuração"]).reset_index(drop=True)


def comparacoes(dados: pd.DataFrame) -> pd.DataFrame:
    """M3 é razão de medianas, e não mediana das razões; sem inferência no piloto."""
    medianas = dados.groupby(["carga", "configuracao"])["vazao_ops_s"].median()
    linhas = []
    for carga in config.CARGAS:
        for hipotese, tratamento, referencia in COMPARACOES:
            razao = medianas.loc[(carga.nome, tratamento)] / medianas.loc[(carga.nome, referencia)]
            linhas.append({
                "Carga": carga.nome, "Comparação": hipotese,
                "Tratamento": tratamento, "Referência": referencia,
                "M3 (×)": razao, "Ganho de vazão (%)": 100 * (razao - 1),
            })
    return pd.DataFrame(linhas)


def _formatar_grafico(figura, titulo, eixo_y, logaritmica):
    figura.update_layout(
        title=titulo, template="plotly_white", height=360,
        margin=dict(l=20, r=20, t=55, b=35),
        font=dict(family="Arial, sans-serif", color="#253447"),
        yaxis=dict(title=eixo_y, type="log" if logaritmica else "linear"),
        xaxis_title="Configuração", legend_title_text="Sincronização",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    return figura


def distribuicao(dados, coluna, eixo_y, carga, logaritmica=False):
    figura = go.Figure()
    for cfg, cor in CORES.items():
        valores = dados.loc[dados.configuracao == cfg, coluna].tolist()
        figura.add_trace(go.Box(
            y=valores, name=cfg, boxpoints="all", jitter=0.25, pointpos=0,
            marker_color=cor, quartilemethod="linear", showlegend=False,
        ))
    return _formatar_grafico(figura, f"Distribuição · {carga}", eixo_y, logaritmica)


def interacao(dados, coluna, eixo_y, carga, logaritmica=False):
    figura = go.Figure()
    for sincronismo, cor in (("FULL", CORES["WAL-FULL"]), ("NORMAL", CORES["DELETE-NORMAL"])):
        medianas = dados[dados.synchronous == sincronismo].groupby("journal_mode")[coluna].median()
        figura.add_trace(go.Scatter(
            x=list(config.JOURNAL_MODES), y=[medianas[j] for j in config.JOURNAL_MODES],
            name=sincronismo, mode="lines+markers", marker=dict(size=9), line=dict(color=cor),
        ))
    _formatar_grafico(figura, f"Interação exploratória · {carga}", eixo_y, logaritmica)
    figura.update_xaxes(title="journal_mode")
    return figura


def ordem_execucao(dados, coluna, eixo_y, carga):
    figura = go.Figure()
    for cfg, cor in CORES.items():
        grupo = dados[dados.configuracao == cfg].sort_values("ordem_execucao")
        figura.add_trace(go.Scatter(
            x=grupo.ordem_execucao.tolist(), y=grupo[coluna].tolist(),
            name=cfg, mode="markers", marker=dict(size=9, color=cor),
        ))
    _formatar_grafico(figura, f"Medições na ordem de execução · {carga}", eixo_y, False)
    figura.update_layout(legend_title_text="Configuração")
    figura.update_xaxes(title="Posição no plano, incluindo aquecimentos descartados")
    return figura
