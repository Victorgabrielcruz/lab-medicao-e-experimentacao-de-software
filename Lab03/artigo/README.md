# Artigo do Lab03 — pacote SBC (#150)

`main.tex` é o arquivo principal. A introdução e as hipóteses preexistentes em
`introducao.tex` e as quatro referências em `referencias.bib` foram preservadas.
O projeto contém metodologia, resultados, discussão/ameaças, conclusão,
abstract/resumo e os links do repositório e GitHub Projects. Resultados empíricos
não foram inventados: as seções registram o que ainda depende da coleta.

O estilo SBC local, a licença e os hashes estão descritos em
[PROVENIENCIA-template.md](PROVENIENCIA-template.md). O espelho é a versão de
2005, anterior à atualização de 2017 da [galeria SBC no Overleaf](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr).

Para compilar um projeto com TeX Live/MiKTeX e BibTeX já disponíveis:

```text
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Para gerar o pacote de importação, na pasta do artigo:

```powershell
Compress-Archive -Path main.tex,introducao.tex,metodologia.tex,resultados.tex,discussao.tex,conclusao.tex,referencias.bib,sbc-template.sty,sbc.bst,caption2.sty,LICENSE-template-MIT.txt,PROVENIENCIA-template.md -DestinationPath artigo-lab03-sbc.zip -Force
```

No Overleaf, importar esse ZIP por New project → Upload project, selecionar
`main.tex` e pdfLaTeX, recompilar e registrar o URL do projeto no relatório.
Alternativamente, abrir o modelo de 2017 da galeria e substituir suas seções
pelos arquivos deste estudo, preservando o .sty/.bst dessa versão.

**Projeto online pendente:** o navegador abriu `/project` na tela de login.
É necessário autenticar a conta Overleaf; não há URL de projeto criado.
Isso mantém pendente o critério online da #150. O editor nativo do Codex
suporta documentos standalone, sem os arquivos adicionais deste projeto;
a prévia autossuficiente gerada separadamente não substitui a compilação do
pacote nem a criação do projeto online.
