# Validação das RQ03 e RQ04

O script `src/metrics/rq03_rq04_validation.py` confere a base processada contra o
CSV bruto da mesma coleta. Ele não altera os datasets de entrada.

## Execução

```bash
cd Lab01
python3 src/metrics/rq03_rq04_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv
```

## Verificações

- igualdade de `releases_count`, `last_commit_date` e `total_commits` entre dados
  brutos e processados;
- `releases_no_teto` quando a contagem de releases chega a 1.000;
- cálculo de `days_since_last_commit` e `days_since_push`;
- cálculo de `development_period_days` com `created_at` como proxy documentado do
  primeiro commit;
- IDs divergentes, datas futuras e repositórios sem último commit;
- outliers por IQR em releases, commits e métricas temporais.

## Evidências

Para cada execução, são gerados:

```text
data/processed/validation_rq03_rq04_<coleta>.csv
reports/drafts/validation_rq03_rq04_<coleta>.md
```

Outliers são registrados para revisão, mas não removidos automaticamente. A rotina
deve ser executada primeiro para a amostra de 100 e novamente após a coleta oficial
de 1.000 repositórios.
