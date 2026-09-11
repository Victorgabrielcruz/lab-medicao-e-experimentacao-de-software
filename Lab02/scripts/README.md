# Scripts

Pontos de entrada previstos:

- preparação e restauração do ambiente;
- geração da alocação contrabalanceada;
- execução cronometrada de trials;
- execução padronizada dos testes;
- coleta de métricas estáticas;
- construção e validação do dataset;
- análise estatística e geração do dashboard.

Os scripts devem apenas orquestrar regras implementadas e testadas em `src/` sempre que a lógica ultrapassar uma operação simples.

## `setup.ps1` e `verify_environment.py` (S01-08)

Preparam o ambiente congelado e registram SO, hardware, ferramentas e
extensões de P01, P02 ou P03:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01
```

Use `-InstallSystemTools` numa máquina nova e `-VerifyOnly` para auditar uma
instalação existente. Os registros válidos são consolidados em
`data/metadata/environment.json`.

## `prepare_trial.py` e `verify_treatment.py` (S01-08)

Preparam uma cópia limpa somente se ela corresponder à alocação congelada:

```powershell
.venv\Scripts\python.exe scripts\prepare_trial.py P01 K01 ai
.venv\Scripts\python.exe scripts\verify_treatment.py ai --trial-dir trials\P01-K01-ai
```

Uma restauração exige `--restore` e é recusada depois que existir evidência
bruta. No tratamento Manual, feche o Codex e use
`--confirm-manual-no-ai`. O procedimento completo está em
`Docs/execution-guide.md`.

## `generate_allocation.py` (S01-07)

Gera e congela os 18 trials usando a semente pré-registrada `20260910`:

```powershell
python scripts/generate_allocation.py
```

O comando cria `data/metadata/allocation.csv` e
`data/metadata/allocation-metadata.json`. Se o CSV já existir, somente uma
alocação byte a byte idêntica e com os mesmos metadados será aceita; qualquer
tentativa de substituição é recusada.

Para auditar o arquivo congelado sem modificá-lo:

```powershell
python scripts/generate_allocation.py --check
```

O gerador preserva as sequências de tratamento da metodologia, três trials de
cada tratamento por participante, os dois tratamentos em cada bloco, ordens
diferentes, separação entre katas do mesmo par e exposição de todas as katas
aos dois tratamentos no conjunto do grupo.

## `run_tests.py` (S01-04)

Execução padronizada dos testes de aceitação de uma kata:

```bash
python scripts/run_tests.py K01
```

Por padrão testa `katas/K01/src/`. Para validar a suíte contra a solução de
referência (uso interno da equipe, nunca durante um trial):

```bash
python scripts/run_tests.py K01 --src reference-solutions/K01
```

Gera um relatório JUnit XML em `.reports/<KATA>_junit.xml` (ignorado pelo
git) e imprime total de testes, quantos passaram e quantos falharam. Roda
sempre uma kata por vez, em processo isolado — não colete testes de várias
katas no mesmo comando `pytest`, porque todas usam o nome de módulo
`solution` e um processo só resolveria o primeiro que importar.

## `run_trial.py` (S01-05)

Cronometra e registra um trial de aceitação:

```bash
python scripts/run_trial.py P01 K01 ai
```

Por padrão cronometra `katas/K01/src/` contra `katas/K01/tests/`. `treatment`
deve ser `ai` ou `manual`. O script roda a suíte em segundo plano a cada
`--poll-interval-seconds` (default 5s) até todos os testes passarem ou até
`--time-limit-seconds` (default 2.100s / 35 min) ser atingido — o que ocorrer
primeiro — e grava o registro em
`data/raw/trials/<participante>-<kata>-<tratamento>/`:

- `final_junit.xml`: saída bruta da verificação final da suíte;
- `trial.json`: horários de início/fim com fuso, duração em segundos,
  `completed`/`censored`, totais de testes e o log de cada checagem.

Um trial já coletado nunca é sobrescrito. Um encerramento inesperado (falha
ao rodar a suíte ou interrupção manual) grava `incident.json` com uma
mensagem clara em vez do registro do trial. Lógica cronometrada e testável
em `src/collection/trial_collector.py`.

## `collect_static_metrics.py` (S01-06)

Instale as dependências congeladas antes da primeira coleta:

```powershell
uv venv --python 3.12.14
uv pip install --python .venv\Scripts\python.exe -r requirements-metrics.txt
npm install --ignore-scripts
```

Colete um trial cujo código final esteja em `trials/<trial_id>/src`:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py P01-K01-ai
```

Para indicar explicitamente outro diretório de produção, como no teste de
sanidade das referências:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py sanity-K01 --source reference-solutions/K01
```

A configuração é fixa em `radon.cfg` e `.jscpd.json`: Radon 6.0.1, JSCPD
5.2.0, duplicações com no mínimo 5 linhas e 50 tokens em modo `mild`. O script
também exige Python 3.12.14 e recusa versões divergentes. Testes, dependências,
código gerado e arquivos de configuração não entram na análise.
