# K01 — Conflitos no pátio de docas

## Problema

Um terminal registra atracações em docas identificadas por texto. Uma doca
permanece indisponível desde o início da atracação até o fim da margem
operacional posterior à saída. Determine quais registros entram em conflito
com pelo menos outro registro da mesma doca.

## Entrada

- `agendamentos`: lista de registros com `id`, `doca`, `inicio` e `fim`;
- `margem`: número inteiro de minutos aplicado depois de cada `fim`.

Os horários usam o formato `HH:MM` e pertencem ao mesmo dia.

## Saída

Uma lista com os `id`s de todos os agendamentos conflitantes, na mesma ordem
em que aparecem na entrada.

## Regras e restrições

- `id` é único; `doca` é uma cadeia não vazia;
- `inicio` é anterior a `fim`; não há atracações que atravessem a meia-noite;
- `0 <= margem <= 60` e há no máximo 100 agendamentos;
- dois registros de docas distintas nunca conflitam;
- para a mesma doca, os períodos de indisponibilidade são comparados do
  `inicio` até `margem` minutos após o `fim`;
- se um período termina exatamente quando outro começa, eles são compatíveis.

## Exemplo

```text
agendamentos = [
  { id: "A1", doca: "Norte", inicio: "08:00", fim: "08:30" },
  { id: "B1", doca: "Norte", inicio: "08:45", fim: "09:00" },
  { id: "C1", doca: "Norte", inicio: "08:35", fim: "08:40" },
  { id: "D1", doca: "Sul",   inicio: "08:35", fim: "08:50" }
]
margem = 10

saida = ["A1", "B1", "C1"]
```

`D1` não aparece na saída porque está em uma doca diferente.

