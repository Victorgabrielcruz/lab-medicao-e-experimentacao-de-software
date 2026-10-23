# FIN-06 — Relato da replicação cruzada (#185)

Revisão de 22/10/2026 sobre a main `7278a40`. Implementação textual no
artigo LaTeX, incorporada pelo `main.tex` existente; não apenas Markdown.

## Critérios e evidências

| Critério | Local no artigo | Fonte |
|---|---|---|
| Processo descrito | Metodologia, `sec:metodo-replicacao` | [Execução #180](../replicacao/fin-01-execucao/README.md): commit parceiro, ambiente, configuração, limite e retomada; [retorno #182](../replicacao/fin-03-retorno/README.md): ambiente e lista usada pelo replicador |
| Problemas e diferenças relatados | Resultados, `sec:resultados-replicacao` | Seis obstáculos da #180, funil, 30 projetos e 28 presentes na publicação de 237; falha textual e interrupção por 403 reportadas nas issues recebidas |
| Ações a partir das issues recebidas | Resultados, itens #251–254 | Tratamento integrado pelo PR #256: documentação, UTF-8, clone parcial/testes e backoff finito |

A discussão explicita o alcance das evidências. 28/30 = 93,33% é
sobreposição de identidades, não concordância de classes. Os 8.320
candidatos não avaliados não são descartes; 58 + 88 + 9 + 30 = 185.
Os 1.199 testes e 94,67% são a validação histórica da #182, sem alegar
nova execução da suíte nesta alteração textual. O relato externo de
1.170 aprovados e uma falha pertence ao commit `24b366e`; os totais de
testes de revisões distintas não são comparados como pares.

## Limites e pendências declarados

- A #181 segue aberta na consulta de 22/10: ainda não há entrega no
  repositório de diferenças relativas por métrica nem de concordância de
  classes nos pares. O artigo registra essa ausência; não calcula valores
  com base em uma publicação não preservada nesta tarefa nem preenche
  esses campos por inferência. Quando a comparação for entregue, seus
  resultados deverão ser incorporados à narrativa.
- Não há evidência de nova execução externa após o PR #256, nem de
  correção dos problemas no repositório parceiro. As verificações locais
  usam fixtures para coleta e passagem do tempo.
- As #251–254 estão fechadas. A #182 segue aberta por vínculo ao Project
  não verificado, conforme registro de falta de permissão em seu relatório.
- Não houve novas consultas de coleta, recálculo da base, alteração de
  CSVs, rótulos, análises, hipóteses ou bibliografia.
- Revisão final de extensão e paginação do artigo permanece na #186.

## Verificação

Foram conferidos o CSV parceiro preservado (30 linhas e 37 colunas), o
funil, os relatórios locais e o corpo/estado das issues #180–182 e
#251–254 na API do GitHub. As referências cruzadas do novo texto apontam
para labels presentes nas fontes incorporadas por `main.tex`.

A compilação integral de `main.tex` pelo compilador nativo do editor
terminou com sucesso, incluindo a nova narrativa. `git diff --check`
passou após normalizar o fim do README. Não foi reexecutada a suíte Python:
esta alteração modifica somente o relato e sua documentação, sem código
de produção ou resultados analíticos. A compilação não substitui a revisão
final de paginação da #186.
