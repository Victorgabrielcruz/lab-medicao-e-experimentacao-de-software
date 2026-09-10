# Metodologia

## 1. Objetivo

Definir um protocolo controlado, rastreável e reproduzível para comparar a resolução de tarefas de programação com e sem o auxílio de um assistente de IA generativa, de modo a responder às três questões de pesquisa do Lab02:

- **RQ1:** o uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?
- **RQ2:** o uso de assistente de IA reduz a quantidade de defeitos no código produzido?
- **RQ3:** o uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?

Esta metodologia deve ser aprovada pelo grupo e congelada antes do primeiro trial. Mudanças posteriores deverão ser registradas como desvios do protocolo, acompanhadas de data, justificativa e impacto esperado sobre a análise.

---

## 2. Caracterização do estudo

O estudo será um experimento controlado com desenho **crossover within-subject**, no qual cada participante será submetido aos dois tratamentos. Dessa forma, cada integrante atuará como seu próprio controle, reduzindo o efeito da diferença individual de experiência e habilidade de programação.

### 2.1 Unidade experimental

A unidade experimental será um **trial**, definido como a tentativa de um participante de resolver uma kata sob um único tratamento e dentro do limite de tempo estabelecido.

Cada trial será identificado de forma única pela combinação:

`participante + kata + tratamento`

Um participante não poderá resolver a mesma kata mais de uma vez. Comparações pareadas serão formadas dentro de cada participante e de cada bloco de dificuldade, conforme descrito na Seção 8.

### 2.2 Participantes

Participarão os três integrantes do grupo:

| ID anonimizado | Integrante |
|---|---|
| P01 | Víctor Gabriel Cruz Pereira |
| P02 | Jonathan Sena da Silva |
| P03 | Matheus Fernandes de Oliveira |

Os identificadores anonimizados serão utilizados no dataset e nos gráficos. Os nomes serão mantidos apenas nos registros de rastreabilidade do GitHub Projects.

Antes da execução, cada participante preencherá uma ficha breve de caracterização contendo:

- experiência de programação, em anos ou meses;
- experiência com a linguagem escolhida;
- familiaridade com testes automatizados;
- frequência de uso de assistentes de IA;
- familiaridade prévia com o assistente selecionado;
- contato prévio com alguma das katas ou com problemas equivalentes.

Essas informações não serão utilizadas para excluir resultados, mas apoiarão a discussão sobre ameaças à validade.

### 2.3 Contexto

O experimento será executado individualmente, por estudantes de graduação, em tarefas curtas de programação com testes automatizados de aceitação. Todos os trials deverão utilizar a mesma linguagem, versão de runtime, estrutura de projeto e conjunto de ferramentas.

---

## 3. Goal-Question-Metric (GQM)

### Goal

Analisar o uso de assistentes de IA generativa na resolução de tarefas de programação, com o propósito de comparar seu efeito frente à codificação manual, com respeito a tempo de resolução, qualidade funcional e qualidade estrutural do código produzido, do ponto de vista do grupo pesquisador, no contexto de katas de dificuldade equivalente resolvidas por estudantes de graduação sob condições controladas.

### Questions e métricas selecionadas

| RQ | Métrica primária | Métricas complementares e de controle |
|---|---|---|
| RQ1 | Tempo até todos os testes passarem (*time-to-green*), em segundos | Indicador de censura e número de interações com IA |
| RQ2 | Taxa de sucesso dos testes de aceitação ao final do trial, em percentual | Número absoluto de testes falhando |
| RQ3 | Complexidade ciclomática média por função/método | Percentual de linhas duplicadas, LOC como controle obrigatório e Índice de Manutenibilidade como análise exploratória |

A distinção entre métricas primárias e complementares será preservada na análise para evitar escolher a métrica mais favorável depois de observar os resultados.

---

## 4. Hipóteses

As hipóteses serão avaliadas a partir de diferenças pareadas. Para as fórmulas abaixo, considere:

- `T_manual` e `T_IA`: tempo observado em cada tratamento;
- `S_manual` e `S_IA`: taxa de testes passando;
- `CC_manual` e `CC_IA`: complexidade ciclomática média;
- `DUP_manual` e `DUP_IA`: percentual de duplicação.

