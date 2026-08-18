# Base Processada — RQs 01 a 06

O pipeline `src/analysis/build_processed_dataset.py` recebe o CSV bruto gerado pelo
coletor e produz uma única base padronizada para validação e análise das RQs 01–06.

## Execução

```bash
cd Lab01
python3 -m pip install -r requirements.txt
python3 src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv
```

Sem argumento, o script seleciona o CSV bruto mais recente em `data/raw/`. Para
escolher o arquivo de saída explicitamente:

```bash
python3 src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv \
  --output data/processed/repos_processed_<coleta>.csv
```

Para rodar os testes:

```bash
python3 -m unittest discover -s tests
```

## Entrada e saída

A entrada deve conter os campos brutos do coletor: identificação, estrelas, datas,
Pull Requests, releases, commits, linguagem e Issues. A saída preserva esses campos
normalizados e acrescenta:

| RQ | Colunas derivadas |
|---|---|
| RQ01 | `age_years` |
| RQ02 | `accepted_pull_requests` |
| RQ03 | `releases_no_teto` |
| RQ04 | `days_since_last_commit`, `days_since_push`, `development_period_days` |
| RQ05 | `is_popular_language` |
| RQ06 | `total_issues`, `has_issues`, `closed_issues_percentage` |

As datas são convertidas para UTC e gravadas em ISO 8601. Linguagem ausente é
normalizada como `Sem linguagem identificada`. Repositórios sem Issues recebem
`has_issues = false` e percentual fechado vazio.

O pipeline remove registros duplicados pelo `id`, valida números negativos e rejeita
datas inválidas. Para o mesmo CSV de entrada e a mesma versão do código, o CSV de
saída é determinístico e pode ser reexecutado sem alterar os dados brutos.
