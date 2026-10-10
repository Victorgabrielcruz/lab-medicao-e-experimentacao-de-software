# Artigo do Lab03

Seções do artigo em LaTeX, prontas para o projeto no Overleaf com o template da SBC (S01-22).

| Arquivo | Conteúdo |
|---|---|
| `introducao.tex` | Seção 1: introdução e uma hipótese informal para cada RQ, de RQ01 a RQ07 |
| `referencias.bib` | Referências citadas nas seções acima |

No Overleaf, cada seção entra com `\input{introducao}`, e as referências com `\bibliography{referencias}`.

## Registro das hipóteses

As RQ01 a RQ04 foram adicionadas na issue #137. As RQ05 a RQ07 foram redigidas
na S01-15 (#143), em **08/10/2026**, a partir do enunciado e das definições do
estudo, sem consultar resultados de coleta ou de análise:

- **RQ05:** associação negativa entre frequência de deploy e CFR, com uma
  associação esperada mais fraca para o proxy de CI.
- **RQ06:** melhor desempenho esperado nos quartis superiores de estrelas,
  contribuidores e idade, os três fatores previstos para comparação.
- **RQ07:** mudanças de categoria entre definições, com maior concordância
  esperada entre referência e releases com pré-releases do que entre referência
  e tags.

Essas afirmações são expectativas a confrontar com os dados, não resultados
observados. O histórico Git registra a versão original e o momento da redação
de cada conjunto. O início da **coleta principal** deve ser registrado na
metodologia ou na issue correspondente e comparado com esses commits para
verificar o critério de hipóteses anteriores à coleta. A data do commit,
isoladamente, não comprova essa ordem.

Se a coleta principal já tiver começado antes da redação, registre essa
limitação: as hipóteses foram escritas sem consultar resultados, mas isso não
equivale a terem sido escritas antes da coleta. Preserve a versão original;
eventuais revisões posteriores devem ser identificadas como tais, com data e
justificativa.
