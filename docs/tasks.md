# Tasks do Projeto

Este documento organiza o plano de execução das tarefas. As tarefas listadas aqui serão convertidas posteriormente em **Issues reais** no GitHub Projects, com responsável atribuído.

## Organização do Grupo

| Integrante | Responsabilidade |
|---|---|
| Integrante A | RQ01 + RQ02 |
| Integrante B | RQ03 + RQ04 |
| Integrante C | RQ05 + RQ06 |

A RQ07 será desenvolvida posteriormente através da integração dos resultados das demais RQs.

## Regras de Rastreabilidade

- Cada task deve virar uma Issue própria no GitHub Projects.
- Cada sprint deve conter ao menos uma Issue/commit de cada integrante (A, B e C).
- Todo commit deve referenciar o número da Issue correspondente (ex.: `#123`).

---

# Sprint 1 — Lab01S01

## S01-01 — Implementar RQ01 e RQ02
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Implementar as métricas de idade de repositório (RQ01) e pull requests aceitas (RQ02).

### O que deve ser feito
- Definir funções de cálculo das métricas.
- Integrar leitura dos campos necessários do dataset bruto.
- Produzir saída inicial das duas métricas para amostra piloto.

### Arquivos/módulos envolvidos
- `src/metrics/`
- `src/analysis/`

### Dependências
- S01-04 (consulta GraphQL integrada)

### Critérios de aceitação
- [ ] Métrica de RQ01 implementada e validada para amostra piloto.
- [ ] Métrica de RQ02 implementada e validada para amostra piloto.
- [ ] Saída gerada sem erros para os registros de teste.

### Resultado esperado
Métricas de RQ01 e RQ02 disponíveis no pipeline para uso nas sprints seguintes.

---

## S01-02 — Implementar RQ03 e RQ04
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Implementar as métricas de número de releases (RQ03) e frequência de atualização (RQ04).

### O que deve ser feito
- Definir cálculo da contagem de releases por repositório.
- Definir cálculo da frequência de atualização.
- Gerar saída piloto das duas métricas.

### Arquivos/módulos envolvidos
- `src/metrics/`
- `src/analysis/`

### Dependências
- S01-04 (consulta GraphQL integrada)

### Critérios de aceitação
- [ ] Métrica de RQ03 implementada.
- [ ] Métrica de RQ04 implementada.
- [ ] Resultados de teste disponíveis para revisão interna.

### Resultado esperado
Métricas de RQ03 e RQ04 prontas para validação na base completa.

---

## S01-03 — Implementar RQ05 e RQ06
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Implementar as métricas de linguagem primária (RQ05) e percentual de issues fechadas (RQ06).

### O que deve ser feito
- Consolidar campo de linguagem primária por repositório.
- Implementar cálculo de percentual de issues fechadas.
- Produzir dataset piloto para conferência.

### Arquivos/módulos envolvidos
- `src/metrics/`
- `src/analysis/`

### Dependências
- S01-04 (consulta GraphQL integrada)

### Critérios de aceitação
- [ ] Métrica de RQ05 implementada.
- [ ] Métrica de RQ06 implementada.
- [ ] Cálculo de percentual validado com casos de teste.

### Resultado esperado
Métricas de RQ05 e RQ06 prontas para integração no pipeline.

---

## S01-04 — Integrar consulta GraphQL
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Centralizar e integrar a consulta GraphQL com todos os campos necessários às RQ01–RQ06 e base para RQ07.

### O que deve ser feito
- Definir consulta base com paginação e campos obrigatórios.
- Integrar autenticação por token.
- Garantir retorno em formato consumível pelo coletor.

### Arquivos/módulos envolvidos
- `src/github/`
- `src/collectors/`

### Dependências
- Nenhuma

### Critérios de aceitação
- [ ] Consulta retorna os campos mínimos para as RQs.
- [ ] Integração executa sem erro em amostra de páginas.
- [ ] Estrutura de resposta documentada para uso interno.

### Resultado esperado
Camada de coleta GraphQL pronta para alimentar as métricas.

---

## S01-05 — Configurar GitHub Projects
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Configurar o board do projeto para rastrear tarefas por sprint com responsáveis e status.

### O que deve ser feito
- Criar colunas/status do fluxo de trabalho.
- Criar Issues iniciais da Sprint 1.
- Atribuir responsáveis e labels por RQ/sprint.

### Arquivos/módulos envolvidos
- Sem módulo de código (gestão no GitHub Projects)

### Dependências
- Nenhuma

