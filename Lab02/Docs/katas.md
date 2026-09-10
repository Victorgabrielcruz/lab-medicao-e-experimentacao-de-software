# Seleção das katas experimentais

**Task:** S01-02 — Selecionar e documentar as seis katas  
**Data da seleção:** 09/09/2026  
**Estado:** especificações prontas; a confirmação individual de familiaridade
descrita na seção 4 é a última condição para congelar a amostra.

Este documento registra os seis objetos experimentais do Lab02. Eles foram
criados como especificações inéditas para este repositório, sem dependências
de rede, serviços externos, interface gráfica ou arquivos particulares. A
linguagem e a assinatura concreta serão definidas apenas na preparação da
suíte de aceitação; os contratos de entrada e saída abaixo são independentes
de linguagem.

Os enunciados descrevem regras observáveis e não prescrevem estruturas de
dados, algoritmos ou técnicas de implementação.

## 1. Conjunto selecionado

| ID | Kata | Contrato resumido | Faixa estimada | Bloco |
|---|---|---|---:|---|
| K01 | [Conflitos no pátio de docas](../katas/K01/README.md) | Identificar agendamentos incompatíveis por doca e horário. | 20–30 min | B1 |
| K02 | [Compartimentos de coleta](../katas/K02/README.md) | Processar entradas e saídas sujeitas a capacidade. | 15–25 min | B1 |
| K03 | [Cadeia de custódia de remessas](../katas/K03/README.md) | Validar etapas sequenciais de remessas intercaladas. | 15–25 min | B2 |
| K04 | [Credenciais de visita](../katas/K04/README.md) | Validar o ciclo de vida de credenciais com expiração. | 20–30 min | B2 |
| K05 | [Alertas de leitura persistente](../katas/K05/README.md) | Emitir alertas por leituras consecutivas fora da faixa. | 15–25 min | B3 |
| K06 | [Roteiros de inspeção](../katas/K06/README.md) | Validar visitas intercaladas contra roteiros ordenados. | 15–25 min | B3 |

As faixas são estimativas de triagem e permanecem abaixo do *time-box* fixo
de 35 minutos. A equivalência objetiva dos blocos — solução de referência,
LOC, complexidade e casos-limite — foi avaliada na S01-03 e confirmou este
agrupamento; ver [`kata-equivalence.md`](kata-equivalence.md).

## 2. Triagem de candidatas

Foram considerados dez exercícios inéditos de escopo local. A triagem buscou
regras claras, entrada pequena, resultado determinístico e código suficiente
para as métricas da RQ3.

| Candidata | Decisão | Justificativa |
|---|---|---|
| Conflitos no pátio de docas | Selecionada como K01 | Regras temporais locais e resultado verificável. |
| Compartimentos de coleta | Selecionada como K02 | Mantém estado por compartimento e rejeições observáveis. |
| Cadeia de custódia de remessas | Selecionada como K03 | Fluxo curto, determinístico e sem domínio especializado. |
| Credenciais de visita | Selecionada como K04 | Ciclo de vida curto com limite temporal explícito. |
| Alertas de leitura persistente | Selecionada como K05 | Regras numéricas e sequências independentes por sensor. |
| Roteiros de inspeção | Selecionada como K06 | Sequências variáveis por rota, com resultado objetivo. |
| Tarifa por faixas | Excluída | Escopo insuficiente para a faixa de tempo pretendida. |
| Agenda com recorrência semanal | Excluída | Casos de calendário elevariam o risco de ultrapassar 35 minutos. |
| Conversão de unidades encadeadas | Excluída | Excessivamente dependente de detalhes de formato. |
| Regras de desconto acumulado | Excluída | Risco de familiaridade com padrões de exercícios comerciais. |

## 3. Origem e verificação de indexação pública

### 3.1 Origem

As seis especificações selecionadas foram elaboradas para a task S01-02 neste
repositório em 09/09/2026. Não foram copiadas de plataformas de katas. Essa
origem reduz o risco de uma solução pronta associada ao enunciado completo.
Antes de usar a classificação “autoral” em uma entrega acadêmica, o grupo deve
validar a atribuição e a declaração de uso de ferramentas conforme a política
da disciplina.

### 3.2 Busca de trechos distintivos

