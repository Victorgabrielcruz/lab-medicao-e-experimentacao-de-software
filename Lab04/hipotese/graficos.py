"""Gráficos do dashboard de testes de hipótese."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pandas import DataFrame
from scipy.stats import binom, norm

from hipotese.config import ALFA, ALTERNATIVA, CORES_TESTES, META_TAXA_FALHA, SEMENTE, TESTE_BINOMIAL, TESTE_Z
from hipotese.exemplo import ExemploSimulado
from hipotese.q3 import REFERENCIA, VIOLACOES

CORES_DADOS = {"Real": "#64748b", "Simulado sob H₀": "#0f766e"}


def _cor(nome: str, opacidade: float) -> str:
    hexadecimal = CORES_TESTES[nome].lstrip("#")
    r, g, b = (int(hexadecimal[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{opacidade})"


def regiao_binomial(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Suporte completo, massas sob H0 e rejeição pela regra estrita p < alfa.

    sf(k - 1) inclui a massa de k; usar sf(k) excluiria a observação.
    A região pode ser vazia em amostras pequenas devido à discretização.
    """
    k = np.arange(n + 1)
    massas = binom.pmf(k, n, META_TAXA_FALHA)
    rejeicao = binom.sf(k - 1, n, META_TAXA_FALHA) < ALFA
    return k, massas, rejeicao


def _layout(figura: go.Figure, titulo: str, eixo_x: str, eixo_y: str) -> None:
    figura.update_layout(
        title={"text": titulo, "font": {"size": 20}},
        xaxis_title=eixo_x, yaxis_title=eixo_y,
        template="plotly_white", height=510,
        margin={"t": 100, "b": 145, "l": 65, "r": 30},
        legend={"orientation": "h", "yanchor": "top", "y": -0.25, "x": 0},
        hovermode="closest",
    )
    figura.update_yaxes(rangemode="tozero")


def construir_g1(reais, simulados) -> go.Figure:
    """Histogramas binários lado a lado, com bins e escalas idênticos (#267).

    As frequências são calculadas em Python nos bins [-0,5; 0,5; 1,5],
    incluindo categorias vazias. O hover preserva também as contagens.
    """
    amostras = [np.asarray(reais), np.asarray(simulados)]
    for amostra in amostras:
        if amostra.ndim != 1 or amostra.size == 0 or not np.isin(amostra, (0, 1)).all():
            raise ValueError("O G1 requer amostras unidimensionais não vazias de 0 e 1.")
    nomes = tuple(CORES_DADOS)
    figura = make_subplots(
        rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.15,
        subplot_titles=tuple(f"{nome} · {amostra.size} builds" for nome, amostra in zip(nomes, amostras)),
    )
    for coluna, (nome, amostra) in enumerate(zip(nomes, amostras), 1):
        contagens, _ = np.histogram(amostra, bins=[-0.5, 0.5, 1.5])
        frequencias = 100 * contagens / amostra.size
        figura.add_trace(go.Bar(
            x=[0, 1], y=frequencias.tolist(), width=0.9,
            name=nome, marker_color=CORES_DADOS[nome], showlegend=True,
            text=[f"{valor:.2f}%".replace(".", ",") for valor in frequencias],
            textposition="outside", cliponaxis=False,
            customdata=[[int(contagem), int(amostra.size)] for contagem in contagens],
            hovertemplate=(
                "Resultado (0 = passou; 1 = falhou): %{x}<br>"
                "Execuções: %{customdata[0]} de %{customdata[1]}<br>"
                "Frequência: %{y:.2f}%<extra>%{fullData.name}</extra>"
            ),
        ), row=1, col=coluna)
    eixo_x = "Resultado da build (0/1; adimensional)"
    eixo_y = "Frequência relativa de builds (%)"
    _layout(
        figura,
        "G1 · Dados reais × simulados<br>"
        f"<sup>Simulação independente sob H₀: p = {META_TAXA_FALHA:.0%}; semente {SEMENTE}</sup>",
        eixo_x, eixo_y,
    )
    figura.update_annotations(font_size=14)
    figura.update_xaxes(
        title_text=eixo_x, range=[-0.65, 1.65], tickvals=[0, 1],
        ticktext=["0 · Passou", "1 · Falhou"], showgrid=False,
    )
    figura.update_yaxes(
        title_text=eixo_y, range=[0, 110], tickvals=[0, 20, 40, 60, 80, 100],
        ticksuffix="%", showticklabels=True, fixedrange=True,
    )
    return figura


