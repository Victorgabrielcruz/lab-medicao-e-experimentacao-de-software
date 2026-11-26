"""Dashboard do experimento SQLite: descritiva, testes e efeitos (#309).

Na raiz do repositório: ``python -m streamlit run lab05/app.py``.
O dashboard somente lê os artefatos; não executa o benchmark.
"""

import csv
import json
from pathlib import Path

import streamlit as st

from experimento import config, impacto, inferencia, painel

RAIZ = Path(__file__).resolve().parent
SECOES = (
    ("1. Software", "software"), ("2. Pergunta de pesquisa", "pergunta"),
    ("3. Método", "metodo"), ("4. Resultados", "resultados"),
    ("5. Ameaças à validade", "ameacas"), ("6. Impacto para empresas e usuários", "impacto"),
)


def documento(nome, texto):
    st.markdown(f"[{texto}]({config.URL_REPOSITORIO}/docs/{nome})")


def titulo_secao(indice):
    titulo, ancora = SECOES[indice]
    st.header(titulo, anchor=ancora)


def exibir_software():
    titulo_secao(0)
    st.markdown(
        "O **SQLite** é um banco SQL embarcado: o motor roda dentro do processo da "
        "aplicação e persiste os dados localmente. Este experimento avalia o software "
        "em funcionamento pelo módulo `sqlite3` do Python."
    )
    colunas = st.columns(3)
    for coluna, titulo, texto in zip(colunas, ("Software real", "Em operação", "Alto impacto"), (
        "Motor transacional de uso geral, com código público e documentação dos autores.",
        "Mantido pelo projeto SQLite, com histórico público de versões e suporte.",
        "Usado no Android, em aplicativos da Apple, no Chrome e em clientes desktop.",
    )):
        with coluna.container(border=True):
            st.markdown(f"**{titulo}**")
            st.write(texto)
    st.markdown(
        "Fontes: [projeto SQLite](https://www.sqlite.org/index.html), "
        "[histórico de versões](https://www.sqlite.org/chronology.html) e "
        "[usuários conhecidos](https://www.sqlite.org/famous.html). A adoção justifica "
        "a relevância da pergunta; não permite extrapolar o ganho local para todos os usuários."
    )
    documento("01-software-criterios.md", "Evidências e critérios de seleção do software")


def exibir_pergunta():
    titulo_secao(1)
    with st.container(border=True):
        st.markdown(
            "**A recomendação de configurar o SQLite com WAL + synchronous=NORMAL se sustenta? "
            "Quanto desempenho o padrão DELETE + FULL deixa na mesa, e quanto desse ganho "
            "exige abrir mão da durabilidade?**"
        )
    st.markdown(
        "**Objetivo GQM:** analisar o desempenho do SQLite para avaliar configurações "
        "de journaling e sincronização, do ponto de vista de quem desenvolve aplicações "
        "com banco embarcado, em execução local com cargas sintéticas."
    )
    st.table([
        {"Pergunta": "Q1 · Efeito do WAL", "Comparação": "H1 · WAL-FULL × DELETE-FULL", "Foco": "Troca do journal mantendo FULL"},
        {"Pergunta": "Q2 · Ganho marginal de NORMAL", "Comparação": "H2 · WAL-NORMAL × WAL-FULL", "Foco": "Desempenho e durabilidade no WAL"},
        {"Pergunta": "Q3 · NORMAL e interação", "Comparação": "H3 · DELETE-NORMAL × DELETE-FULL", "Foco": "Comparar H3 com H2"},
        {"Pergunta": "Q4 · Custo na leitura", "Comparação": "H1–H3 na carga de leitura", "Foco": "Magnitude e referência prática de ±2%"},
    ])
    st.caption(
        "As três comparações são feitas nas três cargas, sem selecionar cenários pela "
        "significância. Durabilidade é discutida pela documentação, sem teste de falha de energia."
    )
    documento("02-pergunta-gqm-hipoteses.md", "GQM, métricas e hipóteses registradas")


