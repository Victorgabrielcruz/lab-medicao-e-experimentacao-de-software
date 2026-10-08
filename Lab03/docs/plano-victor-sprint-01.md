# Plano de execução — Victor, Lab03 Sprint 01

Levantamento em 08/10/2026. Este documento é o ponto de partida do agente;
não é uma declaração de conclusão das issues.

## Autorização e limites

- Branch única de trabalho: `feat/tasks-victor-sprint-01`, renomeada da branch da #148.
- Fazer commits por entrega, referenciando as respectivas issues, e push somente nesta branch.
- Não alterar, fazer push ou merge na `main`. Não alterar Projects, criar itens,
  fechar issues, remover labels ou mudar status. Fechar uma issue pode acionar
  automações do Projects, portanto os estados remotos ficam preservados.
- Não publicar tokens, dados reais, cache nem arquivos locais de configuração com credenciais.
- Preservar a coleta já em execução, sua branch, configuração, terminal e cache.
- A conclusão técnica deve ter evidências e pendências explícitas no relatório;
  teste automatizado aprovado não substitui a validação real exigida.

## Diretórios

Worktree de implementação:
`C:/Users/vgppl/.codex/worktrees/lab03-s01-20-recuperacao-148/lab-medicao-e-experimentacao-de-software`.
Usar esse diretório explicitamente nos comandos Git e seu `Lab03` nos comandos Python.

Checkout original e coleta em andamento:
`C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software`.
Sua branch é `feat/lab03-s01-18-workflow-runs-146`; não trocar essa branch.

Python disponível:
`C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/.venv/Scripts/python.exe`.

## Tasks e evidências ainda necessárias

| Task | Disponível agora | Trabalho restante |
|---|---|---|
| #144 — Cache e retomada | Código na base da branch, já integrado | Auditar como dependência; preservar o cache e comprovar retomada quando aplicável. |
| #145 — Rate limit e backoff | Código integrado e testes | Auditar todos os critérios e documentar a evidência disponível; issue ainda aberta. |
| #146 — Workflow runs mensais | Código integrado, piloto real em execução | Aguardar JSON consolidado, validar recorte, paginação, duplicatas e avisos de limite; registrar coletas incompletas. |
| #147 — CFR variante (a) | Código integrado; PR #197 já mesclado | Calcular sobre o consolidado válido e conferir fórmula, identidade dos repositórios e diagnóstico de coleta parcial. |
| #148 — Tempo de recuperação | Implementação e documentação na branch; 340 testes passam, módulo com 100% de cobertura | Commit e push, validação real, episódios por workflow, censura e estatísticas; confrontar resultados com os runs de origem. |
| #149 — Pipeline único com 100 repositórios | Seleção, metadados, runs, CFR e recuperação disponíveis | Integrar em um comando, resolver dependências necessárias, executar até obter 100 repositórios elegíveis e registrar problemas. |
| #150 — Artigo SBC | Introdução e quatro referências existentes | Completar estrutura no template SBC, links do repositório/Projects e projeto no Overleaf; validar compilação. |

Issues: `https://github.com/Victorgabrielcruz/lab-medicao-e-experimentacao-de-software/issues/NUMERO`.
As #146 e #147 permanecem abertas, com `validacao-pendente` e em In Review.
Os PRs #196 e #197 mesclados não comprovam a validação real.

## Dependências e ordem de execução

1. Auditar #145 e publicar a implementação existente da #148, sem mudar os estados remotos.
2. Enquanto a coleta continua, desenvolver a integração #149 e a estrutura do artigo #150.
3. Ao aparecer o consolidado válido da #146, executar e validar CFR e recuperação uma vez.
4. Reaproveitar a coleta validada e ampliar a amostra para a execução real da #149.
5. Atualizar documentação e produzir relatório final com evidências por critério de aceite.

Fluxo: cache/rate limit → seleção + metadados → workflow runs → CFR e recuperação.
Para o mínimo de inclusão e outras métricas do protocolo, entram releases,
funil e os módulos de cálculo correspondentes.

Dependências de outras pessoas identificadas:

- #134: mínimo de cinco releases e cinquenta runs válidos na janela, tabela do funil
  e testes. Existe `origin/feature/S01-06-funil-selecao`, commit `caad3e1`,
  ainda fora da `origin/main` no levantamento. Revisar o contrato do módulo
  antes de incorporá-lo somente na branch de trabalho, preservando autoria.
- #138: coleta de releases paginada, campos e filtro de drafts/janela/cache.
  Não havia módulo de releases na `origin/main` no levantamento.
