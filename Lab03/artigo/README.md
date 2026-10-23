# Artigo do Lab03 — SBC 2017 (#150)

## RQ08 bônus — evolução temporal (#175)

A subseção RQ08 de [resultados.tex](resultados.tex) resume a evolução
mensal da frequência de releases estáveis, com painel fixo, comparação
semestral e sensibilidade aos alertas. O gráfico e os números derivam do
[notebook executado](../analise/s03-09-rq08-evolucao-temporal.ipynb).
Escolha, fontes, exclusões, reprodução e validação estão no
[registro da #175](../docs/rq08-evolucao-temporal-175.md).

## Discussão das hipóteses — S03-13 (#179)

[discussao.tex](discussao.tex) confronta os componentes das sete expectativas
com os resultados publicados, separando compatibilidade parcial, direção
contrariada e componentes não testados. Relaciona os achados ao DORA 2021,
a Kinsman et al. (2021) e ao preprint de Sánchez Ruiz et al. (2023), sem
apresentar proxies de CI/releases como incidentes de produção ou inferir
causalidade. As implicações distinguem uso pelos mantenedores e pesquisa.

As duas redações das RQ05–RQ07, presentes na introdução e no complemento,
foram preservadas. A introdução inclui idade na RQ06; tipo de projeto
aparece no complemento e permanece sem análise para os 500. A metodologia
e este README foram alinhados a essa distinção, sem reescrever hipóteses.
Os cortes fixos do enunciado também não são tratados como os mesmos
intervalos dos clusters do relatório DORA 2021.

Fontes, vereditos descritivos por componente, limites e conferência estão
em [validacao-s03-179.md](validacao-s03-179.md). Nenhum dado, classificação,
sorteio ou resultado das análises foi alterado. Compilação e conferências
desta revisão são registradas nesse arquivo; os números de testes das
entregas anteriores não representam uma nova execução nesta tarefa textual.

## Resultados RQ07 — S03-12 (#178)

A seção RQ07 de [resultados.tex](resultados.tex) apresenta C1/C2/C3,
percentuais de mudança de classe, kappa ponderado e verificações de robustez
das análises #173/#174. C1 mantém a referência da main: LT(b)+CFR(a).
As tabelas distinguem pares completos de notas gerais parciais nos 500;
o texto mantém os limites da avaliação de CFR(b) e das hipóteses não testadas.

As fontes, os hashes, a reprodução e a compilação estão registrados em
[validacao-s03-178.md](validacao-s03-178.md). Resumo, abstract e conclusão
foram alinhados à existência desses resultados, preservando os resultados
anteriores das outras RQs. A revisão final de páginas permanece na #186.

## Validação manual — S02-15 (#165)

**Atualização de 22/10/2026:** [metodologia.tex](metodologia.tex) incorpora
as planilhas e os relatórios existentes, preservando os dados humanos:

- amostra oficial de 60 projetos e 300 releases, sorteada entre os primeiros
  255 elegíveis, mantida após ampliar a população para 500;
- livro de códigos realmente aplicado: seis tipos, entregas reais sim/não e
  corretiva com ao menos uma correção, inclusive releases mistas;
- Fleiss reproduzido: tipo **0,874570** (60), entregas **0,744318** (60),
  corretiva **0,952752** (300); consenso de 249 corretivas e 51 não corretivas,
  com 405 itens unânimes e 15 divergências resolvidas;
- CFR(b) recalculado sobre 34.255 releases dos 500 projetos, com os 498
  agregados e dois nulos coincidentes com o CSV final;
- avaliação da v1 em **296/300** pares: matriz `[[17,30],[5,244]]`, precisão
  **0,890511**, recall **0,979920**, F1 **0,933078**. As quatro primeiras
  releases sem predecessora ficam indeterminadas. A #163 mantém a v1.

Os escores descrevem o consenso registrado, com limitações explícitas:
assistência e consulta à documentação de B na complementação de C,
declaração de trabalho conjunto e cronologia não comprovada de todos os
julgamentos antes da conciliação. Não se afirma avaliação inteiramente
cega e independente. O critério humano aplicado também é mais amplo que
“objetivo principal de corrigir defeito recente”. Essas limitações não são
resolvidas apenas pela completude dos arquivos ou pelo kappa elevado.

Fontes, reprodução e conferência estão em
[validacao-s02-165.md](validacao-s02-165.md) e no
[relatório final da #162](../validacao/avaliacao-heuristica/final-500/README.md).
O protocolo previsto da entrega de 15/10 é histórico; esta revisão o
substitui pelo relato do procedimento documentado e seus resultados.
Não houve alteração de rótulos nem sincronização do Overleaf.

## Resultados RQ05 e RQ06 — S03-11 (#177)

[Resultados](resultados.tex) incorpora as tabelas das #170–172: Spearman
com rho/p/n nas duas variantes e dispersão em log; todos os 18 globais com
Holm e ε²; 27 pares selecionados com família de 108, com os sete contrastes
Q1–Q4 detalhados por p corrigido e delta de Cliff. Os três fatores são
estrelas, contribuidores e idade, agrupados em quartis. O tipo de projeto
citado no complemento não foi testado para os 500; idade já integra a
expectativa da introdução, conforme a conferência da #179.

A [metodologia](metodologia.tex) descreve famílias, critérios e fórmulas;
a [discussão](discussao.tex) confronta os resultados com as expectativas,
sem atribuir causalidade. Resumos e conclusão foram alinhados à amostra
final de 500, substituindo os textos que ainda descreviam o piloto de 82.
Hipóteses originais, dados humanos e tabelas analíticas foram preservados.
Os resultados da RQ07 estão na seção da #178 acima. Consulte também
[validacao-s03-177.md](validacao-s03-177.md).

## Revisão da metodologia — S02-16 (#166)

**Atualização de 20/10/2026:** a metodologia agora registra a retomada de
16/10, a captura de **500 elegíveis entre 1.064 candidatos**, o funil com
exclusão explícita de um candidato com runs incompletos e o processamento
final parcial após HTTP 403 nos compares. A amostra-ouro de 60 projetos e
300 releases permanece sorteada sobre os primeiros 255. C tem 51 julgamentos
de releases pendentes. O contrato do dataset continua com 28 colunas, na
[nova entrega offline](../entregas/s02-03-dataset-500/README.md).
Os parágrafos seguintes e os hashes da validação anterior são históricos.

A revisão de 15/10/2026 de `metodologia.tex` registra o encerramento humano
da extração da #151 com **255 elegíveis entre 561 candidatos avaliados**,
às **15h09min11s (America/Sao_Paulo)**, conforme a
[decisão de encerramento registrada](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/blob/f1306c7/Lab03/docs/decisao-encerramento-255.md).
A nova decisão substitui a espera
por 300/500; o mínimo original de 300 não foi atingido e o pipeline de 500
foi interrompido antes de todas as etapas.

A metodologia descreve a [política de adiamento por custo observado](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/blob/5d311c2/Lab03/docs/decisoes-coleta-final.md)
como decisão histórica de 14/10. Grafana seria liberado após 300 elegíveis,
mas continuou adiado na parada em 255. A revisão explica o possível viés,
a ordem relativa preservada dos demais e os critérios de inclusão mantidos.
A população oficial inclui somente os IDs elegíveis já consumidos pelo
progresso na parada; checkpoints auxiliares fora dela não ampliam a amostra.

Foram preservadas as definições das RQ01–04, variantes (a)/(b), censura,
ausências e classificação. A fonte referencia o [dicionário de dados](../docs/dicionario-dados.md)
(#154), contrato de 28 colunas da consolidação #153. Comparações de commits
faltantes não são consultadas novamente: só dados locais válidos alimentam
lead time, com ausência/cobertura parcial explicitada. A CFR (b) permanece
dependente da heurística e validação #161; sem fonte, valor e classe são nulos.
A consolidação offline do CSV #153 é uma entrega separada; esta revisão não
alega que ela já tenha terminado.

As demais seções, os resumos e as hipóteses preservam seu contexto histórico
e os resultados do piloto. Esta entrega é uma revisão da **metodologia**,
sem apresentar resultados dos 255 nem sincronizar Overleaf. O PDF/ZIP e a
compilação de seis páginas abaixo pertencem à versão anterior (#150).
A [evidência própria desta revisão](validacao-s02-166.md) distingue verificação
da fonte, compilação da seção isolada e situação do artigo integral.
Recompilar e revisar o artigo inteiro será necessário para uma entrega
integrada com resultados, resumos e conclusões da amostra encerrada.

## Histórico da entrega do piloto (#150)

Projeto existente editado e compilado:
[Overleaf](https://www.overleaf.com/project/6ac8318e750c2cce451d6f68).

Arquivo principal: `main.tex`, com seis inputs, resumo/abstract e quatro
referências. A introdução e suas quatro hipóteses, bem como
`referencias.bib`, foram preservadas. O complemento de RQ05–07 foi
registrado depois do piloto, antes das análises dessas questões; essa
limitação temporal aparece no texto. Não se declara que todas as hipóteses
foram formuladas antes de qualquer observação.

O artigo apresenta a entrega parcial baseada nos dados existentes: 82
repositórios, 238.629 runs, 18 coletas incompletas. A coleta adicional foi
cancelada por decisão do usuário e limite de tempo. A meta de cem
elegíveis completos não foi atingida; hipóteses e análises conjuntas
permanecem pendentes.

## Compilação e conferência

Compilação no Overleaf com pdfLaTeX: **6 páginas A4**, zero erros, zero
avisos e zero mensagens de diagramação. O PDF final foi baixado e suas seis
páginas renderizadas e inspecionadas. As fontes exportadas correspondem ao
conteúdo local após normalização de finais de linha/espaço final.
Introdução/BibTeX locais continuam idênticos aos originais.

PDF e ZIP importável locais, ignorados pelo Git:

- `artigo-lab03-sbc.pdf`: SHA-256
  `c62aba96886c8003c9cbe8ccb12d36c2f105d4c517d2877501095bc25fb15f88`.
- `artigo-lab03-sbc.zip`: pacote com os arquivos atuais deste estudo.

O .sty e .bst usados são os do export original do projeto SBC 2017,
preservados byte a byte na conferência. A licença, os hashes e o histórico
do pacote anterior de 2005 estão em
[PROVENIENCIA-template.md](PROVENIENCIA-template.md) e
[NOTICE-template-2017.txt](NOTICE-template-2017.txt).
Os estilos não foram alterados online. Imagens e bibliografia de exemplo
do projeto original permanecem preservadas, sem uso no artigo.

Para compilar onde TeX Live/MiKTeX e BibTeX já estejam disponíveis:

```text
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Para recriar o ZIP local na pasta do artigo:

```powershell
Compress-Archive -Path main.tex,introducao.tex,hipoteses_complementares.tex,metodologia.tex,resultados.tex,discussao.tex,conclusao.tex,referencias.bib,sbc-template.sty,sbc.bst,NOTICE-template-2017.txt,PROVENIENCIA-template.md,README.md -DestinationPath artigo-lab03-sbc.zip -Force
```

O editor nativo foi mantido com a fonte aberta, mas sua compilação falhou
por infraestrutura (`Unable to find standard directories for platform`).
Essa limitação não impediu a compilação verificada do projeto no Overleaf;
nenhum TeX/plugin foi instalado.
## Registro das hipóteses

As RQ01–RQ04 estão registradas na #137 (06/10/2026), e a #143 registra a
redação das RQ05–RQ07 em 08/10/2026. Coexistem duas formulações no artigo:

- [introducao.tex](introducao.tex): RQ05 prevê associação negativa e menor
  associação para CI; RQ06 prevê desempenho melhor nos quartis superiores
  de estrelas, contribuidores e idade; RQ07 prevê sensibilidade às variantes
  e maior concordância com pré-releases do que com tags;
- [hipoteses_complementares.tex](hipoteses_complementares.tex): RQ05 admite
  associação fraca ou negativa; RQ06 menciona heterogeneidade por popularidade,
  contribuidores e tipo de projeto; RQ07 inclui a expectativa de maior
  concordância nas classes extremas.

O complemento se declara posterior ao piloto. O histórico preserva o
momento da redação, mas isso não comprova hipóteses anteriores a toda coleta
ou observação. A #179 mantém esses textos byte a byte e discute as diferenças
explicitamente. Não se escolhe retrospectivamente uma formulação para tornar
um resultado positivo em confirmação da previsão negativa, nem se interpreta
a análise por idade como teste da previsão por tipo de projeto.
