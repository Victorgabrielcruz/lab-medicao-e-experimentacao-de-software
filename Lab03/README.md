# Lab03 — Mineração de métricas DORA

Cálculo das quatro métricas DORA (deployment frequency, lead time, change failure rate e tempo de recuperação) a partir de dados públicos de repositórios open-source que usam GitHub Actions. A coleta é feita por script próprio sobre as APIs REST/GraphQL do GitHub, sem PyGithub.

## Como executar

Requer Python 3.11 ou superior.

```bash
cd Lab03
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GITHUB_TOKEN=<seu token>  # Windows (PowerShell): $env:GITHUB_TOKEN = "<seu token>"
python -m pipeline --config config.yaml
```

O token é lido apenas da variável de ambiente `GITHUB_TOKEN` e nunca deve ser versionado.

Testes:

```bash
pytest
```

## Estrutura

```text
Lab03/
├── config.yaml        # Parâmetros do pipeline
├── pipeline/          # Código do pipeline (entry point: python -m pipeline)
├── tests/             # Testes automatizados
└── data/              # Cache, dados brutos e processados (gerados pelo pipeline)
```

## Cronograma

| Sprint | Período |
|---|---|
| Lab03S01 | 08/10 a 14/10 |
| Lab03S02 | 15/10 a 21/10 |
| Lab03S03 | 22/10 a 28/10 |
| Entrega Final | 29/10 a 04/11 |

O acompanhamento das tarefas é feito no [GitHub Project](https://github.com/users/Victorgabrielcruz/projects/7). Todo commit deve referenciar o número da issue correspondente (ex.: `feat: ... (#N)`).
