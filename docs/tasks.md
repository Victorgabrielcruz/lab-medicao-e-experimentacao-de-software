# Tasks do Projeto

Este documento organiza o plano de execução das tarefas. As tarefas listadas aqui serão convertidas posteriormente em **Issues reais** no GitHub Projects, com responsável atribuído.

---

## Organização do Grupo

| Integrante   | Responsabilidade |
| ------------ | ---------------- |
| Integrante A | RQ01 + RQ02      |
| Integrante B | RQ03 + RQ04      |
| Integrante C | RQ05 + RQ06      |

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

**Responsável:** Integrante A
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

**Responsável:** Integrante B
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

**Responsável:** Integrante C
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

* [ ] Métrica de RQ05 implementada.
* [ ] Métrica de RQ06 implementada.
* [ ] Cálculo de percentual validado com casos de teste.
* [ ] Divisão por zero tratada.
* [ ] Dataset piloto produzido.

### Resultado esperado

Métricas de RQ05 e RQ06 prontas para integração no pipeline.

---

## S01-04 — Construir coletor GraphQL de dados dos repositórios [S01]

**Responsável:** Integrante A
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

**Responsável:** Integrante B
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

**Responsável:** Integrante C
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

**Responsável:** Integrante A
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

**Responsável:** Integrante B
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

**Responsável:** Integrante C
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

**Responsável:** Integrante A
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

**Responsável:** Integrante B
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

**Responsável:** Integrante C
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

**Responsável:** Integrante A
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

**Responsável:** Integrante B
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

---

# Sprint 3 — Lab01S03

## S03-01 — Analisar idade dos repositórios e Pull Requests aceitas [S03]

**Responsável:** Integrante A
**Tipo:** Obrigatória

### Objetivo

Realizar análise dos resultados de idade dos repositórios e Pull Requests aceitas.

### O que deve ser feito

* Calcular estatísticas descritivas.
* Identificar padrões e outliers relevantes.
* Analisar distribuição da idade dos repositórios.
* Analisar distribuição das Pull Requests aceitas.
* Avaliar possíveis relações entre idade e Pull Requests.
* Registrar interpretação inicial para relatório.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/drafts/`

### Dependências

* S02-04

### Critérios de aceitação

* [ ] Estatísticas de RQ01/RQ02 produzidas.
* [ ] Achados documentados em rascunho.
* [ ] Outliers identificados.
* [ ] Resultados prontos para revisão em grupo.

### Resultado esperado

Conclusões preliminares de RQ01 e RQ02.

---

## S03-02 — Analisar releases e atividade dos repositórios [S03]

**Responsável:** Integrante B
**Tipo:** Obrigatória

### Objetivo

Realizar análise dos resultados de releases e atividade de desenvolvimento.

### O que deve ser feito

* Gerar estatísticas descritivas de releases.
* Analisar quantidade de commits.
* Analisar tempo desde o último commit.
* Analisar período de desenvolvimento.
* Identificar repositórios com atividade recente.
* Identificar repositórios sem atividade recente.
* Identificar tendências e outliers.
* Consolidar síntese para o relatório final.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/drafts/`

### Dependências

* S02-05

### Critérios de aceitação

* [ ] Estatísticas de RQ03/RQ04 concluídas.
* [ ] Tempo desde o último commit analisado.
* [ ] Período de desenvolvimento analisado.
* [ ] Quantidade de commits analisada.
* [ ] Tendências registradas com clareza.
* [ ] Conteúdo integrado ao rascunho.

### Resultado esperado

Conclusões preliminares de RQ03 e RQ04.

---

## S03-03 — Analisar linguagens e fechamento de issues [S03]

**Responsável:** Integrante C
**Tipo:** Obrigatória

### Objetivo

Realizar análise dos resultados de linguagem primária e percentual de issues fechadas.

### O que deve ser feito

