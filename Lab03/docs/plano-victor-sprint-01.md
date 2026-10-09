# Plano vigente — entrega limitada de Victor, Lab03 Sprint 01

Atualizado em 08/10/2026 após a decisão humana de cancelar a coleta adicional
por limite de tempo. Este plano substitui as instruções anteriores de
ampliação e monitoramento do executor.

## Escopo autorizado agora

Usar somente o piloto e o cache já existentes, concluir o artigo e entregar
relatório honesto. **Não reiniciar, ampliar nem criar coleta adicional.**
A decisão foi registrada no [comentário da #149](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/149#issuecomment-6072163752).
Dados/cache/checkpoints permanecem para eventual continuidade com nova
autorização humana. Não declarar cem elegíveis, Sprint 01 completa ou aceite.

## Diretórios e limites preservados

- Worktree: `C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software`; branch exclusiva `feat/tasks-victor-sprint-01`.
- Cwd de implementação/testes: `C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03`.
- Python: `C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/.venv/Scripts/python.exe`.
- Checkout original: `C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03`, branch `feat/lab03-s01-18-workflow-runs-146`.
- Antes de executar: ler `.pytest_cache/sprint01-agente/estado.json`.
- Não recalcular saídas auditadas na mesma versão/entrada; não tocar coleta
  original, main, Projects, estado/labels/milestones, merges ou worktrees.
- Não publicar dados reais, cache, config local ou segredos.
- Commit por issue; staging explicitamente revisado; push somente
  `git push origin feat/tasks-victor-sprint-01`, sem force.
- Não enviar mensagens a outros chats. Não duplicar comentário #149.
- Não retornar ao Canvas; enunciado oficial já fornecido pelo usuário.

## Entregas disponíveis e pendências

| Task | Disponível | Limite |
|---|---|---|
| #145 | Rate limit/backoff, 42 testes, 100% no módulo | Cenários remotos de falha não fabricados. |
| #146 | Piloto consolidado: 82 repos/238.629 runs | 18 coletas incompletas, não cem elegíveis. |
| #147 | CFR auditada em 70 repos | 12 sem runs válidos; incompletude preservada. |
| #148 | RQ04 v2 auditada: 6.163 recuperados/38 censurados, 56 repos | 92 sequências com censura à esquerda e 1 repo temporalmente incompleto. |
| #149 | Comando integrado e dependências #134/#138/#140/#141 | Execução dos cem cancelada; #142 e dados de LT pendentes. |
| #150 | Overleaf existente compilado em seis páginas | Hipóteses RQ05–07 complementadas após piloto, sem fingir anterioridade. |

Reaproveitamento offline: cinco repos com releases completas disponíveis,
77 sem essa evidência, zero elegíveis completos confirmados, 42 não elegíveis
conhecidos e 40 indeterminados. Quatro documentos de compare contêm zero
comparações. Zero novas consultas de coleta. Não inferir que todos são inelegíveis.

## Validação e encerramento

Suíte atual: 532 testes, cobertura 97,89%. RQ04
`rq04-updated-at-run-started-at-v2` e classificação
`lab03-enunciado-cortes-v2`. Backup do legado preservado.
CI das correções aprovada. PDF final Overleaf inspecionado nas seis páginas;
fontes exportadas conferidas; estilos 2017 preservados.

O [relatório final da entrega limitada](relatorio-victor-sprint-01.md) foi
consolidado e o heartbeat está pausado. Não confundir essa
entrega parcial com aceite das issues ou conclusão integral da sprint.
S02/validação manual e S03/análises não foram executadas.
