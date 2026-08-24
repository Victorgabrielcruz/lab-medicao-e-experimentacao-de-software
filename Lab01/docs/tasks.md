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

* [x] Métrica de RQ01 implementada.
* [x] Idade calculada corretamente a partir da data de criação.
* [x] Métrica de RQ02 implementada.
* [x] Apenas Pull Requests `MERGED` são contabilizadas.
* [x] Saída gerada sem erros para os registros de teste.

### Observações

Implementado em `src/metrics/rq01_rq02_age_pullrequests.py`. `age_years` é
calculado como `(collected_at - created_at) / 365.25 dias` e
`accepted_pull_requests` é copiado de `merged_pull_requests` (já filtrado para
`MERGED` pela query GraphQL). Testado em `tests/` e confirmado na coleta
completa de 1.000 repositórios (`data/processed/repos_processed_2026-08-20T222207Z.csv`,
colunas `age_years`/`accepted_pull_requests`), validado sem inconsistências em
S02-04.

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

**Responsável:** Jonathan Sena da Silva
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

* [x] Consulta retorna os campos mínimos para as RQs.
* [x] Primeiro e último commit estão disponíveis. Primeiro commit segue como
  limitação documentada (proxy por `created_at`, ver S01-02).
* [x] Quantidade de commits está disponível.
* [x] Releases, issues e Pull Requests estão disponíveis.
* [x] Dados necessários para RQ07 estão disponíveis.
* [x] Integração executa sem erro em amostra de páginas.
* [x] Estrutura de resposta documentada para uso interno.

### Observações

Consulta versionada em `src/github/queries/` (`00-popular-repos`,
`10-repo-identity`, `20-rq01-rq02-age-pullrequests`,
`30-rq03-rq04-releases-activity`, `40-rq05-rq06-language-issues`), consumida
por `src/collector/Github/GitHubApi.cs`. Schema da resposta documentado em
`docs/raw-dataset.md`. Confirmado em produção pela coleta completa dos 1.000
repositórios em `data/raw/repos_raw_2026-08-20T222207Z.csv`.

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

### Observações

Task de gestão no GitHub Projects, sem artefato de código no repositório
local para conferir automaticamente. Confirmar diretamente no board do
projeto; `src/snapshots/snapshot_project.py` (ver S02-08) pode ser usado para
exportar o estado atual do board e evidenciar o cumprimento destes critérios.

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

* [x] Falhas transitórias não interrompem a coleta imediatamente.
* [x] Erros fatais são reportados com mensagem clara.
* [x] Logs de erro ficam registrados para inspeção.
* [x] Retentativas possuem limite definido.

### Observações

Implementado em `src/collector/Github/Errors.cs` (`TransientApiException` para
rede/timeout/5xx/429/rate limit, `FatalApiException` para 401/400/token
inválido) e `GitHubApi.cs` (retentativa com backoff exponencial, até 4
tentativas, mensagens fatais claras). Logs gravados por execução em `logs/`
via `Log.cs`. Checkpoint em `data/raw/checkpoint.json` permite retomar a
coleta após falha fatal sem repetir requisições já concluídas.

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

* [x] Coleta alcança exatamente 1.000 repositórios válidos.
* [x] Paginação funciona sem duplicações.
* [x] Progresso de páginas registrado em log.
* [x] Cursores são tratados corretamente.

### Observações

Implementado em `src/collector/Collection/RepositoryCollector.cs`: loop por
`endCursor`/`hasNextPage`, deduplicação por `id` (repositório pode trocar de
página durante a coleta por mudança de ranking), checkpoint de retomada em
`Checkpoint.cs`/`PageStore.cs` e log por página em `logs/`. Confirmado pela
coleta oficial `data/raw/repos_raw_2026-08-20T222207Z.csv` (1.000 linhas, 0
duplicados descartados sem substituição).

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

* [x] CSV bruto gerado após coleta.
* [x] CSV processado gerado após métricas.
* [x] Arquivos legíveis e consistentes.
* [x] Schema documentado.

### Observações

