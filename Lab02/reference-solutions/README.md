# Soluções de referência

Esta pasta contém as implementações usadas para validar as suítes, testar o
pipeline de métricas estáticas e apoiar a avaliação de equivalência das katas.

## Validação

Em 10/09/2026, as seis soluções foram executadas separadamente com Python
3.12.14 e pytest 9.1.1 pelo comando:

```powershell
python scripts/run_tests.py K01 --src reference-solutions/K01
```

O mesmo comando foi repetido para K02 a K06.

| Kata | Testes | Passando | Falhando |
|---|---:|---:|---:|
| K01 | 6 | 6 | 0 |
| K02 | 5 | 5 | 0 |
| K03 | 6 | 6 | 0 |
| K04 | 6 | 6 | 0 |
| K05 | 5 | 5 | 0 |
| K06 | 5 | 5 | 0 |
| **Total** | **33** | **33** | **0** |

O registro legível por máquina está em
`data/metadata/reference-solutions-validation.json`.

> Durante a coleta, as soluções de referência não podem ficar acessíveis aos
> participantes. Antes do primeiro trial, elas devem ser movidas para uma área
> privada sob custódia do responsável pela preparação e removidas do histórico
> entregue aos participantes. Apenas os resultados das validações permanecem
> no pacote experimental. Elas podem voltar ao repositório compartilhado após
> todos os trials para permitir a replicação.
