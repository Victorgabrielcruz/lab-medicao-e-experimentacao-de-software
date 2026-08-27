# Validação da RQ07

O script `src/analysis/rq07_validation.py` confere os artefatos gerados por
`src/analysis/rq07_analysis.py` contra o dataset consolidado da RQ07
(`repos_rq07_consolidated_<coleta>.csv`), sem alterar nenhum dos arquivos de
entrada. Segue o mesmo padrão de `rq01_rq02_validation.py`,
`rq03_rq04_validation.py` e `rq05_rq06_validation.py`.

## Execução

```bash
cd Lab01
python src/analysis/rq07_validation.py \
  data/processed/repos_rq07_consolidated_<coleta>.csv \
  data/processed/rq07_statistics_<coleta>.csv
```

O caminho do CSV de outliers (`rq07_analysis_outliers_<coleta>.csv`) é
derivado automaticamente do CSV de estatísticas informado; não é necessário
passá-lo como argumento.

### Saída esperada no terminal

```
Repositórios analisados: 1000
Inconsistências: 0
Sem linguagem: 87
Outliers recalculados: <n>
Evidências: data/processed/validation_rq07_<coleta>.csv
Relatório: reports/drafts/validation_rq07_<coleta>.md
```

* **Código de saída `0`**: nenhuma inconsistência encontrada.
* **Código de saída `1`**: existem inconsistências — confira o CSV/relatório
  gerados para saber quais.

## O que o script verifica

O script reproduz, a partir do dataset consolidado, a mesma função `analyze`
usada por `rq07_analysis.py` (estatísticas de grupo, correlações e outliers) e
compara o resultado recalculado com os artefatos já gravados em disco:

| Verificação | Regra |
|---|---|
| Estatísticas de grupo | `n`, `media`, `mediana`, `q1` e `q3` de cada métrica (`accepted_pull_requests`, `releases_count`, `days_since_push`) por categoria de linguagem (`Popular`/`Não popular`) reproduzem `rq07_statistics_<coleta>.csv` |
| Correlações | `n`, `pearson` e `spearman` entre `stargazer_count` e cada métrica de RQ01–RQ06 reproduzem o mesmo artefato |
| Outliers | os pares `(id, métrica)` recalculados por IQR (cercas de Tukey) reproduzem `rq07_analysis_outliers_<coleta>.csv`, sem casos ausentes nem adicionais |
| Consistência de `id` | todo `id` sinalizado como outlier existe no dataset consolidado; IDs duplicados no consolidado interrompem a validação com erro |

Assim como nas demais validações, nenhuma regra de métrica é reimplementada
aqui — o script reaproveita `analyze()` de `src/analysis/rq07_analysis.py`.

## Evidências

Para cada execução, são gerados:

```text
data/processed/validation_rq07_<coleta>.csv
reports/drafts/validation_rq07_<coleta>.md
```

Cada linha do CSV é uma inconsistência (`record_type = inconsistency`), com
colunas `id`, `name_with_owner`, `field`, `expected`, `actual` e `detail`. O
relatório em Markdown resume as contagens e as regras aplicadas.

## Uso no pipeline único

`scripts/run_pipeline.py` (task S03-06) já executa esta validação
automaticamente, na sequência: `consolidate_rq07_dataset.py` →
`rq07_analysis.py` → `rq07_validation.py`. Uma inconsistência crítica aqui
interrompe o pipeline, no mesmo padrão das validações de RQ01–RQ06.

## Rodando os testes automatizados

```bash
cd Lab01
python -m unittest tests.test_rq07_validation -v
```

Ou a suíte inteira do projeto:

```bash
python -m unittest discover -s tests
```

## Referências

* `docs/methodology.md` — seção 9 (RQ07 e as métricas de RQ01–RQ06 que a compõem).
* `docs/processed-dataset.md` — schema das colunas derivadas usadas pela RQ07.
* `docs/rq01-rq02-validation.md`, `docs/rq03-rq04-validation.md`,
  `docs/rq05-rq06-validation.md` — manuais de validação das demais RQs, no mesmo padrão.
* `docs/tasks.md` — task S03-02 (análise da RQ07) e S03-06 (pipeline único).
