# Livro de códigos da amostra-ouro (#155)

Regras comuns aos rotuladores A (#156), B (#157) e C (#158). O Kappa de
Fleiss (#159) compara as três planilhas, então todos usam exatamente os
valores abaixo, em minúsculas e sem acento.

Preencha somente as colunas de julgamento e `observacoes`. Se a evidência
não bastar para decidir, deixe a célula vazia e explique em `observacoes`;
célula vazia não equivale a `nao`. O consenso (#160) resolve os casos pendentes.

## `rotulador_<X>_repositorios.csv`

### `tipo_projeto`

Função principal do repositório, segundo o README e a documentação.

| Valor | Quando usar | Exemplos |
|---|---|---|
| `biblioteca` | Código importado por outros programas, que não controla o fluxo da aplicação. | cliente HTTP, parser, SDK, componentes de UI |
| `framework` | Estrutura que chama o código do usuário e define a arquitetura da aplicação. | framework web, motor de jogo, framework de testes |
| `aplicacao` | Programa usado diretamente por usuários finais, com interface web, desktop ou mobile. | editor, navegador, app de notas, painel self-hosted |
| `ferramenta_dev` | Ferramenta usada por desenvolvedores na construção, no teste ou na manutenção de software, em geral via CLI ou plugin. | compilador, linter, bundler, gerenciador de pacotes, extensão de IDE |
| `infraestrutura` | Software executado como serviço ou plataforma em que outros sistemas rodam. | banco de dados, servidor, proxy, orquestrador, observabilidade |
| `outro` | Nenhuma das anteriores: coleção de dados, documentação, configuração, modelo. | listas, datasets, dotfiles |

Em casos híbridos, escolha a função que o README apresenta primeiro e
registre a outra em `observacoes`.

### `releases_sao_entregas_reais`

- `sim`: as releases distribuem versões do software estudado (binários,
  pacotes ou código versionado para uso).
- `nao`: as releases são marcações administrativas, snapshots automáticos
  sem mudança de software ou publicação de conteúdo que não é software.

## `rotulador_<X>_releases.csv`

### `corretiva`

- `sim`: as notas da release ou o compare mostram **pelo menos uma correção
  de defeito**, mesmo junto de novas funcionalidades. Contam correções de
  bug, regressão, falha de segurança, crash, revert de mudança defeituosa
  e hotfix.
- `nao`: nenhuma correção de defeito identificada. Atualização de
  dependências, documentação, refatoração, desempenho sem defeito relatado
  e novas funcionalidades não contam.

Não decida só pelo número de versão ou por palavra-chave: confirme no texto
ou no compare que algo defeituoso foi corrigido. `compare_url` vazio indica a
primeira release elegível do repositório; julgue pelas notas.

## Independência

Cada integrante preenche somente a sua planilha, sem consultar as dos
demais nem os resultados da heurística da #161. Ferramentas de apoio à
leitura, como resumos das notas, devem ser declaradas em `observacoes` ou na
metodologia (#165).
