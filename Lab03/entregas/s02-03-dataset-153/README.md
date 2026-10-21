# Dataset da amostra encerrada — #153

**Registro histórico de 15/10/2026.** A atualização para a captura de 500
elegíveis em 20/10/2026 está em [s02-03-dataset-500](../s02-03-dataset-500/README.md).
Os arquivos e hashes desta entrega de 255 permanecem preservados.

Entrega offline de **255 repositórios**, autorizada pelo usuário após encerrar
as consultas externas em 2026-10-15T18:09:11Z. Foram consumidos 561 candidatos.
O mínimo original de 300 e a meta de 500 não foram atingidos. Esta entrega não
altera `execucao_completa` da coleta original para verdadeiro.

- [dataset-255.csv](dataset-255.csv): uma linha por ID oficial, 28 colunas,
  contrato `lab03-dataset-v1`, ordem crescente do ID.
- [manifesto.csv.json](manifesto.csv.json): contrato, janela, hashes e cobertura.
- [evidencias.json](evidencias.json): proveniência, auditorias agregadas e limites.
- [funil.md](funil.md): reconstrução dos 561 consumidos, inclusive exclusão de
  um candidato com runs incompletos após o critério quantitativo.

## Conteúdo e ausências

Janela inclusiva em 2025-10-01T00:00:00Z e exclusiva em 2026-10-01T00:00:00Z.
A DF e a CFR(a) têm 255 valores. A recuperação tem 241 valores; os 14 nulos
não foram preenchidos com zero. As variantes de lead time(a)/(b) usam apenas
9 compares locais compatíveis; 246 repositórios permanecem sem esses valores.
A CFR(b) permanece nula nos 255, dependente da #161.

CSV UTF-8, vírgula, ponto decimal, nulos em células vazias, booleanos
`true`/`false` e listas JSON. `full_name` preserva o nome da fonte; o ID é a
chave da junção. Eventual `full_name_atual` permanece nos metadados locais.

Compare ausente marca `coleta_incompleta=true` e `calculo_parcial=true` na
união final de métricas e no CSV. Nenhum compare vazio foi criado para
representar coleta ausente. Os dois indicadores atingem 246 e 247 repositórios,
respectivamente: `mrdoob/three.js` tem cálculo parcial adicional na variante(b).
Os diagnósticos temporais da recuperação permanecem separados nos JSONs:
352 sequências com censura à esquerda, 149 episódios censurados à direita e
3 repositórios com dados temporais incompletos. Não assumir que os dois
indicadores tabulares resumem todos esses diagnósticos.

A auditoria dos runs conferiu 2.586.659 runs no recorte (2.234.420 válidos),
196.867 falhas, 2.037.553 sucessos e 55.987 recuperações observadas. As duas
variantes de lead time mantêm fórmulas distintas; a variante(b) também teve
as 9 medianas verificadas diretamente dos intervalos locais. As estatísticas
de recuperação excluem censuras à direita/esquerda.

## Reprodução sem API

A partir de `Lab03`, com as dependências Python do projeto disponíveis:

```powershell
python -m pipeline.amostra_encerrada --encerramento 'CAMINHO/encerramento-amostra.json' --saida-dados 'PASTA_NOVA_ISOLADA'
python -m pipeline.dataset_csv --raw 'PASTA_NOVA_ISOLADA/raw' --processed 'PASTA_NOVA_ISOLADA/processed' --saida 'EXPORTACAO/dataset-255.csv' --manifesto 'EXPORTACAO/manifesto.csv.json'
python -m pytest tests/test_dataset_csv.py tests/test_integrado.py -q
```

A autoridade privada identifica o snapshot congelado, IDs oficiais, janela,
contexto e hashes. O primeiro comando recusa reutilizar uma pasta existente;
verifica hashes antes/depois da leitura, reconstrói somente os checkpoints
consumidos, calcula com os módulos científicos existentes e audita as saídas.
Ele não cria cliente HTTP, lê token nem chama coletores. O segundo comando
junta os IDs de `deployment_frequency.json`, metadados e métricas; rejeita
IDs duplicados, nomes/janelas divergentes e metadados intermediários. O CSV
é determinístico; sua reexportação sobre as mesmas entradas preserva bytes.

Nesta execução, os dados locais separados estão em
`Lab03/data/processed/amostra-encerrada-255-20261015T180911Z/{raw,processed}`
no checkout original, além do `config.yaml` local nessa pasta. Não são
versionados. Brutos, cache, checkpoints e logs ficam fora desta publicação.

Validação: 20 testes específicos de exportação/reconstrução e 78 testes de
regressão do integrado passaram. Os testes incluem cópia de identidade,
serialização Unicode/aspas/listas, nulo versus zero, duplicatas, janela,
completude do funil e reconstrução com 0/1/2 compares sob bloqueio de rede.

A população encerrada não representa os primeiros 255 de uma ordenação
estritamente por estrelas: a coleta priorizou custo observado e adiou grandes.
Essa decisão, a parada antes de 300 e a cobertura reduzida de compare limitam
a generalização e podem introduzir viés. Não há rótulos humanos nem
validação da heurística CFR(b) presumidos nesta entrega.
