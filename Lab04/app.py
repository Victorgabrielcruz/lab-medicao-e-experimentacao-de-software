"""Dashboard do Lab04 — testes de hipótese por dentro (par P4).

Execução, a partir da pasta Lab04: ``python executar.py``
"""

import streamlit as st
from scipy.stats import norm

from hipotese import poder, q3
from hipotese.cenario import carregar_amostras_g1, carregar_builds_reais, carregar_resumo, configuracoes_simulacao
from hipotese.config import (
    ALFA, EFEITOS, EFEITO_EXEMPLO, MARGEM_ERRO_TIPO_I_PP,
    META_TAXA_FALHA, N_REPETICOES, SEMENTE,
    TESTE_BINOMIAL, TESTE_Z,
    URL_PROJECT, URL_REPOSITORIO,
)
from hipotese.exemplo import gerar_exemplo
from hipotese.erro_tipo_i import analisar_erro_tipo_i
from hipotese.graficos import (
    construir_g1, construir_g2, construir_g3, construir_g4, construir_poder_interativo, regiao_binomial,
)
from hipotese.testes import aplicar_testes

# Maior efeito do gráfico interativo do bônus (#278): 15 pontos percentuais.
EFEITO_MAXIMO_INTERATIVO = 0.15

# Seções na ordem exigida pelo roteiro, com a issue que preenche cada uma.
SECOES = [
    ("1. Cenário", "#264"),
    ("2. Os dados", "#267"),
    ("3. Como os testes funcionam", "#268"),
    ("4. Erro tipo I", "#273"),
    ("5. Poder", "#274"),
    ("6. Dados reais", "#275"),
    ("7. Conclusão", "#276"),
]

st.set_page_config(page_title="Lab04 — Testes de hipótese", layout="wide")

st.title("Testes de hipótese por dentro: Z para proporção × binomial exato")
url_dashboard = st.context.url or "http://127.0.0.1:8501/"
st.markdown(
    f"[Dashboard]({url_dashboard}) · [Repositório]({URL_REPOSITORIO}) · [GitHub Projects]({URL_PROJECT})"
)


def exibir_cenario():
    resumo = carregar_resumo()
    estatisticas = resumo["estatisticas"]
    configuracoes = configuracoes_simulacao(resumo)
    n = estatisticas["n_execucoes"]
    rho = configuracoes["Rajadas"]["correlacao"]
    periodo = resumo["periodo_amostra_utc"]

    st.markdown(
        f"**Pergunta:** a taxa de falha do workflow `{resumo['workflow']}` "
        f"de `{resumo['repositorio']}` supera a meta de 5%?"
    )
    st.markdown(
        f"**H₀: p = 0,05** · **H₁: p > 0,05** · unicaudal à direita · α = {_num(ALFA)}. "
        "p é a probabilidade de uma execução concluída (`success` ou `failure`) falhar; "
        "só um excesso sobre a meta responde à pergunta."
    )
    st.markdown(
        f"**Dados reais:** [GitHub Actions de {resumo['repositorio']}]"
        f"(https://github.com/{resumo['repositorio']}/actions/workflows/{resumo['workflow_id']}), "
        f"branch `{resumo['branch']}`, evento `{resumo['evento']}`, "
        f"{periodo['inicio'][:10]} a {periodo['fim'][:10]} (UTC). "
        f"{resumo['n_candidatas']} execuções consecutivas, {resumo['n_descartadas']} canceladas excluídas: "
        f"**{n} observações**, **{estatisticas['n_falhas']} falhas ({_pct(estatisticas['taxa_falha'])})**. "
        f"Critérios de coleta em [data/README.md]({URL_REPOSITORIO}/data/README.md)."
    )

    efeitos = ", ".join(f"{efeito * 100:g}" for efeito in EFEITOS)
    repeticoes = f"{N_REPETICOES:,}".replace(",", ".")
    st.markdown(
        f"**Simulação:** Bernoulli com taxa **0,05 + efeito**, efeitos de {efeitos} pontos percentuais, "
        f"{repeticoes} repetições por configuração, semente {SEMENTE}."
    )
    st.table([
        {
            "Situação": nome,
            "n (builds)": parametros["n"],
            "Correlação de lag 1": parametros["correlacao"],
            "Finalidade": finalidade,
        }
        for (nome, parametros), finalidade in zip(configuracoes.items(), [
            "Referência i.i.d., com o n da coleta.",
            "Dependência entre builds (cadeia de Markov calibrada pela ACF real).",
            "Amostra pequena: 1 falha esperada sob H₀.",
        ])
    ])
    st.caption(
        f"ρ = {rho:.4f}, estimado na sequência cronológica da coleta; incerto, com apenas nove "
        "transições a partir de falha."
    )

    st.markdown(
        f"**Expectativa registrada antes da simulação:** com n = {n} (n·p₀ = {n * META_TAXA_FALHA:.2f}), "
        "testes próximos, binomial conservador pela discretização e Z com mais poder e erro tipo I "
        "possivelmente acima de 5%. Com n = 20, Z distorcido. Nas rajadas, ambos acima de 5%."
    )


