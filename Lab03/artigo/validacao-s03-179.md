# Conferência da discussão — S03-13 (#179)

Revisão de **22/10/2026**, branch `feat/s03-13-discussao-hipoteses-179`,
criada da `main` atualizada em `aac76df` (PR #250). A base já incorpora
RQ01–RQ07, incluindo #177 e #178. O documento principal continua sendo
`artigo/main.tex`, no template existente.

## Cobertura dos critérios

[discussao.tex](discussao.tex) confronta cada componente das hipóteses,
com implicações e relação com literatura. As interpretações são descritivas,
não decisões formais de aceitar hipóteses alternativas por testes de nulidade.

| RQ | Expectativa e evidência | Alcance da conclusão |
|---|---|---|
| RQ01 | Mediana 2,08 releases/mês, High 24,0%, Medium 49,6%, Elite 2,4%, cauda até 51,3/semana. | Parcial: mediana, raridade de Elite e cauda compatíveis; maioria High não sustentada. A faixa de 1–3/mês não implica High nos cortes do enunciado. |
| RQ02 | Mediana por commit 12,63 dias; Medium 29,8% dos 500; LT(a)>LT(b) em 303/499 pares (60,7%); medianas agregadas 268h e 303h. | Parcial: faixa de 1–3 semanas e direção em parte dos pares compatíveis; maioria Medium não sustentada. Comparação pareada difere da comparação entre medianas. |
| RQ03 | Medianas CFR(a)=5,34% e CFR(b)=43,96%; mesma classe da métrica em 104/498 pares (20,88%). | Faixa prevista de 10–20% em (a) contrariada; diferença entre variantes compatível. Não estima falhas em produção nem erro entre proxies. |
| RQ04 | Mediana 2,60h em 469 projetos; High 61,0% dos 500; máximo ≈693h; 330 episódios censurados à direita. | Compatível para CI observado, condicionado à cobertura e censura; não mede restauração de serviço em produção. |
| RQ05 | rho=0,154562 (a), n=500; rho=0,799098 (b), n=498; sinais positivos persistem sem alertas. | Direção negativa não sustentada; menor associação em CI compatível com essa componente. “Fraca” não tinha limite numérico pré-fixado. |
| RQ06 | 7/18 globais e 27/108 pares após Holm; sem diferença corrigida por estrelas; Q1–Q4 de contribuidores com deltas −0,580 e −0,686 para LT. Idade favorece CFR em Q4, mas não frequência, LT e recuperação. | Superioridade uniforme não sustentada; heterogeneidade compatível com o complemento. Tipo de projeto não testado nos 500. |
| RQ07 | Trocar LT: 68/468 mudanças (14,53%), kappa 0,8411; trocar CFR: 179/467 (38,33%), kappa 0,5635. | Sensibilidade compatível nas variantes testadas; não testa pré-releases versus tags nem estabilidade das classes extremas. Combinações definidas após a coleta. |

## Redações preservadas e alinhamentos

[Introdução](introducao.tex) e [complemento](hipoteses_complementares.tex)
coexistem com formulações distintas para RQ05–RQ07. A introdução prevê
associação negativa e quartis de estrelas/contribuidores/idade; o complemento
admite associação fraca ou negativa e menciona tipo de projeto. A RQ07 contém
previsões sobre unidades de entrega e sobre classes extremas. Não foi feita
harmonização retrospectiva desses textos para acomodar os resultados.

A metodologia e o README anteriormente descreviam idade como fator adicional
à hipótese original; essa afirmação correspondia apenas ao complemento e
foi corrigida: idade está prevista na introdução. A discussão trata ambas as
redações e mantém tipo de projeto não testado nos 500. Os arquivos das duas
formulações foram preservados byte a byte contra `aac76df`.

O comentário do complemento o declara posterior ao piloto. A discussão
não afirma pré-registro ou formulação anterior a toda observação. Não houve
reescrita das hipóteses, escolha de novas combinações, coleta, alteração de
cortes, ajuste da heurística nem preenchimento de rótulos.

## Fontes numéricas

As evidências continuam nas tabelas versionadas, sem alteração:

- `analise/tabelas/rq01_resumo.csv`, `rq01_faixas_mensais.csv` e
  `c1_distribuicao_classes.csv`;
- `rq02_resumo.csv` e `rq02_comparacao_variantes.csv`;
- `rq03_resumo.csv` e `rq03_comparacao_variantes.csv`;
- `rq04_resumo.csv` e `rq04_censura.csv`;
- `rq05_spearman.csv`, `rq06_holm_globais.csv` e `rq06_holm_pares.csv`;
- `analise/rq07/combinacoes.json` e `robustez.csv`, nas coortes indicadas.

Os percentuais de classes descritivas usam os 500, inclusive os sem classe;
as comparações pareadas e RQ07 usam seus próprios denominadores. As quatro
releases sem previsão da amostra-ouro não se confundem com os repositórios
excluídos das comparações de classe. Nenhuma ausência vira negativo ou zero.

## Relação com literatura: fontes primárias consultadas

- [DORA 2021, relatório original](https://dora.dev/research/2021/dora-report/2021-dora-accelerate-state-of-devops-report.pdf),
  pp. 9–13: métricas, perguntas sobre produção/usuários, intervalos dos
  clusters e contraste entre fluxo e estabilidade. A discussão distingue
  essas unidades dos nossos proxies e os intervalos dos cortes da disciplina.
- [Kinsman et al. (2021), registro dos autores](https://arxiv.org/abs/2103.12224),
  resumo e metadados da publicação no MSR, DOI
  `10.1109/MSR52588.2021.00054`: automação e indicadores de pull requests.
  A comparação distingue esse desenho do nosso recorte só com adotantes.
- [Sánchez Ruiz et al. (2023), preprint dos autores](https://arxiv.org/abs/2304.14790),
  resumo e metadados: proposta de adaptação de benchmarking DORA a OSS,
  com métricas próprias e quatro projetos. Nova entrada bibliográfica
  `sanchezruiz2023benchmarking`, identificada como **preprint**, sem alegar
  replicação quantitativa ou publicação revisada por pares.

As referências sustentam a comparação de construtos e desenhos; não são
usadas para atribuir causalidade aos resultados ou afirmar superioridade
empírica de uma definição. A explicação sobre oportunidades de corretiva
em sete dias é uma interpretação da nossa regra, não um mecanismo comprovado
por essas fontes. Não se extrapola a literatura para validar nosso consenso.

## Conferência desta entrega

A revisão altera somente discussão, referências e os alinhamentos necessários
em metodologia/READMEs. As fontes de dados, classificações, resultados,
hipóteses e planilhas humanas permanecem preservadas. Não foram adicionados
testes que apenas verificam frases nem reexecutada a suíte inteira para uma
alteração documental; os números de testes das entregas anteriores permanecem
históricos. As conferências numéricas, de referências cruzadas, citações e
compilação do artigo completo estão registradas abaixo.

Qualquer commit desta entrega deve referenciar `(#179)`. As conferências
abaixo correspondem à revisão local anterior à publicação dos commits e da
PR; não houve sincronização do Overleaf.

### Resultados das conferências de 22/10/2026

- Conferidos diretamente nas tabelas: medianas mensais e em dias/horas,
  percentuais de classes com denominador de 500, comparação pareada de LT,
  medianas de CFR, rho/n, direção dos deltas Q1–Q4 e contagens de Holm.
- Confirmados em `robustez.csv`: 68/468 e 179/467 mudanças, percentuais
  14,53% e 38,33% e kappas 0,8411 e 0,5635, na coorte de casos completos.
- Citações com entradas BibTeX existentes; chaves e labels únicos;
  referências cruzadas com destinos existentes. A nova entrada é preprint.
- `introducao.tex` e `hipoteses_complementares.tex` idênticos, byte a byte,
  aos da `main` de referência. Sem diferenças em análises, coletores,
  entregas, rótulos humanos ou testes.
- `git diff --check` sem erros.
- **Artigo completo compilado com sucesso** pelo compilador nativo do editor,
  com raiz `Lab03` e principal `artigo/main.tex`, incluindo as figuras
  existentes. Não foi criada uma prévia substituta, aberta nova aba,
  exportado PDF ou sincronizado Overleaf. Essa confirmação não equivale
  a inspeção visual de todas as páginas nem à revisão de páginas da #186.

### Hashes das hipóteses preservadas

| Fonte | SHA-256 |
|---|---|
| `introducao.tex` | `eb671641b2e9b61b01ee27a2c2f26fdb6cbe87a80f7ccf76baac87c7a5f9593f` |
| `hipoteses_complementares.tex` | `5d41d8c6542889a1f56a6b114deeaacf63600f47f65520e090f20f82a65c6935` |
