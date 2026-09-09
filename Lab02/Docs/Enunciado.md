# LAB02 — Laboratório 02

## Informações sobre a avaliação

| Laboratório | Valor |
|---|---:|
| LAB02 | 20 pontos |

### Informações da disciplina

| Curso | Disciplina | Turno | Período / Sala |
|---|---|---|---|
| Engenharia de Software | Laboratório de Experimentação de Software | Noite | 6º |

**Professor:** Danilo Maia

---

## Assistentes de IA vs. codificação manual: um experimento controlado

Ferramentas de IA generativa (GitHub Copilot, ChatGPT, Claude, Gemini etc.) tornaram-se onipresentes no desenvolvimento de software, mas ainda há pouca evidência controlada e reproduzível sobre seu real impacto em produtividade e qualidade — a maior parte do que se ouve é relato anedótico.

Neste laboratório, o objetivo é realizar um experimento controlado para avaliar quantitativamente os efeitos do uso de um assistente de IA na resolução de tarefas de programação.

## Questões de Pesquisa

**RQ1.** O uso de assistente de IA reduz o tempo necessário para resolver uma tarefa de programação?

**RQ2.** O uso de assistente de IA reduz a quantidade de defeitos (testes que falham) no código produzido?

**RQ3.** O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido? As métricas devem ser obtidas por meio do CK — apenas para Java — e/ou PMD. Caso a linguagem escolhida não seja Java, utilize uma ferramenta equivalente, como o Radon.

## GQM (Goal-Question-Metric) e métricas

### Goal

Analisar o uso de assistentes de IA generativa na resolução de tarefas de programação, com o propósito de comparar seu efeito frente à codificação manual, com respeito a tempo de resolução, qualidade funcional (defeitos) e qualidade estrutural do código produzido, do ponto de vista do grupo pesquisador, no contexto de katas de dificuldade equivalente resolvidos por estudantes de graduação sob condições controladas (*crossover within-subject*, com tempo limitado).

As RQ1–RQ3 definidas anteriormente são as *Questions* do GQM. Cabe a cada grupo escolher, entre as métricas candidatas a seguir, quais serão utilizadas para responder a cada RQ. A escolha e sua justificativa devem constar no Desenho do Experimento (Passo 1) e no Relatório Final.

### RQ1 — Tempo

Métricas candidatas:

- **Tempo até passar em todos os testes de aceitação (*time-to-green*):** métrica primária recomendada.
- Um trial que atingir o limite de 35 minutos sem sucesso deve ser registrado como **censurado em 35 minutos**, e não descartado. O descarte distorce a comparação a favor do tratamento com mais falhas.
- **Métrica agregada recomendada:** mediana por tratamento, e não a média, dado o N pequeno (4–6 trials por integrante) e a sensibilidade da média a outliers.
- **Opcional/exploratória:** número de prompts ou interações com o assistente de IA. Não é obrigatória, mas pode ser útil para a discussão qualitativa.

### RQ2 — Defeitos

Métricas candidatas:

- **Taxa de sucesso:** percentual de testes de aceitação passando ao final do limite de tempo. É mais robusta que a contagem bruta, pois normaliza katas com quantidades diferentes de testes.
- **Número absoluto de testes falhando ao final do tempo:** métrica complementar e mais simples de reportar.
- **Opcional:** densidade de defeitos (testes falhando / KLOC), caso sejam comparados katas de tamanhos muito diferentes.

### RQ3 — Estrutura do código

Métricas candidatas:

