# Comparação com a publicação parceira — FIN-02 (#181)

Comparamos a [execução de 30 projetos da #180](../fin-01-execucao/README.md)
com o dataset publicado pelo grupo autor. A comparação é entre as duas
saídas do **pipeline parceiro**, sem misturar nosso dataset de 500 nem
recalcular métricas a partir da API.

## Fontes e reprodução

- Publicação: [CSV no commit 9ba34433f7b0243d1bcca9d130f2dd58b67ed841](https://github.com/matheustitton/lab-medicao-experimentacao-6-periodo/blob/9ba34433f7b0243d1bcca9d130f2dd58b67ed841/lab03-metricas-dora/data/saida/dataset_dora.csv),
  preservado em `dataset_publicado.csv`: 237 linhas, 37 colunas.
- Replicação: `../fin-01-execucao/dataset_dora.csv`: 30 linhas, 37 colunas.
- SHA-256 publicado: `b29008d2700fb53844084b5dbf1bfd1cdef39271d222c59984cbfd1e09199b52`.
- SHA-256 replicado: `c7401766f963f764d4a934270c9a1ca389b7f6b80d4dfbb48041231283207bd4`.

A partir da raiz do repositório, em ambiente Python existente:

```powershell
Lab03/.venv/Scripts/python.exe Lab03/replicacao/fin-02-comparacao/comparar.py
Lab03/.venv/Scripts/python.exe -m unittest discover -s Lab03/replicacao/fin-02-comparacao -p test_comparar.py
```

O script usa apenas a biblioteca padrão. Gera `resumo.json` e
`diferencas_por_repositorio.csv`, com 168 registros (28 pares × 6 métricas).
O pareamento usa `repo` sem distinção de maiúsculas, recusando duplicatas.
Dos 30 replicados, **28** estão na publicação; `itchio/itch` e
`n00bcodr/Jellyfin-Enhanced` ficam fora da comparação pareada, sem imputação.

## Diferenças relativas por métrica

Para cada par, calculamos `100 × (replicado − publicado) / |publicado|`.
Também preservamos a diferença absoluta na unidade da coluna. Base zero
recebe `base_zero`, mesmo quando ambos são zero; ausência recebe `ausente`.
Nenhum desses casos é convertido em diferença relativa zero.
Igualdade numérica usa tolerâncias `rel_tol=1e-9`, `abs_tol=1e-12`.

| Métrica | Pares disponíveis | Valores iguais | Bases zero | Pares relativos | Mediana relativa | Máximo erro relativo absoluto |
|---|---:|---:|---:|---:|---:|---:|
| Frequência semanal | 28 | 28 | 0 | 28 | 0% | 0% |
| Lead time (a), horas | 28 | 28 | 0 | 28 | 0% | 0% |
| Lead time (b), horas | 28 | 28 | 0 | 28 | 0% | 0% |
| CFR de CI | 28 | 28 | 2 | 26 | 0% | 0% |
| CFR de entrega | 28 | 16 | 5 | 23 | 0% | 312,5% |
| Recuperação, horas | 26 | 26 | 0 | 26 | 0% | 0% |

A mediana do erro relativo absoluto também é zero em todas as métricas,
mas isso **não significa igualdade em todos os pares**. CFR de entrega
diverge em 12/28: `signalapp/Signal-Desktop` passa de 0,1454545 a 0,6
(+312,5%); `nginx/nginx` passa de zero a 0,3043478 (+30,43 pontos percentuais,
diferença relativa indefinida). A publicação registra `heuristica_versao=v3`
e a replicação `v1` nos 28 pares. Essa diferença de versão é observada;
sem execução controlada com as duas versões, não atribuímos causalmente
todas as divergências a ela. Duas recuperações estão ausentes nas duas
fontes (`Mithril-mine/libmdbx` e `aseprite/aseprite`).

## Concordância de classificação

| Classe do parceiro | Pares com classe nas duas fontes | Iguais | Concordância |
|---|---:|---:|---:|
| Frequência | 28 | 28 | 100% |
| Lead time (a) | 28 | 28 | 100% |
| CFR de CI | 28 | 28 | 100% |
| Recuperação | 26 | 26 | 100% |
| Geral C1 | 28 | 28 | **100%** |

O percentual de mesma classe geral é **28/28**, condicionado aos projetos
comuns, não 30/30 nem 237/237. A sobreposição de identidades é 28/30
(93,33%) e mede outra coisa. O dicionário parceiro define sua C1 como
release + LT(a) + CFR de CI; não é a C1 de nosso estudo (LT(b) + CFR(a)).
A CFR de entrega divergente não integra essa classe. Não há coluna de
classe CFR de entrega publicada nesse CSV; não a reconstruímos com cortes
potencialmente distintos. Concordância de C1 não valida os proxies nem
demonstra reprodução integral das 237 linhas.

## Problemas documentados e limite de prazo

**Não conseguimos criar as issues no repositório do grupo parceiro devido
ao prazo reduzido e ao tempo corrido de que dispusemos.** O registro local
preserva os achados para rastreabilidade, sem afirmar envio, recebimento
ou correção pelo grupo autor. O critério de abertura externa da #181
fica registrado como não realizado por essa limitação.

Os seis problemas de execução e seus contornos estão na #180: instruções
de ambiente Windows, silêncio prolongado do log, falta de estimativa de
tempo/consumo de API, funil sem avaliados, codificação do console e
sobrescrita das saídas. Para a comparação, acrescentam-se a diferença
de versão da heurística e as 12 divergências em CFR de entrega; dois
projetos ausentes na publicação; e a publicação de 237 projetos diante
do mínimo planejado de 300 e alvo 350. O motivo da parada do parceiro
não é conhecido: o prazo aqui informado descreve nossa impossibilidade
de abrir issues, não explica a amostra publicada por eles.

## Conferência

Além dos testes dos casos de base zero, ausência, sinal, valores não finitos
e identidades duplicadas, a comparação foi conferida por leitura independente
dos CSVs: contagem de pares, diferenças por coluna, versões e classes.
Não foi executado novamente o coletor nem alterado qualquer CSV de entrada.
