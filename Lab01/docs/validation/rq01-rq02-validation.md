# Manual de Uso — Validação das RQ01 e RQ02

Este manual explica, passo a passo, como testar manualmente o script
`src/metrics/rq01_rq02_validation.py`, responsável por validar as métricas de
idade do repositório (RQ01) e Pull Requests aceitas (RQ02).

O script compara a base processada com o CSV bruto da mesma coleta e **não
altera nenhum dos dois arquivos** — ele só lê e gera evidências novas.

---

## 1. Pré-requisitos

* Python 3 instalado.
* Dependências do projeto instaladas:

```bash
cd Lab01
python -m pip install -r requirements.txt
```

* Um CSV bruto de coleta em `data/raw/`, no formato `repos_raw_<coleta>.csv`
  (veja `docs/dataset/raw-dataset.md` para o schema).
* O CSV processado correspondente em `data/processed/`, no formato
  `repos_processed_<coleta>.csv`. Se ainda não existir, gere com o pipeline:

```bash
python src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv
```

---

## 2. Executando a validação

```bash
cd Lab01
python src/metrics/rq01_rq02_validation.py ^
  data/raw/repos_raw_<coleta>.csv ^
  data/processed/repos_processed_<coleta>.csv
```

(No PowerShell/Linux, use `\` ou coloque tudo em uma linha só; o `^` acima é
só para quebra de linha no `cmd.exe`.)

### Saída esperada no terminal

```
Repositórios validados: 1000
Inconsistências: 0
Outliers registrados: 124
Evidências: data/processed/validation_rq01_rq02_<coleta>.csv
Relatório: reports/drafts/validation_rq01_rq02_<coleta>.md
```

* **Código de saída `0`**: nenhuma inconsistência crítica encontrada.
* **Código de saída `1`**: existem inconsistências — confira o CSV/relatório
  gerados para saber quais.

---

## 3. O que o script verifica

| Verificação | Regra |
|---|---|
| Completude | `created_at`, `collected_at`, `age_years` e `accepted_pull_requests` não podem estar vazios |
| Faixa de valores da idade | `age_years >= 0` e `created_at` não pode ser anterior a 2008-04-10 (fundação do GitHub) |
| Fórmula de `age_years` | reproduz `(collected_at − created_at) / 365.25 dias` a partir das datas brutas e compara com o valor processado |
| Pull Requests `MERGED` | `accepted_pull_requests` deve ser igual a `merged_pull_requests` do bruto |
| Faixa de PRs | `accepted_pull_requests` nunca pode ser maior que `total_pull_requests`, nem negativo |
| Consistência de `id` | todo repositório do bruto deve existir no processado e vice-versa |
| Outliers | valores fora do intervalo IQR em `age_years` e `accepted_pull_requests` são **registrados**, nunca removidos |

---

## 4. Onde conferir os resultados

### 4.1 Evidência em CSV

`data/processed/validation_rq01_rq02_<coleta>.csv`

Cada linha é uma inconsistência (`record_type = inconsistency`) ou um outlier
(`record_type = outlier`), com colunas `id`, `name_with_owner`, `field`,
`expected`, `actual` e `detail`. Se o arquivo tiver só o cabeçalho, não há
nada a corrigir.

### 4.2 Relatório em Markdown

`reports/drafts/validation_rq01_rq02_<coleta>.md`

Contém:
* contagem de repositórios validados, inconsistências e outliers;
* as regras aplicadas;
* uma **amostra fixa de 10 repositórios** (sempre a mesma, seed 42) com idade,
  PRs aceitas, PRs merged e PRs totais — use essa tabela para a "conferência
  manual" pedida pela task, comparando alguns desses repositórios diretamente
  no GitHub, se quiser.

---

## 5. Testando com dados pequenos (sem precisar da coleta completa)

Se quiser testar rápido sem esperar uma coleta de 1.000 repositórios, crie
dois CSVs mínimos:

**`raw_teste.csv`**
```csv
id,name_with_owner,url,owner,stargazer_count,is_archived,collected_at,created_at,merged_pull_requests,total_pull_requests,releases_count,updated_at,pushed_at,default_branch,total_commits,last_commit_date,primary_language,open_issues,closed_issues
1,owner/repo,https://github.com/owner/repo,owner,100,false,2025-01-01T00:00:00Z,2015-01-01T00:00:00Z,40,50,5,2025-01-01T00:00:00Z,2025-01-01T00:00:00Z,main,200,2025-01-01T00:00:00Z,Python,10,20
```

Gere o processado e rode a validação:

```bash
python src/analysis/build_processed_dataset.py raw_teste.csv --output processado_teste.csv
python src/metrics/rq01_rq02_validation.py raw_teste.csv processado_teste.csv
```

Para simular um erro, edite `processado_teste.csv` e troque o valor de
`age_years` ou `accepted_pull_requests` por algo errado — o script deve
retornar `Inconsistências: 1` (ou mais) e código de saída `1`.

---

## 6. Rodando os testes automatizados

```bash
cd Lab01
python -m unittest tests.test_rq01_rq02_validation -v
```

Ou a suíte inteira do projeto:

```bash
python -m unittest discover -s tests
```

---

## 7. Referências

* `docs/methodology.md` — seção 9 (fórmulas de RQ01 e RQ02).
* `docs/dataset/processed-dataset.md` — schema da base processada.
* `docs/dataset/raw-dataset.md` — schema do CSV bruto.
* `docs/tasks.md` — task S02-04, com o resultado da última execução completa.
