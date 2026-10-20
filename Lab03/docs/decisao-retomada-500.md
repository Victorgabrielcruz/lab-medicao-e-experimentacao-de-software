# Retomada da coleta até 500 repositórios — #151

Em 16/10/2026, o grupo decidiu retomar a extração encerrada em 255
repositórios (ver [decisao-encerramento-255.md](decisao-encerramento-255.md))
e seguir até a meta original de **500 elegíveis com coleta completa**. Esta
decisão substitui o encerramento em 255 como escopo final. Os artefatos da
população de 255 continuam válidos como registro do estado em 15/10/2026.

## Como a coleta foi retomada

A retomada foi executada pelo Victor (Victorgabrielcruz), com três sessões
autenticadas em paralelo ([coleta-tres-sessoes.md](coleta-tres-sessoes.md)),
sem nova busca de candidatos:

- mesma janela (01/10/2025 inclusive a 01/10/2026 exclusive, UTC), mesmos
  critérios de inclusão (5 releases estáveis e 50 runs válidos, evento push,
  branch padrão) e mesma versão do coletor;
- os 561 candidatos já avaliados até 15/10, com seus 255 elegíveis, foram
  preservados como prefixo confirmado, e seus checkpoints foram reaproveitados;
- **mudança de ordem:** os candidatos pendentes passaram a seguir a ordem
  original da busca, sem adiamento por volume de runs. Isso substitui a regra
  de [decisoes-coleta-final.md](decisoes-coleta-final.md), que liberaria os
  adiados só após 300 elegíveis. O `grafana/grafana` voltou à sua posição na
  ordem e foi incluído. A nova fonte é `candidatos-sem-prioridade-tamanho.json`
  (SHA-256 `9e876ef8…756adf`), com os mesmos 37.383 candidatos da busca;
- depois da seleção, o pipeline coleta os compares de **todos** os elegíveis,
  o que amplia o lead time (RQ02), restrito a 9 repositórios na amostra de 255.

## Situação em 20/10/2026

- **Seleção concluída:** 500 elegíveis entre 1.064 candidatos avaliados, que
  são exatamente os 1.064 primeiros da fonte, sem lacunas. Os 255 da primeira
  etapa e os 60 da amostra-ouro estão todos entre os 500. O funil está na
  metodologia do artigo (#164).
- **Compares incompletos:** a execução parou com HTTP 403 (cota esgotada)
  durante os compares, com 51 repositórios processados. As métricas finais dos
  500 ainda não existem.
- O estado capturado está publicado em `entregas/dados-brutos-500/`, com as
  instruções para restaurar e retomar.

Próximos passos, nesta ordem:

1. Retomar os compares até `execucao_completa=true` em
   `processed/amostra-final-500/execucao.json`.
2. Exportar o `dataset-500.csv` com o contrato `lab03-dataset-v1` e validar o
   dicionário de dados.
3. Reexecutar as análises e atualizar os números do artigo.

## Impacto nas tarefas

| Situação | Issues | O que fazer |
|---|---|---|
| Não depende da população | #156, #157, #158, #159, #160, #161, #162, #163 | Seguir normalmente (ver amostra-ouro abaixo). |
| Código vale; números mudam | #152, #153, #154, #167, #168, #169, #170–#175 | Reexecutar com o CSV de 500 depois dos compares. |
| Texto a atualizar | #164, #165, #166, #176–#179, #183–#186 | Funil já atualizado; tamanho da amostra e números quando o CSV de 500 sair. |

### Amostra-ouro (#155)

O sorteio oficial (60 repositórios e 300 releases, `random_state=42`) foi feito
sobre os 255 e já foi rotulado por A, B e C. **Decisão:** o sorteio é mantido,
sem novo sorteio, e o artigo declara que ele foi feito sobre os primeiros 255
elegíveis da coleta. A amostra-ouro valida a heurística de release corretiva
(CFR b), e um novo sorteio descartaria a rotulagem das três pessoas.

## Limitações

A preferência por menor custo de coleta ficou restrita aos 561 primeiros
avaliados; depois deles, a ordem é a da busca. A amostra não é aleatória.
Ausências continuam nulas, sem imputação por zero. Os 255 publicados em
`entregas/` não são alterados.
