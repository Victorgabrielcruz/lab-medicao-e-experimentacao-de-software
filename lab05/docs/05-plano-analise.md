# Plano de análise — S01-07 (#305)

Este plano usa o [GQM e as hipóteses H1–H3](02-pergunta-gqm-hipoteses.md),
o benchmark da #303 e o [piloto da #304](04-piloto-plano-coleta.md).
A implementação da análise inferencial e suas conclusões ficam para a próxima sprint.
O dashboard desta entrega apresenta somente a descritiva do piloto.

## Dados, escala e unidade de análise

- Fatores nominais: `journal_mode` (DELETE/WAL) e `synchronous` (FULL/NORMAL).
- Analisar separadamente escrita, leitura e mista: seus números de operações diferem.
- M1 = `tempo_total_s`, segundos, escala de razão; menor é melhor.
- M2 = `vazao_ops_s` = operações/M1, operações/s, escala de razão; maior é melhor.
- M3 = mediana de M2 do tratamento / mediana de M2 da referência, adimensional,
  escala de razão; 1 indica ausência de ganho entre as medianas.
- Uma observação é uma execução medida da carga, não cada operação SQL.
  As operações da mesma execução não são réplicas independentes.

O coletor embaralha as 12 combinações em cada rodada e usa a mesma sequência de
operações nas quatro configurações para uma carga/repetição. Portanto, comparar
tratamentos preservando o pareamento por `(carga, repeticao, semente_carga)`.
A sequência comum é um controle; não garante independência entre rodadas.
Ambiente e identificador de coleta também devem integrar a chave se houver replicações.

