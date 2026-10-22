# RQ07 — Mudança de categoria e robustez (#174)

Kappa de Cohen com pesos quadráticos; escala ordinal fixa Low, Medium, High, Elite.
O kappa linear é uma verificação adicional. Matrizes: linhas = primeira combinação;
colunas = segunda. Percentuais usam os pares elegíveis, sem imputar ausências.

## Classe geral

| Par | Coorte | n | Excluídos | Mudaram | Mudança (%) | Kappa quadrático | Kappa linear |
|---|---|---:|---:|---:|---:|---:|---:|
| C1xC2 | completos_por_par | 468 | 32 | 68 | 14.5299 | 0.8411 | 0.7913 |
| C1xC2 | completos_nas_tres | 467 | 33 | 68 | 14.5610 | 0.8394 | 0.7898 |
| C1xC2 | notas_disponiveis | 500 | 0 | 80 | 16.0000 | 0.8278 | 0.7745 |
| C1xC2 | sem_alertas | 420 | 80 | 60 | 14.2857 | 0.8367 | 0.7891 |
| C1xC3 | completos_por_par | 467 | 33 | 179 | 38.3298 | 0.5635 | 0.4431 |
| C1xC3 | completos_nas_tres | 467 | 33 | 179 | 38.3298 | 0.5635 | 0.4431 |
| C1xC3 | notas_disponiveis | 500 | 0 | 187 | 37.4000 | 0.5738 | 0.4629 |
| C1xC3 | sem_alertas | 419 | 81 | 156 | 37.2315 | 0.5648 | 0.4500 |
| C2xC3 | completos_por_par | 467 | 33 | 197 | 42.1842 | 0.4494 | 0.3574 |
| C2xC3 | completos_nas_tres | 467 | 33 | 197 | 42.1842 | 0.4494 | 0.3574 |
| C2xC3 | notas_disponiveis | 500 | 0 | 208 | 41.6000 | 0.4720 | 0.3775 |
| C2xC3 | sem_alertas | 419 | 81 | 173 | 41.2888 | 0.4451 | 0.3576 |

## Resultado observado

C1xC2: 68/468 projetos mudaram de categoria (14.5299%; kappa quadrático 0.8411). Sem alertas, a mudança foi 14.2857% em 420 pares, com kappa 0.8367.

C1xC3: 179/467 projetos mudaram de categoria (38.3298%; kappa quadrático 0.5635). Sem alertas, a mudança foi 37.2315% em 419 pares, com kappa 0.5648.

C2xC3: 197/467 projetos mudaram de categoria (42.1842%; kappa quadrático 0.4494). Sem alertas, a mudança foi 41.2888% em 419 pares, com kappa 0.4451.

Na população completa comum, a troca de lead time altera 14.5610% das classes gerais e a de CFR altera 38.3298%. A diferença descreve a sensibilidade destas combinações nesta amostra; não atribui superioridade de validade a uma definição.


## Discussão e limites

A análise principal usa quatro métricas disponíveis em ambas as combinações
(completos_por_par). completos_nas_tres fixa a população comum aos três pares.
notas_disponiveis inclui medianas parciais, conforme o protocolo de classificação,
e sem_alertas restringe os pares completos a registros sem coleta incompleta nem
cálculo parcial. As comparações por métrica usam as mesmas coortes; a coorte
notas_disponiveis permite examinar cada métrica em todos os pares observados.

C1×C2 isola lead time; C1×C3 isola CFR; C2×C3 altera ambos. A tabela permite
avaliar se a sensibilidade persiste ao fixar disponibilidade e qualidade dos dados.
Mesmo quando o kappa indica proximidade ordinal, o percentual de mudanças mede
quantos projetos efetivamente trocaram de classe; as duas medidas são necessárias.

A #162 está encerrada com relatório publicado parcial (146/300). A conferência
das previsões finais locais alcançou 296/300, com quatro indeterminadas;
o registro de suporte está em docs/evidencias/rq07-validacao-final-162.json.
CFR(b) mantém essa limitação: a avaliação não é integral e ausências não viram negativos.
A concordância entre definições não comprova validade das proxies de produção.
Pré-releases e tags estão fora destas combinações, e não se pode generalizar
esta análise para mudanças da definição de deploy. Não há conclusão causal.
Kappa fica nulo se não houver pares ou se a discordância esperada for zero;
uma categoria constante idêntica não recebe artificialmente kappa igual a 1.
