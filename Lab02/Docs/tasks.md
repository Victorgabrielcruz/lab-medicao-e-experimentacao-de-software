# Tasks do Projeto — Lab02

Este documento organiza o trabalho do Lab02 em tarefas que deverão ser convertidas em **Issues reais** no GitHub Projects. A atribuição dos responsáveis será feita posteriormente pelo grupo diretamente no board; por isso, este planejamento não associa tarefas a integrantes específicos.

---

## Regras de organização e rastreabilidade

- Cada task deste documento deve originar uma Issue própria no GitHub Projects.
- Cada trial deve possuir uma Issue individual, identificada pela combinação `participante + kata + tratamento`.
- Todo commit deve mencionar o número da Issue correspondente, por exemplo: `#42 implementa coleta de métricas do trial`.
- Em cada sprint — S01, S02 e S03 —, cada integrante deve ser Assignee de pelo menos uma Issue que produza artefato de código commitado.
- Issues exclusivamente documentais ou administrativas não atendem, sozinhas, ao requisito de contribuição individual por sprint.
- As tarefas devem ser movimentadas no board conforme o progresso real, sem atualização retroativa apenas no encerramento da sprint.
- Os limites de WIP definidos pelo grupo devem ser respeitados.
- Mudanças no protocolo devem ser refletidas em [`methodology.md`](methodology.md) antes da coleta ou registradas como desvio metodológico.
- Dados brutos nunca devem ser sobrescritos manualmente.
- Critérios de aceitação somente devem ser marcados após a existência de evidência verificável no repositório ou no GitHub Projects.

## Visão geral das entregas

| Entrega | Escopo | Pontos |
|---|---|---:|
| Lab02S01 | Desenho do experimento e preparação | 5 |
| Lab02S02 | Execução do experimento e coleta de dados | 5 |
| Lab02S03 | Análise das RQ1–RQ3 e dashboard | 5 |
| Relatório Final | Documento final reproduzível | 5 |
| **Total** |  | **20** |

---

# Sprint 1 — Lab02S01

**Objetivo da sprint:** concluir o desenho do experimento e preparar todos os artefatos necessários para que os trials possam ser executados sem decisões metodológicas pendentes.

## S01-01 — Pré-registrar as decisões do experimento [S01]

**Tipo:** Obrigatória

### Objetivo

Preencher e congelar as decisões metodológicas que não foram determinadas diretamente pelo enunciado.

### O que deve ser feito

- Definir linguagem e versão do runtime.
- Definir IDE e extensões permitidas.
- Selecionar o assistente de IA, modelo ou versão, plano e forma de interação.
- Definir as fontes de documentação permitidas no tratamento Manual.
- Definir ferramentas e versões para testes, complexidade, duplicação e LOC.
- Definir a janela de execução dos trials.
- Registrar todas as decisões na metodologia.
- Criar um registro para futuros desvios do protocolo.

### Artefatos envolvidos

- `Docs/methodology.md`
- `Docs/protocol-decisions.md`
- `data/metadata/protocol.json`

### Dependências

- Nenhuma.

### Critérios de aceitação

- [x] Todos os campos pendentes da metodologia estão preenchidos. (linguagem, assistente de IA, IDE, framework de testes e janela de execução fechados em `protocol-decisions.md`)
- [x] Ferramentas e versões estão registradas. (versões congeladas em `protocol-decisions.md`, `methodology.md` e `data/metadata/protocol.json`; a S01-08 deve reproduzir e verificar esse ambiente nas três máquinas)
- [x] Regras dos tratamentos IA e Manual estão inequívocas.
- [x] O protocolo possui data de congelamento. (09/09/2026 — `protocol-decisions.md`)
- [x] Existe local definido para registrar desvios metodológicos. (`protocol-decisions.md`, Seção 3)

### Resultado esperado

Protocolo completo e aprovado pelo grupo antes do primeiro trial.

---

## S01-02 — Selecionar e documentar as seis katas [S01]

**Tipo:** Obrigatória

### Objetivo

Selecionar seis exercícios autorais ou pouco indexados, adequados ao limite de 35 minutos e às métricas previstas.

### O que deve ser feito

- Levantar katas candidatas.
- Verificar se os problemas são reconhecidos pelos participantes.
- Pesquisar trechos distintivos dos enunciados para avaliar indexação pública.
- Aplicar os critérios de inclusão e exclusão da metodologia.
- Definir identificadores K01 a K06.
- Documentar enunciado, entrada, saída, restrições e exemplos.
- Evitar pistas sobre implementação ou tratamento.

### Artefatos envolvidos

- `katas/K01/` a `katas/K06/`
- `Docs/katas.md`

### Dependências

- S01-01.

### Critérios de aceitação