def construir_g3(tipo_i: DataFrame) -> go.Figure:
    """Compara as taxas sob H₀ de Q1 e Q3 com o nível nominal (#273)."""
    situacoes = [REFERENCIA, *VIOLACOES]
    figura = go.Figure()
    for teste in (TESTE_Z, TESTE_BINOMIAL):
        dados = tipo_i.loc[tipo_i["teste"] == teste].set_index("situacao").loc[situacoes]
        taxas = (100 * dados["proporcao_rejeicao"]).tolist()
        figura.add_bar(
            x=situacoes, y=taxas, name=teste, marker_color=CORES_TESTES[teste],
            text=[f"{taxa:.2f}%".replace(".", ",") for taxa in taxas],
            textposition="outside", cliponaxis=False,
            customdata=list(zip(dados["n"], dados["classificacao"])),
            hovertemplate=(
                "%{x} · %{customdata[0]} builds por amostra<br>"
                "Erro tipo I: %{text} (%{customdata[1]})<extra>%{fullData.name}</extra>"
            ),
        )
    _layout(figura, "G3 · Erro tipo I por situação", "Situação simulada (categoria)", "Taxa de erro tipo I (%)")
    figura.add_hline(
        y=100 * ALFA, line_color="#8b8f97", line_dash="dash", line_width=2,
        name=f"Referência: {ALFA:.0%}", showlegend=True,
    )
    figura.update_layout(barmode="group", margin={"t": 70, "b": 110})
    figura.update_yaxes(range=[0, 1.18 * 100 * max(ALFA, tipo_i["proporcao_rejeicao"].max())], ticksuffix="%")
    return figura


def construir_g4(simulacao: DataFrame) -> go.Figure:
    """Compara os dois testes em cada situação, na mesma escala (#274)."""
    paineis = list(simulacao.groupby(["situacao", "n"], sort=False))
    figura = make_subplots(
        rows=1, cols=len(paineis), shared_yaxes=True, horizontal_spacing=0.07,
        subplot_titles=[f"{situacao} · n = {n}" for (situacao, n), _ in paineis],
    )
    for coluna, (_, painel) in enumerate(paineis, 1):
        for teste, simbolo in ((TESTE_Z, "circle"), (TESTE_BINOMIAL, "diamond")):
            curva = painel.loc[painel["teste"] == teste].sort_values("efeito")
            figura.add_trace(go.Scatter(
                x=(100 * curva["efeito"]).tolist(),
                y=(100 * curva["proporcao_rejeicao"]).tolist(),
                mode="lines+markers", name=teste, legendgroup=teste, showlegend=coluna == 1,
                line={"color": CORES_TESTES[teste]}, marker={"symbol": simbolo},
                hovertemplate="Efeito: %{x:g} p.p.<br>Rejeições: %{y:.2f}%<extra>%{fullData.name}</extra>",
            ), row=1, col=coluna)
    _layout(figura, "G4 · Curvas de poder por situação", "Efeito (p.p.)", "Proporção de rejeições (%)")
    figura.update_annotations(font_size=14)
    figura.update_xaxes(title_text="Efeito (p.p.)", tickvals=sorted(set(100 * simulacao["efeito"])))
    figura.update_yaxes(range=[0, 104], tickvals=[0, 20, 40, 60, 80, 100], ticksuffix="%")
    return figura


