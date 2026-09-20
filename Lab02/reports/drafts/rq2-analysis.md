# RQ2 — Defeitos e taxa de sucesso

**Pergunta:** o tratamento com IA aumenta a taxa de sucesso dos testes de aceitação em relação ao manual?

**Resumo:** não há evidência estatística suficiente de diferença na direção esperada. Katas diferentes têm quantidades de teste distintas, então a taxa de sucesso (não a contagem bruta de testes) é a métrica primária.

## 1. Taxa de sucesso por tratamento (%)

| Tratamento | n | Mediana (%) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 100.00 | 100.00 | 100.00 | 0.00 | 100.00 | 100.00 | 0 |
| manual | 9 | 100.00 | 100.00 | 100.00 | 0.00 | 100.00 | 100.00 | 0 |

## 2. Testes falhando (métrica complementar, nunca substitui a taxa de sucesso)

| Tratamento | n | Mediana (testes) | Q1 | Q3 | IQR | Mínimo | Máximo | Ausentes |
|---|---|---|---|---|---|---|---|---|
| ai | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| manual | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |

## 3. Trials completamente verdes (success_rate = 100%)

| Tratamento | Trials | 100% verdes | % |
|---|---|---|---|
| ai | 9 | 9 | 100.00% |
| manual | 9 | 9 | 100.00% |

## 4. Comparação inferencial

### Wilcoxon unilateral (ai > manual)

- Pares válidos: 9 (ausentes: 0, empates/diferença zero: 9)
- Mediana das diferenças (manual - ai): 0.00 p.p.
- Estatística W: —
- p-valor (unilateral, ai > manual): —
- Tamanho de efeito (correlação bisserial de postos): —
- IC 95% (bootstrap, exploratório): [0.00, 0.00] p.p.

## 5. Pares participante × bloco

| Participante | Bloco | Trial IA | success_rate (ai) | Trial Manual | success_rate (manual) | Diferença |
|---|---|---|---|---|---|---|
| P01 | B1 | P01-K01-ai | 100.00 | P01-K02-manual | 100.00 | +0.00 |
| P01 | B2 | P01-K04-ai | 100.00 | P01-K03-manual | 100.00 | +0.00 |
| P01 | B3 | P01-K06-ai | 100.00 | P01-K05-manual | 100.00 | +0.00 |
| P02 | B1 | P02-K01-ai | 100.00 | P02-K02-manual | 100.00 | +0.00 |
| P02 | B2 | P02-K04-ai | 100.00 | P02-K03-manual | 100.00 | +0.00 |
| P02 | B3 | P02-K05-ai | 100.00 | P02-K06-manual | 100.00 | +0.00 |
| P03 | B1 | P03-K02-ai | 100.00 | P03-K01-manual | 100.00 | +0.00 |
| P03 | B2 | P03-K03-ai | 100.00 | P03-K04-manual | 100.00 | +0.00 |
| P03 | B3 | P03-K06-ai | 100.00 | P03-K05-manual | 100.00 | +0.00 |

## 6. Limitações

- Testes de aceitação são um proxy de qualidade funcional, não uma contagem completa de defeitos.
- Muitos trials atingem 100% de sucesso (efeito-teto): com pouca variação, o teste de postos perde poder para distinguir tratamentos.
- Nove pares de três participantes não são plenamente independentes; resultado exploratório (Seção 14.3).