def exibir_dados():
    reais, simulados = carregar_amostras_g1()
    taxa_real = f"{reais.mean():.2%}".replace(".", ",")
    st.subheader("G1 · Dados reais ao lado dos simulados")
    st.plotly_chart(construir_g1(reais, simulados), width="stretch", key="g1_dados")
    st.markdown(
        f"Dados binários (1 = falha): **{int(reais.sum())} falhas em {reais.size} builds ({taxa_real})** na coleta "
        f"e **{int(simulados.sum())} ({_pct(simulados.mean())})** na amostra simulada. "
        "A massa concentra-se em sucessos, com assimetria à direita; falhas são o evento de interesse, "
        "não outliers. "
        f"A simulação usa Bernoulli com n = {reais.size} e p = {META_TAXA_FALHA:.0%} (H₀), semente {SEMENTE}; "
        "a taxa observada não substitui a meta. "
        "O histograma não mostra a dependência temporal, tratada na situação de rajadas."
    )


def exibir_exemplo():
    exemplo = gerar_exemplo()
    referencia = exemplo.resultados[0]
    st.subheader("Exemplo · Uma amostra simulada")
    st.markdown(
        f"Amostra independente de **{referencia.n} builds** com taxa verdadeira de "
        f"**{exemplo.taxa_verdadeira:.0%}** (5% + {EFEITO_EXEMPLO * 100:g} pontos percentuais), semente {SEMENTE}, "
        "fixada antes de observar o resultado. "
        f"Resultado: **{referencia.falhas} falhas em {referencia.n} builds** ({referencia.proporcao:.2%}), "
        f"efeito observado de {referencia.efeito_pp:+.2f} p.p."
    )
    st.latex(r"Z = \frac{\hat{p} - p_0}{\sqrt{p_0(1-p_0)/n}},\quad p_0=0{,}05")
    st.markdown(
        "**Z:** compara a proporção observada com 5% pela aproximação normal, com variância sob H₀ e "
        "sem correção de continuidade; p-valor = P(Z ≥ z). "
        "**Binomial exato:** compara a contagem de falhas com X ∼ Binomial(n; 0,05); "
        "p-valor = P(X ≥ x). Ambos pressupõem builds independentes."
    )
    st.table([
        {
            "Teste": resultado.teste,
            "Estatística": resultado.nome_estatistica,
            "Valor da estatística": resultado.estatistica,
            "p-valor": resultado.pvalor,
            "Efeito observado (p.p.)": resultado.efeito_pp,
            "Decisão (α = 0,05)": "Rejeitar H₀" if resultado.rejeita_h0 else "Não rejeitar H₀",
        }
        for resultado in exemplo.resultados
    ])
    for resultado in exemplo.resultados:
        if resultado.rejeita_h0:
            conclusao = "há evidência de que a taxa de falha ultrapassa 5%"
        else:
            conclusao = "não há evidência suficiente de que a taxa de falha ultrapassa 5%"
        comparacao = "<" if resultado.rejeita_h0 else "≥"
        st.markdown(
            f"**{resultado.teste}:** p-valor = {resultado.pvalor:.6g} {comparacao} "
            f"{ALFA:.2f}; {conclusao} nesta amostra."
        )
    if not any(resultado.rejeita_h0 for resultado in exemplo.resultados):
        st.markdown(
            f"Como a taxa gerada é {exemplo.taxa_verdadeira:.0%}, a não rejeição é um **erro tipo II** "
            "nos dois testes; sua frequência é medida na Q2."
        )
    st.caption(
        "O p-valor não é a probabilidade de H₀ ser verdadeira, e não rejeitar H₀ não prova p = 5%."
    )
    return exemplo


