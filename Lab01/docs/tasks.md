# Tasks do Projeto

Este documento organiza o plano de execução das tarefas. As tarefas listadas aqui serão convertidas posteriormente em **Issues reais** no GitHub Projects, com responsável atribuído.

---

## Organização do Grupo

| Integrante   | Responsabilidade |
| ------------ | ---------------- |
| Víctor Gabriel Cruz Pereira | RQ01 + RQ02      |
| Jonathan Sena da Silva | RQ03 + RQ04      |
| Matheus Fernandes | RQ05 + RQ06      |

A RQ07 será desenvolvida posteriormente através da integração dos resultados das demais RQs.

---

## Regras de Rastreabilidade

* Cada task deve virar uma Issue própria no GitHub Projects.
* Cada sprint deve conter ao menos uma Issue/commit de cada integrante (A, B e C).
* Todo commit deve referenciar o número da Issue correspondente (ex.: `#123`).
* As métricas implementadas devem estar alinhadas às definições estabelecidas em `docs/methodology.md`.
* Alterações nas métricas ou regras de processamento devem ser refletidas tanto na implementação quanto na documentação metodológica.

---

# Sprint 1 — Lab01S01

## S01-01 — Implementar métricas de idade e Pull Requests aceitas [S01]

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Implementar as métricas de idade do repositório (RQ01) e quantidade de Pull Requests aceitas (RQ02).

### O que deve ser feito

* Definir a fórmula de cálculo da idade do repositório.
* Utilizar a data de criação e a data de referência da coleta.
* Definir a contagem de Pull Requests aceitas.
* Considerar como aceita uma Pull Request com estado `MERGED`.
* Integrar leitura dos campos necessários do dataset bruto.
* Produzir saída inicial das duas métricas para amostra piloto.

### Arquivos/módulos envolvidos

* `src/metrics/`
* `src/analysis/`

### Dependências

* S01-04

### Critérios de aceitação

* [ ] Métrica de RQ01 implementada.
* [ ] Idade calculada corretamente a partir da data de criação.
* [ ] Métrica de RQ02 implementada.
* [ ] Apenas Pull Requests `MERGED` são contabilizadas.
* [ ] Saída gerada sem erros para os registros de teste.

### Resultado esperado

Métricas de RQ01 e RQ02 disponíveis no pipeline para uso nas sprints seguintes.

---

## S01-02 — Implementar métricas de releases e atividade do repositório [S01]

**Responsável:** Jonathan Sena da Silva
**Tipo:** Obrigatória

### Objetivo

Implementar as métricas de número de releases (RQ03) e atividade/frequência de atualização (RQ04).

### O que deve ser feito

* Definir cálculo da quantidade de releases por repositório.
* Obter a data do primeiro commit.
* Obter a data do último commit.
* Calcular o tempo desde o último commit.
* Calcular o período de desenvolvimento.
* Obter a quantidade total de commits.
* Gerar saída piloto das métricas.

### Métricas temporais

**Tempo desde o último commit:**

`data_de_referência − data_do_último_commit`

**Período de desenvolvimento:**

`data_do_último_commit − data_de_criação_do_repositório`

A fórmula original usava o primeiro commit, mas a API não devolve esse dado numa requisição só: `history(last: 1)` é recusado pedindo um cursor `before`. As alternativas custam uma requisição extra por repositório, o que dobraria o tempo de coleta na Sprint 2. Ficou `createdAt` como aproximação do início, o que subestima o período de repositórios com histórico importado de outro sistema.

O período de desenvolvimento será utilizado como aproximação do intervalo em que o repositório apresentou atividade de desenvolvimento. O último commit não deverá ser interpretado automaticamente como data de conclusão do projeto.

### Arquivos/módulos envolvidos

* `src/metrics/rq03_rq04_releases_activity.py`
* `src/github/queries/30-rq03-rq04-releases-activity.graphql`
* `data/processed/pilot_rq03_rq04.csv`

