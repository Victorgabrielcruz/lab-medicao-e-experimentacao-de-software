# Retorno recebido do grupo replicador — FIN-03 (#182)

Em 22/10/2026 foram lidas as quatro issues criadas por
[Cardosoooo](https://github.com/Cardosoooo) no nosso repositório. Todas se
referem ao commit `24b366e`, Windows 11 e Python 3.12.10. A análise do
código foi feita antes das alterações; nenhuma correção exige nova coleta
nem recálculo da base. Esta entrega trata o retorno recebido sobre nosso
pipeline, distinto da execução do pipeline parceiro na #180.

## Análise e tratamento por issue

| Issue | Diagnóstico anterior à implementação | Correção e verificação |
|---|---|---|
| [#251](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/251) | O integrado já aceita `--candidatos`, lê `candidatos` do JSON e recusa IDs duplicados. Faltavam formato e exemplo de replicação. | README documenta os campos, uma lista fixa, fonte fora da saída, caminhos isolados, janela e critérios preservados, alvo/limite 30 e a possibilidade de menos elegíveis. O exemplo que consulta a API não foi executado. |
| [#252](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/252) | `test_releases_snapshot.py` lia JSON UTF-8 sem especificar a codificação. A produção já grava UTF-8. | Leituras e escrita do JSON de teste agora têm `encoding='utf-8'`. Dez testes passaram com `PYTHONUTF8=0` e padrão local `cp1252`. |
| [#253](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/253) | Dois módulos importavam scripts de entregas durante a coleta do pytest, sem conferir sua presença. Os testes usam pacotes sintéticos, não dependem dos GB publicados. | O README documenta clone filtrado e sparse-checkout excluindo apenas binários. Se os scripts também forem omitidos, os módulos são ignorados com motivo explícito. Dois testes novos verificam essa ausência; 14 testes passaram num checkout local sem partes, gzip ou ZIP, com scripts e CSV pequeno preservados. |
| [#254](https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/254) | `_espera_limite` devolvia zero quando `remaining=0` e o reset informado já havia passado, esgotando quatro repetições sem pausa. | O caso usa o backoff crescente de 60, 120, 240 e 480 segundos. Reset futuro e `Retry-After` mantêm suas regras; erros permanentes de permissão continuam propagados. Os testes reproduziram o erro antes da correção e confirmam recuperação, repetição da mesma página, cache apenas do sucesso e limite finito sob 403/429 persistente. |

O limite de quatro repetições foi preservado: a correção evita tentativas
imediatas na virada da cota, mas não promete recuperação ilimitada quando
o servidor mantém o erro. Nessa condição, o cache/checkpoint permanece
disponível para a retomada documentada. Datas, rótulos, métricas e regras
de elegibilidade não foram alterados.

## Validação

- 73 testes direcionados de rate limit, snapshots e publicação aprovados.
- 10 testes de snapshot aprovados com codificação padrão Windows `cp1252`
  e UTF-8 automático desativado.
- 14 testes aprovados numa cópia Git local com as regras de sparse-checkout
  do README: nenhum arquivo `.part*`, `.gz` ou `.zip` presente; scripts de
  publicação e CSV final preservados. Não houve download ou restauração de
  snapshots nesse teste.
- Suíte completa: **1.199 testes aprovados**, **94,67% de cobertura**,
  Python 3.12.14. Os coletores usam fixtures, HTTP e passagem do tempo simulados;
  os testes das análises também leem o CSV congelado, com saídas temporárias.

O ambiente virtual recebeu `scikit-learn==1.9.1`, já exigido pelo projeto,
e teve SciPy alinhado a `1.17.1`, conforme `requirements.txt`. A primeira
execução integral encontrou bloqueio de hard links na sandbox e SciPy local
1.18.1 divergente do contrato. Com a versão correta e os testes executados
fora da sandbox, a suíte passou sem alteração desses módulos de produção.

Comandos, a partir de `Lab03`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_rate_limit.py tests/test_releases_snapshot.py tests/test_publicacao_500.py tests/test_compares_publicados.py -q
$env:PYTHONUTF8 = '0'
.venv/Scripts/python.exe -m pytest tests/test_releases_snapshot.py -q
Remove-Item Env:PYTHONUTF8
.venv/Scripts/python.exe -m pytest --cov=pipeline --cov-report=term --cov-fail-under=80
```

Nenhum comando do coletor foi executado sobre a amostra real: não houve
novas consultas de coleta, recálculo de métricas a partir dos commits/runs,
modificação dos pacotes publicados ou revisão dos resultados empíricos.

## Project e encerramento

A #182 exige também incluir as issues recebidas no
[Project 7](https://github.com/users/Victorgabrielcruz/projects/7).
A consulta autenticada à API de Projects retornou `INSUFFICIENT_SCOPES`:
a credencial disponível não permite ler Projects. Assim, o vínculo das
quatro issues não pôde ser conferido nem atualizado. A escrita requer
permissão de Projects; este item administrativo permanece pendente.

As correções das #251–254 podem ser revisadas e integradas. A #182 deve
permanecer aberta até confirmar o vínculo das quatro issues no Project
e registrar o tratamento entregue. Não foram enviadas respostas individuais
ao replicador por esta execução; o relatório e o PR concentram as evidências
do tratamento para revisão.
