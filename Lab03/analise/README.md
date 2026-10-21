# Análises da Sprint 03

Notebooks que leem o dataset final de 500 repositórios
(`entregas/s02-03-dataset-500-final/dataset-500.csv`) e gravam tabelas em
`tabelas/` e figuras em `figuras/`. As funções de resumo ficam em
`pipeline/descritiva.py`, com testes em `tests/test_descritiva.py`.

| Notebook | Issue | Conteúdo |
|---|---|---|
| [s03-01-rq01-rq02.ipynb](s03-01-rq01-rq02.ipynb) | #167 | Mediana e IQR da DF e das variantes (a) e (b) do lead time, comparação pareada das variantes e gráficos. |
| [s03-02-rq03-rq04.ipynb](s03-02-rq03-rq04.ipynb) | #168 | Mediana e IQR da CFR (a) e (b) e do tempo de recuperação, comparação das variantes e das classes, percentual de episódios censurados e gráficos. |

`dados/rq04_episodios_500.csv` traz os episódios de recuperação por repositório,
extraídos de `processed/amostra-final-500/tempo_recuperacao.json` (pacote
`entregas/dados-brutos-500/`), com o SHA-256 da origem em
`dados/rq04_episodios_500.json`. Para regerar a partir da base restaurada:

```powershell
python -m pipeline.descritiva --tempo-recuperacao CAMINHO/tempo_recuperacao.json --saida analise/dados/rq04_episodios_500.csv
```

Para reexecutar, a partir de `Lab03`:

```powershell
python -m pip install -r requirements.txt
cd analise
python -m jupyter nbconvert --to notebook --execute --inplace s03-01-rq01-rq02.ipynb s03-02-rq03-rq04.ipynb
```

Ou abra o notebook com o diretório `analise/` como pasta de trabalho e use *Run All*.
