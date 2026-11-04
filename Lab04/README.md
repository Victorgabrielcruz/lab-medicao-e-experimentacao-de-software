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
é sorteada novamente até obter significância. O futuro gráfico G2 (#268)
deve reutilizar `hipotese.exemplo.gerar_exemplo()`.

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

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app.py` | Dashboard em Streamlit |
| `hipotese/` | Código de simulação, testes e parâmetros compartilhados |
| `data/` | Amostra de dados reais (CSV) e sua origem |
| `tests/` | Testes automatizados |

## Testes

```text
.venv/Scripts/python -m pytest
```