* Produzir distribuição por linguagem.
* Avaliar comportamento dos percentuais de fechamento.
* Identificar valores extremos.
* Consolidar interpretação para o relatório.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/drafts/`

### Dependências

* S02-06

### Critérios de aceitação

* [ ] Resultados de RQ05/RQ06 analisados.
* [ ] Interpretações registradas em rascunho.
* [ ] Material pronto para integração final.

### Resultado esperado

Conclusões preliminares de RQ05 e RQ06.

---

## S03-04 — Analisar relações entre características dos repositórios [S03]

**Responsável:** Integrante C
**Tipo:** Obrigatória

### Objetivo

Implementar a análise integrada das características dos repositórios a partir das métricas das RQ01–RQ06 e dos dados complementares coletados.

### O que deve ser feito

* Integrar resultados das RQ01–RQ06.
* Integrar dados de contribuição externa.
* Definir previamente as relações que serão analisadas.
* Analisar linguagem × contribuição externa.
* Analisar linguagem × frequência de atualização.
* Analisar contribuição externa × releases.
* Analisar frequência de atualização × releases.
* Analisar idade × atividade.
* Analisar período de desenvolvimento × quantidade de commits.
* Gerar saída específica da RQ07.

### Arquivos/módulos envolvidos

* `src/metrics/`
* `src/analysis/`
* `reports/drafts/`

### Dependências

* S03-01
* S03-02
* S03-03

### Critérios de aceitação

* [ ] RQ07 implementada com dados consolidados.
* [ ] Variáveis utilizadas documentadas.
* [ ] Relações analisadas documentadas.
* [ ] Método de análise definido antes da interpretação dos resultados.
* [ ] Resultado pronto para revisão do grupo.

### Resultado esperado

Resposta integrada da RQ07 baseada nas demais RQs.

---

## S03-05 — Automatizar geração das visualizações das RQs [S03]

**Responsável:** Integrante B
**Tipo:** Obrigatória

### Objetivo

Automatizar geração de gráficos para apoiar os resultados das RQs.

### O que deve ser feito

* Definir conjunto mínimo de visualizações por RQ.
* Implementar rotina de geração automática.
* Gerar visualizações das métricas temporais.
* Gerar visualizações das relações analisadas na RQ07.
* Salvar saídas em diretório de figuras.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/figures/`

### Dependências

* S03-01
* S03-02
* S03-03
* S03-04

### Critérios de aceitação

* [ ] Gráficos principais gerados sem intervenção manual.
* [ ] Métricas temporais representadas adequadamente.
* [ ] Arquivos exportados em local padrão.
* [ ] Visualizações utilizáveis no relatório final.

### Resultado esperado

Pacote de figuras atualizado e reproduzível.

---

## S03-06 — Automatizar consolidação das estatísticas das RQs [S03]

**Responsável:** Integrante A
**Tipo:** Obrigatória

### Objetivo

Automatizar geração de tabelas-resumo estatísticas para todas as RQs.

### O que deve ser feito

