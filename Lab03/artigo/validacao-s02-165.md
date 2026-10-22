# Conferência da metodologia de validação manual — S02-15 (#165)

## Revisão com as fontes finais — 22/10/2026

O relato de [metodologia.tex](metodologia.tex) passou do protocolo previsto
para os registros efetivamente disponíveis. As seis planilhas estão completas
(60 tipos, 60 decisões de entregas e 300 releases por avaliador). Foram
reexecutados `pipeline.kappa` e `pipeline.consenso` em pastas temporárias:
**os JSONs e CSVs resultantes são idênticos aos oficiais**, sem sobrescrita.

| Dimensão | Itens completos | Fleiss |
|---|---:|---:|
| Tipo de projeto | 60 | 0,8745696015740285 |
| Entregas reais | 60 | 0,7443181818181829 |
| Release corretiva | 300 | 0,952752185211434 |

O consenso tem 405 itens unânimes e 15 divergentes resolvidos, 249 releases
corretivas e 51 não corretivas. A avaliação final #162 usa 296/300 pares,
matriz `[[17,30],[5,244]]`, precisão 0,8905109489051095, recall
0,9799196787148594 e F1 0,9330783938814532. As quatro primeiras releases sem
predecessora, registradas na fonte final, não receberam previsão artificial.
A #163 mantém a v1 sem refinamento, com justificativa e limites condicionais.

Fontes atuais:

- [manifesto e livro de códigos](../validacao/amostra-ouro/LIVRO-CODIGOS.md);
- [kappa](../validacao/amostra-ouro/kappa.json),
  [protocolo de consenso](../validacao/amostra-ouro/PROTOCOLO-CONSENSO.md) e
  seus CSVs preservados;
- [procedimento real de C](../docs/rotulagem-c-158.md) e
  [de B](../docs/rotulagem-b-157.md);
- [avaliação com as fontes finais dos 500](../validacao/avaliacao-heuristica/final-500/README.md)
  e [histórico da regra](../validacao/refinamento-heuristica/versoes.json).

O texto não presume independência a partir de arquivos completos. Relata a
assistência a C, a consulta à documentação de B e a declaração de trabalho
conjunto. O protocolo registra reunião em 20/10 e a complementação de C está
documentada em 21/10: não se afirma cronologia completa e comprovada antes
do consenso. A definição aplicada inclui releases mistas com alguma correção,
em vez de exigir correção como objetivo principal. Kappa e F1 são resultados
contra os registros disponíveis, sujeitos a essas limitações.

Reprodução das conferências, a partir de `Lab03`:

```bash
python -m pipeline.kappa --saida /tmp/lab03-conferencia-kappa
python -m pipeline.consenso --saida /tmp/lab03-conferencia-consenso
```

Nenhuma planilha, decisão humana, fonte congelada ou sorteio foi alterado.
A prévia isolada usada em 15/10 não existe mais no caminho temporário;
não foi criada substituta nem aberta outra aba. A compilação atual do
projeto completo é registrada ao final desta revisão.

## Registro histórico da entrega de 15/10/2026

As afirmações abaixo descrevem exclusivamente a base consultada naquela data.

Revisão documental de **15/10/2026**, na branch
`feat/s02-15-metodologia-validacao-manual-165`, a partir da `main`
`2b4ea3bdba8502a71cb5ea6b4b9fa422775d19a3`.

## Fontes e limites

- [metodologia.tex](metodologia.tex): seção **Validação manual**, protocolo,
  fórmulas e situação da execução, com referência cruzada a partir da CFR(b).
- [amostra_ouro.py](../pipeline/amostra_ouro.py): gerador da #155, 60
  repositórios, 5 releases por repositório, três rotuladores e semente 42.