- [x] Exatamente seis katas foram selecionadas. (K01 a K06 documentadas em `Docs/katas.md` e em diretórios próprios)
- [x] Nenhuma kata é previamente conhecida pelos participantes. (declarações negativas de P01, P02 e P03 registradas em `Docs/katas.md` em 10/09/2026)
- [x] Todas podem ser executadas sem rede ou serviço externo. (contratos em memória e suítes locais)
- [x] Todas possuem escopo compatível com o time-box. (inspeção independente de regras, testes, LOC e complexidade registrada em `Docs/katas.md`, Seção 7)
- [x] A baixa indexação ou autoria própria está documentada. (buscas de trechos distintivos repetidas em 10/09/2026)
- [x] Os enunciados passaram por revisão de clareza. (entrada, saída, restrições, exemplos e ausência de pistas revisados em `Docs/katas.md`, Seção 5)

### Resultado esperado

Conjunto de seis objetos experimentais prontos para implementação dos testes.

---

## S01-03 — Formar e validar os pares de dificuldade [S01]

**Tipo:** Obrigatória

### Objetivo

Organizar as seis katas em três blocos de dificuldade equivalente para permitir comparações pareadas.

### O que deve ser feito

- Estimar complexidade das regras e quantidade de casos-limite.
- Produzir soluções de referência protegidas.
- Medir LOC e complexidade das soluções de referência.
- Estimar o tempo de implementação.
- Aplicar a matriz de equivalência definida na metodologia.
- Formar os blocos B1, B2 e B3.
- Documentar diferenças residuais entre as katas pareadas.

### Artefatos envolvidos

- `Docs/kata-equivalence.md`
- `reference-solutions/`
- `data/metadata/kata-equivalence.csv`

### Dependências

- S01-02.

### Critérios de aceitação

- [x] As seis katas estão distribuídas em três pares. (B1 = K01/K02, B2 = K03/K04 e B3 = K05/K06)
- [x] A equivalência foi avaliada com critérios objetivos. (matriz de regras, testes, SLOC, complexidade e tempo em `Docs/kata-equivalence.md`)
- [x] Soluções de referência passam em todos os testes. (33/33 testes passando em 10/09/2026; evidência em `data/metadata/reference-solutions-validation.json`)
- [x] Soluções de referência não ficam acessíveis durante os trials. (fontes ignoradas pelo Git; participantes usam clone limpo sem as referências)
- [x] Limitações do pareamento estão documentadas. (`Docs/kata-equivalence.md`, Seção 4)

### Resultado esperado

Três blocos de dificuldade prontos para a alocação experimental.

---

## S01-04 — Implementar os testes automatizados de aceitação [S01]

**Tipo:** Obrigatória

### Objetivo

Criar suítes determinísticas capazes de medir a qualidade funcional das soluções finais.

### O que deve ser feito

- Implementar casos usuais, limites e entradas inválidas quando aplicável.
- Padronizar a forma de executar os testes em todas as katas.
- Garantir contagem estável de testes passando e falhando.
- Validar que o esqueleto inicial falha pelo motivo esperado.
- Validar que a solução de referência passa integralmente.
- Impedir que testes sejam alterados durante o trial.
- Documentar o comando de execução.

### Artefatos envolvidos

- `katas/K01/tests/` a `katas/K06/tests/`
- arquivos de configuração do framework de testes
- `scripts/run_tests.*`

### Dependências

- S01-02.

### Critérios de aceitação

- [x] Todas as katas possuem testes automatizados. (`katas/K01/tests/` a `katas/K06/tests/`)
- [x] As suítes são determinísticas em execuções repetidas. (funções puras, sem aleatoriedade nem I/O externo; reexecutadas em bash e PowerShell com o mesmo resultado)
- [x] O esqueleto inicial não passa indevidamente. (todas falham com `NotImplementedError`, não erro de import/sintaxe)
- [x] As soluções de referência atingem 100% de sucesso. (validado localmente via `run_tests.py --src`; soluções não commitadas — ver nota de custódia abaixo)
- [x] O resultado informa total, testes passando e testes falhando. (`scripts/run_tests.py` imprime os três a partir do relatório JUnit)
- [x] Os mesmos comandos funcionam em todos os ambientes previstos. (mesmo comando validado em bash e PowerShell)

### Resultado esperado

Suítes de aceitação confiáveis para medir RQ1 e RQ2.

---

## S01-05 — Implementar o cronômetro e o coletor de trials [S01]

**Tipo:** Obrigatória

### Objetivo

Automatizar o início, encerramento e registro dos trials, reduzindo erros de medição manual.

### O que deve ser feito

- Registrar início e fim com data, hora e fuso.
- Medir duração em segundos.
- Encerrar o trial quando todos os testes passarem ou aos 2.100 segundos.
- Marcar trials incompletos como censurados.
- Executar uma verificação final da suíte.
- Registrar totais de testes passando e falhando.
- Gerar identificador único para cada trial.
- Preservar logs sem sobrescrita.
- Tratar encerramento inesperado com mensagem clara.

### Artefatos envolvidos

- `scripts/run_trial.*`
- `src/collection/`
- `tests/`
- `data/raw/`

### Dependências

- S01-01.
- S01-04.

### Critérios de aceitação

