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

- **Período fechado e anterior à coleta.** A janela termina antes do início do trabalho (08/10/2026), então releases e runs dentro dela não mudam mais. Isso deixa os resultados reprodutíveis por quem executar o pipeline depois, inclusive o grupo replicador.
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

Cada descarte é registrado com o motivo (`sem_github_actions` ou `repositorio_inacessivel`) na tabela do funil de seleção.

## 5. Métricas

| Métrica | RQ | Variantes |
|---|---|---|
| Deployment frequency | RQ01 | releases publicadas na janela |
| Lead time | RQ02 | (a) por release; (b) por commit |
| Change failure rate | RQ03 | (a) runs com falha / (falhas + sucessos); (b) releases corretivas (heurística validada manualmente) |
| Tempo de recuperação | RQ04 | episódios de falha por workflow, com censura no fim da janela |

Os resultados são reportados por **mediana e IQR**. O detalhamento de cada variante é feito nas issues de implementação correspondentes.

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
O cálculo por release é feito pela S01-13; a variante por commit é uma etapa posterior.

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

Cada métrica é classificada em Elite, High, Medium ou Low (`pipeline/classificacao.py`). A tabela parte do *Accelerate State of DevOps 2021*, o último relatório com as quatro classes:

| Métrica | Unidade | Elite | High | Medium | Low |
|---|---|---|---|---|---|
| Deployment frequency | deploys por ano | ≥ 365 (pelo menos 1 por dia) | ≥ 12 (pelo menos 1 por mês) | ≥ 2 (pelo menos 1 a cada 6 meses) | < 2 |
| Lead time | horas | < 1 hora | < 1 semana | < 6 meses | ≥ 6 meses |
| Change failure rate | fração | ≤ 15% | ≤ 30% | ≤ 45% | > 45% |
| Tempo de recuperação | horas | < 1 hora | < 1 dia | < 1 semana | ≥ 1 semana |

Ajustes em relação ao relatório:

- **Lacunas fechadas.** Os intervalos do relatório não são contíguos. Por exemplo, o lead time High é "entre 1 dia e 1 semana", e o Medium é "entre 1 mês e 6 meses". Aqui cada valor cai na melhor classe cujo limite ele atende, então 6 horas é High e 2 semanas é Medium.
- **Change failure rate.** O relatório de 2021 dá "16–30%" para High, Medium e Low, sem diferenciá-las. Aqui a faixa Elite do relatório (até 15%) é mantida, e as demais seguem o mesmo passo de 15 pontos (30% e 45%). É a escolha mais arbitrária da tabela.
- **Tempo de recuperação Low.** O relatório define Low como "mais de 6 meses", deixando de fora o intervalo de 1 semana a 6 meses. Aqui Low começa em 1 semana.
- **Deployment frequency.** Como a janela tem 12 meses, deploys por ano é o número de releases na janela. Com o critério de inclusão de pelo menos 5 releases, nenhum repositório da amostra fica em Low nessa métrica.

**Nota geral:** as classes viram notas (Low = 1, Medium = 2, High = 3, Elite = 4). A nota geral é a mediana das notas, arredondada para baixo, ou seja, para a classe pior em caso de empate (Elite, High, Medium e Low dá 2,5, que vira Medium). Uma métrica que não pôde ser calculada (por exemplo, tempo de recuperação sem nenhum episódio de falha) fica sem classe e não entra na mediana.
