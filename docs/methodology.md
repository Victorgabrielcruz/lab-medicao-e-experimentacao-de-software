# Metodologia

## 1. Objetivo

Definir um processo reproduzível para coletar e analisar dados dos 1.000 repositórios mais populares do GitHub, de forma a responder às 7 questões de pesquisa (RQs) do laboratório sem antecipar resultados.

---

## 2. Seleção dos Repositórios

A amostra será composta pelos 1.000 repositórios públicos com maior número de estrelas no GitHub no momento da coleta.

### Critérios

* considerar apenas repositórios públicos;
* ordenar por número de estrelas (`stars`) de forma decrescente;
* coletar exatamente 1.000 registros válidos;
* registrar a data e hora da coleta;
* utilizar o ranking observado no momento da execução, sem considerar rankings históricos.

### Critérios de validade

Um repositório será considerado válido quando:

* estiver acessível publicamente durante a coleta;
* possuir os campos obrigatórios definidos para as RQs;
* não apresentar erro irrecuperável durante a coleta;
* puder ser identificado de forma única por seu identificador no GitHub.

Repositórios que apresentarem falhas temporárias serão submetidos a retentativas. Caso permaneçam indisponíveis ou inconsistentes, serão descartados e substituídos pelo próximo repositório elegível no ranking.

Repositórios arquivados não serão excluídos automaticamente da amostra. Seu status será coletado e poderá ser utilizado posteriormente nas análises.

---

## 3. Fonte dos Dados

A fonte oficial será a API GraphQL do GitHub, consultada por meio de token com permissões adequadas para leitura dos metadados públicos dos repositórios.

A API será utilizada para obter informações sobre:

* identificação dos repositórios;
* popularidade;
* datas;
* commits;
* linguagem;
* pull requests;
* issues;
* releases;
* contribuições externas;
* status do repositório.

---

## 4. Processo de Coleta

O processo de coleta seguirá as seguintes etapas:

1. definir a consulta GraphQL com os campos necessários para todas as RQs;
2. executar a consulta de forma paginada;
3. ordenar os repositórios por número de estrelas em ordem decrescente;
4. coletar os repositórios até atingir 1.000 registros válidos;
5. armazenar as respostas brutas em `data/raw/`;
6. registrar logs da execução;
7. consolidar os dados coletados;
8. executar as etapas de limpeza e validação;
9. gerar o dataset processado em `data/processed/`.

Os logs deverão registrar, no mínimo:

* data e hora da execução;
* quantidade de páginas processadas;
* quantidade de repositórios coletados;
* quantidade de registros válidos;
* quantidade de registros descartados;
* erros encontrados;
* retentativas realizadas;
* informações relacionadas ao rate limit.

---

## 5. Data de Referência

A **data de referência da coleta** será o instante utilizado como base para o cálculo das métricas temporais.

Essa informação será registrada em formato ISO 8601 e utilizada para calcular métricas como:

* idade do repositório;
* tempo desde o último commit;
* tempo desde a última atualização.

A data de referência deverá ser registrada juntamente aos dados da execução para permitir a reprodução e interpretação dos resultados.

---

## 6. API GraphQL

A consulta GraphQL deverá recuperar, no mínimo, atributos de identificação e indicadores necessários para responder às RQs.

Entre os campos coletados estarão:

* identificador do repositório;
* nome completo;
* URL;
* número de estrelas;
* data de criação;
* data da última atualização;
* primeiro commit;
* último commit;
* quantidade de commits;
* linguagem primária;
* pull requests;
* issues;
* releases;
* contribuições externas;
* status de arquivamento.

A consulta GraphQL deverá ser versionada no projeto para garantir repetibilidade e auditoria.

---

## 7. Paginação

A paginação será implementada utilizando cursores da API GraphQL, por meio de:

* `pageInfo.endCursor`;
* `pageInfo.hasNextPage`.

### Regras

