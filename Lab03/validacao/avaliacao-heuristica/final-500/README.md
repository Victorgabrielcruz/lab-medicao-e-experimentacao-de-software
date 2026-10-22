# Avaliação com os detalhes finais dos 500 — #162

Revisão de 22/10/2026, a partir da `main` `63f3933` (PR #245).
A v1 foi reaplicada à sequência completa de releases dos **500 repositórios**,
sem novas consultas à API, sem consultar rótulos para gerar previsões e sem
alterar a regra ou o sorteio oficial. O arquivo integral cobre **34.255
releases**; 498 repositórios têm CFR(b) estimável e dois permanecem nulos.
Todos os agregados coincidem com o CSV final, com tolerância absoluta e
relativa de `1e-12`. Isso é uma conferência de reprodução, não uma validação
independente do construto de falha em produção.

## Resultado contra o consenso registrado

A amostra continua com 60 repositórios e 300 releases, sorteadas entre os
primeiros 255 elegíveis. Não existem rótulos humanos para validar todas as
34.255 releases dos 500 projetos. A classe positiva é `sim` e cada release
avaliada tem o mesmo peso.

| Consenso / previsão | nao | sim |
|---|---:|---:|
| nao | 17 (VN) | 30 (FP) |
| sim | 5 (FN) | 244 (VP) |

Precisão **0,8905109489051095**, recall **0,9799196787148594**,
F1 **0,9330783938814532**. Cobertura **296/300 (98,67%)**: todos os 249
positivos e 47 dos 51 negativos do consenso têm previsão conhecida.
Foram resolvidas **150 das 154 indeterminações do snapshot histórico**.

As quatro restantes têm motivo `sem_release_anterior` na fonte final,
`release_anterior=null` e nenhum commit de compare; o coletor as registra
como primeiras releases estáveis do histórico:

| Repositório | Release ID | Tag |
|---|---:|---|
| Panniantong/Agent-Reach | 290354431 | v1.1.0 |
| Egonex-AI/Understand-Anything | 300977420 | v1.2.0 |
| vectorize-io/hindsight | 267408243 | v0.0.16 |
| meteor/meteor | 384693385 | release/METEOR@3.0 |

Essa é a evidência preservada na coleta, não uma garantia sobre todo estado
histórico possível do GitHub. Não se cria uma base artificial nem se converte
indeterminação em negativo. `avaliacao_completa` continua `false` e
`--exigir-completa` retorna **3**, gravando os relatórios normalmente.
O diagnóstico genérico de `pendencias.csv` deve ser lido junto com
[diagnostico-fontes.json](diagnostico-fontes.json), que esclarece esses quatro
casos na fonte final. No universo de 34.255 releases, há 95 classificações
indeterminadas: 87 por ausência de predecessora e oito por compare inacessível.
Os 104 compares ignorados não equivalem a 104 classificações indeterminadas:
um sinal patch pode ser suficiente mesmo sem compare completo.

Os escores são contra o consenso **registrado**. O livro de códigos considera
corretiva uma release com ao menos uma correção, incluindo entregas mistas.
Os registros de assistência no preenchimento de C e a declaração de trabalho
conjunto limitam a comprovação de três julgamentos cegos independentes.
A concordância calculada e a avaliação não eliminam essas limitações.

## Reprodução offline pelo artefato completo

Com as dependências do projeto instaladas, a partir de `Lab03`, em um destino
novo (a restauração recusa sobrescrita):

```bash
mkdir -p data/processed/validacao-final-500
python validacao/avaliacao-heuristica/final-500/restaurar_cfr_b.py \
  --destino data/processed/validacao-final-500/cfr_b.json
python -m pipeline.avaliacao_heuristica \
  --previsoes data/processed/validacao-final-500/cfr_b.json \
  --saida /tmp/lab03-avaliacao-final-reproduzida --exigir-completa
```

O segundo comando retorna **3** pela cobertura 296/300, não por falha de
cálculo. O gzip tem 66.826.825 bytes e restaura 345.647.323 bytes. O
[cfr_b-manifesto.json](cfr_b-manifesto.json) identifica os hashes do gzip,
do JSON original e das fontes; o restaurador verifica ambos os arquivos.
O caminho e a versão das bibliotecas fazem parte da proveniência do avaliador.
O cabeçalho histórico `validacao_manual_pendente=true` do JSON gerado pela
#161 foi preservado; o estado e os números desta execução estão em
[avaliacao.json](avaliacao.json), não nesse sinalizador genérico.

## Recalcular a partir dos pacotes de coleta

Os comandos abaixo exigem espaço para o compare descomprimido (5,04 GB),
a extração temporária do snapshot (818 MB), as releases (8,5 MB) e o CFR(b)
(346 MB), além dos pacotes já versionados. A leitura do compare é por
repositório. Não é necessário restaurar os cerca de 35 GiB de cache HTTP.

```bash
mkdir -p data/raw/validacao-final-500
python entregas/compares-500-final/pacote.py \
  --destino data/raw/validacao-final-500/compare.json
python -m pipeline.releases_snapshot \
  --pacote entregas/dados-brutos-500 \
  --saida data/raw/validacao-final-500/releases.json
python -m pipeline.cfr_b --config config.yaml \
  --entrada data/raw/validacao-final-500/releases.json \
  --compare data/raw/validacao-final-500/compare.json \
  --saida data/processed/validacao-final-500/cfr_b.json
python -m pipeline.auditoria_cfr_final \
  --cfr data/processed/validacao-final-500/cfr_b.json \
  --compare data/raw/validacao-final-500/compare.json \
  --dataset entregas/s02-03-dataset-500-final/dataset-500.csv \
  --amostra validacao/amostra-ouro/amostra_ouro.json \
  --saida /tmp/lab03-diagnostico-final.json
```

A recuperação de releases verifica as 20 partes e os 500 checkpoints
utilizados, mantendo toda a sequência e os campos usados pela #161. O pacote
de compare verifica suas 25 partes e o hash do JSON publicado. A publicação
original sanitizou quatro cadeias semelhantes a tokens em mensagens; o hash
publicado é o usado aqui. Não se afirma uma nova auditoria de todos os
membros de cache não utilizados. Uma nova execução da #161 muda `gerado_em`
e, portanto, o hash do JSON; os valores, sinais e classificações devem
concordar. A cópia comprimida preserva exatamente a execução registrada.

[pares.csv](pares.csv) contém os 300 pares e exclusões;
[previsoes_amostra.json](previsoes_amostra.json) permite reavaliar somente a
amostra; o snapshot anterior de 146 pares permanece preservado em
`../snapshot-500/`. A decisão da #163 está em
[refinamento-heuristica-163.md](../../../docs/refinamento-heuristica-163.md).
