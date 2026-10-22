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
| [s03-05-rq06-grupos.ipynb](s03-05-rq06-grupos.ipynb) | #171 | Quartis de estrelas, contribuidores e idade; Kruskal-Wallis por fator e métrica e Mann-Whitney par a par quando há diferença nominal. |

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

## RQ06 — comparação das métricas por fator (#171)

O [notebook da #171](s03-05-rq06-grupos.ipynb) lê somente o CSV final,
sem API ou dados externos. Os três fatores seguem a hipótese do artigo:
`estrelas`, `contribuidores` e `idade_dias`. Comparam-se as seis colunas de
métricas: DF, lead time (a)/(b), CFR (a)/(b) e tempo de recuperação.
São **18 testes globais planejados**. Para executar a partir de `Lab03`:

```bash
python -m jupyter nbconvert --to notebook --execute --inplace analise/s03-05-rq06-grupos.ipynb
```

Também funciona com `analise/` como pasta de trabalho. `LAB03_RQ06_CSV`
permite outro CSV do mesmo contrato e `LAB03_RQ06_SAIDA` define uma pasta de
saída isolada. Os caminhos relativos usam a pasta de trabalho do kernel.
As entradas são validadas e seu SHA-256 é conferido antes da exportação;
um destino que sobrescreveria a entrada é recusado.

### Grupos e cobertura

O [pandas.qcut](https://pandas.pydata.org/docs/reference/api/pandas.qcut.html)
divide cada fator pelos quantis de 0%, 25%, 50%, 75% e 100%. Os cortes são
fixados **antes de excluir nulos das métricas**. Valores empatados não são
separados por ID; limites repetidos são removidos e menos de quatro grupos
são registrados como G1…Gk, com motivo. Q1–Q4 só são usados quando existem
quatro grupos ocupados. O primeiro intervalo inclui ambos os limites; os
demais são abertos à esquerda e fechados à direita.

No CSV final de 500 projetos, cada um dos três fatores produz quatro grupos
de 125, sem fator ausente:

| Fator | Corte 25% | Corte 50% | Corte 75% |
|---|---:|---:|---:|
| Estrelas | 36.047,75 | 45.049 | 68.388,5 |
| Contribuidores | 180,75 | 395 | 887,25 |
| Idade (dias) | 939 | 2.390,5 | 3.954,5 |

Cada combinação fator × métrica exclui somente ausências nesses dois
campos, preservando zero. Os n globais são 500 para DF/CFR(a), 499 para
ambos os lead times, 498 para CFR(b) e 469 para recuperação. Os tamanhos
por grupo podem mudar após essas exclusões; os cortes permanecem fixos.
Os indicadores globais de incompletude não excluem automaticamente uma
métrica disponível. Estrelas e contribuidores são metadados da coleta,
não medidas históricas de toda a janela.

### Testes e integração com a #172

Com três ou mais grupos, usa-se
[Kruskal-Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html),
com estatística H corrigida para empates e p-valor assintótico. Exigem-se
pelo menos cinco valores válidos em cada grupo. Menos de dois grupos,
grupos pequenos/vazios e todos os valores iguais em KW ficam não
estimáveis com motivo, sem preencher p=0. Se limites repetidos resultarem
em apenas dois grupos válidos, usa-se Mann-Whitney diretamente.

Quando o p-valor **bruto** de KW é menor que α=0,05, executam-se todos os
pares não ordenados daquele fator × métrica. O
[Mann-Whitney](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html)
é bilateral, assintótico, com correção de empates e continuidade. Registra-se
o U da primeira amostra e n de ambos os grupos; com quatro grupos são seis
comparações. O teste direto de dois grupos não é repetido como pós-teste.

Nesta execução há **18 Kruskal-Wallis estimáveis, oito com diferença
nominal e 48 pares Mann-Whitney**. A tabela global registra por que os
pós-testes foram ou não executados. Os resultados são **nominais**:
correção de Holm e tamanhos de efeito (ε² e Cliff's delta) são o escopo
explícito da [#172](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/172).
Essa etapa deverá declarar as famílias e revisar o relato dos pares após
correção, preservando os p-valores brutos destas tabelas. Um achado nominal
não é apresentado como diferença confirmada após controle de multiplicidade.

Os testes comparam distribuições; a leitura como diferença de medianas
exige atenção às formas dos grupos. P-valores não medem a magnitude do
efeito e não estabelecem causalidade. A interpretação de CFR(b) continua
sujeita à validação humana da heurística (#162/#163).

### Artefatos

- [rq06_grupos.csv](tabelas/rq06_grupos.csv): IDs, fatores e grupo de cada projeto.
- [rq06_cortes.csv](tabelas/rq06_cortes.csv): limites numéricos completos,
  fechamento dos intervalos, tamanhos e diagnósticos do agrupamento.
- [rq06_resumos.csv](tabelas/rq06_resumos.csv): n, ausentes, mediana e quartis
  por fator × métrica × grupo, nas unidades originais do CSV.
- [rq06_globais.csv](tabelas/rq06_globais.csv): testes globais, estatística,
  p bruto, n, exclusões e decisão nominal de executar pós-testes.
- [rq06_pares.csv](tabelas/rq06_pares.csv): pares, n de cada amostra, U e p bruto.
- [rq06_proveniencia.json](tabelas/rq06_proveniencia.json): origem, hashes,
  janela, bibliotecas, parâmetros e contagens dos testes.

O código está em [comparacao_rq06.py](../pipeline/comparacao_rq06.py).
Os 45 [casos de teste](../tests/test_comparacao_rq06.py) conferem cortes e empates,
permanência dos grupos após nulos, KW por cálculo independente, U por
contagem de pares, orientação das amostras, seleção dos pós-testes,
constantes, grupos pequenos e entradas inválidas. Em Python 3.14.3,
passaram **1.072 testes, com 2 ignorados**, cobertura global de **94,58%**
e 100% no módulo novo. Os 18 H/p e os 48 U exportados também foram conferidos
por cálculo de ranks e contagem de pares independentes.

O notebook foi executado a partir de `analise/` e em kernel limpo a partir
de `Lab03/`, com CSV copiado e saída isolada. As cinco tabelas foram idênticas
byte a byte e a entrada permaneceu intacta. Essa execução local não
substitui a CI em Python 3.11 e 3.13. Os resultados do artigo permanecem
no escopo da #177. Todo commit desta entrega deve referenciar `(#171)`.