Em 09/09/2026, foram pesquisados os trechos entre aspas abaixo em mecanismo
público de busca. A busca não retornou uma página que reproduzisse o enunciado
nem uma solução da kata correspondente. Resultados que compartilhem palavras
isoladas não são tratados como correspondência. As consultas devem ser
repetidas imediatamente antes do primeiro trial e qualquer correspondência
substancial deve excluir ou reescrever a kata afetada.

| Kata | Consulta distintiva | Resultado registrado |
|---|---|---|
| K01 | `"se um período termina exatamente quando outro começa, eles são compatíveis"` | Sem correspondência textual do enunciado ou solução. |
| K02 | `"um movimento recusado não altera o saldo do compartimento"` | Sem correspondência textual do enunciado ou solução. |
| K03 | `"uma etapa recusada não muda a etapa já confirmada da remessa"` | Sem correspondência textual do enunciado ou solução. |
| K04 | `"eventos recusados não alteram o estado; UTILIZADA e REVOGADA são estados finais"` | Sem correspondência textual do enunciado ou solução. |
| K05 | `"o alerta nasce apenas na leitura que completa a sequência"` | Sem correspondência textual do enunciado ou solução. |
| K06 | `"um ponto recusado não substitui a próxima parada esperada"` | Sem correspondência textual do enunciado ou solução. |

Essa verificação é evidência de baixa indexação, não prova de que nenhum
modelo tenha visto conceitos semelhantes. A análise final deve registrar essa
limitação como ameaça à validade de construção.

## 4. Verificação de familiaridade prévia

Familiaridade é uma informação dos participantes e não pode ser inferida pela
equipe de preparação. Antes de divulgar as katas para execução, cada pessoa
deve responder, para **cada** kata: “Antes desta seleção, eu já havia resolvido
este enunciado, conhecido uma solução específica ou praticado exercício
equivalente a ponto de reconhecer imediatamente a solução?”

| Participante | K01 | K02 | K03 | K04 | K05 | K06 | Registro e data |
|---|---|---|---|---|---|---|---|
| P01 — Víctor Gabriel Cruz Pereira | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente |
| P02 — Jonathan Sena da Silva | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente |
| P03 — Matheus Fernandes de Oliveira | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente | Pendente |

Uma resposta “sim” exclui a kata para aquele participante. Como o desenho
requer seis objetos comuns e o grupo tem apenas seis selecionados, o grupo
deve substituir a kata ou registrar um desvio metodológico antes de iniciar a
coleta. Respostas “não” datadas para todas as células são necessárias para
marcar este critério como atendido.

## 5. Revisão de clareza e critérios de inclusão

| Critério | Evidência | Estado |
|---|---|---|
| Exatamente seis katas | Diretórios `K01` a `K06` e tabela da seção 1. | Atendido |
| Entrada, saída, restrições e exemplos | Um `README.md` completo em cada diretório da kata. | Atendido |
| Sem rede ou serviço externo | Todos os contratos recebem dados em memória e não mencionam integração externa. | Atendido |
| Compatibilidade com 35 minutos | Escopo limitado, até 200 eventos/registros e estimativa máxima de 30 minutos. | Atendido; sem piloto externo disponível (só 3 participantes, todos sujeitos do experimento), avaliado por inspeção + solução de referência real na S01-03 — ver `kata-equivalence.md` §1 |
| Baixa indexação ou autoria | Origem e seis consultas distintivas registradas na seção 3. | Atendido com rechecagem pendente antes dos trials |
| Ausência de pistas de implementação | Revisão textual: nenhum enunciado indica algoritmo, estrutura de dados ou técnica. | Atendido |
| Não conhecimento prévio | Matriz individual da seção 4. | Pendente de declaração dos participantes |

## 6. Próximos controles obrigatórios

1. Coletar e datar as declarações da seção 4 antes de qualquer trial.
2. Repetir as seis buscas da seção 3.2 antes de congelar a amostra.
3. ~~Na S01-03, validar os pares B1, B2 e B3 com soluções de referência sob
   custódia, testes-piloto e a matriz de equivalência.~~ Feito — sem piloto
   externo disponível, validado por rubric objetivo + soluções de
   referência reais; ver `kata-equivalence.md`.
4. Na S01-04, criar testes automatizados sem alterar o sentido dos contratos
   publicados em cada kata.
