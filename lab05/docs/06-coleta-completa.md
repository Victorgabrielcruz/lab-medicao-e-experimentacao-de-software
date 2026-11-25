# Coleta completa — S02-01 (#306)

## Execução realizada

A coleta completa foi executada em **25/11/2026**, das **16:42:57 às 16:48:27**
(America/Sao_Paulo, UTC−3), após atualizar a `main` para
`fbf677aa87689cec30949c90bee1de2be819ff1e` e criar a branch `feat/coleta-completa-306`.

O plano da [coleta piloto](04-piloto-plano-coleta.md) foi preservado:

- quatro configurações: DELETE-FULL, DELETE-NORMAL, WAL-FULL e WAL-NORMAL;
- três cargas: escrita, leitura e mista, com os tamanhos do `config.py`;
- **30 repetições medidas e 3 aquecimentos por combinação**;
- **396 execuções: 36 aquecimentos descartados e 360 medições**;
- semente 42, ordem aleatorizada por rodada e sequência equivalente de operações
  entre configurações para cada carga/repetição;
- banco novo por execução, 10.000 linhas iniciais, payload ASCII de 256 bytes e
  um commit por escrita; sem concorrência ou limpeza do cache do SO.

Comando do coletor, a partir de `lab05/`, usando o mesmo Python do piloto:

```powershell
data/.venv-benchmark/Scripts/python.exe executar.py --diretorio data/coleta-completa-01 --repeticoes 30 --aquecimentos 3 --semente 42 --progresso
```

O caminho do ambiente virtual é local. Para reproduzir em Python 3.12, use seu
executável e um **diretório novo**: a coleta existente não deve ser sobrescrita.

O único acréscimo ao coletor foi `--progresso`: uma linha após cada execução,
fora do cronômetro, depois de fechar/remover o banco e, nas medições, gravar o CSV.
Isso não altera as cargas, o sorteio ou os limites da janela cronometrada. A emissão
de progresso e o monitoramento leve dos arquivos continuam sendo atividade de SO;
o ambiente não é isolado. Os hashes dos fontes efetivamente usados estão no registro.

## Ambiente e condições

| Item | Registro desta coleta |
|---|---|
| Python / SQLite | CPython 3.12.14 / SQLite 3.53.1, iguais ao piloto |
| Sistema | Windows, versão `10.0.26200`, AMD64 |
| CPU | AMD Ryzen 5 8500G, 6 núcleos e 12 processadores lógicos |
| Memória física | 16.221.278.208 bytes (aproximadamente 15,1 GiB) |
| Disco | WD Green SN350 500GB 2G0C, SSD NVMe |
| Unidade / sistema de arquivos | C: / NTFS |
| Espaço livre registrado | 169,3 GiB |
| Plano de energia | Equilibrado, sem mudança em relação ao piloto |
| Suspensão | Impedida temporariamente por `SetThreadExecutionState` durante o processo; pedido liberado ao encerrar |

Hardware, versões e plano de energia foram conferidos antes de iniciar. A alimentação
externa não foi instrumentada. Aplicativos existentes não foram encerrados, as
proteções continuaram ativas e não houve isolamento do SO. Não foram iniciados testes,
análises ou outros benchmarks pelo agente durante a coleta; houve somente monitoramento
leve do estado e da contagem de linhas. Não se afirma ausência de ruído de terceiros.

Foi solicitado um terminal de desktop com progresso. A abertura via controle do
computador foi bloqueada pela política do produto; o acompanhamento ocorreu no
terminal integrado, que exibiu a evolução até **396/396 e 360/360**. A execução não foi
reiniciada por esse motivo. O processo PowerShell foi iniciado com `-NoExit` e pode
permanecer ativo, mas não foi possível confirmar uma janela visível no desktop.

## Encerramento e conferência operacional

- Código de saída **0**, estado `concluida`.
- Duração de parede: **329,747719 s (aproximadamente 5 min 30 s)**, incluindo
  preparação, aquecimentos, medições e limpeza. O piloto projetava cerca de 7 min 57 s
  e reservava 16 minutos; a diferença de tempo não foi usada para selecionar dados.
- **360 linhas**, com exatamente **30 repetições em cada um dos 12 grupos**.
- Ordem medida de **37 a 396**, idêntica ao plano com semente 42; aquecimentos ausentes
  do CSV. Também foram conferidas as sementes das cargas e as combinações por rodada.
- **1.560.000 operações medidas**: 1.368.000 leituras e 192.000 escritas, conforme as
  contagens de cada carga. As operações individuais não são réplicas estatísticas.
- Tempos/vazões positivos e finitos; conferência de `vazão = operações / tempo` e dos
  campos de ambiente do CSV contra o JSON.
- Hashes dos fontes e do lançador conferidos; nenhum banco temporário remanescente.
- Nenhuma observação excluída, nenhum preenchimento manual e nenhum dado do piloto
  incorporado à coleta completa.

Essa é uma **conferência operacional da #306**. A validação formal, o dicionário de
dados e o diagnóstico de outliers/deriva temporal permanecem na #307. Não foram
realizados testes de hipótese ou conclusões de superioridade nesta entrega.

## Artefatos preservados

Em [`../data/coleta-completa-01/`](../data/coleta-completa-01/):

| Arquivo | Conteúdo |
|---|---|
| `resultados.csv` | 360 medições brutas, sem aquecimentos |
| `ambiente.json` | Ambiente e parâmetros efetivos do coletor |
| `execucao.json` | Comando, horários, duração total, código de saída, base Git, hashes dos fontes e condições observadas |
| `conferencia.json` | Contagens, verificações operacionais e hashes SHA-256 dos artefatos |
| `lancador.py` | Cópia exata do lançador usado para registrar a execução e impedir suspensão temporariamente |

O lançador foi executado originalmente em `data/.execucao306/rodar.py`; o arquivo
preservado é sua cópia byte a byte. Os hashes dos fontes em `execucao.json` se referem
aos arquivos físicos usados na máquina (incluindo fins de linha), não necessariamente
aos blobs normalizados do Git. As regras de atributos preservam os bytes dos artefatos.

As regras de ética continuam as do plano: dados sintéticos, execução local, sem acesso
a serviços de terceiros ou bancos de produção e sem teste de falha de energia.
Os metadados incluem caminhos técnicos locais para rastreabilidade.
