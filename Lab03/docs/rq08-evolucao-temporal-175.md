# RQ08 bônus — Evolução temporal (#175)

## Escolha e pré-requisitos

Foi escolhida **evolução temporal da frequência de releases estáveis**, em
vez de rework rate. Pergunta exploratória: como varia essa frequência nos
meses da janela, considerando os mesmos projetos? A escolha foi registrada
nesta entrega, após a coleta, sem alegar hipótese pré-registrada.

A base local contém as datas necessárias; não houve nova coleta, consulta
à API ou alteração dos CSVs anteriores. A extração lê `releases.json`, mas
o notebook exige apenas dois CSVs pequenos e seus manifestos: o dataset
final dos 500 e `analise/dados/rq08_releases.csv` (cerca de 1,4 MB).

## Dados e integridade

Foram selecionados os 500 IDs do dataset final entre os 932 registros do
consolidado local. Preservam-se somente `repo_id`, `release_id` e
`published_at` UTC: **34.255 releases estáveis**, sem drafts/prereleases.
Foram excluídas 8.892 pré-releases/drafts na extração. Notas, mensagens,
tokens e commits não fazem parte dessa tabela.

A contagem de cada projeto, dividida pelas semanas reais da janela,
reproduziu a `deployment_frequency` do CSV final, com zero divergências.
Essa é uma conferência de consistência, não uma prova de completude da API.
O manifesto registra os filtros, totais e hashes:

- Dataset final: `2552ba6b0779e895d01bea88742cb668ee1812a8369a224ed5281708140b30bd`.
- JSON de origem: `45edf0a1341c7419195b8a6d3dcf5366d3de5afab7af7b82e651c4ba9aa34d2f`.
- CSV de eventos: `569914771958ab8c2f882ec1dd2f12e01405e833888c716bc3d4d0a958187131`.

## Método

A janela permanece `[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.
Dos 500 projetos, 71 foram criados após o início. A análise principal usa
um painel fixo dos **429 existentes no início**, excluindo esses 71 em vez
de lhes atribuir meses sem releases antes de existirem.

Cada projeto do painel recebe 12 registros mensais, incluindo zero quando
não há release estável registrada. A taxa divide a contagem por
`dias reais do mês / 7`. São reportados média, mediana e quartis lineares
entre projetos. Não se aproximam meses por quatro semanas.

Os primeiros seis meses (outubro a março, 182 dias) e os seis seguintes
(abril a setembro, 183 dias) são comparados por ID. Cada taxa semestral
usa a contagem total dividida pela sua exposição em semanas; não é uma
média simples das taxas mensais. A mediana da diferença pareada é
calculada depois de subtrair taxas do mesmo projeto.

A sensibilidade retira projetos com `coleta_incompleta` ou `calculo_parcial`
no CSV, restando **398**. Os indicadores se referem à coleta/análise geral,
não especificamente à completude das releases. Não são recalculadas as
outras métricas DORA.

## Resultado descritivo

| Painel | n | Mediana 1º semestre | Mediana 2º semestre | Mediana da diferença | Aumentaram | Diminuíram |
|---|---:|---:|---:|---:|---:|---:|
| Inicial | 429 | 0,384615 | 0,420765 | 0,036780 | 228 | 201 |
| Sem alertas | 398 | 0,346154 | 0,420765 | 0,036675 | 211 | 187 |

As taxas e diferenças estão em releases por semana. Não houve igualdade
das taxas semestrais nesses painéis; a diferença de duração pode produzir
taxas distintas mesmo com contagens iguais. As medianas mensais do painel
inicial variam de 0,225806 a 0,466667. O gráfico mostra oscilações e IQR
amplo; a diferença entre semestres não representa crescimento uniforme.

É uma descrição de um único ciclo anual, sem teste de tendência,
sazonalidade ou causalidade. A seleção retrospectiva por popularidade e
pelo mínimo anual de releases restringe a generalização. Publicar mais
releases não demonstra melhoria DORA geral nem redução de incidentes.
Os 71 projetos novos não são representados pelo painel principal.

## Reprodução

A partir de `Lab03`, com `requirements.txt` instalado:

```powershell
.venv/Scripts/python.exe -m jupyter nbconvert --to notebook --execute --inplace analise/s03-09-rq08-evolucao-temporal.ipynb
```

O notebook também funciona com pasta de trabalho `Lab03/analise/`.
`LAB03_RQ08_DATASET` e `LAB03_RQ08_EVENTOS` permitem entradas alternativas,
acompanhadas dos manifestos. `LAB03_RQ08_SAIDA` define outra pasta que
receberá `tabelas/` e `figuras/`; caminhos relativos partem da pasta de
trabalho. Entradas inconsistentes são recusadas antes da análise.

Para gerar apenas as tabelas, sem notebook:

```powershell
.venv/Scripts/python.exe -m pipeline.evolucao_temporal --saida data/processed/rq08-reproducao
```

Para reconstruir a tabela de datas a partir de um JSON local já coletado:

```powershell
.venv/Scripts/python.exe -m pipeline.evolucao_temporal --releases data/raw/amostra-final-500/releases.json --eventos analise/dados/rq08_releases.csv
```

Se esse JSON não estiver disponível, os checkpoints publicados podem ser
restaurados offline por `pipeline.releases_snapshot`, conforme a #162.
Passe o JSON reconstruído em `--releases`; a extração exige reconciliação
com os 500 IDs/contagens. A tabela publicada dispensa essa restauração para
reexecutar o notebook. Nenhum desses comandos chama o coletor ou a API.

## Artefatos e validação

- Notebook executado, com resultados salvos: `analise/s03-09-rq08-evolucao-temporal.ipynb`.
- Eventos/manifesto: `analise/dados/rq08_releases.csv` e `.json`.
- Painel: `analise/tabelas/rq08_painel_mensal.csv`, com 5.148 linhas.
- Resumos: `rq08_mensal.csv` (24 linhas), `rq08_semestres.csv` (2 linhas)
  e `rq08_proveniencia.json`, na mesma pasta.
- Figura: `analise/figuras/rq08_evolucao_mensal.png`, inspecionada visualmente.
- Texto e figura incorporados em `artigo/resultados.tex`; o artigo completo
  compilou com sucesso no compilador nativo. A revisão do limite final de
  páginas permanece na #186.

O notebook foi executado de `analise/` e reexecutado em kernel limpo de
`Lab03/`, com saída isolada. As três tabelas e a proveniência foram
idênticas byte a byte. Uma contagem independente dos eventos por ID e mês,
sem pandas, confirmou as medianas semestrais, a mediana das diferenças e
os 228/201 aumentos/diminuições. O kernel local precisou ser executado fora
da sandbox; configurações e resultados temporários ficaram no workspace.

Os 20 testes específicos cobrem limites UTC, duplicação, filtros, zeros,
exclusão por criação, dias reais/bissexto, pareamento, coorte vazia de
sensibilidade, hashes e fontes inconsistentes, preservação das entradas,
CLI sem rede e reprodução. A suíte completa aprovou **1.219 testes**, com
**94,37% de cobertura global**; o módulo novo alcançou **87%**.
