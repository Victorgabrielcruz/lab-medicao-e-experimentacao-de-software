# Dicionário de dados — dataset consolidado do Lab03 (#154)

## Escopo e situação da entrega

Este documento versiona o contrato **`lab03-dataset-v1`**: uma linha por
repositório incluído na amostra final, com metadados e as seis métricas/variantes
produzidas por [`pipeline/metricas.py`](../pipeline/metricas.py).
O formato tabular corresponde às 28 colunas do exportador local da **#153**,
`pipeline/dataset_csv.py`, na branch `feat/s02-03-dataset-153`. Esta revisão
mantém o contrato v1 e documenta a amostra encerrada por decisão humana em
15/10/2026: **255 repositórios elegíveis entre 561 candidatos avaliados**.
A janela permanece de `2025-10-01T00:00:00Z` (inclusivo) a
`2026-10-01T00:00:00Z` (exclusivo). O mínimo planejado de 300 e a meta de 500
não foram atingidos; a autorização para usar os dados obtidos não equivale
à conclusão do pipeline de coleta originalmente planejado.

A consolidação offline usa o snapshot congelado identificado pelo manifesto
privado `encerramento-amostra.json`; não consulta a API nem amplia a amostra.
As evidências da conferência estão em
[validacao-dicionario-154.md](validacao-dicionario-154.md).

O dicionário descreve o significado dos campos; os resultados da coleta #151 e
os rótulos humanos da #158 não são presumidos. A CFR (b) depende da heurística
validada na #161. Ausência dessa variante deve permanecer explícita.

## Grão, seleção e convenções

- Chave primária: `id` do GitHub; `full_name` preserva o nome da fonte da
  amostra. A junção usa o ID e confere o nome sem distinguir maiúsculas de
  minúsculas. Renomeações confirmadas pelo mesmo ID preservam o nome da fonte
  nos estágios; `full_name_atual` e o registro de renomeação ficam na
  proveniência JSON, sem acrescentar coluna ao CSV.
- População do CSV final: IDs de `processed/deployment_frequency.json`,
  que o integrado gera para os elegíveis com coleta completa de runs. A união
  de IDs feita por `metricas.consolidar` não substitui esse filtro: saídas
  avulsas podem conter repositórios fora da amostra final. Nesta entrega,
  essa população reproduz exatamente os 255 IDs elegíveis dos checkpoints
  consumidos pelo progresso oficial no instante do encerramento. Checkpoints
  auxiliares ainda não consumidos não ampliam a população.
- Cada ID deve ocorrer uma vez nas fontes e no CSV. IDs/nome divergentes,
  janela incompatível e metadados ausentes para um ID selecionado devem causar
  erro de consolidação, em vez de descartar silenciosamente a linha.
- Caminhos `raw/` e `processed/` são relativos aos diretórios configurados,
  inclusive quando apontam para `amostra-final-500/`.
- Datas são ISO 8601 com fuso explícito, convertidas a UTC na exportação.
  `janela_inicio` é inclusivo; `janela_fim_exclusivo` é exclusivo.
- JSON usa `null` para valor ausente. O contrato CSV usa célula vazia para
  nulo, UTF-8, cabeçalho, vírgula como separador e ponto decimal, sem separador
  de milhar. Booleanos são `true`/`false`; listas usam JSON dentro da célula,
  com o escape de aspas normal do CSV. `[]` significa lista conhecida vazia.
- Zero observado é um valor válido e não preenche uma ausência. Textos vazios
  de observação equivalem a ausência de observação, não a falha de coleta.

## Colunas do contrato de consolidação (28)

### Identidade, janela e metadados (13)

Fonte **M**: `raw/metadados.json`, lista `repositorios`, produzida por
[`pipeline/metadados.py`](../pipeline/metadados.py).
Fonte **J**: `processed/metricas.json`, objeto `janela`, conferido contra a
configuração. As datas de criação/coleta são atributos do repositório e não
os limites da janela.