Antes da análise completa (#307), conferir as 360 linhas, as 30 repetições por
combinação, ausência de aquecimentos, duplicatas e lacunas, valores positivos e
finitos, contagens de operações, M2 = operações/M1, sementes e ambiente.
Não misturar o piloto às 30 repetições finais nem juntar ambientes silenciosamente.
Preservar dados brutos e outliers; documentar falhas sem excluir observações por lentidão.

## Estatística descritiva

Para M1 e M2, por configuração e carga: n, média, mediana, desvio-padrão amostral
(n−1), mínimo, máximo, Q1, Q3, IQR e CV = 100 × DP/média.
Usar quartis com interpolação inclusiva, como no resumo do piloto.
Mediana e IQR são os resumos principais, por sua resistência a observações extremas.

Planejar boxplots com todos os pontos, distribuições por grupo e gráficos de
medianas/interação. Inspecionar métricas e diferenças pareadas contra `ordem_execucao`
para identificar deriva temporal, além de Q–Q plots e assimetria das diferenças.
Um teste de normalidade isolado não determina a escolha do método.

O piloto tem somente três observações por grupo e CV de M1 entre 1,18% e 49,46%
([registro do piloto](04-piloto-plano-coleta.md)). Isso evidencia variabilidade,
mas não estabelece a distribuição ou sua simetria. Não assumir normalidade com
base nessa amostra, nem afirmar que 30 repetições garantem poder estatístico.

## Testes de hipótese por métrica

As comparações previamente definidas são, em cada uma das três cargas:

| Hipótese | Tratamento | Referência |
|---|---|---|
| H1 | WAL-FULL | DELETE-FULL |
| H2 | WAL-NORMAL | WAL-FULL |
| H3 | DELETE-NORMAL | DELETE-FULL |

| Métrica | Teste planejado e justificativa | Tamanho do efeito |
|---|---|---|
| M2, principal | Teste dos sinais pareados, binomial exato bilateral. Preserva as rodadas e não exige normalidade nem simetria das diferenças | Probabilidade pareada de ganho, diferença de vazão e M3 |
| M1, complementar | O mesmo teste de sinais, com direção invertida: para uma carga fixa, M2 = n/M1. Não realizar uma segunda família de testes redundantes | Diferença pareada de tempo em segundos; redução percentual |
| M3, derivada | Não tem teste separado: é uma estatística dos grupos, não uma coleção de observações independentes. A evidência de teste vem das comparações de M2 | Razão entre medianas, ganho percentual e IC por bootstrap pareado |

Para cada comparação, calcular `d_i = M2_tratamento_i − M2_referencia_i`.
Operacionalizar as hipóteses amplas de diferença de distribuição do GQM como
H0: `P(d_i > 0 | d_i != 0) = 0,5`; H1: essa probabilidade difere de 0,5.
O teste detecta predominância de ganhos/perdas pareados; não testa toda possível
diferença de distribuição nem, diretamente, a igualdade das medianas marginais.
Essa definição explicita o estimando escolhido nesta etapa de planejamento.

Contar sinais positivos k e pares não empatados n; usar
`scipy.stats.binomtest(k, n, p=0.5, alternative="two-sided")`.
Registrar empates e excluí-los apenas da contagem do teste; preservar todas as
medições na descritiva. Se todos os pares empatarem, registrar ausência de pares
informativos e p = 1 para manter a família definida, sem declarar equivalência.
Não arredondar métricas antes da comparação nem inventar tolerâncias após ver resultados.

Aplicar **Holm aos nove valores-p em conjunto**, com **α = 0,05**, apresentando p bruto,
p ajustado, n efetivo e decisão. O teste é conservador e descarta a magnitude das
diferenças; os tamanhos do efeito abaixo complementam sua interpretação.
Não trocar o teste após observar significância.

O método pressupõe independência dos sinais entre rodadas. Se a auditoria encontrar
dependência temporal relevante ou pares incompletos, suspender conclusões confirmatórias
e registrar uma revisão do plano que trate essa estrutura, preservando os resultados
exploratórios. Trocar automaticamente para Mann–Whitney ou Welch perderia o pareamento;
Wilcoxon exige simetria das diferenças, ainda não sustentada pelo piloto.

### Fatores e interação

Manter a interação **exploratória, sem teste formal**, conforme o GQM já registrado:
comparar o ganho de NORMAL dentro de DELETE (H3) com o ganho dentro de WAL (H2),
por gráfico de medianas e razão `M3_H2 / M3_H3`, separadamente por carga.
As três comparações são efeitos simples, não estimativas de efeitos principais globais.
O desenho fatorial não obriga ANOVA: uma ANOVA independente ignoraria as rodadas;
um eventual modelo fatorial com blocos exigiria revisão explícita do plano e
diagnóstico de resíduos e dependência. Não introduzir esse teste como se já previsto.

## Magnitude, incerteza e relevância prática

- M1: mediana das diferenças pareadas em segundos (tratamento − referência)
  e mediana das reduções pareadas `100 × (1 − M1_tratamento/M1_referencia)`.
- M2: mediana das diferenças pareadas em operações/s e probabilidade de ganho
  `k/n` entre os pares não empatados, com IC binomial exato de 95%; apresentar empates.
- M3: razão entre as **medianas dos grupos**, conforme o GQM; ganho percentual
  `100 × (M3 − 1)`. Não substituir por mediana das razões individuais.

Na coleta completa, estimar IC de 95% das medianas, diferenças e M3 por bootstrap
percentil com **10.000 reamostragens e semente 42**. Em cada carga, reamostrar
rodadas completas com reposição e os mesmos índices nas quatro configurações;
recalcular a estatística a cada amostra, preservando o pareamento. Registrar o método
e as versões. São IC marginais, sem ajuste simultâneo para as nove comparações;
não substituem a decisão com Holm. Não estimar IC inferenciais com os três pontos
do piloto nesta entrega.

Na leitura, usar a faixa M3 de **0,98 a 1,02** como referência prática previamente
registrada no GQM, sem concluir equivalência formal a partir de um IC de 95% ou de
um p não significativo. Para escrita e mista, discutir diferenças absolutas e relativas
com o custo da aplicação, sem inventar limiar universal de relevância.
Significância, magnitude e utilidade prática devem ser discutidas separadamente.

## Entregas e limites

A Sprint 01 entrega este plano, o dashboard com seis seções e a descritiva do piloto.
Na próxima sprint: coleta completa (#306), validação (#307), descritiva de M1/M2,
execução dos testes, correção de Holm, efeitos e intervalos.
Discussão final, revisão das sete categorias, impacto quantitativo, documento e
apresentação dependem dessas evidências. Não há valores-p nem conclusão de superioridade
nesta entrega. Durabilidade continua documental; não há experimento de falha de energia,
concorrência ou mensuração de consumo de recursos.

## Referências metodológicas

- [SciPy: binomtest, teste e IC binomial exatos](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).
- [SciPy: Wilcoxon, pareamento e pressuposto de simetria](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html).
- [SciPy: Mann–Whitney para amostras independentes](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html).
- [SciPy: bootstrap e reamostragem pareada](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
- [statsmodels: correção de comparações múltiplas, incluindo Holm](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).

Fontes consultadas em 19/11/2026. A seleção do teste dos sinais é uma decisão deste
plano, fundamentada no pareamento implementado e na ausência de evidência suficiente
para assumir normalidade ou simetria; não é uma conclusão inferida dos valores-p.

## Implementação e auditoria operacional — #309

O plano foi implementado na #309, com detalhes e resultados em
[09-testes-efeitos.md](09-testes-efeitos.md). As nove hipóteses, teste dos sinais,
Holm, efeitos, bootstrap percentil pareado, 10.000 reamostragens e semente 42
foram mantidos. A auditoria temporal foi operacionalizada depois da coleta:
sequências dos sinais e das diferenças em torno da mediana, com runs exato e Holm
em uma família diagnóstica separada de 18 posições, além de correlações e inspeção
das séries. Esse detalhamento não estava pré-especificado na S01.
Alertas suspendem conclusões confirmatórias; a ausência de alerta não comprova
independência. Todos os valores-p e IC são apresentados como condicionais a esse
pressuposto. Não houve alteração de dados ou substituição do teste por outro mais
favorável. O plano original acima permanece como registro do que foi previsto.
