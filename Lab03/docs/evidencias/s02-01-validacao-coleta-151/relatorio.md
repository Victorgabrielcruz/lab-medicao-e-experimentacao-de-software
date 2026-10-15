# Auditoria da amostra encerrada de 255 — #151

A extração principal e auxiliar foi encerrada por instrução humana em 15/10/2026.
A amostra congelada contém **255 elegíveis entre 561 candidatos**; a consolidação
offline foi validada, sem novas consultas à API. Os critérios originais de
mínimo 300 e meta 500 **não foram atingidos**. A issue permanece para aceite.

## Evidências e funil

Foram conferidos 574 arquivos preservados, 255 identidades, janela UTC
2025-10-01 inclusive a 2026-10-01 exclusive, 12 meses de runs por projeto e
mínimos de cinco releases estáveis e 50 runs válidos. A auditoria independente
do snapshot conferiu 2.586.659 runs no recorte e 2.234.420 runs válidos.

| Etapa | Entrada | Descartados | Restantes |
| --- | ---: | ---: | ---: |
| Busca na Search API | 561 | 0 | 561 |
| Usa GitHub Actions | 561 | 74 | 487 |
| Metadados coletados | 487 | 1 | 486 |
| Releases coletadas | 486 | 0 | 486 |
| Workflow runs coletados | 486 | 198 | 288 |
| Critério mínimo de inclusão | 288 | 32 | 256 |
| Coleta completa de runs (amostra oficial) | 256 | 1 | 255 |

O critério quantitativo admite 256 projetos; um deles tem runs incompletos.
A etapa explícita de completude exclui esse candidato e reproduz os 255 IDs
oficiais, sem incluir tarefas auxiliares não consumidas ou em andamento.

## Cobertura e limites

| Métrica | Projetos com valor |
| --- | ---: |
| deployment_frequency | 255 |
| lead_time_a | 9 |
| lead_time_b | 9 |
| cfr_a | 255 |
| cfr_b | 0 |
| tempo_recuperacao | 241 |

Os 246 projetos sem compare permanecem com lead times (a)/(b) nulos e
indicadores de incompletude/cálculo parcial. CFR(b) #161 permanece nula em todos.
Recuperação é nula quando não observável; ausência não equivale a zero.
Há três projetos com diagnósticos temporais, mantidos nas evidências.

A auditoria de runs/CFR(a)/recuperação passou para 255 IDs; a auditoria de lead
time passou para o subconjunto de nove com compare local. Isso não demonstra
cobertura de compare nos demais nem conclusão do pipeline original de 500.

O encerramento ocorreu antes do marco de 300 e da liberação de Grafana/grandes
adiados. A priorização por custo e a interrupção podem afetar representatividade.
O piloto e suas hipóteses continuam preservados.

## Artefatos e rastreabilidade

O CSV público tem 255 linhas e 28 colunas (`lab03-dataset-v1`). Os dados brutos
e o cache permanecem privados. Hashes agregados das entradas auditadas estão
em [auditoria-amostra-255.json](auditoria-amostra-255.json).
O snapshot é identificado pelo manifesto privado de encerramento; seu
`processo.json` preserva o último sinal antes da parada, e não uma conclusão
artificial da extração.

A [decisão humana](../../decisao-encerramento-255.md) e o
[plano revisado](../../agentes-sprint02.md) definem o escopo de aceite.
O sorteio oficial #155 e a rotulagem independente #158 continuam dependências.
Nenhuma issue foi fechada, nenhum Projects foi alterado e não houve merge automático.