### Dependências

* S01-04

### Critérios de aceitação

* [x] Métrica de RQ03 implementada.
* [ ] Data do primeiro commit disponível. Inviável pela API, ver acima.
* [x] Data do último commit disponível.
* [x] Tempo desde o último commit calculado corretamente.
* [x] Período de desenvolvimento calculado corretamente, com a aproximação acima.
* [x] Quantidade de commits disponível.
* [x] Resultados de teste disponíveis para revisão interna.

### Observações

A RQ04 usa `pushedAt` e não `updatedAt`. O `updatedAt` muda com qualquer alteração de metadado, até estrela nova, e inflaria a atividade de desenvolvimento. Os dois campos estão no CSV, o `updatedAt` fica só como controle.

Na validação manual de 8 repositórios apareceu um problema que não estava previsto: a API trunca `releases.totalCount` em 1000, e 4 repositórios da amostra bateram exatamente nesse valor. Média e máximo da RQ03 ficam subestimados, a mediana não é afetada. Os casos estão marcados na coluna `releases_no_teto`.

### Resultado esperado

Métricas de RQ03 e RQ04 prontas para validação na base completa.

---

## S01-03 — Implementar métricas de linguagem e fechamento de issues [S01]

**Responsável:** Matheus Fernandes
**Tipo:** Obrigatória

### Objetivo

Implementar as métricas de linguagem primária (RQ05) e percentual de issues fechadas (RQ06).

### O que deve ser feito

* Consolidar campo de linguagem primária por repositório.
* Obter quantidade de issues abertas.
* Obter quantidade de issues fechadas.
* Implementar cálculo do percentual de issues fechadas.
* Tratar repositórios sem issues para evitar divisão por zero.
* Produzir dataset piloto para conferência.

### Fórmula

`percentual = issues_fechadas / (issues_abertas + issues_fechadas) × 100`

### Arquivos/módulos envolvidos

* `src/metrics/`
* `src/analysis/`

### Dependências

* S01-04

### Critérios de aceitação

* [x] Métrica de RQ05 implementada.
* [x] Métrica de RQ06 implementada.
* [x] Cálculo de percentual validado com casos de teste.
* [x] Divisão por zero tratada.
* [ ] Dataset piloto produzido (depende da execução do coletor com token válido).

### Resultado esperado

Métricas de RQ05 e RQ06 prontas para integração no pipeline.

---

## S01-04 — Construir coletor GraphQL de dados dos repositórios [S01]

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Centralizar e integrar a consulta GraphQL com todos os campos necessários às RQ01–RQ06 e à base da RQ07.

### O que deve ser feito

* Definir consulta base com paginação.
* Integrar autenticação por token.
* Obter dados de identificação dos repositórios.
* Obter número de stars.
* Obter data de criação.
* Obter data da última atualização.
* Obter primeiro commit.
* Obter último commit.
* Obter quantidade de commits.
* Obter linguagem primária.
* Obter Pull Requests.
* Obter issues.
* Obter releases.
* Obter dados necessários para contribuição externa.
* Obter status de arquivamento (`isArchived`).
* Garantir retorno em formato consumível pelo coletor.

### Arquivos/módulos envolvidos

* `src/github/`
* `src/collectors/`

### Dependências

* Nenhuma

### Critérios de aceitação

* [ ] Consulta retorna os campos mínimos para as RQs.
* [ ] Primeiro e último commit estão disponíveis.
* [ ] Quantidade de commits está disponível.
* [ ] Releases, issues e Pull Requests estão disponíveis.
* [ ] Dados necessários para RQ07 estão disponíveis.
* [ ] Integração executa sem erro em amostra de páginas.
* [ ] Estrutura de resposta documentada para uso interno.

### Resultado esperado

Camada de coleta GraphQL pronta para alimentar as métricas.

---

## S01-05 — Configurar gestão e rastreabilidade das sprints [S01]