CSV bruto gravado por `src/collector/Export/RawCsvWriter.cs`
(`data/raw/repos_raw_<coleta>.csv`); CSV processado gerado por
`src/analysis/build_processed_dataset.py`
(`data/processed/repos_processed_<coleta>.csv`). Convenções de codificação,
separador e tipos documentadas em `docs/raw-dataset.md` e
`docs/processed-dataset.md`, e verificadas por `tests/test_csv_format.py`.

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

* [x] Pipeline executa fim a fim sem erro.
* [x] Métricas aparecem no dataset processado.
* [x] Datas são normalizadas.
* [x] Métricas temporais são calculadas corretamente.
* [x] Etapas do pipeline são reexecutáveis.

### Observações

Implementado em `src/analysis/build_processed_dataset.py`, orquestrando
`src/metrics/rq01_rq02_age_pullrequests.py`,
`src/metrics/rq03_rq04_releases_activity.py` e
`src/metrics/rq05_rq06_language_issues.py`. Normaliza tipos/datas, remove
duplicidade por `id`, valida negativos e gera saída determinística. Testado em
`tests/test_build_processed_dataset.py` e confirmado na execução completa
(`repos_processed_2026-08-20T222207Z.csv`, 1.000 registros, todas as colunas
derivadas de RQ01–RQ06 presentes).

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

* [x] RQ03 validada para os 1.000 repositórios.
* [x] Primeiro e último commit validados (primeiro commit segue como proxy
  por `created_at`, conforme limitação documentada em S01-02/methodology.md).
* [x] Tempo desde o último commit validado.
* [x] Período de desenvolvimento validado.
* [x] Quantidade de commits validada.
* [x] Casos excepcionais documentados.
* [x] Métricas aprovadas para análise.

### Observações

Validação executada contra a coleta completa
(`data/raw/repos_raw_2026-08-20T222207Z.csv` /
`data/processed/repos_processed_2026-08-20T222207Z.csv`), gerando
`data/processed/validation_rq03_rq04_2026-08-20T222207Z.csv` e
`reports/drafts/validation_rq03_rq04_2026-08-20T222207Z.md`.

Resultado: 1.000 repositórios validados, 27 inconsistências, 604 outliers
(IQR), 23 repositórios no teto de `releases_count`, 0 sem último commit.

As 27 inconsistências são todas do tipo "data futura em relação à referência
da coleta" (`pushed_at`/`last_commit_date` posteriores a `collected_at`, com
defasagem máxima de ~4min50s). Causa: `collected_at` é fixado no início da
coleta paginada, mas a coleta de 1.000 repositórios leva minutos para
percorrer todas as páginas, e repositórios muito ativos (ex.:
`spring-projects/spring-boot`, `grpc/grpc`, `pytorch/pytorch`) receberam
push/commit real durante essa janela. Não é erro de coleta ou processamento —
é uma condição de corrida esperada, documentada em `docs/methodology.md`
(seções 5 e 13). Nenhum dado foi alterado ou removido; os registros
permanecem como evidência.

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

* [x] Métrica RQ05 validada sem falhas críticas.
* [x] Métrica RQ06 validada com cálculos corretos.
* [x] Casos sem issues tratados corretamente.
* [x] Evidências documentadas para revisão.

### Observações

`src/metrics/rq05_rq06_validation.py` compara o CSV processado contra o bruto
por `id`, sem alterar nenhum dos dois, reproduzindo `normalize_language`,
`is_popular_language` e `closed_issues_percentage` a partir dos dados brutos.
Testado em `tests/test_rq05_rq06_validation.py` (3 casos: dataset válido,
divergências de linguagem/issues/percentual, observações válidas de
linguagem ausente e repositório sem issues).

Validação executada contra a coleta completa
(`data/raw/repos_raw_2026-08-20T222207Z.csv` /
`data/processed/repos_processed_2026-08-20T222207Z.csv`), gerando
`data/processed/validation_rq05_rq06_2026-08-20T222207Z.csv` e
`reports/drafts/validation_rq05_rq06_2026-08-20T222207Z.md`.

