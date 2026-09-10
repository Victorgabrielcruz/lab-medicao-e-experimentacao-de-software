# Equivalência dos pares de dificuldade

**Task:** S01-03 — Formar e validar os pares de dificuldade
**Data da análise:** 10/09/2026

Este documento aplica os sete fatores de dificuldade listados em
[`methodology.md`, Seção 7.4](methodology.md#74-validação-de-equivalência) às
seis katas, confirma (ou ajusta) os blocos B1, B2 e B3 definidos
provisoriamente em `methodology.md` Seção 7.1, e registra as diferenças que
sobram mesmo depois do pareamento.

## 1. Por que não houve piloto externo

A Seção 7.4 prevê como caminho preferencial um piloto conduzido por alguém
que não vai participar dos trials válidos. Isso não é viável aqui: o grupo
tem três integrantes e o desenho é crossover — todos os três resolvem as
seis katas. Não existe uma quarta pessoa disponível para pilotar sem virar
sujeito do próprio experimento.

O fallback da metodologia para esse caso é avaliar por inspeção, "sem
implementação completa". Fomos além disso: já existem soluções de
referência completas e funcionais para as seis katas (produzidas para
validar as suítes de aceitação da S01-04), então medimos LOC e complexidade
de verdade em vez de estimar. Isso é mais rigoroso que o mínimo exigido, não
menos — mas ainda não substitui um piloto cronometrado por alguém sem
contato prévio com as katas.

## 2. Metodologia da pontuação

A Seção 7.4 lista sete fatores e deixa os critérios e escores a cargo do
grupo. Usamos a seguinte régua, igual para todos os fatores numéricos:

Para cada fator, calculamos o mínimo e o máximo entre as seis katas e
dividimos essa faixa em três terços iguais:

- **tier 1 (baixa):** valor ≤ mínimo + 1/3 da faixa
- **tier 2 (média):** valor ≤ mínimo + 2/3 da faixa
- **tier 3 (alta):** acima disso

Aplicamos essa régua a seis dos sete fatores, todos com um número real por
trás:

| Fator da metodologia | O que medimos |
|---|---|
| Quantidade e complexidade das regras | Número de itens em "Regras e restrições" de cada README |
| Número estimado de casos-limite | Testes de aceitação da S01-04, descontando o teste do exemplo do enunciado |
| Quantidade de testes de aceitação | Total de testes de cada suíte |
| LOC estimada da solução de referência | `SLOC` do `radon raw` sobre a solução de referência |
| Complexidade ciclomática da solução de referência | Média do `radon cc -s -a` |
| Tempo estimado de implementação | Ponto médio da faixa já registrada em `katas.md` §1 |

O sétimo fator — **estruturas de dados necessárias** — não tem um número
óbvio por trás. Classificamos por inspeção direta do código de referência:
tier 1 para estrutura plana (um dicionário, sem coordenação de estado entre
registros), tier 2 para o que exige comparação par a par ou uma máquina de
estados. É o único fator desta tabela que não vem de uma contagem ou
medição — fica registrado aqui para quem quiser questionar o critério.

**Score de dificuldade** = soma simples dos sete tiers (varia de 7 a 21). Os
sete fatores entram com peso igual porque a metodologia não estabelece
prioridade entre eles; inventar pesos diferentes seria uma escolha a mais
sem respaldo. O **delta do par** é a diferença absoluta entre os scores dos
dois membros de cada bloco.

## 3. Números por kata

| Kata | Regras | Casos-limite | Testes | LOC (SLOC) | Funções | CC média | CC máx. | Tempo estimado | Estruturas de dados | Score |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| K01 | 6 | 5 | 6 | 21 | 2 | 5.0 | 9 | 20–30 min | Intervalos + comparação par a par | 14 |
| K02 | 7 | 4 | 5 | 25 | 1 | 7.0 | 7 | 15–25 min | Dicionário plano de saldo/capacidade | 8 |
| K03 | 7 | 5 | 6 | 29 | 1 | 7.0 | 7 | 15–25 min | Máquina de estados sequencial + conjunto de vistos | 14 |
| K04 | 9 | 5 | 6 | 34 | 2 | 7.0 | 13 | 20–30 min | Máquina de estados + comparação de horário | 19 |
| K05 | 8 | 4 | 5 | 21 | 1 | 8.0 | 8 | 15–25 min | Contador/flag plano por sensor | 9 |
| K06 | 6 | 4 | 5 | 32 | 1 | 10.0 | 10 | 15–25 min | Índice de progresso + busca do próximo ponto | 12 |

LOC e complexidade medidos com `radon 6.0.1`; testes reexecutados com
`pytest 9.1.1` antes desta análise — as seis soluções de referência
continuam passando 100% das suítes da S01-04 (ver Seção 6).

`K04.avaliar_credenciais` tem CC=13 (grau C no `radon`), a complexidade
máxima isolada de todo o conjunto — é a única função que combina máquina de
estados com verificação de horário de expiração na mesma peça de código, em
vez de separar as duas responsabilidades.

## 4. Comparação par a par

| Bloco | Kata A | Kata B | Score A | Score B | Delta |
|---|---|---|---:|---:|---:|
| B1 | K01 | K02 | 14 | 8 | 6 |
| B2 | K03 | K04 | 14 | 19 | 5 |
| B3 | K05 | K06 | 9 | 12 | 3 |

O delta de B1 é o maior dos três: K01 supera K02 em casos-limite (5 vs. 4),
testes (6 vs. 5) e tempo estimado (25 vs. 20 min de ponto médio), compensado
apenas parcialmente por K02 ter complexidade ciclomática um pouco mais alta
(7,0 vs. 5,0). Em B2, K04 é objetivamente mais difícil que K03 em quase todo
fator (regras, LOC, tempo, complexidade máxima), exceto casos-limite e
testes, que empatam. B3 é o par mais equilibrado.

## 5. Blocos confirmados

Ordenando as seis katas pelo score (K02=8, K05=9, K06=12, K01=14, K03=14,
K04=19) e parenando adjacentes, o pior delta possível seria 5 (par
K03/K04). O agrupamento provisório de `methodology.md` §7.1 tem pior delta
6 (par B1). A diferença entre as duas opções é de apenas 1 ponto numa escala
de 0 a 14 — não achamos que valha trocar o agrupamento já usado em
`katas.md` e já conhecido pelo grupo por uma vantagem tão pequena, construída
em cima de um rubric de 7 tiers que não pretende ter essa precisão.

**Decisão: mantemos os blocos como estão.**

| Bloco | Kata A | Kata B |
|---|---|---|
| B1 | K01 | K02 |
| B2 | K03 | K04 |
| B3 | K05 | K06 |

## 6. Soluções de referência: testes e custódia

As seis soluções de referência (`reference-solutions/K01` a `K06`) passam
100% das suítes de aceitação da S01-04 — reconfirmado nesta análise, não só
herdado da S01-04.

Elas continuam fora do controle de versão compartilhado
(`Lab02/reference-solutions/**/*.py` no `.gitignore` da raiz) durante toda a
S01 e a S02. Só entram no repositório depois que os 18 trials da S02
terminarem, caso a publicação seja necessária para replicação — é a mesma
regra que já estava em `reference-solutions/README.md`, agora formalizada em
vez de deixada em aberto. Essa é uma garantia de mecanismo, ativa desde já;
não é uma garantia de resultado — só a auditoria da S02-06, depois que os
trials realmente acontecerem, confirma que ninguém acessou uma solução antes
do próprio trial.

## 7. Limitações

- **Sem piloto externo.** Nenhuma das três pessoas disponíveis pode pilotar
  sem virar sujeito do experimento (Seção 1). A equivalência descansa em
  inspeção + medição real de código, não em uma execução cronometrada por
  alguém sem contato prévio com as katas.
- **P02 já viu as seis soluções de referência.** Elas foram escritas por P02
  para validar as suítes da S01-04, antes desta análise. Isso quebra a
  premissa de participante cego para P02 nas seis katas, desde já — não é
  um risco hipotético, já aconteceu. O grupo decidiu registrar isso como
  ameaça à validade interna conhecida (a levar para a discussão de ameaças
  à validade do relatório final), sem excluir os trials de P02 nem trocar
  quem custodia as soluções.
- **Um fator do rubric não é objetivo.** "Estruturas de dados necessárias"
  foi classificado por inspeção, sem uma contagem por trás — é o único dos
  sete fatores nessa situação (Seção 2).
- **Amostra pequena.** Com só seis katas, os terços de cada fator são
  sensíveis a um único valor fora da curva — por exemplo, o fator "casos-
  limite" só tem os valores 4 e 5 entre as seis katas, então nenhuma kata
  cai no tier médio desse fator.
- **B1 é o par com o maior delta residual (6 pontos)**, mesmo mantendo o
  agrupamento. Ficou documentado na Seção 4; não foi escondido atrás da soma
  total.

## 8. Próximos passos

A S01-05/06/07 podem seguir com B1={K01,K02}, B2={K03,K04}, B3={K05,K06}
como definitivo. A definição operacional de LOC usada aqui — `SLOC` do
`radon raw` — deve ser a mesma usada pela coleta de métricas da S01-06,
para manter os números comparáveis entre a preparação e a coleta real.
