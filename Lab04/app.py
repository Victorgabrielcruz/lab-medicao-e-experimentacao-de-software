"""Dashboard do Lab04 — testes de hipótese por dentro (par P4).

Execução, a partir da pasta Lab04: ``streamlit run app.py``
"""

import streamlit as st

from hipotese import q3
from hipotese.cenario import carregar_amostras_g1, carregar_resumo, configuracoes_simulacao
from hipotese.config import (
    ALFA, ALTERNATIVA, EFEITOS, EFEITO_EXEMPLO, MARGEM_ERRO_TIPO_I_PP,
    META_TAXA_FALHA, N_REPETICOES, SEMENTE,
    TESTE_BINOMIAL, TESTE_Z,
    URL_DASHBOARD, URL_PROJECT, URL_REPOSITORIO,
)
from hipotese.exemplo import gerar_exemplo
from hipotese.erro_tipo_i import analisar_erro_tipo_i
from hipotese.graficos import construir_g1, construir_g2, construir_g3, construir_g4, regiao_binomial

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
link_dashboard = f"[Dashboard publicado]({URL_DASHBOARD})" if URL_DASHBOARD else "Dashboard publicado: em breve (#277)"
st.markdown(
    f"[Repositório]({URL_REPOSITORIO}) · [GitHub Projects]({URL_PROJECT}) · {link_dashboard}"
)

def exibir_cenario():
    resumo = carregar_resumo()
    estatisticas = resumo["estatisticas"]
    configuracoes = configuracoes_simulacao(resumo)
    n = estatisticas["n_execucoes"]
    rho = configuracoes["Rajadas"]["correlacao"]
    periodo = resumo["periodo_amostra_utc"]

    st.markdown(
        f"**Pergunta:** A taxa de falha das builds do workflow `{resumo['workflow']}` "
        f"do projeto `{resumo['repositorio']}` está acima da meta de 5%?"
    )
    st.markdown(
        "**H₀: p = 0,05.** A probabilidade de falha está na meta. "
        "**H₁: p > 0,05.** A probabilidade de falha ultrapassa a meta. "
        "Aqui, p é a probabilidade de uma execução terminar em falha, entre as "
        "execuções com conclusão `success` ou `failure`. Escolhemos um teste "
        "**unicaudal à direita**, pois 5% é um teto didático e a pergunta "
        "investiga seu excesso; uma redução da taxa não responde à alternativa. "
        "A decisão é rejeitar H₀ quando o p-valor for menor que 0,05."
    )
    st.caption(
        f"Alternativa compartilhada com os testes: {ALTERNATIVA!r}. "
        "A meta é uma referência da atividade, não um compromisso do projeto observado."
    )
    st.markdown(
        f"**Origem dos dados:** [GitHub Actions de {resumo['repositorio']}]"
        f"(https://github.com/{resumo['repositorio']}/actions/workflows/{resumo['workflow_id']}), "
        f"workflow `{resumo['workflow']}`, branch `{resumo['branch']}`, evento "
        f"`{resumo['evento']}`, de {periodo['inicio'][:10]} a {periodo['fim'][:10]} (UTC). "
        f"Das {resumo['n_candidatas']} execuções consecutivas inspecionadas, "
        f"{resumo['n_descartadas']} canceladas foram descartadas, restando **{n} observações**, "
        f"com **{estatisticas['n_falhas']} falhas "
        f"({estatisticas['taxa_falha'] * 100:.2f}%)**. "
        "Cada observação vale 1 para falha e 0 para sucesso. A seleção, os descartes "
        "e o tratamento das reexecuções estão documentados em "
        f"[data/README.md]({URL_REPOSITORIO}/data/README.md)."
    )

    st.markdown("**Plano de simulação, fixado antes da S02**")
    efeitos = "; ".join(f"{efeito * 100:g}" for efeito in EFEITOS)
    taxas = "; ".join(f"{(META_TAXA_FALHA + efeito) * 100:g}%" for efeito in EFEITOS)
    st.markdown(
        f"Cada build tem distribuição marginal Bernoulli com taxa **0,05 + efeito**. "
        f"Os efeitos são **{efeitos} pontos percentuais** acima da meta "
        f"(taxas verdadeiras: {taxas}). O efeito zero representa H₀ verdadeira; "
        "a taxa observada de 4,12% não substitui a meta sob H₀. "
        f"Serão {N_REPETICOES:,} repetições por situação e efeito, com "
        f"semente {SEMENTE} e α = {ALFA:.2f}."
    )
    st.table([
        {
            "Situação": nome,
            "n (builds)": parametros["n"],
            "Correlação de lag 1": parametros["correlacao"],
            "Justificativa": justificativa,
        }
        for (nome, parametros), justificativa in zip(configuracoes.items(), [
            "Referência i.i.d.; tamanho igual ao da amostra real.",
            "Cadeia de Markov estacionária; persistência calibrada pela ACF real.",
            "Builds independentes, mas apenas 1 falha esperada sob H₀; desafia a aproximação normal.",
        ])
    ])
    st.markdown(
        f"Nas rajadas, usamos **ρ = {rho:.4f}**, estimado na sequência cronológica "
        "das observações válidas. A cadeia preserva a taxa marginal e altera a "
        "dependência entre builds. A estimativa tem incerteza: há somente nove "
        "transições iniciadas por falha, e cancelamentos podem separar linhas "
        "consecutivas do CSV. Já n = 20 é uma escolha deliberada para avaliar "
        "amostra pequena, não o tamanho da coleta."
    )

    st.markdown("**Expectativa registrada antes de executar as simulações da S02**")
    st.markdown(
        f"No caso independente com n = {n}, esperamos resultados próximos entre os "
        f"testes: sob H₀, n·p₀ = {n * META_TAXA_FALHA:.2f} e "
        f"n·(1−p₀) = {n * (1 - META_TAXA_FALHA):.2f}, o que favorece a aproximação "
        "normal do Z. O binomial exato deve controlar o erro tipo I em até 5% "
        "sob independência, podendo ser conservador pela natureza discreta; "
        "o Z pode apresentar maior poder em alguns efeitos, acompanhado de "
        "eventual erro tipo I acima do nominal. Com n = 20, esperamos maior "
        "desvio da aproximação Z e preferimos o binomial exato pelo controle "
        "do erro tipo I, sem presumir que terá mais poder. Nas rajadas, a "
        "dependência viola os pressupostos de ambos: mesmo o teste exato não "
        "garante controle de 5%, e esperamos mais falsos positivos. A recomendação "
        "final dependerá de Q1, Q2 e Q3; estas são expectativas, não resultados."
    )


