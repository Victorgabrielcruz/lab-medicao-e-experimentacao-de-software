# Análise interpretativa dos outliers

Atividade extra da Sprint 3. Complementa a discussão da RQ07 e não faz parte das
entregas obrigatórias.

Base: `repos_rq07_consolidated_2026-08-20T222207Z.csv`, 1000 repositórios.
Detecção e tabelas em `outliers_2026-08-20T222207Z.md`, método IQR com cercas de
Tukey.

Foram 533 sinalizações distribuídas em 441 repositórios distintos. A maioria, 354,
aparece em uma única métrica.

## Não existe outlier de idade

Nenhum repositório ficou fora das cercas em `age_years`, e a assimetria é de 0.06,
praticamente simétrica. Todas as outras métricas têm assimetria entre 1.3 e 5.4.

Isso diz algo sobre a RQ01: não existe uma idade que caracterize projeto popular. A
amostra é bem distribuída entre projetos novos e antigos, e a popularidade não se
concentra em nenhuma faixa etária. Foi a única métrica onde a distribuição se
comportou de forma bem comportada.

## Os outliers formam três perfis distintos

Olhando as características de cada grupo, eles não são "os mesmos repositórios
extremos em tudo". São três populações com explicações diferentes.

### Os projetos de grande porte

124 repositórios em pull requests aceitas e 93 em releases, com 39 em comum. A
mediana do grupo é de 17.110 PRs contra 579 no resto da amostra, quase 30 vezes.

O que os separa do resto é justamente serem software de verdade: apenas 1% está sem
linguagem primária, contra 9% na amostra, e 83% usam linguagem do ranking popular,
contra 70%. As cinco linguagens mais frequentes no grupo são TypeScript, Python, Go,
JavaScript e C++.

São os projetos com processo de engenharia estabelecido: fluxo de contribuição
externa, versionamento explícito e cadência de entrega. Não é anomalia de dado, é o
comportamento esperado de projeto grande e maduro.

### Os projetos parados

196 repositórios em dias desde o último push, com mediana de 492 dias sem receber
código. Esse grupo tem marcas próprias:

| característica | grupo | amostra |
|---|---|---|
| arquivados | 12% | quase zero |
| sem linguagem primária | 23% | 9% |
| mediana de releases | 0 | 39 |
| mediana de issues fechadas | 67,7% | 87,5% |

A proporção de repositórios sem linguagem é duas vezes e meia a da amostra, e a
mediana de releases é zero. Ou seja, boa parte do que está parado nunca foi software
mantido: são listas curadas, coletâneas e material de estudo que acumularam estrelas
e depois deixaram de ser atualizados.

Vale notar que apenas 12% estão formalmente arquivados. Os outros 88% continuam
abertos, dando a impressão de projeto ativo para quem olha só a página.

### Os que usam issues para outra coisa

38 repositórios em percentual de issues fechadas, com mediana de 24% contra 88,4% no
resto. Esse grupo não coincide com o dos parados: a mediana de dias sem push é 112,5,
e nenhum está arquivado.

A explicação aparece nos exemplos. São repositórios onde a issue não é um defeito a
ser corrigido, e sim um formulário: submissão de exercício, sugestão de link,
pedido de inclusão em lista. Uma issue assim fica aberta por natureza, e o percentual
baixo não indica projeto mal mantido.

## Popularidade e engenharia se descolam no topo

Este foi o achado mais contraintuitivo. Os 82 repositórios com estrelas fora da cerca
têm **mediana de 4,5 releases, contra 42 no resto da amostra**. Quase dez vezes menos.

| característica | outliers de estrelas | amostra |
|---|---|---|
| mediana de releases | 4,5 | 42 |
| com zero releases | 46% | 28% |
| sem linguagem primária | 13% | 9% |

Entre os dez mais estrelados, nove têm zero releases:

