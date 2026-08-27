# Respostas das questões de pesquisa

Laboratório 01, disciplina de Laboratório de Experimentação de Software.

Os números abaixo vêm da coleta oficial de 1.000 repositórios
(`data/raw/repos_raw_2026-08-20T222207Z.csv`), processada e validada em
`data/processed/repos_processed_2026-08-20T222207Z.csv` (ver
`docs/validation/rq01-rq02-validation.md`, `docs/validation/rq03-rq04-validation.md`,
`docs/validation/rq05-rq06-validation.md` e `docs/validation/rq07-validation.md`,
todas sem inconsistências críticas). Data de referência da coleta
(`collected_at`): 2026-08-20T22:22:07Z.

As hipóteses foram escritas como previsão para esta base, antes da coleta
oficial acontecer, a partir do indício observado na amostra piloto de 100
repositórios (coletada em 2026-08-13, `data/raw/repos_raw_2026-08-13T225359Z.csv`).
Onde o resultado da base completa diverge do indício da amostra piloto, isso
é discutido explicitamente em cada RQ.

## RQ01. Sistemas populares são maduros/antigos?

Métrica: idade do repositório, a partir da data de criação.

**Hipótese.** A hipótese para esta questão é que sistemas populares tendem a ser maduros/antigos, considerando que projetos que permanecem populares no GitHub podem apresentar maior tempo de desenvolvimento e manutenção.

**O que os dados mostram.**

| Estatística   |   Idade do repositório |
| ------------- | ---------------------: |
| Média         |   **7 anos e 8 meses** |
| Mediana       |   **7 anos e 9 meses** |
| 1º quartil    |   **3 anos e 6 meses** |
| 3º quartil    |  **11 anos e 4 meses** |
| Mínimo        |            **~7 dias** |
| Máximo        | **18 anos e 4 meses** |
| Desvio padrão |  **4 anos e 6 meses** |

A distribuição dos 1.000 repositórios por faixa de idade foi:

| Faixa de idade        | Quantidade | Percentual |
| --------------------- | ---------: | ---------: |
| Até 2 anos            |        139 |       13,9% |
| Mais de 2 até 5 anos  |        185 |       18,5% |
| Mais de 5 até 10 anos |        331 |       33,1% |
| Mais de 10 anos       |        345 |       34,5% |
| **Total**             |  **1.000** |    **100%** |

**Discussão.** Os resultados da base completa confirmam a hipótese de que sistemas populares tendem a ser maduros ou antigos, na mesma direção observada na amostra piloto. A idade média foi de aproximadamente 7 anos e 8 meses e a mediana de 7 anos e 9 meses — muito próximas uma da outra, o que indica uma distribuição menos assimétrica do que a de outras métricas do laboratório (ex.: RQ02, RQ03).

A distribuição por faixas reforça a tendência: 67,6% dos repositórios têm mais de 5 anos, e 34,5% têm mais de 10 anos. Ainda assim, 13,9% têm até 2 anos, incluindo casos com poucos dias de existência, o que confirma que idade não é condição necessária para popularidade — apenas favorece.

Comparado ao indício da amostra piloto (mediana de 8 anos e 3 meses, 40% acima de 10 anos), a base completa mostra uma composição um pouco menos concentrada em projetos muito antigos (34,5% acima de 10 anos) e mais repositórios jovens (13,9% com até 2 anos, contra 18% na piloto, valor semelhante). A diferença é pequena e não muda a conclusão: a hipótese é apoiada, sem que isso signifique que todo sistema popular seja necessariamente antigo.


## RQ02. Sistemas populares recebem muita contribuição externa?

Métrica: total de pull requests aceitas.

**Hipótese.** A hipótese para esta questão é que sistemas populares recebem muita contribuição externa, considerando que projetos com maior popularidade podem atrair uma comunidade maior de desenvolvedores e, consequentemente, mais contribuições por meio de Pull Requests.

