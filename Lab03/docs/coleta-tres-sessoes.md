# Retomada até 500 com três sessões

A coleta usa três clientes autenticados, cada um com `GITHUB_TOKEN_1`,
`GITHUB_TOKEN_2` ou `GITHUB_TOKEN_3` do arquivo local `Lab03/.env`.
O módulo `pipeline.coleta_paralela` carrega esse arquivo sem executar seu conteúdo.
O arquivo é ignorado pelo Git. Os demais comandos continuam usando `GITHUB_TOKEN`.

Um coordenador distribui candidatos únicos entre as três sessões e consolida
os resultados. Uma tarefa demorada não bloqueia o preenchimento das outras vagas.
A fila diminui ao se aproximar de 500 elegíveis para não ultrapassar a meta.
Depois da seleção, as três sessões coletam os compares e o pipeline calcula
e audita as métricas. Os arquivos consolidados têm um único escritor.

## Dados reaproveitados e ordem

O prefixo confirmado da coleta anterior é preservado, incluindo os 255 elegíveis
publicados. Os pendentes seguem a ordem da busca original `data/raw/candidatos.json`,
sem adiamento dos grandes e sem prioridade por menor volume de runs. Essa decisão
substitui a política de liberar projetos pesados somente após 300 elegíveis.
Os critérios do estudo permanecem: pelo menos 1.000 estrelas na busca existente,
5 releases estáveis e 50 runs válidos na janela definida na configuração.

A preparação gera `candidatos-sem-prioridade-tamanho.json` e copia atomicamente
os checkpoints compatíveis para o contexto da nova fonte. Confere janela,
inclusão, runs, versão do coletor, API e identidade integral de cada candidato.
As fontes antigas, checkpoints originais e entrega de 255 permanecem preservados.
O manifesto e o progresso anterior ficam em `data/raw/amostra-final-500/retomada-tres-sessoes/`.
O cache HTTP e os checkpoints de compare existentes são reaproveitados.

O avanço das novas tarefas é consolidado na ordem de conclusão e registrado
em `ids_avaliados`. Isso deve ser declarado na metodologia junto da preferência
por custo utilizada no prefixo histórico. A nova execução não torna a amostra
inteira estritamente ordenada por estrelas.

## Execução no Windows

Na raiz do repositório, abra um PowerShell visível e execute:

```powershell
.\Lab03\iniciar-coleta-500.ps1
```

Ou, a partir de `Lab03`, use diretamente:

```powershell
.\.venv\Scripts\python.exe -u -m pipeline.coleta_paralela
```

Para preparar e migrar sem acessar a API, acrescente `--preparar` ao comando Python.
Uma trava compatível com o coletor antigo impede dois coordenadores na mesma pasta.

O terminal mostra tarefas por sessão e status a cada 15 segundos, com contagem,
etapa e estado. Os mesmos dados ficam em
`data/raw/amostra-final-500/processo-tres-sessoes.json`; o histórico fica em
`coleta-tres-sessoes.log`. As saídas finais ficam em
`data/processed/amostra-final-500/`, incluindo `execucao.json` e auditorias.
Somente o término com código 0 confirma que a meta foi atingida e o processamento
terminou. O código 3 indica fonte esgotada antes da meta; o código 2 indica erro
ou interrupção.

Falhas de conexão, transferências interrompidas, timeouts, respostas 403 com
indicação explícita de cota esgotada e respostas temporárias 429/500/502/503/504 retomam
automaticamente, com espera progressiva de até 60 segundos. Cada tentativa relê
checkpoints e cache; não apaga resultados anteriores. O cliente também respeita
os limites informados pela API. Falhas de autenticação e configuração encerram
a execução para correção. Tokens da mesma conta compartilham o controle de cota;
criar três tokens na mesma conta não multiplica o limite de requisições.

Ctrl+C encerra a execução; tarefas em andamento terminam antes de o processo sair.
O mesmo comando retoma a coleta. Tokens não são passados na linha de comando nem
gravados nos arquivos de status ou log.