**Responsável:** Jonathan Sena da Silva
**Tipo:** Obrigatória

### Objetivo

Configurar o board do projeto para rastrear tarefas por sprint com responsáveis e status.

### O que deve ser feito

* Criar colunas/status do fluxo de trabalho.
* Criar Issues iniciais da Sprint 1.
* Atribuir responsáveis e labels por RQ/sprint.
* Vincular Issues às respectivas sprints.
* Definir padrão de identificação das Issues.

### Arquivos/módulos envolvidos

* Sem módulo de código (gestão no GitHub Projects)

### Dependências

* Nenhuma

### Critérios de aceitação

* [ ] Board criado e acessível ao grupo.
* [ ] Todas as tasks obrigatórias da sprint criadas como Issues.
* [ ] Responsáveis atribuídos em cada Issue.
* [ ] Issues vinculadas à Sprint 1.

### Resultado esperado

Kanban operacional com rastreabilidade por Issue.

---

## S01-06 — Implementar resiliência e tratamento de falhas da API [S01]

**Responsável:** Matheus Fernandes
**Tipo:** Obrigatória

### Objetivo

Adicionar tratamento robusto para falhas de requisição, autenticação e limites da API.

### O que deve ser feito

* Tratar respostas de erro da API.
* Implementar retentativas para falhas transitórias.
* Registrar falhas em logs para auditoria.
* Diferenciar erros transitórios de erros fatais.
* Garantir que erros fatais sejam reportados de forma clara.

### Arquivos/módulos envolvidos

* `src/github/`
* `src/collectors/`

### Dependências

* S01-04

### Critérios de aceitação

* [ ] Falhas transitórias não interrompem a coleta imediatamente.
* [ ] Erros fatais são reportados com mensagem clara.
* [ ] Logs de erro ficam registrados para inspeção.
* [ ] Retentativas possuem limite definido.

### Resultado esperado

Coleta mais resiliente a instabilidades e limites da API.

---

# Sprint 2 — Lab01S02

## S02-01 — Implementar coleta paginada dos 1.000 repositórios [S02]

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Garantir coleta completa e consistente dos 1.000 repositórios usando cursores GraphQL.

### O que deve ser feito

* Implementar loop paginado com `endCursor`/`hasNextPage`.
* Encerrar coleta ao atingir 1.000 repositórios válidos.
* Registrar progresso por página.
* Preservar a ordem de coleta.
* Evitar duplicações entre páginas.
* Registrar informações de paginação.

### Arquivos/módulos envolvidos

* `src/collectors/`
* `src/github/`

### Dependências

* S01-04
* S01-06

### Critérios de aceitação

* [ ] Coleta alcança exatamente 1.000 repositórios válidos.
* [ ] Paginação funciona sem duplicações.
* [ ] Progresso de páginas registrado em log.
* [ ] Cursores são tratados corretamente.

### Resultado esperado

Pipeline de coleta completo para amostra oficial.

---

## S02-02 — Implementar persistência dos dados em CSV [S02]

**Responsável:** Jonathan Sena da Silva
**Tipo:** Obrigatória

### Objetivo

Exportar dados coletados e métricas para arquivos CSV padronizados.

### O que deve ser feito

* Definir schema de colunas.
* Implementar escrita de CSV bruto.
* Implementar escrita de CSV processado.
* Validar codificação.
* Validar separador adotado.
* Garantir consistência dos tipos de dados.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `data/raw/`
* `data/processed/`

### Dependências

* S02-01

### Critérios de aceitação

* [ ] CSV bruto gerado após coleta.
* [ ] CSV processado gerado após métricas.
* [ ] Arquivos legíveis e consistentes.
* [ ] Schema documentado.

### Resultado esperado

Dados exportados para análise e relatório.

---

## S02-03 — Construir pipeline de transformação e cálculo das métricas [S02]

