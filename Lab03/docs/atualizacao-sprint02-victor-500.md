# Revisão da Sprint 02 de Victor — 20/10/2026

Responsável confirmado no GitHub: **Victorgabrielcruz**. Escopo atual:
milestone **Lab03S02**, de 15 a 21/10. As tarefas antigas de Sprint 02 de
outros laboratórios não foram confundidas com as cinco tarefas abaixo.
Branch: `feat/s02-victor-atualizacao-base-500`, criada de `feat-melhoria`
no commit `406d6d5`.

## Conferência das cinco tarefas

| Issue | Estado consultado no GitHub | Revisão com os novos dados |
|---|---|---|
| [#151 — Coleta](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/151) | Fechada pelo aceite do corte de 255 | Captura agora tem 500/1.064; funil corrigido com uma exclusão por runs incompletos. Meta numérica atingida, processamento final parcial. |
| [#153 — Dataset CSV](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/153) | Fechada | Nova entrega de 500 linhas/28 colunas, comando offline, proveniência e cobertura real. A entrega de 255 é preservada. |
| [#154 — Dicionário](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/154) | Fechada | Contrato v1 mantido; escopo de 500, origem pública, nulabilidade e CFR(b) heurística com validação humana pendente. |
| [#158 — Rotulagem C](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/158) | Aberta | Sorteio mantido sobre 255; C tem 60 tipos/60 decisões de entregas/249 releases. Faltam 51 julgamentos; assistência de IA já registrada acompanha a avaliação de independência. |
| [#166 — Metodologia](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/166) | Fechada | Cronologia 255 → retomada → 500, funil atualizado, limitações, sorteio histórico e referência ao novo CSV. |

Os estados refletem o aceite anterior, não uma declaração de conclusão da
extração integral. Esta revisão preserva os estados das issues. Nenhum
coletor ou automação recorrente foi iniciado, e nenhum rótulo humano foi alterado.

## Evidências atuais

A [captura publicada](../entregas/dados-brutos-500/README.md) é a autoridade
dos 500 IDs. A [nova entrega CSV](../entregas/s02-03-dataset-500/README.md)
registra cobertura DF=500, LT(a)=51, LT(b)=51, CFR(a)=500,
CFR(b)=497 e recuperação=469. CFR(b) é saída da heurística v1, ainda sem
validação humana concluída. Compares ausentes permanecem ausentes.
O funil 1064 → 933 → 932 → 569 → 501 → 500 separa mínimos quantitativos
de completude de runs. A decisão de retomada mantém a amostra-ouro oficial
de 60 projetos/300 releases sobre os primeiros 255 elegíveis.

Validação executada: 104 testes de consolidação/exportação/integrado passaram.
O CSV real foi reexportado e comparado byte a byte, conferindo 500 IDs,
28 colunas, janela, hashes e nulabilidade. O compilador do editor desktop
confirmou sucesso de `artigo/main.tex` nesta revisão. Os resultados e resumos
do piloto continuam históricos; sucesso de compilação não atualiza a análise.

## Issues abertas sob responsabilidade de Victorgabrielcruz

Consulta ao repositório em 20/10/2026, filtro `assignee=Victorgabrielcruz`,
excluindo pull requests. Sete issues abertas:

| Issue | Tarefa | Milestone |
|---|---|---|
| [#158](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/158) | Rotulagem independente da amostra-ouro (C) | Lab03S02 |
| [#173](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/173) | RQ07: combinações de definições e classificação | Lab03S03 |
| [#174](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/174) | RQ07: % de mudança de categoria e kappa ponderado | Lab03S03 |
| [#175](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/175) | RQ08 (bônus): rework rate ou evolução temporal | Lab03S03 |
| [#178](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/178) | Artigo: resultados RQ07 | Lab03S03 |
| [#182](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/182) | Tratar issues recebidas do grupo replicador | Entrega Final |
| [#185](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/185) | Artigo: relato da replicação cruzada | Entrega Final |