def exibir_g2(exemplo):
    normal, binomial = construir_g2(exemplo)
    referencia, exato = exemplo.resultados
    k, massas, rejeicao = regiao_binomial(exato.n)
    criticos = k[rejeicao]
    st.subheader("G2 · Distribuições sob H₀, rejeição e p-valor")
    st.plotly_chart(normal, width="stretch", key="g2_z")
    st.markdown(
        f"Sob H₀, Z segue aproximadamente N(0, 1). A região de rejeição (sombra escura) é "
        f"Z ≥ {_num(norm.isf(ALFA), 3)}, com área de {ALFA:.0%} na cauda direita, porque só valores altos "
        f"favorecem H₁. A sombra clara é o p-valor do exemplo, {_pct(referencia.pvalor)}: "
        "a probabilidade, sob H₀, de um Z pelo menos tão alto quanto o observado."
    )
    st.plotly_chart(binomial, width="stretch", key="g2_binomial")
    if criticos.size:
        regiao = (
            f"A região de rejeição do binomial é X ≥ {int(criticos[0])}, com massa de "
            f"{_pct(massas[rejeicao].sum())}, abaixo de {ALFA:.0%} pela discretização."
        )
    else:
        regiao = "Para este n, nenhuma contagem entra na região de rejeição do binomial."
    st.markdown(
        f"{regiao} O p-valor do exemplo é P(X ≥ {exato.falhas}) = {_pct(exato.pvalor)} sob H₀, "
        "incluindo as contagens fora do zoom."
    )


