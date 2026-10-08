# Lab03 — Mineração de métricas DORA

[![Lab03 CI](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml/badge.svg?branch=main)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml)

Cálculo das quatro métricas DORA (deployment frequency, lead time, change failure rate e tempo de recuperação) a partir de dados públicos de repositórios open-source que usam GitHub Actions. A coleta é feita por script próprio sobre as APIs REST/GraphQL do GitHub, sem PyGithub.

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/definicoes-operacionais.md`](docs/definicoes-operacionais.md) | Janela de observação, definição de deploy, regras de runs, critério de inclusão, filtro de Actions, metadados e tabela de classificação DORA (C1) |

## Como executar

Requer Python 3.11 ou superior. Use o Python do ambiente virtual para garantir
que as dependências instaladas sejam as mesmas usadas na execução.

No Linux/macOS:

```bash
cd Lab03
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export GITHUB_TOKEN=<seu token>
python -m pipeline --config config.yaml
```

No Windows (Prompt de Comando ou PowerShell), prepare o ambiente:

```powershell
cd Lab03
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Defina o token no mesmo terminal: no Prompt de Comando, use
`set GITHUB_TOKEN=seu_token`; no PowerShell, use
`$env:GITHUB_TOKEN = "seu_token"`. Execute usando diretamente o Python do ambiente:

```powershell
.\.venv\Scripts\python.exe -m pipeline --config config.yaml
```

Esse caminho funciona sem ativar o ambiente virtual. Ao executar só uma etapa,
mantenha o mesmo executável, por exemplo:

```powershell
.\.venv\Scripts\python.exe -m pipeline --config config.yaml --etapas workflow_runs
```

O token é lido apenas da variável de ambiente `GITHUB_TOKEN` e nunca deve ser versionado.

Para executar só algumas etapas: `python -m pipeline --config config.yaml --etapas metadados`.

### Cache e retomada (S01-16)

As respostas GET da API são salvas em JSON em `caminhos.cache` (padrão:
`data/cache`), separadas por API e repositório. Cada endpoint, combinação de
parâmetros e página tem sua própria entrada, inclusive na Search API. Os headers
necessários à paginação (`Link`) são preservados; o token e os headers de
autenticação não são gravados.

Se a coleta falhar, execute novamente o mesmo comando: as consultas já
concluídas são lidas do disco e as demais voltam à API. A gravação usa um arquivo
temporário e substituição atômica para evitar JSON parcial. Erros HTTP e buscas
com `incomplete_results` não são armazenados; entradas de resposta corrompidas
geram aviso e são consultadas novamente. O cache de metadados já existente é
mantido e também usa gravação atômica.

O cache não expira automaticamente. Para atualizar dados ou alterar a janela de
observação, limpe-o antes de iniciar uma nova coleta:

```bash
python -m pipeline --config config.yaml --limpar-cache
python -m pipeline --config config.yaml
```

O primeiro comando remove apenas os JSON das áreas `respostas/` e `metadados/`
do cache configurado e encerra, sem exigir token nem acessar a API. Os dados
brutos e processados são preservados. O cache local não é versionado no Git.

### Rate limit e backoff (S01-17)

O cliente HTTP trata as falhas temporárias automaticamente em todas as etapas:

- Lê `X-RateLimit-Remaining` e `X-RateLimit-Reset` das respostas da API. Quando
  a cota chega a zero, aguarda até o reset (timestamp Unix em UTC), mais 1 segundo
  de margem, antes da próxima consulta ao mesmo recurso. As cotas `core` e
  `search` são acompanhadas separadamente. Uma resposta bem-sucedida é devolvida
  imediatamente; leituras do cache continuam disponíveis durante esse período.
- Em respostas `403`/`429` de rate limit, repete a mesma consulta após a espera.
  `Retry-After`, quando válido, é respeitado junto com o reset da cota, usando
  o maior prazo quando ambos estiverem presentes. Para
  limite secundário sem prazo, aguarda 60, 120, 240 e 480 segundos. Um `403` de
  permissão, sem indicação de rate limit, é propagado imediatamente.
- Para respostas `5xx`, faz até quatro novas tentativas com esperas de **1, 2,
  4 e 8 segundos**: são no máximo cinco requisições se apenas esse erro ocorrer.
