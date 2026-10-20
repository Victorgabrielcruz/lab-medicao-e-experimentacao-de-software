# Lab03 — Mineração de métricas DORA

[![Lab03 CI](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml/badge.svg?branch=main)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml)

Cálculo das quatro métricas DORA (deployment frequency, lead time, change failure rate e tempo de recuperação) a partir de dados públicos de repositórios open-source que usam GitHub Actions. A coleta é feita por script próprio sobre as APIs REST/GraphQL do GitHub, sem PyGithub.

## Documentação

| Documento | Conteúdo |
|---|---|
| [`entregas/s02-03-dataset-500/README.md`](entregas/s02-03-dataset-500/README.md) | CSV offline atualizado para 500, hashes e cobertura parcial das métricas |
| [`docs/atualizacao-sprint02-victor-500.md`](docs/atualizacao-sprint02-victor-500.md) | Revisão das cinco tarefas de Victor na Sprint 02 e responsabilidades consultadas no GitHub |
| [`entregas/dados-brutos-500/README.md`](entregas/dados-brutos-500/README.md) | Base capturada de 500 elegíveis, cache completo e restauração com verificação de hashes; compares ainda parciais |
| [`docs/coleta-tres-sessoes.md`](docs/coleta-tres-sessoes.md) | Retomada até 500 com três tokens, sem prioridade por tamanho, status no terminal e recuperação de rede |
| [`docs/definicoes-operacionais.md`](docs/definicoes-operacionais.md) | Janela de observação, definição de deploy, regras de runs, critério de inclusão, filtro de Actions, metadados e tabela de classificação DORA (C1) |
| [`artigo/README.md`](artigo/README.md) | Organização do artigo em LaTeX, hipóteses informais das RQ01 a RQ07 e registro de sua cronologia; RQ05 a RQ07 na S01-15 (#143) |

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

As entradas são gravadas sem indentação. As páginas de workflow runs
(`/actions/runs`) guardam somente `total_count` e, de cada run, os campos que
o pipeline usa (`CAMPOS_RUN` em `pipeline/cache.py`): uma página de 100 runs
chega a vários megabytes na API, quase tudo em `pull_requests`, `repository` e
`head_repository`, que não entram em nenhum cálculo. As demais respostas são
guardadas inteiras. Entradas antigas, inteiras e indentadas, continuam válidas.

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
atômica; o cache guarda de cada run somente esses mesmos campos.

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

### Lead time por release (RQ02a — S01-13 — #141)

O módulo `pipeline.lead_time_release` calcula a variante (a) usando
`data/raw/compare.json` da S01-12. Para cada release, o lead time é
`published_at - min(commit.author.date)` em **horas**, sem arredondamento.
O valor do repositório é a **mediana dos lead times das releases válidas**;
cada release tem o mesmo peso, independentemente da quantidade de commits.
Não usa a data do committer nem presume que a ordem dos commits na API seja a
ordem das datas dos autores. Commits escritos antes da janela são considerados.

Execute após a etapa `compare`, na pasta `Lab03`:

```bash
python -m pipeline.lead_time_release --config config.yaml
```

O comando lê `data/raw/compare.json` e grava
`data/processed/lead_time_release.json`. É um cálculo local, sem token nem
acesso à API. Para usar os dados de um piloto:

```bash
python -m pipeline.lead_time_release --config config.yaml --entrada data/raw/piloto-100/compare.json --saida data/processed/piloto-100/lead_time_release.json
```

No Windows, use `.\.venv\Scripts\python.exe` em lugar de `python`, como nos
outros comandos. A entrada deve declarar a mesma janela da configuração e
`definicao_deploy=release_estavel`; a saída não pode sobrescrever a entrada.
A gravação é atômica. A integração dos cálculos no comando único do pipeline
pertence à S01-21 (#149), como ocorre com a CFR.

A saída informa `lead_time_horas` de cada release, a referência à release
anterior, o SHA e a data do autor mais antiga e a quantidade de commits únicos.
Por repositório, contém a mediana em `lead_time_horas`, sua `classe_lead_time`
pela tabela C1, contagens de releases calculadas/ignoradas, motivos e diagnóstico
de coleta incompleta. O consolidado também informa unidade, fórmula, variante
e totais. Por exemplo, uma release em 15/03 com commits de 02/03, 10/03 e 14/03
tem lead time de **312 horas (13 dias)**.

Casos de borda:

- Primeira release histórica sem anterior: `null`, motivo `sem_release_anterior`.
  A primeira release **da janela** pode ser calculada se houver uma anterior
  fora dela, já recuperada pela S01-12.
- Release sem commits novos: `null`, motivo `sem_commits_novos`, fora da mediana.
  Um intervalo real de zero horas é válido e recebe classe Elite.
- Compare ignorado (inclusive HTTP 404) ou incompleto: `null`, preservando o
  motivo/diagnóstico da coleta. A quantidade de SHAs é conferida contra os
  totais declarados para evitar calcular sobre uma lista parcial.
- Commit sem SHA ou com data do autor ausente, inválida ou sem fuso: a release
  inteira é ignorada, pois não há como garantir qual era o commit mais antigo.
- Lead time negativo: `null`, motivo `lead_time_negativo`, sem converter para
  zero; o SHA/data mais antigos permanecem disponíveis para auditoria.
- Repositório sem releases calculáveis: mediana e classe `null`.

O recorte por publicação é conferido novamente em `[início, fim)`. IDs de
releases e SHAs de commits são deduplicados. Releases fora da janela e duplicadas
são contadas separadamente. Datas de publicação inválidas no consolidado geram
erro de entrada. Quando o repositório tem coleta incompleta, a mediana pode usar
as releases com comparações completas, mantendo `coleta_incompleta=true` e aviso
no log; ela não representa todas as releases nesse caso.

### Lead time por commit (RQ02b — S01-14 — #142)

O módulo `pipeline.lead_time_commit` usa `data/raw/compare.json` da S01-12 e
calcula `release.published_at - commit.author.date` para **cada commit incluído
em cada release**, em horas, sem arredondamento. O valor do repositório é a
mediana de **todos esses intervalos**, reunindo todas as releases válidas.
Uma release com mais commits contribui com mais valores. Não há uma agregação
intermediária por release.

Execute após a etapa `compare`, na pasta `Lab03`:

```bash
python -m pipeline.lead_time_commit --config config.yaml
```

O comando é local, sem token nem acesso à API, e grava
`data/processed/lead_time_commit.json`. Para um piloto:

```bash
python -m pipeline.lead_time_commit --config config.yaml --entrada data/raw/piloto-100/compare.json --saida data/processed/piloto-100/lead_time_commit.json
```

No Windows, use `.\.venv\Scripts\python.exe` em lugar de `python`. A entrada
deve declarar a mesma janela da configuração e `definicao_deploy=release_estavel`.
A saída é gravada atomicamente e não pode sobrescrever o compare. A integração
dos cálculos no comando único pertence à S01-21 (#149), como na variante (a).

A saída preserva os intervalos individuais sob `releases[].commits[]`, com SHA,
URL, data do autor em UTC, `lead_time_horas` e diagnóstico de valores ignorados.
Cada repositório informa sua mediana em `lead_time_horas`, `classe_lead_time`
pela tabela C1, contagens de releases/commits calculados e ignorados, seus
motivos e os indicadores `coleta_incompleta` e `calculo_parcial`. O consolidado
inclui unidade, fórmula, variante `b` e totais. No exemplo do enunciado, a
release de 15/03 contém commits de 02/03, 10/03 e 14/03: **312, 120 e 24 horas
(13, 5 e 1 dias)**, com mediana de **120 horas (5 dias)**.

O recorte usa a publicação da release na janela UTC `[início, fim)`; commits
escritos antes da janela são mantidos. IDs de releases são deduplicados e cada
SHA conta uma vez **por release**. Se o mesmo SHA aparecer em outra comparação,
seu intervalo até essa outra publicação também é mantido, conforme a unidade
commit–release. A data do committer não é usada.

A primeira release histórica sem anterior, releases sem commits novos e
comparações ignoradas/incompletas ficam fora do cálculo, com motivo registrado.
Os totais de commits são conferidos para detectar listas parciais; um commit
sem SHA impede confirmar a comparação e invalida a release. Datas de autor
ausentes, inválidas ou sem fuso e intervalos negativos invalidam somente o
commit correspondente, que recebe `null` e um motivo. Os demais intervalos
válidos podem compor a mediana, marcada como `calculo_parcial=true` e com aviso
no log. A coleta incompleta recebida do compare também é preservada.

Zero real é válido. Sem intervalos válidos, a mediana e sua classe ficam `null`.
Uma release cujos commits são todos inválidos recebe motivo `sem_commits_validos`.
Datas de publicação inválidas no consolidado geram erro de entrada. Os testes
incluem a fixture do enunciado e verificam a mediana de todos os commits entre
múltiplas releases, além dos casos de borda e da compatibilidade com a S01-12.

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

#### Consolidados de runs com um repositório por linha

No pipeline integrado, `raw/workflow_runs.json` e
`raw/amostra_workflow_runs.json` são gravados por `pipeline/consolidado.py`
com um repositório por linha. O arquivo continua sendo um único JSON válido,
com as mesmas chaves, e pode ser aberto por qualquer leitor de JSON.

Esse formato permite gravar e ler um repositório por vez. Durante a execução,
o pipeline integrado mantém na memória só o resumo de cada repositório; a
lista de runs fica no checkpoint e é relida na hora de gravar. A CFR, o tempo
de recuperação e a auditoria leem a entrada da mesma forma, e o hash da
auditoria é calculado em blocos. Consolidados antigos, em qualquer
formatação, continuam aceitos e são lidos inteiros.

### Tempo de recuperação por workflow — S01-20

O módulo `pipeline.tempo_recuperacao` implementa a RQ04 oficial por workflow:
a primeira falha após um sucesso observado inicia o episódio em
`run_started_at`; o próximo sucesso encerra em `updated_at`.
Falhas consecutivas mantêm o início. As conclusions e os filtros branch/push
são os da CFR; `created_at` define apenas o recorte da entrada.
A sequência usa início e ID. Sucessos que terminam em/após o fim da janela
mantêm censura à direita e duração limite inferior. A proporção de censurados
é informada por repositório.

Falhas iniciais sem sucesso anterior observado são censuras à esquerda
separadas, sem duração presumida. Timestamps essenciais inválidos deixam
o workflow sem estimativa, com diagnóstico, sem fallback para criação.
A versão `rq04-updated-at-run-started-at-v2` distingue a correção do cálculo
legado por criação. O integrado preserva o legado antes de reprocessar essa
métrica, reutilizando a coleta e a CFR auditada.

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

O teste oficial de 1h20 contém um sucesso às 09:00, primeira falha iniciada
às 10:00, outra às 10:30 e sucesso iniciado às 11:15 e terminado às 11:20.
As datas de criação são diferentes, para detectar o uso indevido de criação.

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

### Métricas em todas as variantes (S02-02 — #152)

A [decisão de priorizar candidatos até 300 elegíveis e depois retomar os grandes](docs/decisoes-coleta-final.md)
registra a justificativa, regra de agendamento e consequências metodológicas
do replanejamento autorizado da #151. A meta final permanece em 500.
O encerramento em 255 de 15/10/2026 foi revertido: a coleta foi
[retomada até 500](docs/decisao-retomada-500.md).

Durante uma coleta integrada, a [instância auxiliar](docs/coleta-auxiliar.md)
prioriza filtros/releases/runs dos próximos candidatos e deixa compares dos
repositórios aprovados em segundo plano, sem reiniciar a principal. Compartilha
cache/checkpoints, mantém estado próprio e preserva a ordem da amostra (#151).

`pipeline/metricas.py` reúne, em uma linha por repositório, as métricas das
RQ01 a RQ04 já calculadas:

| Campo | RQ | Origem em `data/processed/` | Unidade |
|---|---|---|---|
| `deployment_frequency` | RQ01 | `deployment_frequency.json` | releases por semana |
| `lead_time_a` | RQ02a | `lead_time_release.json` | horas |
| `lead_time_b` | RQ02b | `lead_time_commit.json` | horas |
| `cfr_a` | RQ03a | `cfr.json` | fração |
| `cfr_b` | RQ03b | `cfr_b.json` | fração |
| `tempo_recuperacao` | RQ04 | `tempo_recuperacao.json` | horas |

Execute depois do pipeline integrado, na pasta `Lab03`:

```bash
python -m pipeline.metricas --config config.yaml
```

O comando é local, sem token nem acesso à API, e grava
`data/processed/metricas.json`. No Windows, use `.\.venv\Scripts\python.exe`
em lugar de `python`. Se `lead_time_commit.json` ainda não existir e houver
`data/raw/compare.json`, a variante (b) do lead time é calculada antes.

Cada repositório traz o valor e a classe (`classe_<campo>`) de cada métrica,
`coleta_incompleta`, `calculo_parcial` e `metricas_ausentes`. Uma métrica que
não pôde ser calculada fica `null`, nunca zero. O cabeçalho informa a janela,
as origens, as unidades e quantos repositórios têm cada métrica.

A CFR (b) é implementada por `pipeline/cfr_b.py` (S02-11 — #161). Enquanto
`cfr_b.json` não existir, `cfr_b` fica `null` em todos os repositórios e
aparece em `variantes_pendentes`. O arquivo esperado segue o formato de
`cfr.json`: `janela` e `repositorios` com `id`, `full_name`,
`change_failure_rate` e `classe_cfr`. As demais saídas são obrigatórias.

O comando recusa janelas diferentes da configurada, um repositório repetido
na mesma saída e o mesmo ID com nomes diferentes entre as saídas.

### Heurística de release corretiva v1 e CFR(b) (S02-11 — #161)

A v1 identifica corretivas por aumento apenas do patch SemVer **ou** termos
isolados `fix`, `revert` ou `hotfix` nas mensagens de commits. Uma release
falha quando há uma corretiva posterior em até sete dias. As publicadas nos
últimos sete dias da janela ficam censuradas, fora do denominador.

```bash
python -m pipeline.cfr_b --config config.yaml --amostra data/processed/deployment_frequency.json
python -m pipeline.metricas --config config.yaml
```

O comando lê releases e compares locais e grava `data/processed/cfr_b.json`.
O filtro `--amostra` restringe aos repositórios elegíveis. O integrado e a
reconstrução offline já executam essa etapa com esse recorte. Ausências de
evidência produzem decisões indeterminadas e diagnósticos de cobertura;
patch pode sustentar decisões mesmo sem compare. A avaliação manual da v1
continua pendente da #162. Veja as [regras, limites e opções](docs/heuristica-cfr-b-161.md).

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

### Sorteio da amostra-ouro e planilhas de rotulagem (S02-05 — #155)

O protocolo metodológico da validação manual, incluindo rotulagem, Fleiss,
consenso e avaliação da heurística, está documentado na
[seção do artigo S02-15 — #165](artigo/README.md#validação-manual--s02-15-165).
A documentação distingue os procedimentos previstos dos resultados humanos
ainda pendentes; o gerador abaixo não cria rótulos nem métricas de validação.

`pipeline/amostra_ouro.py` sorteia a amostra da validação manual e gera as
planilhas que cada integrante preenche:

- 60 repositórios da amostra final, com `DataFrame.sample(n=60, random_state=42)`;
- 5 releases de cada repositório, com o mesmo `random_state`, entre as
  publicadas na janela, sem drafts nem repetidas e seguindo
  `inclusao.incluir_prereleases`.

Execute depois do pipeline integrado, na pasta `Lab03`:

```bash
python -m pipeline.amostra_ouro --config config.yaml
```

O comando é local, sem token nem acesso à API. Ele lê a amostra final em
`data/processed/deployment_frequency.json` (os elegíveis completos) e as
releases em `data/raw/releases.json`; `--amostra` e `--releases` trocam esses
caminhos. No Windows, use `.\.venv\Scripts\python.exe` em lugar de `python`.

A saída vai para `validacao/amostra-ouro/`, que é versionada:

| Arquivo | Conteúdo |
|---|---|
| `amostra_ouro.json` | O sorteio: janela, `random_state`, tamanho e hash da população, repositórios e releases sorteados. |
| `rotulador_<A,B,C>_repositorios.csv` | Uma linha por repositório, com link do repositório e da página de releases. Colunas a preencher: `tipo_projeto`, `releases_sao_entregas_reais` e `observacoes`. |
| `rotulador_<A,B,C>_releases.csv` | Uma linha por release, com `release_url` (link direto) e `compare_url` (diferença para a release elegível anterior). Colunas a preencher: `corretiva` e `observacoes`. |

As planilhas dos três rotuladores saem idênticas e com os rótulos em branco;
cada integrante preenche somente a sua, sem consultar as demais. Os CSVs usam
UTF-8 com BOM, para abrir no Excel com os acentos corretos.

O sorteio não depende da ordem dos arquivos de entrada: os repositórios são
ordenados por ID e as releases por data de publicação antes do sorteio. O
`amostra_ouro.json` não leva data de geração, então repetir o comando sobre a
mesma amostra regrava o mesmo arquivo.

O comando recusa uma amostra final com menos de 60 repositórios, um
repositório sorteado com menos de 5 releases elegíveis e janelas diferentes
da configurada; nesses casos nada é gravado. Se alguma planilha já existir,
ele também recusa, para não apagar rótulos preenchidos. `--sobrescrever`
regrava todas as planilhas em branco.

O sorteio oficial foi feito sobre a população encerrada de 255 repositórios
(`docs/decisao-encerramento-255.md`), a partir dos consolidados reconstruídos
do snapshot publicado em `entregas/dados-brutos-255/`:

```bash
python -m pipeline.amostra_ouro --config config.yaml \
  --amostra data/processed/amostra-publicada-255/processed/deployment_frequency.json \
  --releases data/processed/amostra-publicada-255/raw/releases.json
```

Resultado: 60 repositórios e 300 releases, `total_populacao=255` e
`populacao_sha256=26b74c8b41531edf6a0b5fe6702d8856f2a5b0a2e0d1171c75e5c2be9f98e4e6`.
Em 34 das 300 releases a release sorteada é a primeira elegível do
repositório na janela, então `compare_url` fica vazio.

### Rascunho B assistido por IA (S02-07 — #157)

As [planilhas B e a orientação de revisão](docs/rotulagem-b-157.md) contêm
sugestões para os 60 projetos e 288 das 300 releases; 12 decisões permanecem
pendentes. Os arquivos identificam o apoio de IA e a revisão humana ainda
necessária. Esta preparação não equivale à rotulagem humana independente
concluída; fontes, limites e pendências estão documentados.

### Kappa de Fleiss entre os rotuladores (S02-09 — #159)

`pipeline/kappa.py` mede a concordância entre A, B e C **antes do consenso**
(#160), separadamente para `tipo_projeto`, `releases_sao_entregas_reais` e
`corretiva`. A partir de `Lab03`:

```bash
python -m pipeline.kappa
```

O comando é local e lê `validacao/amostra-ouro/`: o manifesto
`amostra_ouro.json` e as seis planilhas `rotulador_<X>_*.csv`. Ele recusa
itens fora do sorteio, chaves repetidas e valores fora do
[livro de códigos](validacao/amostra-ouro/LIVRO-CODIGOS.md). Células vazias
são ausências: o item só entra no cálculo da dimensão com os três julgamentos.

O kappa usa `aggregate_raters` e `fleiss_kappa(method="fleiss")` do
statsmodels, com categorias nominais. Sem itens completos, ou com todos os
julgamentos na mesma categoria (P_e = 1), a dimensão fica não estimável, com
motivo. A interpretação segue Landis e Koch (1977): pobre (< 0), leve (até
0,20), razoável (até 0,40), moderada (até 0,60), substancial (até 0,80) e
quase perfeita.

Saídas em `validacao/amostra-ouro/`: `kappa.json`, com itens completos,
ausências por rotulador, distribuição das categorias, itens unânimes, P_o,
P_e, kappa e SHA-256 das entradas, e `kappa.md`, com a tabela resumida.
`--pasta` e `--saida` trocam os caminhos de entrada e saída.

## Estrutura

```text
Lab03/
├── artigo/            # Seções do artigo em LaTeX (template SBC) e referências
├── config.yaml        # Parâmetros do pipeline (janela, critérios, caminhos)
├── docs/              # Definições operacionais e documentação
├── pipeline/          # Código do pipeline (entry point: python -m pipeline)
├── tests/             # Testes automatizados
├── validacao/         # Amostra-ouro: sorteio e planilhas de rotulagem
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
pelo menos cinco releases estáveis e cinquenta runs válidos na janela, ou esgotar o
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

A política principal atual usa `inclusao.incluir_prereleases=false`, conforme
as definições de deploy/inclusão atualizadas na #138. Pré-releases continuam
nos dados brutos para variantes. Configurações antigas sem a chave preservam
a inclusão anterior; `true` conta todas as releases publicadas. O mesmo filtro
é aplicado no prefiltro, funil e frequência de implantação. O hash do contexto
invalida checkpoints se essa política mudar.

A ordem é candidatos → Actions → metadados → releases → workflow runs →
critério mínimo → frequência de releases/CFR (a)/tempo de recuperação. O
prefiltro de releases evita coletar runs de quem já não satisfaz a inclusão.
O funil registra `prefiltro_releases_insuficientes` nessa passagem; ele não
infere quantos runs esses repositórios teriam. Meses com mais de 1000 resultados
são subdivididos recursivamente até caber na API. Saturação dentro de um único
segundo, contagem inconsistente nas folhas ou páginas ausentes mantêm `coleta_incompleta`;
repositórios parciais não contam para os 100 da execução completa.

Na coleta real da #151, intervalos amplos de `openclaw/openclaw` informaram
`total_count=2500` mesmo quando suas subfatias completas continham mais runs
(janeiro/2026: 9153 IDs únicos). O coletor reconhece esse teto observado
somente em intervalos subdivididos: todas as folhas devem estar completas,
e os IDs da página inicial do pai precisam aparecer na união das subfatias.
O diagnóstico mantém `total_api=2500`, `runs_retidos`, `total_api_limitado` e
`ids_pagina_inicial_ausentes`. Outras divergências de contagem continuam
marcando coleta incompleta. Isso trata a contagem limitada do pai sem aceitar
páginas ausentes ou saturação dentro de um segundo.

As consultas de runs usam `exclude_pull_requests=true`: a lista de pull
requests de cada run é a maior parte da resposta e não entra em nenhum cálculo.
Na seleção e no compare, `api.repositorios_paralelos` controla quantos
repositórios são processados ao mesmo tempo (1 a 8; padrão sem a chave: 1).
A configuração distribuída usa dois repositórios. A fila é limitada e os
resultados são consumidos na ordem da fonte, preservando os primeiros N
elegíveis. Perto do alvo, a fila diminui para não coletar candidatos extras.
Somente o coordenador escreve progresso e consolidados; cada worker escreve
seu checkpoint e devolve os runs resumidos. Em falhas, tarefas não iniciadas
são canceladas e as iniciadas terminam antes do retorno, preservando os
checkpoints já concluídos.

Dentro de cada fatia de até 1000 runs, as páginas seguintes à primeira são
consultadas em paralelo. `api.paralelismo` agora é o teto **global** de chamadas
HTTP simultâneas, incluindo todos os repositórios, páginas e retries (1 a 8;
padrão sem a chave: 1). A configuração distribuída usa quatro chamadas. O
cliente mantém uma sessão HTTP por thread e reutiliza o pool de páginas entre
meses. A cota esgotada pausa seu recurso; `Retry-After` e limites secundários
pausam todas as threads. Respostas atrasadas não revogam pausas vigentes e
prazos prolongados durante uma espera são conferidos novamente.

A consulta de contribuidores ocorre apenas após confirmar releases suficientes,
runs suficientes e coleta completa. Metadados de candidatos descartados podem
ter `contribuidores=null`, `contribuidores_pendentes=true` e uma observação de
coleta adiada; esses dados parciais não entram no cache de metadados completos.
A amostra aprovada recebe os metadados completos, inclusive quando o endpoint
de contribuidores informa que a lista é grande demais (nulo com justificativa).
O contexto inclui a versão do coletor de runs. A versão 2 reavalia checkpoints
de versões anteriores para não perpetuar descartes por contagem limitada;
as páginas do cache e os meses completos do piloto continuam reutilizáveis.

`processed/execucao.json` inclui `desempenho`: tempo de seleção/coleta, compare,
cálculos locais e total; número de tentativas HTTP, acertos no cache de respostas,
retries e segundos de espera por rate limit/backoff. Os contadores HTTP são
referentes à execução atual; tempos de espera somam as esperas de cada thread
e podem superar o tempo de parede. Busca de candidatos e preparação entram
no tempo total. Acertos em checkpoints e no cache de metadados evitam HTTP,
mas não entram em `cache_hits`, que conta apenas respostas GET do cache.
Para comparar configurações, use a mesma fonte, critérios e estado inicial de
cache/checkpoints em diretórios de saída separados. Aumente a concorrência
somente quando a redução de tempo compensar as esperas e retries observados;
mais threads não aumentam a cota da API.

Checkpoints atômicos e compactos por repositório ficam em `raw/checkpoints/<hash>/`. O hash
inclui fonte, janela, critérios, regras e API. Uma retomada reutiliza os
repositórios concluídos e páginas do cache; um erro temporário não apaga o
progresso anterior. `raw/progresso.json` permite acompanhar a execução.
No Windows, leitores do progresso e antivírus podem bloquear brevemente a
substituição de um JSON. A escrita atômica repete a substituição até oito
tentativas, com esperas curtas (até 0,81 s no total), sem reserializar o arquivo
nem repetir consultas à API. Bloqueios persistentes e outros erros de escrita
continuam sendo propagados; o JSON anterior permanece íntegro.

Saídas: consolidados por etapa em raw; `amostra_workflow_runs.json` restrito aos
elegíveis completos; `funil.json`, `funil.md`, `deployment_frequency.json`,
`cfr.json`, `tempo_recuperacao.json`, `metricas.json` e `execucao.json` em processed. O exit code
é 0 quando o alvo é atingido, 3 quando faltam elegíveis e 2 em erro. A presença
de arquivos não comprova sucesso: confira `execucao_completa` e contagens.

O compare (#140) é coletado apenas para a amostra elegível, com checkpoints
próprios em `raw/checkpoints/compare/<hash>/`. Seu contexto inclui as releases,
a janela e a API. `raw/compare.json` e `execucao.json` registram comparações
completas, releases ignoradas e repositórios com compare incompleto. Um 404
nessa etapa mantém a amostra e sua incompletude explícita; a release ignorada
não produz lead time.
A retomada de compare não repete os cálculos de CFR/recuperação já auditados.

O comando também calcula lead time por release (#141) em
`processed/lead_time_release.json` e o confere contra os commits de origem em
`auditoria_lead_time.json`. A retomada reutiliza essa métrica apenas com origem
e hash de conteúdo/diagnósticos iguais, desconsiderando somente `gerado_em`.
Resultados auditados divergentes são recusados sem sobrescrever a saída.

O comando calcula também a variante por commit (#142) em
`processed/lead_time_commit.json`, a cada execução, e reúne todas as métricas
por repositório em `processed/metricas.json` (#152). A CFR (b) (#161) é a
dependência explícita em `execucao.json`.
A presença dos tipos de métrica implementados não comprova execução real
nem atendimento de todas as variantes do protocolo. A validação real dos 100 repositórios continua
pendente até haver evidência registrada no relatório.
