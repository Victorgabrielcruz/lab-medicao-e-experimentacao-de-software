# Instância auxiliar de comparação de commits (#151)

`pipeline.auxiliar_compare` antecipa commits entre releases de repositórios
que o processo principal já confirmou como elegíveis. Ele usa o mesmo contrato
de checkpoints de `pipeline.integrado` e não requer reiniciar a principal.
O contador de seleção continua sendo atualizado somente pela principal; a
auxiliar reduz trabalho futuro de compare e lead time, sem alterar a amostra.

## Execução

Use um checkout compatível com a versão da principal e seu Python com as
dependências do Lab03. Na pasta `Lab03`, com `GITHUB_TOKEN` no ambiente:

```powershell
python -m pipeline.auxiliar_compare `
  --config 'C:\caminho\Lab03\data\raw\amostra-final-500\config.yaml' `
  --candidatos 'C:\caminho\Lab03\data\raw\candidatos.json'
```

A configuração deve usar caminhos absolutos quando a auxiliar estiver em
outro checkout. Fonte, janela, critérios, API e versão do coletor devem
corresponder ao contexto em `progresso.json`; divergências impedem o trabalho.
O token não é recebido em argumento nem persistido. Um launcher local pode
recuperar a credencial existente do Git e mantê-la somente na memória.

## Coordenação e prioridades

- Lê o progresso, heartbeat e checkpoints da seleção; só considera candidatos
  já consumidos pelo coordenador em sua ordem, com `elegivel=true`.
- Processa um repositório de cada vez, priorizando os que têm menos releases,
  sem mudar a ordem de seleção nem a população da principal.
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
  checkpoint novo de compare por criação atômica, sem substituir um existente.
  O integrado atual reaproveita esse checkpoint na etapa de compare.
- Não altera `config.yaml`, `processo.json`, `progresso.json`, consolidados,
  critérios ou código carregado pela principal. Apenas acrescenta respostas
  ao cache e novos checkpoints de compare compatíveis.
- Ao atingir o alvo de seleção, a auxiliar encerra para deixar a etapa de
  compare com a principal. Se perceber essa transição durante uma coleta,
  conserva os resultados locais/cache sem publicar um novo checkpoint.

## Estado, retomada e parada

Por padrão, a pasta privada é `<raw>/auxiliar-compare/`:

| Arquivo | Função |
|---|---|
| `estado.json` | PID, heartbeat, estado, repositório atual, orçamento reservado e contadores desta sessão. |
| `auxiliar.log` | Comparações concluídas e falhas temporárias. |
| `prontos/<hash>/<id>.json` | Resultados completos antes da publicação. |
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
