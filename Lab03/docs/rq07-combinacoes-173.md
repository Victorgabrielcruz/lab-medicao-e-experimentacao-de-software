# RQ07 — Combinações de definições e classificação (#173)

As três combinações usam a mesma população do CSV final de 500, mesma janela,
deployment frequency de releases estáveis e recuperação por episódios de CI.
Os cortes são os do enunciado, `lab03-enunciado-cortes-v2`, sem ajuste aos dados.
As combinações foram fixadas nesta implementação, após a coleta; não constituem
um protocolo pré-registrado antes da observação dos dados.

| Combinação | Lead time | Change failure rate | Comparação isolada |
|---|---|---|---|
| C1 (referência) | (b), mediana por commit | (a), falhas de CI | Base, igual à #169 na main |
| C2 | (a), mediana por release | (a), falhas de CI | C1 × C2 altera apenas lead time |
| C3 | (b), mediana por commit | (b), releases corretivas | C1 × C3 altera apenas CFR |

C2 × C3 altera ambas as definições. A C1 coincide com `REFERENCIA_GERAL` de
`pipeline/classes_dora.py`, já integrada na main pela #169. Um teste compara
as classes gerais das duas implementações para todos os 500 projetos.
Pré-releases e tags não entram nestas
três combinações: a análise cobre a sensibilidade às variantes de lead time
e CFR já consolidadas. Ela não responde à sensibilidade da unidade de deploy.

As quatro classes viram notas Low=1, Medium=2, High=3, Elite=4; a classe geral
é a mediana arredondada para baixo. Ausências não recebem zero nem classe e
ficam fora da mediana, conforme o protocolo existente. O CSV identifica
`metricas_disponiveis` e `completa`, para não confundir uma nota parcial com
uma nota baseada nas quatro métricas. Os indicadores de qualidade da fonte
também são preservados. Todas as classes das variantes são recalculadas e
conferidas contra o contrato de entrada; DF usa a duração real da janela.

## Verificação de impedimentos

Em 21/10/2026, o CSV final tem 500 repositórios, seis métricas/variantes,
manifesto e SHA-256 verificável. O módulo de classificação já fornece os
cortes e a agregação. Não há impedimento técnico para esta entrega.
A #162 foi encerrada, com relatório publicado de 146/300 releases no snapshot
parcial. A conferência das previsões finais locais contra o consenso oficial
alcançou 296/300, com quatro indeterminadas, precisão 0,890511, recall 0,979920
e F1 0,933078. O [registro dessa conferência](evidencias/rq07-validacao-final-162.json)
inclui hashes, pares, matriz e exclusões; não altera o relatório histórico da #162
nem imputa previsões negativas às quatro releases. A avaliação não é integral,
e C3 mantém essa limitação de validade. Isso não impede calcular e entregar
a sensibilidade das definições. Completude da coleta não elimina nulos e
cálculos parciais.

## Reprodução

A partir de `Lab03`, sem API ou token:

```powershell
.venv/Scripts/python.exe -m pipeline.rq07
.venv/Scripts/python.exe -m pytest tests/test_rq07.py tests/test_classificacao.py tests/test_classes_dora.py
```

Entrada: `entregas/s02-03-dataset-500-final/dataset-500.csv`, acompanhada de
`manifesto.csv.json`. Opções: `--dataset` e `--saida`.
Resultados em `analise/rq07/classificacoes.csv` (uma linha por projeto e
combinação) e `analise/rq07/combinacoes.json` (definições, janela, hashes,
distribuições por métrica e geral, cobertura e limitações).

## Resultado desta execução

Dataset SHA-256: `2552ba6b0779e895d01bea88742cb668ee1812a8369a224ed5281708140b30bd`.
Foram geradas 1.500 linhas. A distribuição geral inclui as notas parciais:

| Combinação | Elite | High | Medium | Low | Quatro métricas disponíveis |
|---|---:|---:|---:|---:|---:|
| C1 | 28 | 220 | 226 | 26 | 468 |
| C2 | 32 | 203 | 235 | 30 | 468 |
| C3 | 4 | 117 | 318 | 61 | 467 |

Validação: 80 testes aprovados (RQ07 e classificação, incluindo a C1 da #169), conferência de hashes,
classes de entrada, ausências, limites e exportação reproduzível.
