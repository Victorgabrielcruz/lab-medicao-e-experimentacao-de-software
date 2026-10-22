# S03-12 — Resultados RQ07 no artigo (#178)

Implementação na branch existente `feat/S03-07-RQ07`, atualizada com a
main que integra as análises #173/#174. A fonte principal continua sendo
`artigo/main.tex`, no template SBC existente.

## Critérios de aceite

- Combinações C1/C2/C3 apresentadas em `resultados.tex`, com frequência de
  releases estáveis e recuperação fixas. C1 usa LT(b)+CFR(a), igual à #169;
  C2 usa LT(a)+CFR(a), e C3 usa LT(b)+CFR(b).
- Percentuais de mudança e kappa de Cohen quadrático apresentados nos três
  pares, com n, exclusões e quantidade de projetos que mudam de classe.
- Robustez discutida por disponibilidade, qualidade e pesos lineares;
  limitações de construto, cobertura e hipóteses não testadas preservadas.

## Fontes e conferência numérica

As fontes versionadas ficam em `analise/rq07/`: `classificacoes.csv`,
`combinacoes.json`, `robustez.csv`, `robustez.json` e `robustez.md`.
O dataset de entrada é o CSV final de 500, SHA-256
`2552ba6b0779e895d01bea88742cb668ee1812a8369a224ed5281708140b30bd`.
As definições e as quatro coortes seguem as #173/#174, sem nova seleção
de combinações, coleta ou imputação.

| Par | n completo | Excluídos | Mudaram | Mudança | Kappa quadrático |
|---|---:|---:|---:|---:|---:|
| C1×C2 | 468 | 32 | 68 | 14,53% | 0,8411 |
| C1×C3 | 467 | 33 | 179 | 38,33% | 0,5635 |
| C2×C3 | 467 | 33 | 197 | 42,18% | 0,4494 |

A tabela LaTeX foi conferida com `robustez.csv`. Uma contagem independente,
pareada por ID em `classificacoes.csv`, confirmou os denominadores e as
quantidades de mudanças. As referências LaTeX da nova seção têm labels
existentes. A reexecução abaixo produziu os cinco arquivos com bytes
idênticos aos versionados; não alterou as fontes:

```powershell
# A partir de Lab03
.venv/Scripts/python.exe -m pipeline.rq07_robustez --saida data/processed/validacao-artigo-178
```

SHA-256 das duas fontes tabulares principais:

- `classificacoes.csv`: `d35f6f0cde9171b3731170fc6e632184e9cafa62f625bfc66939fd78efac6e01`.
- `robustez.csv`: `127c051297fbe804dac23fbed4d26a163c73f53329821a0e38ec93cdd79fc33c`.

## Coerência do artigo e compilação

A nova seção distingue os resultados principais de casos completos das
notas gerais parciais nos 500 projetos. Retirou-se o resumo antigo de
37% da seção C1, substituindo-o por referência à RQ07, onde os 37,4% da
coorte com notas parciais são separados dos 38,33% em pares completos.
Resumo, abstract, conclusão e referências internas de metodologia/discussão
foram alinhados para não apresentar toda a RQ07 como futura.

O artigo completo compilou **com sucesso** no compilador nativo do editor
após a edição, usando a pasta `Lab03/artigo` e `main.tex` como documento
principal. A tentativa com raiz `Lab03` encontrou uma restrição de leitura
em `.pytest_cache`; a compilação pela pasta do artigo foi bem-sucedida.
Não se afirma nova inspeção visual de todas as páginas nem conclusão da
revisão de limite de páginas da #186.

A avaliação final oficial já disponível em
`validacao/avaliacao-heuristica/final-500/avaliacao.json` registra 296/300
releases avaliadas e quatro indeterminadas. A seção mantém esse limite e
não confunde releases da amostra-ouro com repositórios excluídos por falta
de métricas. Não afirma validação integral nem identificação de incidentes
em produção. Pré-releases, tags e a hipótese sobre classes extremas não
foram testadas pelas combinações disponíveis. A análise das outras
hipóteses permanece no escopo da #179.