def exibir_dados():
    reais, simulados = carregar_amostras_g1()
    taxa_real = f"{reais.mean():.2%}".replace(".", ",")
    st.subheader("G1 · Dados reais ao lado dos simulados")
    st.markdown(
        f"Os dados reais são binários: **{int(reais.sum())} falhas em {reais.size} builds "
        f"({taxa_real})**. "
        "Há concentração em 0 (passou), com assimetria à direita; 1 (falhou) "
        "é uma categoria válida, e as falhas não são outliers. "
        f"Para preservar esse formato, simulamos uma Bernoulli independente com "
        f"**n = {reais.size}**, igual à coleta, **p = {META_TAXA_FALHA:.0%}**, definido "
        f"por H₀, e **semente {SEMENTE}**; os {taxa_real} observados não substituem a meta. "
        "Os histogramas mostram frequências percentuais em escalas idênticas, "
        "mas não a dependência temporal, estudada na situação de rajadas."
    )
    st.plotly_chart(construir_g1(reais, simulados), width="stretch", key="g1_dados")


def exibir_exemplo():
    exemplo = gerar_exemplo()
    referencia = exemplo.resultados[0]
    st.subheader("Aplicação a um conjunto simulado (#266)")
    st.markdown(
        f"Uma única amostra **independente de {referencia.n} builds**, com taxa "
        f"verdadeira de **{exemplo.taxa_verdadeira:.0%}** (meta de 5% + "
        f"{EFEITO_EXEMPLO * 100:g} pontos percentuais) e semente **{SEMENTE}**. "
        "Esses parâmetros foram escolhidos antes de observar o resultado, sem "
        "trocar a semente ou selecionar amostras pela significância. Os dois "
        "testes recebem exatamente as mesmas builds."
    )
    st.markdown(
        f"A amostra gerada teve **{referencia.falhas} falhas em {referencia.n} builds** "
        f"(taxa observada: **{referencia.proporcao:.2%}**). O efeito observado é "
        f"**{referencia.efeito_pp:+.2f} pontos percentuais** em relação à meta; "
        "ele pode diferir dos 4 pontos percentuais usados na geração por variação amostral."
    )
    st.latex(r"Z = \frac{\hat{p} - p_0}{\sqrt{p_0(1-p_0)/n}},\quad p_0=0{,}05")
    st.markdown(
        "O Z usa variância sob H₀ e aproximação normal, sem correção de continuidade. "
        "Para a alternativa à direita, seu p-valor é P(Z ≥ z observado). "
        "O binomial exato usa X ∼ Binomial(n, 0,05) e p-valor P(X ≥ falhas observadas); "
        "sua estatística na tabela é a proporção observada p̂, conforme o SciPy. "
        "Ambos pressupõem builds independentes com probabilidade constante."
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
            "Como sabemos que a taxa usada na geração é 9%, existe um efeito real "
            "na simulação. Não detectá-lo nesta amostra é uma ocorrência de "
            "**erro tipo II** para cada teste; um único exemplo não estima sua frequência."
        )
    st.caption(
        "Não rejeitar H₀ não prova que a taxa seja 5%. O p-valor não é a probabilidade "
        "de H₀ ser verdadeira. Este exemplo simulado não permite concluir sobre o "
        "workflow real nem comparar o poder dos testes; isso cabe às etapas seguintes."
    )
    return exemplo