### 4.1 RQ1 — Tempo

- **H0₁:** a mediana da diferença pareada `T_manual − T_IA` é igual a zero; o assistente de IA não reduz o tempo de resolução.
- **H1₁:** a mediana da diferença pareada `T_manual − T_IA` é maior que zero; o assistente de IA reduz o tempo de resolução.

### 4.2 RQ2 — Defeitos

- **H0₂:** a mediana da diferença pareada `S_IA − S_manual` é igual a zero; o assistente de IA não aumenta a taxa de testes passando.
- **H1₂:** a mediana da diferença pareada `S_IA − S_manual` é maior que zero; o assistente de IA aumenta a taxa de testes passando e, portanto, reduz os defeitos observados.

O número absoluto de testes falhando será usado como medida complementar, sem substituir a taxa de sucesso como métrica primária.

### 4.3 RQ3 — Estrutura do código

- **H0₃a:** a mediana da diferença pareada `CC_IA − CC_manual` é igual a zero.
- **H1₃a:** a mediana da diferença pareada `CC_IA − CC_manual` é diferente de zero.
- **H0₃b:** a mediana da diferença pareada `DUP_IA − DUP_manual` é igual a zero.
- **H1₃b:** a mediana da diferença pareada `DUP_IA − DUP_manual` é diferente de zero.

As hipóteses da RQ3 são bicaudais porque a questão investiga se o uso de IA **altera**, e não necessariamente se melhora, as características estruturais.

---

## 5. Variáveis do experimento

### 5.1 Variável independente

A variável independente será o modo de resolução da tarefa, com dois níveis:

- **IA:** resolução com acesso ao assistente de IA selecionado;
- **Manual:** resolução sem acesso a assistentes de IA generativa.

### 5.2 Variáveis dependentes

- tempo até passar em todos os testes de aceitação, em segundos;
- conclusão dentro do limite de tempo (`sucesso` ou `censurado`);
- quantidade total de testes de aceitação;
- quantidade de testes passando ao final do trial;
- quantidade de testes falhando ao final do trial;
- taxa de sucesso dos testes de aceitação;
- complexidade ciclomática média por função/método;
- percentual de linhas duplicadas;
- linhas de código (LOC).

### 5.3 Variáveis exploratórias

- número de prompts enviados ao assistente;
- número total de interações com o assistente;
- Índice de Manutenibilidade;
- percepção de dificuldade da kata, registrada pelo participante após o trial em escala de 1 a 5;
- ocorrência de erro de ambiente ou interrupção externa.

### 5.4 Variáveis controladas

Serão mantidos constantes:

- linguagem e versão;
- dependências e suas versões;
- IDE e extensões, exceto a habilitação do assistente conforme o tratamento;
- assistente de IA, plano de acesso, modelo e modo de operação;
- hardware, sempre que possível;
- estrutura inicial das katas;
- comandos de teste e de análise estática;
- limite de tempo;
- acesso a documentação convencional;
- critérios de início, pausa e encerramento do cronômetro;
- ambiente físico mínimo, buscando reduzir interrupções.

---

## 6. Tratamentos

### 6.1 Tratamento IA

No tratamento IA, o participante poderá utilizar somente o assistente previamente selecionado pelo grupo. Antes da coleta, os seguintes dados deverão ser preenchidos e congelados:

| Parâmetro | Valor pré-registrado |
|---|---|
| Ferramenta | `<preencher antes dos trials>` |
| Versão ou data de acesso | `<preencher antes dos trials>` |
| Modelo, quando visível | `<preencher antes dos trials>` |
| Plano/modalidade | `<preencher antes dos trials>` |
| Forma de interação | `<chat, autocomplete ou ambos>` |
| Retenção de contexto | Uma conversa/contexto novo por trial |

São permitidas solicitações de explicação, geração, correção e refatoração de código. Todo prompt digitado pelo participante e toda resposta relevante deverão ser exportados ou registrados, quando a ferramenta permitir, para auditoria do tratamento.

O participante não poderá reutilizar prompts, código ou conversas de trials anteriores. O contexto do assistente deverá ser limpo antes de cada nova tarefa.

### 6.2 Tratamento Manual

