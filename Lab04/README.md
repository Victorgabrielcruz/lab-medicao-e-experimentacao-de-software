# Lab04 — Testes de hipótese por dentro

Comparamos o **teste Z para proporção** e o **teste binomial exato** (par P4)
para investigar se a taxa de falha do CI do pytest ultrapassa 5%. O dashboard
reúne o cenário, a coleta, as simulações, os quatro gráficos e a recomendação
em sete seções.

[Dashboard local](http://127.0.0.1:8501/) ·
[Repositório](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software) ·
[GitHub Projects](https://github.com/users/Victorgabrielcruz/projects/7) ·
[Roteiro da apresentação](APRESENTACAO.md)

## Executar em um comando

Use Python 3.12 ou superior (validado com Python 3.14). Na raiz do repositório:

```text
python Lab04/executar.py
```

Use `python3` no macOS/Linux se o executável se chamar assim, ou
`py -3.14` no Windows se usar o Python Launcher. O comando cria o ambiente
isolado em `Lab04/.venv`, instala as versões fixadas em `requirements.txt`
e inicia o [dashboard local](http://127.0.0.1:8501/). A primeira instalação
precisa de acesso à internet para baixar as dependências. Se a porta 8501
estiver ocupada, acrescente `--porta 8502`.

## Reproduzir a análise

O dashboard usa o snapshot da coleta e os resultados de simulação versionados.
Para regenerar os dados tratados e a simulação a partir do snapshot e abrir
o dashboard no mesmo comando, execute:

```text
python Lab04/executar.py --reproduzir
```

A regeneração da análise não consulta a API do GitHub. A semente **42**,
a referência de **5%**, o nível de significância **α = 0,05** e a paleta
dos testes são definidos em `hipotese/config.py`. A simulação deriva cada
gerador de `SeedSequence(SEMENTE, spawn_key=(situação, efeito))`, de modo que
a ordem de execução das configurações não altera seus resultados.

## Publicação no Streamlit Community Cloud

Após incorporar a entrega à `main`, uma conta com acesso administrativo
ao repositório pode criar o app no [Streamlit Community Cloud](https://share.streamlit.io/):

| Campo | Valor |
|---|---|
| Repositório | `Victorgabrielcruz/lab-medicao-e-experimentacao-de-software` |
| Branch | `main` |
| Arquivo de entrada | `Lab04/app.py` |
| Versão do Python | `3.14` |

As dependências ficam ao lado do arquivo de entrada e o app usa apenas
dados versionados. O link **Dashboard** no topo aponta para a URL pela qual
o app foi aberto, local ou hospedada. Depois da publicação, confirme que a
URL pública abre as sete seções e registre-a no README.
[Documentação de publicação](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Cenário e coleta

- **Hipóteses:** H₀: p = 5%; H₁: p > 5%. A alternativa é à direita e rejeitamos
  H₀ quando `p-valor < α`. Os 5% são uma referência do laboratório.
- **Dados:** workflow `test` de `pytest-dev/pytest`, na `main`, por push,
  de 20/04/2026 a 30/10/2026 (UTC). Das 300 execuções consecutivas, 57 foram
  descartadas por cancelamento; sobraram 243, com 10 falhas (4,12%).
- **Modelo:** resultado binário, com taxa marginal de 5% mais o efeito.
  Foram 10.000 repetições por combinação de situação e efeito, de 0 a 10
  pontos percentuais. Comparamos builds independentes (n = 243), rajadas
  (n = 243, autocorrelação de lag 1 de aproximadamente 0,27) e amostra
  independente pequena (n = 20).
- **Testes:** o Z usa a variância sob H₀ e a aproximação normal sem correção
  de continuidade. O binomial exato usa a probabilidade de observar pelo
  menos o número de falhas da amostra. Ambos pressupõem independência.

A [documentação da coleta](data/README.md) detalha os critérios de seleção,
a cronologia e o tratamento de reexecuções. Os dados tratados estão em
[`data/ci_pytest.csv`](data/ci_pytest.csv), e as 36 linhas de resultados em
[`data/simulacao.csv`](data/simulacao.csv).

## Como ler os resultados

- **G1 — Dados reais e simulados:** a distribuição binária se concentra nos
  sucessos. Com 243 builds e semente 42, a amostra independente sob H₀ tem
  12 falhas (4,94%), contra 10 (4,12%) na coleta.
- **G2 — Distribuições sob H₀:** o exemplo independente com taxa verdadeira
  de 9% teve 17 falhas. As caudas destacadas dão p-valores de 7,67% para o Z
  e 10,40% para o binomial; nenhum rejeita H₀. Como nesse exemplo havia um
  aumento real na simulação, os dois cometeram erro tipo II.
- **G3 — Erro tipo I:** o Z foi liberal nas três situações. O binomial foi
  conservador sob independência e liberal nas rajadas.

| Situação | Z para proporção | Binomial exato |
|---|---:|---:|
| Independente | 6,55% | 3,96% |
| Rajadas | 11,83% | 8,60% |
| Amostra pequena | 7,35% | 1,49% |

Na Q1, a margem de ±0,4 ponto percentual define a faixa de 4,6% a 5,4%.
Na Q3, a margem de Monte Carlo é de aproximadamente ±0,43 ponto percentual.
Nenhuma das seis taxas fica perto de 5% por esses critérios.

- **G4 — Poder:** com efeito de +4 pontos percentuais e 243 builds
  independentes, o Z detectou o aumento em 83,40% das amostras e o binomial
  em 76,73%. O Z teve maior poder nos efeitos simulados e também mais
  falsos positivos; os testes têm níveis efetivos de erro tipo I diferentes.
- **Bônus — Poder interativo:** na seção 5, controles de tamanho da amostra,
  efeito e α atualizam as curvas e o poder dos dois testes. Com builds
  independentes, o poder é calculado de forma exata pela binomial, sem nova
  simulação. Com 250 builds, por exemplo, os dois testes rejeitam a partir de
  19 falhas e têm o mesmo poder.

### Aplicação aos dados reais

| Teste | Estatística | p-valor | Efeito em relação à meta | Conclusão |
|---|---:|---:|---:|---|
| Z para proporção | Z = −0,6328 | 0,7366 | −0,88 p.p. | Não rejeitar H₀ |
| Binomial exato | p̂ = 0,0412 | 0,7773 | −0,88 p.p. | Não rejeitar H₀ |

Nenhum teste encontrou evidência de taxa superior a 5%. A diferença
observada equivale a cerca de 0,88 falha a menos por 100 builds em relação
à meta, com importância prática ligada ao volume e ao custo das falhas.
Não rejeitar H₀ não demonstra que a meta seja cumprida.

### Recomendação e limitação

O binomial exato controlou falsos positivos sob independência, como
esperado; o Z ficou acima de 5% mesmo com 243 builds. Prefira o binomial
quando controlar falsos alertas for a prioridade. Considere o Z para
amostras maiores se a aproximação estiver bem calibrada; nas rajadas,
considere um método que leve em conta a dependência.

A coleta de um único workflow, com poucas falhas, limita a estimativa
de dependência e a generalização para outros projetos ou períodos.

## Arquivos e testes

| Caminho | Conteúdo |
|---|---|
| [`app.py`](app.py) | Dashboard em Streamlit |
| [`executar.py`](executar.py) | Execução local e regeneração opcional |
| [`hipotese/`](hipotese/) | Configuração, simulações, testes estatísticos, poder exato e gráficos |
| [`data/`](data/) | Snapshot, amostra tratada e resultados da simulação |
| [`tests/`](tests/) | Testes automatizados, incluindo renderização e reprodutibilidade |

Depois de preparar o ambiente, execute os testes na pasta `Lab04`:

```text
.venv/bin/python -m pytest
```

No Windows, use `.venv\Scripts\python.exe -m pytest`.
