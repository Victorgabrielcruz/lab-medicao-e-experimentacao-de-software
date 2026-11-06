"""Dashboard do Lab04 — testes de hipótese por dentro (par P4).

Execução, a partir da pasta Lab04: ``streamlit run app.py``
"""

import streamlit as st

from hipotese.cenario import carregar_resumo, configuracoes_simulacao
from hipotese.config import (
    ALFA, ALTERNATIVA, EFEITOS, META_TAXA_FALHA, N_REPETICOES, SEMENTE,
    URL_DASHBOARD, URL_PROJECT, URL_REPOSITORIO,
)

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


for titulo, issue in SECOES:
    st.header(titulo)
    if issue == "#264":
        exibir_cenario()
    else:
        st.info(f"Conteúdo em construção ({issue}).")