- **Complexidade ciclomática média (McCabe) por método/função:** obtida com CK (Java, métrica WMC/complexity) ou `radon cc` (Python).
- **Duplicação de código:** percentual de linhas duplicadas, obtido com PMD CPD (Java) ou ferramenta equivalente, como `jscpd` para Python/JavaScript, caso o Radon não cubra duplicação.
- **LOC (linhas de código) como métrica de controle:** obrigatória sempre que forem reportadas complexidade ou duplicação. Código gerado por IA pode ser mais verboso, portanto complexidade e duplicação sem normalização por LOC podem induzir a conclusões equivocadas.
- **Opcional (aprofundamento):** Índice de Manutenibilidade (*Maintainability Index*, disponível em `radon mi`), uma métrica composta por complexidade, LOC e volume de Halstead, mais robusta do que a análise isolada de cada métrica.

> **Robustez estatística:** dado o tamanho amostral reduzido, prefira mediana e IQR (intervalo interquartil) a média e desvio-padrão nas tabelas e nos gráficos descritivos. Na análise inferencial do Passo 4, mantenha o teste de Wilcoxon (não paramétrico), consistente com o desenho *within-subject*.

## Etapas esperadas por sprint

### 1. Desenho do Experimento

Defina, no mínimo:

1. **Hipóteses nula e alternativa.**
2. **Variáveis dependentes:** tempo, número de testes passando e métricas estáticas.
3. **Variável independente:** uso ou não do assistente de IA.
4. **Tratamentos.**
5. **Objetos experimentais:** conjunto de exercícios/katas de dificuldade equivalente.
6. **Tipo de projeto experimental:** recomenda-se o desenho *crossover/within-subject*, contrabalanceado, para controlar a variação individual de habilidade.
7. **Quantidade de medições.**
8. **Ameaças à validade:**
   - efeito de aprendizado entre katas;
   - familiaridade prévia com a ferramenta de IA;
   - vazamento de solução já vista;
   - memorização: quando as katas são muito conhecidas, como exercícios clássicos do LeetCode ou HackerRank, o assistente de IA pode reproduzir uma solução presente em seus dados de treinamento em vez de efetivamente “ajudar”. Para reduzir esse risco, prefira katas autorais do grupo/professor ou exercícios pouco indexados.

### 2. Preparação do Experimento

Escolha **4 ou 6 katas/exercícios de programação de dificuldade comparável**. A quantidade deve ser par para permitir a divisão exata pela metade entre trials com e sem assistente de IA. Podem ser utilizados exercícios do HackerRank, LeetCode, Codewars ou exercícios próprios; dê preferência a exercícios pouco indexados para reduzir o risco de memorização descrito nas ameaças à validade.

Os exercícios devem possuir testes automatizados de aceitação. Prepare o ambiente, incluindo:

- linguagem de programação;
- IDE;
- assistente de IA a ser utilizado;
- cronômetro e registro de tempo;
- scripts de coleta das métricas estáticas.

O grupo deve utilizar o **mesmo assistente de IA em todos os trials**, para que o tratamento seja comparável dentro do próprio experimento. Pode ser utilizado, por exemplo, o GitHub Copilot gratuito por meio do GitHub Student Developer Pack ou a versão gratuita de um chatbot como ChatGPT, Claude ou Gemini.

Fixe também a linguagem de programação das katas de acordo com a ferramenta escolhida para as métricas estáticas. O CK exige Java; para outras linguagens, utilize uma ferramenta equivalente, como o Radon para Python.

### 3. Execução do Experimento

Cada integrante do grupo deve resolver metade dos katas com o assistente de IA habilitado e a outra metade sem o assistente, em ordem contrabalanceada entre os integrantes.

Cada trial deve respeitar o seguinte limite:

> **Time-box fixo: 35 minutos por trial.** O grupo pode reduzir esse limite e justificar a decisão no relatório, mas não pode aumentá-lo, a fim de manter a comparabilidade entre os grupos da turma.

Ao final do tempo, o trial deve ser encerrado independentemente do resultado. Registre:

- o tempo até passar nos testes de aceitação ou até o fim do *time-box*;
- o número de testes passando ao final do tempo;
- as métricas obtidas pela execução do CK/PMD, ou ferramentas equivalentes, sobre o código final de cada trial.