* utilizar tamanho de página constante durante cada execução;
* preservar a ordem dos repositórios;
* interromper a coleta quando forem obtidos 1.000 registros válidos;
* realizar retentativas para falhas transitórias;
* tratar limites de requisições da API;
* registrar informações de paginação nos logs.

---

## 8. Dados Coletados

Os dados coletados deverão cobrir o mínimo necessário para responder às RQs.

### Identificação

* identificador do repositório;
* nome completo;
* URL;
* proprietário/organização.

### Popularidade

* número de estrelas.

### Informações temporais

* data de criação;
* data do primeiro commit;
* data do último commit;
* data da última atualização;
* data/hora da coleta.

### Desenvolvimento

* quantidade total de commits;
* status de arquivamento.

### Linguagem

* linguagem primária.

### Pull Requests

* quantidade total de pull requests;
* quantidade de pull requests aceitas (`MERGED`).

### Issues

* quantidade de issues abertas;
* quantidade de issues fechadas.

### Releases

* quantidade de releases.

### Contribuição externa

Os campos necessários para identificar e quantificar contribuições externas deverão ser coletados de acordo com a definição operacional da RQ07.

---

## 9. Métricas das Questões de Pesquisa

### RQ01 — Idade do Repositório

**Métrica:** idade do repositório, em anos.

Será calculada pela diferença entre a data de referência da coleta e a data de criação do repositório.

**Fórmula conceitual:**

`idade = data_de_referência − data_de_criação`

---

### RQ02 — Pull Requests Aceitas

**Métrica:** número de pull requests aceitas por repositório.

Será considerada aceita uma Pull Request cujo estado seja `MERGED`.

A métrica será calculada a partir da quantidade total de Pull Requests que foram efetivamente integradas ao repositório.

---

### RQ03 — Releases

**Métrica:** número total de releases do repositório.

A contagem será obtida a partir das releases registradas no GitHub e disponíveis por meio da API utilizada na coleta.

---

### RQ04 — Atividade e Frequência de Atualização

A atividade do repositório será analisada utilizando métricas temporais derivadas dos commits.

Serão consideradas:

* **data do último commit**;
* **tempo desde o último commit**;
* **período de desenvolvimento**;
* **quantidade de commits**.

### Tempo desde o último commit

Calculado pela diferença entre a data de referência e a data do último commit.

`tempo_desde_ultimo_commit = data_de_referência − data_do_último_commit`

Essa métrica será utilizada como indicador de atividade recente.

### Período de desenvolvimento

Calculado pela diferença entre o primeiro e o último commit identificado.

`tempo_de_desenvolvimento = data_do_último_commit − data_do_primeiro_commit`

Essa métrica representa uma aproximação do período em que houve atividade de desenvolvimento no repositório.

### Observação

O último commit não será interpretado automaticamente como a data de conclusão do projeto, pois um repositório pode estar ativo, abandonado ou ter sido concluído antes de seu último commit.

---

### RQ05 — Linguagem de Programação

**Métrica:** linguagem primária de cada repositório.

Será calculada a distribuição dos repositórios da amostra de acordo com sua linguagem primária.

Também poderão ser calculadas frequências absolutas e relativas por linguagem.

Para classificar "linguagens mais populares" nas RQs 05 e 07, será utilizado o ranking
do [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/),
baseado na contagem de contribuidores na plataforma GitHub. Serão consideradas populares:
TypeScript, Python, JavaScript, Java, C#, PHP, Shell, C++, HCL e Go. Um repositório será
marcado como linguagem popular quando sua `primaryLanguage` estiver nessa lista.

Quando a API retornar `primaryLanguage` nula ou vazia, o valor será normalizado como
`Sem linguagem identificada`; esse caso será mantido na análise e não será classificado
como linguagem popular.

---

### RQ06 — Issues Fechadas

**Métrica:** percentual de issues fechadas por repositório.

A métrica será calculada utilizando:

`percentual = issues_fechadas / (issues_abertas + issues_fechadas) × 100`

