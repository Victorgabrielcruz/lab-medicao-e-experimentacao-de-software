# Artigo do Lab03 — SBC 2017 (#150)

## Validação manual — S02-15 (#165)

A seção **Validação manual** de [metodologia.tex](metodologia.tex) descreve
o protocolo para a população encerrada de 255 repositórios:

- sorteio oficial da #155: 60 repositórios e 5 releases estáveis de cada um,
  sem reposição e com `random_state=42`, total previsto de 300 pares;
- três rotuladores independentes, catálogo de categorias e tratamento das
  ausências, com preservação dos julgamentos antes do consenso;
- kappa de Fleiss nas três dimensões, calculado **antes do consenso**, com
  número de itens válidos, proporções das categorias e casos não estimáveis;
- proposta explícita de consenso: maioria simples como proposta discutida,
  reunião para três categorias distintas e pendências justificadas sem usar
  a heurística como desempate;
- avaliação binária de **release corretiva** contra consenso: matriz de
  confusão, precisão, recall, F1, cobertura e tratamento de divisões por zero;
- histórico das versões da heurística e refinamento previsto na #163 se
  F1 < 0,70, com declaração do reuso da amostra para ajuste.

O trecho da CFR(b) foi alinhado ao enunciado: a release que falha é aquela
seguida, em até sete dias, por uma corretiva; as publicadas nos últimos sete
dias ficam censuradas. A avaliação da heurística classifica a **corretiva**,
não diretamente a release anterior nem um incidente em produção.

**Estado em 15/10/2026:** na base `2b4ea3b`, não há manifesto do sorteio
oficial nem rótulos completos, consenso, kappa ou avaliação numérica. A
preparação C também registra essa dependência em
[rotulagem-c-158.md](../docs/rotulagem-c-158.md). A publicação dos brutos e do
CSV de 255 não constitui a amostra-ouro rotulada. Não foi feito novo sorteio,
preenchimento de rótulos, implementação da heurística ou consulta aos dados
de A/B/C nesta entrega.

Os tamanhos 60/300 são previstos; as métricas permanecem **pendentes**, não
zero. Para concluir o relato empírico, incorporar o manifesto oficial (#155),
as três rotulagens independentes (#156–158), o relatório de concordância,
o consenso aprovado e a avaliação da heurística (#161–163). O protocolo de
consenso descrito aqui deve ser alinhado com o responsável por essa entrega
antes de ser apresentado como executado. Nenhuma issue é fechada por esta
revisão documental.

As referências metodológicas foram acrescentadas em
[referencias.bib](referencias.bib), preservando as entradas anteriores.
As evidências e o alcance da conferência da seção estão em
[validacao-s02-165.md](validacao-s02-165.md). Não houve sincronização do
Overleaf nem atualização dos resultados/resumos históricos do piloto.

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
