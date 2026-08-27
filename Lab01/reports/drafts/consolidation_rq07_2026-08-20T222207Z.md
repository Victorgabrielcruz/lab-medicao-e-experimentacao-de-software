# Consolidação do dataset para a RQ07

- Base processada de origem: `repos_processed_2026-08-20T222207Z.csv`
- Base consolidada gerada: `repos_rq07_consolidated_2026-08-20T222207Z.csv`
- Repositórios: **1000**
- Status: **PRONTA para a análise da RQ07**
- IDs duplicados: **0**
- Colunas obrigatórias ausentes: **0**
- Repositórios sem linguagem primária: **87**
- Repositórios sem issues: **43**

## Valores ausentes por coluna (esperados, documentados)

- `days_since_last_commit`: 0
- `days_since_push`: 0
- `development_period_days`: 0
- `closed_issues_percentage`: 43

Os valores ausentes acima são esperados e documentados em `docs/dataset/raw-dataset.md` e `docs/methodology.md`: repositórios sem commit/push não têm métricas temporais de atividade e repositórios sem issues não têm `closed_issues_percentage`. Nenhum valor ausente foi convertido em zero.

Este dataset reaproveita as métricas já validadas em `docs/validation/rq01-rq02-validation.md`, `docs/validation/rq03-rq04-validation.md` e `docs/validation/rq05-rq06-validation.md`, sem recalcular nenhuma regra de métrica.