| repositório | estrelas | releases |
|---|---|---|
| codecrafters-io/build-your-own-x | 541.599 | 0 |
| sindresorhus/awesome | 498.218 | 0 |
| public-apis/public-apis | 467.143 | 0 |
| freeCodeCamp/freeCodeCamp | 454.370 | 0 |
| EbookFoundation/free-programming-books | 394.865 | 0 |
| openclaw/openclaw | 386.909 | 234 |
| donnemartin/system-design-primer | 365.103 | 0 |
| nilbuild/developer-roadmap | 365.011 | 1 |
| jwasham/coding-interview-university | 359.347 | 0 |
| vinta/awesome-python | 315.140 | 0 |

O extremo da popularidade não é ocupado por software, e sim por material de
aprendizado e listas curadas. Estrela mede utilidade percebida e alcance, não
atividade de engenharia. Isso é diretamente relevante para a RQ07: usar estrelas como
proxy de maturidade técnica levaria a conclusões erradas.

## Sobreposição entre métricas

Apenas 5 repositórios são outliers em três métricas, e todos na mesma combinação de
PRs aceitas, releases e estrelas: `ggml-org/llama.cpp`, `kubernetes/kubernetes`,
`langchain-ai/langchain`, `n8n-io/n8n` e `vercel/next.js`. São os projetos que
conseguem ser simultaneamente muito populares e muito ativos, o que a seção anterior
mostra ser incomum.

Os pares com mais sobreposição contam a mesma história dos três perfis:

| par | repositórios em comum |
|---|---|
| PRs aceitas e releases | 39 |
| percentual de issues fechadas e dias sem push | 19 |
| PRs aceitas e estrelas | 15 |
| dias sem push e estrelas | 13 |

A segunda linha é coerente: projeto parado acumula issue aberta, porque ninguém está
lá para fechar.

## Anomalias e problemas nos dados

**Releases truncadas.** 23 dos 93 outliers de releases estão no teto de 1000 imposto
pela API. Para esses o valor real é desconhecido e a posição na cauda é um piso. Eles
estão marcados na coluna de observação do CSV. Qualquer estatística de média ou
máximo nessa métrica é subestimada.

**Contagem de issues que não significa o que parece.** `type-challenges/type-challenges`
tem 37.285 issues com 11% fechadas. Não é projeto abandonado nem mal gerido: as issues
são as respostas dos exercícios enviadas pelos participantes. É o caso mais claro de
métrica cujo significado muda conforme o propósito do repositório.

**Contradição que merece conferência manual.** `ziglang/zig` aparece como outlier em
PRs aceitas, com 9.540, e ao mesmo tempo em abandono, com 266 dias sem push, sem estar
arquivado. Histórico alto de contribuição somado a push parado costuma indicar
migração de plataforma ou congelamento do espelho no GitHub. Vale abrir o repositório
e confirmar antes de usar esse caso no relatório final.

**Repositórios que não são software.** `996.ICU` aparece entre os mais estrelados e
entre os parados. Repositórios usados como manifesto ou protesto entram na amostra
pelo critério de estrelas, mas não têm ciclo de desenvolvimento. Não é erro de coleta,
é limitação do critério de amostragem, e vale registrar como ameaça à validade.

## O que isso acrescenta à RQ07

A RQ07 pergunta se linguagens populares recebem mais contribuição, lançam mais
releases e são atualizadas com mais frequência. A análise dos outliers reforça a
direção esperada e ainda mostra o mecanismo por trás dela.

No grupo de grande porte, 83% usam linguagem popular contra 70% na amostra, e apenas
1% está sem linguagem contra 9%. No grupo parado, a proporção sem linguagem sobe para
23%. Ou seja, a presença de uma linguagem primária identificável já separa bastante o
projeto ativo do inativo.

A ressalva importante é que nada disso vale para estrelas. A popularidade medida em
estrelas se comporta de forma independente das métricas de engenharia, e no extremo
chega a se opor a elas. Na discussão da RQ07 vale tratar popularidade e atividade
como dimensões separadas, e não como uma coisa só.

Nenhum outlier foi removido da base. Todos os casos acima seguem no dataset principal.