No tratamento Manual, todo recurso de IA generativa deverá permanecer desabilitado. São permitidos:

- documentação oficial da linguagem e das bibliotecas padronizadas;
- consulta local à assinatura de APIs;
- mensagens do compilador, interpretador, linter e testes;
- recursos convencionais da IDE, como navegação, depuração e completação não generativa.

Não são permitidos:

- chatbots ou mecanismos de busca com respostas geradas por IA;
- autocomplete generativo;
- consulta a soluções prontas da kata;
- código, anotações ou prompts produzidos em trials anteriores.

Se não for possível distinguir a busca convencional de recursos generativos, o grupo deverá adotar uma fonte de documentação previamente definida e registrar essa restrição.

---

## 7. Objetos experimentais

### 7.1 Quantidade e organização

Serão utilizadas **6 katas**, agrupadas previamente em **3 pares de dificuldade equivalente**:

| Bloco | Kata A | Kata B |
|---|---|---|
| B1 | K01 | K02 |
| B2 | K03 | K04 |
| B3 | K05 | K06 |

As especificações, os critérios de seleção, a declaração de origem e a
verificação de indexação estão em [`katas.md`](katas.md). A formação dos
blocos acima é provisória até a avaliação objetiva prevista para a S01-03.

Cada participante resolverá uma kata de cada par com IA e a outra sem IA. Assim, cada participante realizará seis trials — três por tratamento — e o experimento produzirá 18 trials no total.

### 7.2 Critérios de inclusão

Uma kata será elegível quando:

- puder ser concluída em até 35 minutos por alguém com o perfil dos participantes;
- possuir escopo e regras inequívocos;
- exigir produção de código suficiente para cálculo das métricas estáticas;
- possuir testes automatizados de aceitação determinísticos;
- não depender de rede, banco de dados, interface gráfica ou serviço externo;
- não exigir conhecimento de domínio especializado;
- apresentar dificuldade comparável à kata pareada;
- for autoral ou pouco indexada em mecanismos públicos de busca;
- não tiver sido resolvida anteriormente pelos participantes.

### 7.3 Critérios de exclusão

Serão excluídas katas que:

- sejam reconhecidas por algum participante antes da execução;
- apresentem solução pronta facilmente identificável em repositórios públicos;
- tenham testes ambíguos, não determinísticos ou defeituosos;
- exijam configuração substancialmente diferente das demais;
- tenham efeito de piso ou teto no piloto, sendo triviais ou inviáveis no limite definido.

### 7.4 Validação de equivalência

Um piloto será conduzido por uma pessoa que não participará dos trials válidos, sempre que isso for possível. Caso não haja piloto externo disponível, a equivalência será avaliada sem implementação completa, por inspeção independente dos seguintes fatores:

- quantidade e complexidade das regras;
- estruturas de dados necessárias;
- número estimado de casos-limite;
- quantidade de testes de aceitação;
- LOC estimada para uma solução de referência;
- complexidade ciclomática da solução de referência;
- tempo estimado de implementação.

Os critérios e escores de dificuldade serão definidos antes da alocação dos tratamentos. As soluções de referência e os testes não poderão ser acessados pelos participantes antes de seus trials.

---

## 8. Alocação e contrabalanceamento

### 8.1 Formação dos pares

Cada bloco de dificuldade fornecerá uma comparação pareada para cada participante. Dentro do bloco, uma kata será executada com IA e a outra manualmente.

### 8.2 Sequências de tratamento

Serão utilizadas sequências alternadas e contrabalanceadas:

| Participante | Sequência dos seis trials |
|---|---|
| P01 | IA → Manual → IA → Manual → IA → Manual |
| P02 | Manual → IA → Manual → IA → Manual → IA |
| P03 | IA → Manual → Manual → IA → IA → Manual |

A associação entre K01–K06, as posições da sequência e os participantes será sorteada por script com semente fixa e registrada antes da execução. O sorteio deverá obedecer às seguintes restrições:

- cada participante executará exatamente três trials por tratamento;
- cada participante terá os três blocos de dificuldade representados nos dois tratamentos;
- cada kata será executada ao menos uma vez em cada tratamento considerando o conjunto do grupo;
- a ordem das katas será diferente entre os participantes;
- duas katas do mesmo par não serão executadas consecutivamente pelo mesmo participante, reduzindo transferência direta de estratégia.

