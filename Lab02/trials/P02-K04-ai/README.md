# K04 — Credenciais de visita

## Problema

Cada credencial de visita possui um horário de expiração e começa no estado
`NOVA`. O registro de eventos pode liberá-la, utilizá-la ou revogá-la.
Avalie os eventos recebidos e informe o estado final de todas as credenciais.

## Entrada

- `credenciais`: lista de registros com `credencial` e `expiraEm`;
- `eventos`: lista cronológica de registros com `id`, `credencial`, `momento`
  e `acao` (`LIBERAR`, `USAR` ou `REVOGAR`).

Os horários usam o formato `HH:MM` e pertencem ao mesmo dia.

## Saída

Um resultado com:

- `aceitos`: ids dos eventos aceitos, na ordem recebida;
- `recusados`: ids dos eventos recusados, na ordem recebida;
- `statusFinal`: o estado de cada credencial, na ordem definida em
  `credenciais`.

## Regras e restrições

- cada credencial aparece uma única vez e começa no estado `NOVA`;
- ids de evento são únicos; cada evento referencia uma credencial existente;
- os horários dos eventos são não decrescentes;
- nenhuma ação é aceita após o horário `expiraEm`; no horário exato de
  expiração, a ação ainda pode ser aceita;
- `LIBERAR` só é aceita para uma credencial `NOVA` e muda seu estado para
  `LIBERADA`;
- `USAR` só é aceita para uma credencial `LIBERADA` e muda seu estado para
  `UTILIZADA`;
- `REVOGAR` só é aceita para uma credencial `NOVA` ou `LIBERADA` e muda seu
  estado para `REVOGADA`;
- eventos recusados não alteram o estado; `UTILIZADA` e `REVOGADA` são
  estados finais;
- há no máximo 100 credenciais e 200 eventos.

## Exemplo

```text
credenciais = [
  { credencial: "V1", expiraEm: "10:30" },
  { credencial: "V2", expiraEm: "09:00" }
]

eventos = [
  { id: "E1", credencial: "V1", momento: "10:00", acao: "LIBERAR" },
  { id: "E2", credencial: "V2", momento: "09:00", acao: "LIBERAR" },
  { id: "E3", credencial: "V2", momento: "09:01", acao: "USAR" },
  { id: "E4", credencial: "V1", momento: "10:20", acao: "USAR" },
  { id: "E5", credencial: "V1", momento: "10:25", acao: "REVOGAR" }
]

saida = {
  aceitos: ["E1", "E2", "E4"],
  recusados: ["E3", "E5"],
  statusFinal: [
    { credencial: "V1", status: "UTILIZADA" },
    { credencial: "V2", status: "LIBERADA" }
  ]
}
```