* Definir indicadores estatísticos mínimos.
* Implementar geração automática do resumo.
* Incluir estatísticas das métricas temporais.
* Exportar resultado para uso no relatório.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/drafts/`

### Dependências

* S03-01
* S03-02
* S03-03
* S03-04

### Critérios de aceitação

* [ ] Resumo estatístico gerado automaticamente.
* [ ] Indicadores cobrem todas as RQs implementadas.
* [ ] Métricas temporais incluídas.
* [ ] Saída pronta para incorporação no relatório.

### Resultado esperado

Base estatística consolidada para redação final.

---

## S03-07 — Implementar testes automatizados das métricas [S03]

**Responsável:** Integrante C
**Tipo:** Obrigatória

### Objetivo

Criar testes para validar cálculos de métricas e evitar regressões.

### O que deve ser feito

* Definir casos de teste por métrica.
* Implementar testes automatizados.
* Testar cálculo de idade.
* Testar contagem de Pull Requests `MERGED`.
* Testar releases.
* Testar tempo desde o último commit.
* Testar período de desenvolvimento.
* Testar percentual de issues fechadas.
* Testar casos de valores ausentes e divisão por zero.
* Executar testes em pipeline local.

### Arquivos/módulos envolvidos

* `tests/`
* `src/metrics/`

### Dependências

* S01-01
* S01-02
* S01-03
* S03-04

### Critérios de aceitação

* [ ] Casos principais cobertos por testes.
* [ ] Métricas temporais possuem testes.
* [ ] Casos de borda contemplados.
* [ ] Testes executam sem falhas.
* [ ] Regressões detectáveis em futuras alterações.

### Resultado esperado

Camada mínima de confiabilidade para métricas do laboratório.

---

# Relatório Final

## FINAL-01 — Consolidar introdução e metodologia do estudo [FINAL]

**Responsável:** Integrante A
**Tipo:** Obrigatória

### Objetivo

Consolidar seção de introdução e metodologia do relatório final.

### O que deve ser feito

* Integrar contexto, objetivos e metodologia validada.
* Garantir coerência com coleta e processamento executados.
* Documentar as métricas temporais.
* Garantir alinhamento entre metodologia e implementação.
* Revisar alinhamento com requisitos do laboratório.

### Arquivos/módulos envolvidos

* `reports/final/`
* `docs/methodology.md`

### Dependências

* S02-07

### Critérios de aceitação

* [ ] Seção de metodologia consistente com implementação.
* [ ] Métricas estão definidas de acordo com o pipeline.
* [ ] Texto revisado pelo grupo.
* [ ] Versão pronta para avaliação.

### Resultado esperado

Base narrativa inicial do relatório final concluída.

---

## FINAL-02 — Consolidar resultados e evidências das RQs [FINAL]

**Responsável:** Integrante B
**Tipo:** Obrigatória

### Objetivo

Consolidar seção de resultados com tabelas e gráficos finais.

### O que deve ser feito

* Integrar resultados das RQ01–RQ07.
* Selecionar visualizações principais.
* Incluir resultados das métricas temporais.
* Garantir correspondência entre texto e evidências.
* Revisar tabelas e figuras.

### Arquivos/módulos envolvidos

* `reports/final/`
* `reports/figures/`

### Dependências

* S03-05
* S03-06

### Critérios de aceitação

* [ ] Resultados de todas as RQs apresentados.
* [ ] Métricas temporais apresentadas.
* [ ] Visualizações referenciadas corretamente.
* [ ] Seção revisada e validada pelo grupo.

### Resultado esperado

Seção de resultados pronta para submissão.

---

## FINAL-03 — Consolidar discussão, limitações e ameaças à validade [FINAL]

**Responsável:** Integrante C
**Tipo:** Obrigatória

### Objetivo

Consolidar discussão, limitações, ameaças à validade e lições do processo.

### O que deve ser feito

* Relacionar achados com limitações observadas.
* Documentar decisões de processo do grupo.
* Consolidar ameaças à validade.
* Discutir limitações das métricas temporais.
* Explicar que período de desenvolvimento é uma aproximação.
* Consolidar estratégias de mitigação.

### Arquivos/módulos envolvidos

* `reports/final/`

### Dependências

* FINAL-01
* FINAL-02

### Critérios de aceitação

* [ ] Limitações e ameaças à validade descritas.
* [ ] Discussão conectada aos resultados obtidos.
* [ ] Limitações das métricas temporais documentadas.
* [ ] Seção revisada pelo grupo.

### Resultado esperado

Análise crítica final completa e consistente.

---

## FINAL-04 — Revisar e finalizar relatório do estudo [FINAL]

**Responsável:** Integrante A
**Tipo:** Obrigatória

### Objetivo

Executar revisão final e integração de todas as seções do relatório.

### O que deve ser feito

* Padronizar estrutura, formatação e referências.
* Verificar coerência entre seções e figuras.
* Verificar alinhamento entre metodologia e resultados.
* Verificar consistência das métricas.
* Preparar versão final para entrega.

### Arquivos/módulos envolvidos

* `reports/final/`

### Dependências

* FINAL-01
* FINAL-02
* FINAL-03

### Critérios de aceitação

* [ ] Documento final sem inconsistências estruturais.
* [ ] Revisão ortográfica e técnica concluída.
* [ ] Metodologia e implementação estão alinhadas.
* [ ] Versão final pronta para submissão.

### Resultado esperado

Relatório final integrado e pronto para entrega.

---

# Tasks Incrementais

## EXTRA-01 — Aprimorar rastreabilidade e logging da coleta [EXTRA]

**Responsável:** Integrante C
**Tipo:** Incremental

### Objetivo

Ampliar rastreabilidade operacional da coleta com logs detalhados.

### O que deve ser feito

* Registrar início e fim da execução.
* Registrar duração.
* Registrar total por página.
* Registrar eventos de erro.
* Registrar retentativas.
* Definir formato único de log.

### Arquivos/módulos envolvidos

* `src/collectors/`
* `src/github/`

### Dependências

* S02-01

### Critérios de aceitação

* [ ] Logs detalhados disponíveis por execução.
* [ ] Eventos críticos identificáveis.
* [ ] Formato de log documentado.
* [ ] Duração da coleta registrada.

### Resultado esperado

Maior capacidade de auditoria da coleta.

---

## EXTRA-02 — Monitorar consumo e limites da API [EXTRA]

**Responsável:** Integrante A
**Tipo:** Incremental

### Objetivo

Monitorar consumo de rate limit para reduzir risco de interrupção da coleta.

### O que deve ser feito

* Capturar informações de rate limit por requisição.
* Criar alerta interno de limiar crítico.
* Ajustar comportamento de espera quando necessário.
* Registrar consumo nos logs.

### Arquivos/módulos envolvidos

* `src/github/`
* `src/collectors/`

### Dependências

* S01-06

### Critérios de aceitação

* [ ] Consumo de rate limit visível em execução.
* [ ] Limiar crítico detectado automaticamente.
* [ ] Coleta evita falhas por esgotamento previsível.

### Resultado esperado

Coleta mais estável em execuções longas.

---

## EXTRA-03 — Adicionar suporte à exportação em JSON [EXTRA]

**Responsável:** Integrante B
**Tipo:** Incremental

### Objetivo

Adicionar formato JSON para compartilhamento e reuso dos dados.

### O que deve ser feito

* Definir estrutura JSON de saída.
* Implementar exportação para bruto e processado.
* Validar integridade do arquivo gerado.
* Garantir correspondência com o schema dos CSVs.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `data/raw/`
* `data/processed/`

### Dependências

* S02-02

### Critérios de aceitação

* [ ] JSON bruto e processado gerados.
* [ ] Estrutura consistente com os CSVs.
* [ ] Arquivos válidos e legíveis.

### Resultado esperado

Formato adicional de dados disponível para integração.

---

## EXTRA-04 — Automatizar execução reprodutível do pipeline [EXTRA]

**Responsável:** Integrante A
**Tipo:** Incremental

### Objetivo

Facilitar reexecução completa do fluxo com parâmetros padronizados.

### O que deve ser feito

* Padronizar parâmetros de entrada.
* Definir rotina única de execução.
* Documentar passos mínimos de reprodução.
* Registrar data de referência utilizada na execução.
* Garantir que coleta, processamento e análise possam ser executados novamente.

### Arquivos/módulos envolvidos

* `src/collectors/`
* `src/analysis/`
* `README.md`

### Dependências

* S02-03

### Critérios de aceitação

* [ ] Fluxo reexecutável com passos definidos.
* [ ] Parâmetros documentados.
* [ ] Data de referência registrada.
* [ ] Saídas reproduzíveis em nova execução.

### Resultado esperado

Redução de variabilidade operacional entre execuções.

---

## EXTRA-05 — Automatizar execução das análises e resultados [EXTRA]

**Responsável:** Integrante B
**Tipo:** Incremental

### Objetivo

Automatizar a geração de resultados analíticos consolidados.

### O que deve ser feito

* Encadear execução das análises das RQs.
* Integrar geração de estatísticas e visualizações.
* Produzir artefatos de saída padronizados.
* Incluir métricas temporais nas análises automatizadas.

### Arquivos/módulos envolvidos

* `src/analysis/`
* `reports/figures/`
* `reports/drafts/`

### Dependências

* S03-05
* S03-06

### Critérios de aceitação

* [ ] Rotina única executa análises completas.
* [ ] Artefatos são gerados em diretórios padrão.
* [ ] Métricas temporais são incluídas.
* [ ] Execução documentada para o grupo.

### Resultado esperado

Processo analítico com menor esforço manual.

---

## EXTRA-06 — Ampliar cobertura de testes do projeto [EXTRA]

**Responsável:** Integrante C
**Tipo:** Incremental

### Objetivo

Expandir cobertura de testes para coleta, transformação e análise.

### O que deve ser feito

* Adicionar testes além das métricas centrais.
* Incluir cenários de erro e borda.
* Testar paginação.
* Testar tratamento de falhas da API.
* Testar transformação dos dados.
* Consolidar rotina de execução de testes.

### Arquivos/módulos envolvidos

* `tests/`
* `src/collectors/`
* `src/github/`
* `src/analysis/`

### Dependências

* S03-07

### Critérios de aceitação

* [ ] Cobertura ampliada em áreas críticas.
* [ ] Cenários de erro contemplados.
* [ ] Paginação testada.
* [ ] Execução de testes repetível.

### Resultado esperado

Maior confiabilidade geral do projeto.
