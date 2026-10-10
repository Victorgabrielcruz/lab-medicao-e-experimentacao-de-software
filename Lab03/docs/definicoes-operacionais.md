# Janela de observação e definições operacionais

Este documento fixa as regras usadas na coleta e no cálculo das métricas DORA. Os valores numéricos correspondentes ficam em [`config.yaml`](../config.yaml) e são validados pelo pipeline ao iniciar.

## 1. Janela de observação

| Parâmetro | Valor |
|---|---|
| Início | 2025-10-01 00:00:00 UTC (inclusivo) |
| Fim | 2026-09-30 23:59:59 UTC (inclusivo) |
| Duração | 12 meses civis completos |

No código, a janela é tratada como o intervalo semiaberto `[2025-10-01T00:00Z, 2026-10-01T00:00Z)` (`pipeline.config.janela_utc`).

Justificativa da escolha:

- **Período fechado e anterior à coleta.** A janela termina antes do início do trabalho (08/10/2026), evitando meses ainda em curso. Isso não torna os registros imutáveis: retenção/remoção de runs e edição/publicação posterior de releases podem alterar uma nova consulta. A reprodução exige identificar o snapshot coletado, a configuração e os diagnósticos de incompletude.
- **Meses civis completos.** A coleta de workflow runs é subdividida por mês para respeitar o limite de 1000 resultados por consulta. Com meses completos, não há fatias parciais nas pontas.

O pipeline recusa executar se a janela configurada não cobrir exatamente 12 meses.

## 2. Deploy

