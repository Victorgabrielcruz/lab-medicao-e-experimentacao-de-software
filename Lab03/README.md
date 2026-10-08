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
da busca existente e executa Actions, metadados, releases, compare, tags e workflow runs. Os filtros
podem reduzir a quantidade final de repositórios. Os resultados ficam em
`data/raw/piloto-100/`, sem sobrescrever a busca nem as saídas completas. O
cache continua em `data/cache` e as respostas anteriores são reutilizadas.
Use `--piloto` sem `--etapas`; ele não pode ser combinado com `--limpar-cache`.
Se a cota da API ainda estiver esgotada, o piloto também aguardará o reset.
Uma interrupção pode ser retomada repetindo o mesmo comando.

O piloto verifica as coletas da S01-10, S01-11, S01-12 e S01-18. Ele não equivale à conclusão da S01-21,
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

### Coleta de releases na janela (S01-10 — #138)

A etapa `releases` lê `data/raw/metadados.json` e consulta
`GET /repos/{owner}/{repo}/releases` com páginas de 100 registros, seguindo o
cabeçalho `Link` (`rel="next"`) até o fim. Não encerra a paginação ao encontrar
uma release antiga, pois o recorte é feito localmente por `published_at`.

```bash
python -m pipeline --config config.yaml --etapas releases
```

Sem `--etapas`, executa após os metadados; `--piloto 100` também inclui releases,
com saída em `data/raw/piloto-100/releases.json`. A coleta usa o mesmo cliente,
cache por página e tratamento de rate limit/backoff das demais etapas. Após
interrupção, repetir o comando reutiliza as páginas concluídas, inclusive seus
links de paginação. As respostas originais da API ficam no cache para auditoria.

O consolidado `data/raw/releases.json` é gravado atomicamente. Contém apenas
releases com `draft=false` e publicação na janela UTC `[início, fim)`, incluindo
todo o último dia configurado. Datas de publicação nulas ou ausentes são
excluídas; datas inválidas ou sem fuso geram aviso e são excluídas. IDs são
deduplicados e os registros ordenados por publicação/ID. Os campos preservados
são `id`, `draft`, `prerelease`, `published_at`, `tag_name`, `created_at`,
`target_commitish`, `html_url`, `name` e `body`.

Pré-releases são preservadas para a RQ07. `total_releases` conta todas as releases
publicadas retidas; `total_prereleases` conta aquelas com `prerelease=true` e
`total_releases_estaveis` conta aquelas com `prerelease=false`. A definição
principal de deploy usa somente as estáveis. Esses totais aparecem por
repositório e no consolidado, junto da janela e dos descartes. Repositórios sem
releases são mantidos com lista vazia e totais zero. HTTP 404/451 gera descarte
`repositorio_inacessivel`; outros erros são propagados e preservam o consolidado
anterior. O filtro mínimo de inclusão e o cálculo das métricas pertencem à
integração posterior do pipeline.