**Responsável:** Matheus Fernandes
**Tipo:** Obrigatória

### Objetivo

Consolidar o fluxo de transformação dos dados brutos em métricas processadas.

### O que deve ser feito

* Normalizar campos e tipos.
* Padronizar datas.
* Tratar valores ausentes.
* Integrar cálculos das RQ01–RQ06.
* Calcular métricas temporais da RQ04.
* Gerar saída processada padronizada.
* Garantir que o pipeline possa ser reexecutado.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `src/metrics/`

### Dependências

* S01-01
* S01-02
* S01-03
* S02-01

### Critérios de aceitação

* [ ] Pipeline executa fim a fim sem erro.
* [ ] Métricas aparecem no dataset processado.
* [ ] Datas são normalizadas.
* [ ] Métricas temporais são calculadas corretamente.
* [ ] Etapas do pipeline são reexecutáveis.

### Resultado esperado

Base processada pronta para validação e análise.

---

## S02-04 — Validar idade dos repositórios e Pull Requests aceitas [S02]

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Validar consistência das métricas RQ01 e RQ02 na base completa.

### O que deve ser feito

* Executar verificações de completude.
* Verificar faixa de valores da idade dos repositórios.
* Conferir amostras manuais.
* Validar Pull Requests `MERGED`.
* Registrar achados e correções necessárias.

### Arquivos/módulos envolvidos

* `src/metrics/rq01_rq02_validation.py`
* `tests/test_rq01_rq02_validation.py`
* `data/processed/`

### Dependências

* S02-03

### Critérios de aceitação

* [x] Regras de validação executadas.
* [x] Não há inconsistências críticas em RQ01/RQ02. Validado contra a coleta
  completa de 1.000 repositórios (`data/raw/repos_raw_2026-08-20T222207Z.csv`):
  0 inconsistências, 124 outliers registrados (apenas em `accepted_pull_requests`,
  evidência mantida, não removida).
* [x] Pull Requests aceitas validadas.
* [x] Evidências de validação registradas.

### Observações

`src/metrics/rq01_rq02_validation.py` segue o mesmo padrão de
`rq03_rq04_validation.py`: compara o CSV processado contra o bruto por `id` e
não altera nenhum dos dois. Ele verifica:

* completude de `created_at`, `collected_at`, `age_years` e
  `accepted_pull_requests`;
* faixa de valores da idade — `age_years >= 0` e `created_at` não anterior à
  fundação do GitHub (2008-04-10);
* reprodução da fórmula `age_years = (collected_at - created_at) / 365.25 dias`
  a partir das datas brutas;
* `accepted_pull_requests` igual a `merged_pull_requests` (estado `MERGED`) e
  nunca maior que `total_pull_requests`;
* outliers de `age_years` e `accepted_pull_requests` por IQR, registrados como
  evidência e não removidos;
* amostra fixa e reproduzível (seed 42) de repositórios para conferência
  manual, incluída no relatório Markdown.

Uso:

```bash
python src/metrics/rq01_rq02_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv
```

Gera `data/processed/validation_rq01_rq02_<coleta>.csv` e
`reports/drafts/validation_rq01_rq02_<coleta>.md`. Testado com 8 casos
unitários (dataset válido, divergência de fórmula, idade negativa, criação
anterior ao GitHub, PRs aceitas divergentes/maiores que o total, campos
ausentes e outliers).

**Execução na base completa (2026-08-20T22:22:07Z, 1.000 repositórios):**
0 inconsistências críticas; 124 outliers, todos em `accepted_pull_requests`
(repositórios muito populares com PRs muito acima da mediana da amostra —
esperado, mantido como evidência para revisão). Idade dos repositórios e PRs
aceitas dentro da faixa esperada em todos os registros.

### Resultado esperado

RQ01 e RQ02 validadas para análise estatística.

---

## S02-05 — Validar releases e métricas de atividade dos repositórios [S02]

