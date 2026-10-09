# Relatório final da entrega limitada — Victor, Lab03 Sprint 01

Atualizado em 08/10/2026 (America/Sao_Paulo). **Entrega parcial baseada no
piloto disponível. A Sprint 01 e a #149 não estão integralmente concluídas.**

O usuário pediu explicitamente cancelar a coleta adicional dos cem elegíveis
e usar o que já havia sido obtido, registrando o limite de tempo na task.
Essa decisão substitui a ampliação antes prevista. Executor e pipeline
adicionais foram encerrados; seus PIDs não estão vivos. Cache, checkpoints,
dados e worktrees foram preservados. A guarda local impede retomada pelo
executor. Não ampliar nem iniciar coleta sem nova autorização humana.

O [comentário factual na #149](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/149#issuecomment-6072163752)
já registra a decisão, as contagens e o requisito não atendido. Foi verificado
e não duplicado. Não houve aceite remoto, fechamento de issues, mudanças de
estado/labels/Projects, merge de PRs ou alteração da main pelo agente.

## Situação por task: implementação, execução e pendência

| Task | Implementação e testes | Evidência empírica e limite |
|---|---|---|
| [#145 — rate limit/backoff](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/145) | Headers por recurso; espera até reset + 1s; 5xx com 1/2/4/8s; 42 testes simulados, cobertura 100%. Cache #144 auditado como dependência. | Não foram provocados erros remotos para fabricar evidência. Testes verificam comportamento, sem comprovar um cenário real de 5xx. |
| [#146 — workflow runs](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/146) | Coletor mensal, deduplicação e filtros; integrado com subdivisão recursiva dos intervalos saturados. | Piloto original consolidado: 100 candidatos, 82 após Actions/metadados, 238.629 runs. Há 18 coletas incompletas; não equivale a cem elegíveis. |
| [#147 — CFR (a)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/147) | Falhas/(falhas+sucessos), conclusions e null; 47 testes, cobertura 100%; auditoria independente. | 70 repos com CFR e 12 sem runs válidos; 22.893 falhas e 194.519 sucessos. Saída auditada e preservada byte a byte após a correção da RQ04. Incompletude permanece. |
| [#148 — recuperação](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/148) | RQ04 v2 conforme enunciado, censuras esquerda/direita, proporção por repo, diagnóstico temporal; 64 testes específicos. | 56 repos com recuperação, 6.163 episódios recuperados, 38 censurados; 92 sequências iniciais com censura à esquerda e 1 repo temporalmente incompleto. Legado por criação preservado, sem conformidade RQ04. |
| [#149 — pipeline/cem repos](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/149) | Comando único, seleção gradual, releases, runs, funil, CFR/recuperação, compare/LT por release, frequência, cache/checkpoints/auditorias. Fixture: 120 candidatos → 100 elegíveis. | Coleta adicional cancelada por decisão humana/tempo. **Meta de cem elegíveis completos não atendida.** No material existente: 0 elegíveis completos confirmados, 42 não elegíveis conhecidos e 40 indeterminados. Nenhum LT real observado; #142 permanece dependência de integração. |
| [#150 — artigo SBC](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/150) | Projeto existente atualizado com template 2017 preservado, seis inputs, abstract/resumo, quatro referências e links repo/Projects. | Compilado no Overleaf: seis páginas A4, zero erros/avisos/info; PDF baixado e todas as páginas inspecionadas. RQ05–07 foram complementadas após o piloto: não se declara anterioridade a toda coleta nem análise das hipóteses concluída. |

A entrega online da #150 tem evidência real de compilação. Isso não elimina o
critério temporal das hipóteses complementares nem as demais pendências da
sprint. Fixtures, cobertura e arquivos existentes não substituem execução real.

## Piloto real auditado

Janela UTC: 2025-10-01 inclusive a 2026-10-01 exclusive. O snapshot final
original foi gravado atomicamente; páginas de cache não o substituem.
Identidades e totais foram confrontados com metadados; runs foram conferidos
quanto a default branch, evento push, recorte, deduplicação e diagnósticos.

| Evidência | Quantidade |
|---|---:|
| Candidatos do piloto / após Actions e metadados | 100 / 82 |
| Descartes na etapa de Actions | 18 |
| Runs deduplicados no recorte | 238.629 |
| Runs válidos CFR | 217.412 |
| Falhas / sucessos / conclusions ignoradas | 22.893 / 194.519 / 21.217 |
| Repos com CFR / sem runs válidos | 70 / 12 |
| Repos com recuperação observada v2 | 56 |
| Episódios recuperados / censurados à direita | 6.163 / 38 |
| Episódios definidos | 6.201 |
| Sequências iniciais com censura à esquerda | 92 |
| Repos com dados temporais incompletos | 1 |
| Coletas de runs completas / incompletas | 64 / 18 |

**A auditoria demonstra correspondência com o snapshot, não completude de
todos os históricos.** As 18 coletas incompletas podem afetar CFR e episódios;
não foram promovidas a amostra elegível nem ocultadas. As contagens globais
não são medianas por repositório ou confirmação das hipóteses.

Origem: [workflow_runs.json](C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json),
150.200.426 bytes, SHA-256
`02acec9ceb3285d53a14a44ea2fcbb9330b5bb47b5215a6fd486a732e3fd32f1`.

Saídas locais, não versionadas:

- [CFR auditada](C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/cfr.json).
- [Recuperação RQ04 v2](C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/tempo_recuperacao.json).
- [Auditoria atual](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/.pytest_cache/sprint01-agente/validacao-piloto-rq04-v2.json).
- [Estado consolidado](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/.pytest_cache/sprint01-agente/estado.json).
- [Legado anterior preservado](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/.pytest_cache/sprint01-agente/legado-created-at/tempo_recuperacao.json).

## Reaproveitamento offline e elegibilidade

Após o cancelamento, uma rotina Python leu somente páginas do cache REST já
existente, com transporte de rede bloqueado. Foram lidas dez páginas e
realizadas **zero consultas de coleta**. CFR e recuperação v2 não foram
recalculadas. Nenhum novo repositório foi consultado.

| Disponibilidade no universo de 82 | Quantidade |
|---|---:|
| Repos com pelo menos 50 runs válidos | 61 |
| Releases com paginação completa disponível | 5 |
| Releases sem evidência local suficiente | 77 |
| Elegíveis completos confirmados | 0 |
| Não elegíveis pelos critérios já conhecidos | 42 |
| Elegibilidade indeterminada | 40 |
| Documentos de compare disponíveis / comparações com commits | 4 / 0 |
| Repos com LT por release observado | 0 |

Critérios: pelo menos cinco releases estáveis, cinquenta runs válidos e coleta
completa. Os diagnósticos de runs, releases e incompletude se sobrepõem; não são
etapas cumulativas de um funil. Zero confirmado **não significa que todos os
82 sejam inelegíveis**: quarenta permanecem indeterminados. Releases
indisponíveis não viram zero observado. DF foi calculada somente nos cinco
casos com releases completas disponíveis; os demais têm ausência/motivo.
Quatro documentos vazios de compare não comprovam coleta real de commits.

Artefatos ignorados no worktree:

- [Disponibilidade e diagnóstico por repo](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/disponibilidade.json).
- [Funil diagnóstico JSON](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/funil.json) e [Markdown](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/funil.md).
- [Releases reutilizadas](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/victor-piloto-existente/releases.json).
- [Compare disponível](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/victor-piloto-existente/compare.json).
- [Frequência semanal](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/deployment_frequency.json).
- [LT por release e ausências](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/lead_time_release.json).
- [Auditoria do LT disponível](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/victor-piloto-existente/auditoria_lead_time.json).

A execução adicional preservou cinco checkpoints de candidatos concluídos e
nenhum incluído. Seu cache e saídas parciais continuam em
`data/raw/victor-sprint01-100`, `data/processed/victor-sprint01-100` e
`.pytest_cache/sprint01-agente/`. Não há consolidação de cem elegíveis.

## Contrato corrigido e dependências

O enunciado oficial foi fornecido pelo usuário como anexo, SHA-256
`264f8496c57253ce16de555151a132f686a2a6de341bd4d9996510569d53522a`.
Não foi necessário retornar ao Canvas.

RQ04 v2 exige sucesso anterior observado no mesmo workflow. A duração é
`success.updated_at - first_failure.run_started_at`; created_at serve ao
recorte, sem fallback para a duração. Falhas consecutivas mantêm o início.
Sucesso terminado fora da janela mantém censura à direita; sequências iniciais
sem sucesso anterior são censura à esquerda separada. Timestamps essenciais
inválidos impedem estimativa do workflow com diagnóstico, evitando unir
episódios ao remover apenas um run. Proporção censurada usa os episódios
definidos; mediana/IQR inclusivos usam somente recuperações observadas.

Versão: `rq04-updated-at-run-started-at-v2`. O cálculo anterior por criação
(57 repos, 6.206 recuperados/66 censurados) foi preservado como legado.
A recuperação foi recalculada **uma vez** após mudar esse contrato e auditada
independentemente. CFR e entrada bruta permaneceram idênticas.

DF usa releases/semana, com semanas reais da janela. Os cortes fixos do
enunciado são 7/semana, 1/semana, 1/mês; o limite mensal civil equivale a doze
releases em doze meses. LT usa 24/168/720 horas; CFR usa 15/30/45% e recuperação
1/24/168 horas. Versão: `lab03-enunciado-cortes-v2`. Migração de classes audita
valores antes de reclassificar, sem repetir os intervalos; corrupção é recusada.

Dependências integradas preservando autoria: funil #134 de Jonathan
`caad3e1 → 2bf7947`; releases #138 de Matheus `9e27e1d → 245d69b`;
compare #140 `7dfab9f → bbf7053`; LT por release #141
`bff0827 → adc125d`. Nenhum PR dessas pessoas foi mesclado pelo agente.
Tags não eram necessárias à definição principal. A #142 permanece dependência:
a fórmula por commit é conhecida pelo enunciado, mas não se declara
implementação/integridade das quatro métricas completas.

O comando integrado preserva identidade/contexto dos checkpoints, hash e
origem das entradas, subdivide intervalos saturados e coleta compare somente
para a amostra. Auditorias independentes confrontam contadores, episódios,
censuras, quartis, classes, commits e motivos de ausência. Retomadas não repetem
métricas auditadas para a mesma versão/entrada. Saturação em um segundo ou
divergência de contagens continua incompleta.

## Testes, CI e comandos

Última suíte local após as correções: **532 testes aprovados, 97,89% de
cobertura global**. CFR, runs mensais, releases, compare, LT por release,
rate limit, funil e classificação: 100%; recuperação: 98%; auditoria: 91%;
integrado e coletor completo de runs: 93%.

Cobrem paginação/limites, meses e segundos saturados, fronteiras UTC,
deduplicação, conclusões, censura, timestamps distintos, ausência/zero,
corrupção recusada e retomada sem repetir cálculos. Testes com respostas
simuladas não são evidência empírica. A fixture 120→100 comprova o fluxo,
não o cumprimento do alvo na execução cancelada.

Com cwd em `C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03`:

```text
C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/.venv/Scripts/python.exe -m pytest --basetemp=.pytest_cache/sprint-01 --cov=pipeline --cov-report=term-missing --cov-fail-under=80
```

CI pública das correções:
[RQ04 5dfddfb — sucesso](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/runs/37866803433);
[classificação beeafad — sucesso](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/runs/37867066231).
O workflow usa Ubuntu/Python 3.11 e 3.13 e exige cobertura mínima de 80%.
[CI do artigo 4948cf2 — sucesso](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/runs/37869284833).
Os três resultados foram consultados na API pública, sem inferência a partir
dos testes locais.

Operações offline efetivamente aplicadas: invocação Python via stdin no
Lab03 exclusivo; `pipeline.tempo_recuperacao.executar(config, entrada, saida)`
e `pipeline.auditoria.validar` para a mudança de contrato; leitura de
`CacheDisco` com rede impedida para releases/compare e diagnósticos.
As saídas já auditadas não foram recalculadas durante a entrega final.

Comando integrado **histórico, cancelado; não executar novamente**:

```text
python -m pipeline.integrado --config .pytest_cache/sprint01-agente/config-integrado.yaml --alvo 100 --max-candidatos 1000 --candidatos C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/candidatos.json --reutilizar-runs C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json
```

Config/cache originais não foram modificados. Credencial Git esteve apenas
em memória; nenhuma credencial foi publicada. A coleta original e sua branch
`feat/lab03-s01-18-workflow-runs-146` foram preservadas.

## Artigo online e artefatos finais

[Projeto Overleaf fornecido pelo usuário](https://www.overleaf.com/project/6ac8318e750c2cce451d6f68).
O template original foi exportado antes da edição. O .sty e .bst finais
foram confrontados byte a byte com esse backup, sem alterações online.
A versão em uso é SBC 2017, com licença/proveniência registradas; 2005
permanece histórico em 45c524c, sem alegação de identidade.

[Arquivo principal](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/artigo/main.tex),
[README](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/artigo/README.md) e
[proveniência](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/artigo/PROVENIENCIA-template.md).
Introdução original e quatro referências locais continuam preservadas.
Seis inputs cobrem introdução, hipóteses complementares, metodologia,
resultados parciais, discussão e conclusão. Links repo/Projects estão no PDF.

RQ05–07 foram complementadas **após o piloto**, antes das análises dessas
questões. Essa cronologia é explícita e não satisfaz retroativamente o
registro anterior a toda coleta. Os rótulos das quatro hipóteses originais
ficaram preservados mesmo onde divergiam dos cortes confirmados.

Compilação final Overleaf: **6 páginas A4**, zero erros, zero avisos, zero
mensagens de diagramação; todas as páginas foram renderizadas e inspecionadas.
Export final conferido com fontes locais após normalização de fins de linha
e espaço final. O compilador nativo teve falha de infraestrutura; nenhum
TeX/plugin foi instalado. A comprovação de compilação vem do Overleaf.

- [PDF final](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/artigo/artigo-lab03-sbc.pdf), 119.795 bytes;
  SHA-256 `c62aba96886c8003c9cbe8ccb12d36c2f105d4c517d2877501095bc25fb15f88`.
- [ZIP importável](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/artigo/artigo-lab03-sbc.zip), treze arquivos.
- [Export final preservado](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/.pytest_cache/sprint01-agente/artigo-overleaf-final.zip).
- [Conferência visual, página de resultados](C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software/Lab03/.pytest_cache/sprint01-agente/pdf-qa/final-5.png).

PDF, ZIP, dados e cache são locais e ignorados pelo Git. Somente contagens
agregadas, código/testes e fontes/documentação revisadas foram publicadas.

## Commits e publicação

| Commit | Entrega |
|---|---|
| `2bf7947` | Funil #134, autoria de Jonathan preservada. |
| `50ecb8d`, `752da84` | Integrado/subdivisão/auditoria e retomada estrita (#149). |
| `245d69b`, `e2a03de` | Releases de Matheus e política estável de inclusão. |
| `bbf7053`, `004791c` | Compare de Matheus e integração com checkpoints. |
| `adc125d`, `b1be141` | LT por release de Matheus e auditoria/retomada. |
| `45c524c` | Pacote local SBC 2005, preservado no histórico (#150). |
| `704fcc8` | Piloto auditado sob contrato anterior, corrigido depois. |
| `5dfddfb` | RQ04 conforme enunciado, auditoria v2 e piloto corrigido (#148). |
| `beeafad` | DF semanal e cortes fixos oficiais (#149). |
| `4948cf2` | Artigo SBC 2017, online compilado e resultados parciais (#150). |

Publicação exclusivamente por `git push origin feat/tasks-victor-sprint-01`,
sem force. Cada staging teve lista explícita e revisão; dados reais/cache,
config local, credenciais, PDF e ZIP não entraram nos commits.
O estilo externo preserva espaços/cabeçalhos do export; fontes autorais
passaram por diff check. Este relatório e o plano registram a entrega limitada em commit próprio
da #149; o hash pode ser consultado no histórico da branch.

## Encerramento deste acompanhamento

O trabalho autorizado sobre o piloto e o artigo foi entregue. O heartbeat
foi pausado, com a proibição de retomar coleta preservada. A amostra de cem
elegíveis completos, LT observado/variante por commit e o registro anterior
à coleta das hipóteses complementares continuam pendentes; não se dá aceite
integral da Sprint 01. Validação manual de sessenta projetos/Sprint 02 e
análises RQ05–07/Sprint 03 não foram executadas como parte desta entrega.
