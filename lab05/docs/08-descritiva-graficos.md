# Estatística descritiva e gráficos — S02-03 (#308)

## Dados analisados

A seção de resultados do dashboard abre, por padrão, a **coleta completa** em
`data/coleta-completa-01/resultados.csv`: **360 medições**, distribuídas entre
quatro configurações e três cargas, com **30 observações por grupo**.
O piloto permanece em uma seleção separada e não integra a amostra completa.

As entradas são conferidas novamente pelo validador da #307, sem republicar
relatórios ou modificar arquivos. O dashboard exige manifesto aprovado e hashes
compatíveis com as entradas atuais. Se houver reprovação, arquivo ausente ou
manifesto divergente, exibe o erro e não substitui silenciosamente pelo piloto.

SHA-256 do CSV completo:

```text
595eba4d16b1c8fbe4550a2d2f2d545c13932b49d10e6e3ff93f8b5a9214eacc
```

A validação identificou **23 observações distintas sinalizadas**, sem exclusão,
imputação ou winsorização. Todas permanecem nas tabelas, gráficos e downloads.
Os aquecimentos já foram descartados pelo coletor e não estão no CSV analisado.

## Medidas e escala

M1 é o tempo total em segundos, e M2 é a vazão em operações/s. Ambas têm escala
de razão, com zero significativo, e admitem médias, dispersões e razões.
Cada unidade de análise é uma execução da carga, não uma operação SQL.
As cargas são analisadas separadamente, pois seus volumes de operações diferem.

Para cada configuração/carga e para cada uma das duas métricas, são calculados:

- n, média, mediana, mínimo e máximo;
- desvio-padrão amostral, com denominador n−1;
- Q1, Q3 e IQR = Q3 − Q1, com interpolação linear inclusiva;
- CV (%) = 100 × desvio-padrão / média, com médias positivas no conjunto validado.

Mediana e IQR são as medidas principais por sua menor sensibilidade a extremos.
Média, DP e CV complementam a descrição da variação; não pressupõem normalidade
para serem apresentados como resumos amostrais. Não se misturam M1 e M2 em uma
mesma agregação: a tabela geral identifica métrica e unidade em cada linha.

## Resumo da coleta completa

Valores calculados do CSV bruto, arredondados somente nesta apresentação.
As tabelas e exportações do dashboard preservam os valores numéricos dos cálculos.

| Configuração | Carga | n | Mediana M1 (s) | IQR M1 (s) | Mediana M2 (ops/s) | IQR M2 (ops/s) |
|---|---|---:|---:|---:|---:|---:|
| DELETE-FULL | escrita | 30 | 2,590220 | 0,124856 | 386,07 | 18,47 |
| DELETE-FULL | leitura | 30 | 0,406006 | 0,044566 | 24632,42 | 2674,59 |
| DELETE-FULL | mista | 30 | 1,663293 | 0,060873 | 1202,43 | 44,59 |
| DELETE-NORMAL | escrita | 30 | 2,060559 | 0,054284 | 485,31 | 12,89 |
| DELETE-NORMAL | leitura | 30 | 0,406768 | 0,041822 | 24584,07 | 2446,44 |
| DELETE-NORMAL | mista | 30 | 1,339753 | 0,040820 | 1492,83 | 45,27 |
| WAL-FULL | escrita | 30 | 0,521305 | 0,014758 | 1918,26 | 53,69 |
| WAL-FULL | leitura | 30 | 0,075195 | 0,007635 | 132987,36 | 13642,36 |
| WAL-FULL | mista | 30 | 0,335375 | 0,011897 | 5963,48 | 210,28 |
| WAL-NORMAL | escrita | 30 | 0,043349 | 0,002715 | 23068,46 | 1432,67 |
| WAL-NORMAL | leitura | 30 | 0,074007 | 0,008580 | 135127,28 | 15442,99 |
| WAL-NORMAL | mista | 30 | 0,038555 | 0,002262 | 51874,02 | 3031,32 |

São diferenças observadas nesta máquina e nesta coleta. A tabela não estabelece
significância estatística nem qual configuração é universalmente superior.

## Gráficos e exploração

Os filtros de conjunto de dados, carga e métrica atualizam:

1. **Distribuição:** boxplot por configuração com todos os pontos. Q1, mediana
   e Q3 são enviados explicitamente ao Plotly para coincidir com os quartis da
   descritiva e da #307. Os bigodes alcançam os pontos observados dentro dos
   limites Q1 − 1,5 × IQR e Q3 + 1,5 × IQR; extremos continuam visíveis.
2. **Comparação entre configurações:** pontos representam medianas e barras vão
   de Q1 a Q3. São medidas de dispersão observada, não intervalos de confiança.
3. **Interação exploratória:** medianas por journal e sincronização; linhas
   não paralelas descrevem um padrão e não substituem um teste formal.
4. **Ordem de execução:** todos os pontos na posição registrada pelo coletor,
   para inspeção visual sem afirmar independência temporal.

A escala logarítmica opcional muda somente os eixos da distribuição, comparação
e interação. Estatísticas e dados exportados continuam na escala original.
As razões M3 de H1–H3 permanecem descritivas e usam razões entre medianas de M2.

Há downloads do CSV bruto do conjunto selecionado, da descritiva filtrada e da
descritiva completa: 24 linhas, sendo 12 grupos para M1 e 12 para M2.

## Limites e verificação

Esta entrega implementa descritiva e gráficos. A aprovação estrutural permite
essa análise, mas não comprova independência temporal. Auditoria dos sinais,
testes de hipótese, correção de Holm e intervalos inferenciais ficam na **#309**,
conforme o [plano de análise](05-plano-analise.md). Não há nova coleta ou alteração
da metodologia.

Os testes verificam os cálculos com valores conhecidos, quartis e DP contra a
biblioteca padrão, a preservação de extremos no boxplot, as 12 combinações nas
duas métricas, a troca de filtros/coletas e a integridade dos artefatos.

Referências: [coleta completa](06-coleta-completa.md),
[validação e dicionário](07-validacao-dicionario-dados.md) e
[Plotly: quartis pré-calculados e pontos amostrais](https://plotly.com/python/reference/box/).