- #140/#141/#142: commits entre releases e lead time. Consultar disponibilidade
  atual antes de integrar as métricas esperadas pelo protocolo. Não confundir
  a #149 com tarefas adicionais da Sprint 02. Registrar dependências ausentes
  e implementar somente o suporte necessário ao escopo autorizado, com testes.

Buscar atualizações remotas é permitido. Integrações e resolução de conflitos
devem acontecer apenas na branch de trabalho; nunca mesclar PRs de colegas na main.

## Coleta e validação local

Entrada esperada:
`C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json`.

O consolidado é gravado atomicamente no fim. Páginas do cache não substituem
esse arquivo. No levantamento ele ainda não existia. O piloto de 100
**candidatos** deixou 82 repositórios após Actions/metadados; isso não comprova
a execução com 100 repositórios da #149.

Não reiniciar a coleta atual nem limpar cache. Uma pausa longa pode ser rate
limit; ausência de novos arquivos por alguns minutos não comprova falha.
Não iniciar uma segunda coleta volumosa concorrente antes de avaliar a primeira.
Para nova execução, usar configuração e saídas próprias na branch de trabalho,
com caminhos absolutos para reaproveitar o cache sem modificar o config original.

Com cwd no `Lab03` do worktree e o Python acima:

```text
-m pipeline.cfr --config config.yaml --entrada C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json --saida C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/cfr.json
-m pipeline.tempo_recuperacao --config config.yaml --entrada C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/raw/piloto-100/workflow_runs.json --saida C:/Users/vgppl/Documents/lab-medicao-e-experimentacao-de-software/Lab03/data/processed/piloto-100/tempo_recuperacao.json
```

Se uma saída já existir, validar entrada, janela e conteúdo antes de decidir
recalcular. Não repetir cálculos de saídas já validadas para a mesma entrada.

Conferir CFR: `runs_validos = falhas + sucessos`, taxa igual à divisão ou `null`
se não houver runs válidos; verificar mesmos repositórios e flags de incompletude.
Conferir recuperação: primeira falha ao próximo sucesso do mesmo workflow,
ordem temporal, censura no fim da janela e mediana/IQR apenas dos recuperados.
O exemplo de 1h20 está coberto por fixture; confrontar com o exemplo original
se o enunciado completo ficar disponível.

Não ocultar `coleta_incompleta`. Coletas mensais acima do limite da API podem
exigir subdivisão adicional para uma validação completa. Preservar resultados
parciais anteriores e explicar no relatório quais conclusões eles permitem.

## Artigo e template encontrados

O repositório contém `Lab03/artigo/introducao.tex`, `referencias.bib` e `README.md`.
Não contém `sbc-template.sty`, arquivo principal completo nem link de projeto
Overleaf. O usuário informou que ainda não tem projeto criado.

Template encontrado na galeria do Overleaf, atribuído à SBC:
<https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr>.
Registrar proveniência e licença dos arquivos incorporados. Preparar introdução,
metodologia, resultados, discussão/ameaças, conclusão e referências sem inventar
resultados. Criar projeto no Overleaf se houver acesso autenticado disponível.
Se login depender do usuário, concluir tudo que for local e registrar o projeto
online como pendência; não declarar #150 concluída apenas por gerar um `.tex`.

## Testes, publicação e relatório

Criar `.pytest_cache` antes dos testes e usar basetemp dentro do worktree:

```text
-m pytest --basetemp=.pytest_cache/sprint-01 --cov=pipeline --cov-report=term-missing --cov-fail-under=80
```

Baseline validado na branch conjunta: **340 testes, 99,77% geral,
100% em `pipeline.tempo_recuperacao`**. Fazer verificações adicionais proporcionais
às mudanças e ao contrato integrado, incluindo erros, retomada e amostra de 100.

Publicar somente código, testes, documentação e evidências agregadas revisadas.
Os dados processados não estão todos ignorados: revisar o staging explicitamente
para impedir inclusão acidental de dados reais. Não exibir credenciais em logs.

Atualizar `Lab03/docs/relatorio-victor-sprint-01.md` ao final, com:
critérios atendidos/pendentes por issue, mudanças e justificativas, comandos,
testes/cobertura, commits publicados, quantidades reais, coleta incompleta,
links locais das saídas, template/projeto Overleaf e limitações de dependências.
Não substituir evidência ausente por uma declaração de conclusão. O relatório
final será entregue ao usuário; estados no GitHub/Projects ficam preservados.
