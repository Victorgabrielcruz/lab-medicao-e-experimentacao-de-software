# Testes de hipótese e tamanho do efeito — S02-04 (#309)

## Origem e reprodução

Análise da coleta completa de 25/11/2026: **360 medições, 30 rodadas, quatro
configurações e três cargas**, após a [validação da #307](07-validacao-dicionario-dados.md).
O piloto não integra a análise e as 23 observações sinalizadas permanecem nos dados.
Não houve nova coleta, mudança das cargas, remoção de extremos ou imputação.

CSV: `data/coleta-completa-01/resultados.csv`, SHA-256:

```text
595eba4d16b1c8fbe4550a2d2f2d545c13932b49d10e6e3ff93f8b5a9214eacc
```

Com as dependências instaladas, dentro de `lab05/`:

```bash
python analisar_dados.py --saida /tmp/lab05-analise.json
python -m pytest -q
python -m streamlit run app.py
```

No Windows, escolha um caminho local para `--saida`. Sem essa opção, o comando
imprime JSON em stdout. O arquivo de saída deve ser novo; arquivos existentes
nunca são sobrescritos. O comando exige os dados e o manifesto aprovado, revalida
as entradas e não altera dados ou relatórios da #307. O mesmo JSON pode ser baixado
no dashboard. Ele inclui versões da análise, parâmetros, resultados e hash do CSV.

## Teste adequado à escala e ao desenho

Foi implementado o [plano registrado na #305](05-plano-analise.md):

| Métrica | Escala e papel | Teste e efeito |
|---|---|---|
| M2, vazão | Razão, operações/s; resposta principal | Sinais pareados, binomial exato bilateral; probabilidade de ganho e efeitos de magnitude |
| M1, tempo | Razão, segundos; complementar | O sentido do sinal é invertido porque M2 = n/M1 em uma carga fixa; não gerar testes redundantes |
| M3 | Razão entre medianas de M2; derivada | Tamanho do efeito com IC, sem teste separado e sem tratar nove razões como réplicas |

Os pares são reconstruídos por **carga, rodada e semente de carga exata**,
independentemente da ordem das linhas no CSV. São exigidas as 30 rodadas completas
nas quatro configurações, um ambiente, valores positivos e finitos e equivalência
M2 = operações/M1. Sementes de 64 bits não são convertidas por `float`.

Para cada comparação, `d = M2_tratamento − M2_referência`:

- H0: `P(d > 0 | d != 0) = 0,5`; H1: essa probabilidade difere de 0,5.
- H1 compara WAL-FULL com DELETE-FULL; H2, WAL-NORMAL com WAL-FULL; H3,
  DELETE-NORMAL com DELETE-FULL. Todas são realizadas nas três cargas.
- O teste é bilateral e não exige normalidade, variâncias iguais ou simetria das
  diferenças. A escolha não muda conforme um teste de normalidade ou o valor-p.
- Empates são reportados e removidos apenas da contagem binomial. Permanecem
  nos efeitos e no bootstrap. Sem pares informativos, p = 1 para manter a família;
  probabilidade de ganho e seu IC ficam indefinidos, sem declarar equivalência.
- O estimando é a predominância de ganhos/perdas entre pares, não toda possível
  diferença de distribuição nem a igualdade das medianas marginais.

**Holm, α = 0,05, é aplicado aos nove valores-p juntos.** Ordenar os valores-p,
multiplicar por 9, 8, …, 1, aplicar máximo acumulado e limitar a 1; depois restaurar
a ordem original. Empates e ordem de apresentação não alteram a família.
Os filtros do dashboard não recalculam o ajuste dentro de subconjuntos.

## Auditoria dos pressupostos

A independência entre rodadas é necessária para o teste binomial e para os IC
calculados. A #307 aprovou integridade e protocolo; não aprovou independência.
Nesta issue, a auditoria prevista no plano foi operacionalizada da seguinte forma:

1. Inspecionar as diferenças pareadas contra a rodada e sua sequência de sinais.
2. Calcular Spearman das diferenças contra a rodada, correlação de lag 1 das
   diferenças e dos sinais e medianas das duas metades. São diagnósticos descritivos,
   sem p assintótico de Spearman para n = 30 ou limiar arbitrário de correlação.
3. Calcular o **runs exato** em duas sequências por comparação: sinais em torno de
   zero e sinais das diferenças em torno da própria mediana. O segundo diagnóstico
   também examina variação temporal da magnitude quando todos os ganhos têm o mesmo sinal.
4. Aplicar Holm à **família diagnóstica separada de 18 posições**, com α = 0,05.
   Uma rejeição gera alerta e suspende conclusões confirmatórias naquela comparação.
   Valores-p e IC continuam disponíveis como cálculos condicionais, sem fingir que
   o método tenha corrigido a dependência sinalizada.

Um run é um trecho consecutivo de sinais iguais. A distribuição exata do número
de runs é calculada por contagem combinatória, condicionada às quantidades de
sinais positivos e negativos. O p bilateral é o dobro da menor cauda, limitado a 1.
Zeros são retirados apenas do diagnóstico em questão e seu n é apresentado.
Quando só há um tipo de sinal ou nenhum valor informativo, o diagnóstico é
**inconclusivo**, com p indefinido. No ajuste conservador, essa posição recebe
internamente 1; esse número não é exibido como se fosse um diagnóstico válido.

Essa operacionalização foi definida na #309, depois da coleta; **não se afirma
que a regra de auditoria já estivesse pré-especificada na S01**. É uma ferramenta
diagnóstica, com poder limitado para n = 30. Não elimina deriva do ambiente,
dependências não detectadas ou necessidade de replicação. Por isso, mesmo sem
alerta, decisões e IC são explicitamente **condicionais à independência**.

Na coleta real, os nove diagnósticos em torno da mediana e os dois diagnósticos
testáveis dos sinais não geraram alerta após Holm. Os outros **sete diagnósticos
dos sinais são inconclusivos**, pois os 30 sinais são positivos. Por exemplo,
Spearman das diferenças de H1 na leitura é aproximadamente 0,394 e de H2 na escrita,
−0,332: esses padrões merecem inspeção, mesmo sem alerta no teste de sequências.
Não se conclui que as rodadas sejam independentes a partir desses resultados.

## Tamanho do efeito e intervalos

Cada comparação inclui:

- **Probabilidade pareada de ganho**, `ganhos / pares não empatados`, com IC binomial
  exato de Clopper–Pearson a 95%.
- **Efeito direcional dos sinais**, `2p − 1`, com IC obtido pela mesma transformação
  dos limites do IC de p. Varia de −1 a 1 e respeita o pareamento. Não é o delta de
  Cliff para grupos independentes. A probabilidade e M3 já estavam previstas no plano;
  a transformação apenas facilita a leitura da direção.
- **M1:** mediana da diferença pareada em segundos e mediana da redução percentual
  `100 × (1 − M1_tratamento/M1_referência)`.
- **M2:** mediana da diferença pareada em operações/s.
- **M3:** mediana de M2 do tratamento dividida pela mediana de M2 da referência,
  mais ganho percentual `100 × (M3 − 1)`. Não substituir pela mediana das razões.

Diferenças, reduções, M3 e medianas dos 12 grupos de cada métrica recebem IC
**percentil de 95%, 10.000 reamostragens, semente 42**. Em cada carga, os mesmos
índices de rodadas são usados nas quatro configurações e nas duas métricas.
Os geradores são derivados por `SeedSequence([42, índice_carga])`, com cargas na
ordem escrita, leitura e mista. Não reamostrar tratamentos independentemente.

Esses IC são **marginais e condicionais à independência**, sem ajuste simultâneo
para nove comparações. Não substituem o ajuste de Holm dos testes. O teste dos
sinais não testa diretamente o parâmetro de M3; a exclusão de 1 pelo IC de M3 não
deve ser apresentada como outra decisão confirmatória. Não se declara equivalência
na faixa 0,98–1,02, nem se interpreta um p não significativo como ausência de efeito.

## Resultados condicionais da coleta completa

Todos os testes têm 30 pares e nenhum empate nesta coleta. Números arredondados
somente nesta tabela; JSON e tabelas do dashboard mantêm os valores calculados.

| Carga | Hipótese | Ganhos/perdas | p bruto | p Holm | M3 | IC 95% de M3, condicional |
|---|---|---:|---:|---:|---:|---|
| escrita | H1 | 30/0 | 1.862645e-09 | 1.676381e-08 | 4,968720 | [4,870742; 5,104992] |
| escrita | H2 | 30/0 | 1.862645e-09 | 1.676381e-08 | 12,025710 | [11,728398; 12,309316] |
| escrita | H3 | 30/0 | 1.862645e-09 | 1.676381e-08 | 1,257048 | [1,233689; 1,289167] |
| leitura | H1 | 30/0 | 1.862645e-09 | 1.676381e-08 | 5,398875 | [5,180754; 5,652420] |
| leitura | H2 | 16/14 | 0.855536 | 0.855536 | 1,016091 | [0,971536; 1,061314] |
| leitura | H3 | 12/18 | 0.361595 | 0.723189 | 0,998037 | [0,954054; 1,043663] |
| mista | H1 | 30/0 | 1.862645e-09 | 1.676381e-08 | 4,959504 | [4,831828; 5,031557] |
| mista | H2 | 30/0 | 1.862645e-09 | 1.676381e-08 | 8,698618 | [8,493876; 8,863632] |
| mista | H3 | 30/0 | 1.862645e-09 | 1.676381e-08 | 1,241504 | [1,200766; 1,256589] |

Sob o pressuposto de independência, sete comparações rejeitam H0 após Holm.
H2 e H3 na leitura não rejeitam H0. Isso não prova equivalência ou irrelevância
prática: seus IC de M3 são mais largos que a faixa de referência de ±2%.
Nas comparações com 30 ganhos, a probabilidade estimada é 1, mas seu limite inferior
exato de 95% é aproximadamente 0,8843; não se afirma ganho garantido em toda execução.

O estudo continua restrito a uma máquina e cargas sintéticas sequenciais, sem
medir durabilidade ou concorrência. Significância condicional, magnitude, custo
de perda de dados e relevância para cada aplicação devem ser discutidos separadamente.

## Verificação e referências

Testes cobrem sinais e empates, IC exato, Holm com ordem/empates, runs por enumeração
exaustiva de sequências pequenas, entradas inválidas, sementes exatas, ordenação
das linhas, bootstrap pareado e reprodutível, efeitos conhecidos, suspensão por
alerta temporal, serialização sem NaN, CLI e integração do dashboard.

As versões ficam no JSON. A execução local da análise usou Python 3.14.3 e as
dependências fixadas no ambiente do Lab04; a coleta foi feita em Python 3.12.14,
como registrado nos metadados. O código não introduz novas dependências.

- [SciPy: binomtest e IC exato](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).
- [SciPy: bootstrap e reamostragem pareada](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
- [SciPy: Spearman e limite do p assintótico para amostras pequenas](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html).
- [NIST: diagnóstico de sequências e aleatoriedade](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35d.htm).
- [statsmodels: métodos de correção, incluindo Holm](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html).

Referências consultadas em 25/11/2026. O NIST fundamenta o diagnóstico de runs;
a implementação exata condicional foi conferida com enumeração, sem usar a
aproximação normal para amostras pequenas.
