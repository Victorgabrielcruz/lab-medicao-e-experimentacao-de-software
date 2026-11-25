# Validação e versionamento dos dados — S02-02 (#307)

## Conjunto final e rastreabilidade

Validação realizada em **25/11/2026**, na branch `feat/validacao-dados-307`, após
atualizar a `main` para `9d1bc31fc2bc89e4fe67c298ad00d005ce2882c8` (merge da #324).
Foram seguidos o [plano do piloto](04-piloto-plano-coleta.md), o
[plano de análise](05-plano-analise.md) e o [registro da coleta completa](06-coleta-completa.md).
Não houve nova coleta, mistura com o piloto, imputação, arredondamento dos dados
originais ou remoção de observações.

O conjunto final é o próprio [`resultados.csv`](../data/coleta-completa-01/resultados.csv)
da #306: **360 medições, 28 colunas**, sem aquecimentos. Os cinco arquivos originais
continuam byte a byte iguais. O SHA-256 do CSV é:

```text
595eba4d16b1c8fbe4550a2d2f2d545c13932b49d10e6e3ff93f8b5a9214eacc
```

O [`manifesto.json`](../data/coleta-completa-01/validacao/manifesto.json) identifica o
CSV, este dicionário, os hashes das cinco entradas e os hashes dos três relatórios.
O Git versiona juntos os dados, metadados, manifesto, código e documentação; não
há uma segunda cópia supostamente “limpa”. As regras de `.gitattributes` preservam
os bytes usados nos hashes em novos checkouts. Os hashes detectam divergências em
relação aos registros versionados; não são uma certificação externa da coleta.

## Como reproduzir

A partir de `lab05/`, em Python 3.12 (biblioteca padrão, sem SQLite em execução):

```powershell
python validar_dados.py --diretorio data/coleta-completa-01
```

Foi usado `data/.venv-benchmark/Scripts/python.exe` (CPython 3.12.14).
`--saida` permite gerar os relatórios em outra pasta; por padrão é `validacao/`
dentro da coleta. O programa não sobrescreve as entradas. Os relatórios são
recalculados, inclusive após reprovação, evitando deixar um manifesto antigo como
aprovado. Código de saída: **0** aprovado estruturalmente, **1** reprovado, **2** erro
de argumentos ou de publicação. Não depende da CPU, disco ou versões atuais da
máquina: confere o ambiente registrado no momento da coleta.

| Artefato em `data/coleta-completa-01/validacao/` | Conteúdo |
|---|---|
| `validacao.json` | Status, escopo, erros com linha/campo, contagens, hashes e diagnósticos |
| `outliers.csv` | Uma linha por observação/métrica sinalizada, com quartis, limites e ação `preservar` |
| `diagnostico-temporal.csv` | 24 séries de métricas e 9 séries de diferenças pareadas |
| `manifesto.json` | Referência ao conjunto final e hashes de entradas e relatórios |

## Verificações e resultado

**Aprovação estrutural: 360 medições, zero erros.** Foram conferidos:

- os hashes originais de CSV, ambiente, execução e lançador contra `conferencia.json`
  e o hash do lançador contra `execucao.json`;
- execução concluída com código 0, datas com fuso, ambiente dentro da janela de
  execução e duração de parede coerente (tolerância operacional de 2 s);
- cabeçalho com exatamente as 28 colunas, sem duplicação, campos obrigatórios
  preenchidos, inteiros decimais exatos e números reais finitos;
- exatamente 30 repetições únicas em cada uma das 12 combinações, sem duplicatas
  ou lacunas; ordem 37–396, sem as 36 execuções de aquecimento;
- reconstrução do plano sorteado com semente 42: tratamentos, cargas, rodadas,
  sementes de carga, contagens de operações, linhas iniciais e payload;
- pareamento entre configurações por carga/repetição/semente, sem converter as
  sementes de 64 bits para `float`;
- M1 e M2 positivos, M2 = operações/M1 (tolerância relativa `1e-12` para ponto
  flutuante), CPU/disco em domínio válido e campos de ambiente iguais ao JSON.

O protocolo resulta em **1.560.000 operações medidas**: 1.368.000 leituras e
192.000 escritas. Uma observação é uma execução da carga; operações SQL individuais
não são réplicas independentes. A conferência não compara hashes dos fontes atuais
com os fontes históricos da #306, que podem evoluir; estes permanecem registrados
em `execucao.json`.

## Outliers preservados

Regra exploratória aplicada separadamente a M1 e M2 em cada configuração/carga:
valores estritamente fora de `[Q1 − 1,5 × IQR; Q3 + 1,5 × IQR]`, com quartis
inclusivos (`statistics.quantiles(..., method="inclusive")`). Quando IQR = 0,
valores diferentes do intervalo pontual também são sinalizados. Não há remoção,
winsorização ou substituição. M1 e M2 são transformações inversas, e seus limites
de outlier podem sinalizar conjuntos diferentes.

Foram obtidas **43 sinalizações de métrica em 23 observações distintas**:

| Configuração | Escrita | Leitura | Mista | Total de observações distintas |
|---|---:|---:|---:|---:|
| DELETE-FULL | 0 | 0 | 0 | 0 |
| DELETE-NORMAL | 1 | 1 | 3 | 5 |
| WAL-FULL | 4 | 2 | 3 | 9 |
| WAL-NORMAL | 4 | 1 | 4 | 9 |
| Total | 9 | 4 | 10 | 23 |

Essas marcações são diagnósticos de distribuição, não evidência automática de erro
de medição. **Todas as 360 observações seguem no conjunto final.**

## Diagnóstico temporal e limites

O CSV temporal apresenta, em cada série de 30 pontos, Spearman contra a ordem,
correlação de Pearson entre valores consecutivos (lag 1), medianas das primeiras
e últimas 15 observações e a diferença entre essas medianas. Empates recebem
postos médios; correlações de séries constantes ficam vazias (`null` no JSON).
São 24 séries de M1/M2 por grupo, ordenadas por `ordem_execucao`, e nove diferenças
pareadas de M2 (tratamento − referência), ordenadas por rodada, para H1–H3 nas três cargas.

Por exemplo, a diferença pareada de H1 na leitura apresenta Spearman de aproximadamente
**0,394** contra a rodada; H2 na escrita apresenta aproximadamente **−0,332**.
Isso fornece pontos para inspeção temporal, sem valores-p ou limiar automático
de aprovação. Não se conclui que houve ou não dependência temporal relevante a
partir dessas correlações isoladas.

**A independência dos sinais entre rodadas ainda precisa ser auditada na #309**,
com inspeção das séries, diferenças e sinais, seguindo o plano. Esta aprovação
libera a análise exploratória; não libera conclusões confirmatórias automaticamente.
Não foram executados testes de hipótese, correção de Holm, bootstrap ou conclusões
de superioridade nesta entrega. Ruído do SO, cache e demais condições da #306
continuam sendo limitações do experimento.

## Dicionário do CSV final

Formato: UTF-8, cabeçalho, separador vírgula, aspas conforme CSV, ponto decimal,
sem índice externo. Todos os campos são obrigatórios. As sementes devem ser lidas
como inteiros exatos ou texto decimal, nunca como `float` ou número de planilha.
Identificador da observação: `(coleta, configuracao, carga, repeticao)`; a coleta
vem do diretório/manifesto. Chave de pareamento: `(coleta, carga, repeticao,
semente_carga)`, com o mesmo ambiente.

| Coluna | Tipo e unidade | Significado e domínio nesta coleta |
|---|---|---|
| `ordem_execucao` | inteiro | Posição no plano completo; 37–396; aquecimentos 1–36 ausentes |
| `configuracao` | texto nominal | DELETE-FULL, DELETE-NORMAL, WAL-FULL ou WAL-NORMAL |
| `journal_mode` | texto nominal | DELETE ou WAL, coerente com a configuração |
| `synchronous` | texto nominal | FULL ou NORMAL, coerente com a configuração |
| `carga` | texto nominal | escrita, leitura ou mista |
| `repeticao` | inteiro | Rodada medida de 1 a 30 por configuração/carga |
| `n_operacoes` | inteiro, operações | escrita: 1.000; leitura: 10.000; mista: 2.000 |
| `n_leituras` | inteiro, operações | escrita: 0; leitura: 10.000; mista: 1.400 |
| `n_escritas` | inteiro, operações | escrita: 1.000; leitura: 0; mista: 600; um commit por escrita |
| `tempo_total_s` | real, segundos | M1, duração cronometrada positiva e finita das operações e commits |
| `vazao_ops_s` | real, operações/s | M2 = `n_operacoes / tempo_total_s`, positiva e finita |
| `semente_carga` | inteiro exato de 64 bits | Sequência de operações; comum às quatro configurações da mesma carga/rodada |
| `semente` | inteiro | Semente do plano: 42 |
| `linhas_iniciais` | inteiro, linhas | População inicial de cada banco novo: 10.000 |
| `tamanho_payload` | inteiro, bytes | Texto ASCII por registro: 256 bytes |
| `data_hora_utc` | texto ISO 8601 com fuso | Início registrado da coleta; repetido nas linhas, não é horário individual da medição |
| `sqlite_version` | texto | Versão efetiva do SQLite registrada: 3.53.1 |
| `python_version` | texto | Versão do Python registrada: 3.12.14 |
| `python_implementacao` | texto | Implementação: CPython |
| `sistema` | texto | Sistema operacional: Windows |
| `sistema_versao` | texto | Versão do sistema: 10.0.26200 |
| `maquina` | texto | Arquitetura: AMD64 |
| `processador` | texto | Identificação técnica devolvida pelo sistema; copiada do ambiente |
| `n_cpus` | inteiro, CPUs lógicas | Quantidade registrada: 12 |
| `disco_total_gb` | real, GiB | Capacidade da unidade do diretório de dados; bytes / 1024³, apesar do sufixo `_gb` |
| `disco_livre_gb` | real, GiB | Espaço livre no início; entre zero e capacidade total, não monitoramento por execução |
| `diretorio_banco` | texto, caminho | Diretório local dos bancos temporários da coleta |
| `executavel_python` | texto, caminho | Executável usado para a coleta |

M3 é derivada da razão entre medianas dos grupos e não integra este CSV bruto.
Os caminhos e identificações de máquina já publicados na #306 são metadados
técnicos de rastreabilidade. As cargas usam dados sintéticos locais.

## Testes da entrega

```powershell
python -m pytest -q tests/test_validacao.py tests/test_benchmark.py tests/test_config.py tests/test_ambiente.py tests/test_piloto.py
```

Foram executados **67 testes, todos aprovados**, com pytest 9.2.0. Cobrem a coleta
real, hashes e preservação byte a byte, repetibilidade dos relatórios, dados ausentes,
duplicação, aquecimento, reordenação, schema inválido, números não finitos ou fora
do domínio, sementes exatas, fatores, contagens, ambiente e metadados adulterados,
falha após publicação anterior, proteção das entradas, quartis inclusivos, outliers
com IQR zero, direção das diferenças pareadas e diagnósticos com valores conhecidos.
Os testes não executam a coleta completa.
Os testes do dashboard Streamlit não integram essa execução focada.