def exibir_metodo():
    titulo_secao(2)
    st.markdown(
        f"Experimento controlado **fatorial 2 × 2**: `journal_mode` (DELETE/WAL) e "
        f"`synchronous` (FULL/NORMAL). Plano completo: **{config.N_REPETICOES} repetições "
        f"medidas + {config.N_AQUECIMENTO} aquecimentos descartados** por combinação de "
        f"tratamento e carga, totalizando **360 medições em {config.total_execucoes()} execuções**. "
        f"Semente: **{config.SEMENTE}**."
    )
    st.table([
        {"Carga": c.nome.capitalize(), "Operações": c.n_operacoes,
         "Leituras": round(c.n_operacoes * c.fracao_leitura),
         "Escritas / commits": c.n_operacoes - round(c.n_operacoes * c.fracao_leitura)}
        for c in config.CARGAS
    ])
    st.markdown(
        f"Cada execução usa banco novo com **{numero(config.LINHAS_INICIAIS, 0)} linhas** e payload "
        f"de **{config.TAMANHO_PAYLOAD} bytes**, uma conexão por vez e um commit por escrita. "
        "`perf_counter` mede operações e commits; preparação, configuração e fechamento "
        "ficam fora. Checkpoints automáticos durante a carga entram na medição. "
        "As 12 combinações são embaralhadas por rodada; a mesma carga/repetição compartilha "
        "a sequência de operações entre configurações. A análise preserva esses pares."
    )
    st.subheader("Métricas e plano de análise")
    st.table([
        {"Métrica": "M1 · Tempo total", "Unidade / escala": "segundos · razão", "Leitura": "Menor é melhor"},
        {"Métrica": "M2 · Vazão = operações / M1", "Unidade / escala": "operações/s · razão", "Leitura": "Maior é melhor"},
        {"Métrica": "M3 · Razão entre medianas de M2", "Unidade / escala": "adimensional · razão", "Leitura": "1 = sem ganho entre medianas"},
    ])
    st.markdown(
        "**Descritiva:** n, média, mediana, DP amostral, quartis, IQR, mínimo, máximo e CV, "
        "por tratamento e carga. Mediana e IQR são os resumos principais.\n\n"
        "**Inferência planejada:** teste dos sinais pareados, binomial exato bilateral, "
        f"nas nove comparações de M2, com **Holm e α = {numero(config.ALFA)}**. M1 é a "
        "transformação inversa para uma carga fixa e não gera testes redundantes; M3 "
        "é um efeito derivado. O piloto não sustenta assumir normalidade ou simetria.\n\n"
        "**Magnitude e incerteza planejadas:** diferenças absolutas, probabilidade pareada "
        "de ganho, M3 e ganho percentual; IC de 95% por bootstrap de rodadas "
        "(10.000 reamostragens, semente 42). A interação permanece exploratória, "
        "conforme o GQM. A referência de ±2% na leitura não é um teste de equivalência."
    )
    with st.expander("Classificação da pesquisa · sete categorias"):
        st.table([
            {"Categoria": categoria, "Classificação inicial": classificacao}
            for categoria, classificacao in (
                ("Natureza", "Aplicada"), ("Objetivos", "Explicativa, com componente descritivo"),
                ("Abordagem", "Quantitativa"), ("Procedimentos", "Experimental com apoio documental"),
                ("Tempo", "Transversal"), ("Controle", "Laboratório, com controle parcial do ambiente"),
                ("Nível de evidência", "Moderado, classificação inicial do protocolo"),
            )
        ])
        st.caption(
            "Versão inicial do protocolo, sujeita à revisão com a coleta completa. "
            "O piloto não comprova poder estatístico nem elimina ameaças à validade."
        )
        documento("03-categorias-pesquisa.md", "Justificativas e limites das classificações")
    plano = RAIZ / "docs" / "05-plano-analise.md"
    st.download_button("Baixar plano de análise", plano.read_text(encoding="utf-8"),
                       file_name=plano.name, mime="text/markdown", key="plano")
    documento("04-piloto-plano-coleta.md", "Registro do piloto e protocolo da coleta completa")


