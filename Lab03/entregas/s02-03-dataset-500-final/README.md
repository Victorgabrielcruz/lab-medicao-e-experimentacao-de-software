# Dataset de 500 após a conclusão dos compares — #151, #153

Coleta encerrada com **código 0** e **`execucao_completa=true`** no
`data/processed/amostra-final-500/execucao.json`. Os 500 projetos têm registros
de compare processados e preservam os mesmos IDs da captura original.
O CSV tem 500 linhas/28 colunas, contrato `lab03-dataset-v1`, e foi
reexportado com bytes idênticos, sem novas consultas na exportação.

- [dataset-500.csv](dataset-500.csv): CSV final desta execução.
- [manifesto.csv.json](manifesto.csv.json): contrato, janela, cobertura e hashes.
- [validacao.json](validacao.json): código observado, execução, auditorias e fontes.
- [funil.md](funil.md): mínimos quantitativos e completude de runs separados.

A [entrega anterior](../s02-03-dataset-500/README.md) é o corte histórico com
apenas 51 compares e permanece preservada. A janela continua
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.

| Variante | Valores | Nulos |
|---|---:|---:|
| deployment_frequency | 500 | 0 |
| lead_time_a | 499 | 1 |
| lead_time_b | 499 | 1 |
| cfr_a | 500 | 0 |
| cfr_b | 498 | 2 |
| tempo_recuperacao | 469 | 31 |

Processamento concluído não elimina ausências e diagnósticos das fontes:
13 linhas têm `coleta_incompleta=true` e
52 têm `calculo_parcial=true`. Nulos continuam como
células vazias, sem imputação por zero. CFR(b) é saída da heurística v1;
a validação humana #162 permanece uma dependência própria.

## Reexportação local

A partir de `Lab03`, após executar o coletor com sucesso:

```powershell
python -m pipeline.dataset_csv --raw data/raw/amostra-final-500 --processed data/processed/amostra-final-500 --saida entregas/reproducao-500/dataset-500.csv --manifesto entregas/reproducao-500/manifesto.csv.json
```

O ajuste de memória foi validado por 365 testes de coleta, métricas,
consolidação, auditoria e exportação. A exportação real conferiu os 500 IDs,
janela, contrato e hashes antes/depois, além da igualdade byte a byte.
Os detalhes por commit/release permanecem nos JSONs locais. As análises
#167, #168 e #169 são etapas posteriores; não foram executadas nesta entrega.
