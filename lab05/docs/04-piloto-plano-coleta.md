# Coleta piloto e plano de coleta — S01-06 (#304)

## Objetivo e resultado da validação

O piloto valida a execução do benchmark e estima a variabilidade e o custo da coleta
completa, sem responder às hipóteses H1–H3. Foram realizadas **3 repetições medidas e
1 aquecimento por combinação**, mantendo os tamanhos reais das cargas: 12 combinações,
48 execuções no total e **36 linhas medidas** no CSV. A execução terminou com código 0.

O benchmark executado é o commit `663d51964cbfe221525d059a616ac64eaaa868f1`, incorporado
à `main` pelo PR #320. Nenhum parâmetro do `config.py` foi alterado para produzir o piloto.

Comando executado a partir de `lab05/`, usando o Python 3.12.14 do ambiente local:

```powershell
data/.venv-benchmark/Scripts/python.exe executar.py --diretorio data/piloto --repeticoes 3 --aquecimentos 1 --semente 42
```

O caminho do executável é específico desta máquina. Em outro ambiente Python 3.12,
o equivalente é `python executar.py` com os mesmos argumentos. Para repetir o piloto,
use outro diretório, por exemplo `--diretorio data/piloto-repeticao-01`, pois o coletor
recusa sobrescrever dados existentes.

## Ambiente e condições observadas

| Item | Registro |
|---|---|
| Data e horário local | 19/11/2026, 12:18:49–12:19:46 (America/Sao_Paulo, UTC−3) |
| Sistema | Windows, versão registrada `10.0.26200`, AMD64 |
| Python / SQLite | CPython 3.12.14 / SQLite 3.53.1 |
| CPU | AMD Ryzen 5 8500G, 6 núcleos físicos e 12 processadores lógicos |
| Memória física disponível ao SO | 16.221.278.208 bytes (aproximadamente 15,1 GiB) |
| Disco | WD Green SN350 500GB 2G0C, SSD NVMe |
| Sistema de arquivos / unidade | NTFS / C: |
| Espaço livre registrado | 165,3 GiB |
| Plano de energia observado | Equilibrado, sem alteração durante o piloto pelo agente |

CPU, memória, disco e plano de energia foram consultados antes da execução. A consulta
de bateria não retornou dispositivos; o estado de alimentação externa não foi
instrumentado. Não houve encerramento de aplicativos, isolamento do SO nem limpeza do
cache. Nenhum outro benchmark ou teste foi iniciado pelo agente durante a coleta.
Processos já abertos, antivírus, indexação e variações térmicas continuam como fontes
possíveis de ruído; sua contribuição não foi medida.

## Artefatos e verificações

Os arquivos estão em [`../data/piloto/`](../data/piloto/):

- `resultados.csv`: as 36 medições brutas, preservadas sem exclusão de observações;
- `ambiente.json`: ambiente e parâmetros efetivos do benchmark;
- `execucao.json`: comando, commit, horários, duração de parede, código de saída e
  condições complementares da máquina;
- `resumo.csv` e `resumo.json`: estatísticas por grupo, estimativa de duração e hashes
  SHA-256 dos três arquivos de entrada.

O resumo é reproduzido com:

```powershell
python resumir_piloto.py --diretorio data/piloto
```

Essa verificação confirmou as 12 combinações com repetições 1, 2 e 3, sem duplicatas
ou ausências; ordem medida de 13 a 48, sem aquecimentos no CSV; tempos e vazões
positivos e finitos; contagens das cargas; cálculo `vazão = operações / tempo`;
e correspondência dos campos de ambiente entre CSV e JSON. Os diretórios dos bancos
temporários foram removidos ao fim das execuções.

A aplicação efetiva dos PRAGMAs, um commit por escrita, a equivalência das sequências
entre configurações e o banco novo por execução também são cobertos pelos testes do
benchmark. A validação completa dos dados finais e seu dicionário permanecem na #307.

## Variabilidade observada

Mediana e IQR resumem os tempos. O desvio-padrão é amostral (denominador `n−1`),
e o coeficiente de variação é `100 × desvio-padrão / média`. Quartis usam interpolação
inclusiva (`statistics.quantiles(method="inclusive")`). Há apenas **3 observações por
grupo**, portanto estes números são diagnósticos preliminares.

