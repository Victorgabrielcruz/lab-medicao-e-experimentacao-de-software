# Conferência das ameaças externas e de conclusão — FIN-05 (#184)

Revisão de **22/10/2026**, branch `feature/FIN-05-ameacas-externa-conclusao`,
criada da `main` em `5c104ed` (PR #258). Só [discussao.tex](discussao.tex)
mudou: a subseção de validade externa foi reescrita e a de validade de
conclusão ganhou um parágrafo sobre tamanho da amostra e mitigações.

## Cobertura dos critérios

| Critério | Onde | Conteúdo |
|---|---|---|
| Ameaças externas (generalização da amostra) | Validade externa, parágrafos *População* e *Janela e fatores* | Ordem por estrelas, filtros de inclusão, janela única, idade e tipo de projeto. |
| Ameaças de conclusão (testes, tamanho da amostra) | Validade de conclusão, texto anterior e novo parágrafo | Testes sem ajuste e famílias de Holm (já existentes); significância de efeitos fracos com n=500, n efetivo por métrica, perda nos quartis, F1 sem intervalo. |
| Mitigações | Nos dois trechos | Funil declarado e conclusões restritas ao recorte; configuração versionada para outras janelas; tamanhos de efeito, permutações, RQ05 sem coleta incompleta, Holm, n por tabela. |

## Fontes numéricas

Nenhum número novo foi calculado; todos já estão no artigo ou nas tabelas:

- 500 elegíveis entre 1.064 avaliados: Seção de metodologia (funil).
- Mínimo de 30.088 e mediana de 45.049 estrelas: `analise/tabelas/rq06_cortes.csv`
  (limite inferior de Q1 e corte entre Q2 e Q3).
- CFR (a) com rho=0,155, n=500 e p=0,00052: `analise/tabelas/rq05_spearman.csv`.
- n de 469 a 500 por métrica: Tabela `tab:resumo-rq` de [resultados.tex](resultados.tex).
- 419 pares completos na RQ07 e 54 projetos excluídos na sensibilidade da RQ05:
  [resultados.tex](resultados.tex).
- F1 em 296 pares de 60 projetos: subseção *Heurística e rótulos* da discussão.

Não houve coleta, recálculo, alteração de cortes nem ajuste da heurística.
A subseção *Alcance da replicação cruzada* não foi alterada; a menção à
comparação pendente da #181 fica para a revisão final (#186).
