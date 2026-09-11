# Tutorial técnico da Sprint 1

Este documento explica como a infraestrutura experimental do Lab02 está
organizada, o papel de cada arquivo, como executar o que já foi implementado e
como cada artefato atende às tarefas da Sprint 1. Ele também delimita o que
ainda falta antes da coleta oficial.

> **Estado em 10/09/2026:** S01-01 a S01-07 estão implementadas. A infraestrutura
> da S01-08 também está implementada e testada, mas a instalação real ainda deve
> ser executada e registrada por P01, P02 e P03. A S01-09 continua pendente. Os
> 18 trials oficiais não devem começar antes dessas validações externas.

## 1. O que a Sprint 1 prepara

A Sprint 1 transforma o protocolo de pesquisa em uma infraestrutura executável.
O fluxo planejado é:

```text
protocolo congelado
        |
        v
katas + suítes de aceitação + soluções de referência protegidas
        |
        v
pareamento por dificuldade + alocação contrabalanceada
        |
        v
preparação do ambiente + treinamento                 [S01-08 implementada]
        |
        v
execução cronometrada e registro do trial             [S01-05 implementada]
        |
        +--> testes funcionais (RQ1 e RQ2)
        |
        +--> métricas estáticas (RQ3)
        |
        v
dados brutos imutáveis e rastreáveis
```

As responsabilidades são separadas de propósito:

- `scripts/` contém os comandos usados pelas pessoas;
- `src/` contém as regras reutilizáveis e testáveis;
- `tests/` valida a infraestrutura do experimento;
- `katas/` contém os objetos experimentais entregues aos participantes;
- `data/` guarda metadados e resultados;
- `Docs/` registra decisões, evidências e procedimentos.

Essa separação evita que regras importantes fiquem escondidas em comandos
manuais e permite auditar a cadeia `protocolo -> execução -> dado -> análise`.

## 2. Estado das tarefas da Sprint 1

| Task | Estado | Entrega principal |
|---|---|---|
| S01-01 | Concluída | Protocolo, ferramentas e versões congeladas |
| S01-02 | Concluída | Seis katas selecionadas, revisadas e documentadas |
| S01-03 | Concluída | Três pares de dificuldade e referências validadas |
| S01-04 | Concluída | Suítes de aceitação e executor padronizado |
| S01-05 | Concluída | Cronômetro e coletor imutável dos trials |
| S01-06 | Concluída | Coletor de complexidade, LOC, MI e duplicação |
| S01-07 | Concluída | Alocação contrabalanceada congelada dos 18 trials |
| S01-08 | Validação externa pendente | Código, restauração, treinamento e guia prontos; faltam registros das três máquinas |
| S01-09 | Pendente | Kanban, Issues e revisão final de prontidão |

O checklist normativo continua sendo
[`tasks.md`](tasks.md). A tabela acima é apenas um resumo operacional.

## 3. Estrutura do repositório

```text
Lab02/
|-- Docs/                         documentação e evidências metodológicas
|-- data/
|   |-- metadata/                 decisões e planos versionados
|   |-- raw/                      saídas originais, nunca editadas manualmente
|   |-- processed/                dataset futuro da análise
|   |-- project-snapshots/        evidências futuras do board
|   `-- training/                 dados de treinamento fora da amostra
|-- katas/K01..K06/               enunciados, esqueletos e testes das katas
|-- reference-solutions/          referências sob custódia, fora do Git
|-- scripts/                      interfaces de linha de comando
|-- src/                          lógica da infraestrutura
|-- tests/                        testes da própria infraestrutura
|-- training-kata/                exercício de treinamento fora da amostra
|-- trials/                       código final preservado de cada trial
|-- .jscpd.json                   regra global de detecção de duplicação
|-- radon.cfg                     configuração global do Radon
|-- requirements.txt              dependências Python completas e fixadas
|-- requirements.lock             resolução transitiva Python com hashes
|-- requirements-metrics.txt      subconjunto usado pela coleta estática
|-- package.json/package-lock.json versão Node da ferramenta de duplicação
`-- pytest.ini                    configuração do pytest
```