def exibir_g2(exemplo):
    normal, binomial = construir_g2(exemplo)
    referencia, exato = exemplo.resultados
    k, massas, rejeicao = regiao_binomial(exato.n)
    criticos = k[rejeicao]
    st.subheader("G2 · Distribuições sob H₀, rejeição e p-valor (#268)")
    st.markdown(
        "Os dois testes comparam a proporção de falhas à meta de 5%: o Z usa uma "
        "referência normal aproximada, e o binomial exato usa a distribuição "
        "discreta de p̂ = X/n. A sombra mais escura indica a região de rejeição "
        "na cauda direita, e a mais clara destaca a cauda a partir do resultado "
        "observado no mesmo exemplo da #266. O p-valor mede a probabilidade, "
        "sob H₀ e seus pressupostos, de obter um resultado pelo menos tão "
        "extremo nessa direção; não é a probabilidade de H₀ ser verdadeira. "
        "As duas regiões podem se sobrepor: quando o resultado observado fica "
        "antes do limite crítico, a região de rejeição está contida na cauda do p-valor."
    )
    st.plotly_chart(normal, width="stretch", key="g2_z")
    st.caption(
        "A curva N(0, 1) é a aproximação usada pelo teste Z, não a distribuição "
        "discreta exata da estatística em amostras finitas. A área após o limite "
        "crítico é 5%; a área após o Z observado é o p-valor. As linhas pontilhada "
        "e tracejada marcam o observado e o limite crítico, respectivamente."
    )
    st.plotly_chart(binomial, width="stretch", key="g2_binomial")
    if criticos.size:
        limite = int(criticos[0])
        st.caption(
            f"No binomial, rejeitamos a partir de {limite} falhas "
            f"(p̂ ≥ {limite / exato.n:.2%}). A soma das massas nessa região é "
            f"{massas[rejeicao].sum():.5f}, que pode ser menor que 0,05 pela "
            "discretização. O p-valor soma as massas das barras a partir das "
            f"{exato.falhas} falhas do exemplo, incluindo essa observação. "
            "O eixo mostra um zoom da região relevante; as somas incluem todo o suporte."
        )
    else:
        st.caption("Com este tamanho de amostra, nenhuma contagem tem p-valor < 0,05; a região de rejeição exata é vazia.")
    st.markdown(
        f"Neste exemplo, as caudas destacadas correspondem a p = {referencia.pvalor:.5f} "
        f"no Z e p = {exato.pvalor:.5f} no binomial. A decisão de cada teste "
        "está na tabela acima; as regiões usam a mesma regra p-valor < 0,05."
    )


