# Instância auxiliar de candidatos e commits (#151)

`pipeline.auxiliar_compare` prioriza a coleta dos próximos candidatos (filtros,
releases e runs) e deixa os commits entre releases em segundo plano. Usa os
coletores e contratos de checkpoints do `pipeline.integrado` existente, sem
reiniciar a principal. A principal consome os candidatos preparados na ordem
original; somente ela atualiza o contador de seleção. Candidatos prontos na
auxiliar ainda não significam inclusão na amostra final.

Com a [política de adiamento até 300 elegíveis](decisoes-coleta-final.md), a
auxiliar segue a fila dinâmica e os `ids_avaliados` publicados pela principal.
Não antecipa candidatos bloqueados pela política; depois da liberação,
respeita também a prioridade dos grandes nas vagas da principal.

## Execução

Use um checkout compatível com a versão da principal e seu Python com as
dependências do Lab03. Na pasta `Lab03`, com `GITHUB_TOKEN` no ambiente:

```powershell
python -m pipeline.auxiliar_compare `
  --config 'C:\caminho\Lab03\data\raw\amostra-final-500\config.yaml' `
  --candidatos 'C:\caminho\Lab03\data\raw\candidatos.json' `
  --reutilizar-runs 'C:\caminho\Lab03\data\raw\piloto-100\workflow_runs.json'
```

A configuração deve usar caminhos absolutos quando a auxiliar estiver em
outro checkout. Fonte, janela, critérios, API e versão do coletor devem
corresponder ao contexto em `progresso.json`; divergências impedem o trabalho.
O token não é recebido em argumento nem persistido. Um launcher local pode
recuperar a credencial existente do Git e mantê-la somente na memória.
`--reutilizar-runs` é opcional; quando a principal reutiliza um piloto, informe
o mesmo arquivo para conservar seus meses completos. A auxiliar mantém em
memória somente os registros do piloto relativos a candidatos ainda futuros.

## Coordenação e prioridades

- Lê progresso, heartbeat e o mesmo snapshot de candidatos. Trabalha na ordem
  da fonte, a partir de `candidatos_avaliados + repositorios_paralelos + 6`
  (índice começando em zero), fora dos candidatos que a principal pode ter em
  voo. Examina no máximo 32 posições adiante e respeita `max_candidatos`.
- Usa o coletor original para aprovar ou descartar cada candidato pelos mesmos
  critérios. Grava o checkpoint com os runs completos; o resumo em memória
  não serve como entrada para os cálculos finais.
- Reconfere a margem antes de cada tentativa de rede e antes da publicação.
  Se a principal se aproximar, cede aquele candidato e conserva páginas e
  resultados privados já concluídos. Como a principal não participa de um
  lock de tarefas, não há garantia de eliminar toda chamada simultânea nas
  transições; a margem reduz a disputa, e checkpoints existentes não são sobrescritos.
- Limita a 30 requisições reais de coleta por candidato em cada rodada. Ao
  atingir esse orçamento, passa ao próximo, mantendo o cache. Depois de
  visitar os demais pendentes da faixa, retoma os grandes pelas páginas salvas.
- Se a faixa futura já estiver preparada ou tiver acabado, antecipa compares
  de repositórios já confirmados como elegíveis pela principal, priorizando
  aqueles com menos releases. Isso não muda a seleção nem a população final.
- Compartilha o cache GET. A auxiliar usa uma requisição por vez, com intervalo
  mínimo de seis segundos entre tentativas de coleta, inclusive retries.
  Consultas de cota são separadas, com atualização no máximo a cada 30 segundos
  durante uma janela; após reset a cota é consultada novamente.
- Usa o orçamento restante informado pelo GitHub e reserva o maior entre
  2.000 requisições e `ceil(0,9 × limite × segundos_restantes/3600) + 250`,
  limitando o tempo restante a 3.600 segundos. Essa reserva favorece a
  principal; não cria cota adicional. Headers de respostas atualizam a cota.
  A coordenação de orçamento é conservadora, não um limitador global atômico:
  a principal não foi modificada e também pode consumir a cota entre consultas.
- Quando falta orçamento, pausa em vez de disputar a reserva. `Retry-After`,
  limite secundário e esgotamento de cota geram cooldown antes de nova consulta.
- Salva primeiro um resultado completo em sua pasta privada e publica um
  checkpoint novo de candidato ou compare por criação atômica, sem substituir
  um existente. O integrado atual reaproveita candidatos antes de consultar
  a API; os compares são lidos na etapa correspondente.
- Não altera `config.yaml`, `processo.json`, `progresso.json`, consolidados,
  critérios ou código carregado pela principal. Apenas acrescenta respostas
  ao cache e novos checkpoints compatíveis.
- Ao atingir o alvo de seleção, a auxiliar encerra para deixar a etapa de
  compare com a principal. Se perceber essa transição durante uma coleta,
  conserva os resultados locais/cache sem publicar um novo checkpoint.

## Estado, retomada e parada

Por padrão, a pasta privada é `<raw>/auxiliar-compare/`:

| Arquivo | Função |
|---|---|
| `estado.json` | PID, heartbeat, tarefa atual, posição, cota, candidatos antecipados/aprovados/descartados e contadores de compares desta sessão. |
| `auxiliar.log` | Comparações concluídas e falhas temporárias. |
| `prontos/<hash>/<id>.json` | Resultados completos antes da publicação. |
| `candidatos/<contexto>/<id>.json` | Checkpoints completos de candidatos, antes de compartilhar com a principal. |
| `auxiliar.lock` | Lock exclusivo do sistema operacional; impede duplicar a auxiliar. |

Falhas de rede/5xx aguardam 60 segundos e retomam pelas páginas em cache.
Falhas permanentes de autenticação/configuração encerram somente a auxiliar.
Se a principal parar ou seu heartbeat ficar mais de 120 segundos sem atualização,
a auxiliar pausa; retoma quando o estado voltar a permitir. Com menos de
10 GiB livres em disco, também pausa.

Para encerrar **somente a auxiliar**, crie um arquivo vazio em
`<raw>/auxiliar-compare/parar`. O comando não encerra a principal. A verificação
ocorre entre chamadas e antes da publicação, podendo aguardar o timeout ou
backoff da requisição em andamento. Para iniciar novamente, remova esse marcador;
os checkpoints e páginas já concluídos são reaproveitados. Os contadores de
`estado.json` são da sessão atual, não o total histórico da amostra.

O ganho depende da folga de cota e da quantidade de comparações. Não há promessa
de dobrar a velocidade: ambas as instâncias compartilham o orçamento da conta.
Resultados inacessíveis/incompletos mantêm os diagnósticos normais do compare.
Os checkpoints de seleção antecipados só são contabilizados quando a principal
chegar até eles. Um candidato antecipado pode ficar fora da amostra se o alvo
for alcançado antes; não se salta nenhum candidato da ordem original para
aproveitar resultados prontos.