def numero(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tabela_numerica(tabela, casas=4, **kwargs):
    configuracao = {
        coluna: st.column_config.NumberColumn(format=f"%.{casas}f")
        for coluna in tabela.select_dtypes(include="number").columns if coluna != "n"
    }
    st.dataframe(tabela, hide_index=True, width="stretch", column_config=configuracao, **kwargs)


@st.cache_data(show_spinner=False)
def calcular_inferencia(dados):
    return inferencia.analisar(dados)


def exibir_inferencia(coleta, carga):
    st.subheader("Testes de hipótese e tamanho do efeito · #309")
    try:
        analise = calcular_inferencia(coleta.dados)
    except ValueError as erro:
        st.error(f"A análise inferencial exige pares completos e válidos: {erro}")
        return
    st.info(
        "Teste dos sinais pareados, bilateral: H0: P(ganho de vazão | não empate) = 0,5. "
        "O teste não exige normalidade ou simetria. M1 usa os mesmos pares com direção "
        "invertida; M3 é razão de medianas, sem teste separado. Holm é aplicado às "
        "nove comparações em conjunto, independentemente dos filtros."
    )
    if analise.testes.alerta_temporal.any():
        st.warning(
            "A auditoria encontrou alerta temporal. Conclusões confirmatórias nas "
            "comparações afetadas estão suspensas. Valores-p e IC são apresentados "
            "como cálculos condicionais, sem corrigir a dependência detectada."
        )
    else:
        st.info(
            "Não houve alerta nos diagnósticos de sequências após ajuste, mas isso não "
            "comprova independência. Sinais constantes não permitem esse diagnóstico. "
            "As decisões e os IC abaixo continuam condicionados à independência das rodadas."
        )
    st.dataframe(analise.testes.rename(columns={
        "carga": "Carga", "hipotese": "Hipótese", "tratamento": "Tratamento",
        "referencia": "Referência", "n_pares": "Pares", "ganhos": "Ganhos", "perdas": "Perdas",
        "empates": "Empates", "n_efetivo": "n efetivo", "p_bruto": "p bruto", "p_holm": "p Holm",
        "rejeita_condicional": "p Holm < 0,05", "alerta_temporal": "Alerta temporal", "decisao": "Decisão",
    }), hide_index=True, width="stretch", key="testes_hipotese", column_config={
        "p bruto": st.column_config.NumberColumn(format="%.3g"),
        "p Holm": st.column_config.NumberColumn(format="%.3g"),
    })
    st.caption("Empates não entram no teste dos sinais e permanecem nos efeitos de tempo/vazão e no bootstrap. Não rejeitar H0 não demonstra equivalência.")
    efeitos_carga = analise.efeitos[analise.efeitos.carga == carga]
    efeitos_visiveis = efeitos_carga[efeitos_carga.efeito.isin([
        "Probabilidade de ganho", "Efeito dos sinais (2p−1)", "M3",
    ])]
    st.markdown(f"**Efeitos na carga {carga} · IC de 95% condicionais à independência**")
    tabela_numerica(efeitos_visiveis.rename(columns={
        "carga": "Carga", "hipotese": "Hipótese", "efeito": "Efeito", "unidade": "Unidade",
        "estimativa": "Estimativa", "ic_inf": "IC inferior", "ic_sup": "IC superior", "metodo_ic": "Método do IC",
    }), key="efeitos_ic")
    st.caption(
        "A probabilidade de ganho é condicionada aos pares não empatados; 2p−1 é seu "
        "efeito direcional pareado, não o delta de Cliff para grupos independentes. "
        "M3 usa razão entre medianas, não mediana das razões. Os IC são marginais e "
        "não têm ajuste simultâneo para as nove comparações."
    )
    st.plotly_chart(painel.intervalos_m3(efeitos_carga, carga), width="stretch", key="ic_m3")
    with st.expander("Todos os efeitos, diferenças e medianas com IC"):
        tabela_numerica(analise.efeitos, key="efeitos_completos")
        tabela_numerica(analise.medianas, key="medianas_ic")
        st.caption(
            "Bootstrap percentil de 10.000 reamostragens, semente 42. Em cada carga, "
            "a rodada inteira é reamostrada nas quatro configurações e nas duas métricas. "
            "Diferença M1 = tratamento − referência (s); redução M1 positiva indica menor "
            "tempo. Diferença M2 e ganho M2 positivos indicam maior vazão."
        )
    with st.expander("Auditoria dos pressupostos e das séries pareadas"):
        st.markdown(
            "Pareamento por carga/rodada e semente exata; uma coleta e um ambiente. "
            "A auditoria usa sequências dos sinais e das diferenças em torno da mediana "
            "(runs exato, família diagnóstica separada com 18 posições e Holm). "
            "Diagnósticos indefinidos são exibidos sem valor-p. Spearman e lag 1 são "
            "descritivos, sem p assintótico ou limiar automático de independência."
        )
        st.dataframe(analise.auditoria, hide_index=True, width="stretch", key="auditoria",
                     column_config={"p_bruto": st.column_config.NumberColumn(format="%.3g"),
                                    "p_holm": st.column_config.NumberColumn(format="%.3g")})
        tabela_numerica(analise.diagnosticos, key="diagnosticos")
        hipotese = st.selectbox("Comparação para inspecionar as rodadas", ["H1", "H2", "H3"], key="auditoria_hipotese")
        serie = analise.series[(analise.series.carga == carga) & (analise.series.hipotese == hipotese)]
        st.plotly_chart(painel.serie_pareada(serie, carga, hipotese), width="stretch", key="serie_pareada")
        st.code(" ".join("+" if s > 0 else "−" if s < 0 else "0" for s in serie.sinal), language=None)
        st.caption("Sinais das diferenças de M2, da rodada 1 à 30. Sequência constante é inconclusiva para diagnosticar dependência, não evidência de independência.")
    relatorio = analise.como_dict()
    relatorio["origem"] = {"coleta": "coleta-completa-01",
                           "sha256_csv": coleta.validacao["entradas_sha256"]["resultados.csv"]}
    st.download_button("Baixar análise completa (JSON)", json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False),
                       file_name="coleta-completa-01-analise.json", mime="application/json", key="json_analise")
    st.caption(f"Versões da análise: Python {analise.parametros['python']}, NumPy {analise.parametros['numpy']}, SciPy {analise.parametros['scipy']}. As versões da coleta são registradas separadamente.")
    documento("09-testes-efeitos.md", "Métodos, auditoria, resultados e limites da #309")


