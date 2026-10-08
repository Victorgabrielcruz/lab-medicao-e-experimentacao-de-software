# Relatório técnico — Victor, Lab03 Sprint 01

Atualizado em 08/10/2026 às 20:29 (America/Sao_Paulo). **Relatório parcial: coleta real em andamento.**
As entregas de código foram publicadas exclusivamente em
`feat/tasks-victor-sprint-01`. Este relatório não dá aceite, fecha issues nem
altera o GitHub Projects. A validação empírica ainda não permite encerrar o escopo.

## Critérios e situação por task

| Task | Evidência disponível | Situação técnica e trabalho restante |
|---|---|---|
| [#144 — cache/retomada](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/144) | Auditoria de `CacheDisco`, gravação atômica, chave por URL/página sem autenticação persistida; 19 testes do cache passam. | Dependência integrada e preservada; não reaberta. Retomada do novo pipeline validada com fixtures, sem novas chamadas para checkpoints concluídos. |
| [#145 — rate limit/backoff](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/145) | `X-RateLimit-Remaining`/`Reset` lidos por recurso; espera até reset + 1s; 5xx com 1, 2, 4 e 8s. 42 testes simulados e 100% de cobertura do módulo. | Critérios de implementação/testes auditados. Não foi provocado um 5xx ou esgotamento real para simular evidência; estado remoto preservado. |
| [#146 — workflow runs](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/146) | Coletor mensal integrado; 37 testes e 100% de cobertura. O piloto real tem 100 candidatos, 82 após Actions/metadados e 18 descartes de Actions. | **Validação real pendente:** `workflow_runs.json` ainda não existe. Não usar páginas do cache como consolidado. Auditoria automática preparada para identidades, default branch/push, janela, cobertura mensal, deduplicação e incompletude. |
| [#147 — CFR (a)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/147) | Fórmula falhas/(falhas+sucessos), três conclusions de falha, restantes ignoradas; 47 testes e 100% de cobertura. Auditoria independente dos contadores, fração, null e diagnósticos. | **Cálculo e validação reais pendentes** do consolidado da #146. A integração usa CFR sobre a amostra elegível completa. |
| [#148 — recuperação](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/148) | Implementação publicada em `8cc3c30`; episódios por workflow, primeira falha ao próximo sucesso, censura no fim; fixture de 1h20, mediana/IQR apenas dos recuperados. 66 testes e 100% de cobertura. | Implementação validada com fixtures; **validação real pendente** do piloto. O enunciado completo não está versionado; não se afirma confrontação com seu exemplo original. |
| [#149 — pipeline/100 repos](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/149) | Comando integrado, releases paginadas, funil, subdivisão de meses, checkpoints e auditoria; fixture obtém 100 elegíveis a partir de 120 candidatos. | **Execução real com 100 elegíveis pendente.** Executor iniciará após o piloto, com limite inicial de 1000 candidatos e saídas próprias. Compare #140 e lead time por release #141 foram integrados; a variante por commit #142 permanece dependência explícita; não há alegação de quatro métricas DORA completas. |
| [#150 — artigo SBC](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/150) | Pacote local com arquivo principal, cinco seções, abstract/resumo, quatro referências preservadas e links repo/Projects. Template SBC, licença e proveniência registrados. | **Projeto Overleaf e compilação pendentes.** `/project` abriu tela de login; nenhum projeto criado. O compilador nativo falhou por infraestrutura, sem comprovar compilação do pacote. |

As #146/#147 permanecem abertas e com validação pendente, embora os PRs
#196/#197 já estejam mesclados. Nenhum estado/label foi alterado pelo agente.

## Implementações e decisões

O commit da #134 (`caad3e1`, Jonathan Sena da Silva) foi revisado e incorporado
por cherry-pick como `2bf7947`, preservando autoria. O conflito no README foi
resolvido mantendo as seções de recuperação e funil. O PR #198 continuou aberto;
não foi mesclado na main pelo agente. Na consulta inicial não havia suporte
de releases/compare/lead time integrável nas branches consultadas. No heartbeat
seguinte surgiu a #138, já integrada pelo colega via PR #199, e a #139 via
PR #200. A coleta paginada de releases de Matheus (`9e27e1d`) foi revisada e
incorporada por cherry-pick como `245d69b`, preservando autoria, em substituição
ao suporte provisório local. Tags (#139) foram revisadas como dependência
potencial, mas não incorporadas: não são necessárias à definição principal
atual. Compare #140 tornou-se disponível em `feat/s01-12-compare-140`, commit
`7dfab9f` de Matheus, incorporado seletivamente como `bbf7053` com autoria
preservada e protocolo público. A #141 apareceu em
`feat/s01-13-lead-time-release-141`, commit `bff0827` de Matheus, incorporado por
cherry-pick como `adc125d`, preservando autoria. A #142 permanece indisponível
nas branches consultadas.

A #138 atualizou a documentação do protocolo para deploy e inclusão por
releases **estáveis**. A adaptação `e2a03de` torna isso explícito em
`inclusao.incluir_prereleases=false`, mantém os mínimos 5/50, aplica a mesma
política no prefiltro/funil/frequência e preserva as pré-releases no bruto para
variantes. Configurações antigas sem a chave mantêm a regra anterior; `true`
permite a variante com todas as publicadas. Testes de 4 estáveis + 1 prévia
comprovam que só a variante é incluída. O contexto de checkpoints foi versionado
para evitar misturar políticas ou contratos de coleta. Introdução/hipóteses
seguem preservadas; a metodologia e o ZIP refletem a definição atual do protocolo.
A auditoria de retomada agora exige hash e caminho de origem, evitando reutilizar
metadados de uma entrada de outra pasta mesmo com conteúdo idêntico.

`pipeline.integrado` executa seleção → Actions → metadados → releases → runs →
inclusão → CFR (a)/recuperação → auditoria → compare/lead time por release/frequência, em um comando.
O prefiltro de releases evita coletar runs de projetos que já não atingem o
mínimo; seus descartes não inferem contagens de runs. O alvo conta somente
repositórios com >=5 releases estáveis e >=50 runs válidos e coleta completa. Não reduzimos
critérios para produzir cem incluídos. Saídas parciais e dependências ausentes
são registradas em `execucao.json`; ausência de observações vira null.

A integração `004791c` coleta compare apenas para a amostra elegível. Usa
releases estáveis consecutivas em ordem cronológica, base anterior à janela
quando existir e `commit.author.date`, conforme protocolo público da #140.
Pagina com Link, registra o limite sem paginação de 250 commits e preserva os
motivos de descarte por 404/451 ou incompletude. Checkpoints próprios por
repositório permitem retomar a etapa sem repetir a coleta concluída nem os
cálculos auditados de CFR/recuperação. Um compare incompleto mantém diagnóstico
explícito; atingir a amostra de cem não comprova lead time observado nem todas
as variantes exigidas.
`compare.json` e as contagens de `execucao.json` ainda aguardam execução real.

O cálculo público da #141 define RQ02a como `published_at - min(commit.author.date)`
por release estável, em horas, seguido de mediana sem ponderação por commits.
Primeira release histórica sem anterior, compare incompleto/ignorado, ausência
de commits, datas inválidas e intervalos negativos mantêm valor nulo/motivo;
zero real é válido. `b1be141` integra a métrica e uma auditoria independente contra
commits, identidades, janela, mediana, classe, contagens e incompletude. O hash
de retomada inclui conteúdo/diagnósticos e origem; ignora somente o instante de
gravar o compare, para não repetir um cálculo já auditado com os mesmos dados.
Resultados corrompidos são recusados sem sobrescrita. Validação real pendente.

A coleta adicional está em módulo próprio, sem alterar o coletor do checkout
original. Meses com >1000 resultados são subdivididos recursivamente; páginas,
recorte e IDs são conferidos. Saturação em um segundo ou divergência das contagens
mantém incompletude. O cache REST original é reutilizado somente depois que a
coleta original acabar; meses completos do piloto também serão reutilizados.

A retomada conserva a busca completa em `candidatos_busca.json`, verifica um hash
de contexto e fonte para os checkpoints e revalida métricas já auditadas para
a mesma entrada, sem executar novamente seus cálculos. Erros não apagam páginas
ou checkpoints anteriores. O código de saída é 0 se o alvo for atingido, 3 se a
amostra for insuficiente e 2 em erro. `execucao_completa` refere-se ao alvo e às
métricas listadas, não ao atendimento de todas as dependências DORA.

`pipeline.auditoria` reconstrói contadores e episódios por workflow de forma
independente da rotina de produção. Confere origem/janela/identidades, branch,
evento, deduplicação, conclusões, censura, duração, quartis inclusivos e totais.
A documentação da janela foi corrigida: registros podem ser removidos/editados
mesmo em período fechado; a reprodução exige o snapshot e seus diagnósticos.

`.gitignore` foi ampliado para dados brutos/processados reais do Lab03 e
artefatos locais de compilação. Cada staging foi explicitamente revisado, com
lista de arquivos; nenhum dado real, cache, config de execução ou segredo entrou
nos commits. Espaços de fim de linha dos arquivos externos do template foram
preservados como na fonte; código/documentação autorais passaram por diff check.

## Evidências, testes e publicação

Última suíte: **518 testes passaram, cobertura global 98,63%**. CFR, recuperação,
workflow runs, releases, compare, lead time por release, rate limit e funil permanecem com 100% de cobertura. Auditoria:
96%; comando integrado: 93%; coletor completo de runs: 93%. Releases: 100%, incluindo paginação, datas inválidas, erros de acesso, cache,
retomada e o comando próprio da etapa.
Não confundimos cobertura com validação empírica.

Casos de integração: 120 candidatos → 100 incluídos; exclusão por releases,
amostra insuficiente; 404/sem Actions; transporte interrompido e retomada; mudança
de critérios; meses saturados e fronteiras; segundo saturado; reutilização apenas
de meses completos; métricas corrompidas recusadas; censura; fonte preservada na
ampliação e cálculos auditados não repetidos. Os testes usam respostas simuladas,
sem dados reais nem rede. A #140 acrescenta 34 testes públicos de paginação,
limites 249/250/251/301, histórico, deduplicação, erros/cache e CLI. Dois testes
adicionais verificam retomada do compare sem repetir métricas auditadas e 404
com amostra preservada e incompletude explícita. A #141 acrescenta 56 testes,
incluindo exemplo de 13 dias, autor/committer, fusos, nulos/zero, negativos,
mediana por release, classes e CLI local. Cinco casos adicionais recusam
corrupções de lead time na retomada; outro verifica que nova data de gravação
não repete o cálculo. A fixture de regravação explicita UTF-8 no Windows.

Comando de teste, no Lab03 do worktree autorizado:

```text
C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/.venv/Scripts/python.exe -m pytest --basetemp=.pytest_cache/sprint-01 --cov=pipeline --cov-report=term-missing --cov-fail-under=80
```

| Commit publicado | Entrega |
|---|---|
| `8cc3c30` | Recuperação por workflow, censura e testes (#148). |
| `c34e31b` | Plano inicial e fonte do template (#146–#150). |
| `2bf7947` | Funil #134, preservando autoria de Jonathan. |
| `50ecb8d` | Comando integrado, releases, subdivisão e auditoria (#149, #146–#148). |
| `45c524c` | Estrutura completa local SBC e proveniência (#150). |
| `752da84` | Fonte preservada, auditoria estrita e cálculos não repetidos na retomada (#149, #146–#148). |
| `73047ee` | Relatório parcial com evidências e acompanhamento (#145–#150). |
| `245d69b` | Coleta de releases #138, preservando autoria de Matheus. |
| `e2a03de` | Política estável do protocolo em seleção/funil/frequência e origem na retomada (#149, #138). |
| `951e574` | Plano/relatório após integração de releases e política estável. |
| `bbf7053` | Compare e protocolo público #140, preservando autoria de Matheus. |
| `004791c` | Compare apenas da amostra, checkpoints e diagnósticos no comando integrado (#149). |
| `c5c13ff` | Metodologia do artigo alinhada ao protocolo público de compare (#150). |
| `ed58485` | Relatório após integração de compare. |
| `adc125d` | Lead time por release #141, preservando autoria de Matheus. |
| `b1be141` | Lead time por release no integrado, auditoria e retomada (#149). |
| `db65477` | Metodologia com definição pública de lead time por release (#150). |

Publicação: somente `git push origin feat/tasks-victor-sprint-01`, sem force.
A branch do checkout original foi conferida e continua
`feat/lab03-s01-18-workflow-runs-146`.

## Coleta real e execução persistente

Fonte real de seleção conferida: **37.383 candidatos**. Piloto: **100 candidatos,
82 repositórios com Actions/metadados, 18 descartes**. Ainda não há quantidade
validada de runs, CFR ou episódios; não apresentamos estimativas inventadas.
Os processos originais permanecem ativos. Espera de rate limit não é falha.

Um executor próprio, iniciado oculto no Windows, possui trava de arquivo contra
duplicação. Estado local sem segredos:
`Lab03/.pytest_cache/sprint01-agente/estado.json`. Script local:
`Lab03/.pytest_cache/sprint01-agente/executor.py`. O heartbeat existente foi
atualizado para monitorar esse estado e esses processos, sem duplicar cálculos
ou automações; continua ativo a cada dez minutos, silencioso em espera normal.
A automação antiga de CFR continua pausada. A máquina e o app precisam continuar
ligados para esse acompanhamento.

O executor aguarda JSON consolidado válido, verifica identidades contra os
metadados e calcula somente as saídas ausentes. Saídas presentes são auditadas
sem sobrescrita silenciosa. Grava hash e agregados em
`.pytest_cache/sprint01-agente/validacao-piloto.json`; depois chama o comando
integrado público com a credencial Git existente somente em memória. A leitura
da API com essa credencial foi verificada (HTTP 200), sem exibir/gravar o token.

Entrada aguardada e saídas esperadas (ainda não comprovadas neste relatório):

```text
C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json
C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/cfr.json
C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/tempo_recuperacao.json
```

Comando real preparado pelo executor, com cwd no Lab03 do worktree:

```text
python -m pipeline.integrado --config .pytest_cache/sprint01-agente/config-integrado.yaml --alvo 100 --max-candidatos 1000 --candidatos C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/candidatos.json --reutilizar-runs C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json
```

A configuração local usa cache absoluto do checkout original e raw/processed
próprios no worktree: `data/raw/victor-sprint01-100` e
`data/processed/victor-sprint01-100`. Saídas esperadas: funil JSON/Markdown,
frequência, CFR, recuperação, compare bruto, lead time por release, auditorias
e `execucao.json`. Se não atingir cem
após o limite inicial, auditar o funil e ampliar gradualmente com os checkpoints;
não coletar indiscriminadamente todos os candidatos.

## Artigo, bloqueios e próximos critérios

[Arquivo principal](../artigo/main.tex), [instruções de importação](../artigo/README.md)
e [proveniência/licença](../artigo/PROVENIENCIA-template.md). ZIP local importável:
`Lab03/artigo/artigo-lab03-sbc.zip` (não versionado). Introdução/hipóteses e o
BibTeX original não sofreram mudanças. Conferência estrutural: cinco inputs
existentes, quatro referências, nenhuma citação sem chave e ambos os links
solicitados presentes. Resultados/discussão empírica continuam pendentes.

A [galeria Overleaf da SBC](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr)
atribui autoria à SBC e informa CC BY 4.0, com atualização de 2017. Sem sessão
para exportar seu pacote, os arquivos locais foram obtidos de um espelho SBC
2005 de Cezar Lamann, commit fixo e licença MIT, com avisos originais preservados.
Não afirmamos equivalência entre o .sty de 2005 e o de 2017.

O navegador confirmou tela de login no Overleaf. É necessária autenticação da
conta para criar/importar o projeto e registrar sua URL; esse critério não está
atendido. O editor nativo foi aberto no `main.tex`, mas o compilador retornou
`Unable to find standard directories for platform`. Trata-se de falha de
infraestrutura, não de evidência de erro corrigível na fonte. O editor também
não oferece suporte a arquivos adicionais desse projeto. Compilação do pacote
e inspeção visual permanecem não verificadas; não instalamos TeX ou plugin.

A tentativa de consultar o enunciado na sessão privada do Canvas foi rejeitada
pela revisão automática por ausência de autorização explícita para essa conta.
Foi solicitada autorização específica para ler somente o enunciado do Lab03;
nenhum conteúdo privado foi acessado e nenhum acesso alternativo foi tentado.
Enquanto não houver autorização, usar somente repositório/issues e dependências
públicas. Compare e lead time por release foram integrados com protocolo público;
a variante por commit #142 ainda depende de implementação/definição verificável.
Não inventar sua fórmula para declarar o pipeline completo.

O relatório será atualizado quando o consolidado e a execução dos cem elegíveis
forem auditados. O acompanhamento só será encerrado ao cumprir o escopo ou,
terminado todo trabalho independente, quando restar exclusivamente ação humana.
