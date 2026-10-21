# Conferência do dicionário com a exportação offline (#154)

## Revisão de 20/10/2026

O contrato v1 e as 28 colunas são mantidos na
[entrega de 500](../entregas/s02-03-dataset-500/README.md). O manifesto e as
evidências dessa entrega registram a população, hashes e cobertura real por
variante. A seleção atingiu 500; o processamento final da coleta continua
parcial. Nulos e classes nulas permanecem explícitos; CFR(b) é a saída da
heurística v1, com validação humana #162 pendente. Os números abaixo são a
conferência histórica de 255 e não descrevem a cobertura atual.

## Conferência histórica de 15/10/2026

A revisão mantém o contrato `lab03-dataset-v1` e suas 28 colunas. A população
foi encerrada por instrução humana em 15/10/2026 com 255 IDs elegíveis entre
561 candidatos avaliados. Não se afirma atendimento ao mínimo original de
300, à meta de 500 ou à conclusão original da coleta.

## O que foi corrigido

- A situação da entrega passou de contrato proposto para contrato conferido
  com `pipeline/dataset_csv.py` da #153.
- O nome exportado preserva a identidade da fonte da amostra; renomeações
  confirmadas pelo mesmo ID ficam na proveniência JSON.
- A política da reconstrução offline acrescenta `true` a `coleta_incompleta`
  e `calculo_parcial` quando não existe compare local para um ID selecionado.
  Esse comportamento complementa o OR dos indicadores nas fontes existentes.
- Lead time e classes ficam nulos quando o compare não foi coletado. CFR (b)
  e sua classe continuam nulas enquanto a #161 estiver pendente.

Não se alteraram colunas, unidades, fórmulas científicas ou cortes de classes.
Não se recriou o dicionário nem se preencheram métricas ausentes.

## Correspondência do contrato

| Grupo | Conferência |
|---|---|
| Identidade e população | Uma linha por ID de `deployment_frequency.json`; igualdade com os 255 IDs congelados, junção por ID e conferência do nome sem distinguir caixa. |
| 13 campos de identidade/janela/metadados | Tipos e nulabilidade correspondem ao exportador; timestamps têm fuso, são convertidos a UTC e preservam a janela inclusiva/exclusiva. Idade usa fim da janela; contribuidores nulos não viram zero. |
| 12 campos de métricas/classes | Seis variantes intercaladas com suas classes, sem arredondamento novo; DF em releases/semana, lead time/recuperação em horas, CFR em fração. Nulo exige classe nula. |
| 3 campos de qualidade | Booleanos `true`/`false`; lista JSON de métricas ausentes na ordem de `pipeline.metricas.METRICAS`. Compare faltante sinalizado explicitamente. |
| Serialização | UTF-8, vírgula, ponto decimal, nulo como célula vazia, escape CSV e listas JSON. Ordem crescente de ID; zero observado preservado. |
| Fórmulas e classes | Conferidas com `metadados.py`, `metricas.py`, `lead_time_release.py`, `lead_time_commit.py`, `cfr.py`, `tempo_recuperacao.py` e `classificacao.py`. Contrato de cortes `lab03-enunciado-cortes-v2`. |
| Limitações | Compares ausentes e censuras não são inferidos como zero; CFR (b) #161 pendente; recuperação descreve somente episódios observados. |

## Proveniência e validação final

Os hashes, revisão do exportador, contagens reais e verificações de estabilidade
estão no arquivo agregado [validacao-dicionario-154.json](validacao-dicionario-154.json).
O CSV e o manifesto pertencem à entrega #153, na branch
`feat/s02-03-dataset-153`, diretório `Lab03/entregas/s02-03-dataset-153/`.
Os dados brutos/cache e o snapshot permanecem privados.

## Resultado da conferência real

Foram conferidas **255 linhas e 28 colunas**, com IDs únicos iguais à população
congelada e janela UTC correspondente. O CSV reserializado das fontes locais
é byte a byte idêntico ao entregue. Os hashes das entradas e do CSV conferem
com o manifesto; as entradas ficaram estáveis antes/depois da leitura.

| Variante | Valores disponíveis | Nulos |
|---|---:|---:|
| Deployment frequency | 255 | 0 |
| Lead time (a) | 9 | 246 |
| Lead time (b) | 9 | 246 |
| CFR (a) | 255 | 0 |
| CFR (b), pendente #161 | 0 | 255 |
| Recuperação | 241 | 14 |

Os 246 IDs sem compare local têm ambos os indicadores de incompletude
verdadeiros; `calculo_parcial` é verdadeiro em 247 linhas, pois também preserva
um diagnóstico parcial de lead time (b) entre os compares disponíveis.
As classes de todas as linhas foram conferidas com o código de classificação;
nulos e zeros observados permaneceram distintos.

O agente #153 reportou 98 testes finais aprovados em conjunto (20 específicos e 78 de integração).
Esta conferência #154 verificou adicionalmente os dados reais, a ordem exata das
colunas, serialização, listas/nulos/booleanos, identidade, janela, proveniência,
classes e estabilidade das entradas. Links Markdown locais e `git diff --check`
foram verificados. As auditorias de runs e dos compares disponíveis estão
validadas; a cobertura de compare continua limitada a 9 dos 255 repositórios.

Revisão auditada do exportador: `ff017109897f42f228342252599516a07fdb1ac5`
na branch `feat/s02-03-dataset-153`; código, CSV e manifesto publicados.
A última proteção acrescentada ao exportador exige caminhos distintos para CSV
e manifesto; a reexportação confirmou os mesmos bytes do CSV e manifesto.
