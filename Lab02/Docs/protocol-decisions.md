# Decisões do protocolo

**Task:** S01-01 — Pré-registrar as decisões do experimento
**Data de congelamento:** 09/09/2026

**Versões do ambiente congeladas em:** 10/09/2026

Este documento reúne as decisões metodológicas que o enunciado não fecha
sozinho e que, segundo `methodology.md`, precisam ser congeladas antes do
primeiro trial. Ele também é o local onde qualquer desvio do protocolo
durante a coleta deve ser registrado (ver seção 3).

## 1. Decisões fechadas

### 1.1 Linguagem e ferramentas de métricas estáticas

O grupo decidiu usar **Python** nas seis katas. Isso permite medir tudo com a
mesma cadeia de ferramentas: `radon cc` para complexidade ciclomática,
`radon raw` para LOC, `radon mi` para o Índice de Manutenibilidade e `jscpd`
para duplicação de código. Essa decisão está registrada em
[`methodology.md`, Seção 9](methodology.md#9-ambiente-experimental).

As versões abaixo ficam congeladas para todos os trials. A disponibilidade
delas foi verificada em 10/09/2026 durante a preparação; a S01-08 deverá
instalar e confirmar exatamente as mesmas versões nas três máquinas antes da
coleta.

| Componente | Versão congelada | Finalidade |
|---|---:|---|
| Python | 3.12.14 | Runtime das katas e dos scripts de coleta |
| pytest | 9.1.1 | Execução dos testes de aceitação |
| Radon | 6.0.1 | Complexidade (`cc`), LOC (`raw`) e manutenibilidade (`mi`) |
| JSCPD | 5.2.0 | Detecção de duplicação |
| Node.js | 24.19.0 | Runtime do JSCPD e do Codex CLI |
| npm | 11.17.0 | Instalação das ferramentas Node.js |
| uv | 0.12.10 | Gerenciamento do runtime e das dependências Python |

Os comandos de instalação e de verificação serão centralizados pela S01-08.
Qualquer diferença de versão durante a coleta deverá ser corrigida antes do
trial ou registrada como desvio na Seção 3.

### 1.2 Assistente de IA do tratamento IA

O grupo vai usar o **Codex CLI** (OpenAI), no plano **ChatGPT Pro**. A
escolha foi prática: dos assistentes disponíveis, é o único que os três
integrantes já têm com acesso pago, o que evita depender de cota gratuita ou
misturar assistentes diferentes entre participantes — algo que a metodologia
exige que seja evitado (Seção 6.1).

A interação acontece por chat/agente no terminal; o Codex CLI não tem
autocomplete inline em editor, então esse modo não se aplica aqui. Ficam
congelados o **Codex CLI 0.154.0** e o modelo **`gpt-5.3-codex`**, com acesso
via ChatGPT Pro. A disponibilidade do modelo foi conferida em 10/09/2026 na
[documentação oficial da OpenAI](https://developers.openai.com/api/docs/models/gpt-5.3-codex).
Atualizações automáticas da CLI deverão ser desabilitadas ou revertidas antes
de um trial para preservar a configuração definida.

### 1.3 IDE e extensões

O grupo vai usar **Visual Studio Code**, por ser a IDE que todos os três já
usam no dia a dia — reduz a chance de o trial medir familiaridade com a
ferramenta em vez do efeito da IA.

Extensões permitidas: `ms-python.python` e `ms-python.vscode-pylance`
(suporte oficial a Python — execução, depuração e navegação/checagem de
tipo, que conta como "completação não generativa" permitida pela Seção 6.2).
Nenhuma outra extensão fica habilitada.

Ficam **proibidas** extensões de IA generativa no editor — GitHub Copilot,
Copilot Chat, Tabnine, Codeium, Continue ou qualquer equivalente — mesmo no
tratamento IA, porque o único assistente autorizado é o Codex CLI rodando no
terminal integrado do VS Code (Seção 6.1). Ter uma extensão generativa
instalada quebraria o controle do tratamento Manual e duplicaria o
assistente no tratamento IA. Antes do primeiro trial, cada participante deve
conferir a lista de extensões instaladas e remover qualquer uma fora dessa
lista.

### 1.4 Framework de testes

O grupo confirmou **pytest**. Justificativa:

- É o padrão de fato para testes em Python e tem sintaxe mais enxuta que
  `unittest`, o que importa porque quem escreve as suítes de aceitação é a
  equipe de preparação, não o participante durante o trial.
- A saída (`pytest -q`, ou o plugin `pytest-json-report`) dá contagem de
  testes passando/falhando de forma estruturada, o que facilita a coleta
  automática da métrica de RQ2 (taxa de sucesso / testes falhando).
- Fica no mesmo ecossistema Python já decidido para as métricas estáticas,
  sem exigir runtime ou dependência fora desse conjunto.

Foi congelado o **pytest 9.1.1**, conforme o registro completo do ambiente na
Seção 1.1 e na Seção 9 de `methodology.md`.

### 1.5 Janela de execução

Entrega da Lab02S02 confirmada para **17/09/2026** (quinta-feira). A partir
de hoje (09/09), restam 8 dias corridos — e nesse período ainda faltam
fechar oito tasks de S01 além desta (S01-02 a S01-09: katas, equivalência
dos blocos, testes de aceitação, cronômetro/coletor, coleta de métricas,
alocação contrabalanceada, ambiente reproduzível e revisão de prontidão)
antes de qualquer trial poder começar. É um prazo apertado; a proposta
abaixo só funciona se a infraestrutura de S01 for paralelizada entre os três
integrantes em vez de feita em sequência.

| Dias | Foco |
|---|---|
| 09/09 (qua) – 11/09 (sex) | Fechar o restante de S01: mergear a PR das katas com as declarações de familiaridade preenchidas, validar equivalência B1/B2/B3, escrever os testes de aceitação, implementar cronômetro/coletor e coleta de métricas estáticas, definir a alocação contrabalanceada, montar o ambiente (VS Code, Python, pytest, radon, jscpd, Codex CLI) com versões travadas. Dividir essas frentes entre os três para rodar em paralelo. |
| 12/09 (sáb) | Kata de treinamento (S02-01): todos praticam cronômetro, ambiente e regras dos dois tratamentos sem usar nenhuma kata experimental. |
| 13/09 (dom) – 15/09 (ter) | Execução dos 18 trials (S02-02 a S02-04): cada participante resolve as 6 katas na ordem contrabalanceada definida, 3 com IA e 3 manual. Recomenda-se pelo menos 2 sessões por pessoa em dias diferentes, não os 6 trials seguidos no mesmo dia, para reduzir fadiga e efeito de aprendizado dentro da mesma sessão. |
| 16/09 (qua) | Consolidar o dataset bruto, validar schema/qualidade e auditar a execução (S02-05, S02-06). Qualquer trial com problema ou desvio precisa estar registrado na Seção 3 deste documento antes de fechar a sprint. |
| 17/09 (qui) | Entrega da Lab02S02. |

Esse cronograma não tem dia de folga. Se a infraestrutura de S01 não
estiver pronta até o fim de 11/09, o grupo deve cortar escopo (por exemplo,
reduzir a validação de equivalência ao mínimo aceitável) ou registrar um
desvio formal de prazo, em vez de comprimir ainda mais a janela de coleta.

## 2. Decisões ainda pendentes

Nenhuma decisão desta lista original permanece em aberto. Itens que ainda
exigem trabalho de execução (não de decisão) — testes de aceitação,
cronômetro/coletor, alocação contrabalanceada, ambiente montado com versões
travadas — estão listados nas tasks S01-02 a S01-09 de `tasks.md`.

As fontes de documentação do tratamento Manual já estão definidas em
`methodology.md`, Seção 6.2 (documentação oficial da linguagem e das
bibliotecas, assinatura local de APIs, mensagens do compilador/linter/testes)
— não é preciso repetir aqui, só respeitar essa lista.

## 3. Registro de desvios do protocolo

Qualquer mudança em relação ao que está congelado aqui ou em
`methodology.md`, depois que a coleta começar, deve ser registrada nesta
tabela antes de continuar os trials.

| Data | O que estava definido | O que mudou | Motivo | Quem registrou |
|---|---|---|---|---|
| — | — | — | — | — |

Tabela vazia até o momento — nenhum desvio ocorreu.