def construir_g2(exemplo: ExemploSimulado) -> tuple[go.Figure, go.Figure]:
    """Usa o exemplo da #266, sem gerar amostras ou estimar p-valores por Monte Carlo.

    O Z é mostrado contra sua referência normal aproximada. O painel exato
    usa a distribuição discreta de p_hat = X/n; probabilidades são somas de
    massas, não integrais de uma curva contínua.
    """
    if ALTERNATIVA != "greater":
        raise ValueError("O G2 foi definido para a alternativa 'greater' do protocolo.")
    resultados = {resultado.teste: resultado for resultado in exemplo.resultados}
    z = resultados[TESTE_Z]
    exato = resultados[TESTE_BINOMIAL]
    critico = float(norm.isf(ALFA))
    minimo, maximo = min(-4.5, z.estatistica - 1), max(4.5, z.estatistica + 1)
    grade = np.unique(np.r_[np.linspace(minimo, maximo, 2401), z.estatistica, critico])

    normal = go.Figure()
    normal.add_trace(go.Scatter(
        x=grade, y=norm.pdf(grade), mode="lines", name="Referência N(0, 1)",
        line={"color": CORES_TESTES[TESTE_Z], "width": 2},
        hovertemplate="Z = %{x:.3f}<br>Densidade = %{y:.4f}<extra></extra>",
    ))
    for limite, nome, opacidade in (
        (z.estatistica, f"Área do p-valor = {z.pvalor:.5f}", 0.25),
        (critico, f"Rejeição: área α = {ALFA:.2f}", 0.7),
    ):
        cauda = grade[grade >= limite]
        normal.add_trace(go.Scatter(
            x=cauda, y=norm.pdf(cauda), mode="lines", fill="tozeroy",
            fillcolor=_cor(TESTE_Z, opacidade), line={"width": 0}, name=nome,
            hoverinfo="skip",
        ))
    for valor, nome, estilo in (
        (z.estatistica, f"Z observado = {z.estatistica:.3f}", "dot"),
        (critico, f"Limite de rejeição: Z > {critico:.3f}", "dash"),
    ):
        normal.add_trace(go.Scatter(
            x=[valor, valor], y=[0, float(norm.pdf(valor))], mode="lines", name=nome,
            line={"color": "#8b8f97", "dash": estilo, "width": 2}, hoverinfo="skip",
        ))
    _layout(
        normal, f"G2 · {TESTE_Z} — referência sob H₀<br><sup>p₀ = 5%; n = {z.n}; alternativa à direita</sup>",
        "Estatística Z (adimensional)", "Densidade de probabilidade (por unidade de Z)",
    )
    normal.update_xaxes(range=[minimo, maximo])

    k, massas, rejeicao = regiao_binomial(exato.n)
    pvalor = k >= exato.falhas
    criticos = k[rejeicao]
    k_critico = int(criticos[0]) if criticos.size else None
    area_rejeicao = float(massas[rejeicao].sum())
    binomial = go.Figure()
    for mascara, nome, opacidade in (
        (np.ones(k.size, dtype=bool), "Massas sob H₀", 0.15),
        (pvalor, f"Soma do p-valor = {exato.pvalor:.5f}", 0.4),
        (rejeicao, f"Rejeição: soma = {area_rejeicao:.5f} (≤ 0,05)", 0.8),
    ):
        binomial.add_trace(go.Bar(
            x=100 * k[mascara] / exato.n, y=100 * massas[mascara],
            width=0.9 * 100 / exato.n, name=nome,
            marker={"color": _cor(TESTE_BINOMIAL, opacidade),
                    "line": {"color": CORES_TESTES[TESTE_BINOMIAL], "width": 1}},
            customdata=k[mascara],
            hovertemplate="Falhas = %{customdata}<br>p̂ = %{x:.2f}%<br>Probabilidade = %{y:.4f}%<extra></extra>",
        ))
    for valor, nome, estilo in (
        (exato.falhas, f"Exemplo: {exato.falhas} falhas; p̂ = {exato.proporcao:.2%}", "dot"),
        (k_critico, f"Rejeição: a partir de {k_critico} falhas" if k_critico is not None else "", "dash"),
    ):
        if valor is not None:
            binomial.add_trace(go.Scatter(
                x=[100 * valor / exato.n] * 2, y=[0, 100 * float(binom.pmf(valor, exato.n, META_TAXA_FALHA))],
                mode="lines", name=nome, line={"color": "#8b8f97", "dash": estilo, "width": 2}, hoverinfo="skip",
            ))
    _layout(
        binomial, f"G2 · {TESTE_BINOMIAL} — distribuição de p̂ sob H₀<br><sup>X ∼ Binomial({exato.n}, 0,05); p̂ = X/n</sup>",
        "Proporção de builds com falha p̂ (%)", "Probabilidade de cada valor de p̂ (%)",
    )
    # Zoom visual; todos os n+1 valores continuam nos dados e nas somas.
    maior_k = min(exato.n, max(int(binom.ppf(1 - 1e-7, exato.n, META_TAXA_FALHA)), exato.falhas + 3, (k_critico or 0) + 3))
    binomial.update_layout(barmode="overlay")
    binomial.update_xaxes(range=[-50 / exato.n, 100 * (maior_k + 0.5) / exato.n])
    return normal, binomial