**Responsável:** Jonathan Sena da Silva
**Tipo:** Obrigatória

### Objetivo

Validar consistência das métricas de releases e atividade de atualização na base completa.

### O que deve ser feito

* Validar quantidade de releases.
* Validar presença do primeiro commit.
* Validar presença do último commit.
* Validar quantidade de commits.
* Validar cálculo do tempo desde o último commit.
* Validar cálculo do período de desenvolvimento.
* Identificar repositórios sem commits.
* Revisar valores extremos e outliers.
* Registrar problemas e correções.

### Arquivos/módulos envolvidos

* `tests/`
* `src/metrics/`
* `data/processed/`

### Dependências

* S02-03

### Critérios de aceitação

* [ ] RQ03 validada para os 1.000 repositórios.
* [ ] Primeiro e último commit validados.
* [ ] Tempo desde o último commit validado.
* [ ] Período de desenvolvimento validado.
* [ ] Quantidade de commits validada.
* [ ] Casos excepcionais documentados.
* [ ] Métricas aprovadas para análise.

### Resultado esperado

RQ03 e RQ04 consistentes para etapa analítica.

---

## S02-06 — Validar linguagem e percentual de issues fechadas [S02]

**Responsável:** Matheus Fernandes
**Tipo:** Obrigatória

### Objetivo

Validar consistência das métricas de linguagem primária e percentual de issues fechadas na base completa.

### O que deve ser feito

* Validar presença e qualidade da linguagem primária.
* Conferir quantidade de issues abertas.
* Conferir quantidade de issues fechadas.
* Conferir cálculo do percentual de issues fechadas.
* Validar tratamento de repositórios sem issues.
* Registrar resultados e pendências.

### Arquivos/módulos envolvidos

* `tests/`
* `src/metrics/`
* `data/processed/`

### Dependências

* S02-03

### Critérios de aceitação

* [ ] Métrica RQ05 validada sem falhas críticas.
* [ ] Métrica RQ06 validada com cálculos corretos.
* [ ] Casos sem issues tratados corretamente.
* [ ] Evidências documentadas para revisão.

### Resultado esperado

RQ05 e RQ06 aprovadas para análise final.

---

## S02-07 — Avaliar qualidade e completude dos dados coletados [S02]

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Documentar qualidade, completude e limitações dos dados coletados.

### O que deve ser feito

* Consolidar achados das validações S02-04/05/06.
* Descrever problemas encontrados.
* Registrar impacto dos problemas.
* Documentar estratégias de mitigação.
* Registrar limitações da coleta.
* Armazenar relatório em versão de rascunho.

### Arquivos/módulos envolvidos

* `reports/drafts/`
* `data/processed/`

### Dependências

* S02-04
* S02-05
* S02-06

### Critérios de aceitação

* [ ] Relatório cobre todas as RQ01–RQ06.
* [ ] Limitações e riscos estão explícitos.
* [ ] Problemas encontrados estão documentados.
* [ ] Documento disponível para revisão do grupo.

### Resultado esperado

Visão consolidada da confiabilidade dos dados.

---

## S02-08 — Registrar evidências do fluxo de trabalho da sprint [S02]

**Responsável:** Jonathan Sena da Silva
**Tipo:** Obrigatória

### Objetivo

Registrar snapshots do board ao fim da sprint para evidência do processo.

### O que deve ser feito

* Definir rotina de captura do estado do board.
* Armazenar snapshots com identificação da sprint.
* Garantir acesso aos artefatos para avaliação.

### Arquivos/módulos envolvidos

* `data/snapshots/`

### Dependências

* S01-05

### Critérios de aceitação

* [ ] Snapshot da Sprint 2 gerado.
* [ ] Artefato armazenado em local definido.
* [ ] Snapshot vinculado às Issues da sprint.

### Resultado esperado

Histórico rastreável da execução no GitHub Projects.

# Sprint 3 — Lab01S03

