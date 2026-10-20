# Dataset da captura de 500 — #153

Revisão offline de 20/10/2026, baseada no
[snapshot público](../dados-brutos-500/README.md): **500 elegíveis entre
1.064 candidatos avaliados**, janela UTC `[2025-10-01, 2026-10-01)`.
A seleção atingiu a meta, mas a execução original parou nos compares após
HTTP 403. Esta consolidação não declara o processamento final completo.
A [entrega histórica de 255](../s02-03-dataset-153/README.md) permanece intacta.

- [dataset-500.csv](dataset-500.csv): 500 IDs únicos, 28 colunas,
  contrato `lab03-dataset-v1`, ordem crescente de ID, nulos em células vazias.
- [manifesto.csv.json](manifesto.csv.json): colunas, janela, hashes e cobertura.
- [evidencias.json](evidencias.json): hashes das entradas, auditoria publicada
  dos runs, auditorias dos 51 compares e limitações.
- [funil.md](funil.md): 501 passam no critério quantitativo; um tem runs
  incompletos e é excluído, reproduzindo os 500 IDs oficiais.

| Variante | Valores | Nulos |
|---|---:|---:|
| Deployment frequency | 500 | 0 |
| Lead time (a) | 51 | 449 |
| Lead time (b) | 51 | 449 |
| CFR (a) | 500 | 0 |
| CFR (b), heurística v1 | 497 | 3 |
| Tempo de recuperação | 469 | 31 |

Os 497 valores de CFR(b) são estimativas da heurística implementada na #161;
a validação humana #162 continua pendente. Valor disponível não implica
evidência completa: 450 linhas têm `coleta_incompleta=true` e 459 têm
`calculo_parcial=true`, preservando os diagnósticos das variantes.
Os 449 projetos sem compare têm lead times e classes nulos e ambos os
indicadores verdadeiros. A auditoria publicada dos runs confere 4.765.758
runs no recorte, 4.010.735 válidos, 328.182 falhas, 3.682.553 sucessos e
92.560 recuperações. As censuras temporais permanecem separadas: 683
sequências com censura à esquerda, 330 episódios à direita e seis projetos
com dados temporais incompletos. Nulos não são imputados por zero.

## Reprodução sem API

Após restaurar a publicação conforme suas instruções, a partir de `Lab03`:

```powershell
python -m pipeline.amostra_capturada --manifesto entregas/dados-brutos-500/manifesto.json --raiz-dados data/raw/base-publicada-500 --saida data/processed/reproducao-captura-500 --entrega entregas/reproducao-dataset-500
python -m pytest tests/test_amostra_capturada.py tests/test_dataset_csv.py tests/test_integrado.py -q
```

`--raiz-dados` é a pasta que contém `raw/amostra-final-500` e
`processed/amostra-final-500`; no checkout original, ela é `data`.
Os destinos devem ser novos. O comando verifica hashes antes/depois,
confere IDs e janela, reaproveita CFR(a)/recuperação auditadas, calcula DF,
processa cada compare compatível isoladamente, audita LT(a), calcula LT(b)
e CFR(b) com os módulos existentes e exporta o contrato v1.
Não cria cliente HTTP nem lê credenciais. As cópias locais originais com
conteúdo público saneado na publicação são aceitas somente pelos hashes
de origem registrados; o saneamento deve reproduzir o hash publicado.

Validação: **104 testes aprovados**, incluindo reprodução idêntica do CSV,
0/1/2 compares, rede bloqueada, fonte adulterada e proteção dos destinos.
O CSV real foi reexportado das mesmas entradas e comparado byte a byte.
As fórmulas e o contrato de classificação permanecem os existentes.