### Critérios de aceitação
- [ ] Board criado e acessível ao grupo.
- [ ] Todas as tasks obrigatórias da sprint criadas como Issues.
- [ ] Responsáveis atribuídos em cada Issue.

### Resultado esperado
Kanban operacional com rastreabilidade por Issue.

---

## S01-06 — Tratamento de erros da API
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Adicionar tratamento robusto para falhas de requisição, autenticação e limites da API.

### O que deve ser feito
- Tratar respostas de erro da API.
- Implementar retentativas para falhas transitórias.
- Registrar falhas em logs para auditoria.

### Arquivos/módulos envolvidos
- `src/github/`
- `src/collectors/`

### Dependências
- S01-04

### Critérios de aceitação
- [ ] Falhas transitórias não interrompem a coleta imediatamente.
- [ ] Erros fatais são reportados com mensagem clara.
- [ ] Logs de erro ficam registrados para inspeção.

### Resultado esperado
Coleta mais resiliente a instabilidades e limites da API.

---

# Sprint 2 — Lab01S02

## S02-01 — Implementar paginação GraphQL
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Garantir coleta completa e consistente dos 1.000 repositórios usando cursores GraphQL.

### O que deve ser feito
- Implementar loop paginado com `endCursor`/`hasNextPage`.
- Encerrar coleta ao atingir 1.000 válidos.
- Registrar progresso por página.

### Arquivos/módulos envolvidos
- `src/collectors/`
- `src/github/`

### Dependências
- S01-04
- S01-06

### Critérios de aceitação
- [ ] Coleta alcança exatamente 1.000 repositórios.
- [ ] Paginação funciona sem duplicações.
- [ ] Progresso de páginas registrado em log.

### Resultado esperado
Pipeline de coleta completo para amostra oficial.

---

## S02-02 — Implementar exportação CSV
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Exportar dados coletados e métricas para arquivos CSV padronizados.

### O que deve ser feito
- Definir schema de colunas.
- Implementar escrita de CSV para bruto e processado.
- Validar codificação e separador adotado.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `data/raw/`
- `data/processed/`

### Dependências
- S02-01

### Critérios de aceitação
- [ ] CSV bruto gerado após coleta.
- [ ] CSV processado gerado após métricas.
- [ ] Arquivos legíveis e consistentes.

### Resultado esperado
Dados exportados para análise e relatório.

---

## S02-03 — Implementar pipeline de processamento
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Consolidar fluxo de transformação dos dados brutos em métricas processadas.

### O que deve ser feito
- Normalizar campos e tipos.
- Integrar cálculos das RQ01–RQ06.
- Gerar saída processada padronizada.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `src/metrics/`

### Dependências
- S01-01
- S01-02
- S01-03
- S02-01

### Critérios de aceitação
- [ ] Pipeline executa fim a fim sem erro.
- [ ] Métricas aparecem no dataset processado.
- [ ] Etapas do pipeline são reexecutáveis.

### Resultado esperado
Base processada pronta para validação e análise.

---

## S02-04 — Validar RQ01 + RQ02 nos 1.000
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Validar consistência das métricas RQ01 e RQ02 na base completa.

### O que deve ser feito
- Executar verificações de completude e faixa de valores.
- Conferir amostras manuais de registros.
- Registrar achados e correções necessárias.

### Arquivos/módulos envolvidos
- `tests/`
- `src/metrics/`
- `data/processed/`

### Dependências
- S02-03

### Critérios de aceitação
- [ ] Regras de validação executadas.
- [ ] Não há inconsistências críticas em RQ01/RQ02.
- [ ] Evidências de validação registradas.

### Resultado esperado
RQ01 e RQ02 validadas para análise estatística.

---

## S02-05 — Validar RQ03 + RQ04 nos 1.000
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Validar consistência das métricas RQ03 e RQ04 na base completa.

### O que deve ser feito
- Aplicar verificações automáticas e amostrais.
- Revisar casos de outliers.
- Ajustar regras de transformação quando necessário.

### Arquivos/módulos envolvidos
- `tests/`
- `src/metrics/`
- `data/processed/`

### Dependências
- S02-03

### Critérios de aceitação
- [ ] Validação automatizada concluída para RQ03/RQ04.
- [ ] Outliers revisados e classificados.
- [ ] Métricas aprovadas para análise.

### Resultado esperado
RQ03 e RQ04 consistentes para etapa analítica.

---

## S02-06 — Validar RQ05 + RQ06 nos 1.000
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Validar consistência das métricas RQ05 e RQ06 na base completa.

### O que deve ser feito
- Validar presença e qualidade de linguagem primária.
- Conferir cálculo de percentual de issues fechadas.
- Registrar resultados e pendências.