## S03-01 — Consolidar dataset para análise da RQ07 [S03]

**Responsável:**  
**Tipo:** Obrigatória

### Objetivo

Integrar as métricas RQ01–RQ06 em um único dataset consistente para permitir a análise conjunta da RQ07.

### O que deve ser feito

* Integrar as métricas RQ01 e RQ02.
* Integrar as métricas RQ03 e RQ04.
* Integrar as métricas RQ05 e RQ06.
* Garantir uma linha por repositório.
* Garantir que todas as métricas estejam associadas corretamente ao mesmo repositório.
* Verificar valores ausentes e inconsistências.
* Validar a quantidade final de repositórios.
* Preparar o dataset consolidado para a análise da RQ07.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `data/processed/`
* `tests/`

### Dependências

* S02-03
* S02-04
* S02-05
* S02-06
* S02-07

### Critérios de aceitação

* [ ] Dataset consolidado contém os repositórios da amostra oficial.
* [ ] Métricas RQ01–RQ06 estão disponíveis.
* [ ] Não existem repositórios duplicados.
* [ ] Métricas estão associadas corretamente ao respectivo repositório.
* [ ] Valores ausentes estão identificados.
* [ ] Inconsistências relevantes estão registradas.
* [ ] Dataset está pronto para utilização na análise da RQ07.

### Resultado esperado

Dataset consolidado contendo as métricas RQ01–RQ06, pronto para a análise integrada da RQ07.


---

## S03-02 — Implementar análise da RQ07 [S03]

**Responsável:**
**Tipo:** Obrigatória

### Objetivo

Implementar a análise integrada das características dos repositórios populares utilizando as métricas RQ01–RQ06.

### O que deve ser feito

* Carregar o dataset consolidado.
* Definir as variáveis utilizadas na análise da RQ07.
* Realizar análise exploratória das métricas RQ01–RQ06.
* Avaliar a relação entre popularidade e as demais características dos repositórios.
* Calcular medidas de correlação quando aplicável.
* Identificar padrões e possíveis outliers.
* Gerar estatísticas necessárias para responder à RQ07.
* Produzir tabelas e visualizações necessárias para interpretação dos resultados.

### Arquivos/módulos envolvidos

* `src/analysis/rq07_analysis.py`
* `tests/test_rq07_analysis.py`

### Dependências

* S03-01

### Critérios de aceitação

* [ ] Dataset consolidado é carregado corretamente.
* [ ] Métricas RQ01–RQ06 são utilizadas na análise.
* [ ] Relações relevantes entre as métricas são calculadas.
* [ ] Estatísticas necessárias para a RQ07 são produzidas.
* [ ] Outliers relevantes são identificados.
* [ ] Visualizações necessárias são geradas.
* [ ] Análise executa sem erros.

### Resultado esperado

Análise quantitativa da RQ07 implementada, com estatísticas, relações entre as métricas e evidências necessárias para responder à questão de pesquisa.


---

## S03-03 — Interpretar e documentar resultados da RQ07 [S03]

**Responsável:** 
**Tipo:** Obrigatória

### Objetivo

Interpretar os resultados obtidos na análise da RQ07 e produzir a resposta da questão de pesquisa para integração ao relatório final.

### O que deve ser feito

* Interpretar os resultados estatísticos obtidos.
* Relacionar os resultados às hipóteses definidas para a RQ07.
* Identificar as características mais relevantes dos repositórios populares.
* Discutir relações encontradas entre as métricas.
* Identificar resultados inesperados.
* Registrar limitações da análise.
* Elaborar a resposta final da RQ07.
* Preparar os resultados para integração ao relatório do projeto.

### Arquivos/módulos envolvidos

* `reports/`
* `docs/`

### Dependências

* S03-02

### Critérios de aceitação