**O que os dados mostram.**
| Estatística   | Pull Requests aceitas |
| ------------- | --------------------: |
| Média         |      **4.243,18 PRs** |
| Mediana       |        **768,00 PRs** |
| 1º quartil    |        **175,00 PRs** |
| 3º quartil    |      **3.425,25 PRs** |
| Mínimo        |             **0 PRs** |
| Máximo        |    **103.403 PRs** |
| Desvio padrão |     **10.681,43 PRs** |

A distribuição por quantidade de Pull Requests aceitas foi:

| Pull Requests aceitas | Quantidade | Percentual |
| --------------------- | ---------: | ---------: |
| 0 PRs                 |          20 |        2,0% |
| 1–99 PRs              |         161 |       16,1% |
| 100–999 PRs           |         367 |       36,7% |
| 1.000–9.999 PRs       |         353 |       35,3% |
| 10.000+ PRs           |          99 |        9,9% |
| **Total**             |    **1.000** |   **100%** |

**Discussão.** Os resultados da base completa confirmam a hipótese de que sistemas populares recebem contribuições externas, com magnitude um pouco menor do que a sugerida pela amostra piloto. A mediana foi de 768 Pull Requests aceitas — abaixo da mediana de 1.253,5 observada na piloto —, e 98% dos repositórios possuem pelo menos uma PR aceita.

A distribuição mostra que 72,7% dos repositórios possuem pelo menos 100 Pull Requests aceitas, e 45,2% possuem pelo menos 1.000. Esses percentuais são um pouco menores do que os da amostra piloto (88% e 54%, respectivamente), o que é esperado: a amostra de 1.000 inclui repositórios com menos estrelas que os 100 mais estrelados da coleta piloto, e a mediana de contribuição tende a cair conforme a amostra se distancia do topo do ranking.

A assimetria segue forte: a média (4.243,18 PRs) é mais de 5 vezes a mediana (768 PRs), e o desvio padrão de 10.681,43 PRs confirma isso. Essa assimetria é explicada por poucos repositórios com volume extremamente alto de contribuições — 124 deles foram sinalizados como outliers por IQR (ver `reports/drafts/outliers_2026-08-20T222207Z.md`), com destaque para `firstcontributions/first-contributions` (103.403 PRs), `llvm/llvm-project` (97.396) e `elastic/elasticsearch` (95.655).

A mediana continua sendo a estatística mais representativa do comportamento típico da amostra. Ainda assim, a proporção de repositórios com centenas ou milhares de PRs aceitas (72,7%) sustenta a conclusão de que contribuição externa relevante é a regra, não a exceção, entre os populares.

## RQ03. Sistemas populares lançam releases com frequência?

Métrica: total de releases.

**Hipótese.** A gente esperava que sim. A ideia era que projeto popular costuma ser projeto maduro, com muita gente usando, e que por isso precisaria versionar as entregas de forma explícita. A previsão era achar quase todo mundo com um número alto de releases e pouquíssimos repositórios zerados.

**O que os dados mostram.**

| | valor |
|---|---|
| mediana | 39 |
| média | 126,86 |
| 1º quartil | 0 |
| 3º quartil | 147 |
| com zero releases | 285 de 1.000 |

Por faixa: 285 repositórios com 0 releases, 70 entre 1 e 9, 181 entre 10 e 49, 273 entre 50 e 199, e 191 com 200 ou mais. 23 repositórios bateram no teto de 1.000 releases da API (`releases_no_teto`).

**Discussão.** A hipótese caiu pela metade, na mesma direção observada na amostra piloto, mas com uma proporção de repositórios zerados menor: 28,5% da base completa nunca publicou uma release, contra 41% na piloto. O primeiro quartil continua zero, então pelo menos um quarto da amostra fica de fora do uso de releases, mas a maioria (71,5%) tem ao menos uma.