- [x] O cronômetro utiliza segundos e respeita o limite de 35 minutos. (`TIME_LIMIT_SECONDS = 2100` em `src/collection/trial_collector.py`)
- [x] Sucesso encerra a medição na primeira execução completamente verde. (`run_trial` para no primeiro `poll` sem falhas; `test_run_trial_encerra_no_sucesso_na_primeira_execucao_verde`)
- [x] Falha no limite produz `duration_seconds = 2100` e `censored = true`. (`test_run_trial_censura_produz_exatamente_2100_segundos_por_padrao`)
- [x] O log contém horários, duração e resultado final dos testes. (`trial.json`: `started_at`/`finished_at` com fuso, `duration_seconds`, `attempts` e totais de testes)
- [x] Trials existentes não são sobrescritos. (`collect_trial` recusa diretório de trial já existente, inclusive após incidente; `test_collect_trial_grava_registro_de_sucesso_e_nao_sobrescreve`)
- [x] Testes automatizados cobrem sucesso, censura e falha inesperada. (`tests/test_trial_collector.py`, 12 casos)

### Resultado esperado

Comando padronizado para executar e registrar qualquer trial do experimento. (`scripts/run_trial.py`)

---

## S01-06 — Implementar a coleta das métricas estáticas [S01]

**Tipo:** Obrigatória

### Objetivo

Automatizar a medição uniforme de complexidade, duplicação, LOC e manutenibilidade do código final.

### O que deve ser feito

- Configurar a ferramenta de complexidade ciclomática.
- Configurar a ferramenta de duplicação e seu limiar.
- Configurar a medição de LOC.
- Configurar o Índice de Manutenibilidade, quando disponível.
- Excluir testes, dependências, código gerado e arquivos de configuração.
- Gerar saída bruta legível por máquina.
- Consolidar as métricas por trial.
- Documentar comandos e versões.

### Artefatos envolvidos

- `scripts/collect_static_metrics.*`
- arquivos de configuração das ferramentas
- `src/metrics/`
- `tests/`
- `data/raw/metrics/`

### Dependências

- S01-01.
- S01-02.

### Critérios de aceitação

- [x] Complexidade é coletada por função ou método. (`radon cc --json`, com lista detalhada no consolidado)
- [x] Média, máximo e quantidade de funções são preservados. (`complexity` em `metrics.json`)
- [x] Duplicação informa linhas e percentual duplicado. (relatório JSON do JSCPD e seção `duplication` consolidada)
- [x] LOC é coletada obrigatoriamente. (SLOC do `radon raw`, com linhas físicas, lógicas, comentários e brancas preservadas)
- [x] Arquivos fora do código de produção são excluídos. (descoberta restrita a `.py` e exclusões testadas automaticamente)
- [x] A configuração é idêntica para todos os trials. (versões, `.jscpd.json`, `radon.cfg` e hashes registrados)
- [x] As soluções de referência foram usadas em um teste de sanidade. (K01–K06 coletadas em 10/09/2026; resumo em `data/metadata/static-metrics-sanity.json`)

### Resultado esperado

Pipeline reproduzível para coletar as métricas da RQ3.

---

## S01-07 — Implementar a alocação contrabalanceada [S01]

**Tipo:** Obrigatória

### Objetivo

Gerar a ordem das katas e tratamentos sem escolha manual influenciada por preferência ou dificuldade percebida.

### O que deve ser feito

- Implementar sorteio com semente fixa.
- Aplicar as sequências previstas na metodologia.
- Garantir três trials com IA e três manuais por participante.
- Garantir os dois tratamentos em cada bloco de dificuldade.
- Evitar katas do mesmo par em posições consecutivas.
- Garantir que cada kata apareça nos dois tratamentos no conjunto do grupo.
- Exportar a alocação para arquivo versionado.
- Validar automaticamente todas as restrições.

### Artefatos envolvidos

- `scripts/generate_allocation.*`
- `tests/`
- `data/metadata/allocation.csv`

### Dependências

- S01-03.

### Critérios de aceitação

- [x] A mesma semente reproduz a mesma alocação. (semente `20260910`, verificada automaticamente)
- [x] Cada participante possui seis posições e dois tratamentos. (três trials `ai` e três `manual` por participante)
- [x] Todas as restrições metodológicas são verificadas por teste. (`tests/test_allocation.py`)
- [x] A distribuição desigual inevitável entre tratamentos está documentada. (`methodology.md`, Seção 8.2)
- [x] A alocação foi congelada antes da execução. (`allocation-metadata.json`, estado `frozen` em 10/09/2026)

### Resultado esperado

Plano contrabalanceado e auditável para os 18 trials.

---

## S01-08 — Preparar o ambiente reproduzível [S01]

**Tipo:** Obrigatória

### Objetivo

Garantir que todos os participantes executem as tarefas com a mesma base técnica.

### O que deve ser feito

- Criar arquivo de dependências com versões fixadas.
- Criar comando de instalação e verificação do ambiente.
- Registrar sistema operacional, hardware, runtime, IDE e extensões.
- Preparar diretório limpo para cada trial.
- Automatizar restauração do esqueleto inicial.
- Verificar habilitação ou desabilitação da IA conforme o tratamento.
- Criar uma kata de treinamento fora da amostra.
- Documentar o procedimento operacional.

