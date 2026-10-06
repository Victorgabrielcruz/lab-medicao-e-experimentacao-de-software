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

- **Deploy = release publicada** no GitHub: `draft = false` e `published_at` dentro da janela.
- A data do deploy é o `published_at` da release.
- Pre-releases fazem parte da definição principal. O campo `prerelease` é armazenado para permitir variantes na RQ07.
- Tags sem release (com a data do commit da tag) são coletadas apenas como definição alternativa de deploy na RQ07.

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

- **pelo menos 5 releases publicadas**; e
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
