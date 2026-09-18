# K05 — Alertas de leitura persistente

## Problema

Cada sensor possui uma faixa de leitura aceitável. Um alerta deve ser emitido
quando um mesmo sensor completa uma quantidade definida de leituras
consecutivas fora de sua faixa. Leituras de sensores diferentes podem estar
intercaladas.

## Entrada

- `sensores`: lista de registros com `sensor`, `minimo` e `maximo`;
- `consecutivas`: quantidade de leituras consecutivas necessária para um
  alerta;
- `leituras`: lista cronológica de registros com `id`, `sensor` e `valor`.

## Saída

`alertas`: lista de registros com `sensor` e `leitura`, em que `leitura` é o
id da leitura que emitiu o alerta. A ordem é a ordem dos alertas emitidos.

## Regras e restrições

- cada sensor aparece uma única vez; `minimo` é menor ou igual a `maximo`;
- `consecutivas` é um inteiro entre 2 e 5;
- toda leitura referencia um sensor existente e possui id único;
- um valor igual a `minimo` ou `maximo` está dentro da faixa;
- uma leitura dentro da faixa reinicia a sequência daquele sensor;
- um sensor emite no máximo um alerta por sequência ininterrupta de leituras
  fora da faixa;
- o alerta nasce apenas na leitura que completa a sequência;
- há no máximo 200 leituras.

## Exemplo

```text
sensores = [
  { sensor: "S1", minimo: 0, maximo: 10 },
  { sensor: "S2", minimo: 5, maximo: 8 }
]
consecutivas = 2

leituras = [
  { id: "L1", sensor: "S1", valor: 12 },
  { id: "L2", sensor: "S2", valor: 4 },
  { id: "L3", sensor: "S1", valor: 11 },
  { id: "L4", sensor: "S1", valor: 7 },
  { id: "L5", sensor: "S2", valor: 9 },
  { id: "L6", sensor: "S2", valor: 10 }
]

saida = [
  { sensor: "S1", leitura: "L3" },
  { sensor: "S2", leitura: "L5" }
]
```