- **Deploy = release publicada estável** no GitHub: `draft = false`, `prerelease = false` e `published_at` dentro da janela.
- A data do deploy é o `published_at` da release.
- Pré-releases ficam fora da definição principal e são usadas como variantes na RQ07. A coleta S01-10 (#138) as preserva com `prerelease = true`; `total_releases_estaveis` contabiliza apenas a definição principal, enquanto `total_releases` inclui também as pré-releases publicadas na janela.
- Tags sem release (com a data do commit da tag) são coletadas apenas como definição alternativa de deploy na RQ07.

A coleta de tags S01-11 (#139) inclui todas as tags, com ou sem release
associada. Sua data de referência é `commit.author.date` do commit identificado
pelo SHA retornado por `GET /repos/{owner}/{repo}/tags`, consultado em
`GET /repos/{owner}/{repo}/commits/{sha}`. Usa a mesma janela UTC semiaberta da
coleta de releases; a data do committer e a data de criação de tags anotadas
não são usadas. Nomes distintos no mesmo commit são preservados e duplicatas
por nome são removidas. Tags sem data válida ou com commit inacessível ficam
registradas como ignoradas e a coleta do repositório é marcada como incompleta.

## 3. Workflow runs

| Regra | Valor |
|---|---|
| Branch | apenas o default branch do repositório |
| Evento | `event = push` |
| Sucesso | `conclusion = success` |
| Falha | `conclusion` em `failure`, `timed_out` ou `startup_failure` |
| Ignorados | qualquer outra conclusion (`cancelled`, `skipped`, `neutral`, `action_required`, `stale` etc.) e runs sem conclusion |
| Data do run | `created_at`, dentro da janela |

Um **run válido** é um run do default branch, com `event = push`, criado dentro da janela e classificado como sucesso ou falha.

## 4. Critério mínimo de inclusão

Um repositório entra na amostra somente se, dentro da janela, tiver:

- **pelo menos 5 releases publicadas estáveis**; e
- **pelo menos 50 runs válidos**.

Antes disso, são descartados os repositórios **sem GitHub Actions**: os que não têm nenhum workflow com path em `.github/workflows/` no endpoint `GET /repos/{owner}/{repo}/actions/workflows`. O `total_count` do endpoint sozinho não serve, porque inclui workflows dinâmicos criados pelo próprio GitHub (path `dynamic/...`, como Dependabot Updates, Dependency Graph, CodeQL e Pages). Eles aparecem até em repositórios que nunca configuraram Actions; por exemplo, `torvalds/linux` tem `total_count = 2` e nenhum workflow próprio.

Repositórios que respondem 404 ou 451 nessa consulta (removidos, tornados privados ou bloqueados depois da busca) também são descartados.

Cada descarte é registrado com o motivo na tabela do funil de seleção (`pipeline/funil.py`): `sem_github_actions` ou `repositorio_inacessivel` nas etapas de coleta e, no critério mínimo, `releases_insuficientes`, `runs_validos_insuficientes` ou `releases_e_runs_insuficientes` (um único motivo por repositório).

## 5. Métricas

| Métrica | RQ | Variantes |
|---|---|---|
| Deployment frequency | RQ01 | releases estáveis publicadas / semanas reais da janela |
| Lead time | RQ02 | (a) por release; (b) por commit |
| Change failure rate | RQ03 | (a) runs com falha / (falhas + sucessos); (b) releases corretivas (heurística validada manualmente) |
| Tempo de recuperação | RQ04 | episódios de falha por workflow, com censura no fim da janela |

Os resultados são reportados por **mediana e IQR**. O detalhamento de cada variante é feito nas issues de implementação correspondentes.

### 5.1 Tempo de recuperação (RQ04)

O enunciado oficial fornecido em 08/10/2026 define a fórmula
`success.updated_at - first_failure.run_started_at`. O contrato é
`rq04-updated-at-run-started-at-v2`; a versão anterior por `created_at`
não satisfaz a RQ04. A entrada continua restrita a runs criados na janela,
do default branch e com evento push. Em cada workflow, a sequência é ordenada
por `run_started_at` e ID; a primeira falha **após um sucesso observado**
abre o episódio, e o próximo sucesso o encerra em seu `updated_at`.
Falhas consecutivas mantêm o início; conclusions ignoradas não o alteram.

Se o sucesso termina em/após o fim exclusivo da janela, o episódio é censurado
nesse limite, mesmo quando o run foi criado dentro da janela. Sua duração é
um limite inferior, excluído da mediana/IQR dos recuperados.
`proporcao_censurados` é censurados/total de episódios definidos, ou null
quando não há episódios. A primeira sequência de falhas sem sucesso anterior
observado é registrada separadamente em `historico_inicial_nao_observado`,
como censura à esquerda: não se presume um início nem uma duração conhecida.

Não há fallback para criação. Timestamps essenciais ausentes, sem fuso,
inválidos ou contraditórios invalidam a estimativa daquele workflow inteiro,
preservando seus IDs/motivos: retirar somente um run poderia unir episódios.
Runs iniciados depois da janela são diagnosticados. Essas limitações temporais
e `coleta_incompleta` permanecem explícitas. Os demais workflows válidos podem
contribuir à mediana. Quartis usam interpolação inclusiva; uma recuperação tem
IQR zero e nenhuma recuperação produz estatísticas/classificação null.
### Commits entre releases (S01-12 — #140)

Os dados para lead time vêm de `compare/{release anterior}...{release atual}`,
entre releases estáveis em ordem de publicação. A release atual deve estar na
janela, mas sua anterior pode estar fora dela. A primeira release histórica,
sem anterior, é ignorada e contabilizada. Commits usam `commit.author.date` e
podem ter sido escritos antes da janela.

A coleta sempre pagina, evitando o limite de 250 commits das consultas sem
paginação. Esse limite e a quantidade recuperada ficam registrados. Um compare
com HTTP 404 (tag apagada ou inacessível) ignora somente a release atual, registra
o motivo e continua os próximos pares. Comparações incompletas também são
ignoradas, preservando os dados parciais para auditoria. A quantidade de releases
ignoradas e a parcela com HTTP 404 são informadas por repositório e no consolidado.
O cálculo por release é feito pela S01-13 e a variante por commit pela S01-14.

### Lead time por release (RQ02a — S01-13 — #141)

Para cada release estável com comparação completa, o lead time é
`release.published_at - min(commit.author.date)`, expresso em horas. O valor do
repositório é a mediana dos lead times calculados por release, sem ponderar pelo
número de commits. Usa a data do autor, inclusive antes da janela, com os fusos
convertidos para UTC.

A primeira release histórica sem anterior, releases sem commits novos e
comparações ignoradas/incompletas recebem valor nulo e não entram na mediana.
Datas de autor inválidas também invalidam a release inteira, pois o mínimo fica
desconhecido. Um intervalo negativo é registrado como inválido; zero real é
válido. As releases ignoradas são contadas com seus motivos. Sem valores válidos,
a mediana e a classificação C1 ficam nulas. Uma mediana baseada em um repositório
parcial mantém o diagnóstico de coleta incompleta.

O cálculo local lê `data/raw/compare.json` e grava
`data/processed/lead_time_release.json`, preservando os resultados por release
e a mediana/classificação por repositório. Não usa token nem consulta a API.

### Lead time por commit (RQ02b — S01-14 — #142)

Cada par commit–release contribui com `release.published_at - commit.author.date`,
em horas. O valor do repositório é a mediana de todos os intervalos válidos de
todas as releases estáveis da janela. A release de 15/03 com commits de 02/03,
10/03 e 14/03 produz 13, 5 e 1 dias, cuja mediana é 5 dias (120 horas).

A data do autor é convertida para UTC e pode estar antes da janela. Duplicatas
por SHA são removidas dentro de cada release; o mesmo SHA em outra release
representa outro par commit–release. Primeira release sem anterior, releases
sem commits novos e comparações ignoradas/incompletas ficam fora da métrica.
Datas de autor inválidas ou intervalos negativos invalidam o commit individual.
Uma mediana baseada nos demais valores é marcada como cálculo parcial, com
motivos e contagens registrados. Zero real é válido; sem valores válidos, a
mediana e a classificação C1 ficam nulas.

O cálculo local lê `data/raw/compare.json` e grava
`data/processed/lead_time_commit.json`, mantendo os intervalos por commit e a
mediana/classificação por repositório. Não usa token nem consulta a API.

## 6. Metadados dos repositórios

Fatores usados nas análises, coletados para cada repositório aprovado no filtro de Actions:

| Fator | Origem | Observação |
|---|---|---|
| Estrelas | `stargazers_count` de `GET /repos/{owner}/{repo}` | valor no momento da coleta |
| Linguagem principal | `language` | pode ser nula |
| Idade | `created_at` | dias completos até o fim da janela (`2026-10-01T00:00Z`), não até a data da coleta, para o valor não depender de quando o pipeline roda |
| Default branch | `default_branch` | usada também na coleta de workflow runs |
| Contribuidores | Link header de `GET /repos/{owner}/{repo}/contributors?per_page=1&anon=1` | o número da página `rel="last"` é o total |

Sobre os contribuidores:

- **`anon=1`:** sem esse parâmetro, o GitHub só associa a usuários os primeiros 500 e-mails de autor, e a contagem de repositórios grandes fica presa perto de 400 (`pallets/flask` dá 400 sem e 864 com). Com ele, autores sem conta vinculada também contam; um autor com vários e-mails não vinculados pode ser contado mais de uma vez.
- **Repositórios grandes demais:** para alguns, a API responde 403 ("contributor list is too large"), como em `torvalds/linux`. Nesses casos o valor fica nulo, com o motivo em `contribuidores_obs`, e o repositório não é descartado.

## 7. Classificação DORA de referência (C1)

Usamos os cortes fixos do enunciado oficial fornecido pelo usuário, versão
`lab03-enunciado-cortes-v2`. A tabela anterior adaptada de 2021 era divergente
para DF e lead time e não deve ser usada para o aceite do protocolo.

| Métrica | Unidade | Elite | High | Medium | Low |
|---|---|---|---|---|---|
| Deployment frequency | releases/semana | ≥7 | ≥1 e <7 | ≥1 por mês e <1 por semana | <1 por mês |
| Lead time | horas | <24 | ≥24 e <168 | ≥168 e <720 | ≥720 |
| Change failure rate | fração | ≤0,15 | >0,15 e ≤0,30 | >0,30 e ≤0,45 | >0,45 |
| Tempo de recuperação | horas | <1 | ≥1 e <24 | ≥24 e <168 | ≥168 |

A DF divide a quantidade de releases pelas semanas reais:
`(fim_exclusivo - inicio).total_seconds() / 604800`.
Para o corte mensal civil, 1/mês equivale a 12 releases na janela de 12 meses;
o limite semanal correspondente é 12/semanas da janela. Isso trata anos de
365 e 366 dias sem usar uma aproximação de 52 semanas. A função genérica de
classificação toma 365 dias como referência; a integração usa a duração real.
`releases_ano` permanece apenas como contagem de compatibilidade, junto de
`releases_janela`; o valor de DF e sua unidade semanal são explícitos na saída.

Quando somente o contrato de classificação muda, o integrado audita primeiro
os valores de lead time existentes, migra suas classes e audita novamente.
Não repete a coleta nem o cálculo dos intervalos já auditados.

**Nota geral:** as classes viram notas (Low = 1, Medium = 2, High = 3, Elite = 4). A nota geral é a mediana das notas, arredondada para baixo, ou seja, para a classe pior em caso de empate (Elite, High, Medium e Low dá 2,5, que vira Medium). Uma métrica que não pôde ser calculada (por exemplo, tempo de recuperação sem nenhum episódio de falha) fica sem classe e não entra na mediana.
