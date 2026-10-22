# Avaliação da heurística corretiva — S02-12 (#162)

Implementação: [avaliacao_heuristica.py](../pipeline/avaliacao_heuristica.py).
Referência: [consenso da #160](../validacao/amostra-ouro/PROTOCOLO-CONSENSO.md),
com 300 pares oficiais, 249 `sim` e 51 `nao`. O sorteio histórico sobre os
primeiros 255 elegíveis permanece preservado após a seleção de 500.

## Unidade e métricas

A unidade é a **release corretiva**, identificada por `(repo_id, release_id)`.
Compara-se o campo `corretiva` da #161 com o consenso, sem comparar `falhou`
ou o valor agregado de CFR(b). A classe positiva é `sim`. A censura dos
últimos sete dias aplica-se à falha da release anterior na CFR(b); não exclui
da avaliação uma corretiva rotulada nesse período.

As linhas da matriz são o consenso e as colunas, a previsão, na ordem
`[nao, sim]`: `[[VN, FP], [FN, VP]]`. Os escores globais ponderam cada
release igualmente, sem fazer média entre repositórios:

- Precisão: `VP / (VP + FP)`.
- Recall: `VP / (VP + FN)`.
- F1: `2 * VP / (2 * VP + FP + FN)`.

Usam-se as funções oficiais do scikit-learn
[precision_recall_fscore_support](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)
e [confusion_matrix](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html).
O cálculo usa `labels=[False, True]`, `average=None`, `zero_division=0`;
após o cálculo, denominadores nulos são representados por `null` no JSON e
“não estimável” no Markdown, conforme o protocolo da #165. Isso preserva
F1=0 quando há FP/FN mesmo que precisão ou recall sejam não estimáveis.
Sem pares avaliáveis, a matriz tem contagens zero e os três escores são nulos.

## Entradas e integridade

Em `--pasta` (padrão `validacao/amostra-ouro/`):

- `amostra_ouro.json`: autoridade dos IDs, tags, nomes e datas da janela.
- `consenso_releases.csv`: contrato da #160 com `repo_id`, `full_name`,
  `release_id`, `tag_name`, `corretiva` e `origem_corretiva`.

O comando exige exatamente uma fonte de previsões:

1. `--previsoes`: JSON da #161 com `janela`, `variante=b`,
   `versao_heuristica` e `repositorios`. Cada repositório precisa de `id`,
   `full_name` e `releases`; cada detalhe traz `release_id`, `tag_name`,
   `published_at` e `corretiva` estritamente `true`, `false` ou `null`.
   Um resumo sem os detalhes é recusado. A versão é registrada, permitindo
   comparar novas versões na #163 sem alterar o avaliador.
2. `--releases` e, quando disponível, `--compare`: arquivos locais dos
   coletores, com o contrato do pipeline. Reaplica-se a v1 da #161 à sequência
   **completa** de releases de cada projeto antes de selecionar as cinco
   sorteadas. Uma base não sorteada pode ser a predecessora correta; calcular
   o patch usando só as cinco releases produziria previsões diferentes.
   O compare é lido por repositório no formato streaming do projeto.

As entradas precisam ter a mesma janela. IDs repetidos, rótulos inválidos,
tags/datas/nomes divergentes e itens do consenso fora do sorteio são
recusados. Repositórios e releases adicionais nas previsões são permitidos,
pois a entrada pode abranger os 500; somente os pares oficiais são avaliados.
A coluna `origem_corretiva` evita usar acidentalmente a planilha de um único
rotulador como consenso. Ela não comprova, por si, a independência humana:
os limites do procedimento de rotulagem continuam válidos.

Linha de consenso omitida ou `pendente` e previsão ausente ou indeterminada
ficam identificadas fora da matriz. Nenhuma ausência vira `nao`. As
contagens de motivos podem se sobrepor quando faltam ambos os lados.
O relatório registra cobertura, suportes avaliados e contagens do consenso
total, para tornar visível o viés de cobertura.

## Execução com os dados finais

Na pasta `Lab03`:

```bash
python -m pip install -r requirements.txt
python -m pipeline.avaliacao_heuristica \
  --previsoes data/processed/amostra-final-500/cfr_b.json \
  --saida validacao/avaliacao-heuristica/final-500 --exigir-completa
```

Se o JSON processado for um resumo, use os brutos finais:

```bash
python -m pipeline.avaliacao_heuristica \
  --releases data/raw/amostra-final-500/releases.json \
  --compare data/raw/amostra-final-500/compare.json \
  --saida validacao/avaliacao-heuristica/final-500 --exigir-completa
```

Sem `--compare`, somente evidências suficientes das releases podem produzir
uma decisão conhecida. Um compare explicitamente solicitado mas inexistente
gera erro, em vez de ser ignorado. Nenhum comando acessa a API ou usa tokens.

Cada execução gera:

| Arquivo | Conteúdo |
|---|---|
| `avaliacao.json` | Escores, matriz, suportes, denominadores, cobertura, pares, versão e SHA-256 das entradas. |
| `avaliacao.md` | Resultado legível, orientação da matriz e limites de interpretação. |
| `pares.csv` | Um registro por par sorteado, com consenso, previsão, VP/FP/FN/VN ou razões de exclusão. |
| `previsoes_amostra.json` | Previsões utilizadas, restritas à amostra, reutilizáveis como entrada. |
| `pendencias.csv` | Somente os pares excluídos, com IDs, URL oficial de compare, diagnóstico da evidência faltante e ação recomendada. |

O avaliador v2 resume os sinais de commits no recorte de previsões, mantendo
contagem e até cinco exemplos. A classificação já presente no arquivo de
entrada é preservada, e o hash desse arquivo permite recuperar os sinais
integrais. O recorte resumido pode ser reavaliado sem mudar os escores.

O diagnóstico de pendências não altera rótulos. Ele distingue consenso ou
previsão ausentes, falta de compare completo e falta da predecessora
histórica para o sinal SemVer. Uma primeira release da janela pode ter
predecessora anterior à janela, mesmo com `compare_url` vazio no sorteio.
Se a predecessora não existir, a indeterminação da v1 é legítima; ela não
deve ser resolvida inventando uma base ou preenchendo `nao`.

As entradas são verificadas por hash antes e depois da leitura. Os relatórios
não incluem horário de geração e são determinísticos para os mesmos arquivos,
caminhos e versões de bibliotecas. As escritas substituem cada arquivo
atomicamente, e a saída não pode sobrescrever uma entrada. A ordenação dos
pares segue o manifesto; junções não dependem da ordem das previsões nem da tag.

Códigos de saída: `0` para execução válida (pode ser parcial), `2` para
entrada/execução inválida e `3` para relatório parcial quando se usa
`--exigir-completa`. O código 0 não significa F1 satisfatório. O limiar
0,70 é informado separadamente; refinamento pertence à #163, sem alterar os
rótulos nem ajustar automaticamente a heurística nesta tarefa.

## Reprodução do snapshot histórico disponível

Os detalhes da execução final referidos no
[CSV final](../entregas/s02-03-dataset-500-final/README.md) permanecem na
máquina do responsável pela coleta. O CSV agregado não permite reconstruir
a matriz por release. Para permitir uma execução real com os dados
versionados, foi implementado [avaliacao_snapshot.py](../pipeline/avaliacao_snapshot.py):

```bash
python -m pipeline.avaliacao_snapshot \
  --pacote entregas/dados-brutos-500 \
  --saida validacao/avaliacao-heuristica/reproducao-snapshot
```

Esse comando verifica o hash e o tamanho das 20 partes do pacote
`snapshot-500` e dos 73 checkpoints selecionados (60 de releases e 13 de
compare). Não restaura os 35 GiB do cache, não lê julgamentos A/B/C e não
usa notas de release como entrada da heurística. Requer espaço temporário
para aproximadamente 818 MB comprimidos e memória para um checkpoint por vez.
Somente os hashes dos membros utilizados são conferidos; isso não é uma
nova auditoria integral de todos os membros do pacote/cache.

O contexto do compare precisa corresponder ao hash da sequência original de
releases, janela, API e versão do coletor. Compare antigo/incompatível não é
aproveitado. A sequência completa é preservada para a classificação; nos
commits só são mantidos SHA e mensagem, os campos usados pela #161.
O arquivo adicional `entrada_snapshot.json` registra os hashes do manifesto,
partes, checkpoints e códigos da heurística e da recuperação, junto às
previsões calculadas. Para manter os artefatos revisáveis, guarda a contagem
e até cinco exemplos de commits corretivos por release; essa redução ocorre
**depois** da classificação, que examinou todas as mensagens disponíveis.
Os checkpoints originais permitem reproduzir os demais sinais.

Para gerar um `cfr_b.json` no contrato completo da #161, com agregados de
CFR e todas as releases dos 60 projetos, antes do recorte das cinco sorteadas:

```bash
python -m pipeline.avaliacao_snapshot \
  --cfr-b data/processed/amostra-ouro-snapshot-500/cfr_b.json
```

Esse arquivo também deriva do snapshot parcial e preserva as previsões
indeterminadas. Ele não representa a execução final dos 500 repositórios.
Pode ser usado diretamente em `avaliacao_heuristica --previsoes`.
A [cópia versionada do cfr_b.json](../validacao/avaliacao-heuristica/snapshot-500/cfr_b.json)
contém 60 repositórios e 4.505 releases estáveis de toda a janela, com os
agregados de CFR(b) e os detalhes por release. Para reproduzi-la diretamente
nesse local, use o mesmo comando com
`--cfr-b validacao/avaliacao-heuristica/snapshot-500/cfr_b.json`.

O relatório principal versionado é calculado **diretamente dessa cópia de
`cfr_b.json`**, com seu SHA-256 registrado em `avaliacao.json`. Para
reproduzir os cinco artefatos do relatório sem reabrir os pacotes:

```bash
python -m pipeline.avaliacao_heuristica \
  --previsoes validacao/avaliacao-heuristica/snapshot-500/cfr_b.json \
  --saida validacao/avaliacao-heuristica/snapshot-500 --exigir-completa
```

O retorno 3 é esperado enquanto houver pares indeterminados; os relatórios
são gravados normalmente. `entrada_snapshot.json` preserva a extração
intermediária anterior, cuja classificação dos pares sorteados concorda
com a entrada completa. Ela não é a fonte atual do relatório principal.

### Resultado parcial em 21/10/2026

O snapshot foi capturado em 20/10 antes da conclusão dos compares. Para a
amostra-ouro há compare compatível em 13 dos 60 repositórios. A v1 também
reconhece patches sem compare, mas não nega sinais desconhecidos em commits.

| Cobertura | Quantidade |
|---|---:|
| Pares oficiais / com consenso | 300 |
| Previsão conhecida e avaliada | 146 (48,67%) |
| Previsão indeterminada, excluída | 154 |
| Corretivas no subconjunto / no consenso total | 127 / 249 |
| Não corretivas no subconjunto / no consenso total | 19 / 51 |

| Consenso / previsão | nao | sim |
|---|---:|---:|
| nao | 0 (VN) | 19 (FP) |
| sim | 0 (FN) | 127 (VP) |

Precisão: **0,869863**; recall: **1,000000**; F1: **0,930403**.
Os valores completos e os 300 pares estão nos
[artefatos reproduzidos](../validacao/avaliacao-heuristica/snapshot-500/avaliacao.json).

A [lista de pendências](../validacao/avaliacao-heuristica/snapshot-500/pendencias.csv)
identifica 125 pares sem evidência completa dos commits e outros 29 que
também precisam esclarecer a predecessora histórica. Essa lista orienta a
disponibilização dos detalhes finais da #161; não é uma autorização para
substituir as previsões pelos rótulos de consenso.

**Esses escores não concluem a avaliação das 300 releases.** Todas as
previsões conhecidas desse corte foram positivas; 122 corretivas e 32 não
corretivas do consenso ficaram sem previsão. Assim, recall=1 e FN=0 no
subconjunto não demonstram ausência de falsos negativos na amostra inteira.
F1 acima de 0,70 nesse corte também não dispensa a execução final nem valida
a heurística nos pares excluídos. Os arquivos finais deverão gerar outra
pasta, preservando esta evidência histórica. Previsões ainda indeterminadas
mesmo com fontes finais devem continuar registradas, sem imputação negativa.

## Verificação

Os testes cobrem o exemplo do enunciado (VP=30, FP=10, FN=20; P=0,75,
R=0,60, F1=2/3), orientação da matriz, denominadores nulos, ausência de
pares, IDs e metadados divergentes, previsões não booleanas, formatos de
CSV inválidos, versões, exclusões, entradas preservadas e execução sem rede.
Também verificam predecessora não sorteada, inclusão de corretivas censuradas
para CFR(b), hashes/partes corrompidos e compare de contexto antigo no snapshot.

```bash
python -m pytest tests/test_avaliacao_heuristica.py tests/test_avaliacao_snapshot.py -q
python -m pytest --cov=pipeline --cov-report=term-missing --cov-fail-under=80
```

Validação local em 21/10/2026, Python 3.14.3: **992 testes aprovados e
2 ignorados**, com **94,32% de cobertura global**, acima dos 80% exigidos
pela CI. São 65 casos novos; o avaliador tem 100% de cobertura de linhas e
a recuperação do snapshot, 99%. Isso não substitui a execução da CI em
Python 3.11 e 3.13. A dependência adicionada `scikit-learn==1.9.1` declara
compatibilidade com Python >= 3.11.

Nenhum valor do artigo foi atualizado com essa avaliação parcial. Os critérios
de cálculo e registro da matriz estão implementados; a avaliação com a fonte
final permanece dependente da disponibilização dos detalhes por release.
Qualquer commit desta entrega deve referenciar `(#162)`.