- [config.yaml](../config.yaml): releases estáveis, sem pré-releases, na
  janela UTC `[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.
- [decisao-encerramento-255.md](../docs/decisao-encerramento-255.md): população
  congelada de 255, preservando a limitação frente ao mínimo original de 300.
- [rotulagem-c-158.md](../docs/rotulagem-c-158.md) e
  [evidência C](../docs/evidencias/158-preparacao-c.json): preparação aguardando
  o sorteio oficial, sem rotulagem humana concluída.
- Seção 6 do enunciado fornecido pelo usuário: amostra-ouro, independência,
  Fleiss, consenso, avaliação e refinamento da heurística.

A base consultada não contém `validacao/amostra-ouro/amostra_ouro.json`,
rótulos independentes completos, consenso nem resultados de kappa, precisão,
recall ou F1. O tamanho 60/300 é **previsto**, não uma contagem de itens já
rotulados. Não foi gerado sorteio alternativo, preenchido rótulo humano,
implementada heurística ou calculada métrica empírica por esta entrega.
Planilhas individuais A/B/C não foram consultadas.

## Cobertura dos critérios

| Critério da #165 | Conteúdo entregue | Dependência empírica |
|---|---|---|
| Amostra-ouro e rotulagem descritas | População de origem, dois sorteios sem reposição, semente, manifesto comum, categorias, independência e ausências. | Sorteio oficial #155 e preenchimento humano #156–158. |
| Fleiss e consenso reportados | Cálculo nas três dimensões antes da conciliação, itens completos, marginais, casos não estimáveis e proposta de consenso com rastreabilidade. | Julgamentos independentes, relatório de concordância e alinhamento/execução do consenso. |
| Precisão, recall e F1 reportados | Classe positiva, associação por IDs, matriz de confusão, fórmulas, denominadores nulos, cobertura e histórico de refinamentos. | Previsões #161, consenso e execução da avaliação #162; refinamento #163 quando necessário. |

O texto metodológico não declara resultados numéricos disponíveis nem
conclusão da validação. A proposta de consenso precisa ser alinhada com a
entrega responsável antes de ser relatada como executada. Resultados futuros
devem substituir a situação pendente somente quando acompanhados dos
artefatos correspondentes. Nenhuma issue ou cartão foi alterado.

O parágrafo da CFR(b) também foi alinhado ao enunciado: uma release falha
quando é seguida por uma corretiva em até sete dias, excluindo do denominador
as releases dos últimos sete dias da janela. O rótulo avaliado na heurística
é **corretiva**, não diretamente a ocorrência de falha na release anterior.

## Referências conferidas

As entradas bibliográficas anteriores foram preservadas; foram acrescentadas
Fleiss (1971) e as documentações das funções previstas:

- [Fleiss e `aggregate_raters`](https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.fleiss_kappa.html):
  itens nas linhas e categorias nas colunas, marginais amostrais e método
  `fleiss`. A [fonte da implementação](https://www.statsmodels.org/stable/_modules/statsmodels/stats/inter_rater.html)
  confirma a fórmula e os metadados bibliográficos do artigo original.
- [`aggregate_raters`](https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.aggregate_raters.html):
  transformação de item/avaliador para contagens item/categoria.
- [`precision_recall_fscore_support`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html):
  métricas da classe positiva, suportes e necessidade de declarar a política
  de divisão por zero.

São referências ao procedimento previsto; não se declara que as bibliotecas
já estejam instaladas ou que esses cálculos tenham sido executados no estudo.

## Conferência e compilação

- Chaves LaTeX balanceadas, labels únicos e referências cruzadas resolvidas
  nas fontes da metodologia.
- Todas as citações da seção têm entradas em `referencias.bib`; as quatro
  entradas anteriores foram preservadas e três referências foram adicionadas.
- Links locais dos arquivos desta entrega conferidos e `git diff --check`
  sem erros.
- **Compilação da metodologia isolada confirmada com sucesso** pelo compilador
  do editor nativo. A prévia local está em
  `/private/tmp/lab03-s02-165/metodologia-preview.tex`, com o conteúdo literal
  da metodologia dentro de um único documento `article`, pacotes de idioma,
  geometria, URL e matemática e bibliografia inline para as três citações.
  A prévia foi encaminhada ao editor e não depende de inputs externos.

Essa conferência não equivale à compilação do artigo completo no template
SBC. Não houve sincronização do Overleaf, exportação de PDF/ZIP, alteração
dos resumos, resultados, discussão ou conclusão do piloto. Os arquivos de
estilo e os coletores permanecem preservados. A validação documental não
executa a suíte Python nem a coleta de dados.

## Impressões digitais

Os hashes abaixo identificam as fontes e a prévia efetivamente compilada.

| Artefato | SHA-256 |
|---|---|
| artigo/metodologia.tex | `f1bc380d4ae06da957b8d4588c21795ba35ea69089957ea0827c5e692c4f19f6` |
| artigo/referencias.bib | `6d69558db69bcdf2f34f136f8ebd0a8605a5905692c05fe3605d36ea8c8595c1` |
| artigo/README.md | `7adacfe32308bf4d58c4da3a6af879475d26caacd37a428eb77ada062bec1278` |
| Prévia isolada compilada | `89693b72682426cd9bfcacbd6de6de5d934b0a0e29d5d2d1c934a2747fefa61d` |
| Gerador da amostra-ouro (preservado) | `d1700a65cc5fa8c28f1a9addcadf8952e3a86f7ea2dc5e19ee32871b37493c43` |

## Conferência atual de compilação e integridade — 22/10/2026

O projeto completo compilou com sucesso no compilador nativo, usando raiz
`Lab03` e principal `artigo/main.tex`, incluindo as figuras existentes de
`analise/figuras`. Não foi aberta nova aba nem substituída a antiga prévia.
Não houve exportação de PDF ou sincronização do Overleaf; a confirmação não
representa inspeção visual de todas as páginas.

A suíte dos arquivos oficiais aprovou 1.169 testes, com dois ignorados e
94,80% de cobertura. Cópias locais alheias à entrega, com sufixo ` 2.py`,
foram preservadas e excluídas dessa medição. Os CSVs de consenso e as seis
planilhas humanas permanecem idênticos aos recebidos da `main`.