Repositórios sem issues serão tratados separadamente, evitando divisão por zero e evitando interpretar ausência de issues como percentual de fechamento.

No dataset processado, repositórios sem issues terão `has_issues = false` e
`closed_issues_percentage` vazio (`null`). Portanto, ausência de issues não será
interpretada como 0% nem como 100% de fechamento.

---

### RQ07 — Relação entre Características dos Repositórios

A RQ07 realizará uma análise integrada das características observadas nas RQs anteriores.

Serão consideradas, conforme aplicável:

* linguagem primária;
* contribuição externa;
* quantidade de pull requests aceitas;
* quantidade de releases;
* frequência de atualização;
* tempo desde o último commit;
* período de desenvolvimento;
* quantidade de commits;
* idade do repositório.

As análises poderão considerar relações como:

* linguagem × contribuição externa;
* linguagem × frequência de atualização;
* contribuição externa × releases;
* frequência de atualização × releases;
* contribuição externa × atividade do projeto.

As variáveis utilizadas e os métodos estatísticos aplicados deverão ser definidos antes da análise dos resultados, evitando alterações metodológicas motivadas pelos resultados encontrados.

---

## 10. Processamento dos Dados

Após a coleta, os dados serão submetidos às seguintes etapas:

* normalização dos tipos de dados;
* padronização de datas;
* conversão de valores numéricos;
* remoção de duplicidades;
* tratamento de valores ausentes;
* identificação de valores inconsistentes;
* validação das relações entre campos;
* cálculo das métricas derivadas;
* geração dos datasets intermediários;
* geração do dataset final para análise.

As métricas temporais serão calculadas utilizando a mesma data de referência definida para a execução.

Os dados brutos não deverão ser sobrescritos durante o processamento.

---

## 11. Validação dos Dados

A validação incluirá:

* conferência da cardinalidade final de 1.000 repositórios;
* verificação da unicidade dos identificadores;
* verificação de completude dos campos obrigatórios;
* verificação de datas inválidas;
* verificação de valores negativos ou inconsistentes;
* verificação de divisão por zero no cálculo de percentuais;
* conferência de consistência entre totais e métricas derivadas;
* validação por amostragem manual de registros críticos;
* comparação de uma amostra dos dados processados com os dados brutos.

---

## 12. Reprodutibilidade

Para garantir a reprodutibilidade:

* versionar a consulta GraphQL;
* versionar o código do pipeline;
* registrar a data e hora da coleta;
* registrar parâmetros de execução;
* registrar tamanho das páginas;
* registrar informações de paginação;
* manter dados brutos e processados separados;
* registrar erros e retentativas;
* documentar as fórmulas das métricas;
* rastrear tarefas por Issues e commits vinculados.

A estrutura de dados deverá permitir identificar a origem de cada registro processado a partir dos dados brutos.

---

## 13. Limitações

A metodologia apresenta as seguintes limitações:

* os dados representam o estado dos repositórios no momento da coleta;
* o número de estrelas pode mudar após a coleta;
* alterações futuras nos repositórios podem modificar os resultados;
* limites da API podem restringir a quantidade de dados recuperáveis;
* indisponibilidade temporária da API pode afetar a coleta;
* o primeiro e o último commit representam aproximações do período de desenvolvimento;
* o último commit não representa necessariamente a conclusão do projeto;
* métricas de contribuição externa dependem da disponibilidade e granularidade dos dados fornecidos pelo GitHub;
* resultados da RQ07 dependem da qualidade e completude das métricas utilizadas nas análises integradas.

---

## 14. Artefatos da Coleta

A execução da metodologia deverá produzir, no mínimo:

* consulta GraphQL versionada;
* dados brutos em `data/raw/`;
* dados processados em `data/processed/`;
* logs da coleta;
* documentação dos parâmetros utilizados;
* dataset final utilizado nas análises;
* registro da data e hora de referência da coleta.
