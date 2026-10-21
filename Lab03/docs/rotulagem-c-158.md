# Rotulagem C — #158

## Estado da entrega local

Em 21/10/2026, o responsável informou que assumiu a tarefa de outro integrante
e que o professor autorizou o uso de IA. A seu pedido, o Codex analisou os
51 julgamentos ainda vazios, na branch `feat/158-rotulagem-c`, sem push.
A autorização é uma declaração do usuário. A issue não foi alterada ou fechada.

- **60 tipos de projeto** e **60 decisões de entregas reais**, preservados;
- **300 decisões de releases**: **250 `sim` e 50 `nao`**, cinco por projeto;
- **51 novas decisões por IA**: 43 `sim` e 8 `nao`, pendentes de validação humana;
- **249 decisões anteriores preservadas**, inclusive suas observações.

Arquivos oficiais: [repositórios C](../validacao/amostra-ouro/rotulador_C_repositorios.csv)
e [releases C](../validacao/amostra-ouro/rotulador_C_releases.csv).

O sorteio da #155 permanece sobre os primeiros **255 elegíveis**:
60 projetos, 300 releases, `random_state=42`, janela UTC
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`. A captura de 500 não alterou
esse sorteio, conforme a [decisão de retomada](decisao-retomada-500.md).

## Evidências e validação

A [lista de revisão](revisao-c-158.md) apresenta os 51 casos, IDs, decisões,
justificativas e fontes. O [relatório desta etapa](evidencias/158-revisao-c-ia.json)
registra autoria, limitações, contagens e hashes antes/depois. As respostas
públicas e seu índice estão em [158-fontes-publicas.zip](evidencias/158-fontes-publicas.zip).

A [cópia anterior do CSV](evidencias/158-rotulador_C_releases-antes.csv)
preserva os 249 julgamentos e 51 vazios recebidos. A
[transferência anterior](evidencias/158-transferencia-c.json) e a
[proposta-C](../validacao/amostra-ouro/proposta-C/README.md) permanecem históricas:
suas contagens descrevem as etapas anteriores, sem substituírem esta revisão.

Foram conferidos os 60 IDs e 300 pares contra o manifesto, cinco releases
por projeto, ausência de duplicatas, códigos válidos, cabeçalhos, ordem,
campos fixos e UTF-8 com BOM. Campos `null` do manifesto correspondem a
células vazias do CSV. O manifesto e o CSV de repositórios C ficaram idênticos
aos recebidos. A validação estrutural não substitui a revisão dos julgamentos.

## Procedimento e limites

Seguiu-se o [livro de códigos #155](../validacao/amostra-ouro/LIVRO-CODIGOS.md):
`sim` exige ao menos uma correção de defeito, inclusive em release mista.
Dependências, documentação e funcionalidades isoladas não bastam. `nao`
significa nenhuma correção identificada no material examinado, sem provar
ausência em commits não examinados. Não houve classificação por SemVer ou
palavra-chave isolada.

Usaram-se notas dos checkpoints congelados e consultas pontuais a changelogs,
PRs e compares públicos. Nenhum coletor foi reiniciado, nenhum dado bruto
foi alterado e nenhum sorteio foi refeito. Em Julia/ClickHouse usaram-se
fontes da própria série quando identificadas; em create-vite, apenas a seção
da versão/subpacote correspondente. Compares da API podem ser parciais:
uma correção concreta basta para `sim`, mas não prova inspeção exaustiva.

As novas observações declaram **IA/Codex e validação humana pendente**.
Não foi afirmada revisão humana já realizada nesta etapa. Não foram lidos
CSVs A/B nem executada/consultada a heurística CFR(b). No levantamento
foram abertos a documentação e o relatório histórico de B (#157), incluindo
suas pendências; portanto esta sessão **não comprova avaliação cega**.
As decisões complementares foram fundamentadas nas próprias fontes das
releases. Essa assistência e o desenho real devem acompanhar a análise de
independência e eventual cálculo de concordância.

## Arquivos para validar

1. Revisar as 51 justificativas em [revisao-c-158.md](revisao-c-158.md),
   confrontando-as com as fontes e com o CSV de releases C.
2. Conferir os 60 projetos no CSV de repositórios C: a classificação anterior
   foi preservada e não foi reavaliada nesta complementação.
3. Conferir o relatório JSON e a metodologia acima; registrar mudanças e
   a revisão humana sem apagar o histórico de IA.

Dar atenção à atribuição das mudanças à tag Unsloth ARM64, às correções de
distribuição da CLI, às releases de subpacotes e à definição de corretiva
usada no artigo. O preenchimento está completo; a revisão humana e a
avaliação do requisito de independência continuam necessárias para a entrega.
A entrega será registrada em commit local com referência à #158, sem push.