Arquivos `.gitkeep` não implementam comportamento. Eles apenas fazem o Git
preservar diretórios que serão preenchidos em tarefas posteriores.

## 4. Catálogo dos arquivos e diretórios

### 4.1 Documentação

| Arquivo | Responsabilidade |
|---|---|
| [`Docs/Enunciado.md`](Enunciado.md) | Requisitos originais, questões de pesquisa e critérios da disciplina. |
| [`Docs/methodology.md`](methodology.md) | Desenho experimental: participantes, tratamentos, blocos, métricas, hipóteses e análise. |
| [`Docs/protocol-decisions.md`](protocol-decisions.md) | Decisões congeladas, versões permitidas, regras dos tratamentos e registro de desvios. |
| [`Docs/tasks.md`](tasks.md) | Backlog completo e checklist de aceitação de cada task. |
| [`Docs/katas.md`](katas.md) | Seleção das seis katas, familiaridade, baixa indexação, clareza e compatibilidade com 35 minutos. |
| [`Docs/kata-equivalence.md`](kata-equivalence.md) | Formação dos pares B1, B2 e B3 e limitações da equivalência. |
| [`Docs/README.md`](README.md) | Índice de entrada da documentação. |
| [`Docs/execution-guide.md`](execution-guide.md) | Procedimento ponta a ponta de instalação, treinamento, preparação e coleta. |

As subpastas `Docs/dataset/`, `Docs/templates/` e `Docs/validation/` estão
reservadas para esquemas, modelos e evidências das próximas sprints.

### 4.2 Configuração da raiz

| Arquivo | O que controla |
|---|---|
| [`README.md`](../README.md) | Visão geral e mapa de entrada do projeto. |
| [`.gitignore`](../.gitignore) | Impede o versionamento de ambientes, caches, relatórios temporários e das soluções de referência protegidas. |
| [`pytest.ini`](../pytest.ini) | Descoberta e comportamento comum dos testes Python. |
| [`radon.cfg`](../radon.cfg) | Exibição de complexidade e índice de manutenibilidade pelo Radon. |
| [`.jscpd.json`](../.jscpd.json) | Analisa Python, exige ao menos 5 linhas e 50 tokens, usa modo `mild` e ignora testes, dependências e artefatos. |
| [`requirements.txt`](../requirements.txt) | Fixa pytest 9.1.1 e Radon 6.0.1 para o ambiente completo. |
| [`requirements.lock`](../requirements.lock) | Congela dependências transitivas e hashes para instalação repetível. |
| [`requirements-metrics.txt`](../requirements-metrics.txt) | Mantém o subconjunto mínimo do coletor estático. |
| [`package.json`](../package.json) | Declara o JSCPD 5.2.0 como dependência de desenvolvimento. |
| [`package-lock.json`](../package-lock.json) | Congela a árvore exata de dependências Node para instalação repetível. |

### 4.3 Katas experimentais

Cada diretório de `katas/K01` a `katas/K06` repete o mesmo contrato:

| Caminho por kata | Função |
|---|---|
| `README.md` | Enunciado entregue ao participante, entradas, saídas, restrições e exemplos. |
| `src/solution.py` | Esqueleto inicial. Ele lança `NotImplementedError` até ser implementado no trial. |
| `tests/conftest.py` | Lê `KATA_SRC_DIR` e direciona o teste para o código correto. |
| `tests/test_kNN.py` | Casos públicos e de borda que medem a correção funcional. |
| `config/.gitkeep` | Reserva um local para eventual configuração específica. |

As seis katas são:

| Kata | Problema | Bloco equivalente |
|---|---|---|
| K01 | Conflitos no pátio de docas | B1, pareada com K02 |
| K02 | Compartimentos de coleta | B1, pareada com K01 |
| K03 | Cadeia de custódia de remessas | B2, pareada com K04 |
| K04 | Credenciais de visita | B2, pareada com K03 |
| K05 | Alertas de leitura persistente | B3, pareada com K06 |
| K06 | Roteiros de inspeção | B3, pareada com K05 |