def exibir_resultados():
    titulo_secao(3)
    fonte = st.selectbox("Conjunto de dados", ["Coleta completa", "Piloto"], key="coleta")
    completa = fonte == "Coleta completa"
    nome = "coleta-completa-01" if completa else "piloto"
    diretorio = config.DIR_DADOS / nome
    try:
        coleta = (painel.carregar_coleta_completa if completa else painel.carregar_piloto)(diretorio)
    except (OSError, ValueError, KeyError, AttributeError, StopIteration, csv.Error) as erro:
        st.error(f"Não foi possível ler {fonte.lower()}: {erro}")
        st.info("Confira os artefatos versionados do conjunto selecionado e, para a coleta completa, o manifesto da validação #307.")
        return
    parametros = coleta.ambiente["experimento"]
    repeticoes, aquecimentos = parametros["repeticoes"], parametros["aquecimentos"]
    if completa:
        st.success(
            f"Coleta completa validada estruturalmente · {len(coleta.dados)} medições, "
            f"{repeticoes} repetições por grupo e {aquecimentos} aquecimentos descartados. "
            f"{coleta.validacao['outliers_observacoes_unicas']} observações sinalizadas na #307; "
            "todas preservadas na descritiva e nos gráficos. Nenhuma exclusão."
        )
        st.info(
            "Descritiva da #308 e testes/efeitos da #309. A aprovação estrutural não "
            "comprova independência temporal; a auditoria e os resultados condicionais "
            "estão apresentados após a descritiva."
        )
    else:
        st.warning(
            f"Piloto exploratório · {repeticoes} repetições medidas e {aquecimentos} "
            "aquecimento(s) descartado(s) por combinação. Estes dados não respondem às "
            "hipóteses confirmatórias e não são somados à coleta completa."
        )
    colunas = st.columns(4)
    for coluna, rotulo, valor in zip(colunas,
        ("Medições analisadas", "Combinações", "Repetições por grupo", "Duração da coleta"),
        (str(len(coleta.dados)), str(len(coleta.resumo["grupos"])), str(repeticoes),
         f"{numero(coleta.execucao['duracao_parede_s'], 1)} s")):
        coluna.metric(rotulo, valor, border=True)
    st.caption(f"Fonte: lab05/data/{nome}/resultados.csv · estatísticas recalculadas a partir de todas as medições brutas.")
    with st.expander("Ambiente e rastreabilidade da coleta"):
        ambiente = coleta.ambiente
        st.table([
            {"Item": item, "Valor": str(valor)} for item, valor in (
                ("Início (UTC)", ambiente["data_hora_utc"]), ("Sistema", ambiente["sistema"]),
                ("Python da coleta", ambiente["python_version"]), ("SQLite da coleta", ambiente["sqlite_version"]),
                ("CPU", coleta.execucao["cpu"]), ("Disco", coleta.execucao["disco"]),
                ("Sistema de arquivos", coleta.execucao["sistema_arquivos"]),
                ("Semente", parametros["semente"]),
                ("Commit de referência", coleta.execucao.get("commit_benchmark", coleta.execucao.get("commit_base"))),
            )
        ])
        if completa:
            st.code(coleta.validacao["entradas_sha256"]["resultados.csv"], language=None)
            st.caption("SHA-256 do CSV conferido com o manifesto da #307; todos os cálculos preservam os dados originais.")
            documento("07-validacao-dicionario-dados.md", "Validação e dicionário das colunas")
        st.caption("O ambiente acima pertence à coleta. A máquina que abre o dashboard pode ser diferente.")
    filtros = st.columns([1, 1, 1])
    carga = filtros[0].selectbox("Carga de trabalho", [c.nome for c in config.CARGAS], key="carga")
    metrica = filtros[1].selectbox("Métrica", list(painel.METRICAS), key="metrica")
    logaritmica = filtros[2].toggle("Escala logarítmica", key="logaritmica")
    coluna, eixo, sentido = painel.METRICAS[metrica]
    dados = coleta.dados[coleta.dados.carga == carga]
    st.caption(f"{eixo} · {sentido.lower()} · {len(dados)} medições da carga selecionada.")
    graficos = st.columns(2)
    with graficos[0]:
        st.plotly_chart(painel.distribuicao(dados, coluna, eixo, carga, logaritmica), width="stretch", key="distribuicao")
    with graficos[1]:
        st.plotly_chart(painel.comparar_configuracoes(dados, coluna, eixo, carga, logaritmica), width="stretch", key="medianas")
    st.caption(
        "Boxplot: todas as observações, inclusive valores extremos. Comparação: pontos "
        "representam medianas e barras vão de Q1 a Q3; indicam dispersão, não intervalos "
        "de confiança. A escala logarítmica altera apenas a visualização."
    )
    st.subheader("Descritiva por configuração")
    tabela = painel.descritiva(dados, coluna)
    tabela_numerica(tabela.drop(columns="Carga"), key="descritiva")
    st.caption(
        f"Valores em {eixo.split('(', 1)[1].rstrip(')')}, exceto n e CV (%). "
        "DP amostral (n−1), quartis lineares, IQR = Q3 − Q1 e CV = 100 × DP / média. "
        "Tempo e vazão têm escala de razão; mediana e IQR resumem os grupos com menor "
        "sensibilidade a valores extremos. As cargas são analisadas separadamente."
    )
    st.subheader("Comparações de vazão · razões descritivas")
    comparacoes = painel.comparacoes(coleta.dados)
    comparacoes = comparacoes[comparacoes.Carga == carga].drop(columns="Carga").reset_index(drop=True)
    tabela_numerica(comparacoes, casas=2, key="comparacoes")
    h1, h2, h3 = comparacoes["M3 (×)"].tolist()
    st.markdown(
        f"Na carga **{carga}**, a razão entre as medianas de vazão é **{numero(h1)}×** em H1, "
        f"**{numero(h2)}×** em H2 e **{numero(h3)}×** em H3. "
        f"A razão H2/H3 é **{numero(h2 / h3)}×**, uma descrição exploratória da interação. "
        "Esses números descrevem o conjunto selecionado e não estabelecem significância "
        "estatística, equivalência ou causalidade geral."
    )
    st.caption("M3 = mediana M2 do tratamento / mediana M2 da referência; ganho (%) = 100 × (M3 − 1). M3 acima de 1 indica maior vazão observada.")
    with st.expander("Interação, ordem de execução e medições brutas"):
        st.plotly_chart(painel.interacao(dados, coluna, eixo, carga, logaritmica), width="stretch", key="interacao")
        st.caption("Linhas representam medianas. Linhas não paralelas descrevem um padrão a investigar; não comprovam interação estatística.")
        st.plotly_chart(painel.ordem_execucao(dados, coluna, eixo, carga), width="stretch", key="ordem")
        st.caption("A posição inclui os aquecimentos descartados. A inspeção temporal é exploratória; o gráfico não estabelece independência.")
        st.dataframe(dados, hide_index=True, width="stretch", key="brutos")
    tabela_completa = painel.descritiva_completa(coleta.dados)
    with st.expander("Descritiva de todas as cargas · M1 e M2"):
        tabela_numerica(tabela_completa, key="todas_cargas")
    downloads = st.columns(3)
    downloads[0].download_button("Baixar CSV bruto selecionado", (diretorio / "resultados.csv").read_bytes(),
                                 file_name=f"{nome}-resultados.csv", mime="text/csv", key="csv_bruto")
    downloads[1].download_button("Baixar descritiva da seleção", tabela.to_csv(index=False).encode("utf-8-sig"),
                                 file_name=f"{nome}-{carga}-{coluna}-descritiva.csv", mime="text/csv", key="csv_resumo")
    downloads[2].download_button("Baixar descritiva de todas as cargas", tabela_completa.to_csv(index=False).encode("utf-8-sig"),
                                 file_name=f"{nome}-descritiva-completa.csv", mime="text/csv", key="csv_completo")
    if completa:
        exibir_inferencia(coleta, carga)
    else:
        st.info("A inferência da #309 é calculada somente sobre a coleta completa. O piloto permanece descritivo, sem testes de hipótese ou IC inferenciais.")
    return coleta


