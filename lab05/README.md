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
├── validar_dados.py     # validação e manifesto da coleta completa (#307)
├── analisar_dados.py    # testes, efeitos e IC sem benchmark (#309)
├── app.py               # dashboard Streamlit com o roteiro do documento final
├── experimento/
│   ├── config.py        # fatores, cargas, repetições e semente
│   ├── ambiente.py      # registro de versões, hardware e disco
│   ├── benchmark.py     # plano aleatório, cargas e medições em CSV
│   ├── validacao.py     # integridade, completude e diagnósticos da #307
│   ├── painel.py        # leitura, descritiva e gráficos
│   ├── inferencia.py    # testes pareados, efeitos, IC e auditoria da #309
│   └── impacto.py       # cenários, fontes públicas e premissas da #311
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

A [coleta completa da #306](docs/06-coleta-completa.md) está registrada em
`data/coleta-completa-01/`, com 360 medições, ambiente e conferência operacional.
O piloto permanece separado. Para acompanhar futuras coletas pelo terminal, acrescente
`--progresso` ao comando; as mensagens são emitidas fora da janela cronometrada.

Para validar a coleta completa existente, sem executar novamente o benchmark:

```bash
python validar_dados.py --diretorio data/coleta-completa-01
```

O comando usa somente a biblioteca padrão e gera `validacao/validacao.json`,
`outliers.csv`, `diagnostico-temporal.csv` e `manifesto.json`, preservando as entradas.
Retorna código 0 para aprovação estrutural, 1 para dados reprovados e 2 para erro
de argumentos ou de publicação. `--saida` permite outro diretório para os relatórios.
A [validação e o dicionário das 28 colunas](docs/07-validacao-dicionario-dados.md)
registram 360 medições válidas, 23 observações sinalizadas e nenhuma exclusão.
O manifesto identifica por SHA-256 o CSV final, que é o próprio arquivo bruto
versionado na #306. A aprovação não atesta independência temporal: a auditoria
e o escopo da inferência condicional estão documentados na #309.

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

A razão de vazão (M3) é calculada no dashboard usando as medianas dos grupos;
na coleta completa recebe IC bootstrap pareado e, no piloto, permanece descritiva.
O CSV é gravado incrementalmente; em caso de interrupção ele pode estar incompleto.
A validação de completude antes de analisar/versionar os dados é parte da S02-02 (#307).

## Dashboard — plano (#305), descritiva (#308) e testes e efeitos (#309)

Com Python 3.12 e as dependências instaladas, execute dentro de `lab05/`
para carregar também o tema local do Streamlit:

```bash
cd lab05
.venv/bin/python -m streamlit run app.py
```

No Windows, use `.venv/Scripts/python -m streamlit run app.py`.
Com Streamlit disponível no ambiente ativo, também funciona a partir da raiz:
`python -m streamlit run lab05/app.py` (o tema local requer iniciar dentro de `lab05/`).
O dashboard reaproveita
a estrutura narrativa e o AppTest do Lab04, com as seções **software, pergunta,
método, resultados, ameaças e impacto**, nessa ordem.

Abre por padrão **`data/coleta-completa-01/resultados.csv`**, com 360 medições
e 30 repetições em cada configuração/carga. Confere a publicação aprovada da #307,
revalida as entradas e verifica sua correspondência com os hashes do manifesto,
sem executar o benchmark, republicar relatórios ou alterar dados.
As 23 observações sinalizadas são preservadas integralmente. Falhas de leitura ou
validação aparecem no painel, sem troca automática de conjunto.

O seletor **Conjunto de dados** permite consultar separadamente o **Piloto**
(36 medições, 3 por grupo), que não é somado à coleta completa. A #308 descreve
os dados; a #309 acrescenta testes e efeitos condicionais à independência entre rodadas.
Abrir o painel ou trocar um filtro não inicia nova coleta.

O painel oferece:

- navegação pelas seis seções do documento;
- filtros de carga (escrita, leitura e mista) e métrica (tempo ou vazão);
- boxplots com todos os pontos e quartis coerentes com a validação;
- comparação por mediana e Q1–Q3 (dispersão, não IC), interação e ordem de execução;
- descritiva de M1/M2 com DP amostral, quartis, IQR, extremos e CV;
- M3, ganho percentual e razão de razões exploratória para H1–H3;
- ambiente registrado na coleta, sete categorias, ameaças com mitigações e durabilidade;
- tabela de todas as cargas para as duas métricas, com unidades identificadas;
- downloads do CSV bruto, descritiva filtrada, descritiva completa e plano de análise.
- nove testes dos sinais pareados, valores-p brutos e ajustados por Holm;
- probabilidade de ganho, efeito direcional pareado, diferenças de tempo/vazão e M3 com IC;
- auditoria temporal, séries das diferenças/sinais e relatório completo em JSON.

A [entrega da #308](docs/08-descritiva-graficos.md) registra as medidas usadas,
o resumo dos 12 grupos da coleta completa, a interpretação dos gráficos e seus limites.

O [plano de análise](docs/05-plano-analise.md) define descritiva, testes por métrica,
pareamento por rodada, correção de Holm, tamanho do efeito e intervalos de confiança.
O AppTest verifica a ordem das seções, leitura do CSV sem alteração dos artefatos,
filtros, valores dos gráficos e tabelas, escala logarítmica e falhas do piloto.
Os cálculos de descritiva e M3 têm testes com valores conhecidos.

## Reproduzir testes, efeitos e IC — #309

Dentro de `lab05/`, com as dependências instaladas:

```bash
python analisar_dados.py --saida /tmp/lab05-analise.json
```

No Windows, substitua a saída por um caminho local. Sem `--saida`, imprime JSON em
stdout. O comando recusa sobrescrever arquivos e não altera a coleta ou os relatórios.
O [método e os resultados da #309](docs/09-testes-efeitos.md) documentam a auditoria,
o escopo dos testes e os intervalos. M1 não duplica a família de M2; M3 não tem teste
separado. São nove comparações, bilaterais, com Holm e α = 0,05. Os IC bootstrap
percentis usam 10.000 reamostragens de rodadas pareadas e semente 42; a probabilidade
de ganho usa IC binomial exato. Os IC são marginais, sem ajuste simultâneo.

Na auditoria, ausência de alerta não comprova independência. Sinais constantes são
inconclusivos para esse diagnóstico. Valores-p e IC permanecem **condicionais à
independência entre rodadas**, e alertas suspendem conclusões confirmatórias.
O piloto não recebe testes ou IC inferenciais. A análise informa suas próprias
versões de Python e bibliotecas, separadas das versões registradas na coleta.

## Impacto para usuários e empresas — #311

A seção 6 inclui uma [estimativa de impacto documentada](docs/12-estimativa-impacto.md)
e fontes primárias com acesso em **25/11/2026**: Google (mais de 3 bilhões de
dispositivos Android, informação histórica de 13/05/2025), SQLite (estimativa de
mais de 1 trilhão de bancos ativos) e documentação de durabilidade.

O cenário permite ajustar dispositivos, lotes por dispositivo/dia, carga e
comparação. Os valores iniciais de **10.000 dispositivos e um lote/dia são
hipóteses ilustrativas**. As diferenças pareadas de tempo e seus IC vêm da coleta
completa e da #309. O número público dimensiona a escala; não se aplica o ganho
a toda a população Android ou a todos os bancos SQLite.

Na escrita H1, o cenário inicial corresponde a aproximadamente **2,057 s por
dispositivo/dia** e **5,713 h equivalentes/dia agregadas**. São referências
proporcionais de tempo de execução, sem previsão para uma frota ou conversão em
horas humanas, dinheiro ou energia. O IC local escalado é condicional e não cobre
incerteza de uso/adesão ou heterogeneidade dos dispositivos. O painel explicita
esses limites e exporta JSON com premissas, fontes, datas e hash do CSV.

No piloto ou na ausência de dados completos válidos, a seção mantém as fontes e
os limites sem calcular projeções. Os dados e a análise da #309 não são alterados.

## Testes

```bash
.venv/Scripts/python -m pytest
```

## Ética

Execução apenas local: nenhum sistema de terceiros é acessado e nenhum dado pessoal é coletado.