Como há três participantes, não é possível obter equilíbrio perfeito de exposição para cada kata entre os dois tratamentos. A alocação desigual inevitável — duas execuções em um tratamento e uma no outro — será invertida entre as katas do mesmo par e registrada como limitação.

### 8.3 Sigilo da alocação

Cada participante receberá somente a próxima kata e o tratamento correspondente no momento do trial. O cronograma completo e as soluções de referência ficarão sob responsabilidade de outro integrante ou do responsável pela preparação.

---

## 9. Ambiente experimental

Antes dos trials, o grupo deverá registrar em arquivo versionado:

- sistema operacional e versão;
- processador e memória disponível;
- linguagem e versão do runtime;
- gerenciador de dependências e arquivo de bloqueio;
- IDE e versão;
- extensões habilitadas;
- framework de testes e versão;
- assistente de IA e configuração definida na Seção 6;
- versões das ferramentas de métricas estáticas;
- comandos exatos usados para testes e coleta.

Recomenda-se utilizar **Python** para aproveitar uma cadeia única de análise com `radon cc` para complexidade, `radon raw` para LOC, `radon mi` para Índice de Manutenibilidade e `jscpd` para duplicação. Essa escolha somente se tornará definitiva quando registrada pelo grupo antes dos trials. Se Java for escolhido, deverão ser utilizados CK e PMD CPD, preservando as mesmas definições operacionais desta metodologia.

Cada kata deverá partir de um diretório limpo e idêntico para todos os participantes, contendo apenas:

- enunciado da tarefa;
- assinatura ou esqueleto mínimo da solução;
- testes de aceitação;
- configuração necessária para execução local;
- script padronizado para iniciar o trial e coletar os resultados.

Arquivos de teste e configuração serão somente leitura durante o trial. Alterá-los invalidará a tentativa, salvo quando comprovado erro no material experimental.

---

## 10. Procedimento de execução

### 10.1 Preparação anterior à coleta

1. Selecionar e validar as seis katas.
2. Congelar enunciados, testes, soluções de referência e ferramentas.
3. Registrar versões e comandos do ambiente.
4. Gerar e versionar a alocação contrabalanceada.
5. Executar testes de sanidade em todos os pacotes de kata.
6. Criar uma Issue por combinação participante–kata–tratamento no GitHub Projects.
7. Realizar uma sessão de treinamento que não utilize nenhuma kata do experimento, para familiarizar todos os participantes com o cronômetro, a execução dos testes e as regras dos dois tratamentos.

A sessão de treinamento não será incluída no dataset.

### 10.2 Início de cada trial

1. Confirmar que o participante não conhece a kata.
2. Fechar códigos, anotações e conversas de trials anteriores.
3. Restaurar o pacote original da kata em um diretório limpo.
4. Validar que os testes executam e falham pelo motivo esperado no esqueleto inicial.
5. Habilitar ou desabilitar o assistente conforme o tratamento.
6. Criar uma conversa vazia, quando aplicável.
7. Apresentar simultaneamente o enunciado e iniciar o cronômetro.

### 10.3 Durante o trial

O participante poderá editar apenas o código de produção indicado para a kata e executar os testes quantas vezes desejar. O cronômetro continuará correndo durante leitura, compilação, execução de testes e interação com o assistente.

Pausas não serão permitidas, exceto em caso de falha externa comprovada. Interrupções deverão ser anotadas no log do trial.

### 10.4 Critério de encerramento

O trial terminará no primeiro dos seguintes eventos:

1. todos os testes de aceitação passam; ou
2. o cronômetro atinge **35 minutos**.

Quando todos os testes passarem, o tempo será registrado em segundos no instante da primeira execução completamente verde. Quando isso não ocorrer, o trial será encerrado e registrado como **censurado em 2.100 segundos**, sem descarte.

Após o encerramento:

1. nenhuma nova alteração será permitida;
2. o estado final do código será preservado, mesmo incompleto;
3. a suíte completa será executada uma última vez;
4. serão registrados testes passando, falhando e total;
5. as ferramentas de análise estática serão executadas sobre o código final;
6. o participante registrará dificuldade percebida e qualquer ocorrência relevante;
7. o código será commitado com referência à Issue correspondente.