def exibir_ameacas():
    titulo_secao(4)
    st.table([
        {"Validade": "Interna", "Ameaça": "Cache, CPU/SO, ordem e checkpoints", "Mitigação e limite": "Banco novo, ordem aleatória, condições registradas; cache não é limpo e o SO não é isolado."},
        {"Validade": "Externa", "Ameaça": "Uma máquina, uma versão e cargas sintéticas", "Mitigação e limite": "Relatar ambiente e propor replicações; não generalizar para produção ou concorrência."},
        {"Validade": "Construto", "Ameaça": "Tempo da janela não mede latência individual ou durabilidade", "Mitigação e limite": "Explicitar commits e trecho medido; garantias vêm da documentação, sem ensaio de falha."},
        {"Validade": "Conclusão", "Ameaça": "Dependência temporal e comparações múltiplas", "Mitigação e limite": "Auditoria de sequências; Holm nas nove comparações; valores-p e IC condicionais à independência. Alertas suspendem conclusões."},
    ])
    st.markdown(
        "A aleatorização distribui parte do ruído, mas não o elimina. Um banco novo "
        "não significa cache frio. Não remover observações apenas por serem lentas. "
        "A coleta completa contém 30 repetições por grupo, mas esse número, isoladamente, "
        "não comprova estabilidade, normalidade ou poder para diferenças pequenas. "
        "A descritiva preserva todas as observações sinalizadas pela validação."
    )


