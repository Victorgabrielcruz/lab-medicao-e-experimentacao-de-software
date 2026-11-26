# Classificação da pesquisa (7 categorias) — versão 1

Esta é a primeira versão, feita antes da coleta, e fica preservada como registro. A versão
revisada, com base no que foi de fato executado, está em
[11-categorias-revisadas-conclusoes.md](11-categorias-revisadas-conclusoes.md).

Em cada categoria, além da classificação, registramos **o que poderia contestá-la**. Uma
classificação que não admite contestação tende a superestimar a força da evidência.

## Resumo

| Categoria | Classificação | Em uma frase |
|---|---|---|
| Natureza | **Aplicada** | Responde a uma decisão de configuração que equipes tomam em produção |
| Objetivos | **Explicativa** (com uma parte descritiva) | Busca a causa da diferença de desempenho, não só descrevê-la |
| Abordagem | **Quantitativa** | Todas as variáveis dependentes são medidas numéricas em escala de razão |
| Procedimentos | **Experimental** (com apoio documental) | Os fatores são manipulados pelo grupo; os critérios e o impacto vêm de fontes publicadas |
| Tempo | **Transversal** | Uma coleta, em uma versão do software, em um período curto |
| Controle | **Experimento controlado em laboratório** (*in vitro*), com controle parcial do ambiente | Fatores manipulados, ordem aleatorizada e variáveis fixadas, mas o SO e o hardware não são isolados |
| Nível de evidência | **Moderado**: alta validade interna, baixa validade externa | Um experimento, uma máquina e cargas sintéticas, sem replicação independente |

## Justificativas

### 1. Natureza: aplicada
O estudo não busca conhecimento novo sobre como bancos de dados funcionam. Ele quer
responder a uma escolha prática: **vale trocar a configuração padrão do SQLite, e por qual
configuração?** O resultado se destina a quem embute o SQLite numa aplicação.

*O que contestaria:* nada relevante. O mecanismo (menos chamadas de `fsync`) já é conhecido
e documentado; o que falta é quantificar o custo-benefício.

### 2. Objetivos: explicativa
As hipóteses H1–H3 mudam **um fator por vez** e mantêm o restante constante. Por isso, uma
diferença na vazão pode ser atribuída ao fator alterado, e não a outra causa. A parte
descritiva (medianas, dispersão e gráfico de interação) apoia a explicação, mas não é o
objetivo final.

*O que contestaria:* a explicação causal vale **para este ambiente**. O estudo explica *que*
o fator causa a diferença na máquina medida. O *porquê* (número de `fsync`, escrita
sequencial) vem da documentação e não é medido diretamente: não contamos as chamadas de
`fsync`.

### 3. Abordagem: quantitativa
M1 (tempo), M2 (vazão) e M3 (razão de vazão) são numéricas, em escala de razão, e são
analisadas com estatística descritiva, testes de hipótese e tamanho do efeito.

*O que contestaria:* a durabilidade, que é o custo do `NORMAL`, entra de forma
**qualitativa**, pela documentação, e não é medida. Isso não torna o estudo misto, mas deixa
um lado da balança sem número (falácia de McNamara, ver
[02-pergunta-gqm-hipoteses.md](02-pergunta-gqm-hipoteses.md)).

### 4. Procedimentos: experimental, com apoio documental
O grupo controla os níveis de `journal_mode` e `synchronous`, aplica-os por `PRAGMA` e
mede o efeito: é um experimento. A pesquisa documental (sqlite.org e Stack Overflow Survey)
sustenta os três critérios do software, as garantias de cada configuração e a estimativa de
impacto.

*O que contestaria:* as cargas são **sintéticas**. O experimento não reproduz o padrão de
acesso de nenhuma aplicação real, então ele testa o motor, não um caso de uso.

### 5. Tempo: transversal
Cada configuração é medida em uma única janela de coleta, com uma versão do SQLite e do
Python. As 30 repetições servem para estimar a variabilidade, não para acompanhar a
evolução no tempo.

*O que contestaria:* nada na classificação, mas ela limita a conclusão. O resultado vale para a
versão medida (ver a seção de versões em
[01-software-criterios.md](01-software-criterios.md)) e não diz se o ganho do WAL aumentou
ou diminuiu entre versões.

### 6. Controle: experimento controlado em laboratório, com controle parcial
| Elemento | Como é controlado |
|---|---|
| Fatores | Manipulados pelo grupo, nos dois níveis cada (fatorial 2 × 2) |
| Ordem de execução | Aleatorizada com semente fixa, para espalhar efeitos de cache, aquecimento térmico e processos em segundo plano entre as configurações |
| Estado inicial | Banco novo a cada execução, com as mesmas 10.000 linhas |
| Aquecimento | 3 execuções descartadas por combinação |
| Ambiente | Registrado a cada execução (`data/ambiente.json`) |

*O que contestaria:* o **sistema operacional e o hardware não são isolados**. Cache de disco
do SO, antivírus, indexação de arquivos e variação térmica da CPU podem afetar as medições.
A aleatorização da ordem distribui esse ruído entre as configurações, mas não o elimina. Por
isso classificamos o controle como **parcial**, e não total.

### 7. Nível de evidência: moderado
O desenho garante **alta validade interna**: fatores manipulados, um fator por comparação,
ordem aleatorizada e repetições suficientes para testes. A **validade externa é baixa**: uma
máquina, um sistema de arquivos, uma versão do SQLite e cargas sintéticas, sem replicação
independente.

*O que elevaria o nível:* **replicar a coleta nas máquinas dos três integrantes**, com
sistemas operacionais e discos diferentes. O custo é baixo, porque `executar.py` é um
comando único que registra o ambiente. Se a direção dos efeitos se repetir nos três
ambientes, a conclusão deixa de ser "nesta máquina" e passa a ser "em máquinas de
desenvolvimento comuns". A decisão de replicar fica para o plano de coleta (S01-06).