### Artefatos envolvidos

- arquivo de dependências e bloqueio
- `scripts/setup.*`
- `scripts/prepare_trial.*`
- `training-kata/`
- `Docs/execution-guide.md`
- `data/metadata/environment.json`

### Dependências

- S01-01.
- S01-04.
- S01-05.
- S01-06.

### Critérios de aceitação

- [ ] O ambiente pode ser instalado a partir do zero.
- [ ] Todas as versões relevantes estão registradas.
- [ ] O diretório de um trial pode ser restaurado sem resíduos.
- [ ] A kata de treinamento não reutiliza problemas experimentais.
- [ ] Testes e métricas executam por comandos documentados.

### Resultado esperado

Ambiente padronizado, testado e pronto para a coleta oficial.

---

## S01-09 — Configurar o Kanban e revisar a prontidão [S01]

**Tipo:** Obrigatória

### Objetivo

Registrar o planejamento no GitHub Projects e impedir o início da coleta com preparação incompleta.

### O que deve ser feito

- Criar as Issues da S01.
- Criar previamente as Issues individuais dos 18 trials.
- Adicionar labels para sprint, RQ, kata e tratamento.
- Configurar campos de status e iteração.
- Confirmar o limite de WIP.
- Executar checklist de prontidão.
- Registrar aprovação do protocolo.
- Exportar o snapshot de fechamento da sprint, quando aplicável ao processo do grupo.

### Artefatos envolvidos

- GitHub Projects
- `Docs/readiness-checklist.md`
- `data/project-snapshots/`

### Dependências

- S01-01 a S01-08.

### Critérios de aceitação

- [ ] Todas as tarefas da sprint existem como Issues.
- [ ] Os 18 trials possuem Issues individuais.
- [ ] Labels e iteração estão consistentes.
- [ ] Nenhum item obrigatório do checklist está pendente.
- [ ] A contribuição individual planejada atende à regra do enunciado.
- [ ] O protocolo foi aprovado antes de qualquer trial válido.

### Resultado esperado

Sprint encerrada com board atualizado e autorização interna para iniciar a execução.

---

# Sprint 2 — Lab02S02

**Objetivo da sprint:** executar os 18 trials conforme a alocação congelada, preservar o código final de cada tentativa e consolidar os dados brutos sem alterar o protocolo.

## S02-01 — Realizar treinamento e validar a operação [S02]

**Tipo:** Obrigatória

### Objetivo

Familiarizar todos os participantes com as regras e ferramentas sem utilizar nenhuma kata experimental.

### O que deve ser feito

- Executar a kata de treinamento nos dois modos.
- Praticar início, testes e encerramento pelo coletor.
- Confirmar como habilitar e desabilitar a IA.
- Confirmar fontes permitidas no tratamento Manual.
- Simular sucesso e censura.
- Corrigir somente falhas operacionais, sem alterar hipóteses ou métricas após observar trials válidos.

### Artefatos envolvidos

- `training-kata/`
- `data/training/`
- `Docs/execution-guide.md`

### Dependências

- S01-09.

### Critérios de aceitação

- [ ] Todos os participantes concluíram o treinamento.
- [ ] Dados de treinamento estão separados dos dados oficiais.
- [ ] O cronômetro e as ferramentas funcionaram de ponta a ponta.
- [ ] Dúvidas operacionais foram resolvidas antes da coleta.

### Resultado esperado

Participantes preparados para aplicar o protocolo de forma uniforme.

---

## S02-02 — Executar os trials do bloco B1 [S02]

**Tipo:** Obrigatória

### Objetivo

Executar todas as combinações previstas para o primeiro par de dificuldade.

### O que deve ser feito

- Consultar a alocação congelada.
- Executar K01 e K02 para os três participantes nos tratamentos indicados.
- Respeitar ordem, pausas e limite de tempo.
- Preservar código, testes finais, métricas e incidentes.
- Registrar prompts quando aplicável.
- Commitar cada trial mencionando sua Issue individual.

### Artefatos envolvidos

- `trials/`
- `data/raw/trials/`
- `data/raw/metrics/`
- GitHub Projects

### Dependências

- S02-01.

### Critérios de aceitação

- [ ] Os seis trials de B1 foram executados.
- [ ] Cada trial possui código final e dados brutos.
- [ ] Trials censurados foram mantidos em 2.100 segundos.
- [ ] Incidentes e desvios foram registrados.
- [ ] Cada commit referencia a Issue correta.

### Resultado esperado

Bloco B1 completo, rastreável e pronto para validação.

---

## S02-03 — Executar os trials do bloco B2 [S02]

**Tipo:** Obrigatória

### Objetivo

Executar todas as combinações previstas para o segundo par de dificuldade.

### O que deve ser feito

- Consultar a alocação congelada.
- Executar K03 e K04 para os três participantes nos tratamentos indicados.
- Respeitar ordem, pausas e limite de tempo.
- Preservar código, testes finais, métricas e incidentes.
- Registrar prompts quando aplicável.
- Commitar cada trial mencionando sua Issue individual.

