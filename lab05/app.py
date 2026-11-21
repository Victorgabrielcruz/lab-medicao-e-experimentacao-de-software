"""Esqueleto do documento final do Lab05 em Streamlit (#305).

Na raiz do repositório: ``python -m streamlit run lab05/app.py``.
Abrir o dashboard apenas lê os artefatos do piloto; não executa o benchmark.
"""

import csv
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from experimento import config
from resumir_piloto import resumir

RAIZ = Path(__file__).resolve().parent
DIR_PILOTO = config.DIR_DADOS / "piloto"
PLANO = RAIZ / "docs" / "05-plano-analise.md"


def exibir_software():
    st.header("1. Software")
    st.markdown(
        "O **SQLite** é um banco relacional embarcado e sem servidor. O estudo avalia "
        "o motor em execução pelo módulo `sqlite3` do Python, com dados sintéticos locais. "
        "As evidências de software real, em operação e de alto impacto estão em "
        "`lab05/docs/01-software-criterios.md`. "
        "[Usuários conhecidos do SQLite](https://www.sqlite.org/famous.html)."
    )


def exibir_pergunta():
    st.header("2. Pergunta de pesquisa")
    st.markdown(
        "**A recomendação de configurar o SQLite com WAL + synchronous=NORMAL se sustenta? "
        "Quanto desempenho o padrão DELETE + FULL deixa na mesa, e quanto desse ganho "
        "exige abrir mão da durabilidade?**"
    )
    st.markdown(
        "O GQM relaciona tempo total (**M1**), vazão (**M2**) e razão entre medianas de "
        "vazão (**M3**) às comparações: **H1** WAL-FULL × DELETE-FULL; **H2** WAL-NORMAL × "
        "WAL-FULL; **H3** DELETE-NORMAL × DELETE-FULL. Todas serão avaliadas nas três cargas. "
        "O desempenho é medido; as garantias de durabilidade são discutidas a partir da "
        "documentação, sem simular quedas de energia."
    )


def exibir_metodo():
    st.header("3. Método")
    st.markdown(
        f"Experimento controlado **fatorial 2 × 2**, com `journal_mode` (DELETE/WAL) e "
        f"`synchronous` (FULL/NORMAL). A coleta completa prevê **{config.N_REPETICOES} "
        f"repetições medidas e {config.N_AQUECIMENTO} aquecimentos descartados** por "
        f"combinação: 360 medições e {config.total_execucoes()} execuções no total; "
        f"semente **{config.SEMENTE}**."
    )
    st.table([
        {"Carga": carga.nome, "Operações": carga.n_operacoes,
         "Leituras": round(carga.n_operacoes * carga.fracao_leitura),
         "Escritas / commits": carga.n_operacoes - round(carga.n_operacoes * carga.fracao_leitura)}
        for carga in config.CARGAS
    ])
    st.markdown(
        f"Cada execução usa um banco novo com {config.LINHAS_INICIAIS:,} linhas iniciais "
        f"e payload de {config.TAMANHO_PAYLOAD} bytes. Há uma conexão por vez. "
        "`perf_counter` mede operações e commits; preparação e fechamento ficam fora. "
        "Checkpoints automáticos durante as operações entram no tempo. A ordem das "
        "12 combinações é embaralhada em cada rodada, que compartilha a sequência de "
        "operações entre configurações: a análise preservará o pareamento por rodada."
    )
    st.subheader("Plano de análise")
    st.markdown(
        "**Descritiva:** n, média, mediana, desvio-padrão amostral, quartis, IQR, mínimo, "
        "máximo e CV de M1/M2, por tratamento e carga. As métricas têm escala de razão; "
        "mediana e IQR são os resumos principais. O piloto tem três pontos por grupo, "
        "insuficientes para assumir normalidade ou simetria."
    )
    st.markdown(
        "**Teste planejado:** sinais pareados, binomial exato bilateral, aplicado a M2 "
        f"nas nove comparações H1–H3 × cargas; correção de Holm com α = {config.ALFA:.2f}. "
        "M1 é a transformação inversa de M2 para uma carga fixa e não gera outra família "
        "de testes. M3 é um tamanho do efeito, sem teste isolado. "
        "Serão auditadas a integridade dos pares e a dependência entre rodadas."
    )
    st.markdown(
        "**Magnitude e incerteza:** diferença em segundos e operações/s, probabilidade "
        "pareada de ganho, M3 e ganho percentual; IC de 95% por bootstrap de rodadas "
        "(10.000 reamostragens, semente 42). Interação será exploratória por gráfico e "
        "razão de razões, conforme o GQM. A faixa de ±2% na leitura é uma referência "
        "prática, sem declaração de equivalência."
    )
    st.download_button(
        "Baixar plano de análise", PLANO.read_text(encoding="utf-8"),
        file_name=PLANO.name, mime="text/markdown",
    )
    st.caption(
        "Sete categorias de pesquisa: versão inicial em lab05/docs/03-categorias-pesquisa.md; "
        "revisão e justificativas finais previstas para a Sprint 03."
    )