Resultado: 1.000 repositórios validados, **0 inconsistências**, 87
repositórios sem linguagem primária (consistente com o valor documentado em
`docs/raw-dataset.md`) e 43 repositórios sem issues, todos com
`closed_issues_percentage` corretamente ausente (sem divisão por zero).

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

* [x] Relatório cobre todas as RQ01–RQ06.
* [x] Limitações e riscos estão explícitos.
* [x] Problemas encontrados estão documentados.
* [x] Documento disponível para revisão do grupo.

### Observações

Relatório consolidado em `reports/drafts/data_quality_2026-08-20T222207Z.md`,
reunindo os achados de S02-04, S02-05 e S02-06 contra a coleta completa
(1.000 repositórios). Cobre: cardinalidade e unicidade de `id`; as 27
inconsistências de RQ03/RQ04 (data futura por `collected_at` fixo durante
coleta paginada longa, sem impacto na qualidade); o teto de
`releases_count` (23 casos); ausência esperada de linguagem (87) e de
issues (43); os 728 outliers por IQR das quatro validações; estratégias de
mitigação (nenhuma alteração de dado bruto, casos marcados em colunas
dedicadas, regra de validação mantida estrita); e as limitações herdadas da
metodologia (proxy de primeiro commit, teto de releases, `collected_at`
fixo).

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
* [x] Artefato armazenado em local definido. Rotina e diretório definidos
  (`data/snapshots/`), só falta a execução para a Sprint 2.
* [ ] Snapshot vinculado às Issues da sprint.

### Observações

Rotina implementada em `src/snapshots/snapshot_project.py` (exporta itens do
GitHub Projects v2 via GraphQL para `data/snapshots/snapshot_<sprint>_<carimbo>.csv`,
sem sobrescrever execuções anteriores). Só existe o snapshot da Sprint 1
(`data/snapshots/snapshot_Lab01S01_20260814T013915Z.csv`); falta rodar
`python src/snapshots/snapshot_project.py Lab01S02` (requer token com escopo
`read:project`, ver `.env.example`) para gerar o snapshot da Sprint 2 e
vinculá-lo às Issues correspondentes.

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

## S03-06 — Criar pipeline único de execução (pós-coleta) [S03] — EXTRA

**Responsável:**
**Tipo:** Extra / Opcional

### Objetivo

Automatizar em um único comando o trecho do fluxo já existente do projeto que roda em Python — geração do dataset processado, validação das RQ01–RQ06 e (quando aplicável) a análise da RQ07 —, hoje executado manualmente passo a passo conforme `docs/tutorial-execucao.md`.

Esta task é uma **atividade extra da Sprint 3** e não faz parte das entregas obrigatórias da RQ07. Ela não substitui nem altera nenhuma das etapas nem das métricas já implementadas; apenas orquestra os scripts Python existentes.

**Revisão de escopo:** a etapa de coleta (`dotnet run --project src/collector`) **não** faz parte deste pipeline único. O coletor é um projeto C#/.NET separado (`src/collector/Collector.csproj`), com seu próprio ciclo de build/execução e requisitos de ambiente (SDK do .NET), independentes do interpretador Python usado nas demais etapas. Amarrar as duas linguagens num único processo orquestrador criaria acoplamento desnecessário (o script teria que localizar e parsear a saída do `dotnet run` para descobrir o nome do CSV gerado, além de exigir .NET instalado em qualquer ambiente que rode o orquestrador, inclusive em CI/testes automatizados). Por isso, a coleta continua sendo um passo manual e separado, documentado em `docs/tutorial-execucao.md`; o pipeline único assume como **entrada obrigatória** um CSV bruto já coletado (`data/raw/repos_raw_<coleta>.csv`).

### O que deve ser feito

* Criar um script orquestrador (`scripts/run_pipeline.py`) que receba o caminho de um CSV bruto já coletado (obrigatório, via argumento) e execute, na ordem:
  1. `src/analysis/build_processed_dataset.py` sobre o CSV bruto informado;
  2. os três scripts de validação (`rq01_rq02`, `rq03_rq04`, `rq05_rq06`);
  3. a análise da RQ07 (`src/analysis/rq07_analysis.py`), quando essa task (S03-02) já estiver concluída.