### Artefatos envolvidos

- `trials/`
- `data/raw/trials/`
- `data/raw/metrics/`
- GitHub Projects

### Dependências

- S02-01.

### Critérios de aceitação

- [ ] Os seis trials de B2 foram executados.
- [ ] Cada trial possui código final e dados brutos.
- [ ] Trials censurados foram mantidos em 2.100 segundos.
- [ ] Incidentes e desvios foram registrados.
- [ ] Cada commit referencia a Issue correta.

### Resultado esperado

Bloco B2 completo, rastreável e pronto para validação.

---

## S02-04 — Executar os trials do bloco B3 [S02]

**Tipo:** Obrigatória

### Objetivo

Executar todas as combinações previstas para o terceiro par de dificuldade.

### O que deve ser feito

- Consultar a alocação congelada.
- Executar K05 e K06 para os três participantes nos tratamentos indicados.
- Respeitar ordem, pausas e limite de tempo.
- Preservar código, testes finais, métricas e incidentes.
- Registrar prompts quando aplicável.
- Commitar cada trial mencionando sua Issue individual.

### Artefatos envolvidos

- `trials/`
- `data/raw/trials/`
- `data/raw/metrics/`
- GitHub Projects

### Dependências

- S02-01.

### Critérios de aceitação

- [ ] Os seis trials de B3 foram executados.
- [ ] Cada trial possui código final e dados brutos.
- [ ] Trials censurados foram mantidos em 2.100 segundos.
- [ ] Incidentes e desvios foram registrados.
- [ ] Cada commit referencia a Issue correta.

### Resultado esperado

Bloco B3 completo, rastreável e pronto para validação.

---

## S02-05 — Consolidar o dataset dos trials [S02]

**Tipo:** Obrigatória

### Objetivo

Transformar os registros brutos dos 18 trials em um dataset único, sem perder a ligação com as evidências originais.

### O que deve ser feito

- Ler logs, resultados de testes e métricas estáticas.
- Gerar uma linha por trial.
- Calcular taxa de sucesso.
- Consolidar complexidade média e máxima.
- Consolidar duplicação, LOC e manutenibilidade.
- Associar bloco, ordem, tratamento, Issue e commit.
- Preservar valores ausentes como ausentes.
- Gerar relatório de erros de consolidação.

### Artefatos envolvidos

- `src/processing/`
- `scripts/build_dataset.*`
- `tests/`
- `data/processed/trials.csv`

### Dependências

- S02-02.
- S02-03.
- S02-04.

### Critérios de aceitação

- [ ] O dataset possui exatamente 18 linhas e `trial_id` único.
- [ ] Todas as colunas mínimas da metodologia estão presentes.
- [ ] Os valores derivam de fontes brutas rastreáveis.
- [ ] Dados censurados e ausentes foram tratados corretamente.
- [ ] O processamento pode ser reexecutado sem edição manual.
- [ ] Testes automatizados cobrem as principais regras de consolidação.

### Resultado esperado

Dataset processado inicial, pronto para validação na Sprint 3.

---

## S02-06 — Auditar a execução e encerrar a sprint [S02]

**Tipo:** Obrigatória

### Objetivo

Verificar completude e rastreabilidade da coleta antes de iniciar a análise dos resultados.

### O que deve ser feito

- Conferir os 18 trials contra a alocação.
- Conferir código, logs, testes e métricas de cada trial.
- Classificar incidentes e desvios como menores, maiores ou falhas de infraestrutura.
- Confirmar vínculo entre Issue, trial e commit.
- Verificar contribuição individual exigida pelo enunciado.
- Atualizar o GitHub Projects.
- Exportar o snapshot de fechamento da sprint, quando aplicável.

### Artefatos envolvidos

- `Docs/execution-audit.md`
- `data/project-snapshots/`
- GitHub Projects

### Dependências

- S02-05.

### Critérios de aceitação

- [ ] Os 18 trials foram confrontados com a alocação.
- [ ] Toda ausência ou divergência possui justificativa.
- [ ] Desvios foram classificados antes da análise estatística.
- [ ] Issues e commits estão vinculados corretamente.
- [ ] O board representa o estado real da sprint.

### Resultado esperado

Coleta encerrada, auditada e liberada para análise.

---

# Sprint 3 — Lab02S03

**Objetivo da sprint:** validar os dados, responder às três questões de pesquisa e construir o dashboard de visualização sem modificar as decisões após observar resultados favoráveis ou desfavoráveis.

## S03-01 — Implementar e executar a validação do dataset [S03]

**Tipo:** Obrigatória

### Objetivo

Verificar integridade, consistência e completude do dataset oficial antes da análise.

### O que deve ser feito

- Implementar todas as regras da Seção 13 da metodologia.
- Conferir cardinalidade, identificadores e equilíbrio dos tratamentos.
- Validar duração, censura, testes e taxas.
- Validar métricas estruturais não negativas.
- Conferir Issue e commit de cada trial.
- Comparar amostra do dataset com as saídas brutas.
- Identificar outliers sem removê-los automaticamente.
- Gerar relatório de validação.

