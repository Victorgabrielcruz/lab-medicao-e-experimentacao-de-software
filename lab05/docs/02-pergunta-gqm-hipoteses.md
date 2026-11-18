# Pergunta de pesquisa, GQM e hipóteses

## Pergunta de pesquisa

> **Qual é o efeito do modo de journal (`DELETE` × `WAL`) e do nível de sincronização
> (`FULL` × `NORMAL`) sobre o desempenho do SQLite em cargas de escrita, leitura e mista?**

Os dois fatores são configurações de uma linha (`PRAGMA`) que qualquer aplicação pode
mudar. O padrão do SQLite é `DELETE` + `FULL`. A documentação oficial afirma que o WAL
"é significativamente mais rápido na maioria dos cenários" e que o `NORMAL` sincroniza
o disco "menos vezes que o `FULL`" ([WAL](https://www.sqlite.org/wal.html),
[PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous), acessados
em 17/11/2026). O estudo mede quanto isso vale, em quais cargas, e o que se perde em troca.

## Objetivo (GQM, template de Basili)

| Elemento | Definição |
|---|---|
| **Analisar** | o SQLite embutido no Python (módulo `sqlite3`) |
| **com o propósito de** | avaliar |
| **com respeito a** | desempenho (tempo e vazão de operações) |
| **do ponto de vista de** | desenvolvedores que embutem o SQLite em suas aplicações |
| **no contexto de** | execução local controlada, com cargas sintéticas de escrita, leitura e mista, em um desenho fatorial 2 × 2 |

## Perguntas

| Pergunta | Texto | Métricas |
|---|---|---|
| **Q1** | O modo `WAL` muda o desempenho em relação ao `DELETE`? | M1, M2, M3 |
| **Q2** | O nível `NORMAL` muda o desempenho em relação ao `FULL`? | M1, M2, M3 |
| **Q3** | A combinação `WAL` + `NORMAL` muda o desempenho em relação ao padrão (`DELETE` + `FULL`)? | M1, M2, M3 |
| **Q4** | O efeito de um fator depende do nível do outro (interação)? | M2 |

Cada pergunta é respondida **separadamente para cada carga**, porque a documentação
indica efeitos diferentes em escrita e leitura.

## Métricas

| Métrica | Definição | Entidade | Atributo | Medida | Escala |
|---|---|---|---|---|---|
| **M1** Tempo total | Tempo de relógio para executar as *n* operações de uma carga (s), medido com `time.perf_counter` | Produto (SQLite em execução) | Desempenho (externo) | Direta | Razão |
| **M2** Vazão | *n* operações ÷ M1 (operações/s) | Produto | Desempenho (externo) | Derivada | Razão |
| **M3** Razão de vazão | M2 da configuração ÷ mediana de M2 da configuração padrão na mesma carga (adimensional; 1,0 = sem ganho) | Produto | Desempenho (externo) | Derivada | Razão |

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

| Hipótese | Comparação | H0 | H1 |
|---|---|---|---|
| **H1** (Q1) | `WAL-FULL` × `DELETE-FULL` | A distribuição da vazão é a mesma nos dois modos | A distribuição da vazão difere |
| **H2** (Q2) | `DELETE-NORMAL` × `DELETE-FULL` | A distribuição da vazão é a mesma nos dois níveis | A distribuição da vazão difere |
| **H3** (Q3) | `WAL-NORMAL` × `DELETE-FULL` | A distribuição da vazão é a mesma na combinação e no padrão | A distribuição da vazão difere |

- São **9 testes** (3 hipóteses × 3 cargas), **bilaterais**, com **α = 0,05** e correção de
  Holm para comparações múltiplas.
- Cada comparação isola um fator e mantém o outro no padrão. Assim, H1 e H2 medem o
  efeito puro de cada fator e H3 mede o ganho da combinação mais citada como
  "recomendada para produção".
- **Q4 (interação)** é respondida de forma descritiva, com o gráfico de interação das
  medianas, sem teste formal.
- Cada teste é acompanhado do **tamanho do efeito** e de M3. A escolha do teste (por
  exemplo, Mann-Whitney com delta de Cliff ou t de Welch com d de Cohen) fica no plano
  de análise (S01-07), depois de olhar a distribuição dos dados do piloto.

**Expectativa prévia (não usada nos testes).** Pela documentação, esperamos ganho do WAL e
do `NORMAL` nas cargas com escrita, porque os dois reduzem as chamadas de `fsync`, e
diferença pequena na leitura: o WAL "pode ser 1% ou 2% mais lento" em cargas só de
leitura. Mesmo assim, os testes são bilaterais, para não supor a direção do efeito.

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
