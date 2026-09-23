# Respostas preliminares às RQs

Gerado por `python scripts/run_analysis.py` a partir da alocação e dos dados brutos. Os resultados refletem somente os registros disponíveis neste checkout.

## Cobertura e qualidade

- Trials planejados: 18; trials válidos para RQ1/RQ2: 18.
- Pares definidos por participante e bloco de dificuldade; valores ausentes não foram imputados.
- Intervalos de 95% reamostram pares de forma exploratória, como nos relatórios individuais. Eles não corrigem a dependência entre blocos do mesmo participante.
- Os valores de p são Wilcoxon exato por permutação de sinais dos postos não nulos (empates em magnitude recebem postos médios). Com apenas três participantes, os pares do mesmo indivíduo não são independentes: os testes são exploratórios e podem sofrer pseudorreplicação.

### Ausências e ressalvas de origem

- P01-K01-ai: métricas estáticas ausentes
- P01-K03-manual: métricas estáticas ausentes
- P01-K06-ai: métricas estáticas ausentes
- P01-K02-manual: correção auditada por data-quality-note.json e poll registrado; bruto preservado
- P01-K02-manual: JUnit final registra 0/5 passando; análise usa 5/5 do poll documentado
- P01-K02-manual: métricas estáticas ausentes
- P01-K04-ai: métricas estáticas ausentes
- P01-K05-manual: métricas estáticas ausentes
- P02-K06-manual: métricas estáticas ausentes
- P02-K02-manual: métricas estáticas ausentes

## Resultados consolidados

Diferenças: RQ1 = Manual − IA; RQ2 = IA − Manual; RQ3 = IA − Manual. Valor positivo em RQ1/RQ2 favorece IA. Em RQ3 indica aumento com IA.

| RQ | Métrica | Manual: mediana [Q1; Q3] | IA: mediana [Q1; Q3] | Pares / empates / ausentes | Δ mediano | p | p Holm | r bisserial | IC 95% exploratório |
|---|---|---|---|---|---:|---:|---:|---:|---|
| RQ1 | `duration_seconds` (s) | 606.00 [485.00; 695.00] (n=9) | 261.00 [178.00; 316.00] (n=9) | 9 / 0 / 0 | 310.00 | 0.0098 | — | 0.87 | [-92.00; 549.00] |
| RQ2 | `success_rate` (%) | 100.00 [100.00; 100.00] (n=9) | 100.00 [100.00; 100.00] (n=9) | 9 / 9 / 0 | 0.00 | — | — | — | [0.00; 0.00] |
| RQ3 | `mean_cyclomatic_complexity` (points) | 8.00 [7.25; 9.00] (n=4) | 7.00 [7.00; 9.25] (n=6) | 4 / 0 / 5 | 2.00 | 0.7500 | 1.0000 | 0.20 | [-5.00; 4.00] |
| RQ3 | `duplication_percentage` (%) | 0.00 [0.00; 0.00] (n=4) | 0.00 [0.00; 0.00] (n=6) | 4 / 4 / 5 | 0.00 | — | — | — | [0.00; 0.00] |

## Resultados por participante

A tabela mostra a mediana das diferenças dos pares disponíveis em cada participante.

| Participante | RQ1: tempo (s) | RQ2: sucesso (p.p.) | RQ3: complexidade | RQ3: duplicação (p.p.) |
|---|---:|---:|---:|---:|
| P01 | 302.00 (n=3) | 0.00 (n=3) | — (n=0) | — (n=0) |
| P02 | 549.00 (n=3) | 0.00 (n=3) | 4.00 (n=1) | 0.00 (n=1) |
| P03 | -92.00 (n=3) | 0.00 (n=3) | 2.00 (n=3) | 0.00 (n=3) |

## Respostas objetivas

### RQ1 — Tempo

`duration_seconds`: Δ mediano 310.00, 9 pares, p=0.0098.

Nos pares disponíveis, o tempo foi menor com IA.
Sensibilidade por participante: `duration_seconds`: n=3, p=0.2500.
Conclusão observada: Manual 9, IA 9; censura: Manual 0, IA 0. O tempo de trials censurados é limitado a 2.100 s e não é o tempo real até conclusão.
Entre trials concluídos: mediana Manual 606.00 s (n=9), IA 261.00 s (n=9); análise condicionada ao sucesso, sujeita a viés de seleção.
Com apenas três participantes, esta é uma resposta preliminar; não há base para afirmar efeito causal geral nem equivalência entre tratamentos.

### RQ2 — Defeitos

`success_rate`: Δ mediano 0.00, 9 pares, p=—.

Não houve diferença mediana observada na taxa de sucesso dos pares disponíveis.
Sensibilidade por participante: `success_rate`: n=3, p=—.
A taxa de testes passando é o desfecho principal; testes falhando são complementares porque as katas têm quantidades diferentes de testes. Passar nos testes não demonstra ausência de defeitos.
Com apenas três participantes, esta é uma resposta preliminar; não há base para afirmar efeito causal geral nem equivalência entre tratamentos.

### RQ3 — Estrutura do código

`mean_cyclomatic_complexity`: Δ mediano 2.00, 4 pares, p=0.7500, p Holm=1.0000; `duplication_percentage`: Δ mediano 0.00, 4 pares, p=—.

A complexidade média apresentou diferença mediana de 2.00 ponto(s) e a duplicação de 0.00 ponto(s) percentual(is) com IA nos pares disponíveis; não é possível estabelecer um efeito estrutural geral.
Sensibilidade por participante: `mean_cyclomatic_complexity`: n=2, p=0.5000; `duplication_percentage`: n=2, p=—.
Complexidade e duplicação devem ser interpretadas junto com LOC. O Índice de Manutenibilidade é apenas exploratório. No ajuste de Holm dos dois testes pré-registrados, um p indefinido por empates totais conta como 1 apenas no cálculo; seu p bruto fica vazio.
LOC mediana: Manual 31.50 (n=4), IA 33.50 (n=6).
Há métricas estruturais ausentes em parte dos trials. Com apenas três participantes, esta é uma resposta preliminar; não há base para afirmar efeito causal geral nem equivalência entre tratamentos.

## Tabela para o dashboard

`data/processed/statistical-results.csv` contém linhas `treatment`, `participant_treatment`, `pair`, `comparison`, `participant_comparison` e `participant_level_comparison`. Valores ausentes são células vazias. Valores numéricos usam ponto decimal e quatro casas.
