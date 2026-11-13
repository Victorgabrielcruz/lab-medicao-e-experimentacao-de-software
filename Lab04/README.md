# Lab04 — Testes de hipótese por dentro

Par P4: **Z para proporção** × **binomial exato**. A taxa de falha do CI do pytest supera a meta de 5%?

[Dashboard local](http://127.0.0.1:8501/) ·
[Repositório](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software) ·
[GitHub Projects](https://github.com/users/Victorgabrielcruz/projects/7)

## Executar

Python 3.12 ou superior. Na raiz do repositório:

```text
python Lab04/executar.py               # cria .venv, instala dependências e abre o dashboard
python Lab04/executar.py --reproduzir  # regenera dados tratados e simulação antes de abrir
python Lab04/executar.py --porta 8502  # se a porta 8501 estiver ocupada
```

A regeneração usa o snapshot versionado, sem consultar a API do GitHub. Semente, α, meta e cores
ficam em `hipotese/config.py`.

## Protocolo

| Item | Valor |
|---|---|
| Hipóteses | H₀: p = 5% · H₁: p > 5% (unicaudal à direita) · α = 0,05 |
| Dados reais | workflow `test` de `pytest-dev/pytest`, `main`, push, 20/04 a 30/10/2026 · 300 execuções, 57 canceladas excluídas · **243 builds, 10 falhas (4,12%)** |
| Simulação | Bernoulli com taxa 5% + efeito (0 a 10 p.p.) · 10.000 repetições por configuração · semente 42 |
| Situações | independente (n = 243) · rajadas (n = 243, ρ ≈ 0,27) · amostra pequena (n = 20) |

Critérios de coleta em [data/README.md](data/README.md).

## Resultados

| Medida | Z | Binomial |
|---|---:|---:|
| Erro tipo I · independente | 6,55% | 3,96% |
| Erro tipo I · rajadas | 11,83% | 8,60% |
| Erro tipo I · amostra pequena | 7,35% | 1,49% |
| Poder com +4 p.p. · independente | 83,40% | 76,73% |
| p-valor nos dados reais | 0,7366 | 0,7773 |

- **Dados reais:** nenhum teste rejeita H₀; efeito de −0,88 p.p. em relação à meta.
- **Recomendação:** binomial exato, que controla o erro tipo I sob independência. O Z tem mais poder, mas é liberal
  em todas as situações; com falhas em rajadas, nenhum dos dois é adequado.
- **Limitação:** um único workflow, com 10 falhas.
- **Poder interativo (bônus):** na seção 5, n, efeito e α ajustáveis, com poder exato pela binomial.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app.py` | Dashboard (Streamlit) |
| `executar.py` | Execução em um comando |
| `hipotese/` | Testes, simulação, poder exato e gráficos |
| `data/` | Snapshot, amostra tratada (`ci_pytest.csv`) e resultados (`simulacao.csv`) |
| `tests/` | Testes automatizados |

Testes, na pasta `Lab04`: `.venv\Scripts\python.exe -m pytest` (Windows) ou `.venv/bin/python -m pytest`.
