"""Dashboard do experimento SQLite: protocolo e exploração do piloto (#305).

Na raiz do repositório: ``python -m streamlit run lab05/app.py``.
O dashboard somente lê os artefatos; não executa o benchmark.
"""

import csv
from pathlib import Path

import streamlit as st

from experimento import config, painel

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


def exibir_resultados():
    titulo_secao(3)
    diretorio = config.DIR_DADOS / "piloto"
    try:
        piloto = painel.carregar_piloto(diretorio)
    except (OSError, ValueError, KeyError, AttributeError, StopIteration, csv.Error) as erro:
        st.error(f"Não foi possível ler o piloto: {erro}")
        st.info("Restaure os arquivos do piloto versionado: resultados.csv, ambiente.json e execucao.json.")
        return
    parametros = piloto.ambiente["experimento"]
    repeticoes, aquecimentos = parametros["repeticoes"], parametros["aquecimentos"]
    st.warning(
        f"Piloto exploratório · {repeticoes} repetições medidas e {aquecimentos} "
        f"{'aquecimento descartado' if aquecimentos == 1 else 'aquecimentos descartados'} "
        "por combinação. Os dados não respondem às hipóteses "
        "confirmatórias. As razões abaixo descrevem esta amostra; não são apresentados "
        "valores-p ou IC inferenciais do piloto."
    )
    colunas = st.columns(4)
    for coluna, nome, valor in zip(colunas,
        ("Medições do piloto", "Combinações", "Repetições por grupo", "Duração da coleta"),
        (str(len(piloto.dados)), str(len(piloto.resumo["grupos"])), str(repeticoes),
         f"{numero(piloto.execucao['duracao_parede_s'], 1)} s")):
        coluna.metric(nome, valor, border=True)
    st.caption("Fonte: lab05/data/piloto/resultados.csv · estatísticas recalculadas a partir das medições brutas.")
    with st.expander("Ambiente e rastreabilidade da coleta"):
        ambiente = piloto.ambiente
        st.table([
            {"Item": nome, "Valor": str(valor)} for nome, valor in (
                ("Início (UTC)", ambiente["data_hora_utc"]), ("Sistema", ambiente["sistema"]),
                ("Python da coleta", ambiente["python_version"]), ("SQLite da coleta", ambiente["sqlite_version"]),
                ("CPU", piloto.execucao["cpu"]), ("Disco", piloto.execucao["disco"]),
                ("Sistema de arquivos", piloto.execucao["sistema_arquivos"]),
                ("Semente", parametros["semente"]), ("Commit do benchmark", piloto.execucao["commit_benchmark"]),
            )
        ])
        st.caption("O ambiente acima pertence à coleta. A máquina que abre o dashboard pode ser diferente.")
    filtros = st.columns([1, 1, 1])
    carga = filtros[0].selectbox("Carga de trabalho", [c.nome for c in config.CARGAS], key="carga")
    metrica = filtros[1].selectbox("Métrica", list(painel.METRICAS), key="metrica")
    logaritmica = filtros[2].toggle("Escala logarítmica", key="logaritmica")
    coluna, eixo, sentido = painel.METRICAS[metrica]
    dados = piloto.dados[piloto.dados.carga == carga]
    st.caption(f"{eixo} · {sentido.lower()} · pontos individuais preservados; linhas da interação representam medianas.")
    graficos = st.columns(2)
    with graficos[0]:
        st.plotly_chart(painel.distribuicao(dados, coluna, eixo, carga, logaritmica), width="stretch", key="distribuicao")
    with graficos[1]:
        st.plotly_chart(painel.interacao(dados, coluna, eixo, carga, logaritmica), width="stretch", key="interacao")
    st.caption(
        "Com apenas três pontos por grupo, o boxplot é um resumo visual. Linhas não paralelas "
        "sugerem um padrão a investigar, sem comprovar interação estatística."
    )
    st.subheader("Descritiva por configuração")
    tabela = painel.descritiva(dados, coluna)
    tabela_numerica(tabela.drop(columns="Carga"), key="descritiva")
    st.caption(f"Valores em {eixo.split('(', 1)[1].rstrip(')')}, exceto n e CV (%). DP amostral (n−1), quartis lineares e IQR = Q3 − Q1.")
    st.subheader("Comparações de vazão · efeito observado no piloto")
    comparacoes = painel.comparacoes(piloto.dados)
    comparacoes = comparacoes[comparacoes.Carga == carga].drop(columns="Carga").reset_index(drop=True)
    tabela_numerica(comparacoes, casas=2, key="comparacoes")
    h1, h2, h3 = comparacoes["M3 (×)"].tolist()
    st.markdown(
        f"Na carga **{carga}**, a razão entre as medianas de vazão é **{numero(h1)}×** em H1, "
        f"**{numero(h2)}×** em H2 e **{numero(h3)}×** em H3. "
        f"A razão H2/H3 é **{numero(h2 / h3)}×**, uma descrição exploratória da interação. "
        "Esses números descrevem o piloto e não estabelecem superioridade, equivalência ou causalidade geral."
    )
    st.caption("M3 = mediana M2 do tratamento / mediana M2 da referência; ganho (%) = 100 × (M3 − 1). M3 acima de 1 indica maior vazão observada.")
    with st.expander("Ordem de execução e medições brutas"):
        st.plotly_chart(painel.ordem_execucao(dados, coluna, eixo, carga), width="stretch", key="ordem")
        st.caption("A ordem inclui os aquecimentos descartados. Este gráfico ajuda a inspecionar deriva temporal; três rodadas não estabelecem independência.")
        st.dataframe(dados, hide_index=True, width="stretch", key="brutos")
    downloads = st.columns(2)
    downloads[0].download_button("Baixar CSV completo do piloto", (diretorio / "resultados.csv").read_bytes(),
                                 file_name="piloto-resultados.csv", mime="text/csv", key="csv_piloto")
    downloads[1].download_button("Baixar descritiva da seleção", tabela.to_csv(index=False).encode("utf-8-sig"),
                                 file_name=f"piloto-{carga}-{coluna}-descritiva.csv", mime="text/csv", key="csv_resumo")