| Coluna | Tipo lógico | Unidade/formato | Nulo? | Origem ou fórmula |
|---|---|---|---|---|
| `id` | inteiro | identificador GitHub | não | M.`id`, igual ao ID da amostra e das métricas. |
| `full_name` | texto | `owner/repo` | não | M.`full_name`; conferir identidade com a saída das métricas. |
| `janela_inicio` | timestamp | ISO 8601 UTC | não | J.`inicio`; nesta execução, `2025-10-01T00:00:00Z`. |
| `janela_fim_exclusivo` | timestamp | ISO 8601 UTC | não | J.`fim_exclusivo`; nesta execução, `2026-10-01T00:00:00Z`. |
| `estrelas` | inteiro | estrelas | não | M.`estrelas` = `stargazers_count`, observado na coleta/cache; não é o valor histórico ao fim da janela. |
| `linguagem` | texto | nome da linguagem | sim | M.`linguagem` = `language` da API; nulo se não identificada. |
| `created_at` | timestamp | ISO 8601 UTC | não | M.`created_at`, data de criação do repositório na API. |
| `idade_dias` | inteiro | dias completos | não | M.`idade_dias` = `(fim_exclusivo - created_at).days`. |
| `idade_anos` | decimal | anos | não | M.`idade_anos` = `round(idade_dias / 365.25, 2)`; arredondado somente este atributo. |
| `default_branch` | texto | nome do branch | não | M.`default_branch`, usado no filtro dos runs. |
| `contribuidores` | inteiro | entradas de autores | sim | M.`contribuidores`: última página de `/contributors?per_page=1&anon=1`; sem `last`, tamanho da resposta; HTTP 204 → zero. |
| `contribuidores_obs` | texto | diagnóstico | sim | M.`contribuidores_obs`; registra, por exemplo, lista grande demais para a API. Nulo indica ausência de observação. |
| `coletado_em` | timestamp | ISO 8601 UTC | não | M.`coletado_em`: criação do registro de metadados; o cache pode preservar uma data anterior à execução atual. |

`contribuidores` conta as entradas retornadas pelo GitHub, incluindo autores
anônimos. Vários e-mails não vinculados podem representar a mesma pessoa.
HTTP 403 de lista grande demais produz nulo com diagnóstico; não equivale a
zero contribuidores. Metadados com `contribuidores_pendentes=true` são
intermediários da seleção e não devem compor a entrega final.

### Métricas e respectivas classes (12)

Fonte **R**: `processed/metricas.json`, lista `repositorios`. Valores são
copiados sem novo arredondamento. Classes aceitas: `Elite`, `High`, `Medium`,
`Low` ou nulo. RQ02 (a)/(b) e RQ03 (a)/(b) são definições distintas: não se
faz média entre variantes.

