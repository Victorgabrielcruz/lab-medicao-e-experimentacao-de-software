# Decisões da coleta final — S02-01 (#151)

## 2026-10-14 — Adiar projetos com alto volume de runs até 300 elegíveis

**Decisão autorizada pelo responsável pela coleta:** preservar todos os dados
já obtidos, priorizar os demais candidatos até alcançar **300 repositórios
elegíveis com coleta completa de runs**, então liberar os grandes adiados nas
próximas vagas. A meta final continua sendo **500**, e não 300 candidatos
avaliados. Comparações de commits e cálculos continuam sendo exigidos pelo
pipeline depois da seleção.

### Por que fizemos isso

A coleta chegou a 102 elegíveis entre 211 candidatos avaliados e ficou
concentrada em projetos com histórico de CI muito grande. Um repositório,
`unslothai/unsloth`, levou aproximadamente 19 minutos. No snapshot de
14/10/2026 às 17h48 (America/Sao_Paulo), `grafana/grafana` já acumulava
**107.617 runs em sete meses**, com **21.902 em um único mês**, e ainda
faltavam meses para concluir sua coleta. A fila limitada, consumida em ordem,
fazia esse candidato retardar a avaliação dos seguintes.

O critério para reconhecer trabalho pesado neste replanejamento foi volume
de **workflow runs observados**, não tamanho em disco, número de estrelas
ou linguagem: pelo menos 20.000 runs somados nos meses concluídos, ou pelo
menos 5.000 em um mês. Aplicamos o critério somente a candidatos pendentes
com evidência no log; custo desconhecido não implica projeto pequeno.
Projetos grandes já concluídos permanecem incluídos.

Na preparação, o único pendente reconhecido e adiado foi `grafana/grafana`
(ID GitHub `15111821`). O snapshot original e a lista de evidências ficam
preservados localmente, permitindo revisar a decisão. Não foram reduzidos
os cinco releases estáveis, cinquenta runs válidos, janela, branch/evento
ou as verificações de completude.

### Regra de execução e retomada

1. Preservar o prefixo confirmado e seus checkpoints; manter os 102 elegíveis
   como dados concluídos, sem consultá-los novamente na API.
2. Manter os demais candidatos na ordem relativa original, deixando os
   identificados como pesados em uma fila separada.
3. Antes de 300 elegíveis, não iniciar os adiados. Se os demais se esgotarem
   sem atingir 300, registrar amostra insuficiente, sem violar essa regra.
4. A partir de 300, priorizar os adiados nas próximas vagas. Tarefas já em
   andamento terminam normalmente; não são canceladas para trocar a ordem.
5. Depois deles, continuar pelos restantes até atingir os 500 elegíveis ou
   esgotar o limite de candidatos. Checkpoints de compares e páginas parciais
   de runs, inclusive de Grafana, continuam sendo reaproveitados.

A política fica na fonte de candidatos em `agendamento`, com
`liberar_adiados_com_elegiveis=300` e `adiados_ids`. O hash da fonte identifica
a nova execução. A migração copia apenas checkpoints de candidatos com
identidade e regras compatíveis, mantendo os originais. O progresso registra
`ids_avaliados` na ordem efetivamente consumida e `adiados_liberados`;
a auxiliar usa esses IDs, em vez de presumir um prefixo fixo do arquivo.

Foi necessário reiniciar os coletores para carregar a política. O responsável
autorizou essa retomada após confirmar o backup; o cache não foi apagado.
O snapshot contém **225 arquivos verificados por SHA-256**, aproximadamente
**689,8 MiB**, com os 211 candidatos confirmados e seus 102 elegíveis,
configuração, fonte e nove checkpoints de compare. As páginas parciais
permanecem no cache compartilhado; o snapshot não duplica todo esse cache.

### Consequência metodológica

O primeiro marco de 300 passa a favorecer candidatos com menor custo de
coleta observado, portanto deve ser reportado como coleta priorizada por
custo, e não como seleção estritamente por estrelas. Retomar os grandes após
esse marco reduz essa preferência na amostra de 500, sem garantir ausência
de viés. O artigo final deve informar a política, a ordem efetiva, os adiados
e o tamanho realmente concluído. Não apresentamos 300 ou 500 como já atingidos.

Rastreabilidade: fonte original, fonte com política, hashes de ambos, manifesto
do snapshot e manifesto de migração ficam na pasta local da coleta. A justificativa
é versionada neste documento; nenhum token, cache ou dataset bruto é publicado.