### 4. Análise de Resultados

Revise os dados coletados, identifique outliers e aplique os testes estatísticos adequados. Para o desenho *within-subject*, recomenda-se o teste de Wilcoxon para amostras pareadas.

### 5. Relatório Final

Elabore um documento contendo:

1. introdução com as hipóteses;
2. metodologia detalhada o suficiente para permitir reprodução ou replicação, incluindo ambiente, katas utilizados, assistente de IA e versão;
3. resultados por RQ, com as respostas estatísticas obtidas;
4. discussão final;
5. link do repositório/GitHub Projects do grupo.

**Link do repositório/GitHub Projects:** `<preencher>`

### 6. Dashboard de Visualização

Importe os dados do experimento e gere gráficos com Pandas e Matplotlib/Seaborn, comparando entre os tratamentos:

- tempo;
- taxa de sucesso;
- métricas estáticas.

## Processo de Desenvolvimento

### Contribuição individual por sprint

Em todas as sprints — S01, S02 e S03 —, cada integrante do trio deve ser **Assignee de pelo menos uma Issue com um artefato de código commitado**, como script, notebook, gráfico ou trial de kata. A exigência não se restringe às Issues de execução de katas da S02.

> **A ausência de commits atribuíveis a um integrante em uma sprint zera a parcela individual desse integrante na sprint.**

### Sugestão de divisão de papéis

A divisão abaixo não é obrigatória. O trio pode se organizar de outra forma, desde que a regra de contribuição individual por sprint seja respeitada.

#### S01

- Um integrante escreve o script de cronometragem e coleta de tempo.
- Outro prepara o ambiente e o script de execução das métricas estáticas (CK/PMD ou Radon).
- O terceiro pesquisa e valida os katas — considerando dificuldade comparável e baixa indexação — e redige as hipóteses e ameaças à validade.
- Os três integrantes revisam o desenho em conjunto.

#### S02

Esta sprint já é naturalmente dividida pelo desenho do experimento: cada integrante resolve individualmente todos os katas, metade com IA e metade sem IA, em ordem contrabalanceada.

#### S03

- Um integrante conduz os testes estatísticos de Wilcoxon para RQ1 e RQ2.
- Outro conduz a análise da RQ3, com as métricas estáticas.
- O terceiro monta o dashboard com Pandas e Matplotlib/Seaborn, consolidando os resultados dos três integrantes.

## Entregas e pontuação

| Sprint / Entrega | Entregável | Pontos |
|---|---|---:|
| **Lab02S01** | Desenho do experimento e preparação — Passos 1 e 2: katas escolhidos, ambiente, scripts de medição de tempo e métricas. Os cartões do desenho e da preparação devem constar no Kanban do grupo. | 5 |
| **Lab02S02** | Execução do experimento e coleta de dados — Passo 3. | 5 |
| **Lab02S03** | Análise de resultados — Passo 4, cobrindo RQ1, RQ2 e RQ3 — e Dashboard de Visualização — Passo 6. | 5 |
| **Relatório Final** | Elaboração do documento final — Passo 5, conforme a seção “Relatório Final”. | 5 |
| **Total** |  | **20** |

**Prazo final:** conforme o cronograma da disciplina.

> **Atenção:** poderá haver desconto de até 10% da nota da sprint por qualidade insuficiente do uso do GitHub Projects, incluindo WIP não respeitado, Issues sem Assignee, cartões desatualizados ou ausência de evolução semanal.

## Rastreabilidade no GitHub Projects

Todos os trials devem ser registrados no GitHub Projects do grupo como **Issues individuais**, uma por kata/tratamento, atribuídas ao integrante responsável por meio do campo Assignee. Deve ser mantida a rastreabilidade entre o experimento e o board.

> **A correção é feita a partir do GitHub Projects. Commits sem referência ao número da Issue correspondente não serão considerados.**