| Coluna | Tipo lógico | Unidade | Nulo? | Origem ou fórmula |
|---|---|---|---|---|
| `deployment_frequency` | decimal | releases/semana | sim | R.`deployment_frequency` ← `deployment_frequency.json` com campo homônimo. Releases estáveis na janela / `((fim_exclusivo - inicio).total_seconds() / 604800)`. |
| `classe_deployment_frequency` | categoria | classe DORA | sim | R.`classe_deployment_frequency` ← `deployment_frequency.json`.`classe`; limites abaixo. |
| `lead_time_a` | decimal | horas | sim | R.`lead_time_a` ← `lead_time_release.json`.`lead_time_horas`. Mediana, entre releases válidas, de `(published_at - min(commit.author.date)) / 3600`. |
| `classe_lead_time_a` | categoria | classe DORA | sim | R.`classe_lead_time_a` ← `lead_time_release.json`.`classe_lead_time`. |
| `lead_time_b` | decimal | horas | sim | R.`lead_time_b` ← `lead_time_commit.json`.`lead_time_horas`. Mediana de todos os intervalos válidos `(published_at - commit.author.date) / 3600`, sem mediana intermediária por release. |
| `classe_lead_time_b` | categoria | classe DORA | sim | R.`classe_lead_time_b` ← `lead_time_commit.json`.`classe_lead_time`. |
| `cfr_a` | decimal | fração [0, 1] | sim | R.`cfr_a` ← `cfr.json`.`change_failure_rate` = falhas / (falhas + sucessos), no recorte de runs. Sem denominador → nulo. |
| `classe_cfr_a` | categoria | classe DORA | sim | R.`classe_cfr_a` ← `cfr.json`.`classe_cfr`. |
| `cfr_b` | decimal | fração [0, 1] | sim | R.`cfr_b` ← `cfr_b.json`.`change_failure_rate`. Definição prevista: releases estáveis corretivas / releases estáveis elegíveis na janela; heurística/validação dependem da #161. Não substituir pela CFR (a). |
| `classe_cfr_b` | categoria | classe DORA | sim | R.`classe_cfr_b` ← `cfr_b.json`.`classe_cfr`; permanece nulo enquanto a variante não estiver disponível. |
| `tempo_recuperacao` | decimal | horas | sim | R.`tempo_recuperacao` ← `tempo_recuperacao.json`.`tempo_recuperacao`. Mediana dos episódios recuperados: `(success.updated_at - first_failure.run_started_at) / 3600`. |
| `classe_tempo_recuperacao` | categoria | classe DORA | sim | R.`classe_tempo_recuperacao` ← `tempo_recuperacao.json`.`classe_tempo_recuperacao`. |

A frequência é nula no contrato genérico se faltar o valor na fonte; na
amostra final selecionada pelo integrado, a inclusão exige ao menos cinco
releases e essa métrica deve estar presente. Sem valores válidos de lead time
ou sem episódios recuperados, valor e classe correspondentes ficam nulos.

### Qualidade e ausências (3)

| Coluna | Tipo lógico | Unidade/formato | Nulo? | Origem ou fórmula |
|---|---|---|---|---|
| `coleta_incompleta` | booleano | `true`/`false` | não | R.`coleta_incompleta`: OR dos indicadores homônimos nas fontes presentes, acrescido de `true` para ID sem compare local no encerramento. Runs completos não garantem compare completo. |
| `calculo_parcial` | booleano | `true`/`false` | não | R.`calculo_parcial`: OR dos indicadores homônimos nas fontes presentes, acrescido de `true` para ID sem compare local no encerramento. Não resume todos os diagnósticos temporais da RQ04. |
| `metricas_ausentes` | lista de texto | array JSON | não | R.`metricas_ausentes`: nomes das seis métricas cujo valor é nulo, na ordem de `pipeline.metricas.METRICAS`. Não inclui os campos de classe. |

`coleta_incompleta=false` e `calculo_parcial=false` não garantem seis métricas
disponíveis nem ausência de censura. `cfr_b` pendente aparece em
`metricas_ausentes`, mesmo que os dois indicadores sejam falsos.

Na reconstrução offline da amostra encerrada, `pipeline/amostra_encerrada.py`
calcula lead time somente para compares locais efetivamente disponíveis.
Um ID sem compare mantém `lead_time_a`, `lead_time_b` e suas classes nulos;
`metricas_ausentes` inclui ambas as variantes e `cfr_b`. A união
`metricas.json` marca `coleta_incompleta=true`, `calculo_parcial=true` e o
atributo JSON `compare_ausente_no_encerramento=true`. Esse último atributo não
é coluna adicional. Não se sintetizam compares vazios nem se converte ausência
em zero. A auditoria de lead time registra a cobertura de compare; validar os
compares disponíveis não afirma cobertura da população inteira.

## Fontes complementares e rastreabilidade

