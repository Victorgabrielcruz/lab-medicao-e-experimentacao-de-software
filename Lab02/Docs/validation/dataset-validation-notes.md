# Notas de execução — S03-01 (validação do dataset)

## Escopo

Implementa as verificações da Seção 13 da metodologia sobre o dataset oficial
(`data/processed/trials.csv`) em `src/validation/dataset_validator.py`,
cobrindo:

- cardinalidade (18 trials únicos, 6 por participante, 3 por tratamento por
  participante, 3 observações por kata, os dois tratamentos em cada kata);
- consistência com a alocação congelada (`data/metadata/allocation.csv`);
- duração, censura, conclusão, soma de testes e taxa de sucesso;
- não negatividade das métricas estruturais;
- vínculo de todo trial com Issue e commit;
- correspondência entre o dataset persistido e uma reconstrução independente
  a partir das fontes brutas (`src/processing/dataset_builder.build_dataset`);
- imutabilidade dos testes de aceitação de cada kata desde o congelamento
  (histórico git de `katas/KXX/tests`);
- consistência de versões das ferramentas de métricas entre trials;
- outliers por IQR, reportados e nunca removidos automaticamente.

Erros críticos impedem a autorização do dataset para as análises de RQ1–RQ3
(`ValidationResult.authorized`); lacunas previstas na metodologia (métricas
estruturais ausentes em trials antigos, dificuldade percebida não coletada,
log de prompts ausente) são avisos, não bloqueiam a análise. O relatório
gerado fica em `reports/drafts/data-validation.md` e é reproduzido com:

```bash
.venv/Scripts/python.exe scripts/validate_dataset.py
```

## Correção de auditoria: dataset oficial estava obsoleto

Ao rodar a primeira validação, a regra `raw_correspondence_mismatch`
encontrou que `data/processed/trials.csv` (gerado pelo merge da PR #125,
issue #73) tinha as linhas de `P02-K01-ai` e `P02-K04-ai` **vazias**, embora
as evidências brutas dos dois trials já existissem em `data/raw/`.

Causa raiz: a branch `codex/s02-05-build-trials-dataset` foi criada a partir
de um commit anterior à execução desses dois trials (commit-base
`f4a3291`); o merge para `main` não foi refeito sobre o histórico mais
recente, então o CSV commitado refletia um estado da árvore mais antigo que
o `main` atual.

Correção aplicada: reexecução de `scripts/build_dataset.py` (determinístico,
sem edição manual) sobre o `main` atual, substituindo
`data/processed/trials.csv` e `data/processed/consolidation-errors.csv`.
Após a correção, os 18 trials têm evidência bruta, Issue e commit
vinculados; o teste
`tests/test_dataset_builder.py::test_dataset_real_tem_dezoito_trials_unicos_e_csv_reexecutavel`,
que dependia implicitamente do estado antigo, foi atualizado para refletir
os dados reais (a lacuna genuína e permanente é a ausência de métricas
estruturais em `P02-K02-manual`, não mais `P02-K01-ai`).

Rastro de auditoria: o commit que regenerou os artefatos derivados e ajustou
o teste, referenciando esta issue (#75), mais este documento e o relatório
reproduzível em `reports/drafts/data-validation.md`.
