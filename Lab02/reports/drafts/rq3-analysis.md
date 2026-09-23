# RQ3 — Qualidade estrutural (complexidade e duplicação)

**Pergunta:** o tratamento com IA altera a complexidade e a duplicação do código, controlando o tamanho (LOC)?

**Resumo:** apenas 4 de 9 pares têm métricas estruturais nos dois lados (Seção 12: valores ausentes nunca viram zero); a amostra efetiva para RQ3 é pequena e os resultados abaixo são fortemente exploratórios.

## 1. LOC por tratamento (covariável de tamanho)

| Tratamento | n | Mediana (linhas) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 33.50 | 30.00 | 35.50 | 5.50 | 21.00 | 37.00 | 3 |
| manual | 9 | 31.50 | 29.25 | 34.25 | 5.00 | 27.00 | 38.00 | 5 |

## 2. Complexidade ciclomática média por tratamento

| Tratamento | n | Mediana (complexidade) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 7.00 | 7.00 | 9.25 | 2.25 | 5.00 | 12.00 | 3 |
| manual | 9 | 8.00 | 7.25 | 9.00 | 1.75 | 5.00 | 12.00 | 5 |

## 3. Duplicação por tratamento (%)

| Tratamento | n | Mediana (%) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 3 |
| manual | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 5 |

## 4. Índice de Manutenibilidade (exploratório, não é métrica principal)

| Tratamento | n | Mediana (MI) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 78.98 | 76.04 | 80.35 | 4.30 | 56.74 | 81.36 | 3 |
| manual | 9 | 63.60 | 57.06 | 70.94 | 13.88 | 56.24 | 74.15 | 5 |

## 5. Comparação inferencial (bilateral, ajustada por Holm)

A família pré-registrada contém dois testes. Quando todos os pares de um desfecho empatam, seu p bruto permanece indefinido; apenas para o ajuste de Holm ele é tratado como 1, preservando a família de dois testes.

### Complexidade ciclomática média

- Pares válidos: 4 (ausentes: 5, empates/diferença zero: 0)
- Mediana das diferenças (ai - manual): 2.00 pts
- Estatística W: 4.000
- p-valor (bilateral, bruto): 0.7500
- p-valor ajustado (Holm, 2 comparações): 1.0000
- Tamanho de efeito (correlação bisserial de postos): 0.200
- IC 95% (bootstrap, exploratório): [-5.00, 4.00] pts

### Duplicação

- Pares válidos: 4 (ausentes: 5, empates/diferença zero: 4)
- Mediana das diferenças (ai - manual): 0.00 p.p.
- Estatística W: —
- p-valor (bilateral, bruto): —
- p-valor ajustado (Holm, 2 comparações): —
- Tamanho de efeito (correlação bisserial de postos): —
- IC 95% (bootstrap, exploratório): [0.00, 0.00] p.p.

## 6. Pares participante × bloco (LOC, complexidade e duplicação lado a lado)

| Participante | Bloco | Trial IA | LOC (ai) | Complexidade (ai) | Duplicação % (ai) | Trial Manual | LOC (manual) | Complexidade (manual) | Duplicação % (manual) |
|---|---|---|---|---|---|---|---|---|---|
| P01 | B1 | P01-K01-ai | — | — | — | P01-K02-manual | — | — | — |
| P01 | B2 | P01-K04-ai | — | — | — | P01-K03-manual | — | — | — |
| P01 | B3 | P01-K06-ai | — | — | — | P01-K05-manual | — | — | — |
| P02 | B1 | P02-K01-ai | 21 | 5.00 | 0.00 | P02-K02-manual | — | — | — |
| P02 | B2 | P02-K04-ai | 33 | 12.00 | 0.00 | P02-K03-manual | 38 | 8.00 | 0.00 |
| P02 | B3 | P02-K05-ai | 34 | 7.00 | 0.00 | P02-K06-manual | — | — | — |
| P03 | B1 | P03-K02-ai | 36 | 7.00 | 0.00 | P03-K01-manual | 27 | 5.00 | 0.00 |
| P03 | B2 | P03-K03-ai | 29 | 7.00 | 0.00 | P03-K04-manual | 33 | 12.00 | 0.00 |
| P03 | B3 | P03-K06-ai | 37 | 10.00 | 0.00 | P03-K05-manual | 30 | 8.00 | 0.00 |

## 7. Limitações

- Métricas estruturais estão ausentes para vários trials manuais antigos (coleta retroativa incompleta); esses pares ficam fora dos testes de RQ3, reduzindo bastante a amostra efetiva.
- Código de teste, dependências e arquivos gerados não entram nas métricas (configuração de coleta em `radon.cfg`/`.jscpd.json`).
- LOC é reportado ao lado de toda comparação estrutural porque complexidade e duplicação absolutas tendem a crescer com o tamanho do código.
- O Índice de Manutenibilidade é exploratório: combina LOC, complexidade e comentários em uma única escala e não substitui as métricas primárias.
- Nove pares de três participantes não são plenamente independentes; resultado exploratório (Seção 14.3).
