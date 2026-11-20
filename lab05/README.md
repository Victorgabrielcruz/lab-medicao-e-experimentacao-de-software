# Lab05 — Experimento em software real: SQLite

Experimento controlado sobre o desempenho do **SQLite** em execução local, comparando
dois fatores de configuração em um desenho fatorial 2 × 2:

| Fator | Níveis |
|---|---|
| `journal_mode` | `DELETE` (padrão) × `WAL` |
| `synchronous` | `FULL` (padrão) × `NORMAL` |

Cada configuração é medida em três cargas (escrita, leitura e mista), com
30 repetições e 3 de aquecimento descartadas. Os parâmetros ficam em
[`experimento/config.py`](experimento/config.py).

## Estrutura

```
lab05/
├── executar.py          # ponto de entrada do experimento
├── app.py               # dashboard Streamlit com o roteiro do documento final
├── experimento/
│   ├── config.py        # fatores, cargas, repetições e semente
│   ├── ambiente.py      # registro de versões, hardware e disco
│   └── benchmark.py     # plano aleatório, cargas e medições em CSV
├── tests/
└── data/                # saídas locais (ambiente.json, bancos, CSVs)
```

## Como executar

Requer Python 3.12.

```bash
cd lab05
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python executar.py
```

O comando executa as 396 execuções do plano (360 medidas e 36 aquecimentos),
registra o ambiente e os parâmetros em `data/ambiente.json` e salva as 360 medições
em `data/resultados.csv`. O benchmark usa apenas a biblioteca padrão do Python;
as dependências de `requirements.txt` também atendem à análise e ao dashboard.

Para uma coleta curta, mantendo as cargas do protocolo:

```bash
.venv/Scripts/python executar.py --diretorio data/piloto --repeticoes 3 --aquecimentos 1
```

`--semente` permite alterar a semente (padrão: 42). Uma coleta existente nunca é
sobrescrita: use outro `--diretorio` para repetir, inclusive se a anterior falhou.
O piloto formal e a coleta completa devem seguir o plano da S01-06 (#304).

O [piloto da S01-06 e o plano de coleta](docs/04-piloto-plano-coleta.md) registram
36 medições em `data/piloto/`, a variabilidade e a estimativa de duração da coleta
completa. Para reproduzir o resumo sem executar novamente o benchmark:

```bash
python resumir_piloto.py --diretorio data/piloto
```

### Como a medição funciona

- Em cada rodada, todas as 12 combinações de configuração e carga são embaralhadas.
  Todas as rodadas de aquecimento acontecem antes das rodadas medidas; seus tempos
  não entram no CSV.
- Cada execução cria um banco exclusivo com as mesmas 10.000 linhas e payload ASCII
  de 256 bytes. O banco e seus arquivos auxiliares são removidos após fechar a conexão.
- A carga de escrita faz um `INSERT` e um `commit` por operação; a leitura faz
  `SELECT` por chave primária e consome o resultado. A carga mista tem exatamente
  1.400 leituras e 600 escritas, em ordem aleatória. As leituras consultam as chaves
  iniciais, sempre existentes.
- A mesma carga/repetição usa a mesma sequência de operações em todas as configurações.
  A sequência é preparada antes da cronometragem.
- `time.perf_counter` mede somente a execução das operações e seus commits.
  Criação/população do banco, aplicação e verificação dos PRAGMAs, abertura/fechamento
  da conexão e gravação do CSV ficam fora da medição. Checkpoints automáticos do WAL
  que ocorrerem durante a carga entram no tempo; o checkpoint ao fechar a conexão fica
  fora. Portanto, o resultado representa a janela das operações, não todo o ciclo de
  vida do banco.
- O cache do sistema operacional não é limpo: banco novo não significa cache frio.
  A execução é sequencial, com uma conexão por vez, sem teste de concorrência ou falhas
  de energia. Essas condições devem acompanhar a interpretação dos resultados.

### Saída CSV

Cada linha de `resultados.csv` corresponde a uma repetição **medida**:

| Colunas | Significado |
|---|---|
| `configuracao`, `journal_mode`, `synchronous`, `carga` | Tratamento e carga executados |
| `repeticao` | Índice de 1 até o número de repetições, por configuração/carga |
| `ordem_execucao` | Posição real no plano, incluindo os aquecimentos descartados |
| `n_operacoes`, `n_leituras`, `n_escritas` | Quantidades efetivamente executadas |
| `tempo_total_s` | M1: tempo total em segundos |
| `vazao_ops_s` | M2: operações divididas pelo tempo total |
| `semente`, `semente_carga` | Sementes da coleta e da sequência de operações |
| `linhas_iniciais`, `tamanho_payload` | Estado inicial e tamanho do campo de texto em bytes |
| Campos do ambiente | Data/hora de início da coleta, versões, sistema, máquina, processador, CPUs, disco, diretório do banco e executável Python |

A razão de vazão (M3) será calculada na análise, usando as medianas dos grupos.
O CSV é gravado incrementalmente; em caso de interrupção ele pode estar incompleto.
A validação de completude antes de analisar/versionar os dados é parte da S02-02 (#307).

## Dashboard e plano de análise — S01-07 (#305)

Com as dependências instaladas, na raiz do repositório:

```bash
python -m streamlit run lab05/app.py
```

Ou, dentro de `lab05/`, use `.venv/bin/python -m streamlit run app.py`
(Windows: `.venv/Scripts/python -m streamlit run app.py`). O dashboard reaproveita
a estrutura narrativa e o AppTest do Lab04, com as seções **software, pergunta,
método, resultados, ameaças e impacto**, nessa ordem.

Lê `data/piloto/resultados.csv`, valida com os metadados do piloto e recalcula
o resumo sem executar o benchmark nem alterar os dados. As 36 medições são
exploratórias: a inferência e as conclusões dependem da coleta completa.

O [plano de análise](docs/05-plano-analise.md) define descritiva, testes por métrica,
pareamento por rodada, correção de Holm, tamanho do efeito e intervalos de confiança.
O AppTest verifica a ordem das seções, leitura do CSV e comportamento sem o piloto.

## Testes

```bash
.venv/Scripts/python -m pytest
```

## Ética

Execução apenas local: nenhum sistema de terceiros é acessado e nenhum dado pessoal é coletado.
