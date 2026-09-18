# K02 — Compartimentos de coleta

## Problema

Uma central mantém compartimentos independentes, cada um com capacidade
máxima conhecida. Os movimentos são recebidos em ordem e podem adicionar ou
retirar unidades de um compartimento. Identifique os movimentos aceitos, os
recusados e o saldo final de cada compartimento.

## Entrada

- `capacidades`: coleção de pares `compartimento` e `capacidade`;
- `movimentos`: lista ordenada de registros com `id`, `compartimento`, `tipo`
  (`ENTRADA` ou `SAIDA`) e `quantidade`.

## Saída

Um resultado com:

- `aceitos`: ids dos movimentos aceitos, na ordem recebida;
- `recusados`: ids dos movimentos recusados, na ordem recebida;
- `saldoFinal`: saldo de cada compartimento, na ordem definida em
  `capacidades`.

## Regras e restrições

- cada compartimento aparece uma única vez em `capacidades` e começa com
  saldo zero;
- cada capacidade é inteira e está entre 1 e 1.000;
- todo movimento referencia um compartimento existente, possui id único e
  quantidade inteira positiva;
- uma `ENTRADA` é recusada se o saldo resultante ultrapassar a capacidade;
- uma `SAIDA` é recusada se o saldo resultante for negativo;
- um movimento recusado não altera o saldo do seu compartimento;
- há no máximo 200 movimentos.

## Exemplo

```text
capacidades = [
  { compartimento: "A", capacidade: 10 },
  { compartimento: "B", capacidade: 5 }
]

movimentos = [
  { id: "M1", compartimento: "A", tipo: "ENTRADA", quantidade: 6 },
  { id: "M2", compartimento: "A", tipo: "SAIDA",   quantidade: 7 },
  { id: "M3", compartimento: "B", tipo: "ENTRADA", quantidade: 5 },
  { id: "M4", compartimento: "B", tipo: "ENTRADA", quantidade: 1 },
  { id: "M5", compartimento: "A", tipo: "SAIDA",   quantidade: 2 }
]

saida = {
  aceitos: ["M1", "M3", "M5"],
  recusados: ["M2", "M4"],
  saldoFinal: [
    { compartimento: "A", saldo: 4 },
    { compartimento: "B", saldo: 5 }
  ]
}
```

