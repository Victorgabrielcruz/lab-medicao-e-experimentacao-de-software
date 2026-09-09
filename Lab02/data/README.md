# Dados do experimento

| Pasta | Finalidade |
|---|---|
| `raw/trials/` | Logs, tempos e resultados brutos dos testes |
| `raw/metrics/` | Saídas originais das ferramentas de métricas estáticas |
| `processed/` | Dataset consolidado e resultados estatísticos |
| `metadata/` | Protocolo, ambiente, alocação e equivalência das katas |
| `project-snapshots/` | Snapshots do GitHub Projects |
| `training/` | Registros de treinamento, excluídos da análise oficial |

Dados brutos não devem ser alterados manualmente nem sobrescritos. Toda transformação deve ser reproduzível por código e gravada em `processed/`.
