# Índice da documentação — Lab01

Guia de navegação pelos documentos do projeto. Os arquivos foram agrupados
por assunto para facilitar a consulta; todos os documentos usam caminhos
relativos a partir de `Lab01/`.

## Planejamento e processo

| Documento | Conteúdo |
|---|---|
| [`Enunciado.md`](Enunciado.md) | Enunciado original do laboratório (RQs, entregas, critérios de avaliação). |
| [`methodology.md`](methodology.md) | Metodologia de coleta, cálculo das métricas e reprodutibilidade. |
| [`tasks.md`](tasks.md) | Plano de execução por sprint, responsáveis e critérios de aceitação. |
| [`tutorial-execucao.md`](tutorial-execucao.md) | Passo a passo operacional: pré-requisitos, coleta, pipeline, validação, dashboard, snapshot e testes. |

## `dataset/` — schemas dos dados

| Documento | Conteúdo |
|---|---|
| [`dataset/raw-dataset.md`](dataset/raw-dataset.md) | Schema do CSV bruto gerado pelo coletor (`data/raw/`). |
| [`dataset/processed-dataset.md`](dataset/processed-dataset.md) | Schema do CSV processado com as métricas derivadas (`data/processed/`). |

## `validation/` — manuais de validação por RQ

| Documento | Conteúdo |
|---|---|
| [`validation/rq01-rq02-validation.md`](validation/rq01-rq02-validation.md) | Validação de idade do repositório e Pull Requests aceitas. |
| [`validation/rq03-rq04-validation.md`](validation/rq03-rq04-validation.md) | Validação de releases e métricas de atividade/atualização. |
| [`validation/rq05-rq06-validation.md`](validation/rq05-rq06-validation.md) | Validação de linguagem primária e percentual de issues fechadas. |
| [`validation/rq07-validation.md`](validation/rq07-validation.md) | Validação da análise integrada da RQ07. |

## `templates/` — modelo do relatório final

| Documento | Conteúdo |
|---|---|
| [`templates/Template_Relatorio_Laboratorio.md`](templates/Template_Relatorio_Laboratorio.md) | Estrutura a preencher para o Relatório Final (versão Markdown). |
| [`templates/Template_Relatorio_Laboratorio.docx`](templates/Template_Relatorio_Laboratorio.docx) | Mesmo modelo, arquivo original em `.docx`. |

## Onde encontrar o quê

* Quer rodar o projeto do zero? Comece por `tutorial-execucao.md`.
* Quer entender uma métrica específica? Veja a seção 9 de `methodology.md` e o manual correspondente em `validation/`.
* Quer saber o schema de uma coluna de CSV? Veja `dataset/`.
* Quer saber o que falta ser feito ou quem é responsável por quê? Veja `tasks.md`.
* Vai escrever o Relatório Final? Comece por `templates/Template_Relatorio_Laboratorio.md`.