Os campos abaixo **não são colunas adicionais do contrato CSV v1**. Devem
permanecer disponíveis nos JSONs de origem e ser consultados nas análises:

| Arquivo | Campos | Significado/tipo/unidade |
|---|---|---|
| `metricas.json` | `janela`, `origens`, `unidades`, `variantes_pendentes`, `gerado_em` | Objetos de proveniência, lista de variantes sem arquivo e timestamp de geração; `gerado_em` não é a data dos metadados. |
| `deployment_frequency.json` | `releases_janela`, `releases_ano`, `semanas_janela`, `incluir_prereleases` | Contagens inteiras equivalentes (alias legado `releases_ano`), duração decimal em semanas no cabeçalho e booleano da definição de deploy. |
| `cfr.json` | `falhas`, `sucessos`, `ignorados`, `runs_validos` | Contagens inteiras; `runs_validos = falhas + sucessos`. |
| `tempo_recuperacao.json` | `total_episodios`, `episodios_recuperados`, `episodios_censurados` | Contagens inteiras; total = recuperados + censurados à direita. Sequências com censura à esquerda são separadas. |
| `tempo_recuperacao.json` | `proporcao_censurados` | Fração censurados à direita / total de episódios; nula se total zero. |
| `tempo_recuperacao.json` | `q1_horas`, `q3_horas`, `iqr_horas` | Decimais em horas dos episódios recuperados; IQR = Q3 − Q1, interpolação inclusiva. Um recuperado → IQR zero; nenhum → nulos. |
| `tempo_recuperacao.json` | `historico_inicial_nao_observado` | Lista de sequências de falha sem sucesso anterior observado; duração nula, sem presumir início. |
| `tempo_recuperacao.json` | `dados_temporais_incompletos`, `workflows_com_dados_temporais_invalidos`, `runs_iniciados_fora_janela` | Booleano e listas de diagnóstico; não são propagados automaticamente pelo `metricas.consolidar`. |
| `execucao.json`, `auditoria.json`, `auditoria_lead_time.json` | `contexto`, `entrada_sha256`, `entrada_semantica_sha256` conforme o arquivo | Configuração e identificação das entradas auditadas. Guardar também o commit do código e os hashes das fontes usadas na exportação #153. |

As estatísticas de recuperação excluem censurados à direita e à esquerda.
Por isso descrevem recuperações observadas, não uma estimativa de sobrevivência
da população inteira. Os JSONs detalhados preservam episódios e motivos de
exclusão para permitir a avaliação dessa limitação.

## Classes e regras comuns

Contrato de classificação: `lab03-enunciado-cortes-v2`, implementado em
[`pipeline/classificacao.py`](../pipeline/classificacao.py).

| Métrica | Elite | High | Medium | Low |
|---|---|---|---|---|
| DF (releases/semana) | ≥ 7 | ≥ 1 e < 7 | ≥ 12/semanas da janela e < 1 | < 12/semanas da janela |
| Lead time (horas), a/b | < 24 | ≥ 24 e < 168 | ≥ 168 e < 720 | ≥ 720 |
| CFR (fração), a/b | ≤ 0,15 | > 0,15 e ≤ 0,30 | > 0,30 e ≤ 0,45 | > 0,45 |
| Recuperação (horas) | < 1 | ≥ 1 e < 24 | ≥ 24 e < 168 | ≥ 168 |

Para a DF, o corte Medium equivale a 12 releases nos 12 meses civis,
sem aproximar a janela por 52 semanas. A classificação geral calculada por
`nota_geral` não é emitida por `metricas.json` e não é uma coluna deste
contrato; as combinações C1/C2/C3 da RQ07 são outra entrega.

Regras de seleção, recorte dos runs, interpretação de comparações e censura:
[`definicoes-operacionais.md`](definicoes-operacionais.md). A descrição no
artigo está em [`artigo/metodologia.tex`](../artigo/metodologia.tex) (#166).
