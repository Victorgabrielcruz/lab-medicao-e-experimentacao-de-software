# Lab02 — Assistentes de IA vs. codificação manual

Experimento controlado para comparar produtividade, qualidade funcional e qualidade estrutural na resolução de katas com e sem um assistente de IA.

## Documentação principal

| Documento | Conteúdo |
|---|---|
| [`Docs/Enunciado.md`](Docs/Enunciado.md) | Enunciado, questões de pesquisa, entregas e critérios de avaliação |
| [`Docs/methodology.md`](Docs/methodology.md) | Desenho experimental, métricas, protocolo e plano de análise |
| [`Docs/tasks.md`](Docs/tasks.md) | Divisão do trabalho por sprint, sem atribuição de responsáveis |
| [`Docs/README.md`](Docs/README.md) | Índice da documentação do laboratório |

## Estrutura do projeto

```text
Lab02/
├── Docs/                   # Enunciado, metodologia e documentação operacional
├── data/                   # Dados brutos, processados e metadados
├── katas/                  # Seis objetos experimentais (K01–K06)
├── reference-solutions/    # Soluções de referência sob acesso controlado
├── reports/                # Relatórios, análises e figuras
├── scripts/                # Pontos de entrada para automações
├── src/                    # Implementação da coleta, métricas e análise
├── tests/                  # Testes da infraestrutura experimental
├── training-kata/          # Exercício de treinamento fora da amostra
└── trials/                 # Código final preservado de cada trial
```

## Fluxo esperado

1. Concluir as decisões pendentes em `Docs/methodology.md`.
2. Preparar e validar K01–K06.
3. Implementar testes, cronômetro, coleta e métricas.
4. Gerar e congelar a alocação contrabalanceada.
5. Executar os 18 trials e preservar as evidências.
6. Consolidar e validar o dataset.
7. Analisar RQ1–RQ3 e gerar o dashboard.
8. Elaborar e revisar o relatório final.

Todo trial deve manter a cadeia de rastreabilidade:

`Issue → trial_id → commit → dados brutos → dataset processado → análise`