### 10.5 Falhas de infraestrutura

Uma tentativa poderá ser repetida somente quando houver falha externa que impeça materialmente a execução, como queda de energia, travamento do ambiente ou teste defeituoso. A decisão deverá ser tomada sem consultar o resultado produzido e registrada no log.

Falhas de compilação, erros lógicos, uso inadequado da ferramenta e indisponibilidade causada pelo próprio código são resultados do trial, não falhas de infraestrutura.

---

## 11. Definições operacionais e coleta das métricas

### 11.1 Tempo e censura — RQ1

- `started_at`: instante de apresentação do enunciado e início do cronômetro;
- `finished_at`: instante da primeira execução completamente verde ou do fim do limite;
- `duration_seconds`: diferença entre `finished_at` e `started_at`, limitada a 2.100 segundos;
- `completed`: verdadeiro quando todos os testes passaram antes ou exatamente no limite;
- `censored`: verdadeiro quando o trial terminou sem sucesso aos 2.100 segundos.

Trials censurados serão mantidos no dataset com `duration_seconds = 2100` e `censored = true`.

### 11.2 Defeitos — RQ2

Os testes de aceitação serão a definição operacional de qualidade funcional:

`success_rate = passed_tests / total_tests × 100`

`failed_tests = total_tests − passed_tests`

Cada caso de teste deverá ter peso igual. Se uma ferramenta reportar testes parametrizados como casos separados, essa convenção será mantida para todas as katas e documentada.

### 11.3 Complexidade — RQ3

A complexidade ciclomática será coletada por função ou método apenas no código de produção criado para a solução. Serão excluídos testes, arquivos de configuração, dependências, código gerado e o esqueleto fornecido que não tenha sido alterado.

Serão armazenados:

- quantidade de funções/métodos analisados;
- complexidade de cada função/método;
- complexidade média do trial;
- complexidade máxima, como diagnóstico complementar.

Quando não houver função ou método detectável, o resultado será marcado como ausente e revisado, em vez de convertido automaticamente em zero.

### 11.4 Duplicação — RQ3

A duplicação será medida no código de produção final, utilizando a mesma configuração, limiar de tokens e exclusões para todos os trials. Serão armazenados:

- linhas analisadas;
- linhas duplicadas;
- percentual de linhas duplicadas;
- quantidade de blocos duplicados.

A configuração exata da ferramenta será versionada antes da coleta.

### 11.5 Linhas de código — controle da RQ3

LOC será medida com a mesma ferramenta e regra em todos os trials. Linhas em branco e comentários deverão ser armazenados separadamente quando a ferramenta permitir. A análise principal utilizará LOC lógica ou de código-fonte, conforme a definição da ferramenta pré-registrada.

Complexidade e duplicação nunca serão interpretadas isoladamente de LOC.

### 11.6 Interações com IA — exploratória

No tratamento IA, será registrado o número de prompts enviados pelo participante. Interações automáticas de autocomplete somente serão contadas se a ferramenta fornecer um registro confiável; caso contrário, a limitação será declarada e essa contagem não será comparada quantitativamente.

---

## 12. Estrutura dos dados

O dataset principal terá uma linha por trial e deverá conter, no mínimo:

| Campo | Descrição |
|---|---|
| `trial_id` | Identificador único do trial |
| `participant_id` | P01, P02 ou P03 |
| `kata_id` | K01 a K06 |
| `difficulty_block` | B1, B2 ou B3 |
| `order_position` | Posição de 1 a 6 na sequência do participante |
| `treatment` | `ai` ou `manual` |
| `started_at` | Data e hora de início em ISO 8601 |
| `finished_at` | Data e hora de encerramento em ISO 8601 |
| `duration_seconds` | Duração observada, limitada a 2.100 segundos |
| `completed` | Se todos os testes passaram dentro do limite |
| `censored` | Se o trial atingiu o limite sem sucesso |
| `passed_tests` | Quantidade de testes passando ao final |
| `failed_tests` | Quantidade de testes falhando ao final |
| `total_tests` | Quantidade total de testes |
| `success_rate` | Percentual de testes passando |
| `function_count` | Funções/métodos analisados |
| `mean_cyclomatic_complexity` | Complexidade ciclomática média |
| `max_cyclomatic_complexity` | Maior complexidade observada |
| `duplicated_lines` | Quantidade de linhas duplicadas |
| `duplication_percentage` | Percentual de duplicação |
| `loc` | Linhas de código de produção |
| `maintainability_index` | Métrica exploratória, quando disponível |
| `prompt_count` | Quantidade de prompts no tratamento IA |
| `perceived_difficulty` | Escala de 1 a 5 informada pelo participante |
| `incident_flag` | Indica ocorrência durante a execução |
| `issue_number` | Issue correspondente no GitHub Projects |
| `commit_sha` | Commit que preserva o estado final |

Datas deverão incluir o fuso horário. Campos não aplicáveis serão vazios, nunca preenchidos artificialmente com zero.

Além do dataset consolidado, deverão ser preservados:

- saída bruta da suíte de testes;
- saída bruta das ferramentas de métricas;
- log do cronômetro;
- código final de cada trial;
- histórico de prompts, quando exportável;
- manifesto do ambiente;
- registro de incidentes e desvios.

---

## 13. Validação e qualidade dos dados

Antes da análise, serão executadas as seguintes verificações:

- exatamente 18 `trial_id` únicos;
- seis trials por participante;
- três trials de cada tratamento por participante;
- três observações por kata;
- presença dos dois tratamentos em cada kata no conjunto do grupo;
- duração entre 0 e 2.100 segundos;
- `censored = true` implica `duration_seconds = 2100` e `completed = false`;
- `completed = true` implica `failed_tests = 0` e `success_rate = 100`;
- `passed_tests + failed_tests = total_tests`;
- taxa de sucesso entre 0 e 100;
- métricas estruturais não negativas;
- vínculo de todo trial com Issue e commit;
- correspondência entre os valores consolidados e as saídas brutas;
- inexistência de alterações nos testes de aceitação;
- versões de ferramentas consistentes entre os trials.

Valores extremos não serão removidos automaticamente. Todo outlier será investigado contra os registros brutos e mantido quando representar uma observação legítima. Correções de erro de transcrição deverão preservar um log de auditoria.

---

## 14. Plano de análise

### 14.1 Preparação

1. Validar a integridade dos dados conforme a Seção 13.
2. Identificar dados ausentes, incidentes e desvios do protocolo.
3. Formar pares por `participant_id` e `difficulty_block`.
4. Calcular, para cada par, a diferença entre os tratamentos na direção definida para cada RQ.
5. Manter trials censurados na análise.

As análises serão implementadas em script ou notebook versionado, sem edição manual dos resultados.

### 14.2 Estatística descritiva

Para cada tratamento serão reportados:

- número de trials;
- mediana;
- primeiro e terceiro quartis;
- IQR;
- mínimo e máximo;
- quantidade e percentual de trials concluídos;
- quantidade de valores ausentes.

Média e desvio-padrão poderão aparecer apenas como informações complementares. As conclusões serão baseadas prioritariamente em mediana e IQR.

### 14.3 Comparação inferencial

Será aplicado o **teste de Wilcoxon para amostras pareadas**, com nível de significância `α = 0,05`:

- RQ1: teste unilateral sobre o tempo, na direção de redução com IA;
- RQ2: teste unilateral sobre a taxa de sucesso, na direção de aumento com IA;
- RQ3: testes bilaterais para complexidade e duplicação.

Para os dois testes da RQ3, os valores de `p` serão ajustados pelo método de Holm. Além do valor de `p`, serão apresentados:

- magnitude e direção da mediana das diferenças pareadas;
- tamanho de efeito por correlação bisserial de postos, quando calculável;
- quantidade de empates e pares válidos;
- intervalo de confiança por reamostragem, identificado como exploratório devido ao tamanho da amostra.

Com apenas três participantes, as observações de um mesmo participante não são plenamente independentes. O uso dos nove pares participante–bloco aumenta a informação descritiva, mas pode produzir pseudorreplicação se interpretado como nove participantes independentes. Por isso:

- os resultados também serão apresentados agregados por participante;
- o teste de Wilcoxon será tratado como evidência exploratória;
- nenhuma ausência de significância será interpretada como prova de equivalência;
- as conclusões enfatizarão efeito observado, dispersão e incerteza.

### 14.4 Tratamento da censura

Trials sem sucesso permanecerão com tempo de 2.100 segundos e indicador de censura. Esse valor será usado no resumo e no teste de postos conforme exigido pelo enunciado, mas não representa o tempo real que seria necessário para concluir a tarefa.

Como análise de sensibilidade, serão comparados:

- resultados com todos os trials limitados a 2.100 segundos;
- proporção de conclusão por tratamento;
- tempo apenas entre trials concluídos, claramente identificado como análise condicionada ao sucesso e sujeita a viés de seleção.

### 14.5 Dados ausentes

Trials válidos não serão descartados por ausência de uma métrica secundária. A causa do valor ausente será registrada. Não haverá imputação de tempo, resultados de teste, complexidade ou duplicação.

### 14.6 Critério para responder às RQs

Cada RQ será respondida combinando:

1. direção e magnitude da diferença observada;
2. mediana e IQR por tratamento;
3. resultado do teste de Wilcoxon;
4. tamanho de efeito, quando calculável;
5. análise de sensibilidade e ameaças à validade.

O valor de `p` não será utilizado isoladamente para classificar o efeito como relevante ou irrelevante.

---

## 15. Visualização dos resultados

O dashboard será gerado por código com Pandas e Matplotlib/Seaborn e deverá conter, no mínimo:

- distribuição do tempo por tratamento, com trials censurados identificados;
- gráfico pareado ligando os resultados Manual e IA por participante/bloco;
- taxa de sucesso dos testes por tratamento;
- quantidade de trials concluídos e censurados;
- complexidade ciclomática por tratamento;
- duplicação por tratamento;
- relação entre LOC e complexidade;
- resultados individuais por participante, sem ocultar a variabilidade.

Com apenas 18 trials, todos os pontos deverão ser mostrados sempre que a legibilidade permitir. Barras isoladas com média não serão utilizadas como visualização principal.

---

## 16. Ameaças à validade e mitigação

### 16.1 Validade interna

| Ameaça | Mitigação |
|---|---|
| Diferença de habilidade entre participantes | Desenho within-subject e apresentação dos resultados individuais |
| Aprendizado e fadiga | Ordem contrabalanceada, katas distintas e limite de sessões por dia |
| Transferência de solução entre katas | Pares não consecutivos, problemas com superfícies diferentes e proibição de reutilizar código |
| Familiaridade com a IA | Sessão de treinamento e ficha de caracterização |
| Contaminação do tratamento Manual | IA desabilitada e regras explícitas de fontes permitidas |
| Variação do assistente ao longo do tempo | Mesma ferramenta/configuração e trials realizados em janela curta |
| Diferença entre computadores | Ambiente padronizado e registro de hardware/software |
| Expectativa do participante | Critérios automáticos de teste e coleta por script |

Cada participante deverá realizar, preferencialmente, no máximo dois trials por dia, com intervalo mínimo de 15 minutos, reduzindo fadiga. A mesma regra será aplicada a todos.

### 16.2 Validade de construção

| Ameaça | Mitigação |
|---|---|
| Testes passando não representam ausência total de defeitos | Suíte com casos normais, limites e exceções; limitação declarada |
| Testes em quantidades diferentes | Uso da taxa de sucesso como métrica primária da RQ2 |
| Complexidade ou duplicação influenciadas pelo tamanho | LOC reportada obrigatoriamente |
| Tempo limitado mistura produtividade e conclusão | Registro explícito de censura e análise conjunta com sucesso |
| Número de prompts não captura toda a assistência | Uso apenas exploratório e registro da forma de interação |

### 16.3 Validade externa

Os resultados estarão limitados a três estudantes, seis katas curtas, uma linguagem, um assistente e um ambiente acadêmico. Não poderão ser generalizados diretamente para equipes profissionais, sistemas de grande porte, manutenção de software ou outras ferramentas de IA.