* [ ] RQ07 possui uma resposta baseada nos dados coletados.
* [ ] Hipótese da RQ07 é discutida.
* [ ] Principais resultados são apresentados.
* [ ] Relações relevantes entre as métricas são discutidas.
* [ ] Resultados inesperados são registrados quando existentes.
* [ ] Limitações da análise estão documentadas.
* [ ] Texto final está pronto para integração ao relatório.

### Resultado esperado

Resposta final da RQ07 documentada e fundamentada nos resultados da análise das métricas RQ01–RQ06.

## S03-04 — Identificar outliers nos repositórios [S03] — EXTRA

**Responsável:**  
**Tipo:** Extra / Opcional

### Objetivo

Identificar repositórios que apresentam valores significativamente diferentes do comportamento geral da amostra nas métricas analisadas no Lab01.

Esta task é uma **atividade extra da Sprint 3** e não faz parte das entregas obrigatórias da RQ07.

### O que deve ser feito

* Utilizar o dataset consolidado das métricas RQ01–RQ06.
* Identificar outliers nas principais métricas quantitativas.
* Avaliar diferentes métodos de identificação de outliers, quando aplicável.
* Utilizar medidas estatísticas como quartis e IQR.
* Identificar repositórios com valores extremos de:
  * idade;
  * Pull Requests aceitas;
  * releases;
  * atividade;
  * percentual de issues fechadas;
  * popularidade.
* Registrar os repositórios identificados como possíveis outliers.
* Comparar os outliers com o comportamento geral da amostra.
* Evitar remover automaticamente os outliers do dataset principal.

### Arquivos/módulos envolvidos

* `src/analysis/rq07_outliers.py`
* `tests/test_rq07_outliers.py`

### Dependências

* S03-01
* S03-02

### Critérios de aceitação

* [ ] Outliers são identificados utilizando um método estatístico definido.
* [ ] O método utilizado é documentado.
* [ ] Outliers das principais métricas são identificados.
* [ ] Os repositórios identificados podem ser rastreados pelo seu nome.
* [ ] Os resultados são apresentados sem alterar o dataset original.
* [ ] A análise executa sem erros.

### Resultado esperado

Lista dos principais repositórios identificados como outliers nas métricas analisadas, acompanhada das respectivas métricas e valores extremos.

**EXTRA:** Esta task é "opcional" e somente deve ser executada caso as entregas obrigatórias da Sprint 3 estejam concluídas.

## S03-05 — Analisar e interpretar os outliers identificados [S03] — EXTRA

**Responsável:**
**Tipo:** Extra / Opcional

### Objetivo

Analisar os repositórios identificados como outliers e verificar quais características podem explicar seus comportamentos extremos.

Esta task é uma **atividade extra da Sprint 3** e não faz parte das entregas obrigatórias da RQ07.

### O que deve ser feito

* Analisar os principais outliers encontrados na S03-04.
* Comparar os valores dos outliers com média, mediana e quartis da amostra.
* Identificar padrões entre os repositórios extremos.
* Verificar se os outliers apresentam características específicas relacionadas à popularidade.
* Avaliar se os valores extremos podem representar casos relevantes ou possíveis anomalias nos dados.
* Registrar exemplos representativos.
* Documentar os principais achados.

### Arquivos/módulos envolvidos

* `src/analysis/rq07_outliers.py`
* `reports/`
* `docs/`

### Dependências

* S03-04

### Critérios de aceitação

* [ ] Principais outliers possuem interpretação documentada.
* [ ] Comparação com o comportamento geral da amostra é apresentada.
* [ ] Casos relevantes são destacados.
* [ ] Possíveis anomalias ou problemas nos dados são registrados.
* [ ] Os resultados podem ser utilizados como complemento à discussão da RQ07.

### Resultado esperado

Análise interpretativa dos principais outliers encontrados, identificando comportamentos extremos e possíveis explicações para esses casos.

**EXTRA:** Esta task é "opcional" e somente deve ser executada caso as entregas obrigatórias da Sprint 3 estejam concluídas.
