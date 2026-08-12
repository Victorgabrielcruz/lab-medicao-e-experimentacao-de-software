# Metodologia

## 1. Objetivo

Definir um processo reproduzível para coletar e analisar dados dos 1.000 repositórios mais populares do GitHub, de forma a responder às 7 questões de pesquisa (RQs) do laboratório sem antecipar resultados.

## 2. Seleção dos Repositórios

A amostra será composta pelos 1.000 repositórios públicos com maior número de estrelas no GitHub no momento da coleta.

Critérios:
- considerar apenas repositórios públicos;
- ordenar por popularidade (stars) de forma decrescente;
- coletar exatamente 1.000 registros válidos;
- registrar data/hora da coleta para contextualizar variações futuras.

## 3. Fonte dos Dados

A fonte oficial será a API GraphQL do GitHub, consultada por meio de token com permissões adequadas para leitura dos metadados públicos dos repositórios.

## 4. Processo de Coleta

1. Definir consulta GraphQL com os campos necessários para todas as RQs.
2. Executar coleta paginada até atingir 1.000 repositórios.
3. Armazenar resposta bruta em `data/raw/`.
4. Registrar logs da execução (tempo, páginas, total coletado, erros).
5. Consolidar dataset para processamento em `data/processed/`.

## 5. API GraphQL

A consulta deve recuperar, no mínimo, atributos de identificação e os indicadores usados nas métricas das RQs, como:
- data de criação e atualização;
- linguagem primária;
- total de stars;
- dados agregados de pull requests, issues e releases.

A consulta deve ser versionada no projeto para garantir repetibilidade e auditoria.

## 6. Paginação

A paginação será implementada com cursores (`pageInfo.endCursor` e `pageInfo.hasNextPage`).

Regras:
- tamanho de página constante por execução;
- interrupção ao atingir 1.000 repositórios válidos;
- tratamento de rate limit e retentativas para falhas transitórias;
- preservação da ordem de coleta para rastreabilidade.

## 7. Dados Coletados

Os dados coletados devem cobrir o mínimo necessário para responder às RQs:
- identificador do repositório;
- nome completo;
- URL;
- stars;
- data de criação;
- data de última atualização;
- linguagem primária;
- quantidade de pull requests aceitas;
- quantidade de releases;
- quantidade de issues abertas/fechadas (ou equivalente para cálculo do percentual);
- dados auxiliares para analisar contribuição externa na RQ07.

## 8. Métricas das Questões de Pesquisa

### RQ01
Métrica: idade do repositório (em anos), calculada a partir da data de criação até a data de referência da coleta.

### RQ02
Métrica: número de pull requests aceitas por repositório.

### RQ03
Métrica: número de releases por repositório.

### RQ04
Métrica: frequência de atualização, derivada da data de última atualização e/ou intervalos de atividade no período analisado.

### RQ05
Métrica: linguagem primária de cada repositório e distribuição por linguagem na amostra.

### RQ06
Métrica: percentual de issues fechadas por repositório.

### RQ07
Métrica: análise integrada da relação entre linguagem, contribuição externa, releases e frequência de atualização, construída a partir das métricas das RQs anteriores e dos campos complementares coletados.

## 9. Processamento dos Dados

- normalizar tipos (datas, inteiros e campos textuais);
- remover duplicidades;
- validar valores ausentes e inconsistentes;
- derivar métricas calculadas (idade, percentuais, frequências);
- exportar datasets intermediários e finais (ex.: CSV) para análise.

## 10. Validação dos Dados

A validação incluirá:
- conferência da cardinalidade final (1.000 repositórios);
- verificação de completude dos campos obrigatórios por RQ;
- checagem de consistência entre totais e percentuais;
- validação por amostragem manual de registros críticos.

## 11. Reprodutibilidade

Para garantir reprodutibilidade:
- versionar consulta GraphQL e pipeline;
- registrar parâmetros de execução (data, token, paginação e limites);
- manter dados brutos e processados separados;
- rastrear tarefas por Issues e commits vinculados.

## 12. Limitações

- os dados refletem o estado do GitHub no momento da coleta;
- alterações futuras nos repositórios podem mudar resultados;
- limites de API e campos indisponíveis podem restringir algumas análises;
- resultados de RQ07 dependem da qualidade e completude das métricas das RQ01–RQ06.
