# Rotulagem C — #158

## Estado da entrega local

Em 21/10/2026, foram analisados os 51 julgamentos ainda vazios, na branch
`feat/158-rotulagem-c`, sem push. A issue não foi alterada ou fechada.

- **60 tipos de projeto** e **60 decisões de entregas reais**, preservados;
- **300 releases**: **250 `sim` e 50 `nao`**, cinco por projeto;
- **51 casos complementares**: 43 `sim` e 8 `nao`, confirmados pelo responsável;
- **249 decisões anteriores preservadas**, inclusive suas observações.

Arquivos oficiais: [repositórios C](../validacao/amostra-ouro/rotulador_C_repositorios.csv)
e [releases C](../validacao/amostra-ouro/rotulador_C_releases.csv).

O sorteio da #155 permanece sobre os primeiros **255 elegíveis**:
60 projetos, 300 releases, `random_state=42`, janela UTC
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`. A captura de 500 não alterou
esse sorteio, conforme a [decisão de retomada](decisao-retomada-500.md).

## Evidências e validação

Em 21/10/2026, o responsável confirmou os 51 casos após apresentação
dos resumos das evidências: 43 `sim` e oito `nao`. O caso 39 foi resolvido
como `sim` após investigação adicional do compare da tag Windows-ARM64.
O [registro dos lotes](evidencias/158-confirmacoes-responsavel.json) descreve
o alcance dessa concordância; ela não comprova consulta direta das fontes
pelo responsável nem avaliação independente ou cega.

A [lista de revisão](revisao-c-158.md) apresenta os 51 casos, IDs, decisões,
justificativas e fontes. O [relatório desta etapa](evidencias/158-revisao-c.json)
registra limitações, contagens e hashes antes/depois. As respostas
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

As observações dos 51 casos registram a confirmação pelo responsável
após apresentação dos resumos das evidências. A análise inicial e a
confirmação posterior estão registradas separadamente. Não foram lidos
CSVs A/B nem executada/consultada a heurística CFR(b). No levantamento
foram abertos a documentação e o relatório histórico de B (#157), incluindo
suas pendências; portanto esta sessão **não comprova avaliação cega**.
As decisões complementares foram fundamentadas nas próprias fontes das
releases. O desenho real deve acompanhar a análise de
independência e eventual cálculo de concordância.

## Situação após a revisão em lotes

Os 51 casos complementares foram confirmados pelo responsável. Não há
células de julgamento vazias no CSV C de releases. As contagens são
250 `sim` e 50 `nao`; IDs, campos fixos, ordem e cinco releases por
projeto foram conferidos contra o manifesto oficial.

Os 60 projetos e os 249 julgamentos anteriores foram preservados nesta
revisão. O requisito de independência e o aceite final da #158 continuam
separados da confirmação das decisões. A issue não foi fechada, e nenhum
push foi realizado nesta revisão.

## Declaração do responsável sobre a conferência anterior

Em 21/10/2026, o responsável declarou ter conferido os 60 projetos e os
249 julgamentos anteriores sem consultar as classificações de A/B nem os
resultados da heurística CFR(b). Esta é a data da declaração; a data
original da conferência não foi informada.

A declaração refere-se à conferência anterior. Os 51 casos complementares
foram confirmados após apresentação de resumos das evidências, conforme o
registro dos lotes. O aceite do requisito de independência deve considerar
o procedimento de cada etapa.