Referência: [releases na REST API do GitHub](https://docs.github.com/en/rest/releases/releases#list-releases).

### Coleta de tags com data do commit (S01-11 — #139)

A etapa `tags` lê `data/raw/metadados.json` e consulta
`GET /repos/{owner}/{repo}/tags` com páginas de 100 registros, seguindo o
cabeçalho `Link` (`rel="next"`) até o fim. Para cada SHA informado pela lista,
consulta `GET /repos/{owner}/{repo}/commits/{sha}` e obtém `commit.author.date`.
Essa é a data usada no filtro, inclusive quando difere de `commit.committer.date`;
a data de criação de uma tag anotada não substitui a data do autor do commit.
As consultas usam o SHA, permitindo nomes de tags com barras ou outros caracteres.

```bash
python -m pipeline --config config.yaml --etapas tags
```

Sem `--etapas`, a coleta roda após as releases. Também participa do
`--piloto 100`, com saída em `data/raw/piloto-100/tags.json`. Páginas e respostas
de commits são salvas pelo cache compartilhado, com o mesmo controle de rate
limit/backoff. Uma reexecução reutiliza ambas, inclusive após interrupção no
meio de uma página. Tags distintas no mesmo SHA são mantidas, com uma única
consulta ao commit; duplicatas por nome são removidas.

O consolidado `data/raw/tags.json` é gravado atomicamente e contém as tags cuja
data do autor está na janela UTC `[início, fim)`, incluindo todo o último dia
configurado. A paginação percorre todas as páginas mesmo após encontrar uma tag
antiga, pois a ordem das tags não garante ordem cronológica. Os registros são
ordenados por data/nome e preservam `name`, `commit_sha`, `commit_author_date`,
`commit_url`, `node_id`, `zipball_url` e `tarball_url`. Os totais são registrados
por repositório e no consolidado, junto da janela e de
`data_referencia="commit.author.date"`. Repositórios sem tags são mantidos com
lista vazia e total zero. A coleta inclui tags com ou sem release associada,
como alternativa de unidade de deploy para a RQ07.

HTTP 404/451 ao listar tags gera descarte `repositorio_inacessivel`. Quando
apenas a consulta do commit responde 404/451, ou `commit.author.date` está
ausente, inválida ou sem fuso, somente as tags desse commit são ignoradas.
Esses casos geram aviso, entram em `tags_ignoradas` com nome/SHA/motivo e marcam
`coleta_incompleta=true`, preservando as demais tags do repositório. Tags fora
da janela são filtradas normalmente e não indicam coleta incompleta.
Outros erros são propagados e preservam o consolidado anterior para retomada.

Referências: [lista de tags](https://docs.github.com/en/rest/repos/repos#list-repository-tags)
e [consulta de commit](https://docs.github.com/en/rest/commits/commits#get-a-commit)
na REST API do GitHub.

### Commits entre releases consecutivas (S01-12 — #140)

A etapa `compare` lê `data/raw/releases.json`, confere se a janela corresponde
à configuração e usa as releases estáveis (`draft=false`, `prerelease=false`)
publicadas dentro dela, em ordem de `published_at`/ID. Para cada par consecutivo,
consulta `GET /repos/{owner}/{repo}/compare/{anterior}...{atual}`. As tags são
codificadas na URL, incluindo nomes com barras e caracteres especiais.

```bash
python -m pipeline --config config.yaml --etapas compare
```

Sem `--etapas`, roda após `releases`; `--piloto 100` também inclui a coleta,
com saída em `data/raw/piloto-100/compare.json`. A primeira release da janela
usa como base a última release estável anterior à janela. Essa referência é
recuperada percorrendo o endpoint de releases com o cache compartilhado da
S01-10. Se não existir release anterior, a primeira é registrada como ignorada
com motivo `sem_release_anterior`, e a seguinte é comparada normalmente.
Pré-releases permanecem nos dados da S01-10 para variantes posteriores; não
interrompem a sequência estável usada nesta etapa.

Todas as consultas de compare usam `per_page=100` e `page`, seguindo
`Link` (`rel="next"`) até o fim. O limite de **250 commits** é da consulta
**sem paginação**: esta etapa não trunca nesse número. Cada comparação registra
`limite_sem_paginacao=250`, `limite_250_superado`, o total da API, o total de
SHAs únicos recuperados e as páginas coletadas. Valores acima de 250 também
são registrados no log e no contador `comparacoes_acima_250` por repositório
e no consolidado. Commits são deduplicados por SHA dentro de cada comparação;
o commit base não é incluído na lista.

O consolidado `data/raw/compare.json` é gravado atomicamente. Cada registro
identifica a release, a anterior, o status do compare e os commits, preservando
SHA, URL, `commit.author`, `commit.committer`, mensagem e SHAs dos pais. A data
para o cálculo posterior de lead time é `commit.author.date`. Commits anteriores
à janela são preservados, pois podem ter sido entregues numa release da janela.
Comparações sem commits novos são mantidas como completas com lista vazia.
Esta etapa fornece os dados; não calcula o lead time.

HTTP **404** no compare registra a release como ignorada, com as duas tags e
o motivo `compare_inacessivel`, sem interromper os próximos pares ou repositórios.
O par seguinte continua usando a release cronologicamente anterior, inclusive
se o compare dela falhou; não se salta essa base. HTTP 451 recebe o mesmo
tratamento. Se o histórico de releases estiver inacessível, as releases desse
repositório são registradas com motivo `historico_releases_inacessivel`.

Se a paginação entregar uma quantidade de SHAs diferente de `total_commits`,
ou se esse total mudar entre páginas, a comparação fica
`coleta_incompleta=true` e a release é ignorada com motivo `compare_incompleto`.
Os commits parciais ficam no registro para auditoria. A saída informa
`total_comparacoes` completas, `total_releases_ignoradas`, os motivos por
repositório e `total_releases_ignoradas_404`, por repositório e no consolidado.
A primeira release histórica sem anterior é ignorada, mas não representa
coleta incompleta.

Páginas de releases e compare ficam no cache da S01-16 e usam o controle de
rate limit/backoff da S01-17. Após interrupção, repetir o comando reutiliza as
páginas concluídas. Erros HTTP não são cacheados; um compare que respondeu 404
é consultado novamente numa reexecução. Outros erros são propagados, preservando
o consolidado anterior.

Referência: [compare na REST API do GitHub](https://docs.github.com/en/rest/commits/commits#compare-two-commits).

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

### Etapas

| Etapa | Saída | Descrição |
|---|---|---|
| `candidatos` | `data/raw/candidatos.json` | Busca pela Search API (seção `busca` do `config.yaml`). A faixa de estrelas é dividida ao meio até cada consulta ter no máximo 1000 resultados; faixas indivisíveis acima do limite são marcadas como truncadas e geram alerta. Duplicatas são removidas pelo id do repositório. |
| `actions` | `data/raw/actions.json` | Lê `candidatos.json` e consulta o endpoint de workflows de cada repositório. Descarta os que não têm nenhum workflow em `.github/workflows/` (workflows dinâmicos do GitHub, como Dependabot e CodeQL, não contam) e os que respondem 404 ou 451. Os descartes ficam no arquivo com o motivo, para o funil de seleção. |
| `metadados` | `data/raw/metadados.json` | Lê os aprovados de `actions.json` e coleta estrelas, linguagem, idade (até o fim da janela), default branch e número de contribuidores (Link header com `per_page=1&anon=1`). Cada repositório é salvo em `data/cache/metadados/`; numa reexecução, os que já estão lá não são consultados de novo. |
| `releases` | `data/raw/releases.json` | Lê `metadados.json`, pagina pelo Link header com cache e retém publicações na janela sem drafts; preserva pré-releases e contabiliza as estáveis separadamente. |
| `compare` | `data/raw/compare.json` | Lê `releases.json`, compara releases estáveis consecutivas com paginação/cache, recupera a base anterior à janela e registra o limite de 250 commits e releases ignoradas por 404 ou coleta incompleta. |
| `tags` | `data/raw/tags.json` | Lê `metadados.json`, pagina as tags e consulta a data do autor de cada commit por SHA, filtrando pela janela e reutilizando o cache de páginas/commits para a variante da RQ07. |
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