### Artefatos envolvidos

- `src/validation/`
- `tests/`
- `reports/drafts/data-validation.md`

### Dependências

- S02-06.

### Critérios de aceitação

- [ ] Todas as regras de integridade são automatizadas.
- [ ] Erros críticos interrompem a análise.
- [ ] Outliers legítimos são mantidos.
- [ ] Correções possuem registro de auditoria.
- [ ] O relatório informa pares válidos e dados ausentes.

### Resultado esperado

Dataset validado e autorizado para as análises das RQs.

---

## S03-02 — Analisar tempo e conclusão da RQ1 [S03]

**Tipo:** Obrigatória

### Objetivo

Comparar o tempo de resolução entre os tratamentos, preservando os trials censurados.

### O que deve ser feito

- Calcular estatísticas descritivas por tratamento.
- Reportar mediana, quartis, IQR, mínimo e máximo.
- Identificar trials concluídos e censurados.
- Formar diferenças pareadas por participante e bloco.
- Aplicar o teste de Wilcoxon unilateral previsto.
- Calcular tamanho de efeito quando possível.
- Executar a análise de sensibilidade da censura.
- Gerar tabelas e gráficos preliminares.

### Artefatos envolvidos

- `src/analysis/rq1_time.*`
- `tests/`
- `reports/drafts/rq1-analysis.md`
- `reports/figures/rq1/`

### Dependências

- S03-01.

### Critérios de aceitação

- [ ] Trials censurados permanecem com 2.100 segundos.
- [ ] A análise usa mediana e IQR como medidas principais.
- [ ] O pareamento segue participante e bloco.
- [ ] Wilcoxon, tamanho de efeito e pares válidos estão registrados.
- [ ] A resposta não depende apenas do valor de `p`.
- [ ] Limitações da censura e da amostra estão explícitas.

### Resultado esperado

Evidências quantitativas e resposta preliminar para a RQ1.

---

## S03-03 — Analisar defeitos e taxa de sucesso da RQ2 [S03]

**Tipo:** Obrigatória

### Objetivo

Comparar a qualidade funcional final entre os tratamentos.

### O que deve ser feito

- Calcular taxa de sucesso por trial.
- Resumir taxa de sucesso por tratamento.
- Reportar testes falhando como métrica complementar.
- Formar diferenças pareadas por participante e bloco.
- Aplicar o teste de Wilcoxon unilateral previsto.
- Calcular tamanho de efeito quando possível.
- Comparar quantidade de trials completamente verdes.
- Gerar tabelas e gráficos preliminares.

### Artefatos envolvidos

- `src/analysis/rq2_defects.*`
- `tests/`
- `reports/drafts/rq2-analysis.md`
- `reports/figures/rq2/`

### Dependências

- S03-01.

### Critérios de aceitação

- [ ] A taxa usa `passed_tests / total_tests × 100`.
- [ ] Diferenças na quantidade de testes entre katas são consideradas.
- [ ] Testes falhando não substituem a métrica primária.
- [ ] O pareamento e o teste estatístico seguem a metodologia.
- [ ] Resultados completos e incompletos estão visíveis.
- [ ] Limitações dos testes como proxy de defeitos estão documentadas.

### Resultado esperado

Evidências quantitativas e resposta preliminar para a RQ2.

---

## S03-04 — Analisar qualidade estrutural da RQ3 [S03]

**Tipo:** Obrigatória

### Objetivo

Comparar complexidade ciclomática e duplicação entre os tratamentos, controlando o tamanho do código.

### O que deve ser feito

- Resumir complexidade média por tratamento.
- Resumir duplicação por tratamento.
- Reportar LOC ao lado de todas as comparações estruturais.
- Formar diferenças pareadas por participante e bloco.
- Aplicar os testes de Wilcoxon bilaterais.
- Ajustar os valores de `p` da RQ3 pelo método de Holm.
- Calcular tamanhos de efeito quando possível.
- Explorar Índice de Manutenibilidade sem transformá-lo em métrica principal.
- Gerar tabelas e gráficos preliminares.

### Artefatos envolvidos

- `src/analysis/rq3_structure.*`
- `tests/`
- `reports/drafts/rq3-analysis.md`
- `reports/figures/rq3/`

### Dependências

- S03-01.

### Critérios de aceitação

- [ ] Complexidade, duplicação e LOC são apresentadas em conjunto.
- [ ] Código de teste e dependências não entram nas métricas.
- [ ] Os testes da RQ3 são bilaterais.
- [ ] A correção de Holm foi aplicada e documentada.
- [ ] Valores ausentes não foram convertidos artificialmente em zero.
- [ ] A interpretação considera verbosidade e tamanho do código.

### Resultado esperado

Evidências quantitativas e resposta preliminar para a RQ3.

---

## S03-05 — Consolidar a análise estatística [S03]

**Tipo:** Obrigatória

### Objetivo

Produzir uma saída única, reproduzível e coerente para todas as RQs.

### O que deve ser feito

