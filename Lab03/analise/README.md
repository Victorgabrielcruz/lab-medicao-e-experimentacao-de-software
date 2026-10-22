# Análises da Sprint 03

Notebooks que leem o dataset final de 500 repositórios
(`entregas/s02-03-dataset-500-final/dataset-500.csv`) e gravam tabelas em
`tabelas/` e figuras em `figuras/`. As funções de resumo ficam em
`pipeline/descritiva.py`, com testes em `tests/test_descritiva.py`.

| Notebook | Issue | Conteúdo |
|---|---|---|
| [s03-01-rq01-rq02.ipynb](s03-01-rq01-rq02.ipynb) | #167 | Mediana e IQR da DF e das variantes (a) e (b) do lead time, comparação pareada das variantes e gráficos. |
| [s03-03-classificacao-dora.ipynb](s03-03-classificacao-dora.ipynb) | #169 | Distribuição das classes DORA de referência (C1) por métrica e geral (LT b + CFR a), com sensibilidade às outras combinações de variantes. |
| [s03-02-rq03-rq04.ipynb](s03-02-rq03-rq04.ipynb) | #168 | Mediana e IQR da CFR (a) e (b) e do tempo de recuperação, comparação das variantes e das classes, percentual de episódios censurados e gráficos. |
| [s03-04-rq05-spearman.ipynb](s03-04-rq05-spearman.ipynb) | #170 | Spearman entre DF e CFR (a)/(b): rho, p-valor, n, dispersão, verificação por permutação e sensibilidade aos indicadores de incompletude. |

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

## RQ05 — correlação entre frequência e taxa de falha (#170)

O notebook da RQ05 lê somente o CSV. Pode ser executado a partir de `Lab03/`
ou `Lab03/analise/`; não exige coleta, token ou os JSONs usados na validação
humana. A partir de `Lab03`, usando o Python do ambiente do projeto:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace analise/s03-04-rq05-spearman.ipynb
```

Para outra exportação do mesmo contrato, configure `LAB03_RQ05_CSV` antes de
iniciar o kernel. `LAB03_RQ05_SAIDA` permite gravar as tabelas e a figura em
outra pasta; os caminhos relativos são resolvidos a partir da pasta de
trabalho do kernel. O carregamento valida os campos usados, IDs únicos,
janela comum com fuso, domínios numéricos e indicadores booleanos.

Cada variante usa seus próprios pares completos, preservando zeros e sem
imputar valores ausentes. O cálculo usa `scipy.stats.spearmanr`, bilateral,
com empates por ranks médios. `p_valor` é o p-valor assintótico. A verificação
`p_permutacao` usa 99.999 permutações de pareamentos, semente 170, mantendo
DF fixa; seu menor valor bilateral aleatório nesta configuração é 0,00002.
Essa verificação acompanha a ressalva do
[SciPy sobre o p-valor com até 500 pares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html).
O [teste de permutação](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html)
usa duas vezes a menor cauda e ajuste +1 no cálculo aleatório.

Resultados principais do CSV final de 500 repositórios:

| Par | rho | p-valor assintótico | p por permutação | n |
|---|---:|---:|---:|---:|
| DF × CFR (a) | 0,154562 | 0,000523733 | 0,00054 | 500 |
| DF × CFR (b) | 0,799098 | 1,10854 × 10⁻¹¹¹ | 0,00002 | 498 |

As duas exclusões em (b) são nulos de CFR, identificados por ID na tabela
de exclusões. A sensibilidade retira os 54 repositórios com pelo menos um
indicador global (`coleta_incompleta` ou `calculo_parcial`): restam n=446
para (a), rho=0,115381, e n=444 para (b), rho=0,777516. Dois nulos de CFR(b)
permanecem nesse recorte. A ausência desses indicadores não é uma auditoria
independente da completude de cada métrica.

Os p-valores são apresentados sem ajuste de multiplicidade; são dois testes
predefinidos e bilaterais. A diferença entre os rhos não foi formalmente
testada. As associações positivas observadas contrariam a direção negativa
da hipótese local, sem estabelecer causalidade ou refutar o DORA de forma
geral. CFR(a) mede falhas de CI; CFR(b) depende da heurística ainda sem
validação humana completa (#162/#163). Além disso, uma frequência maior
cria mais oportunidades de observar uma corretiva na janela de sete dias,
o que pode contribuir para a associação de CFR(b) com DF.

Saídas reproduzíveis:

- [rq05_spearman.csv](tabelas/rq05_spearman.csv): rho, p-valores, n, exclusões,
  parâmetros e motivos de não estimação nos dois recortes e variantes.
- [rq05_pares.csv](tabelas/rq05_pares.csv): valores e IDs usados em cada análise.
- [rq05_exclusoes.csv](tabelas/rq05_exclusoes.csv): pares principais ausentes,
  sem preenchê-los artificialmente.
- [rq05_proveniencia.json](tabelas/rq05_proveniencia.json): hash do CSV e do
  código, janela, versões de bibliotecas e parâmetros.
- [rq05_df_cfr_spearman.png](figuras/rq05_df_cfr_spearman.png): dois painéis,
  DF em log e CFR linear, preservando os zeros. O notebook usa `symlog`
  se outro CSV contiver DF=0, sem remover esses pares.

O código está em [correlacao_rq05.py](../pipeline/correlacao_rq05.py), com
35 casos de teste para pares, exclusões, empates, permutação exata conferida
por enumeração, reprodutibilidade, constantes, dados inválidos e gráficos.
Validação local: 1.027 testes aprovados, 2 ignorados, cobertura global de
94,46% e 100% no novo módulo, em Python 3.14.3. O notebook foi executado a
partir de `analise/` e novamente em kernel limpo a partir de `Lab03/`, com
CSV copiado e saída isolada: as três tabelas CSV e a figura foram idênticas
byte a byte, preservando a entrada. O SciPy foi fixado em 1.17.1, compatível
com o Python 3.11 da CI; a execução local não substitui essa CI.
Os resultados do artigo ficam para a #177. Todo commit desta entrega deve
referenciar `(#170)`.