def exibir_resultados():
    st.header("4. Resultados")
    try:
        # Reaproveita a validação e a descritiva da #304, calculadas do CSV bruto.
        resumo = resumir(DIR_PILOTO)
        dados = pd.read_csv(DIR_PILOTO / "resultados.csv")
        ambiente = dados.iloc[0]
    except (OSError, ValueError, KeyError, StopIteration, csv.Error) as erro:
        st.error(f"Não foi possível ler o piloto em data/piloto: {erro}")
        st.info("Restaure resultados.csv, ambiente.json e execucao.json do piloto versionado.")
        return

    st.warning(
        "Piloto exploratório: apenas 3 repetições medidas e 1 aquecimento descartado por "
        "combinação. Estes dados não respondem às hipóteses; a coleta completa será "
        "analisada separadamente. Não são apresentados testes de hipótese nem IC do piloto."
    )
    st.caption("Fonte: lab05/data/piloto/resultados.csv · resumo recalculado ao abrir o dashboard.")
    st.metric("Medições do piloto", resumo["medicoes"])
    st.markdown(
        f"**Ambiente da coleta:** {ambiente['sistema']}, Python {ambiente['python_version']}, "
        f"SQLite {ambiente['sqlite_version']}; início em {ambiente['data_hora_utc']}. "
        "Estas versões pertencem à coleta, independentemente da máquina que exibe o dashboard."
    )
    tabela = pd.DataFrame(resumo["grupos"]).rename(columns={
        "configuracao": "Configuração", "carga": "Carga",
        "tempo_mediana_s": "Mediana M1 (s)", "tempo_media_s": "Média M1 (s)",
        "tempo_desvio_padrao_s": "DP M1 (s)", "tempo_q1_s": "Q1 M1 (s)",
        "tempo_q3_s": "Q3 M1 (s)", "tempo_iqr_s": "IQR M1 (s)",
        "tempo_min_s": "Mínimo M1 (s)", "tempo_max_s": "Máximo M1 (s)",
        "tempo_cv_pct": "CV M1 (%)", "vazao_mediana_ops_s": "Mediana M2 (ops/s)",
    })
    st.dataframe(tabela[[
        "Configuração", "Carga", "n", "Mediana M1 (s)", "IQR M1 (s)", "Média M1 (s)",
        "DP M1 (s)", "Q1 M1 (s)", "Q3 M1 (s)", "Mínimo M1 (s)", "Máximo M1 (s)",
        "CV M1 (%)", "Mediana M2 (ops/s)",
    ]], hide_index=True, width="stretch")
    st.caption("DP amostral (n−1); quartis com interpolação inclusiva; CV = 100 × DP / média.")
    carga = st.selectbox("Carga do piloto", [c.nome for c in config.CARGAS])
    figura = px.box(
        dados[dados["carga"] == carga], x="configuracao", y="tempo_total_s", points="all",
        category_orders={"configuracao": [c.nome for c in config.CONFIGURACOES]},
        labels={"configuracao": "Configuração", "tempo_total_s": "Tempo total M1 (s)"},
        title=f"Piloto · {carga} · todas as observações",
    )
    st.plotly_chart(figura, width="stretch")
    with st.expander("Medições brutas do piloto"):
        st.dataframe(dados, hide_index=True, width="stretch")
    st.info(
        "Próximas entregas: coleta completa (#306), validação dos dados (#307) e análise "
        "inferencial com tamanhos do efeito. Conclusões e comparação com as hipóteses "
        "serão preenchidas com os dados completos validados."
    )


def exibir_ameacas():
    st.header("5. Ameaças à validade")
    st.markdown(
        "- **Interna:** cache, carga do SO e deriva temporal; mitigar com ordem aleatória, "
        "banco novo e registro das condições e da ordem de execução.\n"
        "- **Externa:** uma máquina e cargas sintéticas sequenciais; limitar as conclusões "
        "ao ambiente medido e propor replicações em outros ambientes.\n"
        "- **Construto:** tempo da janela de operações não mede latência individual, "
        "concorrência ou durabilidade; explicitar o trecho cronometrado e os commits.\n"
        "- **Conclusão:** piloto pequeno, dependência e múltiplas comparações; preservar "
        "pares, verificar rodadas, aplicar Holm e relatar efeitos e incerteza."
    )


def exibir_impacto():
    st.header("6. Impacto para empresas e usuários")
    st.markdown(
        "Aplicações embarcadas, móveis e desktop podem usar os resultados para orientar "
        "um teste de configuração no próprio ambiente. Ganho de vazão deve ser avaliado "
        "junto ao custo aceitável de perda de dados e ao tamanho das transações. "
        "Segundo a [documentação do SQLite](https://www.sqlite.org/pragma.html#pragma_synchronous), "
        "WAL + NORMAL pode perder transações confirmadas após queda de energia; WAL + FULL "
        "oferece garantias de durabilidade mais fortes. O experimento não mede esse risco."
    )
    st.info(
        "A quantificação do impacto depende da coleta completa: ganho percentual, "
        "diferenças absolutas e IC por carga. Nenhuma configuração é declarada "
        "universalmente superior a partir deste piloto."
    )


def main():
    st.set_page_config(page_title="Lab05 · SQLite", page_icon="🗃️", layout="wide")
    st.title("Lab05 · Experimento em software real: SQLite")
    st.markdown(f"[Repositório]({config.URL_REPOSITORIO}) · [Projeto]({config.URL_PROJECT})")
    st.caption("Sprint 01 · proposta, plano de análise e piloto · S01-07 (#305)")
    for exibir in (
        exibir_software, exibir_pergunta, exibir_metodo, exibir_resultados,
        exibir_ameacas, exibir_impacto,
    ):
        exibir()


if __name__ == "__main__":
    main()
