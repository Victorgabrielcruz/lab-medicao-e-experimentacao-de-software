# Relatório de validação do dataset — S03-01

Gerado em 2026-09-19T21:29:13-03:00 a partir de `data\processed\trials.csv`.

## Veredito: AUTORIZADO para as análises de RQ1-RQ3

- Linhas no dataset: 18
- Pares participante × bloco válidos: 9/9
- Achados críticos: 0
- Avisos (lacunas conhecidas e toleradas): 28
- Observações (outliers preservados): 1

## 1. Erros críticos

Qualquer achado nesta seção interrompe a autorização do dataset para a análise das RQs.

_Nenhum achado nesta categoria._

## 2. Dados ausentes e avisos

Lacunas previstas e toleradas pela metodologia (Seção 12): campos não aplicáveis permanecem vazios e nunca são preenchidos artificialmente com zero.

| Regra | Trial | Mensagem |
|---|---|---|
| `missing_perceived_difficulty` | P01-K01-ai | Dificuldade percebida não registrada. |
| `missing_prompt_count` | P01-K01-ai | Log de prompts não exportável para o tratamento IA. |
| `missing_structural_metrics` | P01-K03-manual | Métricas estruturais (LOC/complexidade/duplicação) ausentes. |
| `missing_perceived_difficulty` | P01-K03-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P01-K06-ai | Dificuldade percebida não registrada. |
| `missing_prompt_count` | P01-K06-ai | Log de prompts não exportável para o tratamento IA. |
| `missing_structural_metrics` | P01-K02-manual | Métricas estruturais (LOC/complexidade/duplicação) ausentes. |
| `missing_perceived_difficulty` | P01-K02-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P01-K04-ai | Dificuldade percebida não registrada. |
| `missing_prompt_count` | P01-K04-ai | Log de prompts não exportável para o tratamento IA. |
| `missing_structural_metrics` | P01-K05-manual | Métricas estruturais (LOC/complexidade/duplicação) ausentes. |
| `missing_perceived_difficulty` | P01-K05-manual | Dificuldade percebida não registrada. |
| `missing_structural_metrics` | P02-K06-manual | Métricas estruturais (LOC/complexidade/duplicação) ausentes. |
| `missing_perceived_difficulty` | P02-K06-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P02-K04-ai | Dificuldade percebida não registrada. |
| `missing_prompt_count` | P02-K04-ai | Log de prompts não exportável para o tratamento IA. |
| `missing_structural_metrics` | P02-K02-manual | Métricas estruturais (LOC/complexidade/duplicação) ausentes. |
| `missing_perceived_difficulty` | P02-K02-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P02-K05-ai | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P02-K03-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P02-K01-ai | Dificuldade percebida não registrada. |
| `missing_prompt_count` | P02-K01-ai | Log de prompts não exportável para o tratamento IA. |
| `missing_perceived_difficulty` | P03-K03-ai | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P03-K01-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P03-K04-manual | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P03-K06-ai | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P03-K02-ai | Dificuldade percebida não registrada. |
| `missing_perceived_difficulty` | P03-K05-manual | Dificuldade percebida não registrada. |

## 3. Outliers identificados

Valores extremos são reportados e mantidos; nenhum é removido automaticamente.

| Regra | Trial | Mensagem |
|---|---|---|
| `outlier_detected` | P02-K02-manual | 'duration_seconds'=1191 fora de [-374.12, 1146.88] (IQR); mantido sem remoção automática. |

## 4. Pares válidos por participante e bloco de dificuldade

| Participante | Bloco | Trial IA | Trial Manual | Válido |
|---|---|---|---|---|
| P01 | B1 | P01-K01-ai | P01-K02-manual | Sim |
| P01 | B2 | P01-K04-ai | P01-K03-manual | Sim |
| P01 | B3 | P01-K06-ai | P01-K05-manual | Sim |
| P02 | B1 | P02-K01-ai | P02-K02-manual | Sim |
| P02 | B2 | P02-K04-ai | P02-K03-manual | Sim |
| P02 | B3 | P02-K05-ai | P02-K06-manual | Sim |
| P03 | B1 | P03-K02-ai | P03-K01-manual | Sim |
| P03 | B2 | P03-K03-ai | P03-K04-manual | Sim |
| P03 | B3 | P03-K06-ai | P03-K05-manual | Sim |