def exibir_ameacas():
    titulo_secao(4)
    st.table([
        {"Validade": "Interna", "Ameaça": "Cache, CPU/SO, ordem e checkpoints", "Mitigação e limite": "Banco novo, ordem aleatória, condições registradas; cache não é limpo e o SO não é isolado."},
        {"Validade": "Externa", "Ameaça": "Uma máquina, uma versão e cargas sintéticas", "Mitigação e limite": "Relatar ambiente e propor replicações; não generalizar para produção ou concorrência."},
        {"Validade": "Construto", "Ameaça": "Tempo da janela não mede latência individual ou durabilidade", "Mitigação e limite": "Explicitar commits e trecho medido; garantias vêm da documentação, sem ensaio de falha."},
        {"Validade": "Conclusão", "Ameaça": "Piloto pequeno, dependência e comparações múltiplas", "Mitigação e limite": "Preservar pares e auditar rodadas; Holm, efeitos e IC previstos na análise completa."},
    ])
    st.markdown(
        "A aleatorização distribui parte do ruído, mas não o elimina. Um banco novo "
        "não significa cache frio. Não remover observações apenas por serem lentas. "
        "O piloto valida o fluxo de coleta e descreve sua variabilidade; três repetições "
        "não permitem demonstrar estabilidade, normalidade ou poder para diferenças pequenas."
    )


def exibir_impacto():
    titulo_secao(5)
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
        "**Conclusão do piloto:** o pipeline produz as 12 combinações planejadas e permite "
        "examinar tempo, vazão e variabilidade. As diferenças observadas motivam a análise "
        "completa; não justificam eleger uma configuração universal. "
        "O próximo marco científico é a coleta de 360 medições, sua validação e a execução "
        "do plano de análise, preservando o piloto separado."
    )


def main():
    st.set_page_config(page_title="Lab05 · SQLite", page_icon="🗃️", layout="wide")
    with st.sidebar:
        st.markdown("**LAB05 / SQLITE**")
        st.caption("Experimento em software real")
        st.markdown("\n\n".join(f"[{titulo}](#{ancora})" for titulo, ancora in SECOES))
        st.divider()
        st.markdown("**Dados disponíveis**")
        st.caption("Piloto versionado · análise exploratória")
        st.link_button("Repositório", config.URL_REPOSITORIO)
        st.link_button("Projeto da disciplina", config.URL_PROJECT)
    st.caption("LABORATÓRIO DE EXPERIMENTAÇÃO DE SOFTWARE · PUC MINAS")
    st.title("SQLite: desempenho e durabilidade")
    st.markdown("Um experimento local sobre os efeitos de **journal_mode** e **synchronous** nas cargas de escrita, leitura e mista.")
    st.caption("Painel do piloto · protocolo fatorial 2 × 2 · proposta, método e resultados exploratórios")
    for exibir in (exibir_software, exibir_pergunta, exibir_metodo, exibir_resultados,
                   exibir_ameacas, exibir_impacto):
        with st.container(border=True):
            exibir()
    st.caption("Dados sintéticos locais · sem acesso a bancos de produção · cálculos feitos a partir do CSV versionado")


if __name__ == "__main__":
    main()
