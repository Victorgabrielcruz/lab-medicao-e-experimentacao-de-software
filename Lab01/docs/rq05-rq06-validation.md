# Validação das RQ05 e RQ06

O script `src/metrics/rq05_rq06_validation.py` compara o CSV bruto e o dataset
processado da mesma coleta. Ele não altera os arquivos de entrada.

## Execução

```bash
cd Lab01
python3 src/metrics/rq05_rq06_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv
```

## Verificações

- preservação de `primary_language`, `open_issues` e `closed_issues`;
- normalização da linguagem e classificação como popular;
- soma de issues, indicador `has_issues` e percentual de issues fechadas;
- percentual limitado ao intervalo de 0 a 100;
- repositórios sem linguagem e sem issues, registrados como observações válidas;
- IDs divergentes entre as bases.

Para cada execução, são gerados um CSV de evidências em `data/processed/` e um
relatório em `reports/drafts/`. A rotina deve ser executada para a amostra atual
e novamente quando a coleta completa de 1.000 repositórios estiver disponível.
