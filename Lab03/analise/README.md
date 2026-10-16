# Análises da Sprint 03

Notebooks que leem o dataset exportado na #153
(`entregas/s02-03-dataset-153/dataset-255.csv`) e gravam tabelas em
`tabelas/` e figuras em `figuras/`. As funções de resumo ficam em
`pipeline/descritiva.py`, com testes em `tests/test_descritiva.py`.

| Notebook | Issue | Conteúdo |
|---|---|---|
| [s03-01-rq01-rq02.ipynb](s03-01-rq01-rq02.ipynb) | #167 | Mediana e IQR da DF e das variantes (a) e (b) do lead time, comparação pareada das variantes e gráficos. |

Para reexecutar, a partir de `Lab03`:

```powershell
python -m pip install -r requirements.txt
cd analise
python -m jupyter nbconvert --to notebook --execute --inplace s03-01-rq01-rq02.ipynb
```

Ou abra o notebook com o diretório `analise/` como pasta de trabalho e use *Run All*.