A leitura de "dois grupos" que apareceu na piloto se confirma: entre os 87 repositórios sem linguagem primária, 85,1% têm zero releases; entre os 913 com linguagem, esse número cai para 23,1%. A explicação é a mesma — repositório sem linguagem primária tende a ser lista curada, coletânea de links ou material de estudo, onde release não faz sentido. Segmentando só por software de fato (com linguagem), a proporção de zerados fica bem menor que a leitura ingênua da amostra inteira sugere.

A ressalva de medição da piloto se confirma na base completa: a API trunca `releases.totalCount` em 1.000, e agora 23 repositórios bateram exatamente nesse valor (contra 4 na amostra de 100), incluindo casos como `langchain-ai/langchain`, `vercel/next.js` e `home-assistant/core`. A média de 126,86 é um piso, não uma estimativa, e o máximo (1.000) não representa o valor real desses repositórios. A mediana (39) é a estatística mais confiável aqui, por estar longe do teto.

## RQ04. Sistemas populares são atualizados com frequência?

Métrica: tempo até a última atualização.

Usamos o `pushedAt`, que é a data do último push de código. O `updatedAt` foi descartado porque ele muda com qualquer alteração de metadado, até quando alguém dá uma estrela, e isso inflaria a atividade. Os dois campos foram coletados, o `updatedAt` ficou só como controle.

**Hipótese.** Esperávamos que sim, mas com ressalva. A previsão era achar a maioria ativa e uma parcela relevante de projeto popular parado, aquele que juntou estrela no passado e foi abandonado. O chute era algo entre 20% e 30% da amostra sem atualização há mais de um ano.

**O que os dados mostram.**

| | dias desde o último push | dias desde o último commit |
|---|---|---|
| mediana | 1 | 3 |
| 3º quartil | 48 | 67,5 |
| máximo | 2.452 | 4.016 |

Por janela de tempo: 423 repositórios receberam push no mesmo dia da coleta, 617 na última semana, 729 no último mês, 791 nos últimos três meses. 115 estão parados há mais de um ano (11,5% da amostra). 27 repositórios da amostra estão arquivados.

A mediana de commits é 2.960 e a mediana do período de desenvolvimento é de aproximadamente 7 anos e 3 meses (2.638,5 dias).

**Discussão.** A hipótese se confirmou, mas de forma mais moderada do que na amostra piloto e mais próxima do chute original. Na piloto, apenas 4% dos repositórios estavam parados há mais de um ano — bem abaixo da faixa de 20%–30% prevista. Na base completa de 1.000, esse número sobe para 11,5%, ainda abaixo da faixa prevista, mas bem mais alinhado a ela. Isso sugere que a amostra piloto (limitada aos repositórios com mais de 10.000 estrelas) capturou uma fatia especialmente ativa, e que, ao descer no ranking de popularidade, aparece mais espaço para projetos que ganharam estrelas no passado e hoje estão com atividade mais espaçada.

Mesmo assim, a maioria segue muito ativa: mediana de 1 dia desde o último push, e 72,9% dos repositórios tiveram push no último mês. A mediana de zero dias observada na piloto não se repete aqui (a mediana da base completa é 1 dia), mas a diferença é pequena e não muda a leitura geral: projeto popular tende a ser mantido com frequência alta.

Juntando com a mediana de aproximadamente 7 anos e 3 meses de período de desenvolvimento (usando `created_at` como proxy do início, ver limitação abaixo), o retrato geral segue o mesmo da piloto: sistema velho e ativo ao mesmo tempo, o que conversa direto com a RQ01 e é retomado na RQ07 (correlação entre estrelas e `days_since_push` de -0,09, indicando leve tendência de repositórios mais populares terem push mais recente).

Uma limitação aqui: o início do período usa a data de criação do repositório e não a do primeiro commit, que a API não entrega numa requisição só. Em repositório que teve o histórico importado de outro sistema de controle de versão, esse período fica menor do que o real. Há também 27 registros com data futura em relação a `collected_at` (`pushed_at`/`last_commit_date` levemente posteriores à referência da coleta), efeito esperado de `collected_at` fixo numa coleta paginada longa (ver `docs/methodology.md`, seções 5 e 13), sem impacto na conclusão.

