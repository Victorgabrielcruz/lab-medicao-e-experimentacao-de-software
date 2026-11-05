"""G2: distribuições de referência, rejeição e p-valor do exemplo (#268)."""

import numpy as np
import plotly.graph_objects as go
from scipy.stats import binom, norm

from hipotese.config import ALFA, ALTERNATIVA, CORES_TESTES, META_TAXA_FALHA, TESTE_BINOMIAL, TESTE_Z
from hipotese.exemplo import ExemploSimulado


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