* Validar, antes de iniciar, que o CSV bruto informado existe e é legível; interromper com mensagem clara caso contrário (não é responsabilidade deste script rodar a coleta).
* Interromper o pipeline e reportar claramente a etapa e o motivo em caso de falha em qualquer passo (ex.: CSV ausente/malformado, inconsistência crítica).
* Registrar, ao final, o caminho de cada artefato gerado (processado, validações).
* Documentar o uso do script em `docs/tutorial-execucao.md`, deixando explícito que a coleta (`dotnet run --project src/collector`) deve ser executada manualmente antes, sem remover o passo a passo manual já existente (o script é um atalho para a parte Python, não uma substituição da documentação detalhada nem da coleta).

### Arquivos/módulos envolvidos

* `scripts/run_pipeline.py`
* `docs/tutorial-execucao.md`
* `tests/test_run_pipeline.py`

### Dependências

* S02-04
* S02-05
* S02-06
* S02-07
* S03-02 (a etapa de RQ07 do pipeline só roda quando esta task estiver concluída)

### Critérios de aceitação

* [ ] Um único comando executa processamento e as três validações em sequência, a partir de um CSV bruto informado.
* [ ] Script recusa executar (com mensagem clara) se o CSV bruto informado não existir ou for inválido, sem tentar rodar a coleta.
* [ ] Falha em qualquer etapa interrompe o pipeline com mensagem clara indicando qual etapa falhou.
* [ ] Caminhos dos artefatos gerados são exibidos ao final da execução.
* [ ] Uso documentado em `docs/tutorial-execucao.md`, incluindo a observação de que a coleta C# é um passo manual prévio, fora do escopo deste script.
* [ ] Script executa sem erros sobre um CSV bruto de amostra piloto (100 repositórios).

### Resultado esperado

Comando único que reproduz, a partir de um CSV bruto já coletado manualmente, o fluxo de processamento e validação já documentado, reduzindo erro manual e facilitando a reexecução do laboratório a cada nova sprint — sem depender de integrar a etapa de coleta em C# ao orquestrador Python.

**EXTRA:** Esta task é "opcional" e somente deve ser executada caso as entregas obrigatórias da Sprint 3 estejam concluídas.

## S03-07 — Criar dashboard Streamlit com as métricas e resultados das RQs [S03] — EXTRA

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Extra / Opcional

### Objetivo

Criar uma interface visual, usando Streamlit, que apresente as métricas utilizadas e os resultados obtidos para as RQ01–RQ06 (e RQ07, quando disponível) a partir da base processada, complementando os relatórios em Markdown com uma visualização interativa.

Esta task é uma **atividade extra da Sprint 3** e não faz parte das entregas obrigatórias da RQ07. O dashboard é somente leitura: ele não recalcula métricas nem substitui os scripts de `src/metrics/` e `src/analysis/`, apenas lê e exibe a base processada já validada.

### O que deve ser feito

* Criar `src/dashboard/app.py`, lendo o CSV processado mais recente de `data/processed/` (com opção de escolher outra execução/coleta na própria interface).
* Exibir uma visão geral da coleta: quantidade de repositórios, data de referência (`collected_at`), repositórios arquivados, repositórios sem linguagem identificada.
* Para cada RQ (01 a 06), apresentar: a métrica/fórmula utilizada (texto curto, coerente com `docs/methodology.md`), estatísticas descritivas (mediana, média, mínimo, máximo) e ao menos uma visualização (histograma, barras ou equivalente).
* Para a RQ07 (quando a análise da S03-02 estiver disponível), apresentar a comparação entre linguagens populares e não populares nas métricas de RQ02, RQ03 e RQ04.
* Adicionar filtro por linguagem primária e, se fizer sentido, por status de arquivamento.
* Tratar o caso de não existir nenhum CSV processado ainda, orientando o usuário a rodar o pipeline antes.
* Permitir a exportação de cada gráfico exibido no dashboard (ex.: botão de download em PNG/SVG e/ou dos dados subjacentes em CSV), para que os gráficos possam ser reaproveitados diretamente no Relatório Final.
* Adicionar `streamlit` (e dependências de gráficos, se usadas) a `requirements.txt`.
* Documentar como iniciar o dashboard (`streamlit run src/dashboard/app.py`) em `docs/tutorial-execucao.md` e no `README.md`.