### Arquivos/módulos envolvidos
- `tests/`
- `src/metrics/`
- `data/processed/`

### Dependências
- S02-03

### Critérios de aceitação
- [ ] Métrica RQ05 validada sem falhas críticas.
- [ ] Métrica RQ06 validada com cálculos corretos.
- [ ] Evidências documentadas para revisão.

### Resultado esperado
RQ05 e RQ06 aprovadas para análise final.

---

## S02-07 — Relatório de qualidade dos dados
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Documentar qualidade, completude e limitações dos dados coletados.

### O que deve ser feito
- Consolidar achados das validações S02-04/05/06.
- Descrever problemas, impacto e mitigação.
- Armazenar relatório em versão de rascunho.

### Arquivos/módulos envolvidos
- `reports/drafts/`
- `data/processed/`

### Dependências
- S02-04
- S02-05
- S02-06

### Critérios de aceitação
- [ ] Relatório cobre todas as RQ01–RQ06.
- [ ] Limitações e riscos estão explícitos.
- [ ] Documento disponível para revisão do grupo.

### Resultado esperado
Visão consolidada da confiabilidade dos dados.

---

## S02-08 — Snapshot automático do Kanban
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Registrar snapshots do board ao fim da sprint para evidência do processo.

### O que deve ser feito
- Definir rotina de captura do estado do board.
- Armazenar snapshots com identificação da sprint.
- Garantir acesso aos artefatos para avaliação.

### Arquivos/módulos envolvidos
- `data/snapshots/`

### Dependências
- S01-05

### Critérios de aceitação
- [ ] Snapshot da Sprint 2 gerado.
- [ ] Artefato armazenado em local definido.
- [ ] Snapshot vinculado às Issues da sprint.

### Resultado esperado
Histórico rastreável da execução no GitHub Projects.

---

# Sprint 3 — Lab01S03

## S03-01 — Analisar RQ01 + RQ02
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Realizar análise dos resultados de idade de repositório e PRs aceitas.

### O que deve ser feito
- Calcular estatísticas descritivas.
- Identificar padrões e outliers relevantes.
- Registrar interpretação inicial para relatório.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/drafts/`

### Dependências
- S02-04

### Critérios de aceitação
- [ ] Estatísticas de RQ01/RQ02 produzidas.
- [ ] Achados documentados em rascunho.
- [ ] Resultados prontos para revisão em grupo.

### Resultado esperado
Conclusões preliminares de RQ01 e RQ02.

---

## S03-02 — Analisar RQ03 + RQ04
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Realizar análise dos resultados de releases e frequência de atualização.

### O que deve ser feito
- Gerar estatísticas descritivas e comparações.
- Identificar tendências de atividade.
- Consolidar síntese para o relatório final.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/drafts/`

### Dependências
- S02-05

### Critérios de aceitação
- [ ] Estatísticas de RQ03/RQ04 concluídas.
- [ ] Tendências registradas com clareza.
- [ ] Conteúdo integrado ao rascunho.

### Resultado esperado
Conclusões preliminares de RQ03 e RQ04.

---

## S03-03 — Analisar RQ05 + RQ06
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Realizar análise dos resultados de linguagem primária e percentual de issues fechadas.

### O que deve ser feito
- Produzir distribuição por linguagem.
- Avaliar comportamento dos percentuais de fechamento.
- Consolidar interpretação para o relatório.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/drafts/`

### Dependências
- S02-06

### Critérios de aceitação
- [ ] Resultados de RQ05/RQ06 analisados.
- [ ] Interpretações registradas em rascunho.
- [ ] Material pronto para integração final.

### Resultado esperado
Conclusões preliminares de RQ05 e RQ06.

---

## S03-04 — Implementar RQ07
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Implementar a análise integrada entre linguagem, contribuição externa, releases e frequência de atualização.

### O que deve ser feito
- Integrar resultados das RQ01–RQ06.
- Definir abordagem de análise para relações entre variáveis.
- Gerar saída específica da RQ07.

### Arquivos/módulos envolvidos
- `src/metrics/`
- `src/analysis/`
- `reports/drafts/`

### Dependências
- S03-01
- S03-02
- S03-03

### Critérios de aceitação
- [ ] RQ07 implementada com dados consolidados.
- [ ] Relações entre variáveis documentadas.
- [ ] Resultado pronto para revisão do grupo.

### Resultado esperado
Resposta integrada da RQ07 baseada nas demais RQs.

---

## S03-05 — Gerar visualizações automaticamente
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Automatizar geração de gráficos para apoiar resultados das RQs.

### O que deve ser feito
- Definir conjunto mínimo de visualizações por RQ.
- Implementar rotina de geração automática.
- Salvar saídas em diretório de figuras.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/figures/`