O catálogo geral está em [`katas/README.md`](../katas/README.md). As referências
corretas ficam localmente em `reference-solutions/K01` a `K06`, são ignoradas
pelo Git e não podem existir no clone usado pelo participante. O arquivo
[`reference-solutions/README.md`](../reference-solutions/README.md) documenta
essa custódia; somente hashes e evidências de validação são versionados.

### 4.4 Scripts executáveis

| Arquivo | Responsabilidade | Task |
|---|---|---|
| [`scripts/run_tests.py`](../scripts/run_tests.py) | Executa uma suíte isolada, produz JUnit XML e resume total, aprovados e falhas. | S01-04 |
| [`scripts/collect_static_metrics.py`](../scripts/collect_static_metrics.py) | Interpreta argumentos e chama o coletor de métricas para um `trial_id`. | S01-06 |
| [`scripts/generate_allocation.py`](../scripts/generate_allocation.py) | Gera, congela ou audita a alocação dos 18 trials. | S01-07 |
| [`scripts/README.md`](../scripts/README.md) | Referência curta dos comandos disponíveis. | Geral |
| [`scripts/run_trial.py`](../scripts/run_trial.py) | Cronometra, verifica e preserva o resultado bruto do trial. | S01-05 |
| [`scripts/setup.ps1`](../scripts/setup.ps1) | Instala, sincroniza, verifica e registra o ambiente de cada participante. | S01-08 |
| [`scripts/verify_environment.py`](../scripts/verify_environment.py) | Coleta versões, SO, hardware e extensões e confronta o protocolo. | S01-08 |
| [`scripts/prepare_trial.py`](../scripts/prepare_trial.py) | Cria ou restaura uma cópia limpa validada pela alocação. | S01-08 |
| [`scripts/verify_treatment.py`](../scripts/verify_treatment.py) | Confere extensões, Codex/processos e preserva evidência do tratamento. | S01-08 |

Os scripts são camadas finas: recebem parâmetros, apresentam erros e chamam a
lógica de `src/`. Assim, as regras importantes podem ser testadas sem iniciar
um processo de terminal completo.

### 4.5 Código de apoio em `src`

| Caminho | Responsabilidade atual |
|---|---|
| [`src/collection/allocation.py`](../src/collection/allocation.py) | Algoritmo determinístico, validações, leitura e congelamento da alocação. |
| [`src/collection/trial_collector.py`](../src/collection/trial_collector.py) | Cronometragem, censura, execução da suíte e gravação imutável do trial. |
| [`src/collection/trial_preparation.py`](../src/collection/trial_preparation.py) | Preparação/restauração segura do código conforme a alocação. |
| [`src/metrics/static_metrics.py`](../src/metrics/static_metrics.py) | Descoberta de arquivos, validação de versões, execução do Radon/JSCPD e consolidação JSON. |
| [`src/environment.py`](../src/environment.py) | Versões esperadas, inventário de máquina e validação dos tratamentos. |
| [`src/metrics/README.md`](../src/metrics/README.md) | Contrato e interpretação das saídas do coletor estático. |
| [`src/README.md`](../src/README.md) | Define as responsabilidades arquiteturais planejadas. |
| `src/collection/__init__.py` e `src/metrics/__init__.py` | Tornam os diretórios pacotes Python. |
| `src/analysis/`, `dashboard/`, `processing/`, `validation/` | Apenas reservados por `.gitkeep`; serão implementados nas próximas sprints. |

Diretórios `__pycache__` e arquivos `.pyc` são caches locais do Python. Eles
não são código-fonte nem evidência experimental e não devem ser commitados.

### 4.6 Testes da infraestrutura

Os arquivos de `tests/` não resolvem as katas; eles verificam se a plataforma
experimental cumpre suas regras:

| Arquivo | O que garante |
|---|---|
| [`tests/test_kata_equivalence.py`](../tests/test_kata_equivalence.py) | Integridade dos pares, das referências e das evidências de validação. |
| [`tests/test_static_metrics.py`](../tests/test_static_metrics.py) | Exclusões, consolidação, falhas esperadas e proteção contra sobrescrita das métricas. |
| [`tests/test_allocation.py`](../tests/test_allocation.py) | Reprodutibilidade, balanço, blocos, posições e congelamento da alocação. |
| [`tests/test_trial_collector.py`](../tests/test_trial_collector.py) | Sucesso, censura, incidentes e imutabilidade da coleta cronometrada. |
| [`tests/test_trial_preparation.py`](../tests/test_trial_preparation.py) | Cópia limpa, restauração sem resíduos e proteção da evidência bruta. |
| [`tests/test_environment.py`](../tests/test_environment.py) | Versões, registro de P01–P03, extensões e controles IA/Manual. |
| [`tests/test_training_kata.py`](../tests/test_training_kata.py) | Falha do esqueleto, sucesso de uma referência e independência temática. |
| [`tests/README.md`](../tests/README.md) | Escopo da suíte de infraestrutura. |

Os testes dentro de `katas/KNN/tests/` medem as soluções dos participantes; os
testes em `tests/` medem a confiabilidade da infraestrutura. Essa diferença é
importante ao interpretar um resultado.

### 4.7 Dados e evidências

| Arquivo ou pasta | Conteúdo |
|---|---|
| [`data/metadata/protocol.json`](../data/metadata/protocol.json) | Protocolo legível por máquina, versões, IDE, IA e janela de execução. |
| [`data/metadata/kata-equivalence.csv`](../data/metadata/kata-equivalence.csv) | Medidas objetivas usadas para formar B1, B2 e B3. |
| [`data/metadata/reference-solutions-validation.json`](../data/metadata/reference-solutions-validation.json) | Resultado 33/33 e hashes das referências validadas. |
| [`data/metadata/allocation.csv`](../data/metadata/allocation.csv) | Plano congelado: `trial_id`, participante, posição, kata, bloco e tratamento. |
| [`data/metadata/allocation-metadata.json`](../data/metadata/allocation-metadata.json) | Semente, versão do algoritmo, data, quantidade e SHA-256 do CSV. |
| [`data/metadata/static-metrics-sanity.json`](../data/metadata/static-metrics-sanity.json) | Resumo da coleta de sanidade feita sobre K01–K06. |
| [`data/metadata/environment.json`](../data/metadata/environment.json) | Versões esperadas e inventários reais de P01, P02 e P03. |
| `data/raw/metrics/sanity-KNN/` | Relatórios originais do Radon/JSCPD e consolidados das referências. |
| `data/raw/metrics/<trial_id>/` | Destino futuro das métricas de cada trial oficial. |
| `data/raw/trials/` | Destino futuro de horários, duração, censura e resultado dos testes. |
| `data/processed/` | Destino futuro do dataset consolidado; não deve receber edição manual. |
| `data/training/` | Evidências de treinamento, sempre excluídas do dataset oficial. |

Veja também [`data/README.md`](../data/README.md). Dados brutos são imutáveis:
se um registro estiver errado, preserve o original, registre o desvio e faça a
correção reproduzível na camada processada.

## 5. Preparação e verificação do ambiente

As versões congeladas são Python 3.12.14, uv 0.12.10, pytest 9.1.1, Radon
6.0.1, Node 24.19.0, npm 11.17.0, JSCPD 5.2.0, VS Code 1.137.0 x64 e Codex CLI
0.154.0 com o modelo `gpt-5.3-codex`.

No PowerShell, a preparação disponível hoje é:

```powershell
uv venv --python 3.12.14
uv pip sync --python .venv\Scripts\python.exe requirements.lock
npm install --ignore-scripts
```

Depois, valide a infraestrutura:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

O comando oficial e completo está em `scripts/setup.ps1`. A instalação só fica
comprovada quando cada participante o executa e seu inventário aparece como
válido em `data/metadata/environment.json`.

## 6. Como executar as suítes das katas

Para testar o esqueleto de K01:

```powershell
.venv\Scripts\python.exe scripts\run_tests.py K01
```

O resultado esperado para o esqueleto é falha por `NotImplementedError`. Isso
comprova que uma solução vazia não passa indevidamente.

Para testar uma referência, somente o custodiante e fora de um trial:

```powershell
.venv\Scripts\python.exe scripts\run_tests.py K01 --src reference-solutions\K01
```

O script define `KATA_SRC_DIR`, inicia o pytest em processo separado e escreve
`.reports/K01_junit.xml`. O isolamento é obrigatório porque todas as katas
importam um módulo chamado `solution`; executar várias suítes no mesmo processo
poderia reutilizar o módulo errado do cache de imports.

Para validar todas as referências, repita o comando para K01 até K06. A
evidência já registrada informa 33 testes aprovados em 33.

## 7. Como auditar a alocação dos trials

O comando normal é:

```powershell
.venv\Scripts\python.exe scripts\generate_allocation.py
```

Ele usa a semente `20260910`. Na primeira execução, grava o CSV e os metadados;
nas seguintes, aceita apenas conteúdo idêntico. Para conferir sem escrever:

```powershell
.venv\Scripts\python.exe scripts\generate_allocation.py --check
```

O algoritmo garante:

- 18 `trial_id` únicos;
- seis posições por participante;
- três tratamentos `ai` e três `manual` para cada pessoa;
- presença dos dois tratamentos em cada bloco B1, B2 e B3;
- separação das duas katas do mesmo par;
- exposição de cada kata aos dois tratamentos no grupo;
- reprodução exata a partir da mesma semente.

A desigualdade de 2 contra 1 por kata é inevitável com três participantes.
K01, K04 e K06 aparecem duas vezes com IA; K02, K03 e K05 aparecem duas vezes
no tratamento manual. A comparação continua balanceada por participante e por
bloco.

O CSV completo deve ficar com o custodiante. Durante a coleta, revele ao
participante apenas a próxima linha que ele executará, evitando antecipação e
treino direcionado.

## 8. Como coletar métricas estáticas

Para um trial cujo código final esteja em `trials/P01-K01-ai/src`:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py P01-K01-ai
```

Para apontar outro código de produção:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py sanity-local --source caminho\para\src
```

O coletor executa três modos do Radon e o JSCPD:

1. `radon cc` mede a complexidade ciclomática por função ou método;
2. `radon raw` mede linhas físicas, lógicas, SLOC, comentários e linhas vazias;
3. `radon mi` calcula o índice de manutenibilidade por arquivo;
4. JSCPD identifica blocos duplicados segundo `.jscpd.json`.

Antes de executar, o código valida as versões das ferramentas e calcula hashes
das configurações. Somente arquivos Python de produção entram na análise.
Testes, `conftest.py`, ambientes virtuais, dependências, caches, arquivos
gerados, `dist`, `build` e configurações são excluídos.

Cada coleta cria `data/raw/metrics/<trial_id>/` com:

| Saída | Interpretação |
|---|---|
| `radon-cc.json` | Registros detalhados de complexidade. |
| `radon-raw.json` | Contagens de linhas por arquivo. |
| `radon-mi.json` | Índice de manutenibilidade por arquivo. |
| `jscpd/jscpd-report.json` | Relatório bruto de duplicação. |
| `jscpd-stdout.txt` | Saída operacional da ferramenta. |
| `metrics.json` | Resultado consolidado do trial e metadados de reprodução. |

No consolidado:

- `loc` significa SLOC do Radon, não o total físico de linhas;
- `complexity` preserva quantidade, média, máximo e itens individuais;
- `maintainability_index` é a média aritmética entre arquivos;
- `duplication` preserva blocos, linhas duplicadas e percentual;
- ausência de funções produz complexidade `null` e `missing = true`, nunca zero.

O diretório de saída deve ser novo. A recusa de sobrescrita protege o dado
bruto e impede que uma segunda medição apague a primeira.

## 9. Como o código cumpre cada task concluída

### S01-01 — Decisões do experimento

- decisões humanas estão em `Docs/protocol-decisions.md`;
- especificação científica está em `Docs/methodology.md`;
- cópia processável está em `data/metadata/protocol.json`;
- linguagem, IDE, testes, IA, versões, datas e regras dos tratamentos foram
  preenchidos;
- desvios futuros possuem local explícito de registro.

