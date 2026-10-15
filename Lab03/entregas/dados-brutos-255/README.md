# Dados brutos da amostra encerrada em 255 repositórios

Publicação autorizada pelo responsável em 15/10/2026, após a entrega do CSV.
O snapshot preserva os dados coletados e seus hashes originais: 255 IDs elegíveis
completos nos checkpoints consumidos de 561 candidatos, na janela
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.

As partes `snapshot-255.tar.gz.partNNN` formam um único arquivo tar.gz. São
arquivos binários versionados diretamente no Git, sem Git LFS. O manifesto
registra ordem, tamanho e SHA-256 de cada parte e de cada arquivo restaurado.
Use clone/download completo do repositório para obter todas as partes.

## Restaurar

Na raiz do repositório, com Python 3.10 ou posterior (somente biblioteca padrão):

```powershell
python Lab03/entregas/dados-brutos-255/restaurar.py --destino Lab03/data/raw/amostra-publicada-255
```

O comando verifica todas as partes e todos os arquivos, recusa destino existente
e não faz chamadas à API. O original `encerramento-amostra.json` e os arquivos
em `snapshot/` mantêm seus bytes e hashes. Uma cópia `encerramento-local.json`
adapta exclusivamente os caminhos `origem` e `snapshot` ao computador atual.
Os caminhos históricos do computador da coleta permanecem nos arquivos originais.

## Reconstruir os consolidados locais

Instale as dependências de `Lab03/requirements.txt` em seu próprio ambiente.
Depois de restaurar, execute a partir de `Lab03`:

```powershell
python -m pipeline.amostra_encerrada --encerramento data/raw/amostra-publicada-255/encerramento-local.json --saida-dados data/processed/amostra-publicada-255
```

Esse comando reconstrói `raw/releases.json`, metadados, runs, compares e as
métricas processadas somente dos checkpoints locais. A saída deve ser uma pasta
nova. Os arquivos restaurados e gerados continuam ignorados pelo Git.
O CSV já publicado está em `../s02-03-dataset-153/dataset-255.csv`.

## Alcance e limitações

- Inclui 561 checkpoints consumidos de candidatos, 9 checkpoints de compare,
  configuração, fonte de candidatos, progresso, sinal de processo histórico
  e manifesto de congelamento. Os 255 IDs oficiais constam na autoridade.
- Não inclui o cache HTTP, logs, ambiente Python, cópias duplicadas, piloto
  ou checkpoints auxiliares não consumidos no encerramento.
- A extração foi encerrada por solicitação humana. O mínimo original de 300
  e a meta de 500 não foram atingidos; o pipeline original não está completo.
- Há compare local para 9 dos 255 repositórios. Ausências não equivalem a zero.
  CFR(b) continua pendente da #161; a publicação não cria métricas ou rótulos.
- Não houve nova extração ou consulta à API para preparar esta publicação.
- Foram conferidos hashes antes e depois do empacotamento e padrões de
  credenciais. A única correspondência de Authorization era um placeholder
  de documentação em uma mensagem pública de commit, não uma credencial.

Dados relacionados à auditoria #151 e à consolidação #153. Este pacote permite
ao grupo trabalhar sobre o mesmo material sem reiniciar a coleta.

## Verificação desta publicação

O pacote foi restaurado integralmente: 576 arquivos conferidos. A reconstrução
offline, com conexões de rede bloqueadas no teste, reproduziu os registros dos
consolidados anteriores de releases, metadados, compares e todas as métricas
disponíveis. As duas auditorias passaram. Destino existente e parte corrompida
foram recusados. Os resultados estão em `validacao.json`.
