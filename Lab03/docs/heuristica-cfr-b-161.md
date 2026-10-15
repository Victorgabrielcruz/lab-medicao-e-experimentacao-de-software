# Heurística corretiva v1 e CFR(b) — S02-11 (#161)

Implementação: [pipeline/cfr_b.py](../pipeline/cfr_b.py).
Versão: `corretiva-v1-patch-ou-mensagem`.

## Evidências de release corretiva

A primeira versão usa **patch SemVer OU mensagem de commit**:

1. Major e minor iguais aos da release estável anterior, com patch maior.
   Aceita `X.Y.Z` e `vX.Y.Z`, sem zeros à esquerda. Ignora metadata de build
   `+...` na comparação; não aceita sufixos de pré-release, prefixos de
   monorepo ou versões incompletas. Um salto de patch também satisfaz a regra;
   versão igual, regressiva ou mudança de major/minor não satisfazem.
   A [especificação SemVer](https://semver.org/) fundamenta o formato e a
   precedência; aceitar o prefixo `v` é uma convenção explícita desta v1.
2. Alguma mensagem dos commits entre a release anterior e a atual contém
   o termo isolado `fix`, `revert` ou `hotfix`, sem distinguir maiúsculas.
   Examina a mensagem inteira, incluindo corpo. Exemplos: `fix(parser): ...`,
   `Revert "..."` e `hotfix: ...`. Substrings como `prefix`, `fixture`,
   `fixes` e `hotfixes` não correspondem; `_` também integra uma palavra.

O resultado por release contém `corretiva`, `patch_semver`, SHAs e termos dos
commits positivos, `compare_completo` e `motivo_corretiva`. É uma previsão
automática, **ainda não validada** contra consenso humano. Não é um julgamento
de que o objetivo principal da release realmente foi corrigir defeitos.
Precisão, recall e F1 e o refinamento pertencem às #162 e #163.

## CFR(b) e tempo

Entram apenas releases estáveis, publicadas no intervalo UTC
`[inicio, fim_exclusivo)`, sem drafts nem pré-releases. A sequência é
ordenada por publicação/ID; IDs repetidos idênticos são deduplicados.
Datas inválidas e duplicatas divergentes são recusadas.

Uma release R falha quando existe **qualquer release corretiva posterior**
em até sete dias: `0 < published_at(corretiva) - published_at(R) <= 7 dias`.
Não se limita à sucessora imediata. Cada R conta uma vez no numerador,
mesmo com várias corretivas posteriores. Publicações simultâneas não são
consideradas posteriores entre si; ordenar por ID não inventa ordem temporal.

Releases com `published_at >= fim_exclusivo - 7 dias` são censuradas e
excluídas do numerador e denominador, mesmo havendo correção observada.
Uma corretiva censurada ainda pode demonstrar a falha de uma release anterior
não censurada. Na janela configurada, a censura começa em 24/09/2026 00:00 UTC.

`change_failure_rate = releases_falhas / releases_avaliadas`, em fração,
sem arredondamento. `releases_avaliadas` contém somente decisões de falha
conhecidas e não censuradas. Sem denominador, valor e classe são `null`;
zero observado continua sendo zero. A classificação usa os cortes comuns
de `pipeline/classificacao.py`.

## Dados ausentes e cobertura

O compare é associado por ID do repositório e da release, conferindo nome,
tag, data e base contra a sequência local. A base histórica anterior à janela
é aproveitada quando existe no compare. Sem base, o sinal de patch da
primeira release é desconhecido; isso não impede avaliar se ela foi seguida
por uma corretiva.

Uma evidência positiva basta para o OR: patch pode identificar uma corretiva
sem compare, e um commit positivo coletado pode identificá-la mesmo em compare
parcial. Para negar a presença de sinal nos commits, exigem-se compare válido,
contagens completas, SHAs únicos e todas as mensagens disponíveis. Um 404,
histórico inacessível, compare ausente ou mensagem faltante não vira negativo.
Esses casos preservam a possibilidade de usar o patch das releases locais.

Se não houver corretiva conhecida, mas alguma release posterior em até sete
dias tiver classificação indeterminada, `falhou` fica `null` e R sai do
denominador com motivo. Sem qualquer publicação posterior nesse intervalo,
a lista completa de releases basta para decidir que R não falhou. Se a própria
coleta de releases estiver marcada incompleta, decisões negativas também
ficam indeterminadas. Falhas já comprovadas permanecem positivas.

A saída registra contagens de avaliadas, falhas, censuradas, indeterminadas,
duplicadas e fora do recorte, além de `coleta_incompleta` e `calculo_parcial`.
Uma CFR com parte das releases indeterminadas descreve somente as avaliadas;
a exclusão pode introduzir viés. Consultar sempre cobertura e motivos.

## Execução local e integração

Na pasta `Lab03`, após dispor de releases e da população elegível:

```bash
python -m pipeline.cfr_b --config config.yaml \
  --amostra data/processed/deployment_frequency.json
python -m pipeline.metricas --config config.yaml
```

Entradas padrão: `data/raw/releases.json` e `data/raw/compare.json` quando
disponível. Saída: `data/processed/cfr_b.json`, gravada atomicamente. Opções
`--entrada`, `--compare`, `--amostra` e `--saida` permitem caminhos isolados.
Um compare explicitamente solicitado e inexistente gera erro; a ausência do
compare padrão permite cálculo apenas onde as evidências disponíveis bastam.
Sem `--amostra`, processa todos os repositórios da entrada de releases; use
o filtro antes de consolidar métricas dos elegíveis para não ampliar a amostra.

O pipeline integrado e a reconstrução offline da amostra encerrada já chamam
a etapa com os IDs elegíveis, antes da consolidação de métricas. A v1 é
recalculada a partir das entradas locais, sem invalidar checkpoints de coleta.
O cabeçalho registra origens, versão, regra temporal, censura e
`validacao_manual_pendente=true`.

Esta implementação e seus testes não retomam coleta nem geram previsões
para a amostra-ouro. Os dados e o CSV publicado anteriormente permanecem
preservados; sua atualização é uma execução separada. A aplicação aos dados
reais depende da cobertura local: compare ausente não impede toda decisão
por patch, mas limita decisões que dependem de mensagens.

## Verificação

[tests/test_cfr_b.py](../tests/test_cfr_b.py) cobre os exemplos do enunciado:
`v2.3.0` (10/05) seguida de `v2.3.1` (12/05, `fix`) falha;
`v2.4.0` (01/06) seguida de `v2.5.0` (20/06) não falha.
Também cobre limites temporais, censura, corretiva não imediata, fontes
incompletas, SemVer, termos isolados, integridade e execução sem rede.
Os testes de integração verificam restrição aos elegíveis, consolidação
e cálculo por patch mesmo quando o compare responde 404.

Validação local em 15/10/2026, Python 3.14.3:

```bash
python -m pytest --cov=pipeline --cov-report=term-missing --cov-fail-under=80
```

Resultado: **863 testes aprovados, 2 ignorados, cobertura global de 97,00%**
e 99% no módulo `cfr_b.py`. A execução local não substitui as verificações
da CI nas versões Python 3.11 e 3.13. Os dados usados pelos testes são
fixtures; não houve execução sobre a população real nem rotulagem humana.
