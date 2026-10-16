# Encerramento humano da extração e amostra revisada — #151

> **Atualização 16/10/2026:** esta decisão foi substituída pela
> [retomada da coleta até 500](decisao-retomada-500.md). O texto abaixo
> registra o estado em 15/10/2026.

Em 15/10/2026, o responsável solicitou encerrar a extração e trabalhar com
os dados obtidos. As coletas principal e auxiliar foram encerradas. O
progresso oficial continha **561 candidatos avaliados e 255 repositórios
com coleta completa**. Os números têm significados distintos.

Esta decisão substitui a espera operacional por 300 elegíveis e pela meta
500. Não muda retroativamente os critérios de inclusão nem demonstra o
atingimento dos critérios originais da #151. A issue permanece aberta
para aceite humano do escopo revisado.

## População e preservação

A população é formada exclusivamente pelos 255 IDs elegíveis nos checkpoints
consumidos pelo progresso oficial no instante da parada. Checkpoints da
auxiliar ainda fora dessa ordem e tarefas em andamento não são incorporados.
Foram preservados a fonte, a configuração, os 561 checkpoints consumidos,
os compares já disponíveis e os estados da parada em um snapshot privado.
As cópias foram conferidas por SHA-256. Cache e dados brutos permanecem
locais e não são publicados.

O manifesto privado de autoridade é
`Lab03/data/processed/sprint02-agentes/encerramento-amostra.json` no checkout
original. Ele contém IDs, janela, contexto, hashes e localização do snapshot.
Novas saídas de consolidação devem ficar em diretórios separados dos antigos
coletores. Não há autorização para novas consultas à API ou retomada da extração.

## Procedimento mantido e limitações

A janela continua de 01/10/2025 inclusive a 01/10/2026 exclusive (UTC).
Permanecem os mínimos de cinco releases estáveis publicadas e 50 runs válidos,
com evento push e branch padrão. Nulos não equivalem a zero ou resposta negativa.

A política anterior priorizou custo observado antes do marco de 300 e previa
liberar grandes adiados nas próximas vagas, continuando até 500. O encerramento
em 255 ocorreu antes dessa liberação. Portanto, a ordem realizada não é estrita
por estrelas e pode favorecer projetos de menor custo de coleta. A interrupção
e o tamanho reduzido limitam a generalização dos resultados.

A consolidação é exclusivamente local. Deployment frequency, CFR(a) e tempo
de recuperação podem ser calculados dos checkpoints completos. Lead time nas
variantes (a)/(b) usa apenas os compares já disponíveis e compatíveis; ausências
continuam nulas e documentadas. CFR(b), dependente da #161, permanece pendente
na ausência de evidência. Consolidar esta amostra não torna completo o pipeline
original de 500 nem elimina essas pendências.

## Agentes e aceite

Os acompanhamentos #151, #153, #154, #158 e #166 passam a usar a população
encerrada, sem aguardar 300/500. Mantêm worktrees e estados separados,
periodicidade de 30 minutos, testes pertinentes, idempotência e silêncio
quando não houver mudança acionável. Nenhum agente reinicia a coleta.

A #153 publica o CSV consolidado e proveniência; a #154 confere o contrato;
a #166 revisa o procedimento do artigo preservando o piloto. A #158 continua
dependente do sorteio oficial #155 e da rotulagem humana independente. O
protocolo de 60 projetos e cinco releases por projeto não é substituído por
um segundo sorteio ou por rótulos automáticos. A #151 entrega evidência
agregada, distinguindo o escopo revisado dos critérios originais não atingidos.
Issues e Projects exigem aceite humano e não são alterados automaticamente.