def exibir_cenario_impacto(coleta):
    st.subheader("Estimativa para uma empresa · cenário hipotético")
    st.info(
        "Este cenário replica proporcionalmente um resultado local. Dispositivos e frequência "
        "de uso são hipóteses ajustáveis, sem estimativa de adoção real de uma empresa. "
        "O parâmetro é a mediana da diferença pareada de tempo da coleta completa."
    )
    escolhas = st.columns(2)
    carga = escolhas[0].selectbox("Carga do cenário", [c.nome for c in config.CARGAS], key="impacto_carga")
    hipotese = escolhas[1].selectbox("Comparação do cenário", ["H1", "H2", "H3"], key="impacto_hipotese")
    premissas = st.columns(2)
    dispositivos = premissas[0].number_input("Dispositivos no cenário (hipótese)", min_value=0,
                                            max_value=1_000_000, value=10_000, step=1_000, key="impacto_dispositivos")
    lotes = premissas[1].number_input("Lotes por dispositivo/dia (hipótese)", min_value=0,
                                     max_value=10_000, value=1, step=1, key="impacto_lotes")
    analise = calcular_inferencia(coleta.dados)
    cenario = impacto.estimar(analise.efeitos, carga=carga, hipotese=hipotese,
                              dispositivos=dispositivos, lotes_por_dia=lotes)
    carga_config = next(c for c in config.CARGAS if c.nome == carga)
    leituras = round(carga_config.n_operacoes * carga_config.fracao_leitura)
    st.markdown(
        f"**{cenario.tratamento} × {cenario.referencia}** · cada lote representa "
        f"**{numero(cenario.operacoes_por_lote, 0)} operações**: {numero(leituras, 0)} leituras "
        f"e {numero(cenario.operacoes_por_lote - leituras, 0)} escritas, com um commit por escrita. "
        "As leituras são em autocommit. O modelo repete lotes equivalentes ao benchmark."
    )
    colunas = st.columns(3)
    colunas[0].metric("Redução por lote (s)", numero(cenario.reducao_por_lote_s, 6), border=True)
    colunas[1].metric("Redução por dispositivo/dia (s)", numero(cenario.reducao_dispositivo_dia_s, 6), border=True)
    colunas[2].metric("Horas equivalentes/dia", numero(cenario.horas_equivalentes_dia, 3), border=True)
    st.markdown(
        f"O cenário contém **{numero(cenario.lotes_total_dia, 0)} lotes/dia**, ou "
        f"**{numero(cenario.operacoes_total_dia, 0)} operações/dia**. "
        f"IC local de 95% escalado: **[{numero(cenario.horas_ic_inf, 3)}; "
        f"{numero(cenario.horas_ic_sup, 3)}] h equivalentes/dia**. "
        "Valores negativos indicam acréscimo de tempo."
    )
    st.caption(
        "Fórmula: horas equivalentes/dia = −mediana(tempo tratamento − tempo referência) "
        "× dispositivos × lotes por dispositivo/dia ÷ 3.600. O sinal e os extremos do IC "
        "são invertidos ao converter diferença em redução."
    )
    st.caption(
        "A faixa escala o IC marginal local, condicional à independência entre rodadas; "
        "não é intervalo de predição da frota. Multiplicar uma mediana não produz a mediana "
        "de uma soma. Horas equivalentes são tempo agregado de execução, não horas de pessoas "
        "ou redução do prazo de uma operação em paralelo."
    )
    st.markdown(
        f"**Referência pública de escala:** {numero(dispositivos, 0)} dispositivos equivalem "
        f"numericamente a **{numero(cenario.razao_referencia_publica_pct, 6)}%** de uma referência "
        "arredondada de **3 bilhões**, baseada no número histórico publicado pelo Google em "
        "13/05/2025 (a fonte informa mais de 3 bilhões). Essa razão não estima participação "
        "de mercado, usuários únicos ou uma frota atual de 2026. "
        f"[Fonte Google]({impacto.FONTES[0]['url']}) · acesso: 25/11/2026. "
        "O número público dimensiona o contexto e não multiplica o ganho local por toda a base Android."
    )
    if cenario.horas_ic_inf <= 0 <= cenario.horas_ic_sup:
        st.info("A faixa local escalada inclui zero: este cenário também admite ausência de redução ou acréscimo de tempo.")
    if carga == "leitura":
        st.info("A leitura do experimento usa SELECTs isolados em autocommit. O resultado não estima desempenho de leituras agrupadas em uma transação.")
    tabela = impacto.cenarios_alternativos(analise.efeitos, dispositivos, lotes)
    with st.expander("Comparar cenários alternativos com as mesmas premissas"):
        tabela_numerica(tabela[["carga", "hipotese", "operacoes_por_lote", "reducao_por_lote_s",
                                "horas_equivalentes_dia", "horas_ic_inf", "horas_ic_sup"]].rename(columns={
            "carga": "Carga", "hipotese": "Comparação", "operacoes_por_lote": "Operações/lote",
            "reducao_por_lote_s": "Redução por lote (s)", "horas_equivalentes_dia": "h equivalentes/dia",
            "horas_ic_inf": "Faixa inferior (h/dia)", "horas_ic_sup": "Faixa superior (h/dia)",
        }), key="cenarios_impacto")
        st.caption("As linhas são cenários alternativos, não parcelas para somar. A mesma quantidade de lotes contém volumes diferentes conforme a carga.")
    relatorio = {
        "tipo": "cenário proporcional hipotético; não é previsão populacional",
        "cenario": cenario.como_dict(), "fontes_publicas": impacto.FONTES,
        "origem": {"coleta": "coleta-completa-01", "sha256_csv": coleta.validacao["entradas_sha256"]["resultados.csv"]},
        "parametros_analise_local": analise.parametros, "limites": impacto.LIMITES,
    }
    st.download_button("Baixar cenário de impacto (JSON)", json.dumps(relatorio, ensure_ascii=False, indent=2, allow_nan=False),
                       file_name="sqlite-cenario-impacto.json", mime="application/json", key="json_impacto")