def _num(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def _pct(valor):
    return f"{_num(100 * valor)}%"


def exibir_q3(resultados, tipo_i):
    st.subheader("Q3 · Violação de pressupostos")
    repeticoes = f"{N_REPETICOES:_}".replace("_", ".")
    margem = _num(100 * q3.MARGEM_MONTE_CARLO)
    st.markdown(
        f"Q1 e Q2 repetidas com rajadas e com amostra pequena ({repeticoes} conjuntos por configuração), "
        "em comparação com a situação independente. Erro tipo I fora de 5% "
        f"± {margem} p.p. (margem de Monte Carlo) é classificado como liberal ou conservador."
    )

    st.markdown("**Erro tipo I (efeito zero)**")
    st.table([
        {
            "Situação": linha.situacao, "n (builds)": int(linha.n), "Teste": linha.teste,
            "Erro tipo I": _pct(linha.proporcao_rejeicao),
            "Desvio de 5% (p.p.)": f"{linha.desvio_pp:+.2f}".replace(".", ","),
            "Classificação": linha.classificacao,
        }
        for linha in tipo_i.itertuples()
    ])

    n_pequeno = int(tipo_i.loc[tipo_i["situacao"] == "Amostra pequena", "n"].iloc[0])
    k_z = q3.contagem_minima_rejeicao(TESTE_Z, n_pequeno)
    k_b = q3.contagem_minima_rejeicao(TESTE_BINOMIAL, n_pequeno)
    st.markdown(
        f"**Amostra pequena (n = {n_pequeno}):** sob H₀ espera-se {n_pequeno * META_TAXA_FALHA:.0f} falha, "
        "e a aproximação normal deixa de valer. "
        f"O Z rejeita com X ≥ {k_z} (erro tipo I exato de {_pct(q3.erro_tipo_i_exato(TESTE_Z, n_pequeno))}, "
        f"liberal); o binomial, com X ≥ {k_b} ({_pct(q3.erro_tipo_i_exato(TESTE_BINOMIAL, n_pequeno))}, "
        "conservador pela discretização)."
    )
    rho = float(resultados.loc[resultados["situacao"] == "Rajadas", "correlacao"].iloc[0])
    st.markdown(
        f"**Rajadas (ρ = {_num(rho)}):** a variância da contagem fica cerca de "
        f"{_num(q3.inflacao_variancia(rho))} vezes maior que a suposta pelos dois testes, que ficam liberais. "
        "O binomial é exato apenas sob independência."
    )

    st.markdown("**Poder nas situações de violação (proporção de rejeições)**")
    poderes = {situacao: q3.poder(resultados, situacao) for situacao in q3.VIOLACOES}
    for situacao, tabela in poderes.items():
        st.markdown(f"*{situacao}*")
        st.table([
            {
                "Efeito (p.p.)": f"{100 * linha['efeito']:.0f}", TESTE_Z: _pct(linha[TESTE_Z]),
                TESTE_BINOMIAL: _pct(linha[TESTE_BINOMIAL]),
                "Z − binomial (p.p.)": f"{linha['diferenca_pp']:+.2f}".replace(".", ","),
            }
            for linha in tabela.to_dict("records")
        ])
    pequena = poderes["Amostra pequena"]
    maior_vantagem = pequena["diferenca_pp"].max()
    poder_maximo = pequena[[TESTE_Z, TESTE_BINOMIAL]].max().max()
    efeito_maximo = 100 * pequena["efeito"].max()
    st.markdown(
        f"O Z tem mais poder nas duas violações, com vantagem de até {_num(maior_vantagem, 0)} p.p. na amostra "
        "pequena, mas opera com erro tipo I maior. "
        f"Com n = {n_pequeno}, o poder máximo até +{efeito_maximo:.0f} p.p. é {_pct(poder_maximo)}."
    )


@st.cache_data
def _curva_poder(n, alfa):
    efeitos = [round(0.005 * passo, 3) for passo in range(int(EFEITO_MAXIMO_INTERATIVO / 0.005) + 1)]
    return poder.curva_poder(n, efeitos, alfa)


def exibir_poder_interativo():
    st.subheader("Poder interativo")
    st.markdown(
        "Poder exato com builds independentes, calculado pela distribuição binomial a cada ajuste. "
        "Com n = 243, reproduz a situação independente do G4 dentro da margem de Monte Carlo."
    )
    colunas = st.columns(3)
    n = colunas[0].slider("Tamanho da amostra (builds)", 10, 1000, 243, step=1, key="bonus_n")
    efeito_pp = colunas[1].slider(
        "Efeito (p.p. acima de 5%)", 0.0, 100 * EFEITO_MAXIMO_INTERATIVO, 100 * EFEITO_EXEMPLO,
        step=0.5, key="bonus_efeito",
    )
    alfa = colunas[2].select_slider(
        "Nível de significância α", options=[0.01, 0.05, 0.10], value=ALFA,
        format_func=lambda valor: f"{100 * valor:g}%", key="bonus_alfa",
    )
    efeito = efeito_pp / 100

    st.plotly_chart(
        construir_poder_interativo(_curva_poder(n, alfa), n, efeito, alfa),
        width="stretch", key="bonus_poder",
    )
    metricas = st.columns(4)
    for coluna, teste in zip(metricas, poder.TESTES):
        coluna.metric(f"Poder · {teste}", _pct(poder.poder_exato(teste, n, efeito, alfa)))
    for coluna, teste in zip(metricas[2:], poder.TESTES):
        coluna.metric(f"Erro tipo I · {teste}", _pct(poder.poder_exato(teste, n, 0.0, alfa)))

    minimo_z, minimo_binomial = (poder.contagem_minima_rejeicao(teste, n, alfa) for teste in poder.TESTES)

    def limiar(minimo):
        return f"{minimo} falhas" if minimo <= n else "nenhuma contagem"

    if minimo_z == minimo_binomial:
        comparacao = (
            f"Com n = {n} e α = {100 * alfa:g}%, os dois testes rejeitam H₀ a partir de "
            f"**{limiar(minimo_z)}**: mesmo erro tipo I e mesmo poder."
        )
    else:
        comparacao = (
            f"Com n = {n} e α = {100 * alfa:g}%, o Z rejeita H₀ a partir de **{limiar(minimo_z)}** "
            f"e o binomial exato a partir de **{limiar(minimo_binomial)}**; o limiar menor dá mais poder "
            "e mais falsos positivos."
        )
    st.markdown(
        f"{comparacao} A diferença entre os testes depende da discretização e oscila com n. "
        "Com rajadas, as taxas reais de rejeição são maiores que as mostradas (G3)."
    )


def exibir_q1():
    resultados = analisar_erro_tipo_i()
    z, binomial = resultados

    def percentual(valor):
        return f"{100 * valor:.2f}%".replace(".", ",")

    inferior = ALFA - MARGEM_ERRO_TIPO_I_PP / 100
    superior = ALFA + MARGEM_ERRO_TIPO_I_PP / 100
    faixa = f"{percentual(inferior)} a {percentual(superior)}"
    margem = f"{MARGEM_ERRO_TIPO_I_PP:g}".replace(".", ",")
    repeticoes = f"{z.repeticoes:,}".replace(",", ".")
    posicao = {"Liberal": "acima da faixa", "Conservador": "abaixo da faixa", "Dentro da margem": "dentro da faixa"}
    st.subheader("Q1 · Falsos positivos com H₀ verdadeira")
    st.markdown(
        f"**{repeticoes} amostras independentes de {z.n} builds** com efeito zero (p = {META_TAXA_FALHA:.0%}). "
        f"Faixa de referência: **{ALFA:.0%} ± {margem} p.p.** ({faixa}). "
        f"**Resultado:** Z **{percentual(z.taxa_erro)}**, {posicao[z.classificacao]} "
        f"(**{z.classificacao.lower()}**); binomial exato **{percentual(binomial.taxa_erro)}**, "
        f"{posicao[binomial.classificacao]} (**{binomial.classificacao.lower()}**)."
    )
    st.table([
        {
            "Teste": resultado.teste,
            "Falsos positivos": resultado.rejeicoes,
            "Erro tipo I (%)": round(100 * resultado.taxa_erro, 2),
            "Desvio de 5% (p.p.)": round(resultado.desvio_pp, 2),
            "Classificação": resultado.classificacao,
        }
        for resultado in resultados
    ])
    st.markdown(
        f"Limiares de rejeição: Z com X ≥ **{z.primeira_contagem_rejeitada}**, binomial com "
        f"X ≥ **{binomial.primeira_contagem_rejeitada}**. Erro tipo I exato: **{percentual(z.taxa_teorica)}** "
        f"e **{percentual(binomial.taxa_teorica)}**. Os desvios vêm da aproximação normal e da "
        "discretização, não da variação de Monte Carlo."
    )
    st.caption(
        f"A faixa de ±{margem} p.p. é um critério de comparação, não um intervalo de confiança. "
        "Valores lidos de data/simulacao.csv."
    )


def exibir_g3(tipo_i):
    st.subheader("G3 · Comparação das situações")
    st.plotly_chart(construir_g3(tipo_i), width="stretch", key="g3_erro_tipo_i")

    perto = int((tipo_i["classificacao"] == q3.PROXIMO).sum())
    margem = _num(100 * q3.MARGEM_MONTE_CARLO)
    resumo = (
        f"{perto} de {len(tipo_i)} taxas ficaram em {ALFA:.0%} ± {margem} p.p." if perto
        else f"Nenhuma das {len(tipo_i)} taxas ficou em {ALFA:.0%} ± {margem} p.p."
    )
    dados = tipo_i.set_index(["situacao", "teste"])
    linhas = []
    for situacao in (q3.REFERENCIA, *q3.VIOLACOES):
        z = dados.loc[(situacao, TESTE_Z)]
        binomial = dados.loc[(situacao, TESTE_BINOMIAL)]
        linhas.append(
            f"- **{situacao}:** Z {_pct(z.proporcao_rejeicao)} ({z.classificacao}) · "
            f"binomial {_pct(binomial.proporcao_rejeicao)} ({binomial.classificacao})"
        )
    liberal_sempre = [
        teste for teste in (TESTE_Z, TESTE_BINOMIAL)
        if (tipo_i.loc[tipo_i["teste"] == teste, "classificacao"] == q3.LIBERAL).all()
    ]
    desvio = (
        f"O {liberal_sempre[0]} é liberal em todas as situações; "
        "o binomial só ultrapassa 5% quando há dependência entre builds."
        if liberal_sempre == [TESTE_Z] and dados.loc[("Rajadas", TESTE_BINOMIAL)].classificacao == q3.LIBERAL
        else ""
    )
    st.markdown("\n".join([f"{resumo} {desvio}".strip(), "", *linhas]))


def exibir_q2(simulacao):
    independente = simulacao.loc[simulacao["situacao"] == "Independente"]
    taxas = independente.pivot(index="efeito", columns="teste", values="proporcao_rejeicao")
    taxas = 100 * taxas.loc[sorted(EFEITOS), [TESTE_Z, TESTE_BINOMIAL]]
    amostra = independente.iloc[0]
    repeticoes = f"{amostra['repeticoes']:,}".replace(",", ".")

    st.subheader("Q2 · Poder dos testes na situação independente")
    st.markdown(
        f"Proporção de rejeições a α = {ALFA:.0%} em **{repeticoes} amostras de {amostra['n']} builds "
        "independentes por efeito** (aumento da taxa sobre 5%, em p.p.). Efeito zero mede o erro tipo I; "
        "os demais, o poder."
    )
    st.table([
        {
            "Efeito (p.p.)": round(100 * efeito, 2),
            "Medida": "Erro tipo I" if efeito == 0 else "Poder",
            f"{TESTE_Z} (%)": round(linha[TESTE_Z], 2),
            f"{TESTE_BINOMIAL} (%)": round(linha[TESTE_BINOMIAL], 2),
        }
        for efeito, linha in taxas.iterrows()
    ])
    z, binomial = taxas.loc[EFEITO_EXEMPLO]
    efeito_pp = f"{100 * EFEITO_EXEMPLO:g}"
    comparacao = f"Z {z:.2f}% e binomial {binomial:.2f}%".replace(".", ",")
    acima_99 = taxas[(taxas[TESTE_Z] >= 99) & (taxas[TESTE_BINOMIAL] >= 99)].index
    saturacao = (
        f" Ambos passam de 99% a partir de +{100 * acima_99.min():g} p.p." if len(acima_99) else ""
    )
    st.markdown(
        f"Em +{efeito_pp} p.p.: **{comparacao}**.{saturacao} "
        "A vantagem do Z acompanha seu erro tipo I maior (Q1)."
    )


def exibir_g4(simulacao):
    st.plotly_chart(construir_g4(simulacao), width="stretch", key="g4_poder")
    curva = simulacao.pivot_table(index=["situacao", "efeito"], columns="teste", values="proporcao_rejeicao")
    diferenca = 100 * (curva[TESTE_Z] - curva[TESTE_BINOMIAL])
    situacao_max, efeito_max = diferenca.idxmax()
    pequena = curva.loc["Amostra pequena"]
    st.markdown(
        "Efeito zero mostra o erro tipo I; os demais pontos, o poder. "
        f"O **Z rejeita mais em todos os efeitos e situações**, com a maior vantagem em {situacao_max.lower()} "
        f"(+{_num(diferenca.max())} p.p. em +{100 * efeito_max:g} p.p.). "
        f"Com n = 20, o poder não passa de {_pct(pequena.max().max())} até +{100 * pequena.index.max():g} p.p. "
        "A vantagem do Z não é líquida: ele também rejeita mais sob H₀ (G3)."
    )


def exibir_testes_reais():
    resultados = aplicar_testes(carregar_builds_reais())
    observado = resultados[0]
    meta = _pct(META_TAXA_FALHA)
    st.markdown(
        f"Amostra real: **{observado.falhas} falhas em {observado.n} builds ({_pct(observado.proporcao)})**. "
        f"H₁: p > {meta}; α = {_num(ALFA)}."
    )
    st.table([
        {
            "Teste": resultado.teste,
            "Estatística": resultado.nome_estatistica,
            "Valor da estatística": resultado.estatistica,
            "p-valor": resultado.pvalor,
            "Efeito (p.p.)": round(resultado.efeito_pp, 2),
            "Conclusão": "Rejeitar H₀" if resultado.rejeita_h0 else "Não rejeitar H₀",
        }
        for resultado in resultados
    ])

    rejeitaram = [resultado.teste for resultado in resultados if resultado.rejeita_h0]
    if len(rejeitaram) == len(resultados):
        conclusao = f"Os dois testes encontraram evidência de que a taxa de falha supera {meta}."
    elif rejeitaram:
        conclusao = f"Apenas o teste {rejeitaram[0]} encontrou evidência de que a taxa de falha supera {meta}."
    else:
        conclusao = (
            f"Nenhum dos testes encontrou evidência de que a taxa de falha supera {meta}. "
            "Não rejeitar H₀ não comprova que a meta seja cumprida."
        )
    st.markdown(conclusao)

    efeito = observado.efeito_pp
    efeito_assinado = f"{efeito:+.2f}".replace(".", ",").replace("-", "−") if efeito else "0,00"
    if efeito:
        direcao = "a mais" if efeito > 0 else "a menos"
        unidade = "falha" if abs(efeito) <= 1 else "falhas"
        impacto = f"São cerca de **{_num(abs(efeito))} {unidade} {direcao} por 100 builds** em relação à meta."
    else:
        impacto = "Na amostra, a taxa observada coincide com a meta."
    st.markdown(
        f"**Tamanho do efeito:** **{efeito_assinado} p.p.** em relação à meta. {impacto} "
        "A relevância prática depende do volume de execuções e do custo de uma falha."
    )
    st.caption(
        "Ambos os testes pressupõem independência; o agrupamento de falhas na coleta limita a "
        "interpretação dos p-valores."
    )


def exibir_conclusao(tipo_i):
    dados = tipo_i.set_index(["situacao", "teste"])["proporcao_rejeicao"]
    st.table([
        {
            "Situação": situacao,
            "Esperado": esperado,
            "Encontrado (erro tipo I)": (
                f"Z {_pct(dados.loc[(situacao, TESTE_Z)])} · binomial {_pct(dados.loc[(situacao, TESTE_BINOMIAL)])}"
            ),
            "Confirmou?": confirmou,
        }
        for situacao, esperado, confirmou in (
            (q3.REFERENCIA, "Testes próximos; binomial ≤ 5%", "Parcialmente: Z liberal mesmo com n = 243"),
            ("Amostra pequena", "Z distorcido; binomial ≤ 5%", "Sim"),
            ("Rajadas", "Ambos acima de 5%", "Sim"),
        )
    ])
    st.markdown(
        "**Recomendação:** **binomial exato**. Controla o erro tipo I sob independência, ao custo de "
        "algum poder. "
        "A escolha muda para o Z quando n for grande o bastante para os limiares coincidirem (poder "
        "interativo), ou quando deixar passar um aumento custar mais que um falso alarme. "
        "Com falhas em rajadas, nenhum dos dois serve: use um método que leve em conta a dependência."
    )
    st.markdown(
        "**Limitação:** um único workflow com 10 falhas, insuficiente para estimar a dependência entre "
        "builds com precisão e para generalizar a outros projetos ou períodos."
    )


simulacao = q3.carregar_resultados()
tipo_i = q3.erro_tipo_i(simulacao)
for titulo, issue in SECOES:
    st.header(titulo)
    if issue == "#264":
        exibir_cenario()
    elif issue == "#267":
        exibir_dados()
    elif issue == "#268":
        exemplo = exibir_exemplo()
        exibir_g2(exemplo)
    elif issue == "#273":
        exibir_q1()
        exibir_g3(tipo_i)
    elif issue == "#274":
        exibir_q2(simulacao)
        exibir_g4(simulacao)
        exibir_q3(simulacao, tipo_i)
        exibir_poder_interativo()
    elif issue == "#275":
        exibir_testes_reais()
    elif issue == "#276":
        exibir_conclusao(tipo_i)
