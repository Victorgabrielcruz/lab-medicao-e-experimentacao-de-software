# Figuras e tabela do relatório final

Esta pasta contém apenas artefatos usados por `reports/final/relatorio-final.md` e
`reports/final/relatorio-final.docx`.

| Artefato final | Origem rastreável | Gerador |
| --- | --- | --- |
| `rq1_duration.png` | `reports/figures/dashboard/rq1_duration.png` | `scripts/generate_dashboard.py` |
| `rq2_outcomes.png` | `reports/figures/dashboard/rq2_outcomes.png` | `scripts/generate_dashboard.py` |
| `rq3_structure.png` | `reports/figures/dashboard/rq3_structure.png` | `scripts/generate_dashboard.py` |
| `tabela-resumo-rqs.csv` e `tabela-resumo-rqs.md` | `data/processed/statistical-results.csv` | `scripts/generate_final_report_table.py` |

As três imagens foram selecionadas da saída do dashboard e copiadas sem edição
manual. Para recriá-las, execute primeiro `scripts/run_analysis.py` e depois
`scripts/generate_dashboard.py`; para recriar a tabela, execute
`scripts/generate_final_report_table.py`.
