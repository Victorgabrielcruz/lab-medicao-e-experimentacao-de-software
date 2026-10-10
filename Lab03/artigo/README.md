# Artigo do Lab03 — SBC 2017 (#150)

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
