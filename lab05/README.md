# Lab05 — Experimento em software real: SQLite

Experimento controlado sobre o desempenho do **SQLite** em execução local, comparando
dois fatores de configuração em um desenho fatorial 2 × 2:

| Fator | Níveis |
|---|---|
| `journal_mode` | `DELETE` (padrão) × `WAL` |
| `synchronous` | `FULL` (padrão) × `NORMAL` |

Cada configuração é medida em três cargas (escrita, leitura e mista), com
30 repetições e 3 de aquecimento descartadas. Os parâmetros ficam em
[`experimento/config.py`](experimento/config.py).

## Estrutura

```
lab05/
├── executar.py          # ponto de entrada do experimento
├── experimento/
│   ├── config.py        # fatores, cargas, repetições e semente
│   └── ambiente.py      # registro de versões, hardware e disco
├── tests/
└── data/                # saídas locais (ambiente.json, bancos, CSVs)
```

## Como executar

Requer Python 3.12.

```bash
cd lab05
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python executar.py
```

O comando registra o ambiente em `data/ambiente.json` e executa o plano de coleta.

## Testes

```bash
.venv/Scripts/python -m pytest
```

## Ética

Execução apenas local: nenhum sistema de terceiros é acessado e nenhum dado pessoal é coletado.
