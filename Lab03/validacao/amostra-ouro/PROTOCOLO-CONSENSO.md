# Protocolo de consenso da amostra-ouro (#160)

O consenso é aplicado **depois** do kappa de Fleiss (#159), sobre as planilhas
independentes de A, B e C, que não são alteradas.

## Regras

1. **Item unânime:** o rótulo comum dos três é o rótulo de consenso, sem discussão.
2. **Item com maioria (dois votos iguais):** a maioria é a proposta levada à
   discussão. O grupo pode aceitá-la ou decidir outro valor, com justificativa.
3. **Três categorias diferentes:** discussão conjunta até uma decisão
   fundamentada, com justificativa obrigatória.
4. **Sem acordo:** o item fica pendente (decisão vazia), com o motivo em
   `justificativa`. Pendências não viram `nao` nem outra categoria.
5. A heurística da #161 não é usada como desempate.
6. Cada decisão registra participantes e data. Só valores do
   [livro de códigos](LIVRO-CODIGOS.md) são aceitos.

## Arquivos

- [decisoes-consenso.csv](decisoes-consenso.csv): uma linha por item
  divergente, com `dimensao`, chave (`repo_id` e, para `corretiva`,
  `release_id`), `decisao`, `justificativa`, `participantes` e `data`.
- [consenso_repositorios.csv](consenso_repositorios.csv) e
  [consenso_releases.csv](consenso_releases.csv): rótulo final de cada item e
  sua origem (`unanime`, `maioria`, `discussao` ou `pendente`).
- [consenso.json](consenso.json): SHA-256 das entradas, contagem por origem e,
  para cada divergência, os votos de A, B e C, a maioria, a decisão e o registro.

Para regerar, a partir de `Lab03`:

```bash
python -m pipeline.consenso
```

O comando recusa item divergente sem decisão, decisão para item unânime,
valor fora do livro de códigos, decisão fora da maioria sem justificativa e
decisão sem participantes ou data.

## Resultado (reunião de 20/10/2026)

Participantes: rotuladores A, B e C. Dos 420 itens, 405 foram unânimes e 15
divergentes. Nenhum item ficou pendente.

| Dimensão | Unânimes | Maioria aceita | Discussão |
|---|---:|---:|---:|
| `tipo_projeto` | 52 | 7 | 1 |
| `releases_sao_entregas_reais` | 59 | 1 | 0 |
| `corretiva` | 294 | 6 | 0 |

Divergências e decisões:

| Dimensão | Item | A | B | C | Decisão |
|---|---|---|---|---|---|
| `tipo_projeto` | apple/container | infraestrutura | ferramenta_dev | ferramenta_dev | ferramenta_dev |
| `tipo_projeto` | coder/code-server | aplicacao | ferramenta_dev | ferramenta_dev | ferramenta_dev |
| `tipo_projeto` | denoland/deno | infraestrutura | ferramenta_dev | infraestrutura | infraestrutura |
| `tipo_projeto` | jgm/pandoc | aplicacao | biblioteca | ferramenta_dev | ferramenta_dev (discussão) |
| `tipo_projeto` | mozilla/pdf.js | biblioteca | aplicacao | biblioteca | biblioteca |
| `tipo_projeto` | nodejs/node | infraestrutura | ferramenta_dev | infraestrutura | infraestrutura |
| `tipo_projeto` | slidevjs/slidev | aplicacao | ferramenta_dev | ferramenta_dev | ferramenta_dev |
| `tipo_projeto` | zed-industries/zed | aplicacao | ferramenta_dev | ferramenta_dev | ferramenta_dev |
| `releases_sao_entregas_reais` | meteor/meteor | nao | sim | sim | sim |
| `corretiva` | Alishahryar1/free-claude-code v6.3.2 | nao | sim | sim | sim |
| `corretiva` | browser-use/browser-use 0.10.1 | nao | sim | nao | nao |
| `corretiva` | Egonex-AI/Understand-Anything v2.0.0 | nao | nao | sim | nao |
| `corretiva` | openclaw/openclaw v1.2.0 | nao | sim | sim | sim |
| `corretiva` | payloadcms/payload v3.68.1 | nao | sim | sim | sim |
| `corretiva` | vectorize-io/hindsight v0.0.16 | nao | sim | nao | nao |

Os rótulos de consenso de `corretiva` são a referência para avaliar a
heurística da CFR (b) na #162.