def _num(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def _pct(valor):
    return f"{_num(100 * valor)}%"


def exibir_q3(resultados, tipo_i):
    st.subheader("Q3 · Quando os dados não se comportam bem (#272)")
    repeticoes = f"{N_REPETICOES:_}".replace("_", ".")
    margem = _num(100 * q3.MARGEM_MONTE_CARLO)
    st.markdown(
        f"Repetimos Q1 e Q2 em duas situações que violam pressupostos, com {repeticoes} conjuntos "
        "por configuração, e comparamos com a situação independente (n = 243). Um erro tipo I é "
        "considerado liberal ou conservador quando se afasta de 5% mais que a margem de Monte Carlo "
        f"(±{margem} p.p.)."
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
        f"**Amostra pequena afeta mais o Z.** Com n = {n_pequeno}, a meta implica só "
        f"{n_pequeno * META_TAXA_FALHA:.0f} falha esperada, e a distribuição do número de falhas é muito "
        f"assimétrica; a aproximação normal em que o Z se apoia deixa de valer. O Z rejeita a partir de "
        f"{k_z} falhas, o que sob H₀ acontece com probabilidade exata de "
        f"{_pct(q3.erro_tipo_i_exato(TESTE_Z, n_pequeno))}: ele fica liberal. O binomial calcula a cauda "
        f"exata e só rejeita a partir de {k_b} falhas ({_pct(q3.erro_tipo_i_exato(TESTE_BINOMIAL, n_pequeno))} "
        "sob H₀); nunca passa de 5%, mas fica conservador porque a contagem é discreta."
    )
    rho = float(resultados.loc[resultados["situacao"] == "Rajadas", "correlacao"].iloc[0])
    st.markdown(
        f"**Rajadas afetam os dois.** A independência entre builds é pressuposto de ambos os testes. "
        f"Com correlação de lag 1 de {_num(rho)}, a variância do número de falhas fica cerca de "
        f"{_num(q3.inflacao_variancia(rho))} vezes maior do que os testes supõem, e os dois passam a "
        "rejeitar H₀ verdadeira com mais frequência. Ser exato não protege o binomial aqui: a exatidão "
        "vale só para builds independentes. O Z continua o mais liberal porque já partia acima de 5%."
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
        "Nas duas situações o Z rejeita mais que o binomial em todos os efeitos, com a maior vantagem na "
        f"amostra pequena (até {_num(maior_vantagem, 0)} p.p.). Essa vantagem não é poder real: vem junto de "
        "um erro tipo I acima de 5%, então parte das rejeições aconteceria mesmo sem efeito. Com "
        f"n = {n_pequeno}, o maior poder até +{efeito_maximo:.0f} p.p. é {_pct(poder_maximo)}, e nas rajadas "
        "o poder com efeitos pequenos fica inflado pelos falsos positivos."
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
        f"Foram simuladas **{repeticoes} amostras independentes de {z.n} builds**, "
        f"com H₀ verdadeira (p = {META_TAXA_FALHA:.0%}), efeito zero e semente {SEMENTE}. "
        f"Cada rejeição com p-valor < {ALFA:.2f} é um **erro tipo I**: o teste "
        "encontra um aumento da taxa de falha quando ele não existe. "
        f"A referência é **{ALFA:.0%} ± {margem} p.p.**, "
        f"ou **{faixa}**, incluindo os limites. "
        f"O Z teve **{percentual(z.taxa_erro)}**, {posicao[z.classificacao]} "
        f"(**{z.classificacao.lower()}**), e o binomial exato "
        f"**{percentual(binomial.taxa_erro)}**, {posicao[binomial.classificacao]} "
        f"(**{binomial.classificacao.lower()}**)."
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
        f"No Z, a rejeição começa em **{z.primeira_contagem_rejeitada} falhas**; "
        f"no binomial, em **{binomial.primeira_contagem_rejeitada}**. "
        "Somando as probabilidades dessas contagens sob H₀, os erros tipo I "
        f"teóricos são **{percentual(z.taxa_teorica)}** e "
        f"**{percentual(binomial.taxa_teorica)}**, respectivamente: a aproximação "
        "normal e os limiares discretos ajudam a explicar os desvios observados "
        "mesmo com builds independentes."
    )
    st.caption(
        "A margem de ±0,4 p.p. é a faixa de comparação definida para Q1, "
        "não um intervalo de confiança da taxa real de falhas. "
        "Resultados lidos da simulação congelada, sem novos sorteios ao abrir a página."
    )


def exibir_g3(tipo_i):
    st.subheader("G3 · Comparação das situações")
    st.plotly_chart(construir_g3(tipo_i), width="stretch", key="g3_erro_tipo_i")

    perto = int((tipo_i["classificacao"] == q3.PROXIMO).sum())
    margem = _num(100 * q3.MARGEM_MONTE_CARLO)
    resumo = (
        f"{perto} de {len(tipo_i)} taxas ficaram perto de **{ALFA:.0%}**" if perto
        else f"Nenhuma das taxas ficou perto de **{ALFA:.0%}**"
    )
    frases = [f"{resumo} pela margem de ±{margem} p.p. usada na Q3."]
    dados = tipo_i.set_index(["situacao", "teste"])
    for situacao in (q3.REFERENCIA, *q3.VIOLACOES):
        z = dados.loc[(situacao, TESTE_Z)]
        binomial = dados.loc[(situacao, TESTE_BINOMIAL)]
        frases.append(
            f"**{situacao}**: o Z ficou {z.classificacao} ({_pct(z.proporcao_rejeicao)}) "
            f"e o binomial exato ficou {binomial.classificacao} ({_pct(binomial.proporcao_rejeicao)})."
        )
    st.markdown(" ".join(frases))


def exibir_q2(simulacao):
    independente = simulacao.loc[simulacao["situacao"] == "Independente"]
    taxas = independente.pivot(index="efeito", columns="teste", values="proporcao_rejeicao")
    taxas = 100 * taxas.loc[sorted(EFEITOS), [TESTE_Z, TESTE_BINOMIAL]]
    amostra = independente.iloc[0]
    repeticoes = f"{amostra['repeticoes']:,}".replace(",", ".")

    st.subheader("Q2 · Poder dos testes na situação independente")
    st.markdown(
        f"A tabela mostra a porcentagem de amostras que rejeitaram H₀ a {ALFA:.0%} "
        f"em **{repeticoes} repetições de {amostra['n']} builds independentes por efeito**. "
        "O efeito é o aumento da taxa verdadeira de falhas acima da meta de 5%, em pontos "
        "percentuais. A linha de efeito zero mede o **erro tipo I**. As demais estimam "
        "o **poder**, a frequência com que cada teste detecta um aumento real."
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
    comparacao = f"{z:.2f}% no Z e {binomial:.2f}% no binomial exato".replace(".", ",")
    st.markdown(
        f"Com efeito de **+{efeito_pp} p.p.**, o poder foi de **{comparacao}**. "
        "À medida que o efeito aumenta, os dois testes passam a detectá-lo com mais "
        "frequência e chegam perto de 100%. Na comparação a 5% nominal, vale considerar "
        "também o erro tipo I de cada teste na linha de efeito zero e na análise de Q1."
    )


def exibir_g4(simulacao):
    st.plotly_chart(construir_g4(simulacao), width="stretch", key="g4_poder")
    st.caption("Em 0 p.p., os pontos representam erro tipo I. A partir de 2 p.p., representam poder estimado.")
    st.markdown(
        "O **Z detectou mais aumentos** que o binomial exato em todos os efeitos positivos "
        "simulados. A vantagem não se inverteu entre as três situações. Com efeito de +4 p.p., "
        "a diferença foi de 6,67 p.p. em amostras independentes, 6,07 p.p. em rajadas e "
        "16,70 p.p. na amostra pequena. Nas duas situações com 243 builds, as curvas "
        "quase coincidem perto de 100% em +10 p.p. Na amostra pequena, a diferença "
        "chega a 24,27 p.p. nesse efeito. Em efeito zero, o Z também apresentou mais "
        "falsos positivos nas três situações, o que ajuda a contextualizar a diferença de poder."
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
    else:
        st.info(f"Conteúdo em construção ({issue}).")