## RQ05. Sistemas populares são escritos nas linguagens mais populares?

Métrica: linguagem primária de cada repositório.

**Fonte e hipótese.** Foi usado o [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/). A fonte classifica como mais populares TypeScript, Python, JavaScript, Java, C#, PHP, Shell, C++, HCL e Go. A expectativa era que a maior parte dos repositórios mais estrelados usasse uma dessas linguagens, embora listas curadas e materiais de documentação pudessem não ter linguagem primária.

**O que os dados mostram.** Dos 1.000 repositórios, 702 (70,2%) têm uma linguagem do top 10 do Octoverse e 298 (29,8%) não têm (o que inclui os 87 sem linguagem identificada e 211 com linguagem fora dessa lista).

| linguagem primária | repositórios | percentual |
|---|---:|---:|
| Python | 227 | 22,7% |
| TypeScript | 173 | 17,3% |
| JavaScript | 111 | 11,1% |
| Sem linguagem identificada | 87 | 8,7% |
| Go | 77 | 7,7% |
| Rust | 58 | 5,8% |
| Java | 41 | 4,1% |
| C++ | 41 | 4,1% |
| Jupyter Notebook | 24 | 2,4% |
| C | 21 | 2,1% |
| Outras linguagens | 140 | 14,0% |

As linguagens populares mais frequentes são Python, TypeScript e JavaScript: juntas, aparecem em 511 dos 1.000 repositórios (51,1%). A categoria `Sem linguagem identificada` não foi descartada; ela reúne repositórios para os quais a API não informou `primaryLanguage`.

**Discussão.** A hipótese se confirmou para a maior parte da amostra: 70,2% dos repositórios usam linguagens populares conforme a mesma plataforma de onde a amostra foi coletada — um percentual maior que o indício da piloto (66,7%, mas obtido sobre apenas 75 repositórios válidos, devido a uma falha 502 durante aquela coleta). O resultado não significa que popularidade dependa apenas da linguagem: os 87 repositórios sem linguagem e parte dos 140 de "outras linguagens" incluem projetos de documentação, listas e materiais que não são necessariamente aplicações com código executável, como já observado na RQ03 (85,1% desses repositórios sem linguagem também têm zero releases). Essa categoria continua separada na análise, porque removê-la artificialmente infla o percentual de linguagens populares.

## RQ06. Sistemas populares possuem um alto percentual de issues fechadas?

Métrica: razão entre issues fechadas e total de issues.

**Hipótese.** Esperávamos um percentual alto de Issues fechadas. Projetos populares recebem muitos relatos e pedidos, mas também tendem a ter mais mantenedores e colaboradores para classificar, resolver ou encerrar Issues antigas.

**O que os dados mostram.** Dos 1.000 repositórios, 43 não possuem Issues abertas nem fechadas e, portanto, não entram no cálculo do percentual para evitar divisão por zero. Nos 957 repositórios com Issues, os resultados foram:

| | percentual de Issues fechadas |
|---|---:|
| mediana | 87,5% |
| média | 80,2% |
| 1º quartil | 70,4% |
| 3º quartil | 96,8% |
| mínimo | 7,7% |
| máximo | 100,0% |

Por faixa: 22 repositórios estão entre 0% e 24,9%, 86 entre 25% e 49,9%, 171 entre 50% e 74,9%, 642 entre 75% e 99,9%, e 36 chegaram a 100%. Assim, 677 dos 957 repositórios com Issues (70,7%) têm pelo menos 75% de fechamento; 429 (44,8%) têm pelo menos 90%.

**Discussão.** A hipótese se confirmou, na mesma direção da amostra piloto, com uma mediana ligeiramente menor (87,5% contra 92,6% na piloto). A média de 80,2% também ficou perto da observada na piloto (81,8%). A mediana continua mostrando que o repositório típico da amostra fecha a maior parte das Issues que recebe.

