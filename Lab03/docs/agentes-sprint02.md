# Agentes recorrentes da Sprint 02

Em 14/10/2026, o responsável autorizou um agente por task de sua Sprint 02,
com verificação **a cada 30 minutos**, para analisar o marco de coleta e
iniciar as entregas quando as dependências permitirem. As tasks são #151,
#153, #154, #158 e #166. O agente #151 audita a conclusão; a coleta continua
sendo executada pelos processos principal e auxiliar existentes, com meta
de 500 elegíveis.

## Gatilho comum e proteção da coleta

Cada agente lê `processo.json` e `progresso.json` em
`Lab03/data/raw/amostra-final-500/`, no checkout original. O gatilho é
**300 elegíveis com coleta completa de runs**, não 300 candidatos avaliados.
Antes disso, registra apenas uma verificação em seu estado privado, sem
editar implementações, mudar Git ou consultar a API de coleta.

O marco de 300 não congela a amostra nem autoriza interromper a execução:
os grandes adiados são liberados nesse marco, e a coleta continua até 500.
Saídas consolidadas e auditorias só ficam disponíveis ao terminar o pipeline.
Não gerar resultados finais a partir de um conjunto de checkpoints mutável.

Nenhum agente pode interromper/reiniciar coletores, alterar configuração,
fila, fontes, cache ou checkpoints ativos. Implementações usam worktrees
separados e branches `feat/`, sem trocar a branch do checkout original nem
do worktree que mantém o coletor em execução.

## Responsabilidades

| Agente | Escopo após o marco | Dependências para concluir |
|---|---|---|
| #151 — S02-01 | Registrar o marco de 300 e preparar auditoria da coleta, sem duplicar o executor. | Pipeline completo com cache, mínimo de 300 incluídos (meta 500), funil atualizado e evidências/auditorias finais consistentes. |
| #153 — S02-03 | Implementar exportador CSV local, uma linha por ID da amostra, com metadados/métricas e nulos preservados; testar sem API. | Para o CSV real: execução final concluída, amostra imutável e fontes/auditorias compatíveis. O CSV consolidado deve ser versionado conforme a issue; cache, dados brutos e credenciais não são publicados. |
| #154 — S02-04 | Revisar o dicionário já publicado e conferir as colunas reais do exportador #153, corrigindo somente divergências. | Contrato real do exportador e evidência de correspondência. Não recriar documentação equivalente a cada execução. |
| #158 — S02-08 | Preparar instruções e somente as planilhas em branco do rotulador C, preservando a independência. | População final congelada e sorteio oficial #155; depois, rotulagem independente feita pelo responsável. O agente não inventa rótulos humanos nem consulta A/B ou a heurística. |
| #166 — S02-16 | Revisar a metodologia já publicada, incluindo priorização por custo até 300, retomada dos grandes e referência ao dicionário vigente. | Política documentada, definições/variantes/censura consistentes e validação LaTeX. Resultados da amostra final continuam distintos do piloto. |

As tasks #154 e #166 foram implementadas em `feat/docs-s02-154-166`; os
agentes partem desse trabalho. A política do coletor está em
`feat/coleta-auxiliar`, com a justificativa em
[decisoes-coleta-final.md](decisoes-coleta-final.md).

## Execução idempotente e coordenação

Estado durável, separado por agente, no checkout original:
`Lab03/data/processed/sprint02-agentes/<numero>/estado.json`.
Guardar fase, última verificação, contagem observada, dependências, worktree,
branch, commits, hashes das entradas e evidências de validação. Nunca escrever
estado de outro agente nem reaproveitar o Git index de um worktree compartilhado.

Ao iniciar implementação, criar/reutilizar um worktree dedicado. Prefixos
de branches reservados: `feat/s02-01-validacao-coleta-151`, `feat/s02-03-dataset-153`,
`feat/s02-04-dicionario-154`, `feat/s02-08-rotulagem-c-158` e
`feat/s02-16-metodologia-166`. Os agentes #154 e #166 usam clones de trabalho
separados, mesmo quando partem da mesma branch documental.

Antes de cada geração de dados, validar identidade, janela e estabilidade
das entradas por hashes. Mesmo hash e entrega já validada significam nenhuma
reexecução. A CFR (b) pendente da #161 continua nula e explícita; não inventar
métrica para satisfazer completude. Não sobrescrever planilhas com rótulos
nem gerar sorteio alternativo ao oficial da #155.

Publicar código/documentação por commits que referenciem a respectiva issue,
com testes adequados, sem force push ou merge automático. Não fechar issues
nem mudar o Projects automaticamente: entrega técnica e aceite são distintos.
Após entrega validada, desativar o acompanhamento correspondente para evitar
repetições. Quando faltar apenas a rotulagem humana, informar isso uma vez e
pausar o agente #158, mantendo o material preparado.

Os acompanhamentos ficam associados a esta conversa e retornam ao mesmo
contexto. Enquanto aguardarem sem mudança relevante, apenas atualizar estado
interno; comunicar conclusão, falha confirmada ou ação humana necessária.
