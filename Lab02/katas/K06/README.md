# K06 — Roteiros de inspeção

## Problema

Cada roteiro de inspeção define os pontos que devem ser visitados em uma
ordem específica. Os registros de visita de vários roteiros podem estar
intercalados. Avalie os registros e informe quais roteiros foram concluídos.

## Entrada

- `roteiros`: lista de registros com `rota` e `pontos`, sendo `pontos` a lista
  ordenada de identificadores de pontos daquele roteiro;
- `visitas`: lista cronológica de registros com `id`, `rota` e `ponto`.

## Saída

Um resultado com:

- `aceitos`: ids das visitas aceitas, na ordem recebida;
- `recusados`: ids das visitas recusadas, na ordem recebida;
- `concluidas`: ids das rotas que visitaram todos os seus pontos, na ordem
  definida em `roteiros`;
- `pendentes`: ids das demais rotas, também na ordem definida em `roteiros`.

## Regras e restrições

- cada rota aparece uma única vez e possui entre 2 e 10 pontos distintos;
- todo id de visita é único e referencia uma rota existente;
- uma visita é aceita somente quando seu `ponto` for o próximo ponto ainda
  não visitado no roteiro daquela rota;
- um ponto recusado não substitui a próxima parada esperada;
- depois de concluído, um roteiro não aceita novas visitas;
- há no máximo 50 roteiros e 200 visitas.

## Exemplo

```text
roteiros = [
  { rota: "A", pontos: ["P1", "P2", "P3"] },
  { rota: "B", pontos: ["X", "Y"] }
]

visitas = [
  { id: "V1", rota: "A", ponto: "P1" },
  { id: "V2", rota: "B", ponto: "Y" },
  { id: "V3", rota: "B", ponto: "X" },
  { id: "V4", rota: "A", ponto: "P3" },
  { id: "V5", rota: "A", ponto: "P2" },
  { id: "V6", rota: "A", ponto: "P3" },
  { id: "V7", rota: "B", ponto: "Y" }
]

saida = {
  aceitos: ["V1", "V3", "V5", "V6", "V7"],
  recusados: ["V2", "V4"],
  concluidas: ["A", "B"],
  pendentes: []
}
```

