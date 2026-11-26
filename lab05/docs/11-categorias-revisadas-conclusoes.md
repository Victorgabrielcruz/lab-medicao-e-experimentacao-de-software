# Categorias revisadas, conclusões e limitações — S03-02 (#312)

Este documento fecha o estudo. Ele revisa as 7 categorias da
[versão 1](03-categorias-pesquisa.md) com base no que foi **executado**, responde
às duas perguntas do enunciado ("o que o estudo mostrou?" e "o que isso significa
para quem usa o SQLite?") e registra o que veio dos Labs 01–04 e o que foi feito
de novo.

Os números vêm da [descritiva](08-descritiva-graficos.md) e dos
[testes e efeitos](09-testes-efeitos.md) da coleta completa (360 medições,
25/11/2026). As ameaças citadas por código (C1, I1, K1…) estão em
[10-ameacas-validade.md](10-ameacas-validade.md).

## 1. As 7 categorias, revisadas

| Categoria | Versão 1 (S01) | Versão revisada | Mudou? |
|---|---|---|---|
| Natureza | Aplicada | **Aplicada** | Não |
| Objetivos | Explicativa, com parte descritiva | **Explicativa para o efeito; descritiva para o mecanismo** | Sim |
| Abordagem | Quantitativa | **Quantitativa**, com o custo de durabilidade qualitativo | Não |
| Procedimentos | Experimental, com apoio documental | **Experimental, com apoio documental** e verificações exploratórias | Ajuste |
| Tempo | Transversal | **Transversal**, confirmado: uma sessão de cerca de 5 min 30 s | Não |
| Controle | In vitro, controle parcial | **In vitro, controle parcial**, com uma confusão que a aleatorização não resolve | Ajuste |
| Nível de evidência | Moderado: alta validade interna, baixa externa | **Moderado para escrita e mista; fraco para leitura** | Sim |

### 1. Natureza: aplicada (mantida)
O estudo responde a uma decisão de configuração (qual `journal_mode` e qual
`synchronous` usar) e termina numa recomendação para quem embute o SQLite
(seção 3). Nada na execução muda isso.

### 2. Objetivos: explicativa para o efeito, descritiva para o mecanismo (revisada)
A v1 dizia que o desenho permite atribuir a diferença ao fator alterado, e isso se
manteve: cada comparação muda um único fator, com pares por rodada e ordem
aleatória. A execução mostrou dois limites que a v1 não previa:

- **O mecanismo da leitura não era o que supúnhamos.** O ganho de 5,4× do WAL na
  leitura vem do custo de abrir uma transação por `SELECT`, e não da leitura em si
  (K1). O estudo explica *que* o `journal_mode` causa a diferença, mas o *porquê*
  só foi esclarecido por uma verificação exploratória, fora do protocolo.
- **Os efeitos não são aditivos.** O ganho do `NORMAL` vale 1,26× sob `DELETE` e
  12,0× sob `WAL` (C4). A explicação de cada fator só vale **condicionada ao nível
  do outro**, e "de onde vem o ganho" depende do caminho escolhido.

Por isso, a parte explicativa vale para o **efeito** de cada fator neste ambiente.
O **mecanismo** (número de sincronizações, custo de transação) continua
descritivo: vem da documentação e não foi medido diretamente.

### 3. Abordagem: quantitativa (mantida)
M1, M2 e M3 são numéricas, em escala de razão, e foram analisadas com descritiva,
teste dos sinais com Holm, tamanho do efeito e IC bootstrap. A durabilidade, que é
o custo do `NORMAL`, continua **qualitativa**, apoiada na documentação (K4). O
estudo não é misto por isso, mas um lado da balança continua sem número.

### 4. Procedimentos: experimental, com apoio documental (ajustada)
A classificação se mantém. O ajuste é declarar que a discussão das ameaças usou
**três verificações locais exploratórias**: leitura em transação única, modos
`TRUNCATE`/`PERSIST` e checkpoint ao fechar. Elas ficaram fora do protocolo, dos
dados e dos testes, servem só para dimensionar ameaças e não mudam a natureza
experimental do estudo.

### 5. Tempo: transversal (mantida e confirmada)
A coleta completa foi uma única sessão, em 25/11/2026, das 16:42:57 às 16:48:27,
com uma versão do SQLite (3.53.1) e do Python (3.12.14). Uma sessão tão curta
concentra as rodadas num mesmo estado da máquina, e isso pesa contra a
independência entre rodadas (C1).

### 6. Controle: in vitro, controle parcial (ajustada)
Os controles previstos foram aplicados: fatores manipulados, ordem aleatória por
rodada, banco novo, aquecimentos descartados e ambiente registrado. A execução
mostrou um caso que a v1 tratava só como "ruído": o **antivírus e a criação do
arquivo de journal afetam só o modo `DELETE`** (I1). Por estar ligada ao próprio
tratamento, essa confusão **não é distribuída pela aleatorização**. O controle
continua parcial, e agora com uma fonte de viés identificada, não só de ruído.

### 7. Nível de evidência: moderado para escrita e mista, fraco para leitura (revisada)
A v1 dava um único nível, moderado, e condicionava a subida à replicação nas
máquinas dos três integrantes. A replicação **não foi executada**. Com os
resultados em mãos, o nível passa a ser diferente para cada conclusão:

| Conclusão | Nível | Por quê |
|---|---|---|
| Direção dos efeitos na escrita e na mista (WAL > DELETE; NORMAL > FULL) | **Moderado** | 30/0 pares em todas as comparações, efeitos grandes; na escrita, a mesma direção apareceu nas verificações exploratórias em outra máquina |
| Magnitude desses efeitos (4,97×, 12,0×…) | **Fraco a moderado** | Uma máquina e um disco (E1); possível inflação por I1 e K3; padrão de um commit por escrita (K2) |
| Leitura | **Fraco** | O construto não mede a velocidade de leitura (K1); H2 e H3 inconclusivos (C3) |

## 2. O que o estudo mostrou?

**A pergunta de pesquisa** era se a recomendação `WAL` + `NORMAL` se sustenta,
quanto o padrão deixa na mesa e quanto desse ganho exige abrir mão da
durabilidade. Vazão mediana (M2, ops/s) por configuração:

| Configuração | Escrita | Mista | Leitura | Garantia (documentação) |
|---|---:|---:|---:|---|
| DELETE-FULL (padrão) | 386 | 1.202 | 24.632 | Atômica, consistente, isolada; durável conforme o sistema de arquivos |
| DELETE-NORMAL | 485 | 1.493 | 24.584 | Pode não ficar consistente após queda de energia |
| WAL-FULL | 1.918 | 5.963 | 132.987 | ACID |
| WAL-NORMAL | 23.068 | 51.874 | 135.127 | Consistente; pode perder as últimas transações |

Respostas às perguntas do GQM, todas condicionais à independência entre rodadas (C1):

- **Q1 — O padrão deixa desempenho na mesa sem motivo?** Sim. Trocar só o
  `journal_mode` para WAL, mantendo o `FULL`, deu **4,97× na escrita e 4,96× na
  mista** (30/0 pares, p Holm ≈ 1,7 × 10⁻⁸), **sem perder garantia**: WAL-FULL é
  ACID. Parte desse ganho pode vir do custo de criar e apagar o journal no Windows
  (I1). A verificação exploratória ainda deixa o WAL cerca de 4× à frente.
- **Q2 — O `NORMAL` acrescenta pouco depois do WAL?** **Não. A expectativa prévia
  foi refutada.** Esperávamos que o WAL concentrasse o ganho e que o `NORMAL`
  fosse um "risco sem retorno". Na escrita, o `NORMAL` sob WAL rendeu **12,0×**
  (IC 95% [11,7; 12,3]) e, na mista, **8,70×**: o maior passo isolado do estudo. Com
  um commit por escrita, o `FULL` faz uma sincronização do WAL a cada commit, e o
  `NORMAL` a elimina. O ganho é real e grande, e é justamente o passo que **custa
  durabilidade**.
- **Q3 — O "atalho" `DELETE` + `NORMAL` compete com o WAL?** Não. Ele rendeu só
  **1,26× na escrita e 1,24× na mista**, e o WAL-FULL é cerca de **4× mais rápido
  que o DELETE-NORMAL** nas duas cargas, com garantia maior. O atalho é **dominado**:
  é mais lento e menos seguro. A interação é forte: o `NORMAL` vale muito mais sob
  WAL (12,0×) que sob DELETE (1,26×).
- **Q4 — O WAL penaliza a leitura?** **Este estudo não consegue responder.** A carga
  de leitura mediu 10.000 transações curtas em autocommit, e nelas o WAL foi
  **5,4× mais rápido**. Isso é um resultado válido para esse padrão de uso, mas não
  é a "leitura" de que fala a documentação (K1). Numa verificação exploratória com
  todas as leituras numa única transação, o WAL ficou levemente mais lento, como a
  documentação diz. O `synchronous` não teve efeito detectável na leitura, mas os IC
  são largos demais para afirmar equivalência (C3).

**Em uma frase:** a recomendação `WAL` + `NORMAL` se sustenta em velocidade, mas
não é um almoço grátis. **O WAL é o passo grátis (cerca de 5×). O `NORMAL` é o passo
grande (cerca de 9 a 12× a mais) e é pago em durabilidade.** O padrão, mantido por
"segurança", é dominado pelo WAL-FULL, que é mais seguro e mais rápido.

## 3. O que isso significa para quem usa o SQLite?

1. **Troque o padrão pelo WAL.** Em aplicações com muitas transações pequenas de
   escrita, manter `DELETE` custou cerca de 5× em vazão, sem ganho de garantia:
   WAL-FULL também é ACID. A página do [WAL](https://www.sqlite.org/wal.html) lista
   as desvantagens a conferir antes, como não funcionar em sistemas de arquivos de
   rede e criar os arquivos auxiliares `-wal` e `-shm`.
2. **Decida o `NORMAL` pela tolerância a perda de dados, não pela velocidade.** O
   ganho do `NORMAL` é grande demais para chamar de marginal. A pergunta certa é:
   *perder as últimas transações confirmadas numa queda de energia é aceitável?*
   Para cache local, dados derivados ou dados que podem ser sincronizados de novo
   com um servidor, provavelmente sim. Para registro financeiro ou dado que o
   usuário digitou e não existe em outro lugar, o `FULL` é a escolha defensável.
3. **Nunca use `DELETE` + `NORMAL`.** Ele é dominado pelo WAL-FULL: é mais lento e
   tem a pior garantia da tabela.
4. **Agrupe escritas antes de baixar a garantia.** O estudo mediu o pior caso, um
   commit por `INSERT` (K2). Agrupar escritas em transações maiores reduz o número
   de sincronizações sem mudar o `synchronous`. Isso **não foi medido** aqui e fica
   como alternativa a testar.
5. **Quem usa o `sqlite3` do Python:** leituras soltas rodam em autocommit, e cada
   uma paga o custo de uma transação. Na verificação exploratória, abrir uma
   transação explícita para um lote de leituras multiplicou a vazão do modo
   `DELETE` em cerca de 15×. É uma indicação para testar, não um resultado do
   experimento.
6. **Meça na sua plataforma.** Os valores absolutos variaram cerca de 5× entre duas
   máquinas Windows. No Linux e no macOS, o custo e o significado do `FULL` são
   outros (E1, E2). A direção dos efeitos deve se repetir; a magnitude, não
   necessariamente.

A tradução desses números em impacto para empresas e usuários, com fontes
públicas e premissas explícitas, está em
[12-estimativa-impacto.md](12-estimativa-impacto.md), entrega da S03-01 (#311).

## 4. Limitações

As 17 ameaças estão discutidas em [10-ameacas-validade.md](10-ameacas-validade.md).
As que mais limitam as conclusões acima são:

- **Uma máquina, uma sessão, sem replicação** (C1, E1): toda inferência é
  condicional à independência entre rodadas, e as magnitudes valem para este
  Windows, NTFS e SSD.
- **A durabilidade não foi medida** (K4): o custo do `NORMAL` é qualitativo.
  O estudo não estima quantas transações seriam perdidas nem com que frequência.
- **A leitura foi mal operacionalizada para a Q4** (K1): o resultado vale para
  leituras em autocommit, não para leituras em geral.
- **Sem concorrência** (K5): o principal benefício do WAL, leitores simultâneos com
  um escritor, ficou fora.
- **Carga sintética e banco pequeno** (K2, E4): um commit por escrita e 10.000
  linhas que cabem no cache.

O que um próximo estudo deveria fazer: replicar nas três máquinas do grupo (e em
Linux), incluir leitura em transação única e escrita em lote como cargas, usar
`TRUNCATE` como controle do custo do journal e testar a durabilidade com
desligamento forçado de uma máquina virtual.

## 5. O que foi reaproveitado dos Labs 01–04 e o que foi feito de novo

| Lab | O que foi reaproveitado | Como aparece no Lab05 |
|---|---|---|
| **Lab01** — repositórios populares | Kanban no GitHub Projects, sprints com milestones, uma branch e um PR por issue | Project 7 com as issues #299–#315 e o mesmo fluxo de PRs. A coleta via API do GitHub **não** foi reaproveitada: o enunciado proíbe repositórios como objeto de estudo |
| **Lab02** — IA × codificação manual | Desenho de experimento com tratamentos, piloto antes da coleta, ordem controlada, análise pareada e correção de Holm | Fatorial 2 × 2, piloto (#304), ordem aleatória por rodada, pares por rodada e Holm nas nove comparações. O Wilcoxon pareado do Lab02 foi trocado pelo teste dos sinais, porque o piloto não sustentava a simetria das diferenças que o Wilcoxon exige |
| **Lab03** — métricas DORA | Validação dos dados, versionamento com hashes, reprodução offline e a ideia de replicação | Validador com manifesto SHA-256 (#307), CSV bruto versionado e análise que não reexecuta a coleta. As métricas DORA **não** se aplicam: medem o processo de entrega, e o estudo mede o desempenho do produto |
| **Lab04** — testes de hipótese | Escolha do teste pela escala e pelo pressuposto, binomial exato (`scipy.stats.binomtest`), semente 42, dashboard Streamlit com AppTest e estrutura narrativa | O teste dos sinais é um binomial exato. A lição do Lab04, de que com falhas em rajadas nem o binomial controla o erro tipo I, motivou a **auditoria de independência** da #309. O dashboard reusa a estrutura e os testes de interface |

**O que foi feito de novo:**

- **Instrumento próprio de benchmark:** cargas determinísticas por semente, mesma
  sequência de operações nas quatro configurações, janela cronometrada explícita e
  verificação dos `PRAGMA` efetivos.
- **Métrica derivada M3** (razão entre medianas de vazão) com **IC bootstrap
  pareado**, para medir magnitude em vez de só significância.
- **Auditoria temporal** com teste exato de sequências (*runs*) e regra de
  suspensão de conclusões confirmatórias.
- **Software real em operação como objeto**, e não um repositório: o SQLite que
  vem no Python, com a análise ligada às garantias da documentação oficial.
- **Armadilhas de medição usadas no desenho:** Goodhart e Campbell justificam a
  exclusão do `synchronous=OFF`, e a falácia de McNamara obriga a apresentar a
  durabilidade junto com a vazão.
- **Verificações exploratórias para testar as próprias ameaças**, separadas do
  protocolo, em vez de só listar as ameaças.
