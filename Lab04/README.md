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
