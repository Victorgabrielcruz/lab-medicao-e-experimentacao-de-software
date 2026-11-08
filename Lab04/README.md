# Lab04 — Testes de hipótese por dentro

Comparação entre o **teste Z para proporção** e o **teste binomial exato** (par P4)
por simulação. Cenário: a taxa de builds com falha de um projeto open-source
frente a uma meta de 5%. Uma amostra pequena de execuções reais de CI calibra
a simulação e serve para aplicar os dois testes no fim.

O resultado é um dashboard em Streamlit, com sete seções na ordem do enunciado:
Cenário, Os dados, Como os testes funcionam, Erro tipo I, Poder, Dados reais e
Conclusão.

- Board: [GitHub Projects](https://github.com/users/Victorgabrielcruz/projects/7)
- Dashboard publicado: em breve (#277)

## Como executar

Requer Python 3.11 ou superior. Na pasta `Lab04`, prepare o ambiente uma vez.

No Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

No Linux/macOS:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Depois, abra o dashboard com um único comando:

```text
.venv/Scripts/python -m streamlit run app.py
```

No Linux/macOS, use `.venv/bin/python` no lugar de `.venv/Scripts/python`.
O dashboard abre em `http://localhost:8501`.

## Amostra de dados reais — S01-02 (#263)

O arquivo [`data/ci_pytest.csv`](data/ci_pytest.csv) contém **243 execuções**
do workflow `test` do repositório público `pytest-dev/pytest`, na branch `main`,
disparadas por `push`. Foram inspecionadas 300 execuções consecutivas, de
20/04/2026 a 30/10/2026 (UTC), e descartadas 57 com conclusão `cancelled`.
Há **10 falhas (4,12%)**, com **IC nominal de 95% de Wilson: 2,25% a 7,41%**.
A maior sequência na amostra válida é de **3 falhas** e a autocorrelação
amostral de lag 1 é **0,2741**. Ao exigir que não haja cancelamentos entre
as falhas, a maior sequência é 2.

A [documentação da coleta](data/README.md) registra origem, corte temporal,
paginação, descartes, tratamento das tentativas e as limitações do IC e das
sequências para calibrar a situação `rajadas` da #265. O
[`resumo JSON`](data/ci_pytest_resumo.json) mantém as estatísticas sem
arredondamento. Para regenerar CSV e resumo **sem rede**, a partir de `Lab04`:

```text
.venv/Scripts/python -m hipotese.dados_reais
```

No Linux/macOS, use `.venv/bin/python` no lugar de `.venv/Scripts/python`.

## Reprodutibilidade

### Cenário e hipóteses — S01-03 (#264)

Protocolo registrado em 04/11/2026, antes da execução das simulações da S02.
A seção **1. Cenário** do dashboard apresenta a pergunta, as hipóteses,
a origem dos dados, os parâmetros e as expectativas anteriores à simulação.

- Pergunta: a taxa de falha do workflow `test` de `pytest-dev/pytest` está acima de 5%?
- H₀: `p = 0,05`; H₁: `p > 0,05`. A alternativa é unicaudal à direita
  (`ALTERNATIVA = "greater"`), pois a meta é tratada como teto didático.
- Cada execução válida é Bernoulli, com taxa marginal `0,05 + efeito`.
  `EFEITOS = (0; 0,02; 0,04; 0,06; 0,08; 0,10)` são diferenças absolutas
  de proporção: 0 a 10 pontos percentuais acima da meta, não aumentos relativos.
- Situações: independente com `n` igual ao tamanho da amostra real; rajadas
  com o mesmo `n` e correlação de lag 1 estimada na coleta; independente
  com `N_AMOSTRA_PEQUENA = 20` para desafiar a aproximação normal.
- `hipotese.cenario.carregar_resumo()` lê os dados versionados offline;
  `configuracoes_simulacao(resumo)` fornece `n`, `situacao` e `correlacao`
  para passar explicitamente a `gerar_builds` ou `gerar_lote`. Assim, rajadas
  usa a estimativa real (aproximadamente 0,2741), não o padrão 0,5 do gerador.
- A grade será executada com 10.000 repetições por situação e efeito,
  α = 0,05 e semente 42. Sob H₀, a taxa é 5%, não os 4,12% observados.

**Expectativa anterior à S02:** para dados independentes com `n = 243`,
esperamos aproximação razoável entre Z e binomial exato: sob H₀,
`n·p₀ = 12,15` e `n·(1−p₀) = 230,85`. O exato pode ser conservador pela
discretização; eventual vantagem de poder do Z deve ser avaliada junto do
seu erro tipo I. Com `n = 20`, esperamos pior aproximação normal e preferimos
o exato para controlar o erro tipo I, sem garantir maior poder. Sob rajadas,
ambos perdem a garantia de calibração baseada em independência e podem
apresentar mais falsos positivos. A comparação de Q1–Q3 deverá confirmar
ou contrariar essas expectativas antes da recomendação final.

A ACF real é uma referência de calibração com incerteza, não prova de
dependência: há poucas transições iniciadas por falha e a filtragem remove
cancelamentos entre observações. O teste exato também pressupõe independência.

### Parâmetros compartilhados

Toda geração aleatória parte de `hipotese.config.gerador()`, que usa a semente
fixa `SEMENTE = 42`. O nível de significância (`ALFA = 0,05`), o número de
repetições (`N_REPETICOES = 10.000`) e a meta de 5% também ficam nesse módulo.
O mesmo vale para a cor de cada teste, que é igual em todos os gráficos.

## Aplicação a um conjunto simulado — S01-05 (#266)

A seção **3. Como os testes funcionam** apresenta os dois testes aplicados
à mesma amostra independente. O protocolo do exemplo foi escolhido antes
de consultar seu resultado: `n` igual ao tamanho da amostra real (243),
`EFEITO_EXEMPLO = 0,04` (taxa verdadeira de 9%) e semente 42. A amostra não
é sorteada novamente até obter significância. O gráfico G2 (#268)
reutiliza `hipotese.exemplo.gerar_exemplo()`.

- Z para proporção: `Z = (p_hat - p0) / sqrt(p0 * (1-p0) / n)`, com
  variância sob H₀ e **sem correção de continuidade**. Para a alternativa
  `greater`, o p-valor é a cauda superior da normal padrão, calculada por
  `scipy.stats.norm.sf(Z)`.
- Binomial exato: `scipy.stats.binomtest(falhas, n, p=0.05, alternative="greater")`.
  O p-valor é `P(X >= falhas)` para `X ~ Binomial(n, 0.05)`; a estatística
  retornada pelo SciPy é `p_hat = falhas/n`, identificada como tal no dashboard.
- O efeito observado, comum aos dois testes, é `100 * (p_hat - p0)` em
  **pontos percentuais**, com sinal. Ele não é o efeito verdadeiro usado na
  geração. A regra de decisão é estritamente `pvalor < ALFA`.

`hipotese.testes.teste_z(falhas, n)` e `teste_binomial(falhas, n)` retornam
`ResultadoTeste`, com estatística identificada, p-valor, contagens, proporção,
efeito em p.p. e decisão. Aceitam `meta`, `alternativa` e `alfa` opcionais;
os padrões vêm do protocolo compartilhado. `aplicar_testes(builds)` valida
uma amostra binária e aplica ambos. As funções não acessam o dashboard nem
consomem aleatoriedade: a S02 pode chamar as mesmas funções com as contagens
de `gerar_lote`, e a #275 pode usá-las nos dados reais.

Neste exemplo, a semente 42 produz **17 falhas em 243 builds (7,00%)**:
o efeito observado é **+2,00 p.p.**, Z ≈ 1,4276, p-valor Z ≈ 0,07671 e
p-valor binomial ≈ 0,10400. Ambos não rejeitam H₀ a 5%. Como a taxa verdadeira
simulada é 9%, trata-se de uma ocorrência de erro tipo II para ambos, não
de evidência de ausência de efeito. Estimar a frequência desse erro e o
poder exige as repetições da S02. Nenhuma conclusão sobre o workflow real
é obtida a partir deste exemplo.

Referências das APIs: [normal padrão do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html)
e [teste binomial do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).

## Gráfico G1 — S01-06 (#267)

A seção **2. Os dados** apresenta os histogramas das observações reais e
simuladas lado a lado, com título, legenda, contagens no hover e percentuais
nas barras. Como o par P4 compara uma proporção à meta, há um grupo real
de execuções de CI; os dois testes são aplicados a esse mesmo tipo de dado.

- `hipotese.cenario.carregar_amostras_g1()` lê a coluna `falhou` do CSV
  congelado e usa `gerar_builds` com um gerador próprio de semente 42,
  `n` igual ao tamanho efetivo da coleta e taxa de falha igual à meta de 5%.
  A amostra independente sob H₀ tem **12 falhas em 243 builds (4,94%)**;
  a real tem **10 em 243 (4,12%)**. Não há seleção por proximidade entre
  as taxas nem alteração do exemplo com taxa de 9% usado na seção 3.
- `hipotese.graficos.construir_g1(reais, simulados)` usa dois bins fixos,
  `[-0,5; 0,5)` e `[0,5; 1,5]`, centrados em 0 (passou) e 1 (falhou).
  As contagens são calculadas com `numpy.histogram` e desenhadas em barras
  Plotly; categorias vazias permanecem visíveis com frequência zero.
  Os eixos mostram o resultado binário adimensional e a frequência relativa
  em porcentagem, com as mesmas escalas nos dois painéis. Cinza identifica
  os dados reais e verde os simulados; as cores dos testes permanecem no G2.
- O texto de quatro frases explica a concentração em zero, a assimetria
  à direita e que falhas são uma categoria válida, não outliers. Justifica
  a Bernoulli pelo suporte binário, `n = 243` pela coleta e `p = 5%` por H₀:
  a taxa empírica não substitui a referência do protocolo. Também explicita
  que histogramas não exibem a ordem temporal nem a dependência das rajadas.

O G1 é regenerado ao abrir o dashboard, sem rede, com a mesma amostra a
cada execução. As contagens, a normalização, a reprodução e a integração
na seção 2 são verificadas pela suíte do Lab04.

Referências: [histogramas com contagens calculadas em Python](https://plotly.com/python/histograms/#accessing-the-counts-y-axis-values)
e [painéis lado a lado no Plotly](https://plotly.com/python/subplots/).

## Gráfico G2 — S01-07 (#268)

A seção 3 apresenta dois painéis Plotly produzidos por
`hipotese.graficos.construir_g2(exemplo)`, com o mesmo objeto de exemplo
usado na tabela da #266. Não há novo sorteio nem Monte Carlo para calcular
as áreas. O azul do Z e o laranja do binomial vêm de `CORES_TESTES`.

- **Z:** curva da normal padrão, referência aproximada usada pelo teste sob
  H₀. A sombra clara parte do Z observado (1,4276) e representa o p-valor
  (0,07671); a escura parte de `norm.isf(0.05)` (1,6449), com área 5%.
  A normal não é apresentada como distribuição exata do Z para n finito.
- **Binomial exato:** barras das massas de `p_hat = X/n`, em porcentagem
  no eixo x, com `X ~ Binomial(243, 0.05)`. O eixo y mostra a probabilidade
  de cada valor em porcentagem. O p-valor é a **soma das massas a partir de
  17 falhas, incluindo 17**, e não a integral de uma densidade contínua.
  A rejeição começa em 19 falhas (7,82%), com probabilidade sob H₀ de
  0,03735. É menor que 5% por discretização, mantendo a regra estrita `p < α`.
- As regiões de p-valor e rejeição são sobrepostas, em tons da cor do teste;
  as linhas pontilhada e tracejada identificam observado e limite crítico.
  Títulos, legendas, nomes dos eixos e unidades ficam nos próprios gráficos.
  O binomial abre com zoom na região relevante, mas os dados contêm todos
  os `n+1` valores e as somas usam todo o suporte.

Os gráficos e o texto explicam que ambos comparam a taxa de falha à meta
e que o p-valor representa extremidade sob H₀ e seus pressupostos, não a
probabilidade de H₀ ser verdadeira. As decisões permanecem consistentes
com a tabela da #266.

Validação da #268: **83 testes passaram** no ambiente isolado `Lab04/.venv`,
com as versões exatas do `requirements.txt`, incluindo as áreas desenhadas,
as massas binomiais e a fronteira de rejeição para cada contagem. O dashboard
foi conferido no navegador com os dois gráficos, legendas e textos renderizados.

Referências: [distribuição binomial do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binom.html)
e [áreas preenchidas no Plotly](https://plotly.com/python/filled-area-plots/).

## Motor de simulação Monte Carlo — S02-01 (#269)

`hipotese/simulacao.py` gera **10.000 conjuntos** por configuração. São 3
situações (Independente com n = 243, Rajadas com n = 243 e ACF da amostra real,
Amostra pequena com n = 20) e os 6 efeitos de `EFEITOS`, de 0 a 10 p.p. Os dois
testes são aplicados ao **mesmo** conjunto, e a saída é a proporção de
p-valores abaixo de α = 0,05: com efeito zero é o erro tipo I, e com efeito
positivo é o poder.

- Os p-valores vêm das mesmas funções `teste_z` e `teste_binomial` da S01. Como
  a contagem de falhas é um inteiro de 0 a n, cada contagem distinta é testada
  uma única vez e o p-valor é reaproveitado.
- Cada configuração tem um gerador próprio, derivado de `SEMENTE` por
  `SeedSequence(SEMENTE, spawn_key=(situação, efeito))`. O resultado de uma
  configuração não depende da ordem das demais.
- A saída [`data/simulacao.csv`](data/simulacao.csv) tem uma linha por
  situação × efeito × teste (36 linhas), com rejeições, proporção e erro-padrão
  de Monte Carlo `sqrt(p(1−p)/10.000)`. O dashboard lê esse arquivo sem
  recalcular.

Para regenerar, a partir de `Lab04` (cerca de 7 segundos):

```text
.venv/Scripts/python -m hipotese.simulacao
```

Os testes conferem a igualdade dos p-valores com os da S01, a
reprodutibilidade, a independência entre configurações e o erro tipo I
simulado contra o valor exato, que é a soma das massas binomiais das contagens
rejeitadas: 6,39% para o Z e 3,73% para o binomial com n = 243. Também
conferem que o CSV versionado é o que a semente fixa gera.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app.py` | Dashboard em Streamlit |
| `hipotese/` | Código de simulação, testes e parâmetros compartilhados |
| `data/` | Amostra de dados reais (CSV), sua origem e os resultados da simulação |
| `tests/` | Testes automatizados |

## Testes

```text
.venv/Scripts/python -m pytest
```