A cauda inferior é um pouco mais espessa na base completa: 108 repositórios (22 + 86, 11,3% dos 957 com Issues) ficam abaixo de 50% de fechamento, contra 7 dos 66 (10,6%) na piloto — proporção parecida, mas em números absolutos mostra que a base completa captura mais casos com baixo percentual de fechamento, plausivelmente por incluir repositórios menos maduros no ranking de estrelas do que os 100 mais estrelados da piloto. Os 43 repositórios sem Issues continuam reportados separadamente; ausência de Issues não é evidência de 0% nem de 100% de fechamento.

## RQ07. Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?

Métrica: resultados das RQ02, RQ03 e RQ04 divididos por linguagem.

Os números desta seção vêm da coleta oficial de 1.000 repositórios
(`data/raw/repos_raw_2026-08-20T222207Z.csv`), consolidada em
`data/processed/repos_rq07_consolidated_2026-08-20T222207Z.csv` (S03-01) e
analisada por `src/analysis/rq07_analysis.py` (S03-02), com saída em
`reports/drafts/rq07_analysis_2026-08-20T222207Z.md` e
`data/processed/rq07_statistics_2026-08-20T222207Z.csv`. A validação
independente (`src/analysis/rq07_validation.py`, ver `docs/validation/rq07-validation.md`)
reproduziu as mesmas estatísticas, correlações e outliers sem inconsistências.

**Hipótese.** A expectativa era que sim: repositórios em linguagens populares
(segundo o GitHub Octoverse 2025 — TypeScript, Python, JavaScript, Java, C#,
PHP, Shell, C++, HCL, Go) deveriam atrair mais contribuidores externos, por
estarem em ecossistemas com mais desenvolvedores disponíveis, e por isso
também tenderiam a lançar mais releases e a ser atualizados com mais
frequência. Uma observação que já havia aparecido na RQ03 servia de ponto de
partida: a falta de linguagem primária tem forte relação com a falta de
releases (85,1% contra 23,1% na base completa, ver RQ03), então "sem
linguagem" precisa ser tratada como categoria própria na segmentação, e não
descartada.

**O que os dados mostram.** Da amostra de 1.000, 87 repositórios não têm
linguagem primária identificada e ficam fora da comparação por popularidade
de linguagem (mas continuam nas correlações gerais). Dos 913 restantes, 702
(76,9%) usam linguagem popular e 211 (23,1%) não.

| grupo | métrica | n | média | mediana | Q1 | Q3 |
|---|---|---:|---:|---:|---:|---:|
| Popular | Pull requests aceitas | 702 | 4.519,09 | 1.000,00 | 222,00 | 3.908,25 |
| Popular | Releases | 702 | 153,00 | 62,00 | 6,00 | 186,00 |
| Popular | Dias desde o último push | 702 | 90,61 | 1,00 | 0,00 | 20,75 |
| Não popular | Pull requests aceitas | 211 | 4.424,78 | 670,00 | 181,00 | 3.216,50 |
| Não popular | Releases | 211 | 89,91 | 30,00 | 0,00 | 114,00 |
| Não popular | Dias desde o último push | 211 | 116,83 | 3,00 | 0,00 | 36,50 |

Correlação entre estrelas (popularidade) e as métricas de RQ01–RQ06, na
amostra completa:

| métrica | n | Pearson | Spearman |
|---|---:|---:|---:|
| Idade (anos) | 1.000 | 0,001 | -0,033 |
| Pull requests aceitas | 1.000 | 0,083 | 0,107 |
| Releases | 1.000 | -0,022 | -0,019 |
| Dias desde o último push | 1.000 | -0,087 | -0,111 |
| Issues totais | 1.000 | 0,168 | 0,086 |
| % de issues fechadas | 957 | 0,033 | 0,041 |

**Discussão.** A hipótese se confirmou parcialmente, com magnitude bem menor
do que o esperado. Nas três métricas, o grupo de linguagens populares
apresenta mediana melhor que o grupo não popular: mais Pull Requests aceitas
(1.000 vs. 670), mais releases (62 vs. 30) e push mais recente (1 dia vs. 3
dias de mediana). A direção da hipótese está correta nos três casos.

