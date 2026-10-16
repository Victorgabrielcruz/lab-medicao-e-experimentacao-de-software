# Retomada da coleta até 500 repositórios — #151

Em 16/10/2026, o grupo decidiu retomar a extração encerrada em 255
repositórios (ver [decisao-encerramento-255.md](decisao-encerramento-255.md))
e seguir até a meta original de **500 elegíveis com coleta completa**. Esta
decisão substitui o encerramento em 255 como escopo final. Os artefatos da
população de 255 continuam válidos como registro do estado em 15/10/2026.

## Como a coleta continua

A coleta retoma exatamente de onde parou, sem nova busca de candidatos:

- mesma fonte `candidatos-prioridade-leves.json` do snapshot publicado em
  `entregas/dados-brutos-255/` (SHA-256 `c1cf8800…d94382`, igual ao registrado
  no `progresso.json` da coleta original) e mesma ordem dos 561 candidatos já
  avaliados;
- mesma janela (01/10/2025 inclusive a 01/10/2026 exclusive, UTC), mesmos
  critérios de inclusão (5 releases estáveis e 50 runs válidos, evento push,
  branch padrão) e mesma versão do coletor. O contexto gera o mesmo digest de
  checkpoints (`efc8b161…`), então os 561 checkpoints são reaproveitados sem
  novas chamadas e a coleta segue a partir do candidato 562;
- a regra de [decisoes-coleta-final.md](decisoes-coleta-final.md) volta a valer:
  ao atingir 300 elegíveis, o adiado `grafana/grafana` é liberado na próxima
  vaga, e a coleta continua pela ordem da fonte até 500;
- depois da seleção, o pipeline integrado coleta os compares de **todos** os
  elegíveis. Isso amplia o lead time (RQ02), hoje restrito a 9 repositórios.

Execução, a partir de `Lab03`, com os checkpoints do snapshot copiados para
`data/raw/amostra-final-500/checkpoints/` e uma cópia de `config.yaml` com os
caminhos `raw`/`processed` em `amostra-final-500`:

```powershell
$env:GITHUB_TOKEN = gh auth token
python -m pipeline.integrado --config data/raw/amostra-final-500/config-500.yaml --alvo 500 --max-candidatos 37383 --candidatos data/raw/amostra-final-500/candidatos-prioridade-leves.json
```

A coleta é limitada pela cota da API (5.000 requisições/hora) e deve levar
alguns dias. Interrupções são retomadas pelo mesmo comando.

## Impacto nas tarefas

| Situação | Issues | O que fazer |
|---|---|---|
| Não depende da população | #156, #157, #158, #159, #160, #161, #162, #163 | Seguir normalmente (ver amostra-ouro abaixo). |
| Código vale; números mudam | #152, #153, #154, #167, #168, #169, #170–#175 | Desenvolver sobre o CSV de 255 e reexecutar com o CSV de 500. |
| Texto a atualizar | #164, #165, #166, #176–#179, #183–#186 | Atualizar funil, tamanho da amostra e números quando o CSV de 500 sair. |

### Amostra-ouro (#155)

O sorteio oficial (60 repositórios e 300 releases, `random_state=42`) foi feito
sobre os 255 e já foi rotulado por A, B e C. **Proposta:** manter esse sorteio
e declarar no artigo que ele foi feito sobre os primeiros 255 elegíveis. A
amostra-ouro valida a heurística de release corretiva (CFR b), e um novo sorteio
descartaria a rotulagem das três pessoas. A proposta depende de aceite do grupo.

## Ainda vale

As limitações registradas em 15/10/2026 continuam: a ordem da fonte prioriza
custo observado e não é estritamente por estrelas. Ausências continuam nulas,
sem imputação por zero. Os 255 publicados em `entregas/` não são alterados;
a população de 500 terá entrega própria quando a coleta terminar.
