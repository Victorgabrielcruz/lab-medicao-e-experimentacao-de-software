# Amostra real de CI — S01-02 (#263)

Coleta para o par **P4 — Z para proporção × binomial exato**, descrita na
[issue #263](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/263).
Cada linha representa uma execução completa do workflow, com `falhou = 1`
para `failure` e `falhou = 0` para `success`. A meta de **5%** é a referência
didática do Lab04; não é uma meta declarada pelo projeto observado.

## Origem e janela

| Item | Valor |
|---|---|
| Repositório público | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| Workflow | [`test`, ID `22158026`](https://github.com/pytest-dev/pytest/actions/workflows/test.yml) |
| Definição | [`.github/workflows/test.yml`](https://github.com/pytest-dev/pytest/blob/main/.github/workflows/test.yml) |
| Branch principal | `main` |
| Evento | Somente `push` |
| Regra fixada antes de observar as conclusões | 300 execuções mais recentes até o corte; depois aplicar os descartes |
| Corte de criação, inclusivo | `2026-11-01T17:47:58Z` |
| Coleta | `2026-11-01T17:48:34Z` (01/11/2026, 14:48:34 em São Paulo) |
| Período efetivamente encontrado, UTC | `2026-04-20T21:31:49Z` a `2026-10-30T10:38:59Z` |

O projeto não estava arquivado e teve atividade em 01/11/2026. O workflow
foi escolhido por executar testes de um projeto Python ativo e permitir
`push` na branch principal, antes de consultar suas taxas de sucesso/falha.
Restringir o evento a `push` evita misturar execuções de PRs ou disparos
manuais. Não houve seleção por resultado, autor ou commit.

## Procedimento e regra de descarte

1. Consultar os metadados do repositório e a lista de workflows na API pública
   do GitHub, sem autenticação, e confirmar `main` e o workflow `test`.
2. Consultar as páginas 1, 2 e 3 do endpoint de execuções desse workflow,
   com 100 registros por página, `branch=main`, `event=push` e criação até
   o corte. **Não filtrar `status` nem `conclusion` na API**, para contabilizar
   também os descartes. As três páginas retornaram 300 `run_id` distintos.
3. Guardar os campos necessários das respostas no snapshot, junto dos URLs
   consultados, contagens por página e SHA-256 das respostas originais.
   O snapshot é uma projeção dos dados, não uma cópia integral dessas respostas.
4. Validar repositório, ID/nome do workflow, branch, evento, unicidade dos IDs
   e corte temporal. Manter somente `status=completed` e conclusão exatamente
   `success` ou `failure`. Descartar `cancelled`, `skipped`, `timed_out`,
   `neutral`, outros resultados e execuções sem conclusão.
5. Ordenar os registros válidos de forma crescente por `(created_at, run_id)`
   e exportar o CSV em UTF-8. Não embaralhar ou agrupar por conclusão.

Foram descartadas **57 `cancelled`**; as demais categorias de descarte
tiveram contagem zero. A janela original tem 300 execuções consecutivas do
workflow/branch/evento escolhidos; o CSV contém as 243 válidas dessa janela.
Lacunas no `run_number` também podem corresponder a outras branches/eventos.

Uma reexecução mantém o mesmo `run_id`: considera-se apenas a conclusão da
última tentativa disponível na coleta, sem transformar tentativas em novas
observações. Das 300 execuções, 299 estavam em `run_attempt=1` e uma em
`run_attempt=2`; esse campo permanece no snapshot. Portanto, a estimativa
descreve a conclusão observada por execução, não a taxa da primeira tentativa.

Comando de consulta equivalente, em um shell Linux/macOS com `curl`, usando
a [API oficial de workflow runs](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-workflow):

```bash
for pagina in 1 2 3; do
  curl --fail-with-body --silent --show-error --location --get \
    -H 'Accept: application/vnd.github+json' \
    -H 'X-GitHub-Api-Version: 2022-11-28' \
    --data-urlencode 'branch=main' \
    --data-urlencode 'event=push' \
    --data-urlencode 'created=<=2026-11-01T17:47:58Z' \
    --data-urlencode 'per_page=100' \
    --data-urlencode "page=$pagina" \
    'https://api.github.com/repos/pytest-dev/pytest/actions/workflows/22158026/runs' \
    --output "pagina-$pagina.json"
done
```

Os URLs exatos usados estão no snapshot. Uma consulta futura pode retornar
conclusões alteradas por reexecuções ou perder execuções removidas pelo
projeto. Para reproduzir esta entrega, use o snapshot versionado, sem
consultar novamente a API.

## Arquivos e reprodução offline

| Arquivo | Conteúdo |
|---|---|
| [`ci_pytest.csv`](ci_pytest.csv) | Uma linha por execução válida, em ordem cronológica |
| [`ci_pytest_snapshot.json`](ci_pytest_snapshot.json) | Origem, consultas e 300 registros, incluindo descartes e tentativa observada |
| [`ci_pytest_resumo.json`](ci_pytest_resumo.json) | Contagens, período, descartes e estatísticas sem arredondamento |
| [`../hipotese/dados_reais.py`](../hipotese/dados_reais.py) | Validação, exportação e cálculos reproduzíveis |

Colunas do CSV: `run_id`, `workflow`, `branch`, `evento`, `conclusao`,
`criado_em`, `url`, `falhou`. Datas usam ISO 8601 em UTC (`Z`). O `run_id`
identifica a execução e `url` permite conferir sua origem no GitHub Actions.

Com as dependências do Lab04 instaladas, a partir de `Lab04`:

```bash
.venv/bin/python -m hipotese.dados_reais
.venv/bin/python -m pytest
```

No Windows, substitua `.venv/bin/python` por `.venv/Scripts/python`.
O primeiro comando regenera somente o CSV e o resumo; não acessa a rede nem
altera o snapshot. Os testes verificam também a reprodução exata dos arquivos.

## Estatísticas descritivas

| Medida | Resultado |
|---|---:|
| Execuções inspecionadas | 300 |
| Descartadas (`cancelled`) | 57 |
| Execuções válidas | 243 |
| Sucessos | 233 |
| Falhas | 10 |
| Taxa de falha observada | 4,1152% |
| IC nominal de 95% de Wilson | [2,2504%; 7,4082%] |
| Maior sequência de falhas na amostra válida | 3 |
| Maior sequência sem descartes intermediários | 2 |
| Autocorrelação amostral de lag 1, na amostra válida | 0,274072 |

O IC usa o [método de Wilson sem correção de continuidade](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html),
adequado para evitar o intervalo degenerado da aproximação de Wald quando
há poucas ou nenhuma falha. É calculado por
`binomtest(k=10, n=243).proportion_ci(confidence_level=0.95, method="wilson")`.
A referência de 5% pertence ao intervalo nominal; a comparação formal entre
os testes e a conclusão inferencial pertencem à etapa de aplicação real.

## Sequências e calibração de `rajadas` (#265)

Seja `x_t = falhou` em ordem cronológica e `p = média(x)`. A autocorrelação
usada é a ACF amostral sem ajuste por `n-k`:

```text
r1 = soma de t=2 até n [(x_t - p)(x_(t-1) - p)]
     / soma de t=1 até n [(x_t - p)^2]
```

Ela corresponde à convenção de
[`statsmodels.tsa.stattools.acf(adjusted=False, fft=False)`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.acf.html)
no lag 1; não é exatamente a correlação de Pearson calculada com médias
separadas para as duas subsequências. Para uma série constante, retorna-se
`null`, pois a autocorrelação é indefinida.

As transições entre as 243 observações válidas são:

| Anterior → seguinte | Contagem |
|---|---:|
| Sucesso → sucesso | 226 |
| Sucesso → falha | 7 |
| Falha → sucesso | 6 |
| Falha → falha | 3 |

Assim, `P(falha seguinte | sucesso) = 7/233 = 3,0043%` e
`P(falha seguinte | falha) = 3/9 = 33,3333%`. A última observação é uma
falha e não tem sucessora, por isso o segundo denominador é 9, não 10.
Essas frequências, a taxa marginal de 4,1152% e `r1 ≈ 0,2741` são referências
descritivas para calibrar a persistência da situação `rajadas`, sem substituir
a meta de 5% sob H₀. Há somente nove transições iniciadas por falha: os
parâmetros de persistência têm bastante incerteza.

**Adjacência significa aqui execuções válidas consecutivas**, e não intervalo
fixo de tempo. Uma execução cancelada pode existir entre duas linhas do CSV.
Por exemplo, as três falhas de 23/05/2026 formam uma sequência na amostra
filtrada, mas há cancelamento intermediário; na sequência original de 300
execuções, exigindo que um descarte interrompa a sequência, o máximo é 2.
O snapshot permite distinguir as duas situações. Nenhum cancelamento é
recodificado como sucesso ou falha.

## Limitações

O IC binomial tem cobertura nominal sob observações independentes com
probabilidade constante; não corrige dependência temporal. A autocorrelação
positiva e as sequências motivam estudar `rajadas`, mas não demonstram, por si
só, dependência estatisticamente significativa. O IC deve ser interpretado
com essa limitação, não como garantia de cobertura sob rajadas.

Excluir cancelamentos segue a regra da atividade, mas condiciona a taxa às
execuções que chegaram a `success`/`failure`; o workflow cancela execuções
anteriores do mesmo grupo de concorrência. O período de cerca de seis meses
também pode envolver mudanças de código, matriz de testes e infraestrutura.
Uma falha do workflow agregado não identifica sua causa e não equivale
necessariamente a um defeito do produto. Os resultados não representam
outros workflows, branches ou projetos.
