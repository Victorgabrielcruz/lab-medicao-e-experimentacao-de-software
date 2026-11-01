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

Toda geração aleatória parte de `hipotese.config.gerador()`, que usa a semente
fixa `SEMENTE = 42`. O nível de significância (`ALFA = 0,05`), o número de
repetições (`N_REPETICOES = 10.000`) e a meta de 5% também ficam nesse módulo.
O mesmo vale para a cor de cada teste, que é igual em todos os gráficos.

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