- As repetições por rate limit também são limitadas a quatro por consulta. Os
  contadores de rate limit e `5xx` são independentes. Se as falhas persistirem,
  o erro HTTP final é propagado e o cache concluído fica disponível para retomada.

As esperas e repetições são registradas no log. Não é necessário configurar
flags adicionais. Os testes simulam respostas, relógio e espera, sem acessar a
rede nem aguardar os intervalos reais. Erros de conexão e timeout continuam
sendo propagados pelo cliente.

Referência: [rate limits da REST API do GitHub](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

### Coleta mensal de workflow runs (S01-18)

Para validar a coleta sem percorrer todos os candidatos, depois de gerar
`data/raw/candidatos.json`, execute um piloto:

```bash
python -m pipeline --config config.yaml --piloto 100
```

Esse comando não repete a Search API. Usa os primeiros **até 100 candidatos**
da busca existente e executa Actions, metadados e workflow runs. Os filtros
podem reduzir a quantidade final de repositórios. Os resultados ficam em
`data/raw/piloto-100/`, sem sobrescrever a busca nem as saídas completas. O
cache continua em `data/cache` e as respostas anteriores são reutilizadas.
Use `--piloto` sem `--etapas`; ele não pode ser combinado com `--limpar-cache`.
Se a cota da API ainda estiver esgotada, o piloto também aguardará o reset.
Uma interrupção pode ser retomada repetindo o mesmo comando.

O piloto verifica a coleta da S01-18. Ele não equivale à conclusão da S01-21,
que exige seleção, coleta **e cálculo** integrados para 100 repositórios.

A etapa `workflow_runs` lê `data/raw/metadados.json` e usa a `default_branch`
de cada repositório. Consulta `GET /repos/{owner}/{repo}/actions/runs` com
`branch=<default_branch>`, `event=push` e `created=<início>..<fim>` para cada mês
da janela de observação. O fim da consulta é inclusivo: o primeiro segundo do
mês seguinte menos um segundo, evitando sobreposição entre meses.

```bash
python -m pipeline --config config.yaml --etapas workflow_runs
```

Sem `--etapas`, a coleta de runs também é executada após os metadados. Cada mês
é paginado em até dez páginas de 100 runs. As páginas são persistidas pelo cache
da S01-16 e as requisições usam o controle de rate limit/backoff da S01-17.
Depois de uma interrupção, execute novamente o mesmo comando para reutilizar
as páginas concluídas e consultar as restantes.

Se um mês atingir **1.000 runs**, há um alerta no log e
`limite_atingido=true` nos dados. Acima de 1.000, a API não permite recuperar
todos os resultados com esses filtros: `coleta_incompleta=true`. Essa marca
também é aplicada se a paginação entregar menos IDs únicos que o total esperado.
Não há subdivisão diária nesta etapa; uma coleta marcada como incompleta deve
ser considerada nas análises posteriores.

A saída `data/raw/workflow_runs.json` contém os repositórios, os runs ordenados
por `created_at`/ID, os totais e o diagnóstico de cada mês. Os IDs são
deduplicados e os filtros de branch, evento e intervalo são conferidos também
localmente. São preservados `workflow_id`, status, conclusion (inclusive nula),
datas, SHA, número/tentativa do run e URL. As conclusions ignoradas nas métricas
são mantidas nesta coleta para auditoria; CFR e recuperação serão calculados
nas tarefas S01-19 e S01-20. Repositórios com HTTP 404/451 são registrados como
inacessíveis; os demais erros são propagados. O consolidado é gravado de forma
atômica e respostas completas da API ficam no cache.

Referência: [workflow runs na REST API do GitHub](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository).

### CFR variante (a) — S01-19

O módulo `pipeline.cfr` calcula, para cada repositório, a fração
`falhas / (falhas + sucessos)` usando o JSON produzido pela coleta de workflow
runs da S01-18. `success` conta como sucesso; `failure`, `timed_out` e
`startup_failure` contam como falha. `cancelled`, `skipped`, `neutral`,
`action_required`, `stale`, conclusões desconhecidas, nulas ou ausentes são
ignoradas no numerador e no denominador.

Execute depois de concluir a coleta, na pasta `Lab03`:

```bash
python -m pipeline.cfr --config config.yaml
```

O comando lê `data/raw/workflow_runs.json` e grava `data/processed/cfr.json`.
É um cálculo local: não exige `GITHUB_TOKEN` nem acessa a API. Para usar os
resultados de um piloto, indique os arquivos explicitamente:

```bash
python -m pipeline.cfr --config config.yaml --entrada data/raw/piloto-100/workflow_runs.json --saida data/processed/piloto-100/cfr.json
```

No Windows, também é possível executar com `.\.venv\Scripts\python.exe`
em lugar de `python`. Em um worktree separado, informe `--entrada` com o
caminho absoluto do arquivo na pasta em que a coleta foi executada. A entrada
precisa ser o consolidado concluído; as páginas isoladas do cache não bastam.

A saída inclui falhas, sucessos, conclusions ignoradas, runs válidos e
`change_failure_rate` como fração entre 0 e 1, sem arredondamento (por exemplo,
1 falha em 4 runs válidos resulta em `0.25`, isto é, 25%). Sem runs válidos, a
CFR e sua classe ficam `null`, pois não há denominador; zero indica que houve
runs válidos e nenhuma falha. `classe_cfr` usa a classificação C1 já documentada.

O cálculo confere novamente default branch, evento `push` e `created_at` na
janela `[início, fim)`, deduplica IDs e informa quantos registros ficaram fora
do recorte ou eram duplicados. Também exige que a janela declarada na entrada
corresponda à configuração. Conclusões ignoradas contam apenas entre os runs
retidos após esses filtros. Cada repositório mantém `coleta_incompleta` e gera
um alerta quando o valor é baseado em coleta parcial; ele não representa a
CFR de todos os runs nesse caso. A gravação da saída é atômica e não pode
sobrescrever o arquivo de entrada.

A S01-19 calcula a métrica dos repositórios recebidos, sem aplicar o filtro
final de inclusão por releases/runs e sem calcular uma CFR global. A integração
das métricas e da seleção em um único comando pertence à S01-21 (#149).

### Tempo de recuperação por workflow — S01-20

O módulo `pipeline.tempo_recuperacao` identifica episódios independentes para
cada `workflow_id`: a primeira falha abre o episódio e o próximo sucesso do
mesmo workflow o encerra. Falhas seguintes não reiniciam o relógio. São usadas
as mesmas conclusions da CFR: `failure`, `timed_out` e `startup_failure` para
falhas, e `success` para recuperação. Conclusions ignoradas não abrem nem
encerram episódios; o sucesso de outro workflow também não encerra o episódio.

As datas são `created_at`, conforme as definições operacionais. Os runs são
ordenados por data e ID e deduplicados por ID. O cálculo confere novamente
default branch, `push` e a janela `[início, fim)`. Sucessos no instante final
ou depois da janela não são recuperações observadas nesse período. Episódios
abertos no fim da janela têm `censurado=true`, `run_sucesso_id=null` e a duração
observada até o limite final; essa duração é um **limite inferior**, não um
tempo conhecido de recuperação.

Execute após concluir a coleta, na pasta `Lab03`:

```bash
python -m pipeline.tempo_recuperacao --config config.yaml
```

O comando lê `data/raw/workflow_runs.json` e grava atomicamente
`data/processed/tempo_recuperacao.json`, sem token nem acesso à API. Para o piloto:

```bash
python -m pipeline.tempo_recuperacao --config config.yaml --entrada data/raw/piloto-100/workflow_runs.json --saida data/processed/piloto-100/tempo_recuperacao.json
```

Em outro worktree, indique o caminho absoluto da entrada na pasta da coleta.
Use o Python do ambiente virtual com as dependências instaladas; no Windows,
`.\.venv\Scripts\python.exe` também funciona sem ativação. O consolidado de
runs deve estar concluído e declarar a mesma janela da configuração. A saída
não pode sobrescrever a entrada.

A saída preserva os episódios, IDs, datas, quantidade de falhas e censura.
`tempo_recuperacao` é a **mediana em horas dos episódios recuperados**;
`q1_horas`, `q3_horas` e `iqr_horas` usam quartis inclusivos com interpolação
linear (`statistics.quantiles`, método `inclusive`). Com uma recuperação,
Q1 = Q3 = mediana e IQR = 0. Sem recuperações, essas estatísticas e a classe C1
ficam `null`. As quantidades de episódios recuperados e censurados são
reportadas separadamente; censurados não entram na mediana/IQR. Essas
estatísticas descrevem os episódios observados com recuperação, sem estimar
uma distribuição que inclua episódios censurados.

O teste de 1h20 exigido na #148 usa a primeira falha às 10:00, outra falha às
10:30 e o sucesso às 11:20: a duração é 80 minutos (`4/3` hora). É um cenário
numérico equivalente; o enunciado completo não está versionado neste
repositório. A suíte também cobre workflows intercalados, repetição de
falhas, conclusões ignoradas, fronteiras da janela e censura.

Coletas incompletas mantêm `coleta_incompleta=true` e geram alerta. Ausência de
páginas pode esconder a primeira falha ou uma recuperação, então os episódios
calculados também ficam sujeitos a essa limitação. O cálculo não aplica o
filtro final de inclusão nem integra as etapas em um único comando; isso fica
para a S01-21 (#149). A validação real e o aceite da task permanecem pendentes.
### Funil de seleção e critério mínimo de inclusão (S01-06)

O módulo `pipeline.funil` aplica o critério mínimo de inclusão de
`config.yaml` (`inclusao`) e gera a tabela do funil de seleção, com a
quantidade de repositórios em cada etapa e os motivos de descarte. É um
cálculo local: não exige `GITHUB_TOKEN` nem acessa a API.

```bash
python -m pipeline.funil --config config.yaml
```

O comando lê de `caminhos.raw` as saídas `candidatos.json`, `actions.json`,
`metadados.json`, `workflow_runs.json` e `releases.json`, e grava
`funil.json` e `funil.md` em `caminhos.processed`. A tabela também é exibida
no terminal. Para um piloto:

```bash
python -m pipeline.funil --config config.yaml --raw data/raw/piloto-100 --saida data/processed/piloto-100
```

Etapas da tabela:

| Etapa | Descartes possíveis |
|---|---|
| Busca na Search API | — (candidatos deduplicados pelo id) |
| Usa GitHub Actions | `sem_github_actions`, `repositorio_inacessivel` |
| Metadados coletados | `repositorio_inacessivel` |
| Workflow runs coletados | `repositorio_inacessivel` |
| Releases coletadas | `repositorio_inacessivel` |
| Critério mínimo de inclusão | `releases_insuficientes`, `runs_validos_insuficientes`, `releases_e_runs_insuficientes` |

No critério mínimo, cada repositório recebe um único motivo, para que a soma
dos descartes por motivo feche com o total da etapa. São contadas como
**releases publicadas** as que têm `draft = false` e `published_at` em
`[início, fim)`, deduplicadas por `id` (ou `tag_name`); pre-releases contam.
Os **runs válidos** seguem as mesmas regras da CFR (S01-19). Um repositório
com coleta de runs incompleta continua na amostra, com
`coleta_runs_incompleta=true` e um alerta no log.

`funil.json` traz as etapas, a amostra final (com releases publicadas e runs
válidos de cada repositório) e a lista de descartes com etapa, motivo e
detalhe. O comando recusa saídas inconsistentes: um repositório que chegou a
uma etapa e não aparece no arquivo dela, que aparece como aprovado e
descartado ao mesmo tempo, ou janelas de runs/releases diferentes da
configurada.

A coleta de releases é a S01-10 (#138). O funil espera em `releases.json` o
mesmo formato das demais etapas: `janela` (`inicio` e `fim_exclusivo`, como
em `workflow_runs.json`), `repositorios` com `id`, `full_name` e a lista
`releases` (`id`, `tag_name`, `draft`, `prerelease`, `published_at`) e
`descartes` com `id`, `full_name`, `motivo` e `detalhe`. Drafts e releases
fora da janela podem estar no arquivo: o funil os filtra de novo.

### Etapas

| Etapa | Saída | Descrição |
|---|---|---|
| `candidatos` | `data/raw/candidatos.json` | Busca pela Search API (seção `busca` do `config.yaml`). A faixa de estrelas é dividida ao meio até cada consulta ter no máximo 1000 resultados; faixas indivisíveis acima do limite são marcadas como truncadas e geram alerta. Duplicatas são removidas pelo id do repositório. |
| `actions` | `data/raw/actions.json` | Lê `candidatos.json` e consulta o endpoint de workflows de cada repositório. Descarta os que não têm nenhum workflow em `.github/workflows/` (workflows dinâmicos do GitHub, como Dependabot e CodeQL, não contam) e os que respondem 404 ou 451. Os descartes ficam no arquivo com o motivo, para o funil de seleção. |
| `metadados` | `data/raw/metadados.json` | Lê os aprovados de `actions.json` e coleta estrelas, linguagem, idade (até o fim da janela), default branch e número de contribuidores (Link header com `per_page=1&anon=1`). Cada repositório é salvo em `data/cache/metadados/`; numa reexecução, os que já estão lá não são consultados de novo. |
| `workflow_runs` | `data/raw/workflow_runs.json` | Lê `metadados.json`, coleta os runs de push do default branch por mês com paginação e cache e registra os meses que atingem o limite de 1000 resultados. |

Testes:

```bash
pytest --cov=pipeline --cov-fail-under=80
```

O workflow [`lab03-ci.yml`](../.github/workflows/lab03-ci.yml) roda esse mesmo comando a cada push e pull request, em Python 3.11 e 3.13. O build falha se algum teste falhar ou se a cobertura ficar abaixo de 80%.

## Estrutura

```text
Lab03/
├── artigo/            # Seções do artigo em LaTeX (template SBC) e referências
├── config.yaml        # Parâmetros do pipeline (janela, critérios, caminhos)
├── docs/              # Definições operacionais e documentação
├── pipeline/          # Código do pipeline (entry point: python -m pipeline)
├── tests/             # Testes automatizados
└── data/              # Cache, dados brutos e processados (gerados pelo pipeline)
```

## Cronograma

| Sprint | Período |
|---|---|
| Lab03S01 | 08/10 a 14/10 |
| Lab03S02 | 15/10 a 21/10 |
| Lab03S03 | 22/10 a 28/10 |
| Entrega Final | 29/10 a 04/11 |

O acompanhamento das tarefas é feito no [GitHub Project](https://github.com/users/Victorgabrielcruz/projects/7). Todo commit deve referenciar o número da issue correspondente (ex.: `feat: ... (#N)`).


### Pipeline integrado — S01-21 (#149)

Um único comando amplia gradualmente a busca até obter 100 repositórios com
pelo menos cinco releases e cinquenta runs válidos na janela, ou esgotar o
limite explícito de candidatos:

```text
python -m pipeline.integrado --config config.yaml --alvo 100 --max-candidatos 1000
```

`--candidatos CAMINHO` reutiliza uma busca consolidada existente. No modo
padrão, `raw/candidatos_busca.json` preserva a busca completa, enquanto
`raw/candidatos.json` contém somente os candidatos avaliados no funil.
`--reutilizar-runs CAMINHO` reutiliza os meses completos de uma coleta mensal
com a mesma janela, identidade e default branch. Use caminhos próprios em
`caminhos.raw` e `caminhos.processed` para preservar o piloto; o cache pode ser
compartilhado depois que a coleta original terminar.

A ordem é candidatos → Actions → metadados → releases → workflow runs →
critério mínimo → frequência de releases/CFR (a)/tempo de recuperação. O
prefiltro de releases evita coletar runs de quem já não satisfaz a inclusão.
O funil registra `prefiltro_releases_insuficientes` nessa passagem; ele não
infere quantos runs esses repositórios teriam. Meses com mais de 1000 resultados
são subdivididos recursivamente até caber na API. Saturação dentro de um único
segundo, contagem inconsistente ou páginas ausentes mantêm `coleta_incompleta`;
repositórios parciais não contam para os 100 da execução completa.

Checkpoints atômicos por repositório ficam em `raw/checkpoints/<hash>/`. O hash
inclui fonte, janela, critérios, regras e API. Uma retomada reutiliza os
repositórios concluídos e páginas do cache; um erro temporário não apaga o
progresso anterior. `raw/progresso.json` permite acompanhar a execução.

Saídas: consolidados por etapa em raw; `amostra_workflow_runs.json` restrito aos
elegíveis completos; `funil.json`, `funil.md`, `deployment_frequency.json`,
`cfr.json`, `tempo_recuperacao.json` e `execucao.json` em processed. O exit code
é 0 quando o alvo é atingido, 3 quando faltam elegíveis e 2 em erro. A presença
de arquivos não comprova sucesso: confira `execucao_completa` e contagens.

O comando integra as métricas disponíveis. Compare/lead time (#140/#141/#142)
ainda são dependências explícitas em `execucao.json`; isso não comprova o
cálculo das quatro métricas DORA. A validação real dos 100 repositórios continua
pendente até haver evidência registrada no relatório.
