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
| Víctor Gabriel Cruz Pereira | @Victorgabrielcruz |
| Jonathan Sena da Silva | @github |
| Matheus Fernandes de Oliveira | @github |


## Estrutura do projeto

- `src/github/` → integração com a API GraphQL do GitHub;
- `src/collectors/` → coleta e paginação dos repositórios;
- `src/metrics/` → implementação das métricas das questões de pesquisa;
- `src/analysis/` → análise dos resultados;
- `data/raw/` → dados brutos;
- `data/processed/` → dados processados;
- `data/snapshots/` → snapshots das sprints/GitHub Projects;
- `reports/drafts/` → versões preliminares dos relatórios;
- `reports/final/` → relatório final;
- `reports/figures/` → gráficos e visualizações;
- `tests/` → testes e validações.
