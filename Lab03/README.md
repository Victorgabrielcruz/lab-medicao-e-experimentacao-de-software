# Lab03 — Mineração de métricas DORA

[![Lab03 CI](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml/badge.svg?branch=main)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml)

Cálculo das quatro métricas DORA (deployment frequency, lead time, change failure rate e tempo de recuperação) a partir de dados públicos de repositórios open-source que usam GitHub Actions. A coleta é feita por script próprio sobre as APIs REST/GraphQL do GitHub, sem PyGithub.

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/definicoes-operacionais.md`](docs/definicoes-operacionais.md) | Janela de observação, definição de deploy, regras de runs, critério de inclusão, filtro de Actions, metadados e tabela de classificação DORA (C1) |

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

Para executar só algumas etapas: `python -m pipeline --config config.yaml --etapas metadados`.

### Cache e retomada (S01-16)

As respostas GET da API são salvas em JSON em `caminhos.cache` (padrão:
`data/cache`), separadas por API e repositório. Cada endpoint, combinação de
parâmetros e página tem sua própria entrada, inclusive na Search API. Os headers
necessários à paginação (`Link`) são preservados; o token e os headers de
autenticação não são gravados.

Se a coleta falhar, execute novamente o mesmo comando: as consultas já
concluídas são lidas do disco e as demais voltam à API. A gravação usa um arquivo
temporário e substituição atômica para evitar JSON parcial. Erros HTTP e buscas
com `incomplete_results` não são armazenados; entradas de resposta corrompidas
geram aviso e são consultadas novamente. O cache de metadados já existente é
mantido e também usa gravação atômica.

O cache não expira automaticamente. Para atualizar dados ou alterar a janela de
observação, limpe-o antes de iniciar uma nova coleta:

```bash
python -m pipeline --config config.yaml --limpar-cache
python -m pipeline --config config.yaml
```

O primeiro comando remove apenas os JSON das áreas `respostas/` e `metadados/`
do cache configurado e encerra, sem exigir token nem acessar a API. Os dados
brutos e processados são preservados. O cache local não é versionado no Git.

### Etapas

| Etapa | Saída | Descrição |
|---|---|---|
| `candidatos` | `data/raw/candidatos.json` | Busca pela Search API (seção `busca` do `config.yaml`). A faixa de estrelas é dividida ao meio até cada consulta ter no máximo 1000 resultados; faixas indivisíveis acima do limite são marcadas como truncadas e geram alerta. Duplicatas são removidas pelo id do repositório. |
| `actions` | `data/raw/actions.json` | Lê `candidatos.json` e consulta o endpoint de workflows de cada repositório. Descarta os que não têm nenhum workflow em `.github/workflows/` (workflows dinâmicos do GitHub, como Dependabot e CodeQL, não contam) e os que respondem 404 ou 451. Os descartes ficam no arquivo com o motivo, para o funil de seleção. |
| `metadados` | `data/raw/metadados.json` | Lê os aprovados de `actions.json` e coleta estrelas, linguagem, idade (até o fim da janela), default branch e número de contribuidores (Link header com `per_page=1&anon=1`). Cada repositório é salvo em `data/cache/metadados/`; numa reexecução, os que já estão lá não são consultados de novo. |

Testes:

```bash
pytest --cov=pipeline --cov-fail-under=80
```

O workflow [`lab03-ci.yml`](../.github/workflows/lab03-ci.yml) roda esse mesmo comando a cada push e pull request, em Python 3.11 e 3.13. O build falha se algum teste falhar ou se a cobertura ficar abaixo de 80%.

## Estrutura

```text
Lab03/
├── artigo/            # Seções do artigo em LaTeX (template SBC) e referências
├── config.yaml        # Parâmetros do pipeline (janela, critérios, caminhos)
├── docs/              # Definições operacionais e documentação
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
