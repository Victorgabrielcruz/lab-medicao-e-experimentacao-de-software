# Ameaças externas e de conclusão — FIN-05 (#184)

Entrega na branch `feat/conclusao-tasks-matheus`, a partir de `91f0518`.
O arquivo principal é `main.tex`; as ameaças estão em
[discussao.tex](discussao.tex), na seção já existente de discussão e validade.

## Critérios e evidências

| Critério da #184 | Conteúdo entregue | Mitigação e limite |
|---|---|---|
| Ameaças externas: generalização | Seleção não probabilística por popularidade, Actions e mínimos de atividade; adiamento de candidatos; projetos privados e outras ferramentas fora do recorte | Funil, ordem e critérios auditáveis; conclusões restritas ao recorte, sem alegar remoção do viés |
| Ameaças externas: janela e avaliação humana | Um ciclo anual, painel inicial de 429; amostra-ouro de 60/255 projetos, 296/300 releases avaliáveis | Denominadores explícitos e proposta de validação independente em outras janelas e populações; sem generalizar F1 aos 500 |
| Ameaças de conclusão: testes | Hipóteses complementares posteriores ao piloto; Spearman sem ajuste; Holm em famílias locais; confundimento e dependência entre projetos | Interpretação exploratória, tamanhos de efeito, ausência de causalidade; não afirmar controle de toda multiplicidade |
| Ameaças de conclusão: tamanho amostral | 500 nominais, 499 LT(b), 498 CFR(b), 469 recuperações; casos completos e grupos desbalanceados | Informar n por análise e sensibilidade à qualidade/variantes; ausência de análise de poder declarada, sem alegar suficiência ou equivalência |
| Mitigações descritas | Cobertura, censura, variantes, dados contínuos, funil e rastreabilidade | Ausências não viram zero; as verificações não eliminam seleção, dependência ou ausência informativa |

As fontes são as definições e o funil em `metodologia.tex`, os resultados
em `resultados.tex`, as tabelas em `../analise/tabelas/`, a robustez em
`../analise/rq07/` e o painel temporal da #175. Não foram introduzidos
novos testes estatísticos, novos dados nem referências externas nesta revisão.

## Relação com #179 e #181

A #179 já foi implementada e integrada pelo PR #255 (`d02376a` consta
no histórico da base). Seu confronto das sete expectativas, implicações e
literatura foi preservado. O registro original permanece em
[validacao-s03-179.md](validacao-s03-179.md); não se apresenta essa discussão
como implementação nova desta branch.

A comparação da #181 foi concluída localmente com os CSVs congelados;
[fontes, fórmulas, resultados e reprodução](../replicacao/fin-02-comparacao/README.md).
A classe C1 do parceiro usa LT(a), enquanto nossa C1 usa LT(b). A nova
redação distingue identidade, concordância de classes e divergências de
CFR de entrega. A abertura de issues no repositório parceiro não foi
realizada por falta de tempo, conforme informado pelo usuário, e está
explicitamente registrada como limitação. Não há alegação de tentativa
rejeitada pela API nem de envio de mensagens ao parceiro.

## Validação desta entrega

- Script offline executado: 237 publicados, 30 replicados, 28 pares;
  seis métricas e cinco classes, com bases zero e ausências explícitas.
- Cinco testes aprovados: base e sinal da diferença, zero, ausência,
  valores não finitos e pareamento com rejeição de duplicatas.
  A primeira execução foi bloqueada ao criar o CSV temporário pela sandbox;
  a execução autorizada fora dela passou.
- Conferência independente dos CSVs por PowerShell, incluindo pares,
  classes, ausências e versões da heurística.
- Compilação integral confirmada pelo editor nativo com `artigo` como
  raiz e `main.tex` como principal. A tentativa com raiz `Lab03` encontrou
  bloqueio de leitura de `.pytest_cache`; compilar com a raiz do artigo
  teve sucesso, sem alterar fontes ou remover caches.
- Sem alteração de hipóteses, resultados analíticos originais, amostra-ouro,
  CSV da #180 ou definições dos coletores. Não houve nova coleta ou
  sincronização com Overleaf. A revisão visual e de páginas da #186
  não é confirmada apenas pela compilação.
