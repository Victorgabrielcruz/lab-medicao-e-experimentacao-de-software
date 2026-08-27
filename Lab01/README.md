# GitHub Popular Repositories Analysis

## Sobre o projeto

Este projeto foi desenvolvido para a disciplina **Laboratório de Experimentação de Software** e tem como objetivo estudar características de sistemas open-source populares por meio da mineração dos **1.000 repositórios com maior número de estrelas no GitHub**.

Os dados serão coletados utilizando a **API GraphQL do GitHub** e posteriormente analisados para responder às questões de pesquisa propostas no laboratório.

## Escopo

O projeto analisará, de forma resumida:

- idade dos repositórios;
- quantidade de Pull Requests aceitas;
- quantidade de releases;
- frequência de atualização;
- linguagem primária;
- percentual de issues fechadas;
- relação entre linguagem, contribuição externa, releases e frequência de atualização.

Também fará parte do projeto:

- coleta automatizada através da API GraphQL;
- paginação para obtenção de 1.000 repositórios;
- armazenamento dos dados coletados;
- processamento das métricas;
- geração de arquivos CSV;
- análise dos resultados;
- geração de gráficos e visualizações;
- elaboração dos relatórios;
- snapshots do GitHub Projects ao final das sprints.

## Integrantes

| Integrante | GitHub |
|---|---|
| Víctor Gabriel Cruz Pereira | [@Victorgabrielcruz](https://github.com/Victorgabrielcruz)  |
| Jonathan Sena da Silva | [@JonathaDaSilva](https://github.com/JonathaDaSilva) |
| Matheus Fernandes de Oliveira | [@matheus-0063](https://github.com/matheus-0063) |


## Estrutura do projeto

- `src/github/` → consultas GraphQL versionadas (`src/github/queries/`);
- `src/collector/` → coletor em C# (.NET 8): paginação, resiliência e escrita do CSV bruto;
- `src/metrics/` → implementação e validação das métricas das questões de pesquisa;
- `src/analysis/` → pipeline de transformação (base processada);
- `src/snapshots/` → exportação do estado do GitHub Projects por sprint;
- `data/raw/` → dados brutos;
- `data/processed/` → dados processados;
- `data/snapshots/` → snapshots das sprints/GitHub Projects;
- `reports/drafts/` → versões preliminares dos relatórios;
- `reports/final/` → relatório final;
- `reports/figures/` → gráficos e visualizações;
- `tests/` → testes e validações.

## Como executar

Guia completo, passo a passo (pré-requisitos, `.env`, coleta, pipeline,
validação, snapshot do board, testes e troubleshooting):
**[`docs/tutorial-execucao.md`](docs/tutorial-execucao.md)**.

Resumo rápido:

```bash
cd Lab01
python3 -m pip install -r requirements.txt
cp .env.example .env                       # preencher GITHUB_TOKEN

dotnet run --project src/collector         # coleta -> data/raw/repos_raw_<coleta>.csv

python3 src/analysis/build_processed_dataset.py data/raw/repos_raw_<coleta>.csv

python3 src/metrics/rq01_rq02_validation.py data/raw/repos_raw_<coleta>.csv data/processed/repos_processed_<coleta>.csv
python3 src/metrics/rq03_rq04_validation.py data/raw/repos_raw_<coleta>.csv data/processed/repos_processed_<coleta>.csv
python3 src/metrics/rq05_rq06_validation.py data/raw/repos_raw_<coleta>.csv data/processed/repos_processed_<coleta>.csv

python3 -m unittest discover -s tests      # testes automatizados
```

Veja o schema e as regras de normalização em `docs/processed-dataset.md`.
