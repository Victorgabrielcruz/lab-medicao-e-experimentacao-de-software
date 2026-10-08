# Lab03 — Mineração de métricas DORA

[![Lab03 CI](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml/badge.svg?branch=main)](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/actions/workflows/lab03-ci.yml)

Cálculo das quatro métricas DORA (deployment frequency, lead time, change failure rate e tempo de recuperação) a partir de dados públicos de repositórios open-source que usam GitHub Actions. A coleta é feita por script próprio sobre as APIs REST/GraphQL do GitHub, sem PyGithub.

## Documentação

| Documento | Conteúdo |
|---|---|
| [`docs/definicoes-operacionais.md`](docs/definicoes-operacionais.md) | Janela de observação, definição de deploy, regras de runs, critério de inclusão, filtro de Actions, metadados e tabela de classificação DORA (C1) |

## Como executar

Requer Python 3.11 ou superior.

```bash
cd Lab03
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GITHUB_TOKEN=<seu token>  # Windows (PowerShell): $env:GITHUB_TOKEN = "<seu token>"
python -m pipeline --config config.yaml
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
