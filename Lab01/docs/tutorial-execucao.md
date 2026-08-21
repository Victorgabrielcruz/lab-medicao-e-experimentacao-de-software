# Tutorial — Como Executar o Projeto do Zero

Este tutorial cobre o fluxo completo: coleta (C#) → pipeline de métricas
(Python) → validação → snapshot do board → testes. Os comandos assumem que
você está na raiz `Lab01/` do repositório.

Para detalhes de cada etapa, veja os documentos referenciados ao longo do
texto. Este arquivo é só o "passo a passo" operacional.

---

## 1. Pré-requisitos

| Ferramenta | Versão | Para quê |
|---|---|---|
| [.NET SDK](https://dotnet.microsoft.com/download) | 8.0 | Rodar o coletor (`src/collector`) |
| [Python](https://www.python.org/downloads/) | 3.10+ | Pipeline de métricas, validação e testes |
| Token do GitHub | classic, **sem nenhum scope** marcado | Autenticar a API GraphQL da coleta |
| Token do GitHub (separado) | classic, com escopo `read:project` | Só para o snapshot do board (`src/snapshots`) |

Gere os tokens em <https://github.com/settings/tokens>.

Verifique as instalações:

```bash
dotnet --version
python --version
```

---

## 2. Configurar o `.env`

Copie o exemplo e preencha os valores:

```bash
cd Lab01
cp .env.example .env      # no PowerShell: Copy-Item .env.example .env
```

Edite `.env` e ajuste, no mínimo:

```ini
GITHUB_TOKEN=ghp_seu_token_aqui
SEARCH_QUERY=stars:>10000 sort:stars-desc
PAGE_SIZE=10
TARGET_REPOS=1000
```

* **`PAGE_SIZE`**: já testado como 10. Valores como 20 e 25 causaram timeout do
  servidor do GitHub por causa dos campos aninhados da query — não aumente
  sem testar antes.
* **`TARGET_REPOS`**: 100 para uma amostra piloto rápida, 1000 para a amostra
  oficial (limite máximo que o `search` do GitHub devolve).
* **`PROJECT_OWNER`/`PROJECT_NUMBER`/`SPRINT`**: só são usados pelo script de
  snapshot do board (passo 6), exigem o segundo token com `read:project`.

**Nunca faça commit do `.env`** — ele já está no `.gitignore`; apenas o
`.env.example` é versionado.

---

## 3. Instalar as dependências Python

```bash
cd Lab01
python -m pip install -r requirements.txt
```

O coletor em C# não tem dependências externas além do próprio .NET SDK; o
`dotnet run` restaura o necessário automaticamente na primeira execução.

---

## 4. Rodar a coleta (C#)

```bash
cd Lab01
dotnet run --project src/collector
```

O que acontece:

* lê o `.env` na raiz do projeto (via `ProjectPaths.Discover()`);
* pagina a busca do GitHub por `endCursor`/`hasNextPage` até atingir
  `TARGET_REPOS` repositórios válidos, sem duplicar por `id`;
* grava logs em `logs/collect_<execução>.log`;
* grava uma resposta bruta por página em `data/raw/repos_raw_<coleta>_pNNN.json`;
* ao final, escreve `data/raw/repos_raw_<coleta>.csv` (uma linha por
  repositório).

**Se a coleta for interrompida** (erro fatal, queda de rede, Ctrl+C), rode o
mesmo comando de novo: existe um checkpoint em `data/raw/checkpoint.json` que
retoma a partir da última página confirmada, sem repetir requisições já
concluídas. O checkpoint é apagado automaticamente ao concluir com sucesso.

Erros fatais (token inválido, query malformada) interrompem a coleta com uma
mensagem clara no log; erros transitórios (rede, timeout, 5xx, rate limit)
são reenviados automaticamente, com backoff exponencial, até 4 tentativas.

Referência: `docs/raw-dataset.md` (schema do CSV bruto), `docs/methodology.md`
(seções 4 e 7).

---

## 5. Gerar o dataset processado (métricas RQ01–RQ06)

```bash
cd Lab01
python src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv
```

Sem argumento, o script usa o CSV bruto mais recente em `data/raw/`:

```bash
python src/analysis/build_processed_dataset.py
```

Isso gera:

```text
data/processed/repos_processed_<coleta>.csv   # base integrada RQ01–RQ06
data/processed/pilot_rq05_rq06.csv            # visão piloto de RQ05/RQ06
```

Referência: `docs/processed-dataset.md` (schema completo das colunas
derivadas).

---

## 6. Validar as métricas contra a base bruta

Rode as três validações (uma por par de RQs), sempre com o par bruto +
processado da **mesma coleta**:

```bash
cd Lab01

python src/metrics/rq01_rq02_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv

python src/metrics/rq03_rq04_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv

python src/metrics/rq05_rq06_validation.py \
  data/raw/repos_raw_<coleta>.csv \
  data/processed/repos_processed_<coleta>.csv
```

Cada comando:

* **não altera** nenhum dos CSVs de entrada;
* imprime um resumo no terminal (repositórios validados, inconsistências,
  outliers);
* gera evidências em `data/processed/validation_<par>_<coleta>.csv` e um
  relatório em `reports/drafts/validation_<par>_<coleta>.md`;
* retorna código de saída `0` (sem inconsistências) ou `1` (há
  inconsistências a revisar).

Guias detalhados: `docs/rq01-rq02-validation.md`, `docs/rq03-rq04-validation.md`
e `docs/rq05-rq06-validation.md`.

---

## 7. Gerar o snapshot do board (GitHub Projects)

Opcional, usado para evidenciar o andamento da sprint (task S01-05/S02-08).
Requer `PROJECT_OWNER`, `PROJECT_NUMBER` e um token com escopo `read:project`
no `.env`:

```bash
cd Lab01
python src/snapshots/snapshot_project.py Lab01S02
```

Gera `data/snapshots/snapshot_Lab01S02_<carimbo>.csv` sem sobrescrever
snapshots de sprints anteriores.

---

## 8. Rodar os testes automatizados

```bash
cd Lab01
python -m pip install -r requirements.txt   # se ainda não instalou
python -m unittest discover -s tests
```

Ou, se preferir `pytest` (também funciona, mesma suíte):

```bash
python -m pytest tests/ -q
```

Para rodar um teste específico:

```bash
python -m unittest tests.test_rq01_rq02_validation -v
```

---

## 9. Onde encontrar cada saída

| Etapa | Saída |
|---|---|
| Coleta | `data/raw/repos_raw_<coleta>.csv`, `data/raw/repos_raw_<coleta>_pNNN.json`, `logs/collect_<execução>.log` |
| Pipeline de métricas | `data/processed/repos_processed_<coleta>.csv`, `data/processed/pilot_rq05_rq06.csv` |
| Validação RQ01/RQ02 | `data/processed/validation_rq01_rq02_<coleta>.csv`, `reports/drafts/validation_rq01_rq02_<coleta>.md` |
| Validação RQ03/RQ04 | `data/processed/validation_rq03_rq04_<coleta>.csv`, `reports/drafts/validation_rq03_rq04_<coleta>.md` |
| Validação RQ05/RQ06 | `data/processed/validation_rq05_rq06_<coleta>.csv`, `reports/drafts/validation_rq05_rq06_<coleta>.md` |
| Qualidade dos dados | `reports/drafts/data_quality_<coleta>.md` |
| Snapshot do board | `data/snapshots/snapshot_<sprint>_<carimbo>.csv` |

---

## 10. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `401 token invalido ou expirado` | Token errado, expirado ou colado com espaço | Gerar outro token em `github.com/settings/tokens` e atualizar `GITHUB_TOKEN` no `.env` |
| Timeout na coleta com `PAGE_SIZE` alto | Query aninhada demais para o servidor do GitHub | Voltar `PAGE_SIZE` para 10 |
| Coleta reinicia do zero mesmo com `checkpoint.json` presente | Parâmetros do `.env` mudaram (`SEARCH_QUERY`, `PAGE_SIZE` ou `TARGET_REPOS`) desde o checkpoint | Esperado — a amostra mudaria; delete `data/raw/checkpoint.json` manualmente se quiser recomeçar de propósito |
| `o token nao tem o escopo read:project` no snapshot | Está usando o token da coleta (sem escopos) no script de snapshot | Gerar um segundo token com `read:project` só para `snapshot_project.py` |
| CSV abre errado no Excel (tudo em uma coluna) | Separador de listas do Windows em pt-BR é `;`, o CSV usa `,` | Usar Dados → Obter Dados → De Texto/CSV, escolhendo vírgula e UTF-8 (ver `docs/raw-dataset.md`) |
| Validação aponta inconsistência de data futura em RQ03/RQ04 | `collected_at` é fixado no início da coleta paginada; repositórios muito ativos podem receber push durante a execução | Comportamento esperado e documentado em `docs/methodology.md` (seção 5); não é erro de coleta |

---

## 11. Referências

* `README.md` — visão geral do projeto e estrutura de pastas.
* `docs/methodology.md` — metodologia completa de coleta e cálculo das RQs.
* `docs/raw-dataset.md` / `docs/processed-dataset.md` — schemas dos CSVs.
* `docs/rq01-rq02-validation.md`, `docs/rq03-rq04-validation.md`,
  `docs/rq05-rq06-validation.md` — manuais de validação por par de RQs.
* `docs/tasks.md` — plano de execução por sprint e critérios de aceitação.
