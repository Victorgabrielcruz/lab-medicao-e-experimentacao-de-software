# Revisão da análise e preparação do Relatório Final na Sprint 3 — Lab02

**Verificação:** 23/09/2026 · **Issue:** [S03-08, #82](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/82) · **Projects:** [board do Lab02](https://github.com/users/Victorgabrielcruz/projects/6/views/1).

## Cobertura das RQs

| RQ | Análise e discussão | Script e teste | Gráficos | Estado |
|---|---|---|---|---|
| RQ1, tempo | [`rq1-analysis.md`](../reports/drafts/rq1-analysis.md) e [`rq-answers.md`](../reports/drafts/rq-answers.md) | `scripts/analyze_rq1.py`, `tests/test_rq1_time.py` | `reports/figures/rq1/duration_by_treatment.png`, `paired_duration.png` e dashboard pareado | Presente; 9/9 pares, 7 a favor de IA e 2 a favor de Manual. |
| RQ2, testes | [`rq2-analysis.md`](../reports/drafts/rq2-analysis.md) e [`rq-answers.md`](../reports/drafts/rq-answers.md) | `scripts/analyze_rq2.py`, `tests/test_rq2_defects.py` | `reports/figures/rq2/success_rate_by_treatment.png`, `paired_success_rate.png` e dashboard | Presente; empate 9/9 condicionado à interpretação documentada de `P01-K02-manual`. |
| RQ3, estrutura | [`rq3-analysis.md`](../reports/drafts/rq3-analysis.md), [`rq-answers.md`](../reports/drafts/rq-answers.md) e [`validity-threats.md`](../reports/drafts/validity-threats.md) | `scripts/analyze_rq3.py`, `tests/test_rq3_structure.py` | `reports/figures/rq3/` e dashboard com complexidade, duplicação e LOC | Presente com cobertura parcial: 10/18 trials medidos e 4/9 pares completos. |

A [`metodologia`](methodology.md) preserva o desenho planejado; a [`revisão de validade`](../reports/drafts/validity-threats.md) interpreta desvios reais, direção possível dos vieses, pseudorreplicação e limites de generalização. A falta de oito coletas de métricas estruturais não foi convertida em zero nem ocultada.

## Scripts, testes, dados e dashboard

- Estão versionados os scripts de validação, análises consolidadas e individuais, geração de dashboard e os testes em `scripts/`, `src/analysis/`, `src/dashboard/` e `tests/`. A análise consolidada publica `data/processed/statistical-results.csv` e as respostas em `reports/drafts/rq-answers.md`.
- O [dataset oficial](../data/processed/trials.csv) foi autorizado pela [validação](../reports/drafts/data-validation.md): 18 trials, 9 pares, zero erros críticos, 31 avisos e um tempo extremo preservado. O CSV permanece a fonte das figuras.
- `src/dashboard/app.py` e `src/dashboard/figures.py` chamam `load_validated_dataset` antes de exibir ou gerar figuras. `scripts/generate_dashboard.py` usa `data/processed/trials.csv` por padrão.
- Em 23/09, a suíte `.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --disable-warnings --tb=short` passou. A execução inicial sem restringir `tests/` tentou coletar todas as katas como um módulo único; a invocação acima é a correta para os testes do projeto.
- Em 23/09, `.\.venv\Scripts\python.exe scripts/generate_dashboard.py --dataset data/processed/trials.csv --output reports/figures/dashboard` passou: **12 figuras, `index.html` e dois CSVs**. `trial-points.csv` contém 18 IDs distintos; `paired-points.csv` contém 9 linhas para cada uma das 6 métricas (54 linhas). O índice exibe 18 trials, 0 censurados e 10/18 com métricas estruturais. O teste automatizado também rejeita dataset não autorizado antes de criar saída.
- Inspeção visual das figuras pareadas de RQ1 e RQ3 e da figura de RQ2: títulos, eixos, unidades, legenda e fonte estão presentes; pontos e ausências são exibidos. Algumas etiquetas de pares próximos se sobrepõem; os pontos, as linhas e os CSVs continuam disponíveis para leitura. Isso merece ajuste de apresentação antes de selecionar figuras para o Relatório Final.
- A regeneração altera timestamps e identificadores internos dos SVGs, embora os PNGs e os dois CSVs não tenham mudado no `git status`. As diferenças de SVG criadas apenas pelo teste foram descartadas; esse detalhe deve ser considerado se a entrega exigir igualdade byte a byte.

## Contribuição individual por código na S03

A [regra do plano](tasks.md) exige que cada integrante seja Assignee de uma Issue que produza código commitado em cada sprint; Issues só documentais ou administrativas não bastam. O histórico do repositório entre **19 e 23/09/2026** mostra:

| Integrante no Git | Evidência de código S03 | Veredito |
|---|---|---|
| Victor (`Victor`) | `9fb8ac6` (#79, análise consolidada) e `16dbbd3` (#80, dashboard e testes) | Evidenciado. |
| Jonathan (`Jonathan Sena da Silva`) | `dcee756` (#75, validador), `5a7808e` (#76), `c0f5581` (#77) e `36c3b9a` (#78) | Evidenciado. |
| Matheus (`matheus-0063`) | RF-01 (#83), RF-02 (#84) e RF-03 (#85) atribuídas para a etapa final da S03; nenhum commit de código S03 encontrado até 23/09 | **Planejado, ainda não realizado:** RF-01 prevê script/notebook de apoio ao relatório com commit de Matheus. |

A autoria nominal dos trials da S02 tem divergências documentais descritas em `validity-threats.md`. Para Victor e Jonathan, a tabela usa autores de commits da S03; para Matheus, mostra somente atribuições planejadas, sem inferir quem executou cada trial experimental.

O Relatório Final é a **etapa final da S03**, conforme organização definida pelo grupo, embora seja uma entrega de 5 pontos separada de Lab02S03 no enunciado. Matheus ficará responsável por essa etapa; as Issues #83–#85 já estão atribuídas a ele no Projects. Para cumprir a regra de contribuição individual da S03, o trabalho no relatório deve incluir um artefato de código commitado por ele e vinculado à Issue. A atribuição e o trabalho planejado não são evidência de entrega concluída.

## Projects e snapshot

As Issues #79–#82 tiveram critérios conferidos, comentários de evidência publicados, foram movidas para **Done** e encerradas. #75–#78 também estão **Done**. As Issues #83–#85 foram identificadas como **[S03]**, estão atribuídas a Matheus e seguem **Ready** até o início do trabalho. O [snapshot atualizado do Projects](../data/project-snapshots/2026-09-23-s03-final-phase-backlog.tsv) preserva 45 linhas carregadas da visão Backlog e confirma títulos e status. O [snapshot anterior](../data/project-snapshots/2026-09-23-s03-backlog.tsv) foi mantido para rastrear a atualização; a exportação da interface inclui apenas linhas carregadas.

## Insumos para o Relatório Final

- Protocolo e execução: `Docs/methodology.md`, `Docs/protocol-decisions.md`, `Docs/kata-equivalence.md`, `Docs/execution-audit.md` e `data/metadata/allocation.csv`.
- Dados e rastreabilidade: `data/processed/trials.csv`, `data/processed/statistical-results.csv`, `reports/drafts/data-validation.md`, registros brutos dos trials e notas de incidentes.
- Resultados: os três `reports/drafts/rq*-analysis.md`, `reports/drafts/rq-answers.md`, `reports/drafts/validity-threats.md` e figuras em `reports/figures/`.
- Reprodução: `scripts/run_analysis.py`, `scripts/generate_dashboard.py`, `src/analysis/`, `src/dashboard/`, `tests/` e `requirements-analysis.txt`.
- Ressalvas obrigatórias no texto final: RQ1 tem só três participantes; RQ2 depende da interpretação do `poll` de P01; RQ3 usa apenas quatro pares completos; a autoria dos trials oficiais e alguns desvios ainda exigem reconciliação. Preservar os resultados desfavoráveis à IA.

**Estado de S03-08:** concluída a revisão da análise, dos gráficos, scripts, dashboard, Issues e insumos do relatório. A **Sprint 3** continua em execução na etapa do Relatório Final; o fechamento ocorre em RF-03, após a entrega do relatório e a verificação do commit de código de Matheus.
