# Base capturada: 500 elegíveis

Snapshot autorizado pelo responsável em 20/10/2026. A seleção atingiu **500
repositórios elegíveis entre 1.064 candidatos avaliados**, na janela
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.

**O processamento final ainda não terminou.** A execução parou durante os
compares após um HTTP 403. As saídas processadas publicadas representam o estado
parcial observado, não um conjunto completo das quatro métricas para 500 projetos.
Ausências de métricas não equivalem a zero.

## Conteúdo

As partes `snapshot-500.tar.gz.partNNN` contêm a fonte de candidatos, configuração,
progresso, estado da execução, os checkpoints do contexto atual, checkpoints de
compare e auxiliares, todos os consolidados produzidos e as saídas processadas
existentes. As partes `cache-500.tar.gz.partNNN` preservam **todo o cache HTTP local**,
incluindo páginas de coletas parciais. Assim, o material já capturado pode ser
reaproveitado em outra máquina sem recomeçar as requisições concluídas.

Cada parte tem no máximo 40 MiB e é versionada como binário diretamente no Git.
O manifesto registra os 500 IDs, contexto, quantidade de candidatos, arquivos,
tamanhos e SHA-256 de cada parte e arquivo restaurado. Não inclui `.env`, tokens,
ambiente virtual, logs ou backups duplicados de contextos antigos. O snapshot de
255 publicado anteriormente permanece disponível em `../dados-brutos-255/`.

## Verificar ou restaurar

Na raiz do repositório, com Python 3.10 ou posterior, sem consultar a API:

```powershell
python Lab03/entregas/dados-brutos-500/restaurar.py --verificar
python Lab03/entregas/dados-brutos-500/restaurar.py --destino Lab03/data/raw/base-publicada-500
```

A verificação lê todos os pacotes, confere partes, membros e hashes sem extrair
a base inteira. A restauração recusa um destino existente e caminhos inseguros.
Ela preserva os arquivos originais e gera `config-local.yaml` com os caminhos
ajustados ao destino local. Reserve espaço para todos os dados descompactados;
os tamanhos exatos estão no manifesto.

## Retomar a coleta e finalizar métricas

Instale as dependências de `Lab03/requirements.txt` e configure os três tokens em
`Lab03/.env`, conforme `docs/coleta-tres-sessoes.md`. A partir de `Lab03`:

```powershell
.\.venv\Scripts\python.exe -u -m pipeline.coleta_paralela --config data/raw/base-publicada-500/config-local.yaml
```

O coletor relê os checkpoints, retoma os compares pendentes e gera as métricas
e auditorias finais. Somente o término com código 0 e `execucao_completa=true`
em `processed/amostra-final-500/execucao.json` confirma o processamento final.
As consultas pendentes dependem de credenciais válidas e da disponibilidade/cota
da API. O snapshot publicado não será alterado por essa retomada.
