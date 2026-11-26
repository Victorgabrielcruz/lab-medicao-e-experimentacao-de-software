# Ameaças à validade — S02-05 (#310)

Este texto discute as ameaças nos quatro tipos de validade, com base no que foi
**efetivamente executado**: a [coleta completa](06-coleta-completa.md), a
[validação](07-validacao-dicionario-dados.md), a [descritiva](08-descritiva-graficos.md)
e os [testes e efeitos](09-testes-efeitos.md). Cada ameaça indica a evidência, a
mitigação aplicada ou a limitação assumida e o que ela muda na conclusão.

Os números citados vêm da coleta completa (360 medições, CSV SHA-256
`595eba4d…eacc`). Três verificações locais **exploratórias** foram feitas para
testar ameaças específicas. Elas estão fora do protocolo e do conjunto de dados,
foram rodadas em outra máquina Windows, com Python 3.13.6 e SQLite 3.50.4, poucas
repetições (5 a 7) e sem registro formal de ambiente. Servem só para indicar a
direção e a ordem de grandeza de cada ameaça. Não entram em testes, IC ou no
dashboard.

## Resumo

| # | Validade | Ameaça | Tratamento | Efeito na conclusão |
|---|---|---|---|---|
| C1 | Conclusão | Independência entre rodadas não comprovada | Auditoria de sequências com Holm; resultados condicionais | Inferência condicional; replicação necessária |
| C2 | Conclusão | Teste dos sinais satura em 30/0 | M3 com IC bootstrap para a magnitude | O valor-p não ordena efeitos |
| C3 | Conclusão | Poder baixo para efeitos pequenos na leitura | Equivalência não declarada | H2 e H3 na leitura ficam inconclusivos |
| C4 | Conclusão | Interação forte torna a decomposição dependente do caminho | Mostrar os dois caminhos | "De onde vem o ganho" não tem resposta única |
| C5 | Conclusão | Regras de análise definidas em momentos diferentes | Registro de quando cada regra foi fixada | Auditoria temporal é *post hoc* |
| I1 | Interna | Antivírus e criação do arquivo de journal confundem o fator `journal_mode` | Limitação assumida; verificação exploratória | H1 na escrita pode estar inflado, mas não se inverte |
| I2 | Interna | Ruído do SO, cache, deriva e monitoramento | Ordem aleatória por rodada, banco novo, pareamento | Distribuído, não eliminado |
| I3 | Interna | Janelas curtas são mais sensíveis a interrupções | Mediana, IQR e outliers preservados | Mais dispersão nas configurações WAL |
| K1 | Construto | A carga "leitura" mede o custo de transação, não de leitura | Limitação assumida; verificação exploratória | **Q4 não é respondida por esta carga** |
| K2 | Construto | Um commit por `INSERT` é o pior caso de sincronização | Carga explicitada no protocolo | Razões são um limite superior para cargas em lote |
| K3 | Construto | O checkpoint ao fechar fica fora da janela | Limitação documentada; verificação exploratória | Favorece levemente o WAL-NORMAL |
| K4 | Construto | Durabilidade não é medida | Garantias tiradas da documentação | O custo do trade-off é qualitativo |
| K5 | Construto | Uma conexão só: não mede concorrência | Limitação assumida | Subestima o principal benefício do WAL |
| E1 | Externa | Uma máquina, um disco e um SO | Ambiente registrado; replicação planejada | Magnitude não generaliza; direção talvez |
| E2 | Externa | Semântica de sincronização varia por plataforma | Limitação assumida | `FULL` não custa o mesmo em todo lugar |
| E3 | Externa | Uma versão do SQLite, via `sqlite3` do Python | Versões registradas | Outras bindings mudam a carga de leitura |
| E4 | Externa | Banco pequeno e carga sintética | Limitação assumida | Não extrapolar para bancos grandes ou produção |

## Validade de conclusão

