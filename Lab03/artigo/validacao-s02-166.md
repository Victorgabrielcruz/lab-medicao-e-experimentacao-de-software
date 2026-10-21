# Validação da revisão metodológica — S02-16 (#166)

## Integração do PR #232 — 21/10/2026

O conflito com a `main` foi resolvido preservando sua cronologia da retomada,
inclusão de Grafana e funil de 37.383 candidatos encontrados, 1.064 avaliados
e 500 elegíveis. Foi acrescentado o encerramento real dos compares em
21/10, com código 0, `execucao_completa=true`, 34.151 comparações e os
diagnósticos de incompletude. A referência do artigo aponta agora para o
CSV final, preservando os cortes históricos.

O compilador do editor desktop confirmou sucesso de `main.tex` após essa
resolução. A suíte completa passou no checkout isolado: 913 testes, com
94,16% de cobertura de `pipeline` em Python 3.12. O teste do checkpoint
auxiliar confere o retorno resumido e a preservação dos detalhes no disco. Os
rótulos B e a decisão de retomada recebidos da `main` foram preservados;
o CSV final não foi alterado pela resolução.

## Atualização de 20/10/2026

`metodologia.tex` incorpora a decisão de retomada, a captura pública de
500 elegíveis em 1.064 candidatos e o funil 1064 → 933 → 932 → 569 → 501 → 500.
O requisito quantitativo e o de completude de runs são etapas distintas.
Compares e processamento final continuam parciais; a validação humana da
heurística CFR(b) continua pendente. O sorteio de 60 projetos/300 releases
é mantido sobre 255, e as 51 decisões ausentes de C permanecem explícitas.
A evidência de compilação e os hashes abaixo pertencem à revisão de 15/10;
não comprovam a compilação desta versão. A validação atual e a lista das
issues estão em [atualizacao-sprint02-victor-500.md](../docs/atualizacao-sprint02-victor-500.md).

O compilador do editor desktop confirmou **sucesso do artigo integral**
`main.tex` nesta revisão de 20/10/2026. Isso valida a compilação da fonte;
resumos e resultados históricos do piloto continuam preservados e exigem
integração científica posterior. Hashes atuais e validação do CSV estão em
[`validacao.json`](../entregas/s02-03-dataset-500/validacao.json).

## Evidência histórica de 15/10/2026

Revisão de 15/10/2026 na branch `feat/s02-16-metodologia-166`, a partir de
`11b08425d494943790d89020b670e15da4eba722`. Escopo: [metodologia.tex](metodologia.tex),
[README.md](README.md) e esta evidência. Nenhuma alteração nos coletores,
cache, população ou arquivos de dados.

## Estado da amostra e decisões registradas

- Extração encerrada por instrução humana em **15/10/2026 às 15h09min11s
  (America/Sao_Paulo), 18h09min11s UTC**; coletor no commit `4ddbab9`.
- **255 IDs elegíveis únicos**, consumidos pelo progresso oficial, entre
  **561 candidatos avaliados**. O mínimo original de 300 e a meta de 500
  não foram atingidos; o pipeline original foi interrompido.
- A [priorização por custo observado](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/blob/5d311c2/Lab03/docs/decisoes-coleta-final.md)
  previa retomar Grafana após 300. A
  [decisão posterior de encerramento](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/blob/f1306c7/Lab03/docs/decisao-encerramento-255.md)
  interrompeu essa espera em 255; Grafana não foi liberado e não integra
  a população. A metodologia explicita o possível viés de custo.
- Janela UTC: `[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.
  Cinco releases estáveis, cinquenta runs válidos, evento `push`, default
  branch e diagnósticos de completude permanecem como critérios.
- Comparações ausentes continuam diagnosticadas; somente dados locais
  válidos alimentam o lead time, com cobertura parcial indicada quando
  pertinente. CFR (b) depende de #161 e, sem fonte, permanece nula.
  Documentar o procedimento não declara a consolidação #153 concluída.

## Conferências locais

O manifesto privado `Lab03/data/processed/sprint02-agentes/encerramento-amostra.json`
e seu snapshot `amostra-encerrada-255-20261015T180911Z` foram lidos sem
alteração ou requisição externa. A validação em **18h15min20s UTC** confirmou:

- **574 arquivos** do snapshot correspondentes aos SHA-256 do manifesto;
- **255 identidades** de candidatos correspondentes aos IDs oficiais,
  sem duplicatas e contidas nos 561 IDs consumidos;
- contagens coerentes com o progresso, janela e configuração compatíveis,
  Grafana ausente e `adiados_liberados=false`;
- preservação dos arquivos `main.tex`, `introducao.tex`,
  `hipoteses_complementares.tex`, `resultados.tex`, `discussao.tex`,
  `conclusao.tex`, `referencias.bib`, `sbc-template.sty` e `sbc.bst` frente
  à base, após normalizar apenas finais de linha;
- preservação literal dos blocos de metadados, frequência de deploy, CFR,
  recuperação e censura da metodologia. O lead time recebeu somente a
  explicação da disponibilidade local após o encerramento;
- resolução dos links locais do README e existência dos caminhos versionados
  das decisões nos objetos Git de `5d311c2` e `f1306c7`. Não foi realizada
  requisição HTTP para declarar disponibilidade remota desses links;
- `git diff --check` sem erros.

Impressões digitais das entradas e fontes conferidas:

| Artefato | SHA-256 |
|---|---|
| Manifesto privado de encerramento | `ffd16cf789c813f65eea2d47ca124c882fd169075864dfd3ffaa856112b8ad11` |
| Contexto dos checkpoints | `efc8b16132452557c7fd291b70cef74d2c97e7dd53b0b36dce76db5a17362609` |
| Fonte de candidatos com política | `c1cf8800c17ffbaff90408685fa24a4ab52caa2105c580f6fba641e729d94382` |
| metodologia.tex | `ffdd349f62b3e9892fdb8b2eb440b25872b3e119d61f7e12bc03dc0ba094c9a1` |
| README.md | `bdfe0a85bcea355c241fe6ea94cadda1da858cf188c90c0678d5fbe773477b99` |
| Wrapper privado da compilação isolada | `6d19115ab1dfe3a5aeaaf72a23a925438b4454a742b89a6ad458db8b4eae4656` |

IDs detalhados, dados brutos, cache, manifesto e relatório integral de
verificação permanecem locais; esta evidência publica apenas contagens,
critérios e hashes. Não foram feitas novas consultas à API.

## Compilação e limites da entrega

O compilador nativo confirmou **sucesso da seção isolada**. O wrapper
privado contém uma classe `article`, pacotes `inputenc`, `fontenc`, `babel`,
`url` e `amsmath` e o conteúdo integral, sem alteração, de `metodologia.tex`.
Sua impressão digital está na tabela. Ele não usa inputs externos.

**O artigo integral revisado não foi compilado nesta entrega**, e não se
alega sincronização com Overleaf. As seis páginas, PDF e ZIP históricos
referidos no README pertencem ao piloto #150. Resumos, resultados,
discussão, conclusão e hipóteses não foram reescritos com resultados dos
255; sua integração demanda revisão e compilação próprias.

A entrega validada atende ao escopo documental revisado de #166 e fica
pronta para revisão humana. Não fecha automaticamente a issue #166 nem
converte a coleta interrompida em cumprimento do mínimo da #151.
