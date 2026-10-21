# Funil de seleção

Janela: `2025-10-01T00:00:00Z` a `2026-10-01T00:00:00Z` (exclusivo). Critério mínimo: 5 releases estáveis publicadas e 50 runs válidos na janela.

| Etapa | Entrada | Descartados | Restantes | Motivos de descarte |
|---|---:|---:|---:|---|
| Busca na Search API | 1064 | 0 | 1064 | — |
| Usa GitHub Actions | 1064 | 131 | 933 | `sem_github_actions`: 131 |
| Metadados coletados | 933 | 1 | 932 | `repositorio_inacessivel`: 1 |
| Releases coletadas | 932 | 0 | 932 | — |
| Workflow runs coletados | 932 | 363 | 569 | `prefiltro_releases_insuficientes`: 363 |
| Critério mínimo de inclusão | 569 | 68 | 501 | `runs_validos_insuficientes`: 68 |
| Coleta completa de runs (amostra oficial) | 501 | 1 | 500 | `coleta_runs_incompleta`: 1 |

Amostra final: **500** repositórios.
