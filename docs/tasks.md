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

`data_do_último_commit − data_do_primeiro_commit`

O período de desenvolvimento será utilizado como aproximação do intervalo em que o repositório apresentou atividade de desenvolvimento. O último commit não deverá ser interpretado automaticamente como data de conclusão do projeto.

### Arquivos/módulos envolvidos

* `src/metrics/`
* `src/analysis/`

### Dependências

* S01-04

### Critérios de aceitação

* [ ] Métrica de RQ03 implementada.
* [ ] Data do primeiro commit disponível.
* [ ] Data do último commit disponível.
* [ ] Tempo desde o último commit calculado corretamente.
* [ ] Período de desenvolvimento calculado corretamente.
* [ ] Quantidade de commits disponível.
* [ ] Resultados de teste disponíveis para revisão interna.

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

* `tests/`
* `src/metrics/`
* `data/processed/`

### Dependências

* S02-03

### Critérios de aceitação

* [ ] Regras de validação executadas.
* [ ] Não há inconsistências críticas em RQ01/RQ02.
* [ ] Pull Requests aceitas validadas.
* [ ] Evidências de validação registradas.

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
