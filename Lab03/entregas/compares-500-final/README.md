# Compare final dos 500 repositórios — #151, #153

Esta entrega publica o `compare.json` final que fundamenta o
[CSV final de 500](../s02-03-dataset-500-final/README.md), sem novas consultas
ao GitHub. São **34.151 comparações entre releases**, cobrindo **500
repositórios**, na janela `[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.

O JSON original ocupa 5.037.734.099 bytes. Ele é distribuído como
`compare.json.gz.partNNN`: 25 partes concatenáveis de um único gzip,
com no máximo 40 MiB por parte, cerca de 1 GB compactado no total.
O [manifesto](manifesto.json) registra ordem, tamanho e SHA-256 das partes
e do JSON restaurado, além do hash do original e da auditoria final.
A versão publicada substitui padrões de tokens GitHub encontrados em
textos públicos por `[TOKEN_GITHUB_REMOVIDO]`, usando a mesma regra do
snapshot anterior. Foram removidas quatro ocorrências; o arquivo local
original não foi alterado. IDs, datas e campos numéricos são preservados.

## Verificar e restaurar

Na raiz do repositório, com Python 3.10 ou posterior:

```powershell
python Lab03/entregas/compares-500-final/pacote.py --verificar
python Lab03/entregas/compares-500-final/pacote.py --destino C:/dados/compare.json
```

A pasta do destino deve existir e o arquivo deve ser novo. A verificação
confere os hashes das partes e descompacta em streaming, sem manter os 5 GB
em memória ou gravar o JSON. A restauração publica o destino somente após
conferir tamanho e hash; reserve ao menos 6 GB livres. O processo não requer
token nem rede. A concatenação binária das partes na ordem do manifesto
também forma um gzip padrão.

## Limites da coleta

`execucao_completa=true` significa que o pipeline terminou; não implica
ausência de lacunas nas fontes. A auditoria registra **104 releases ignoradas**
e **11 repositórios com coleta de compare incompleta**. São 34.255 releases
avaliadas, das quais 34.151 têm comparação. As métricas e os diagnósticos
do CSV permanecem os mesmos; esta publicação não preenche ausências nem
altera as decisões ou os resultados da avaliação da heurística.

O [snapshot anterior](../dados-brutos-500/README.md) permanece disponível
como corte histórico parcial. Para reproduzir análises que precisam dos
compares finais, use o arquivo restaurado desta entrega em lugar do
`compare.json` parcial daquele snapshot. Os demais dados brutos e caches
da coleta não são republicados por esta entrega.

## Validação desta publicação

Todas as 25 partes e os 5.037.734.031 bytes do JSON publicado foram
verificados por descompactação integral e SHA-256. O hash do original confere
com a auditoria que fundamenta o CSV final. Os dez testes de publicação,
saneamento entre blocos, corrupção, restauração e reprodução passaram.
As contagens e os hashes estão em [validacao.json](validacao.json).
