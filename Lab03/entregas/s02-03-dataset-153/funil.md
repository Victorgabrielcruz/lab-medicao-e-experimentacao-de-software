# Funil de seleção

Janela: `2025-10-01T00:00:00Z` a `2026-10-01T00:00:00Z` (exclusivo). Critério mínimo: 5 releases estáveis publicadas e 50 runs válidos na janela.

| Etapa | Entrada | Descartados | Restantes | Motivos de descarte |
|---|---:|---:|---:|---|
| Busca na Search API | 561 | 0 | 561 | — |
| Usa GitHub Actions | 561 | 74 | 487 | `sem_github_actions`: 74 |
| Metadados coletados | 487 | 1 | 486 | `repositorio_inacessivel`: 1 |
| Releases coletadas | 486 | 0 | 486 | — |
| Workflow runs coletados | 486 | 198 | 288 | `prefiltro_releases_insuficientes`: 198 |
| Critério mínimo de inclusão | 288 | 32 | 256 | `runs_validos_insuficientes`: 32 |
| Coleta completa de runs (amostra oficial) | 256 | 1 | 255 | `coleta_runs_incompleta`: 1 |

Amostra final: **255** repositórios.
