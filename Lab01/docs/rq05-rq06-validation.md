# Validação das RQ05 e RQ06

O script `src/metrics/rq05_rq06_validation.py` confere a base processada contra o
CSV bruto da mesma coleta. Ele não altera os datasets de entrada.

## Execução

```bash
cd Lab01
python3 src/metrics/rq05_rq06_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv
```

### Saída esperada no terminal

```
Repositórios validados: 1000
Inconsistências: 0
Sem linguagem: 87
Sem issues: 43
Evidências: data/processed/validation_rq05_rq06_<coleta>.csv
Relatório: reports/drafts/validation_rq05_rq06_<coleta>.md
```

* **Código de saída `0`**: nenhuma inconsistência encontrada.
* **Código de saída `1`**: existem inconsistências — confira o CSV/relatório
  gerados para saber quais.

## Verificações

O script reproduz, a partir dos dados brutos, as mesmas funções usadas em
`src/metrics/rq05_rq06_language_issues.py` (`normalize_language`,
`is_popular_language`, `closed_issues_percentage`) e compara com o valor
gravado no processado:

- `language_group` é igual à normalização de `primary_language` (nulo/vazio
  vira `Sem linguagem identificada`);
- `is_popular_language` é igual à checagem contra a lista do Octoverse 2025,
  sem diferenciar maiúsculas de minúsculas;
- `total_issues` é igual a `open_issues + closed_issues`;
- `has_issues` é `false` quando `total_issues` é zero, e `true` caso contrário;
- `closed_issues_percentage` reproduz `closed_issues / total_issues × 100`,
  vazio (nunca `0` nem `100`) quando não há issues;
- consistência de `id` entre bruto e processado.

Não há outliers estatísticos (IQR) nesta validação: RQ05/RQ06 são
categóricas/percentuais e o próprio percentual já é limitado a 0–100, então a
verificação relevante é de divergência de fórmula, não de valores extremos.

## Evidências

Para cada execução, são gerados:

```text
data/processed/validation_rq05_rq06_<coleta>.csv
reports/drafts/validation_rq05_rq06_<coleta>.md
```

Cada linha do CSV é uma inconsistência (`record_type = inconsistency`) ou uma
observação registrada (`record_type = observation`, por exemplo linguagem
ausente ou repositório sem issues), com colunas `id`, `name_with_owner`,
`field`, `expected`, `actual` e `detail`. O relatório em Markdown resume as
contagens e as regras aplicadas.

## Rodando os testes automatizados

```bash
cd Lab01
python -m unittest tests.test_rq05_rq06_validation -v
```

Ou a suíte inteira do projeto:

```bash
python -m unittest discover -s tests
```

## Referências

* `docs/methodology.md` — seção 9 (fórmulas de RQ05 e RQ06).
* `docs/processed-dataset.md` — schema da base processada.
* `docs/raw-dataset.md` — schema do CSV bruto.
* `docs/tasks.md` — task S02-06, com o resultado da última execução completa.
