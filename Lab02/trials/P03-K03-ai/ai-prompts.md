# Interações com IA — P03-K03-ai

## Prompt 1

> Estou resolvendo a kata K03. Leia somente o README.md e os testes desta kata. Explique uma estratégia para implementar a função solicitada em `src/solution.py`, incluindo as regras de aceitação e recusa, mas não altere arquivos.

## Resposta relevante

O Codex CLI recomendou percorrer os eventos uma única vez e manter estado
independente por remessa, seguindo a sequência fixa:

```text
COLETA → LACRE → DESPACHO → RECEBIMENTO
```

- Manter `estado_por_remessa`, que associa cada remessa à sua última etapa
  aceita, e listas `aceitos` e `recusados`.
- Para uma remessa sem etapa aceita, aceitar somente `COLETA`.
- Depois, aceitar exclusivamente a próxima etapa da sequência; após
  `RECEBIMENTO`, recusar qualquer evento posterior.
- Um evento recusado não altera o estado, permitindo que a próxima etapa
  correta ainda seja aceita depois.
- Gerar `pendentes` com as remessas cujo estado não é `RECEBIMENTO`, na ordem
  de primeira etapa aceita; a ordem de inserção do dicionário Python atende
  esse requisito.

O assistente destacou que devem ser recusados inícios fora de `COLETA`, etapas
repetidas, puladas ou fora da ordem, e eventos posteriores ao recebimento.
O retorno deve conter `aceitos`, `recusados` e `pendentes`.
