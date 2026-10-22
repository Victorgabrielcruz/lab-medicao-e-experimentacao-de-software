# Refinamento da heurística corretiva — S02-13 (#163)

## Decisão em 22/10/2026

**Manter `corretiva-v1-patch-ou-mensagem`, sem refinamento da regra.**
A execução com as fontes finais dos 500 repositórios substitui a dependência
anterior de disponibilização dos compares. O F1 observado é **0,933078**
em **296/300 releases**; as quatro restantes têm ausência de predecessora
registrada no coletor final. Não foi criada uma v2 nem imputada previsão.

A `main` de referência é `63f3933`, que incorpora o pacote final pela PR
#245. O [registro de versões](../validacao/refinamento-heuristica/versoes.json)
registra números sem arredondamento, cobertura, matriz, hashes e decisão.
Há uma única versão da regra. A versão 2 do **avaliador** da #162 não é uma
versão 2 da **heurística**. `versao_final_selecionada` identifica a regra
mantida; `versao_final_validada` permanece nula, pois não houve avaliação
observada dos 300 pares nem comprovação de três rotulagens cegas independentes.

## Histórico de versões e resultados

| Regra v1 (#161), fonte | Precisão | Recall | F1 | Cobertura | Decisão naquela revisão |
|---|---:|---:|---:|---:|---|
| Snapshot parcial, 21/10 | 0,869863 | 1,000000 | 0,930403 | 146/300 (48,67%) | Provisória; aguardar detalhes finais |
| Fontes finais, 22/10 | 0,890511 | 0,979920 | 0,933078 | 296/300 (98,67%) | Manter v1; quatro indeterminações justificadas |

A regra usa aumento de patch SemVer com mesmo major/minor **OU** mensagem
com termo isolado `fix`, `revert` ou `hotfix`, ignorando maiúsculas. Evidência
positiva basta; ausência de sinal com evidência incompleta fica indeterminada.
A sequência integral é classificada antes do recorte da amostra; a janela de
sete dias e sua censura pertencem ao cálculo da CFR(b). A unidade avaliada é
`corretiva`, classe positiva `sim`, não `falhou` nem CFR(b) agregada. As
[regras da #161](heuristica-cfr-b-161.md) permanecem preservadas.

## Evidência e justificativa da decisão

A matriz final, com linhas de consenso e colunas de previsão `[nao, sim]`,
é **`[[17,30],[5,244]]`**: VN=17, FP=30, FN=5, VP=244. Dos 154 pares antes
indeterminados, **150 passaram a ter previsão** com a fonte final. Todos os
249 positivos e 47 dos 51 negativos do consenso estão avaliados. A regra foi
reaplicada sem olhar os rótulos para decidir previsões, sem ajuste de termos,
sem exceções por ID e sem mudança do consenso. Os artefatos estão no
[relatório da #162](../validacao/avaliacao-heuristica/final-500/README.md).

As quatro exclusões são primeiras releases estáveis sem predecessora, conforme
os registros do compare publicado: Agent-Reach `v1.1.0`, Understand-Anything
`v1.2.0`, hindsight `v0.0.16` e meteor `release/METEOR@3.0`.
O [diagnóstico das fontes](../validacao/avaliacao-heuristica/final-500/diagnostico-fontes.json)
preserva IDs, datas, motivo, base nula e contagem de commits. A v1 não deve
inventar uma comparação para preencher esses casos. `avaliacao_completa=false`
continua correto; não se declara F1 observado para as 300 releases.

Mantendo as 296 previsões conhecidas e o consenso fixos, todos os quatro
pares desconhecidos têm consenso negativo. Uma eventual conclusão binária
teria os seguintes extremos:

- Quatro previsões positivas: VP=244, FP=34, FN=5, VN=17;
  **F1 = 488/527 = 0,925996**.
- Quatro previsões negativas: VP=244, FP=30, FN=5, VN=21;
  **F1 = 488/523 = 0,933078**.

São **limites condicionais**, não resultados medidos, imputações ou intervalos
de confiança. Ambos excedem 0,70. Assim, com as evidências atuais não há motivo
para refinar a regra para alcançar o limiar: ela supera a meta no subconjunto,
e as quatro indeterminações não poderiam reverter essa conclusão numérica
sob as condições declaradas. A alternativa de justificativa do card cobre
explicitamente a impossibilidade de medir o F1 das 300 com a v1 e essas fontes.
O campo de meta *observada na amostra completa* permanece falso no registro;
a robustez do limiar sob os limites condicionais é registrada separadamente.

## Limites e novas versões

O consenso usa a definição do livro de códigos: pelo menos uma correção,
incluindo releases mistas, em vez de exigir que corrigir defeito recente
seja o objetivo principal. A assistência registrada no preenchimento de C e
a declaração de trabalho conjunto limitam a comprovação de três avaliações
cegas independentes. F1 alto contra esse consenso não prova desempenho fora
dessa amostra nem detecção de incidentes em produção. A população de origem
do sorteio foi de 255 projetos, preservada após a ampliação para 500.

Se novas fontes ou uma revisão humana aprovada alterarem o diagnóstico,
reexecutar a #162 sem substituir o histórico. Uma mudança futura de regra
deve receber identificador próprio e registrar motivo, código, hashes, matriz,
cobertura, precisão, recall e F1 de **cada candidata**, inclusive descartadas.
Comparar os mesmos pares e declarar qualquer uso do consenso para ajuste;
não interpretar ganho por exclusão de casos difíceis como melhora da regra.
Se a regra mudar, recalcular a CFR(b) e todas as análises derivadas.

## Reprodução

Seguir o [README da execução final](../validacao/avaliacao-heuristica/final-500/README.md)
para restaurar o CFR(b) completo comprimido e reavaliar os mesmos 300 pares.
O retorno com `--exigir-completa` é **3**, pela cobertura de 296. O código
não usa esse retorno como reprovação de F1. A reprodução do snapshot anterior
e seus extremos de 146 pares também foi preservada no registro de versões.

Esta entrega conclui a decisão condicional por desempenho e justificativa,
sem fabricar uma versão ou resultados para as quatro exclusões.
Qualquer commit desta revisão deve referenciar `(#163)`.
