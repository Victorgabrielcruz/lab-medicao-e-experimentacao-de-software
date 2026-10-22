# Avaliação da heurística corretiva — #162

Versão: `corretiva-v1-patch-ou-mensagem`. Classe positiva: **sim**.

**Parcial:** 296/300 releases avaliadas; 4 excluídas.

| Consenso / previsão | nao | sim |
|---|---:|---:|
| nao | 17 (VN) | 30 (FP) |
| sim | 5 (FN) | 244 (VP) |

| Métrica | Valor |
|---|---:|
| Precisão | 0.890511 |
| Recall | 0.979920 |
| F1 | 0.933078 |
| Suporte positivo avaliado | 249 |
| Suporte negativo avaliado | 47 |

No consenso total há 249 corretivas e 51 não corretivas; ficaram fora do cálculo 0 corretivas e 4 não corretivas.

Exclusões por motivo (podem se sobrepor): `{"previsao_indeterminada": 4}`.

Diagnóstico das pendências: `{"predecessora_historica+commits_compare": 4}`. Os IDs, URLs oficiais de compare e ações recomendadas estão em `pendencias.csv`. Uma URL vazia indica que o sorteio não fornece compare para a primeira release elegível; ela não comprova ausência de predecessora fora da janela.

Ausências não viram negativos. Valores com denominador nulo são não estimáveis. A censura de sete dias pertence à falha da CFR(b); esta avaliação usa `corretiva`, inclusive nas releases censuradas para CFR. Os pares e as exclusões estão em `pares.csv`.

O limiar de F1 é 0,70 (#163). Um resultado parcial descreve somente o subconjunto avaliado, sujeito a viés de cobertura, e não confirma a meta para toda a amostra. Este comando não refina a heurística nem altera os rótulos de consenso.