### S01-02 — Seleção das katas

- existem exatamente K01–K06, todas locais e sem serviço externo;
- P01, P02 e P03 declararam não conhecer as seis katas;
- buscas de baixa indexação foram repetidas em 10/09/2026;
- contratos, casos de borda e ausência de pistas foram revisados;
- a compatibilidade com 35 minutos foi avaliada por inspeção independente.

Essa última evidência é uma limitação: foi usada inspeção porque ainda não
havia o cronômetro da S01-05 para um piloto humano instrumentado.

### S01-03 — Equivalência

- B1 = K01/K02, B2 = K03/K04 e B3 = K05/K06;
- regras, testes, SLOC, complexidade e estimativa de tempo estão tabulados;
- referências atingiram 33/33 testes;
- seus hashes são auditáveis, mas o código permanece fora do Git;
- as limitações do pareamento estão documentadas.

### S01-04 — Testes de aceitação

- cada kata possui suíte determinística;
- todos os esqueletos falham pelo motivo esperado;
- referências passam integralmente;
- `run_tests.py` informa total, aprovados e falhas via JUnit XML;
- uma nova execução isolada evita colisão entre módulos `solution`.

### S01-05 — Cronômetro e coletor

- mede o trial até a primeira suíte verde ou 2.100 segundos;
- preserva horários com fuso, duração, censura, tentativas e totais finais;
- grava incidentes de infraestrutura com mensagem explícita;
- recusa sobrescrever um trial já coletado;
- possui testes com relógio falso, sem esperar 35 minutos reais.

### S01-06 — Métricas estáticas

- Radon coleta CC, LOC e MI;
- JSCPD coleta linhas e percentual duplicado;
- filtros impedem a contagem de código que não é de produção;
- configurações e versões fixas tornam trials comparáveis;
- JSON bruto e consolidado mantêm rastreabilidade;
- K01–K06 passaram pelo teste de sanidade registrado.

### S01-07 — Contrabalanceamento

- a semente fixa reproduz a ordem;
- as restrições metodológicas são verificadas em testes;
- o plano contém 18 trials e três usos de cada tratamento por pessoa;
- o hash detecta alteração posterior no CSV;
- a operação de congelamento recusa substituição divergente.

## 10. O que ainda falta antes dos trials oficiais

### S01-08 — Ambiente reproduzível

O código da task está pronto. P01, P02 e P03 ainda precisam executar
`scripts/setup.ps1` nas próprias máquinas. Isso preencherá SO, hardware,
runtime, IDE, extensões e versões reais em `data/metadata/environment.json`.
Somente depois de o registro atingir `status: verified` será possível comprovar
a instalação do zero e a igualdade dos três ambientes.

### S01-09 — Prontidão e governança

Ainda é necessário conferir Issues, labels, iteração, responsáveis, os 18
cards de trials, contribuição individual e aprovação formal do protocolo. O
board deve refletir o repositório e nenhum checklist obrigatório pode permanecer
aberto.

## 11. Fluxo recomendado para contribuir agora

1. Leia `Docs/protocol-decisions.md` e não altere uma decisão congelada sem
   registrar um desvio.
2. Crie uma branch e uma Issue para a task em andamento.
3. Mantenha interfaces de terminal em `scripts/` e regras testáveis em `src/`.
4. Adicione ou ajuste testes da infraestrutura em `tests/`.
5. Execute `python -m pytest tests -q` no ambiente congelado.
6. Se mexer na alocação, execute `generate_allocation.py --check`; não edite o
   CSV manualmente.
7. Se mexer nas métricas, use um `trial_id` de teste novo; não apague uma saída
   bruta para reutilizar o nome.
8. Atualize `Docs/tasks.md` somente quando houver implementação e evidência para
   todos os critérios marcados.
9. Nunca publique as soluções de referência nem mostre a alocação futura aos
   participantes.

Depois da captura das três máquinas e da S01-09, este tutorial deve receber a
data final de prontidão. O guia operacional será a lista curta usada durante o
trial; este documento continuará como explicação técnica e material de
onboarding da equipe.
