# Avaliação da heurística corretiva — #162

Versão: `corretiva-v1-patch-ou-mensagem`. Classe positiva: **sim**.

**Parcial:** 146/300 releases avaliadas; 154 excluídas.

| Consenso / previsão | nao | sim |
|---|---:|---:|
| nao | 0 (VN) | 19 (FP) |
| sim | 0 (FN) | 127 (VP) |

| Métrica | Valor |
|---|---:|
| Precisão | 0.869863 |
| Recall | 1.000000 |
| F1 | 0.930403 |
| Suporte positivo avaliado | 127 |
| Suporte negativo avaliado | 19 |

No consenso total há 249 corretivas e 51 não corretivas; ficaram fora do cálculo 122 corretivas e 32 não corretivas.

Exclusões por motivo (podem se sobrepor): `{"previsao_indeterminada": 154}`.

Diagnóstico das pendências: `{"commits_compare": 125, "predecessora_historica+commits_compare": 29}`. Os IDs, URLs oficiais de compare e ações recomendadas estão em `pendencias.csv`. Uma URL vazia indica que o sorteio não fornece compare para a primeira release elegível; ela não comprova ausência de predecessora fora da janela.

Ausências não viram negativos. Valores com denominador nulo são não estimáveis. A censura de sete dias pertence à falha da CFR(b); esta avaliação usa `corretiva`, inclusive nas releases censuradas para CFR. Os pares e as exclusões estão em `pares.csv`.

O limiar de F1 é 0,70 (#163). Um resultado parcial descreve somente o subconjunto avaliado, sujeito a viés de cobertura, e não confirma a meta para toda a amostra. Este comando não refina a heurística nem altera os rótulos de consenso.