def exibir_impacto(coleta=None):
    titulo_secao(5)
    st.subheader("Escala pública de adoção · fontes e data de acesso")
    st.markdown(
        "O Google informou **mais de 3 bilhões de dispositivos Android ativos** em 13/05/2025. "
        "Os autores do SQLite estimam **mais de 1 trilhão de bancos ativos** e registram "
        "sua presença em dispositivos Android. São unidades e métodos diferentes: "
        "bancos e dispositivos não são contagens de pessoas nem população observada no experimento."
    )
    st.table([
        {"Fonte": f"[{f['publicador']} · {f['titulo']}]({f['url']})",
         "Número ou papel": (f"{f['qualificador']} {numero(f['numero'], 0)} {f['unidade']}" if "numero" in f else f["natureza"]),
         "Publicação / atualização": f.get("publicado_em", f.get("atualizado_em", "não informada na seção")),
         "Acesso": f["acessado_em"]}
        for f in impacto.FONTES
    ])
    if coleta is not None and coleta.validacao is not None:
        exibir_cenario_impacto(coleta)
    else:
        st.info("A estimativa quantitativa exige a coleta completa validada. Com o piloto ou dados indisponíveis, a seção mantém as fontes e os limites, sem calcular projeções.")
    st.markdown(
        "O estudo orienta uma decisão de configuração em aplicações **desktop, móveis "
        "e embarcadas**. Na prática, o ganho depende da carga, do disco e da política "
        "de transações. Um commit por operação não representa automaticamente aplicações "
        "que gravam em lotes ou mantêm conexões concorrentes."
    )
    st.table([
        {"Configuração": "DELETE-FULL", "Durabilidade segundo a documentação": "Depende também do sistema de arquivos; EXTRA oferece proteção adicional ao apagar o journal."},
        {"Configuração": "DELETE-NORMAL", "Durabilidade segundo a documentação": "Menos sincronizações; há risco pequeno de corrupção após falha em alguns sistemas de arquivos."},
        {"Configuração": "WAL-FULL", "Durabilidade segundo a documentação": "Sincroniza o WAL em cada commit para preservar transações confirmadas sob as garantias do armazenamento."},
        {"Configuração": "WAL-NORMAL", "Durabilidade segundo a documentação": "Mantém consistência, mas pode perder transações confirmadas após queda de energia."},
    ])
    st.markdown(
        "Fonte: [SQLite · PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous). "
        "As garantias são documentais: o benchmark não mede frequência de perda de dados, "
        "falhas de energia ou consumo de recursos."
    )
    with st.container(border=True):
        st.markdown("**Como usar esta evidência**")
        st.markdown(
            "1. Identifique a carga mais próxima da aplicação e compare diferenças absolutas e relativas.\n"
            "2. Defina a exigência de durabilidade e replique o teste no próprio ambiente.\n"
            "3. Use a coleta completa validada, efeitos e incerteza antes de recomendar uma mudança."
        )
    st.markdown(
        "**Alcance dos resultados:** a coleta completa e sua validação estrutural já foram "
        "registradas. O painel descreve tempo, vazão e variabilidade nas 12 combinações, "
        "preservando o piloto separado. As diferenças observadas não justificam eleger "
        "uma configuração universal. Os testes e IC do painel são condicionais à "
        "independência entre rodadas; diagnósticos sem alerta não comprovam esse pressuposto."
    )
    st.subheader("O que não é possível afirmar")
    st.markdown("\n".join(f"- {limite}" for limite in impacto.LIMITES))
    documento("12-estimativa-impacto.md", "Estimativa de impacto, fontes e limites da #311")
    documento("11-categorias-revisadas-conclusoes.md", "Conclusões e categorias revisadas da #312")


