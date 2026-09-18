# Auditoria de execução — Sprint S02

**Task:** S02-06 — Auditar a execução e encerrar a sprint (Issue #74)
**Data da auditoria:** 17/09/2026 (achados iniciais) — **atualizada em 18/09/2026** após a execução dos dois trials que faltavam
**Responsável:** Jonathan (com apoio de Claude Code)
**Base analisada:** `origin/main` (todas as PRs de S02-02 a S02-04 já mergeadas, incluindo a PR #120 e os commits que fecham `P02-K01-ai`/`P02-K04-ai`), confrontada com `data/metadata/allocation.csv`, `Docs/protocol-decisions.md`, as 18 Issues de trial e o histórico de commits/PRs no GitHub.

## 1. Resultado resumido

| Verificação | Resultado |
|---|---|
| Trials confrontados com a alocação (18) | **18/18** com código + dado bruto |
| Métricas estruturais obrigatórias (`data/raw/metrics/<id>/metrics.json`) | **10/18** possuem; **8/18 ainda faltando** |
| Vínculo Issue ↔ trial ↔ commit | **18/18 OK** |
| Desvios/incidentes registrados em `protocol-decisions.md` | **3 registrados corretamente**; **2 ainda pendentes de registro** (ver 3.5) |
| Contribuição individual por integrante na sprint | OK — os três têm commits atribuíveis no período |
| GitHub Projects reflete o estado real | **Não verificado** (token do `gh` usado nesta auditoria não tem escopo `read:project`; checagem manual necessária) |
| Dataset consolidado (S02-05, #73) | **Não existe ainda** (`data/processed/trials.csv` vazio) — Issue #73 segue aberta |
| Prazo da sprint (17/09, 23:59) | `P02-K04-ai` fechou às 23:55 de 17/09 (dentro do prazo). `P02-K01-ai` fechou às 00:10 de **18/09**, ~10min após o prazo — registrado aqui sem alteração de timestamp |

**Atualização de 18/09/2026:** os dois trials que faltavam (`P02-K01-ai`, `P02-K04-ai`) foram executados e commitados diretamente na `main` (ver Seção 3.1/3.2, agora resolvidas). A coleta dos 18 trials está **completa**. Restam pendências de menor severidade — métricas estruturais de 8 trials antigos, um registro de incidente não formalizado, o atraso de `P02-K01-ai` em relação ao prazo, e a dependência de S02-05/#73 — ver Seção 8 para a lista atualizada.

## 2. Trials x alocação

| trial_id | participante | ordem | bloco | tratamento | Issue | `trials/` | `data/raw/trials/` | `data/raw/metrics/` | Observação |
|---|---|---|---|---|---|:---:|:---:|:---:|---|
| P01-K01-ai | P01 | 1 | B1 | ai | #115 | ✅ | ✅ | ❌ | Tentativa 1 invalidada e documentada (Seção 4); retentativa válida sem métricas estruturais |
| P01-K02-manual | P01 | 4 | B1 | manual | #116 | ✅ | ✅ | ❌ | Incidente de captura documentado (Seção 4); sem métricas estruturais |
| P01-K03-manual | P01 | 2 | B2 | manual | #97 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P01-K04-ai | P01 | 5 | B2 | ai | #98 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P01-K05-manual | P01 | 6 | B3 | manual | #99 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P01-K06-ai | P01 | 3 | B3 | ai | #100 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P02-K01-ai | P02 | 6 | B1 | ai | #101 | ✅ | ✅ | ✅ | Executado em 18/09 (00:05–00:10, ~10min após o prazo de 17/09 23:59). Assistente: Claude (substituição ao Codex, não registrada em `protocol-decisions.md` — ver 3.5) |
| P02-K02-manual | P02 | 3 | B1 | manual | #102 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P02-K03-manual | P02 | 5 | B2 | manual | #103 | ✅ | ✅ | ✅ | Completo |
| P02-K04-ai | P02 | 2 | B2 | ai | #104 | ✅ | ✅ | ✅ | Executado em 17/09 23:54–23:55 (dentro do prazo). Tentativa 1 (89s, sem interação real) invalidada e preservada em `_invalidated/`. Assistente: Claude (mesma ressalva de registro) |
| P02-K05-ai | P02 | 4 | B3 | ai | #105 | ✅ | ✅ | ✅ | Completo |
| P02-K06-manual | P02 | 1 | B3 | manual | #106 | ✅ | ✅ | ❌ | Sem métricas estruturais |
| P03-K01-manual | P03 | 2 | B1 | manual | #107 | ✅ | ✅ | ✅ | Completo |
| P03-K02-ai | P03 | 5 | B1 | ai | #108 | ✅ | ✅ | ✅ | Completo |
| P03-K03-ai | P03 | 1 | B2 | ai | #109 | ✅ | ✅ | ✅ | Retentativa válida completa, mas a tentativa 1 invalidada **não está registrada** em `protocol-decisions.md` (ver Seção 4 abaixo) |
| P03-K04-manual | P03 | 3 | B2 | manual | #110 | ✅ | ✅ | ✅ | Completo |
| P03-K05-manual | P03 | 6 | B3 | manual | #111 | ✅ | ✅ | ✅ | Completo |
| P03-K06-ai | P03 | 4 | B3 | ai | #112 | ✅ | ✅ | ✅ | Completo |

## 3. Achados classificados

### 3.1 [RESOLVIDO] `P02-K01-ai` estava ausente sem justificativa (Issue #101)

**Estado original (17/09):** a Issue #101 tinha sido fechada sem nenhum commit, PR ou branch associado, sem entrada em `protocol-decisions.md`, e sem diretórios em `trials/`, `data/raw/trials/` ou `data/raw/metrics/`. Nenhuma evidência de execução nem de exclusão deliberada.

**Resolução (18/09):** o trial foi executado — participante propôs a abordagem (agrupar por doca, ordenar por início) antes da implementação, 6/6 testes em 316s. Commit `41f541c` (`#101 feat: executa trial P02-K01-ai...`) na `main`, com métricas estruturais coletadas. **Execução terminou às 00:10 de 18/09, ~10min após o prazo de 23:59 de 17/09** — ver nota de prazo na Seção 1 e recomendação na Seção 8.

### 3.2 [RESOLVIDO] `P02-K04-ai` estava bloqueado, decisão de grupo pendente (Issue #104)

**Estado original (17/09):** o Codex CLI 0.154.0 (autenticado via conta ChatGPT) tinha retornado `HTTP 400` ao tentar usar o modelo congelado `gpt-5.3-codex`, impedindo o início do trial. O registro do incidente só existia numa PR aberta (#120), não mergeada, e a Issue #104 já tinha sido fechada sem a decisão de grupo mencionada no próprio texto do incidente.

**Resolução (18/09):** a PR #120 foi mergeada na `main` (registro do incidente de infraestrutura preservado em `protocol-decisions.md`, Seção 4). O trial foi então executado com Claude como assistente de IA (mesma substituição já usada nos trials de P01). Uma primeira tentativa oficial fechou em 89s sem interação real do participante — invalidada e preservada em `trials/_invalidated/P02-K04-ai-attempt1/` e `data/raw/trials/_invalidated/P02-K04-ai-attempt1/incident.json`, seguindo o mesmo procedimento já usado para `P01-K01-ai`. A segunda tentativa, com decisão real do participante registrada antes da suíte fechar (57s), é o resultado oficial. Commit `f4a3291`/merge na `main`.

### 3.3 Falha sistemática (menor a moderada, mas recorrente) — métricas estruturais ausentes em 8 trials

`Docs/execution-guide.md` (Seção 9, checklist de encerramento) exige explicitamente `data/raw/metrics/<trial_id>/metrics.json` antes de liberar a próxima linha da alocação. Esse artefato está ausente em **todos os 6 trials de P01** e em **P02-K02-manual** e **P02-K06-manual** — 8 dos 16 trials executados. Apenas P02-K03-manual, P02-K05-ai e os 6 trials de P03 têm o diretório completo (`metrics.json`, `radon-cc.json`, `radon-mi.json`, `radon-raw.json`, `jscpd/`).

Isso não invalida os trials (código, testes e cronometragem estão preservados), mas compromete diretamente a Issue #78 (RQ3 — qualidade estrutural), que depende desses dados para todos os 18 trials, e nenhum dos casos tem justificativa registrada em `protocol-decisions.md`.

**Ação recomendada:** rodar `scripts/collect_static_metrics.py <trial_id> --source trials/<trial_id>/src` para os 8 trials listados, preservando o dado bruto sem edição manual; se algum código-fonte não estiver mais disponível tal como estava no momento do trial, registrar isso como desvio na Seção 3 em vez de gerar a métrica retroativamente sem nota.

### 3.4 Falha menor — tentativa invalidada de `P03-K03-ai` sem registro (Issue #109)

`data/raw/trials/_invalidated/P03-K03-ai-attempt1/trial.json` mostra o mesmo padrão já visto e formalmente invalidado em `P01-K01-ai`: a suíte fechou 100% em ~22s, sem sinal de interação do participante (a retentativa válida levou 251s). Diferente do caso de P01-K01-ai — que tem `incident.json`, está documentado na Seção 4 de `protocol-decisions.md` e tem README explicando a invalidação — este caso de P03 não tem `incident.json` e não aparece em `protocol-decisions.md`.

**Ação recomendada:** adicionar uma linha à Seção 4 de `protocol-decisions.md` para `P03-K03-ai-attempt1`, no mesmo padrão usado para `P01-K01-ai`, para manter a auditoria consistente entre participantes.

### 3.5 Falha menor, ainda aberta — substituição de assistente em `P02-K01-ai`/`P02-K04-ai` não registrada

Os dois trials resolvidos em 18/09 usaram **Claude** como assistente de IA em vez do Codex CLI congelado para P02 (`PARTICIPANT_AI_ASSISTANT` em `src/environment.py` mapeia P02 → codex). Isso é a mesma exceção já usada e formalmente registrada para os três trials de IA de P01 (`protocol-decisions.md`, Seção 3) — mas, para P02, a decisão foi tomada durante a execução e **não foi registrada** em `protocol-decisions.md`. Os `treatment-verification.json` dos dois trials já refletem `ai_assistant: "claude"` honestamente (não há inconsistência no dado bruto), só falta o registro formal do desvio, que a própria Seção 3 do documento exige antes de continuar os trials.

**Ação recomendada:** o grupo deve decidir se quer formalizar essa exceção em `protocol-decisions.md` (Seção 3), no mesmo padrão usado para P01, para manter a auditoria consistente — decisão explicitamente adiada por Jonathan durante a execução (18/09), não esquecida.

### 3.6 Itens já corretamente registrados (sem ação necessária)

- Mudança de política de extensões do VS Code (15/09) — Seção 3.
- Uso de Claude em vez de Codex CLI nos trials de IA de P01 (15/09) — Seção 3, com ressalva já anotada sobre ameaça à comparabilidade entre participantes que a própria equipe deverá avaliar na análise (RQ2/RQ3).
- Invalidação de `P01-K01-ai` (tentativa 1) e correção da condição de corrida em `P01-K02-manual` — Seção 4, ambos com evidência bruta preservada e causa raiz documentada.
- Incidente de infraestrutura de `P02-K04-ai` (Codex CLI + conta ChatGPT) — Seção 4, desde o merge da PR #120 em 18/09.

## 4. Vínculo Issue ↔ trial ↔ commit

Os 18 trials têm commit(s) na `main` referenciando a Issue correspondente no formato `#<issue> feat: executa trial <trial_id>` (ou `docs:`/`fix:` para incidentes), consistente com o exigido pelo protocolo.

## 5. Contribuição individual

Commits atribuíveis a cada integrante desde o início da S02 (12/09/2026):

- Jonathan Sena da Silva — 10 commits (P01, completo)
- Matheus Fernandes / matheus-0063 — 11 commits (P02, com as duas lacunas acima)
- Victor Gabriel / Victor — 10 commits (P03, completo)

Os três integrantes têm commits atribuíveis na sprint; a regra do enunciado ("ausência de commits... zera a parcela individual") não é violada para nenhum integrante.

## 6. GitHub Projects

Não foi possível consultar o board programaticamente nesta auditoria (o token do `gh` disponível não tem o escopo `read:project`). **Verificação manual pendente:** confirmar que as duas Issues #101 e #104 não aparecem como "Concluído" no board sem os apontamentos acima, e que o board reflete `data/processed/trials.csv` ainda não existir.

## 7. Dependência de S02-05 (#73)

A própria Issue #74 depende de #73 ("Consolidar o dataset dos trials"), que segue **aberta**; `data/processed/trials.csv` ainda não existe (só `.gitkeep`). A consolidação de #73 vai automaticamente expor a lacuna de `P02-K01-ai` (dataset teria 17, não 18, linhas) e os valores ausentes de métricas estruturais — reforça que #74 não pode ser fechada antes de #73, e que os achados 3.1–3.3 devem ser resolvidos (ou formalmente registrados como exclusão) antes da consolidação.

## 8. Recomendação final

A coleta dos 18 trials está completa desde 18/09/2026 — os dois bloqueios que impediam a auditoria (3.1, 3.2) estão resolvidos. Restam pendências de menor severidade, nenhuma delas bloqueando o trabalho de outra pessoa do grupo:

1. **Prazo:** `P02-K01-ai` foi concluído às 00:10 de 18/09, ~10min após o prazo formal de 23:59 de 17/09 (Seção 1.5 de `protocol-decisions.md`). Isso deveria ser comunicado ao grupo/professor como um atraso pontual, não omitido.
2. Decidir se a substituição de assistente (Claude em vez de Codex) em `P02-K01-ai`/`P02-K04-ai` será formalmente registrada em `protocol-decisions.md` — item 3.5.
3. Gerar as métricas estruturais faltantes dos 8 trials antigos (6 de P01 + P02-K02-manual + P02-K06-manual) — item 3.3.
4. Registrar a tentativa invalidada de `P03-K03-ai` na Seção 4 de `protocol-decisions.md` — item 3.4.
5. Conferir manualmente o GitHub Projects — item 6.
6. S02-05 (#73) segue aberta e é dependência formal desta issue — a consolidação do dataset (`data/processed/trials.csv`) ainda precisa acontecer antes de #74 poder ser considerada 100% encerrada, mas isso está fora do escopo de execução desta auditoria.