**C1 — Independência entre rodadas.** O teste binomial dos sinais e o bootstrap
pareado supõem rodadas independentes. A coleta completa durou cerca de 5 min 30 s
em uma única sessão, e algumas séries de diferenças pareadas têm tendência visível:
Spearman de aproximadamente 0,394 em H1 na leitura e −0,332 em H2 na escrita. A
auditoria por sequências (*runs*), com Holm sobre 18 diagnósticos, não gerou
alerta. Porém **sete dos nove diagnósticos de sinais são inconclusivos**, porque
os 30 sinais têm o mesmo sentido, e o teste tem pouco poder com n = 30.
*Mitigação aplicada:* aleatorização das 12 combinações em cada rodada, pareamento
por rodada e semente de carga, auditoria explícita e regra de suspensão. *Limitação
assumida:* valores-p e IC continuam **condicionais à independência**. Ausência de
alerta não prova independência. Só uma nova coleta, em outro momento ou máquina,
reduz essa ameaça.

**C2 — Saturação do teste dos sinais.** Com 30 ganhos em 30 pares, o p bruto é
2 × 0,5³⁰ ≈ 1,86 × 10⁻⁹, o menor valor possível com n = 30. Sete comparações caem
exatamente nesse piso, de H3 na escrita (M3 ≈ 1,26) a H2 na escrita (M3 ≈ 12,0).
Um ganho de 26% e outro de 1.100% recebem o mesmo valor-p. *Mitigação aplicada:*
a magnitude é lida em M3 e no seu IC bootstrap, não no valor-p. *Consequência:*
não se ordenam efeitos por significância, e "p muito pequeno" não significa
"efeito grande".

**C3 — Poder para efeitos pequenos (leitura).** H2 e H3 na leitura não rejeitam
H0, mas os IC de M3 são [0,972; 1,061] e [0,954; 1,044], **mais largos que a faixa
de ±2%** que a documentação usa como referência. *Limitação assumida:* nenhuma
equivalência é declarada. O estudo não sabe dizer se `synchronous` afeta a leitura
em menos de 2%. Para isso seriam necessárias mais rodadas ou um teste de
equivalência planejado antes da coleta.

**C4 — Interação e dependência do caminho.** O ganho do `NORMAL` depende do modo de
journal: na escrita, ele vale 1,26× sob `DELETE` (H3) e 12,0× sob `WAL` (H2). Com
uma interação desse tamanho, a parcela atribuída a cada fator **depende da ordem em
que os passos são somados**. Na escrita, o ganho total de DELETE-FULL até WAL-NORMAL
é de cerca de 59,8× (razão das medianas de M2: 23.068 ÷ 386).

| Caminho | 1º passo | 2º passo |
|---|---|---|
| Primeiro o WAL (H1, depois H2) | WAL: 4,97× | NORMAL: 12,0× |
| Primeiro o NORMAL (H3, depois o WAL) | NORMAL: 1,26× | WAL: 47,5× (23.068 ÷ 485) |

As hipóteses foram desenhadas pelo primeiro caminho, por ser o "passo sem custo de
garantia" seguido do "passo que custa durabilidade". *Mitigação aplicada:* a
interação é mostrada pelo gráfico de medianas e pela razão de razões exploratória,
e as duas leituras são apresentadas. *Limitação assumida:* não há teste formal de
interação. A pergunta "de onde vem o ganho" só tem resposta **relativa ao caminho
escolhido**, e não como uma divisão única entre os fatores.

Um ponto a favor da validade: a **expectativa prévia registrada na S01 foi
contrariada**. Esperava-se que H1 concentrasse o ganho, mas na escrita e na mista
o passo do `NORMAL` sob WAL é maior. Um resultado contrário à expectativa dos
autores reduz a suspeita de viés de confirmação na análise.