| Configuração | Carga | Mediana M1 (s) | IQR M1 (s) | CV de M1 (%) |
|---|---|---:|---:|---:|
| DELETE-FULL | escrita | 2,754180 | 0,407291 | 15,13 |
| DELETE-FULL | leitura | 1,259757 | 0,136476 | 11,58 |
| DELETE-FULL | mista | 2,136508 | 0,329273 | 15,23 |
| DELETE-NORMAL | escrita | 2,406407 | 0,657010 | 26,33 |
| DELETE-NORMAL | leitura | 1,308276 | 0,422171 | 30,25 |
| DELETE-NORMAL | mista | 1,809883 | 0,327443 | 17,72 |
| WAL-FULL | escrita | 0,502411 | 0,246849 | 42,84 |
| WAL-FULL | leitura | 0,057757 | 0,001273 | 2,20 |
| WAL-FULL | mista | 0,383357 | 0,106060 | 27,36 |
| WAL-NORMAL | escrita | 0,039622 | 0,022021 | 49,46 |
| WAL-NORMAL | leitura | 0,058323 | 0,000691 | 1,18 |
| WAL-NORMAL | mista | 0,024823 | 0,004254 | 16,85 |

Os valores exatos estão no resumo; a tabela apresenta arredondamentos. O CV variou de
1,18% a 49,46%, com maior instabilidade em alguns grupos de escrita. Não foi aplicada
regra de remoção de outliers nem realizado teste de hipótese neste piloto. Três pontos
não permitem caracterizar bem a distribuição nem garantir poder para diferenças de 2%.

As diferenças de nível entre modos, inclusive na leitura, merecem acompanhamento na
coleta completa e discussão do custo de bloqueios/transações do benchmark. Elas não
foram usadas para mudar a carga ou selecionar comparações depois de observar os dados.

## Tempo estimado e decisão sobre repetições

A duração de parede do processo foi **57,830424 s**, incluindo preparação dos bancos,
aquecimentos, medições, CSV e limpeza. A soma de M1 das 36 medições foi 41,580211 s;
ela não representa toda a duração do processo.

O plano completo mantém **30 repetições medidas e 3 aquecimentos por combinação**:

```text
Piloto:   12 × (3 + 1)  = 48 execuções
Completa: 12 × (30 + 3) = 396 execuções
Estimativa: 57,830424 × 396 / 48 = 477,101 s ≈ 7 min 57 s
```

Reservar **16 minutos** (aproximadamente duas vezes a projeção), além da preparação
manual do ambiente. Essa folga é operacional, não um intervalo de confiança. A projeção
supõe custo médio semelhante por execução; o piloto e o plano completo têm proporções
diferentes de aquecimento, e o ruído pode mudar o tempo real.

Manter 30 repetições é viável pelo custo observado e preserva o protocolo previamente
documentado. Isso **não comprova suficiência estatística**: a precisão, os intervalos de
confiança e a escolha justificada dos testes devem ser tratados no plano de análise
(#305). O piloto não será somado às 30 repetições da coleta completa.

## Plano operacional para a coleta completa (#306)

1. Usar inicialmente a mesma máquina, unidade C:/NTFS e versões de Python/SQLite.
   Registrar novamente o ambiente junto aos dados; uma mudança exige documentação.
2. Antes de iniciar, conferir alimentação estável, impedir suspensão durante a janela
   e registrar o plano de energia. Manter o plano escolhido constante durante toda a
   coleta. Se o plano mudar em relação ao piloto, a estimativa de tempo passa a ser
   apenas uma referência e essa diferença precisa constar no registro.
3. Evitar downloads, builds, testes, benchmarks, sincronizações e outras tarefas
   intensivas; aguardar o fim de atualizações e deixar a máquina estabilizar. Fechar
   aplicativos desnecessários com controle do usuário. Manter as proteções do sistema
   ativas e registrar interferências conhecidas.
4. Executar sequencialmente, em um diretório novo, sem rodar a análise ao mesmo tempo:

   ```powershell
   python executar.py --diretorio data/coleta-completa-01 --repeticoes 30 --aquecimentos 3 --semente 42
   ```

5. Preservar banco novo, 10.000 linhas iniciais, payload de 256 bytes, cargas, um
   commit por escrita e aleatorização do benchmark. Não limpar o cache entre grupos
   nem acrescentar concorrência, para manter o método documentado.
6. Conferir código de saída, as 360 medições e a completude em #307 antes de analisar.
   Registrar interrupções e interferências. Em caso de falha, preservar a saída parcial
   e recomeçar em outro diretório; não completar manualmente linhas nem selecionar
   somente execuções favoráveis. Não remover observações apenas por serem lentas.
7. A coleta inicial será em uma máquina. A replicação nos outros dois integrantes é
   uma extensão futura, ainda não executada; seus dados devem ser identificados e
   analisados por ambiente, sem misturar silenciosamente as amostras.

## Ética e limites

A carga usa somente dados sintéticos locais. Não acessa sistemas de terceiros nem
coleta dados pessoais da aplicação. Os metadados técnicos incluem caminhos locais do
executável e do banco para rastreabilidade. Não há tráfego de benchmark para serviços
externos, teste de queda de energia, alteração de credenciais, desativação de proteções
ou acesso a bancos de produção. O custo de durabilidade continua baseado nas fontes
documentais; este piloto mede desempenho.
