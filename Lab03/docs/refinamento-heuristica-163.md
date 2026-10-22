# Refinamento da heurística corretiva — S02-13 (#163)

## Decisão em 21/10/2026

**Manter a v1, com validação final pendente e justificativa registrada.**
O resultado disponível não permite decidir se o refinamento condicional
previsto neste card é necessário. Não foi criada uma v2 nem alterada a
classificação para aumentar o F1 do subconjunto observado.

A `main` de referência é `ff3db78`, que incorpora a avaliação da #162
pela PR #241. O [registro de versões](../validacao/refinamento-heuristica/versoes.json)
preserva as métricas sem arredondamento, cobertura, matriz, hashes e estado
da decisão. Há uma única versão da regra até esta revisão. A versão 2 do
**avaliador** da #162 não é uma versão 2 da **heurística**.

## Histórico de versões e resultados

| Versão da heurística | Regra | Precisão | Recall | F1 | Cobertura | Decisão |
|---|---|---:|---:|---:|---:|---|
| `corretiva-v1-patch-ou-mensagem` (#161) | Aumento de patch SemVer com mesmo major/minor **OU** mensagem com termo isolado `fix`, `revert` ou `hotfix` | 0,869863 | 1,000000 | 0,930403 | 146/300 (48,67%) | Mantida provisoriamente; meta global não comprovada |

As [regras completas da v1](heuristica-cfr-b-161.md) incluem a sequência de
releases estáveis e a base histórica quando disponível. Evidência positiva
basta para o OR; evidência incompleta sem sinal positivo permanece
indeterminada. A unidade avaliada é `corretiva`, com classe positiva `sim`,
e não o campo `falhou` nem a CFR(b) agregada. A janela de sete dias e sua
censura continuam pertencendo ao cálculo da CFR(b).

A matriz observada, com linhas de consenso e colunas de previsão na ordem
`[nao, sim]`, é `[[0, 19], [0, 127]]`: VN=0, FP=19, FN=0 e VP=127.
Fonte: [avaliação da #162](../validacao/avaliacao-heuristica/snapshot-500/avaliacao.json),
calculada diretamente do `cfr_b.json` versionado. Os 300 pares oficiais
foram preservados; apenas 146 possuem previsão conhecida.

## Justificativa para não concluir o refinamento

O F1 observado supera 0,70, mas todas as 146 previsões conhecidas são
positivas. Das 154 releases excluídas, 122 são corretivas e 32 não são,
segundo o consenso. Portanto, FN=0 e recall=1 descrevem apenas o subconjunto
com evidência suficiente. A meta na amostra inteira permanece **não
comprovada**, e não se registra aprovação final por esse resultado parcial.

A [lista de pendências](../validacao/avaliacao-heuristica/snapshot-500/pendencias.csv)
identifica 125 pares sem compare completo e outros 29 que também precisam
esclarecer a predecessora histórica. Os detalhes finais por release da
coleta dos 500 repositórios ainda não estão disponíveis no repositório.
O CSV agregado final não substitui essas previsões. A ausência legítima de
histórico poderá continuar indeterminada mesmo após disponibilizar a fonte.

Para dimensionar a incerteza, mantendo fixas as 146 previsões conhecidas e
os rótulos de consenso, os extremos matemáticos para uma eventual previsão
binária de todos os 154 pares restantes seriam:

- Todos os restantes errados: VP=127, FP=51, FN=122, VN=0;
  `F1 = 254 / 427 = 0,594848`.
- Todos os restantes certos: VP=249, FP=19, FN=0, VN=32;
  `F1 = 498 / 517 = 0,963250`.

Esses extremos são cenários condicionais, **não resultados medidos nem
intervalos de confiança**. Não se preenchem as previsões ausentes com esses
valores. Como os extremos ficam em lados diferentes de 0,70, o resultado
parcial não decide o atendimento da meta. Ajustar a regra somente aos 19
falsos positivos conhecidos, sem observar os possíveis falsos negativos,
também não demonstraria melhora na amostra completa.

Assim, o critério de alternativa por justificativa fica documentado:
**não há evidência suficiente para declarar uma versão final com F1 >=
0,70, nem para demonstrar necessidade de alterar a v1**. A restrição atual
é a cobertura das entradas; o desempenho final ainda não foi estabelecido.

## Como retomar a decisão

1. Disponibilizar os detalhes finais de `cfr_b.json` ou `releases.json` e
   `compare.json` e executar a #162 nos mesmos 300 pares e consenso. Usar
   outra pasta de saída para preservar o snapshot histórico.
2. Conferir cobertura e exclusões. O código 3 com `--exigir-completa`
   indica relatório parcial; código 0, sozinho, não comprova F1 >= 0,70.
   Indeterminações legítimas exigem justificativa explícita e continuam
   fora da matriz; não viram negativos nem são retiradas do sorteio.
3. Se houver avaliação completa e F1 >= 0,70, manter a v1 e acrescentar
   sua avaliação final ao histórico, sem criar uma versão de regra fictícia.
4. Se F1 < 0,70, examinar FP/FN com evidências, definir uma mudança geral
   fundamentada e atribuir um novo identificador à regra. Registrar regra,
   motivo, código, hashes das fontes, cobertura, matriz, precisão, recall e
   F1 **de cada candidata**, incluindo as descartadas. Não usar exceções por
   ID de repositório ou release, nem alterar o consenso para melhorar o escore.
5. Reavaliar cada candidata com o avaliador da #162. Comparar versões nos
   mesmos pares conhecidos e reportar também a cobertura de cada uma; um
   ganho causado apenas por excluir casos difíceis não basta para escolher
   a versão. Preservar os artefatos de cada execução em pastas distintas.
6. Selecionar a versão final com F1 >= 0,70 ou registrar o motivo de não
   alcançar a meta, incluindo lacunas de dados, limitações das regras e
   tentativas realizadas. Se a regra mudar, recalcular a CFR(b) a partir da
   sequência completa e revisar os resultados derivados antes de publicá-los.

Se o mesmo consenso for usado para ajuste e avaliação, os escores devem ser
declarados como obtidos na amostra usada no ajuste. Eles não constituem
avaliação independente em dados novos, conforme a metodologia da #165.

Para avaliar os detalhes finais, a partir de `Lab03`:

```bash
python -m pipeline.avaliacao_heuristica \
  --previsoes data/processed/amostra-final-500/cfr_b.json \
  --saida validacao/avaliacao-heuristica/final-500 --exigir-completa
```

## Reprodução da evidência desta revisão

Com as dependências de `requirements.txt` instaladas:

```bash
python -m pipeline.avaliacao_heuristica \
  --previsoes validacao/avaliacao-heuristica/snapshot-500/cfr_b.json \
  --saida /tmp/lab03-s02-163-avaliacao --exigir-completa
```

O retorno esperado é **3**, com 146 avaliadas e 154 excluídas. A execução
offline produz F1=0,9304029304029304 e a matriz acima. Os hashes das entradas
e do relatório histórico estão no registro de versões. O relatório deve ser
reproduzido antes de atualizar esse registro com novas evidências.

Esta entrega documenta a v1, seu F1 parcial e a justificativa; preserva o
código da heurística, as previsões, os rótulos e os valores do artigo.
Qualquer commit desta entrega deve referenciar `(#163)`.