**C5 — Momento em que cada regra foi fixada.** As hipóteses, as nove comparações,
α e Holm foram definidos na S01 (#301), antes de qualquer dado. O teste dos sinais
e o bootstrap foram escolhidos na #305, depois do piloto e antes da coleta completa.
A regra de auditoria temporal foi operacionalizada na #309, **depois** da coleta.
*Mitigação aplicada:* isso está declarado na #309, e a regra só pode suspender
conclusões, nunca criar significância. Nenhuma observação foi removida: as 23
observações sinalizadas continuam em todas as análises.

**Confiabilidade das medidas.** A análise roda sobre o CSV versionado, com hashes
conferidos, e é reprodutível com semente fixa. A versão do Python usada na análise
(3.14.3) difere da usada na coleta (3.12.14), mas a análise não executa o SQLite e
só lê o CSV. Isso não afeta os resultados.

## Validade interna

**I1 — Antivírus e ciclo de vida do arquivo de journal.** No modo `DELETE`, cada
commit cria e apaga o arquivo `-journal`. No WAL, o arquivo `-wal` é reaproveitado.
A coleta rodou com as proteções do Windows ativas, e a criação de arquivos é
justamente o tipo de evento que a varredura em tempo real e o sistema de arquivos
mais encarecem. Isso cria um **fator de confusão ligado ao próprio tratamento**: a
aleatorização não resolve, porque o custo não se distribui entre as configurações,
e o `DELETE` paga por ele em toda escrita.

*Verificação exploratória:* com 500 commits de um `INSERT`, `journal_mode=TRUNCATE`
e `PERSIST`, que mantêm o arquivo de journal em vez de apagá-lo, foram cerca de
**1,4× mais rápidos que `DELETE`**, e o WAL-FULL continuou cerca de **4,2× mais
rápido que o TRUNCATE-FULL**. Logo, o ciclo de vida do arquivo explica uma parte de
H1 na escrita, mas não o efeito todo. A verificação não separa o antivírus do custo
do próprio NTFS. *Limitação assumida:* o M3 de H1 nas cargas com escrita pode estar
inflado por esse custo, mas a direção se mantém. Uma replicação com a pasta dos
bancos excluída da varredura, ou incluindo `TRUNCATE` como nível de controle,
isolaria o efeito.

**I2 — Ruído do SO, cache, deriva e instrumentação.** O SO não foi isolado:
aplicativos abertos, indexação e as proteções continuaram ativos, e o agente
monitorou o estado e a contagem de linhas no mesmo disco durante a coleta. O cache
do SO não foi limpo. O cache de páginas do SQLite já começa populado pela inserção
das 10.000 linhas na mesma conexão.
*Mitigações aplicadas:* as 12 combinações são embaralhadas em cada rodada,
3 aquecimentos por combinação são descartados, cada execução usa um banco novo com
o mesmo estado inicial, a mesma sequência de operações vale para as quatro
configurações e a comparação é pareada por rodada. O cache populado e o custo do
laço Python são iguais em todas as configurações. Por serem custos aditivos
comuns, eles **comprimem** as razões, o que torna M3 conservador. *Limitação
assumida:* o ruído foi distribuído, não eliminado, e a contribuição de cada fonte
não foi medida.

**I3 — Janelas curtas e dispersão.** As configurações WAL produzem janelas de
medição muito curtas: cerca de 43 ms no WAL-NORMAL de escrita, contra 2,6 s no
DELETE-FULL. Uma interrupção do escalonador pesa proporcionalmente mais numa janela
curta. Isso aparece nos dados: das 23 observações sinalizadas como outliers,
**18 são de configurações WAL e nenhuma é do DELETE-FULL**. *Mitigação aplicada:*
mediana e IQR como resumo principal, outliers preservados e teste pareado baseado
em sinais, que não é sensível a extremos. *Limitação assumida:* as medidas das
configurações rápidas têm menos precisão relativa. Cargas maiores aumentariam as
janelas, mas mudariam o protocolo.

## Validade de construto

**K1 — A carga "leitura" mede custo de transação, não velocidade de leitura.** Esta
é a ameaça de maior impacto nas conclusões. O módulo `sqlite3` do Python, com
`isolation_level="DEFERRED"`, só abre transação implícita antes de comandos de
escrita. Cada `SELECT` da carga de leitura é, portanto, **uma transação de leitura
própria (autocommit)**: são 10.000 transações de uma linha. No modo rollback, cada
transação de leitura precisa "obter um lock SHARED", verificar se existe um
*hot journal*, e os dados em cache são "considerados suspeitos e sujeitos a
verificação contra o arquivo do banco antes de serem usados"
([File Locking](https://www.sqlite.org/lockingv3.html)). No WAL, essa verificação
usa o índice em memória compartilhada.

O resultado de H1 na leitura (WAL-FULL **5,40×** mais rápido que DELETE-FULL)
parece contradizer a documentação, que admite o oposto: "WAL might be very slightly
slower (perhaps 1% or 2% slower) than the traditional rollback-journal approach in
applications that do mostly reads and seldom write" ([WAL](https://www.sqlite.org/wal.html)).

*Verificação exploratória:* repetindo a carga de leitura (10.000 `SELECT` por chave)
nas duas formas, temos:

| Forma da carga | DELETE-FULL (ops/s) | WAL-FULL (ops/s) | WAL ÷ DELETE |
|---|---:|---:|---:|
| Uma transação por `SELECT`, como no protocolo | ≈ 7.354 | ≈ 44.520 | ≈ 6,1 |
| Todos os `SELECT` em uma única transação | ≈ 115.795 | ≈ 107.587 | ≈ 0,93 |

Dentro de uma única transação, a vantagem do WAL **desaparece** e ele fica
ligeiramente mais lento, como a documentação diz. O efeito medido em H1 na leitura
é, portanto, **o custo de abrir e fechar 10.000 transações de leitura**, e não o
custo de ler dados.

*Limitação assumida:* o construto "desempenho de leitura" ficou mal operacionalizado
para a Q4. O resultado de H1 na leitura é válido para o que foi de fato medido:
aplicações que fazem leituras curtas e isoladas em autocommit, padrão comum em
código que usa o `sqlite3` do Python sem transação explícita. Ele **não refuta** a
afirmação do fornecedor sobre leituras em transação, e a Q4 não deve ser respondida
com esse número. O protocolo não foi alterado depois dos dados. Uma replicação
deveria incluir a carga de leitura em transação única como outra carga.

**K2 — Um commit por escrita é o pior caso.** Cada `INSERT` tem o próprio commit,
então a carga de escrita mede essencialmente **o custo de sincronização por
transação**. É exatamente onde `journal_mode` e `synchronous` agem, e onde as razões
ficam maiores. Aplicações que agrupam escritas em transações maiores pagam a
sincronização uma vez por lote, e as razões encolhem. *Limitação assumida:* os M3
de escrita e de mista são um **limite superior** do ganho para aplicações que
fazem commits em lote, e valem diretamente só para aplicações com muitas transações
pequenas.

**K3 — Checkpoint fora da janela.** Com `synchronous=NORMAL` no WAL, a documentação
diz que "the checkpoint is the only operation to issue an I/O barrier or sync
operation" ([WAL](https://www.sqlite.org/wal.html)). Os checkpoints automáticos
durante a carga entram no tempo, mas o checkpoint ao fechar a conexão fica fora.
Isso transfere parte do custo do WAL-NORMAL para depois do cronômetro.
*Verificação exploratória:* incluir o `close()` na janela de 1.000 escritas
acrescentou cerca de **+11,6%** ao tempo do WAL-NORMAL e **+0,3%** ao do WAL-FULL.
*Limitação assumida:* o M3 de H2 está levemente superestimado, mas a diferença é
pequena diante de uma razão de 12×. A direção não muda.

**K4 — Durabilidade não medida.** O estudo mede só velocidade, que é o lado fácil
do trade-off (falácia de McNamara, já apontada na S01). As garantias de cada
configuração vêm da documentação: com WAL e `NORMAL`, as transações "are no longer
durable and might rollback following a power failure or hard reset"
([WAL](https://www.sqlite.org/wal.html)). Não houve ensaio de queda de energia, e
isso é um **viés de método único** no lado do custo. *Limitação assumida:* o custo
de durabilidade é apresentado de forma qualitativa, ao lado de M3, e não como
número. O estudo não estima a probabilidade ou o volume de perda de dados.

**K5 — Uma conexão por vez.** A principal vantagem do WAL na documentação é permitir
leitores concorrentes com um escritor. A execução sequencial com uma conexão não
exercita isso: é um **viés de operação única**. *Limitação assumida:* o estudo
provavelmente **subestima** o benefício do WAL em aplicações concorrentes e não diz
nada sobre bloqueios (`SQLITE_BUSY`).

## Validade externa

**E1 — Uma máquina, um disco, um SO.** Toda a coleta foi feita em um único ambiente:
Windows 10.0.26200, NTFS, AMD Ryzen 5 8500G e SSD NVMe de consumo
(WD Green SN350). O custo de um `FlushFileBuffers` depende do disco, do controlador
e do driver, e as razões de H1 e H2 são, no fundo, razões entre quantidades de
sincronização. *Mitigação aplicada:* o ambiente completo está registrado em cada
linha e em `ambiente.json`. *Limitação assumida:* a replicação nas máquinas dos três
integrantes foi proposta (#302, #304), mas não foi executada.

As verificações exploratórias, em outra máquina, dão uma indicação: a vazão
absoluta de escrita foi cerca de **5× menor** (DELETE-FULL ≈ 75 contra 386 ops/s),
mas a direção dos efeitos se manteve (WAL-FULL ÷ DELETE-FULL ≈ 6; WAL-NORMAL ÷
WAL-FULL ≈ 17). Isso sugere que **valores absolutos não generalizam**, mas a direção
e a ordem de grandeza das razões talvez sim. Não é uma replicação: o protocolo, o
ambiente e o número de repetições são diferentes.

**E2 — A sincronização não significa o mesmo em toda plataforma.** No Windows,
`FULL` chama `FlushFileBuffers`. Em Linux, chama `fsync()`, cujo custo depende do
sistema de arquivos. No macOS, `PRAGMA fullfsync` vem desligado por padrão e só o
macOS oferece `F_FULLFSYNC` ([PRAGMA](https://www.sqlite.org/pragma.html#pragma_fullfsync)).
Por isso o `FULL` padrão de lá não força a gravação no meio físico do mesmo modo, e
o "custo do FULL" pode ser bem menor, com uma garantia também menor. *Limitação
assumida:* as razões de H2 e H3 não devem ser transportadas para outras plataformas
sem nova medição.

**E3 — Uma versão e uma binding.** O estudo usou SQLite 3.53.1 pelo módulo `sqlite3`
do CPython 3.12.14. Outra versão pode mudar o custo relativo (ver as versões em
[01-software-criterios.md](01-software-criterios.md)). Outra binding, como C, Android
ou um ORM, muda a sobrecarga por operação e, principalmente, o **controle de
transações**, que define a carga de leitura (K1). *Limitação assumida:* os resultados
valem para o SQLite usado a partir do Python com as transações implícitas padrão.

**E4 — Banco pequeno e carga sintética.** O banco tem 10.000 linhas de 256 bytes,
alguns MB, e cabe no cache. O acesso é por chave primária, sem índices secundários,
sem consultas complexas e sem crescimento do banco ao longo do tempo. *Limitação
assumida:* não extrapolar para bancos grandes que não cabem em memória, para cargas
de produção ou para padrões de acesso diferentes. O estudo é *in vitro*, e o nível
de evidência continua **moderado**, como classificado em
[03-categorias-pesquisa.md](03-categorias-pesquisa.md).

## O que muda na leitura dos resultados

1. **Escrita e mista:** a direção dos efeitos é robusta às ameaças discutidas
   (WAL > DELETE; NORMAL > FULL, muito mais sob WAL). As magnitudes são desta
   máquina, deste disco e deste padrão de um commit por escrita, e podem estar
   infladas no H1 (I1) e no H2 (K3).
2. **Leitura:** o 5,4× do H1 é o custo de transação em autocommit, não de leitura
   (K1). A Q4 fica **sem resposta** por este experimento, e o resultado não contradiz
   a documentação. H2 e H3 na leitura são inconclusivos (C3).
3. **De onde vem o ganho:** depende do caminho de decomposição (C4). Nesta máquina,
   o maior passo isolado na escrita é o `NORMAL` sob WAL, justamente o que custa
   durabilidade. Esse custo continua não medido (K4).
4. **Toda a inferência** é condicional à independência entre rodadas (C1) e a uma
   única coleta, em uma única máquina (E1).

Esses pontos devem ser levados para as conclusões e limitações da S03-02 (#312), para
a estimativa de impacto da S03-01 (#311) e para a seção de ameaças do dashboard
(#313).

## Referências

- SQLite. [Write-Ahead Logging](https://www.sqlite.org/wal.html).
- SQLite. [File Locking And Concurrency In SQLite Version 3](https://www.sqlite.org/lockingv3.html).
- SQLite. [PRAGMA synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous) e
  [PRAGMA fullfsync](https://www.sqlite.org/pragma.html#pragma_fullfsync).
- Wohlin, C. et al. *Experimentation in Software Engineering*. Springer, 2012, cap. 8
  (ameaças à validade).

Páginas do SQLite acessadas em 25/11/2026.