Mas a diferença é pequena diante da dispersão de cada métrica. As médias de
Pull Requests aceitas são quase idênticas entre os grupos (4.519 vs. 4.425),
o que mostra que a mediana capta melhor o efeito da linguagem do que a média,
dominada por outliers presentes nos dois grupos. As correlações diretas entre
estrelas e as métricas de RQ02/RQ03/RQ04 são todas fracas (|r| < 0,17 em
Pearson e Spearman), inclusive com sinal contrário ao esperado para releases
(-0,02) e dias desde o push (-0,09, mas na direção "mais popular, push mais
recente", o que é consistente com a RQ04). Ou seja: dentro da amostra de
repositórios já populares, ter mais estrelas não se traduz em mais
contribuição externa ou mais releases de forma proporcional — o efeito de
linguagem observado na comparação por grupo é mais sobre "que tipo de
projeto é" do que sobre "quão popular é".

A análise de outliers (`reports/drafts/outliers_2026-08-20T222207Z.md`, S03-04)
reforça essa leitura: os repositórios sinalizados simultaneamente em Pull
Requests aceitas, releases e estrelas (`ggml-org/llama.cpp`,
`kubernetes/kubernetes`, `vercel/next.js`, `n8n-io/n8n`,
`langchain-ai/langchain`) são todos escritos em linguagens populares
(C++, Go, JavaScript, TypeScript, Python), o que é consistente com a
hipótese — mas são apenas 5 dos 1.000 repositórios, e não sustentam sozinhos
uma relação forte na população inteira.

Um resultado inesperado: a correlação entre estrelas e `releases_count` é
levemente negativa. Combinado com o teto de `releases.totalCount` em 1000 da
API (23 repositórios truncados, ver `docs/dataset/raw-dataset.md`), isso sugere que
parte dos repositórios mais estrelados tem o valor real de releases
subestimado, o que pode estar atenuando ou até invertendo artificialmente
essa correlação — uma limitação a considerar antes de qualquer conclusão
causal.

**Limitações.** As correlações são de associação, não de causalidade.
`releases_count` truncado em 1000 (23 casos na amostra completa) subestima
o grupo com mais releases, que tende a coincidir com repositórios populares
e ativos — isso é uma limitação conhecida também na RQ03. `days_since_push`
usa `collected_at` fixo por execução (ver `docs/methodology.md`, seções 5 e
13), então repositórios com atividade durante a janela de coleta paginada
podem ter valores levemente distorcidos, sem impacto relevante na mediana.
Os 87 repositórios sem linguagem primária (documentação, listas curadas)
foram mantidos fora da comparação por grupo, mas continuam nas correlações
gerais, o que é consistente com o tratamento dado a essa categoria nas
RQ05/RQ06.

## Limitações

Todos os números deste documento (RQ01–RQ07) vêm da coleta oficial de 1.000
repositórios, coletada em 2026-08-20T22:22:07Z e validada sem inconsistências
críticas (`docs/validation/`).

A API limita o `releases.totalCount` em 1.000, o que subestima média e máximo da RQ03 (23 repositórios no teto na base completa) e, possivelmente, a correlação entre estrelas e releases discutida na RQ07.

A data do primeiro commit não é obtida pela API numa requisição só, então o período de desenvolvimento (RQ04) usa a data de criação do repositório como aproximação, o que pode subestimar o período real de repositórios com histórico importado de outro sistema de controle de versão.

`collected_at` é fixado no início da coleta paginada; 27 registros de RQ03/RQ04 apresentaram `pushed_at`/`last_commit_date` levemente posteriores a essa referência, efeito esperado de uma coleta longa contra uma API em produção (ver `docs/methodology.md`, seções 5 e 13), sem impacto relevante nas conclusões.

Os dados são um retrato do momento da coleta. O número de estrelas muda o tempo todo e a composição da amostra pode ser diferente numa coleta futura.
