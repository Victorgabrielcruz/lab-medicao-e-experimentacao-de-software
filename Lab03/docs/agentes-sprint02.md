# Agentes recorrentes da Sprint 02 — amostra encerrada

## Situação em 20/10/2026

Este plano de recorrência é histórico. As automações foram removidas por
solicitação humana, conforme a documentação da #158. A
[retomada em 16/10](decisao-retomada-500.md) substituiu o encerramento como
escopo final, e a [captura de 20/10](../entregas/dados-brutos-500/README.md)
tem 500 elegíveis entre 1.064 candidatos, com processamento final parcial.
A [revisão atual das tarefas de Victor](atualizacao-sprint02-victor-500.md)
usa somente dados locais, sem reativar agentes ou iniciar coletores.

## Revisão humana de 15/10/2026

O responsável determinou parar a extração e trabalhar com os dados já obtidos.
As duas coletas foram encerradas com **255 elegíveis completos entre 561 candidatos**.
Esta decisão substitui os gates anteriores de 300 elegíveis e de pipeline final
com 500. O mínimo original de 300 e a meta original de 500 não foram atingidos.
Ver [decisao-encerramento-255.md](decisao-encerramento-255.md).

Nenhum agente pode iniciar ou retomar coletores, fazer novas consultas à API,
alterar fonte/cache/checkpoints ou declarar completo o pipeline original.
Dados de origem e cache são privados. Saídas locais novas ficam separadas.

## Entradas e tarefas

Autoridade no checkout original:
`Lab03/data/processed/sprint02-agentes/encerramento-amostra.json`.
Ler o manifesto e o snapshot imutável ali indicado, conferir identidade,
janela e hashes antes/depois. A população é exatamente a lista oficial de
255 IDs; não incluir checkpoints auxiliares não consumidos.

| Task | Trabalho autorizado agora | Condição para entrega |
| --- | --- | --- |
| #151 — S02-01 | Auditar preservação, população, funil e auditorias locais; reportar encerramento e critérios originais não atingidos. | Evidência agregada validada sobre o escopo revisado, sem alegar 300/500. |
| #153 — S02-03 | Consolidar offline e publicar CSV de 255 linhas com contrato, proveniência, métricas disponíveis e nulos explícitos. | CSV real, manifesto, comando offline e testes/validações; nenhuma API. |
| #154 — S02-04 | Conferir dicionário já implementado contra exportador/contrato reais da #153; corrigir divergências comprovadas. | Contrato e testes reais, incluindo nulos e incompletudes. |
| #158 — S02-08 | Preparar somente planilhas C do sorteio oficial #155 e instruções; validar posteriormente rótulos humanos. | População encerrada e sorteio oficial compatíveis; nenhum rótulo inventado ou planilha sobrescrita. |
| #166 — S02-16 | Revisar metodologia já publicada com política de custo, encerramento em 255, limitações e variantes. | Links e LaTeX validados; piloto preservado e nenhuma alegação de 300/500 completos. |

As tasks #154 e #166 partem de `feat/docs-s02-154-166` (11b0842), sem
refazer a base. A política anterior continua documentada em
[decisoes-coleta-final.md](decisoes-coleta-final.md), como histórico.
A correção de renomeação ativada na coleta foi 4ddbab9.

## Isolamento, recorrência e aceite

Cada agente mantém somente seu estado privado no checkout original:
`Lab03/data/processed/sprint02-agentes/<numero>/estado.json`.
Guardar fase, contagem, dependências, worktree/branch, commits, hashes e
validações. Não iniciar rodada duplicada nem repetir entrega equivalente.

Branches dedicadas: `feat/s02-01-validacao-coleta-151`,
`feat/s02-03-dataset-153`, `feat/s02-04-dicionario-154`,
`feat/s02-08-rotulagem-c-158` e `feat/s02-16-metodologia-166`.
Nunca trocar a branch original ou dos worktrees compartilhados. Não fazer
force push, merge automático, comentários GitHub ou mensagens a outros chats.

Compares ausentes e CFR(b) #161 continuam nulos com razão explícita. Nenhum
agente preenche dados para simular completude. Na #158, não consultar A/B ou
heurística, não usar --sobrescrever e não gerar sorteio alternativo ao #155.

A periodicidade permanece 30 minutos. Sem mudança acionável, atualizar apenas
estado interno. Comunicar conclusão, falha confirmada ou necessidade humana uma
vez. Após validar o próprio escopo revisado, pausar o acompanhamento. Se faltar
só rotulagem humana, #158 informa uma vez e pausa aguardando_rotulagem_humana.
Não fechar issues nem mudar Projects automaticamente: a entrega exige aceite.
