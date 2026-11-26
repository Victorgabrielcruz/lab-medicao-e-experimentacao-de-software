# Estimativa de impacto para usuários e empresas — S03-01 (#311)

## Evidência pública e data de acesso

As fontes primárias abaixo foram consultadas em **25/11/2026**. Seus números
contextualizam a adoção; não são a população amostrada pelo experimento.

| Fonte | Número ou informação | Data da publicação/atualização | Como é utilizado |
|---|---|---|---|
| [Google — The Android Show: I/O Edition](https://blog.google/products-and-platforms/platforms/android/the-android-show-io-2025/) | Mais de **3 bilhões de dispositivos Android ativos** | Publicado em **13/05/2025** | Referência histórica de escala, arredondada para 3 bilhões; não contagem atual de 2026 ou de pessoas |
| [SQLite — Most Widely Deployed and Used Database Engine](https://www.sqlite.org/mostdeployed.html) | Estimativa de mais de **1 trilhão de bancos SQLite ativos**; presença em Android | Página atualizada em **21/04/2026** | Evidência de adoção estimada pelos próprios autores; não entra como multiplicador do tempo |
| [SQLite — PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) | Garantias de FULL/NORMAL por modo de journal | A seção não informa data própria; acesso em **25/11/2026** | Contextualizar o custo de durabilidade, sem inventar uma probabilidade de perda |

Um dispositivo pode conter vários bancos e atender a mais de uma pessoa. Por isso,
**bancos, dispositivos e usuários não são unidades intercambiáveis**. Os números
públicos não informam quais configurações, transações ou cargas são usadas.
Os endereços, datas, qualificadores e números também estão em `experimento/impacto.py`
e acompanham o JSON exportável do cenário.

## Resultado experimental utilizado

O cálculo usa exclusivamente a coleta completa validada: **360 medições**, de
25/11/2026, em Windows/NTFS, Python 3.12.14 e SQLite 3.53.1. O piloto não é somado
nem usado para projetar impacto. O SHA-256 do CSV é:

```text
595eba4d16b1c8fbe4550a2d2f2d545c13932b49d10e6e3ff93f8b5a9214eacc
```

A [análise da #309](09-testes-efeitos.md) fornece a **mediana da diferença pareada
de M1**, definida como tempo do tratamento menos tempo da referência, e seu IC
bootstrap pareado de 95%. Os pares seguem as mesmas rodadas e sementes.
O parâmetro não é a diferença entre as medianas dos dois grupos e não vem de
converter diretamente a razão de vazão M3 em segundos.

São comparações diferentes: H1 = WAL-FULL × DELETE-FULL; H2 = WAL-NORMAL × WAL-FULL;
H3 = DELETE-NORMAL × DELETE-FULL. Cada lote mantém o volume do benchmark:

| Carga | Operações por lote | Política observada |
|---|---:|---|
| escrita | 1.000 INSERTs | Um commit por escrita |
| leitura | 10.000 SELECTs por chave | Leituras em autocommit |
| mista | 2.000 operações | 1.400 leituras e 600 escritas, um commit por escrita |

## Modelo de cenário e origem das premissas

O painel oferece um **cenário hipotético para uma empresa**, com quantidade de
dispositivos e lotes por dispositivo/dia ajustáveis. Os valores iniciais de
**10.000 dispositivos e um lote/dia são hipóteses ilustrativas**, não estatísticas
de uma empresa real, pesquisa de usuários ou números fornecidos pelo Google.

Definindo δ como a mediana da diferença pareada de M1, N como dispositivos e L como
lotes por dispositivo/dia:

```text
Redução por lote (s) = −δ
Redução por dispositivo/dia (s) = −δ × L
Horas equivalentes/dia = −δ × N × L / 3.600
Operações/dia = N × L × operações do lote da carga escolhida
```

O modelo assume lotes equivalentes, mesma política de transações e o mesmo custo
por lote medido localmente, repetidos sem efeitos adicionais de escala. Não foi
validado para uma frota. Multiplicar uma mediana **não** produz a mediana da soma
ou uma previsão da média do tempo agregado. Valores negativos representam aumento
de tempo e são preservados, inclusive quando a faixa cruza zero.

O número público entra separadamente para dimensionar a escala da hipótese:

```text
Razão de referência (%) = N / 3.000.000.000 × 100
```

Para N = 10.000, essa razão é aproximadamente **0,000333%** da referência arredondada
do Google. Não é participação de mercado ou fração observada da população Android:
a fonte diz *mais de* 3 bilhões em 2025 e não mede a frota desta empresa fictícia.
Não se multiplica o ganho local pelos 3 bilhões de dispositivos nem pelo trilhão
de bancos para anunciar economia global.

## Exemplo reproduzível: 10.000 dispositivos, um lote por dia

São **cenários alternativos**, não parcelas de uma carga combinada. Números
arredondados apenas na apresentação:

| Carga | Comparação | Redução pareada por lote (s) | Horas equivalentes/dia | Faixa do IC local escalado (h/dia) |
|---|---|---:|---:|---|
| escrita | H1 | 2,056775 | 5,713263 | [5,606645; 5,930678] |
| escrita | H2 | 0,477631 | 1,326752 | [1,317668; 1,334772] |
| escrita | H3 | 0,538781 | 1,496614 | [1,408047; 1,576580] |
| leitura | H1 | 0,329778 | 0,916049 | [0,882556; 0,947514] |
| leitura | H2 | 0,000505 | 0,001403 | [−0,002679; 0,011016] |
| leitura | H3 | −0,008466 | −0,023517 | [−0,061558; 0,034937] |
| mista | H1 | 1,321513 | 3,670871 | [3,590268; 3,719664] |
| mista | H2 | 0,296013 | 0,822258 | [0,810567; 0,835181] |
| mista | H3 | 0,311894 | 0,866371 | [0,756556; 0,967702] |

Por exemplo, na escrita H1, cada lote tem 1.000 INSERTs com commit individual.
O cenário corresponde a 10 milhões de escritas/dia e redução local de referência de
cerca de **2,057 s por dispositivo/dia**, agregada em **5,713 horas equivalentes/dia**.
H1 mantém `synchronous=FULL`. Já H2 envolve a redução de durabilidade descrita
abaixo, mesmo quando seu ganho de tempo é grande.

Se essas operações bloquearem a interface de uma aplicação, menor tempo de banco
pode ser relevante para seus usuários. O estudo, porém, não instrumentou a interface
ou a percepção humana. As horas agregadas não são horas de produtividade ou redução
de um prazo de calendário: os dispositivos podem executar as operações em paralelo.

## Como interpretar a faixa

O IC da diferença é invertido e escalado preservando seus extremos. Se o IC local
de δ é [a; b], a faixa da redução agregada é:

```text
[−b × N × L / 3.600; −a × N × L / 3.600]
```

É o IC marginal do **parâmetro local escalado**, condicional à independência entre
rodadas, como na #309. Não é um intervalo de predição ou de incerteza total da frota.
Não incorpora incerteza sobre N, L, adesão, diferenças entre dispositivos ou mudança
do ambiente. H2 e H3 na leitura têm faixas que incluem zero; não se anunciam ganhos
garantidos ou equivalência nesses casos.

## Desempenho e durabilidade

A documentação informa que WAL-FULL sincroniza a cada commit; WAL-NORMAL pode
perder transações confirmadas após queda de energia ou falha do sistema.
No DELETE, FULL pode depender do sistema de arquivos para durabilidade completa;
NORMAL tem risco pequeno de corrupção em sistemas de arquivos antigos. Essas
garantias são documentais, não resultados de um teste de falha deste experimento.
[Fonte e acesso em 25/11/2026](https://www.sqlite.org/pragma.html#pragma_synchronous).

Para uma empresa, a escolha exige requisitos de recuperação e de persistência dos
dados. A estimativa não converte esse risco em dinheiro nem recomenda NORMAL para
toda aplicação. Também é necessário verificar as restrições operacionais do WAL,
como compartilhamento do mesmo host e arquivos auxiliares.
[Documentação WAL, acesso em 25/11/2026](https://www.sqlite.org/wal.html).

## O que não é possível afirmar

- Ganho global para todos os usuários do SQLite, Android, iOS ou uma empresa nomeada.
- Desempenho em outros discos, sistemas, versões, tamanhos de banco e transações em lote.
- Melhoria geral da leitura: o protocolo mediu SELECTs isolados em autocommit.
- Vantagem de concorrência, latência individual, p95/p99, SLA ou tempo total da aplicação.
- Horas humanas recuperadas, economia financeira, menor energia, bateria ou emissões.
- Frequência de perda de dados, número de transações perdidas ou custo de incidentes.
- Independência comprovada ou IC que cubra todas as incertezas do cenário.

Esses limites complementam as [conclusões revisadas da #312](11-categorias-revisadas-conclusoes.md).
Não foram executadas novas medições, alterados dados ou modificadas as funções da #309.

## Interface e verificação

A seção **6. Impacto para empresas e usuários** contém fontes e datas, seleção de
carga e comparação, premissas editáveis, métricas por lote/dispositivo e agregadas,
cenários alternativos, limites e download JSON com fontes, datas, parâmetros e hash.
No piloto ou com a coleta indisponível, as projeções não são calculadas.

Testes verificam unidades, inversão dos limites do IC, crescimento proporcional,
valores negativos/zero, entradas inválidas, fontes/datas e atualização do dashboard.
O benchmark e os arquivos de dados e validação permanecem preservados.
