# K03 — Cadeia de custódia de remessas

## Problema

Uma remessa deve registrar quatro etapas, nesta ordem: `COLETA`, `LACRE`,
`DESPACHO` e `RECEBIMENTO`. Os eventos de várias remessas podem estar
intercalados no registro. Avalie cada evento e informe quais remessas ficaram
pendentes ao final.

## Entrada

`eventos`: lista ordenada de registros com `id`, `remessa` e `etapa`.

## Saída

Um resultado com:

- `aceitos`: ids dos eventos aceitos, na ordem recebida;
- `recusados`: ids dos eventos recusados, na ordem recebida;
- `pendentes`: ids das remessas que tiveram ao menos uma etapa aceita, mas
  ainda não chegaram a `RECEBIMENTO`, na ordem de sua primeira ocorrência.

## Regras e restrições

- `id` de evento é único; `remessa` é uma cadeia não vazia;
- `etapa` é exatamente uma entre `COLETA`, `LACRE`, `DESPACHO` e
  `RECEBIMENTO`;
- a primeira etapa aceita de uma remessa deve ser `COLETA`;
- cada etapa seguinte só é aceita quando for a próxima da sequência;
- uma etapa recusada não muda a etapa já confirmada da remessa;
- depois de `RECEBIMENTO`, nenhum evento adicional daquela remessa é aceito;
- há no máximo 200 eventos.

## Exemplo

```text
eventos = [
  { id: "E1", remessa: "R1", etapa: "COLETA" },
  { id: "E2", remessa: "R1", etapa: "DESPACHO" },
  { id: "E3", remessa: "R2", etapa: "LACRE" },
  { id: "E4", remessa: "R1", etapa: "LACRE" },
  { id: "E5", remessa: "R1", etapa: "DESPACHO" },
  { id: "E6", remessa: "R1", etapa: "RECEBIMENTO" },
  { id: "E7", remessa: "R3", etapa: "COLETA" }
]

saida = {
  aceitos: ["E1", "E4", "E5", "E6", "E7"],
  recusados: ["E2", "E3"],
  pendentes: ["R3"]
}
```