### Dependências
- S03-01
- S03-02
- S03-03
- S03-04

### Critérios de aceitação
- [ ] Gráficos principais gerados sem intervenção manual.
- [ ] Arquivos exportados em local padrão.
- [ ] Visualizações utilizáveis no relatório final.

### Resultado esperado
Pacote de figuras atualizado e reproduzível.

---

## S03-06 — Gerar resumo estatístico automaticamente
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Automatizar geração de tabelas-resumo estatísticas para todas as RQs.

### O que deve ser feito
- Definir indicadores estatísticos mínimos.
- Implementar geração automática do resumo.
- Exportar resultado para uso no relatório.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/drafts/`

### Dependências
- S03-01
- S03-02
- S03-03
- S03-04

### Critérios de aceitação
- [ ] Resumo estatístico gerado automaticamente.
- [ ] Indicadores cobrem todas as RQs implementadas.
- [ ] Saída pronta para incorporação no relatório.

### Resultado esperado
Base estatística consolidada para redação final.

---

## S03-07 — Criar testes das métricas
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Criar testes para validar cálculos de métricas e evitar regressões.

### O que deve ser feito
- Definir casos de teste por métrica.
- Implementar testes automatizados de unidades-chave.
- Executar testes em pipeline local.

### Arquivos/módulos envolvidos
- `tests/`
- `src/metrics/`

### Dependências
- S01-01
- S01-02
- S01-03
- S03-04

### Critérios de aceitação
- [ ] Casos principais cobertos por testes.
- [ ] Testes executam sem falhas.
- [ ] Regressões detectáveis em futuras alterações.

### Resultado esperado
Camada mínima de confiabilidade para métricas do laboratório.

---

# Relatório Final

## FINAL-01 — Introdução e metodologia
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Consolidar seção de introdução e metodologia do relatório final.

### O que deve ser feito
- Integrar contexto, objetivos e metodologia validada.
- Garantir coerência com coleta e processamento executados.
- Revisar alinhamento com requisitos do laboratório.

### Arquivos/módulos envolvidos
- `reports/final/`
- `docs/methodology.md`

### Dependências
- S02-07

### Critérios de aceitação
- [ ] Seção de metodologia consistente com implementação.
- [ ] Texto revisado pelo grupo.
- [ ] Versão pronta para avaliação.

### Resultado esperado
Base narrativa inicial do relatório final concluída.

---

## FINAL-02 — Resultados e visualizações
**Responsável:** Integrante B  
**Tipo:** Obrigatória

### Objetivo
Consolidar seção de resultados com tabelas e gráficos finais.

### O que deve ser feito
- Integrar resultados das RQ01–RQ07.
- Selecionar visualizações principais.
- Garantir correspondência entre texto e evidências.

### Arquivos/módulos envolvidos
- `reports/final/`
- `reports/figures/`

### Dependências
- S03-05
- S03-06

### Critérios de aceitação
- [ ] Resultados de todas as RQs apresentados.
- [ ] Visualizações referenciadas corretamente.
- [ ] Seção revisada e validada pelo grupo.

### Resultado esperado
Seção de resultados pronta para submissão.

---

## FINAL-03 — Discussão e processo
**Responsável:** Integrante C  
**Tipo:** Obrigatória

### Objetivo
Consolidar discussão, limitações, ameaças à validade e lições do processo.

### O que deve ser feito
- Relacionar achados com limitações observadas.
- Documentar decisões de processo do grupo.
- Consolidar ameaças e mitigação.

### Arquivos/módulos envolvidos
- `reports/final/`

### Dependências
- FINAL-01
- FINAL-02

### Critérios de aceitação
- [ ] Limitações e ameaças à validade descritas.
- [ ] Discussão conectada aos resultados obtidos.
- [ ] Seção revisada pelo grupo.

### Resultado esperado
Análise crítica final completa e consistente.

---

## FINAL-04 — Revisão e integração do relatório
**Responsável:** Integrante A  
**Tipo:** Obrigatória

### Objetivo
Executar revisão final e integração de todas as seções do relatório.

### O que deve ser feito
- Padronizar estrutura, formatação e referências.
- Verificar coerência entre seções e figuras.
- Preparar versão final para entrega.

### Arquivos/módulos envolvidos
- `reports/final/`

### Dependências
- FINAL-01
- FINAL-02
- FINAL-03

### Critérios de aceitação
- [ ] Documento final sem inconsistências estruturais.
- [ ] Revisão ortográfica e técnica concluída.
- [ ] Versão final pronta para submissão.

### Resultado esperado
Relatório final integrado e pronto para entrega.

---

# Tasks Incrementais

## EXTRA-01 — Logging das coletas
**Responsável:** Integrante C  
**Tipo:** Incremental

### Objetivo
Ampliar rastreabilidade operacional da coleta com logs detalhados.

### O que deve ser feito
- Registrar início/fim de execução e duração.
- Logar total por página e eventos de erro.
- Definir formato único de log.

### Arquivos/módulos envolvidos
- `src/collectors/`
- `src/github/`

### Dependências
- S02-01

### Critérios de aceitação
- [ ] Logs detalhados disponíveis por execução.
- [ ] Eventos críticos identificáveis.
- [ ] Formato de log documentado.

### Resultado esperado
Maior capacidade de auditoria da coleta.

---

## EXTRA-02 — Monitoramento do rate limit
**Responsável:** Integrante A  
**Tipo:** Incremental

### Objetivo
Monitorar consumo de rate limit para reduzir risco de interrupção da coleta.

### O que deve ser feito
- Capturar informações de rate limit por requisição.
- Criar alerta interno de limiar crítico.
- Ajustar comportamento de espera quando necessário.

### Arquivos/módulos envolvidos
- `src/github/`
- `src/collectors/`

### Dependências
- S01-06

### Critérios de aceitação
- [ ] Consumo de rate limit visível em execução.
- [ ] Limiar crítico detectado automaticamente.
- [ ] Coleta evita falhas por esgotamento previsível.

### Resultado esperado
Coleta mais estável em execuções longas.

---

## EXTRA-03 — Exportação dos dados em JSON
**Responsável:** Integrante B  
**Tipo:** Incremental

### Objetivo
Adicionar formato JSON para compartilhamento e reuso dos dados.

### O que deve ser feito
- Definir estrutura JSON de saída.
- Implementar exportação para bruto e processado.
- Validar integridade do arquivo gerado.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `data/raw/`
- `data/processed/`

### Dependências
- S02-02

### Critérios de aceitação
- [ ] JSON bruto e processado gerados.
- [ ] Estrutura consistente com os CSVs.
- [ ] Arquivos válidos e legíveis.

### Resultado esperado
Formato adicional de dados disponível para integração.

---

## EXTRA-04 — Pipeline reproduzível
**Responsável:** Integrante A  
**Tipo:** Incremental

### Objetivo
Facilitar reexecução completa do fluxo com parâmetros padronizados.

### O que deve ser feito
- Padronizar parâmetros de entrada.
- Definir rotina única de execução.
- Documentar passos mínimos de reprodução.

### Arquivos/módulos envolvidos
- `src/collectors/`
- `src/analysis/`
- `README.md`

### Dependências
- S02-03

### Critérios de aceitação
- [ ] Fluxo reexecutável com passos definidos.
- [ ] Parâmetros documentados.
- [ ] Saídas reproduzíveis em nova execução.

### Resultado esperado
Redução de variabilidade operacional entre execuções.

---

## EXTRA-05 — Automação das análises
**Responsável:** Integrante B  
**Tipo:** Incremental

### Objetivo
Automatizar a geração de resultados analíticos consolidados.

### O que deve ser feito
- Encadear execução das análises das RQs.
- Integrar geração de estatísticas e visualizações.
- Produzir artefatos de saída padronizados.

### Arquivos/módulos envolvidos
- `src/analysis/`
- `reports/figures/`
- `reports/drafts/`

### Dependências
- S03-05
- S03-06

### Critérios de aceitação
- [ ] Rotina única executa análises completas.
- [ ] Artefatos são gerados em diretórios padrão.
- [ ] Execução documentada para o grupo.

### Resultado esperado
Processo analítico com menor esforço manual.

---

## EXTRA-06 — Testes automatizados
**Responsável:** Integrante C  
**Tipo:** Incremental

### Objetivo
Expandir cobertura de testes para coleta, transformação e análise.

### O que deve ser feito
- Adicionar testes além das métricas centrais.
- Incluir cenários de erro e borda.
- Consolidar rotina de execução de testes.

### Arquivos/módulos envolvidos
- `tests/`
- `src/collectors/`
- `src/github/`
- `src/analysis/`

### Dependências
- S03-07

### Critérios de aceitação
- [ ] Cobertura ampliada em áreas críticas.
- [ ] Cenários de erro contemplados.
- [ ] Execução de testes repetível.

### Resultado esperado
Maior confiabilidade geral do projeto.
