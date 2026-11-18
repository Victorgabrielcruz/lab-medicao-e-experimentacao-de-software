# Pergunta de pesquisa, GQM e hipóteses

## Pergunta de pesquisa

> **A recomendação popular de configurar o SQLite com `WAL` + `synchronous=NORMAL` se
> sustenta? Quanto desempenho o padrão (`DELETE` + `FULL`) deixa na mesa, e quanto desse
> ganho exige abrir mão da durabilidade?**

Os dois fatores são configurações de uma linha (`PRAGMA`). Guias e respostas em fóruns
repetem `WAL` + `NORMAL` como "a configuração de produção", e a documentação oficial
afirma que o WAL "é significativamente mais rápido na maioria dos cenários"
([WAL](https://www.sqlite.org/wal.html), acessado em 17/11/2026). Só que as duas trocas
têm naturezas diferentes:

- trocar `DELETE` por `WAL`, mantendo o `FULL`, **não custa garantia**: `WAL` + `FULL`
  é ACID, enquanto o padrão "pode não ser durável";
- trocar `FULL` por `NORMAL` **custa garantia**: com `WAL`, as últimas transações
  confirmadas podem ser perdidas numa queda de energia
  ([PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous)).

A questão crítica, então, não é "o WAL é mais rápido?". É **de onde vem o ganho**: se
quase todo ele vier do WAL, abrir mão da durabilidade com o `NORMAL` é um risco
desnecessário.

## Objetivo (GQM, template de Basili)

| Elemento | Definição |
|---|---|
| **Analisar** | o SQLite embutido no Python (módulo `sqlite3`) |
| **com o propósito de** | avaliar o custo-benefício das configurações recomendadas |
| **com respeito a** | desempenho (tempo e vazão de operações) e à garantia de durabilidade cedida em troca |
| **do ponto de vista de** | desenvolvedores que embutem o SQLite em suas aplicações |
| **no contexto de** | execução local controlada, com cargas sintéticas de escrita, leitura e mista, em um desenho fatorial 2 × 2 |

## Perguntas

| Pergunta | Texto | Por que é crítica | Métricas |
|---|---|---|---|
| **Q1** | Quanto de vazão o padrão desperdiça em relação ao `WAL`, **sem abrir mão de nenhuma garantia** (`WAL-FULL` × `DELETE-FULL`)? | Se o ganho for grande, manter o padrão é deixar desempenho na mesa sem motivo | M2, M3 |
| **Q2** | Depois de adotar o WAL, quanto o `NORMAL` acrescenta (`WAL-NORMAL` × `WAL-FULL`)? Esse ganho marginal justifica perder as últimas transações numa queda de energia? | Testa a recomendação popular: um ganho marginal pequeno torna o `NORMAL` um risco sem retorno | M2, M3 |
| **Q3** | O "atalho" de ficar no `DELETE` e só baixar para `NORMAL` (`DELETE-NORMAL` × `DELETE-FULL`) dá um ganho comparável ao do WAL? E o ganho do `NORMAL` depende do modo de journal (interação)? | O atalho é a configuração com o pior risco da tabela (pode corromper o banco); se ganhar menos que o WAL, é dominado | M2, M3 |
| **Q4** | O WAL penaliza a leitura, como a própria documentação admite ("1% ou 2% mais lento")? A diferença é detectável e tem relevância prática? | Confere uma afirmação do fornecedor e verifica se o custo aparece para quem só lê | M2, M3 |

Q1 a Q3 importam nas cargas com escrita (escrita e mista). Q4 olha a carga de leitura.
Mesmo assim, todas as comparações são feitas nas três cargas, para não escolher onde
olhar depois de ver os dados.

## Métricas

| Métrica | Definição | Entidade | Atributo | Medida | Escala |
|---|---|---|---|---|---|
| **M1** Tempo total | Tempo de relógio para executar as *n* operações de uma carga (s), medido com `time.perf_counter` | Produto (SQLite em execução) | Desempenho (externo) | Direta | Razão |
| **M2** Vazão | *n* operações ÷ M1 (operações/s) | Produto | Desempenho (externo) | Derivada | Razão |
| **M3** Razão de vazão | Mediana de M2 da configuração tratada ÷ mediana de M2 da configuração de referência da comparação, na mesma carga (adimensional; 1,0 = sem ganho) | Produto | Desempenho (externo) | Derivada | Razão |

O desempenho é um **atributo externo**: depende do ambiente (disco, sistema operacional,
versão do SQLite) além do software. Por isso cada execução grava o ambiente em
`data/ambiente.json`.

**Estatísticas permitidas.** As três métricas estão na escala de razão, que admite todas
as estatísticas: média, mediana, desvio-padrão, coeficiente de variação e razões ("2× mais
rápido"). Como tempos de execução costumam ter distribuição assimétrica, com cauda à
direita, a **mediana** e o **IQR** são as medidas de resumo principais. Os fatores e a
carga são variáveis **nominais**.

## Variáveis

| Tipo | Variável | Níveis ou valor |
|---|---|---|
| Independente (fator) | `journal_mode` | `DELETE`, `WAL` |
| Independente (fator) | `synchronous` | `FULL`, `NORMAL` |
| Bloco | Carga | escrita (1.000 transações de 1 `INSERT`), leitura (10.000 `SELECT` por chave), mista (2.000 operações, 70% leitura) |
| Dependente | M1, M2 (e M3, derivada de M2) | — |
| Controlada | Máquina, versão do Python e do SQLite, linhas iniciais (10.000), tamanho do registro (256 bytes), banco novo por execução, aquecimento descartado, ordem aleatorizada com semente fixa | `experimento/config.py` |

## Hipóteses

Para cada carga *c* ∈ {escrita, leitura, mista}, comparando a vazão (M2):

| Hipótese | Pergunta | Comparação | H0 | H1 |
|---|---|---|---|---|
| **H1** | Q1, Q4 | `WAL-FULL` × `DELETE-FULL` | A distribuição da vazão é a mesma | A distribuição da vazão difere |
| **H2** | Q2 | `WAL-NORMAL` × `WAL-FULL` | A distribuição da vazão é a mesma | A distribuição da vazão difere |
| **H3** | Q3 | `DELETE-NORMAL` × `DELETE-FULL` | A distribuição da vazão é a mesma | A distribuição da vazão difere |

- São **9 testes** (3 hipóteses × 3 cargas), **bilaterais**, com **α = 0,05** e correção de
  Holm para comparações múltiplas.
- Cada comparação muda **um único fator**. Assim, a soma dos passos explica de onde vem
  o ganho total do padrão até `WAL-NORMAL`: H1 mede o passo sem custo de garantia, e H2 o
  passo que custa durabilidade.
- **Interação (Q3):** compara-se o ganho do `NORMAL` sob `DELETE` (H3) com o ganho sob
  `WAL` (H2), pelas razões M3 e pelo gráfico de interação das medianas, sem teste formal.
- **Relevância prática (Q2 e Q4):** a significância estatística não basta. Para
  responder se "vale a pena", cada comparação traz M3 com intervalo de confiança
  (bootstrap). Na leitura (Q4), verifica-se se o intervalo de M3 fica dentro da faixa de
  ±2% que a documentação admite.
- Cada teste é acompanhado do **tamanho do efeito**. A escolha do teste (por exemplo,
  Mann-Whitney com delta de Cliff ou t de Welch com d de Cohen) fica no plano de análise
  (S01-07), depois de olhar a distribuição dos dados do piloto.

**Expectativa prévia (não usada nos testes).** Como o WAL já elimina a maior parte das
chamadas de `fsync` (a documentação diz que ele escreve o conteúdo "uma vez, em vez de
duas"), esperamos que **H1 concentre a maior parte do ganho** nas cargas com escrita e
que o ganho marginal de H2 seja menor. Se isso se confirmar, a recomendação
`WAL` + `NORMAL` troca durabilidade por pouco. Os testes continuam bilaterais, para não
supor a direção do efeito.

## Armadilhas de medição

- **Lei de Goodhart e de Campbell.** Se a vazão virar a meta, a configuração "vencedora" é
  sempre a que sincroniza menos. O `synchronous=OFF` é o caso extremo: é mais rápido,
  mas a documentação avisa que o banco pode ser **corrompido** após uma queda de energia.
  Por isso o `OFF` ficou fora do estudo: não é uma escolha aceitável em produção.
- **Falácia de McNamara.** O estudo mede só o que é fácil de medir (velocidade) e não mede a
  **durabilidade**. Pela documentação oficial, `WAL` + `NORMAL` continua consistente, mas
  "uma transação confirmada pode ser desfeita após uma queda de energia", e `DELETE` +
  `NORMAL` tem chance "muito pequena, mas não nula" de corromper o banco em sistemas de
  arquivos antigos. A conclusão precisa apresentar esse custo junto com o ganho de
  desempenho, e não só o número de vazão.

| Configuração | Garantia segundo a documentação |
|---|---|
| `DELETE` + `FULL` (padrão) | Atômica, consistente e isolada; durável dependendo do sistema de arquivos |
| `DELETE` + `NORMAL` | Pode não ser consistente após queda de energia (risco muito pequeno) |
| `WAL` + `FULL` | ACID |
| `WAL` + `NORMAL` | Consistente, mas pode perder as últimas transações após queda de energia |

Fonte: [PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous), acessado em 17/11/2026.