Para ampliar a possibilidade de replicação, serão publicados os objetos experimentais, testes, configurações, dados e scripts, respeitadas as restrições de acesso à ferramenta de IA.

### 16.4 Validade de conclusão

O tamanho amostral reduzido implica baixo poder estatístico e grande incerteza. Serão privilegiados métodos não paramétricos, estatísticas robustas, visualização de todos os dados, tamanhos de efeito e linguagem cautelosa nas conclusões.

### 16.5 Memorização e vazamento

Assistentes podem reproduzir soluções de exercícios amplamente indexados. Para mitigar essa ameaça:

- serão priorizadas katas autorais ou pouco indexadas;
- trechos distintivos do enunciado serão pesquisados antes da seleção;
- problemas clássicos reconhecíveis serão excluídos;
- o histórico de prompts será preservado quando possível;
- qualquer resposta da IA que reproduza uma solução conhecida será registrada para discussão.

---

## 17. Reprodutibilidade e rastreabilidade

Serão versionados:

- enunciados e esqueletos das katas;
- testes de aceitação;
- soluções de referência mantidas fora do alcance dos participantes durante a coleta;
- arquivo de alocação e semente do sorteio;
- scripts de cronometragem e coleta;
- configurações das ferramentas estáticas;
- manifesto do ambiente e dependências;
- dados brutos e processados;
- scripts/notebooks de análise;
- figuras do dashboard;
- relatório final;
- registro de desvios do protocolo.

Cada trial deverá possuir uma Issue individual no GitHub Projects com participante responsável, kata, tratamento e critérios de aceitação. O commit final deverá mencionar o número da Issue correspondente.

A cadeia mínima de rastreabilidade será:

`Issue → trial_id → commit_sha → saídas brutas → linha no dataset → análise/gráfico`

Dados brutos não serão sobrescritos. Qualquer processamento deverá gerar um novo artefato ou ser inteiramente reproduzível por script.

---

## 18. Critérios de validade de um trial

Um trial será considerado válido quando:

- tiver seguido a alocação pré-registrada;
- tiver duração registrada pelo mecanismo padronizado;
- não tiver usado recurso proibido pelo tratamento;
- preservar o estado final do código;
- possuir saída final dos testes;
- possuir vínculo com Issue e commit;
- não apresentar falha de infraestrutura que impeça a tentativa.

Violações serão classificadas antes da análise como:

- **desvio menor:** não altera diretamente tratamento ou medidas; o trial é mantido com anotação;
- **desvio maior:** compromete tratamento ou medição; o trial é separado da análise principal e apresentado em análise de sensibilidade;
- **falha de infraestrutura:** permite reagendamento conforme a Seção 10.5.

Nenhuma exclusão será decidida com base em o resultado favorecer ou prejudicar uma hipótese.

---

## 19. Artefatos esperados

A execução desta metodologia deverá produzir, no mínimo:

- protocolo metodológico pré-registrado;
- seis pacotes de katas com testes automatizados;
- matriz de equivalência dos três pares;
- arquivo de alocação contrabalanceada;
- manifesto do ambiente;
- script de cronometragem e coleta;
- configuração e script das métricas estáticas;
- 18 códigos finais de trial;
- saídas brutas de testes e métricas;
- dataset consolidado e validado;
- script ou notebook de análise estatística;
- dashboard com gráficos por RQ;
- registro de incidentes e desvios;
- relatório final;
- Issues e commits rastreáveis no GitHub Projects.

---

## 20. Decisões que devem ser preenchidas antes da execução

Os itens abaixo não estão definidos no enunciado e precisam ser registrados pelo grupo antes do primeiro trial:

- linguagem e versão;
- seis katas e respectivos pares de dificuldade;
- assistente de IA, versão/modelo, plano e forma de interação;
- IDE e extensões;
- ferramentas e versões para complexidade, duplicação e LOC;
- limiar e exclusões da ferramenta de duplicação;
- comandos padronizados de teste e coleta;
- data ou janela de execução;
- semente e resultado da alocação aleatória;
- fonte de documentação permitida no tratamento Manual;
- responsável por custodiar soluções de referência e cronograma.

Essas decisões deverão constar também no Relatório Final para permitir reprodução e replicação.