def main():
    st.set_page_config(page_title="Lab05 · SQLite", page_icon="🗃️", layout="wide")
    with st.sidebar:
        st.markdown("**LAB05 / SQLITE**")
        st.caption("Experimento em software real")
        st.markdown("\n\n".join(f"[{titulo}](#{ancora})" for titulo, ancora in SECOES))
        st.divider()
        st.markdown("**Dados disponíveis**")
        st.caption("Coleta completa e piloto separados · análises por conjunto")
        st.link_button("Repositório", config.URL_REPOSITORIO)
        st.link_button("Projeto da disciplina", config.URL_PROJECT)
    st.caption("LABORATÓRIO DE EXPERIMENTAÇÃO DE SOFTWARE · PUC MINAS")
    st.title("SQLite: desempenho e durabilidade")
    st.markdown("Um experimento local sobre os efeitos de **journal_mode** e **synchronous** nas cargas de escrita, leitura e mista.")
    st.caption("Coleta completa · protocolo fatorial 2 × 2 · descritiva, testes pareados e efeitos")
    for exibir in (exibir_software, exibir_pergunta, exibir_metodo):
        with st.container(border=True):
            exibir()
    with st.container(border=True):
        coleta = exibir_resultados()
    with st.container(border=True):
        exibir_ameacas()
    with st.container(border=True):
        exibir_impacto(coleta)
    st.caption("Dados sintéticos locais · sem acesso a bancos de produção · cálculos feitos a partir do CSV versionado")


if __name__ == "__main__":
    main()
