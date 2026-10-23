# Revisão final do artigo — FIN-07 (#186)

Revisão de **22/10/2026**, branch `feature/FIN-07-revisao-final`, criada sobre
`feature/FIN-05-ameacas-externa-conclusao` (PR #259), que precisa ser mergeado
antes.

## Compilação

MiKTeX 25.12 (pdfTeX 4.23), com a sequência `pdflatex`, `bibtex`, `pdflatex`,
`pdflatex` descrita no README.

| Versão | Páginas (com referências) | Erros | Overfull |
|---|---|---|---|
| `main` em `5c104ed` + #259 | 25 | 0 | 0 |
| Esta revisão | **9** | 0 | 0 |

Todas as páginas renderizadas foram inspecionadas. O BibTeX não mostra mais
os avisos de ano vazio em `statsmodelsFleiss` e `sklearnPrecisionRecall`.

## Critérios de aceite

| Critério | Situação |
|---|---|
| Máximo de 10 páginas no template SBC | 9 páginas, contando as referências; `.sty` e `.bst` sem alteração. |
| Link do repositório e do GitHub Projects | Notas de rodapé na Seção 2.5, junto com o link do repositório do grupo replicado. |
| Revisão de texto, figuras e referências | Texto condensado; quatro figuras das RQ01–RQ04 mantidas, e as das RQ05 e RQ08 removidas; anos adicionados a duas referências. |

## O que foi condensado

O grupo decidiu condensar todas as seções, mantendo os detalhes no
repositório. Não houve número novo, recálculo, coleta nem mudança de
definição; todos os valores vêm do texto anterior.

- **Introdução e hipóteses**: contexto em dois parágrafos; as hipóteses das
  RQ01–RQ07 viraram uma lista com a previsão de cada uma; o complemento
  pós-piloto ficou em um parágrafo que preserva suas diferenças.
- **Metodologia**: a história de 255→500 e do adiamento ficou em duas frases,
  com referência a `Lab03/docs/`; funil com as linhas de Actions e metadados
  juntas; definições sem equações; validação manual em um parágrafo, com
  kappa no texto; métodos estatísticos em um parágrafo.
- **Resultados**: RQ01–RQ04 em texto corrido; a tabela de 18 testes da RQ06
  virou uma matriz de ε² com marca de significância; os contrastes Q1–Q4 e a
  RQ05 foram para o texto; as duas tabelas da RQ07 foram unidas; RQ08 e
  replicação viraram um parágrafo cada.
- **Discussão**: confronto das hipóteses em um parágrafo; literatura e
  implicações juntas; as quatro ameaças em um parágrafo cada, mantendo as
  mitigações da #183 e da #184.
- **Resumo e abstract**: reduzidos a cerca de 110 palavras.

## Correções de conteúdo

- Replicação: a comparação por métrica (#181) aparece como não realizada,
  sem permissão para abrir issues no repositório do grupo autor, e não mais
  como pendente.
- As issues #251–#254 estão no Project 7 como Done (verificado em
  22/10/2026). A frase que dizia que o vínculo não tinha sido verificado foi
  removida.

A redação completa anterior continua no histórico Git e nos arquivos
`validacao-*.md` de cada issue.
