# RQ1 — Tempo de resolução e conclusão

**Pergunta:** o tratamento com IA reduz o tempo de resolução em relação ao manual?

**Resumo:** há evidência exploratória de tempo menor com IA (p < 0,05). Com apenas 3 participantes e 9 pares, o resultado é tratado como evidência exploratória, não conclusiva (Seção 14.3).

## 1. Estatística descritiva (duration_seconds, em segundos)

| Tratamento | n | Mediana | Q1 | Q3 | IQR | Mínimo | Máximo | Concluídos | Ausentes |
|---|---|---|---|---|---|---|---|---|---|
| ai | 9 | 261 | 178 | 316 | 138 | 57 | 384 | 9 (100.00%) | 0 |
| manual | 9 | 606 | 485 | 695 | 210 | 75 | 1191 | 9 (100.00%) | 0 |

## 2. Censura

Trials sem sucesso dentro do limite permanecem com 2.100 segundos e `censored=true`; esse valor é usado no teste de postos, mas não representa o tempo real necessário (Seção 14.4).

| Tratamento | Trials | Censurados | % censurados |
|---|---|---|---|
| ai | 9 | 0 | 0.00% |
| manual | 9 | 0 | 0.00% |

## 3. Comparação inferencial — todos os pares (censurados incluídos)

### Wilcoxon unilateral (manual > ai)

- Pares válidos: 9 (ausentes: 0, empates/diferença zero: 0)
- Mediana das diferenças (manual - ai): 310.0 s
- Estatística W: 42.000
- p-valor (unilateral, manual > ai): 0.0098
- Tamanho de efeito (correlação bisserial de postos): 0.867
- IC 95% (bootstrap, exploratório) da mediana das diferenças: [-92.0, 549.0] s

## 4. Análise de sensibilidade — apenas trials concluídos

Exclui qualquer par em que ao menos um lado não tenha concluído dentro do limite. Amostra menor e **condicionada ao sucesso**: sujeita a viés de seleção, não deve ser lida isoladamente (Seção 14.4).

### Wilcoxon unilateral, apenas concluídos

- Pares válidos: 9 (ausentes: 0, empates/diferença zero: 0)
- Mediana das diferenças (manual - ai): 310.0 s
- Estatística W: 42.000
- p-valor (unilateral, manual > ai): 0.0098
- Tamanho de efeito (correlação bisserial de postos): 0.867
- IC 95% (bootstrap, exploratório) da mediana das diferenças: [-92.0, 549.0] s

## 5. Pares participante × bloco (análise principal)

| Participante | Bloco | Trial IA | duration (ai) | Trial Manual | duration (manual) | Diferença |
|---|---|---|---|---|---|---|
| P01 | B1 | P01-K01-ai | 363 | P01-K02-manual | 885 | +522 |
| P01 | B2 | P01-K04-ai | 384 | P01-K03-manual | 686 | +302 |
| P01 | B3 | P01-K06-ai | 281 | P01-K05-manual | 485 | +204 |
| P02 | B1 | P02-K01-ai | 316 | P02-K02-manual | 1191 | +875 |
| P02 | B2 | P02-K04-ai | 57 | P02-K03-manual | 606 | +549 |
| P02 | B3 | P02-K05-ai | 261 | P02-K06-manual | 695 | +434 |
| P03 | B1 | P03-K02-ai | 178 | P03-K01-manual | 488 | +310 |
| P03 | B2 | P03-K03-ai | 251 | P03-K04-manual | 107 | -144 |
| P03 | B3 | P03-K06-ai | 167 | P03-K05-manual | 75 | -92 |

## 6. Limitações

- Três participantes geram nove pares não plenamente independentes (pseudorreplicação); o teste é evidência exploratória, não prova estatística formal.
- A análise de sensibilidade tem amostra menor e viés de seleção por depender da conclusão.
- O valor de `p` não é interpretado isoladamente (Seção 14.6): direção, magnitude, IQR e tamanho de efeito compõem a resposta.