### Arquivos/módulos envolvidos

* `src/dashboard/app.py`
* `requirements.txt`
* `docs/tutorial-execucao.md`
* `README.md`

### Dependências

* S02-04
* S02-05
* S02-06
* S02-07
* S03-06 (o dashboard é a etapa final do pipeline único, quando esta também for implementada)

### Critérios de aceitação

* [ ] Dashboard sobe com `streamlit run src/dashboard/app.py` sem erros.
* [ ] Visão geral da coleta é exibida corretamente.
* [ ] Métrica, estatísticas e ao menos um gráfico são exibidos para cada uma das RQ01–RQ06.
* [ ] Comparação da RQ07 é exibida quando a análise correspondente estiver disponível.
* [ ] Filtro por linguagem funciona sem quebrar os gráficos e estatísticas.
* [ ] Todo gráfico exibido possui opção de exportação (download em imagem e/ou CSV dos dados).
* [ ] Caso de ausência de CSV processado é tratado com mensagem clara, sem erro não tratado.
* [ ] Uso documentado em `docs/tutorial-execucao.md` e no `README.md`.

### Resultado esperado

Dashboard interativo em Streamlit, alimentado pela base processada oficial, apresentando as métricas utilizadas e os resultados de cada RQ, com opção de exportação dos gráficos, para apoiar a leitura do relatório final e a "Configuração do processo" apresentada na correção.

**EXTRA:** Esta task é "opcional" e somente deve ser executada caso as entregas obrigatórias da Sprint 3 estejam concluídas.

## S03-08 — Implementar cache local da coleta [S03] — EXTRA

**Responsável:** Matheus Fernandes
**Tipo:** Extra / Opcional

### Objetivo

Implementar cache local para a coleta de repositórios via API GraphQL do GitHub, evitando novas requisições à API quando já existe uma coleta recente e compatível disponível localmente.

Esta task é uma **atividade extra da Sprint 3**, complementar à resiliência já implementada em S01-06. Ela não altera os campos coletados nem o formato do CSV bruto gerado; apenas evita refazer requisições à API quando uma coleta anterior equivalente já está disponível.

### O que deve ser feito

* Salvar metadados da coleta em `data/cache/metadata.json` após uma execução bem-sucedida (parâmetros usados, data/hora de conclusão, caminhos dos arquivos JSON gerados).
* Adicionar a opção `USE_CACHE` (`.env`/`CollectorOptions`):
  * `USE_CACHE=true`: antes de coletar, verificar se a coleta anterior registrada em `metadata.json` usou os mesmos parâmetros, foi concluída há menos de 24 horas e se os arquivos JSON referenciados ainda existem e são válidos; em caso positivo, reaproveitar os dados localmente, sem novas requisições à API.
  * `USE_CACHE=false`: ignorar o cache e forçar nova coleta via API, atualizando o `metadata.json` ao final.
* Cair de volta (fallback) para a coleta via API sempre que o cache estiver ausente, expirado (mais de 24h), com parâmetros incompatíveis ou com arquivos JSON ausentes/inválidos.
* Garantir que uma coleta cacheada produza o CSV bruto no mesmo formato de uma coleta feita via API.
* Atualizar `metadata.json` somente após uma nova coleta concluída com sucesso pela API (nunca a partir de uma execução servida pelo cache).
* Documentar a variável `USE_CACHE` em `.env.example` e em `docs/tutorial-execucao.md`.

### Arquivos/módulos envolvidos

* `src/collector/CollectorOptions.cs`
* `src/collector/Collection/`
* `data/cache/metadata.json`
* `.env.example`
* `docs/tutorial-execucao.md`