- Integrar as análises de RQ1, RQ2 e RQ3.
- Padronizar tabelas, arredondamento e nomenclatura.
- Apresentar resultados agregados e individuais.
- Registrar quantidade de pares, empates e ausências.
- Consolidar valores de `p`, tamanhos de efeito e intervalos exploratórios.
- Verificar risco de pseudorreplicação.
- Gerar arquivo tabular para alimentar o dashboard.
- Redigir respostas objetivas às RQs.

### Artefatos envolvidos

- `scripts/run_analysis.*`
- `src/analysis/`
- `data/processed/statistical-results.csv`
- `reports/drafts/rq-answers.md`

### Dependências

- S03-02.
- S03-03.
- S03-04.

### Critérios de aceitação

- [ ] Um único comando reproduz todas as análises.
- [ ] Resultados não dependem de edição manual.
- [ ] Estatísticas descritivas e inferenciais são coerentes.
- [ ] Resultados por participante estão disponíveis.
- [ ] As três RQs possuem resposta preliminar sustentada pelos dados.
- [ ] Conclusões respeitam o tamanho reduzido da amostra.

### Resultado esperado

Análise estatística consolidada, pronta para visualização e relatório.

---

## S03-06 — Construir o dashboard de visualização [S03]

**Tipo:** Obrigatória

### Objetivo

Criar gráficos reproduzíveis para comparar tempo, sucesso e métricas estáticas entre os tratamentos.

### O que deve ser feito

- Carregar apenas datasets validados.
- Criar visão geral dos 18 trials.
- Mostrar tempo por tratamento com censura identificada.
- Criar gráfico pareado por participante e bloco.
- Mostrar taxa de sucesso e conclusão.
- Mostrar complexidade, duplicação e LOC.
- Exibir todos os pontos sempre que possível.
- Evitar gráficos baseados apenas em médias.
- Permitir exportação das figuras ou dados subjacentes.
- Documentar o comando de geração ou execução.

### Artefatos envolvidos

- `src/dashboard/` ou `notebooks/dashboard.ipynb`
- `tests/`
- `reports/figures/`
- `Docs/execution-guide.md`

### Dependências

- S03-05.

### Critérios de aceitação

- [ ] RQ1, RQ2 e RQ3 possuem visualizações identificadas.
- [ ] Trials censurados são distinguíveis.
- [ ] Comparações pareadas são visualmente verificáveis.
- [ ] LOC acompanha a leitura das métricas estruturais.
- [ ] Os 18 pontos não são ocultados por agregações indevidas.
- [ ] Gráficos podem ser reproduzidos a partir do dataset oficial.
- [ ] Arquivos possuem título, eixos, unidade, legenda e fonte.

### Resultado esperado

Dashboard reproduzível e figuras prontas para o Relatório Final.

---

## S03-07 — Revisar ameaças à validade e desvios [S03]

**Tipo:** Obrigatória

### Objetivo

Interpretar os resultados considerando limitações reais observadas durante o experimento.

### O que deve ser feito

- Revisar incidentes e desvios registrados na S02.
- Avaliar aprendizado, fadiga e transferência entre katas.
- Avaliar familiaridade com IA e contaminação do tratamento Manual.
- Discutir equivalência dos pares de katas.
- Verificar sinais de memorização ou reprodução de solução conhecida.
- Avaliar efeito do tamanho da amostra e pseudorreplicação.
- Distinguir validade interna, de construção, externa e de conclusão.
- Relacionar limitações às respostas das RQs.

### Artefatos envolvidos

- `reports/drafts/validity-threats.md`
- `Docs/methodology.md`
- registros de incidentes e desvios

### Dependências

- S02-06.
- S03-05.

### Critérios de aceitação

- [ ] Todos os desvios possuem impacto discutido.
- [ ] Ameaças não são apresentadas apenas de forma genérica.
- [ ] A interpretação considera a direção potencial de cada viés.
- [ ] Limitações de generalização estão explícitas.
- [ ] Nenhuma limitação é usada para ocultar resultado desfavorável.

### Resultado esperado

Discussão de validade específica para o experimento executado.

---

## S03-08 — Encerrar a sprint e preparar os resultados para o relatório [S03]

**Tipo:** Obrigatória

### Objetivo

Revisar a cobertura das entregas, organizar os artefatos finais da análise e atualizar o GitHub Projects.

### O que deve ser feito

- Conferir cobertura de RQ1, RQ2 e RQ3.
- Revisar scripts, testes, tabelas e gráficos.
- Verificar que o dashboard usa o dataset validado.
- Confirmar contribuição individual por código na sprint.
- Atualizar status e evidências das Issues.
- Exportar snapshot de fechamento, quando aplicável.
- Criar checklist de insumos para o Relatório Final.

### Artefatos envolvidos

- `Docs/s03-checklist.md`
- `data/project-snapshots/`
- GitHub Projects

### Dependências

- S03-06.
- S03-07.

### Critérios de aceitação

- [ ] As três RQs possuem análise, gráfico e discussão preliminar.
- [ ] Todos os scripts necessários estão versionados.
- [ ] O dashboard foi testado com os dados oficiais.
- [ ] O requisito de contribuição individual foi verificado.
- [ ] O board representa o estado real da sprint.
- [ ] Os insumos do relatório estão identificados.

