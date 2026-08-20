# Base Bruta — saída do coletor

O coletor `src/collector` grava, para cada execução, um CSV em `data/raw/` com uma
linha por repositório e as respostas originais da API em JSON, uma por página.

```
data/raw/repos_raw_<coleta>.csv          uma linha por repositorio
data/raw/repos_raw_<coleta>_pNNN.json    resposta bruta de cada pagina
data/raw/checkpoint.json                 so existe durante uma coleta interrompida
```

Os JSON não são sobrescritos pelo processamento e servem de evidência da coleta,
conforme as seções 4 e 10 da `docs/methodology.md`. Eles também são o que permite
retomar uma coleta interrompida sem repetir requisição.

Este CSV é o contrato entre a coleta em C# e a análise em Python. Alterar uma
coluna aqui quebra `src/analysis/build_processed_dataset.py` e os módulos de
`src/metrics/`.

## Convenções de formato

Valem para todos os CSV do projeto, brutos e processados.

| item | valor |
|---|---|
| codificação | UTF-8 sem BOM |
| separador de campos | vírgula |
| separador decimal | ponto |
| datas | ISO 8601 em UTC, `2026-08-19T13:16:12Z` |
| booleanos | `true` e `false` em minúsculas |
| valor ausente | campo vazio, nunca `0`, `NA` ou `null` |
| aspas | apenas em campos que contêm vírgula |

A quebra de linha não faz parte do contrato: o coletor em C# grava CRLF no Windows
e o pandas segue o sistema operacional. Todo leitor de CSV aceita as duas formas.

Abrir o arquivo com duplo clique no Excel em português joga tudo na coluna A,
porque o separador de listas do Windows em pt-BR é ponto e vírgula. Use
Dados → Obter Dados → De Texto/CSV e escolha vírgula e UTF-8. O arquivo está
correto, o padrão do Excel é que difere.

## Colunas

| coluna | tipo | origem na query | usada em |
|---|---|---|---|
| `id` | texto | `id` | chave única do repositório |
| `name_with_owner` | texto | `nameWithOwner` | identificação |
| `url` | texto | `url` | conferência manual |
| `owner` | texto | `owner.login` | identificação |
| `stargazer_count` | inteiro | `stargazerCount` | critério da amostra |
| `is_archived` | booleano | `isArchived` | segmentação |
| `collected_at` | data | data de referência da execução | RQ01, RQ04 |
| `created_at` | data | `createdAt` | RQ01, RQ04 |
| `merged_pull_requests` | inteiro | `mergedPullRequests.totalCount` | RQ02 |
| `total_pull_requests` | inteiro | `totalPullRequests.totalCount` | RQ02 |
| `releases_count` | inteiro | `releases.totalCount` | RQ03 |
| `updated_at` | data | `updatedAt` | controle |
| `pushed_at` | data | `pushedAt` | RQ04 |
| `default_branch` | texto | `defaultBranchRef.name` | RQ04 |
| `total_commits` | inteiro | `lastCommit.totalCount` | RQ04 |
| `last_commit_date` | data | `lastCommit.nodes[0].committedDate` | RQ04 |
| `primary_language` | texto | `primaryLanguage.name` | RQ05, RQ07 |
| `open_issues` | inteiro | `openIssues.totalCount` | RQ06 |
| `closed_issues` | inteiro | `closedIssues.totalCount` | RQ06 |

Todas as linhas da mesma execução têm o mesmo `collected_at`. Ele é a data de
referência usada em todas as métricas temporais e é preservado quando uma coleta
interrompida é retomada, para que o arquivo não misture bases de tempo.

## Campos que vêm vazios

| coluna | quando | quantos na coleta de 1000 |
|---|---|---|
| `primary_language` | listas curadas, coletâneas de links, material de estudo | 87 |
| `default_branch`, `total_commits`, `last_commit_date` | repositório sem branch padrão | 0 |

Vazio não vira zero em nenhum caso. Ausência de commits não é o mesmo que zero
commits, e o processamento precisa distinguir os dois.

## Limitações conhecidas

`releases_count` é truncado em 1000 pela API. Repositórios no teto têm o valor
real desconhecido, e o processamento marca esses casos em `releases_no_teto`.

A data do primeiro commit não é obtida: `history(last: 1)` é recusado pela API por
exigir cursor `before`. O período de desenvolvimento usa `created_at` como
aproximação do início.

O `search` do GitHub devolve no máximo 1000 resultados, então a amostra não pode
passar disso e cada duplicata descartada é uma vaga que não dá para repor.

## Validação

`tests/test_csv_format.py` verifica codificação, separador, cabeçalho, tipos,
formato de data e unicidade de `id` em todos os CSV presentes em `data/`.

```bash
python3 -m unittest discover -s tests
```