### Dependências

* S01-04
* S01-06

### Critérios de aceitação

* [x] Coletas cacheadas mantêm o mesmo formato de CSV bruto de uma coleta via API.
* [x] Cache inválido, expirado (>24h), incompatível (parâmetros diferentes) ou com JSONs ausentes utiliza a API como fallback.
* [x] `metadata.json` é atualizado somente após uma nova coleta concluída pela API.
* [x] `USE_CACHE=false` força a atualização dos dados, ignorando qualquer cache existente.
* [x] Build do coletor executado sem erros.

### Observações

Implementado via PR #47 ("feat: implementa cache local da coleta"). Cache
controlado pela variável `USE_CACHE` e metadados persistidos em
`data/cache/metadata.json` (parâmetros da coleta, timestamp de conclusão e
referência aos arquivos JSON brutos). Validado manualmente conforme os
critérios acima; build do coletor (`dotnet build`) executado sem erros.

### Resultado esperado

Coletas repetidas com os mesmos parâmetros, dentro da janela de 24h, deixam de gerar novas requisições à API do GitHub, reduzindo tempo de execução e consumo de rate limit durante testes e reexecuções do pipeline.

**EXTRA:** Esta task é "opcional" e somente deve ser executada caso as entregas obrigatórias da Sprint 3 estejam concluídas.

---

# Relatório Final

## RF-01 — Elaborar o Relatório Final do Lab01

**Responsável:** Víctor Gabriel Cruz Pereira
**Tipo:** Obrigatória

### Objetivo

Elaborar o documento do Relatório Final do Lab01, seguindo a estrutura definida em `docs/Template_Relatorio_Laboratorio.md`, consolidando hipóteses, metodologia, resultados por RQ (RQ01–RQ07), discussão e a seção "Configuração do processo" (colunas do board, política de WIP e print do quadro Kanban).

Esta task fica sob a responsabilidade de Víctor Gabriel Cruz Pereira por ele já ser o responsável pela criação do dashboard (S03-07): os gráficos exportados diretamente do dashboard (PNG/SVG e/ou CSV) são a fonte usada para ilustrar a seção 4.2 (Visualização Gráfica) do relatório, evitando divergência entre o que é mostrado no dashboard e o que é apresentado no relatório.

### O que deve ser feito

* Preencher `docs/Template_Relatorio_Laboratorio.md` (convertido a partir de `docs/Template_Relatorio_Laboratorio.docx`) com o conteúdo real do grupo, removendo os parágrafos de "ORIENTAÇÃO".
* Redigir introdução, contexto, metodologia (desafios, decisões, etapas, ferramentas, tabela de métricas e inovações) e conclusão.
* Exportar do dashboard Streamlit (S03-07) os gráficos referentes a cada RQ (RQ01–RQ07) e inseri-los na seção de resultados/visualização gráfica do relatório.
* Redigir a discussão comparando hipótese informal vs. resultado obtido, por RQ.
* Incluir a seção "Configuração do processo": colunas do board, política de WIP e print do GitHub Projects ao final do laboratório.
* Salvar o relatório final em `reports/final/`.

### Arquivos/módulos envolvidos

* `docs/Template_Relatorio_Laboratorio.md`
* `reports/final/`
* `src/dashboard/app.py` (fonte dos gráficos exportados)

### Dependências

* S03-02
* S03-03
* S03-07

### Critérios de aceitação

* [ ] Relatório final segue a estrutura de `docs/Template_Relatorio_Laboratorio.md`, sem parágrafos de "ORIENTAÇÃO" remanescentes.
* [ ] Todas as RQs (RQ01–RQ07) possuem resultado, gráfico exportado do dashboard e discussão hipótese vs. resultado.
* [ ] Seção "Configuração do processo" presente, com print do board e política de WIP.
* [ ] Relatório final salvo em `reports/final/`.

### Resultado esperado

Relatório Final do Lab01 completo, com os gráficos de cada RQ exportados diretamente do dashboard Streamlit, pronto para entrega.