### Resultado esperado

Sprint 3 encerrada com resultados validados e organizados para redação final.

---

# Relatório Final

## RF-01 — Elaborar o Relatório Final do Lab02

**Tipo:** Obrigatória

### Objetivo

Consolidar desenho, execução, resultados e discussão em um documento reproduzível.

### O que deve ser feito

- Redigir introdução e contextualização.
- Apresentar hipóteses nulas e alternativas.
- Descrever participantes, katas, ambiente e tratamentos.
- Informar assistente de IA, modelo ou versão e data de acesso.
- Explicar alocação, contrabalanceamento e time-box.
- Apresentar métodos de coleta e análise.
- Responder separadamente RQ1, RQ2 e RQ3.
- Inserir tabelas e gráficos do dashboard.
- Discutir tamanhos de efeito, incerteza e ameaças à validade.
- Incluir o link do repositório e do GitHub Projects.
- Referenciar scripts, dataset e demais artefatos necessários à replicação.

### Artefatos envolvidos

- `reports/final/relatorio-final.md`
- `reports/final/figures/`
- `Docs/methodology.md`

### Dependências

- S03-08.

### Critérios de aceitação

- [ ] O relatório contém introdução, metodologia, resultados e discussão.
- [ ] Hipóteses e métricas correspondem ao protocolo pré-registrado.
- [ ] As três RQs são respondidas com evidências quantitativas.
- [ ] Trials censurados e desvios estão explícitos.
- [ ] Ferramentas e versões permitem replicação.
- [ ] Tabelas e gráficos são legíveis e rastreáveis.
- [ ] O link do repositório/GitHub Projects está preenchido.

### Resultado esperado

Primeira versão completa do documento final.

---

## RF-02 — Revisar consistência e reprodutibilidade da entrega

**Tipo:** Obrigatória

### Objetivo

Verificar se o relatório pode ser conferido a partir do repositório e se não há divergências entre texto, dados e código.

### O que deve ser feito

- Reexecutar validação, análise e geração dos gráficos em ambiente limpo.
- Comparar números do relatório com as saídas dos scripts.
- Conferir referências a tabelas, figuras e arquivos.
- Revisar hipóteses, terminologia e unidades.
- Conferir anonimização nos dados e identificação no board.
- Revisar ortografia e formatação.
- Verificar links e comandos documentados.
- Registrar pendências em checklist.

### Artefatos envolvidos

- `Docs/final-review-checklist.md`
- `reports/final/relatorio-final.md`
- scripts e datasets oficiais

### Dependências

- RF-01.

### Critérios de aceitação

- [ ] Pipeline final executa sem intervenção manual indevida.
- [ ] Valores do relatório coincidem com os artefatos gerados.
- [ ] Links e referências funcionam.
- [ ] Não existem campos `<preencher>` no documento final.
- [ ] Não existem contradições entre metodologia e execução.
- [ ] Todas as pendências do checklist foram resolvidas.

### Resultado esperado

Relatório revisado e entrega tecnicamente reproduzível.

---

## RF-03 — Fechar o GitHub Projects e preparar a entrega

**Tipo:** Obrigatória

### Objetivo

Concluir a rastreabilidade do laboratório e disponibilizar os artefatos finais para correção.

### O que deve ser feito

- Conferir Assignee, sprint e status de todas as Issues.
- Confirmar referências de Issues nos commits.
- Mover apenas tarefas realmente concluídas para Done.
- Verificar respeito aos limites de WIP durante o processo.
- Atualizar o link do repositório/GitHub Projects no relatório.
- Exportar o snapshot final do board, quando aplicável.
- Criar tag ou release da versão entregue, se adotado pelo grupo.
- Conferir acesso do professor aos recursos necessários.

### Artefatos envolvidos

- GitHub Projects
- `data/project-snapshots/`
- `reports/final/relatorio-final.md`

### Dependências

- RF-02.

### Critérios de aceitação

- [ ] Todas as Issues possuem estado e metadados corretos.
- [ ] Cada trial mantém a cadeia `Issue → commit → dados → análise`.
- [ ] O board representa o trabalho realmente realizado.
- [ ] O relatório final está acessível no repositório.
- [ ] Links de entrega foram verificados.
- [ ] A versão final foi identificada de forma inequívoca.

### Resultado esperado

Lab02 finalizado, rastreável e pronto para avaliação.

---

## Ordem resumida de execução

1. **S01:** congelar protocolo → selecionar e parear katas → implementar testes → implementar coleta e métricas → gerar alocação → preparar ambiente → revisar prontidão.
2. **S02:** realizar treinamento → executar B1, B2 e B3 → consolidar dataset → auditar coleta.
3. **S03:** validar dataset → analisar RQ1, RQ2 e RQ3 → consolidar estatística → gerar dashboard → revisar validade → fechar sprint.
4. **Relatório Final:** redigir → revisar e reproduzir → fechar board e entrega.
