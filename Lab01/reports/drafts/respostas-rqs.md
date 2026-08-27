# Respostas das questões de pesquisa

Laboratório 01, disciplina de Laboratório de Experimentação de Software.

Os números abaixo vêm de uma amostra piloto de 100 repositórios, coletada em 2026-08-13 com o filtro `stars:>10000 sort:stars-desc` pela API GraphQL do GitHub. A amostra oficial de 1.000 repositórios será coletada na Sprint 2, então os resultados aqui valem como indício e podem mudar. Os dados brutos estão em `data/raw/repos_raw_2026-08-13T225359Z.csv`.

As hipóteses foram escritas como previsão para a base de 1.000, antes dessa coleta maior acontecer.

## RQ01. Sistemas populares são maduros/antigos?

Métrica: idade do repositório, a partir da data de criação.

**Hipótese.** A hipótese para esta questão é que sistemas populares tendem a ser maduros/antigos, considerando que projetos que permanecem populares no GitHub podem apresentar maior tempo de desenvolvimento e manutenção.

**O que os dados mostram.**

| Estatística   |   Idade do repositório |
| ------------- | ---------------------: |
| Média         |   **7 anos e 8 meses** |
| Mediana       |   **8 anos e 3 meses** |
| 1º quartil    |   **3 anos e 4 meses** |
| 3º quartil    |  **11 anos e 8 meses** |
| Mínimo        |            **4 meses** |
| Máximo        | **16 anos e 11 meses** |
| Desvio padrão |  **4 anos e 10 meses** |

A distribuição dos repositórios por faixa de idade foi:
| Faixa de idade        | Quantidade | Percentual |
| --------------------- | ---------: | ---------: |
| Até 2 anos            |         18 |        18% |
| Mais de 2 até 5 anos  |         18 |        18% |
| Mais de 5 até 10 anos |         24 |        24% |
| Mais de 10 anos       |         40 |        40% |
| **Total**             |    **100** |   **100%** |

**Discussão.** Os resultados da amostra piloto fornecem evidências favoráveis à hipótese de que sistemas populares tendem a ser maduros ou antigos. A idade média dos repositórios foi de aproximadamente 7 anos e 8 meses, enquanto a mediana foi de 8 anos e 3 meses.

A distribuição por faixas reforça essa tendência. 64% dos repositórios possuem mais de 5 anos, sendo que 40% possuem mais de 10 anos. Portanto, a maior parte da amostra é composta por projetos que possuem um período considerável de existência.

O intervalo entre o primeiro e o terceiro quartil também demonstra uma variação relevante na idade dos projetos: metade dos repositórios possui idade entre aproximadamente 3 anos e 4 meses e 11 anos e 8 meses.

Apesar dessa concentração em projetos mais antigos, a amostra também apresenta repositórios relativamente recentes. 18% possuem até 2 anos, incluindo projetos com aproximadamente 4 meses de existência. Isso demonstra que a idade não é uma condição necessária para um repositório alcançar popularidade.

Dessa forma, a hipótese é apoiada pela amostra piloto, uma vez que a maioria dos repositórios populares analisados possui vários anos de existência. Entretanto, os resultados não permitem afirmar que todo sistema popular seja necessariamente antigo.


## RQ02. Sistemas populares recebem muita contribuição externa?

Métrica: total de pull requests aceitas.

**Hipótese.** A hipótese para esta questão é que sistemas populares recebem muita contribuição externa, considerando que projetos com maior popularidade podem atrair uma comunidade maior de desenvolvedores e, consequentemente, mais contribuições por meio de Pull Requests.

**O que os dados mostram.**
| Estatística   | Pull Requests aceitas |
| ------------- | --------------------: |
| Média         |      **7.302,54 PRs** |
| Mediana       |      **1.253,50 PRs** |
| 1º quartil    |           **243 PRs** |
| 3º quartil    |         **7.014 PRs** |
| Mínimo        |             **0 PRs** |
| Máximo        |        **73.425 PRs** |
| Desvio padrão |     **14.112,05 PRs** |

A distribuição por quantidade de Pull Requests aceitas foi:

| Pull Requests aceitas | Quantidade | Percentual |
| --------------------- | ---------: | ---------: |
| 0 PRs                 |          3 |         3% |
| 1–99 PRs              |          9 |         9% |
| 100–999 PRs           |         34 |        34% |
| 1.000–9.999 PRs       |         35 |        35% |
| 10.000+ PRs           |         19 |        19% |
| **Total**             |    **100** |   **100%** |

**Discussão.** Os resultados da amostra piloto fornecem forte evidência favorável à hipótese de que sistemas populares recebem contribuições externas.

A mediana foi de 1.253,5 Pull Requests aceitas, indicando que metade dos repositórios analisados possui pelo menos esse número de contribuições incorporadas. Além disso, 97% dos repositórios possuem pelo menos uma Pull Request aceita.

A distribuição também mostra que 88% dos repositórios possuem pelo menos 100 Pull Requests aceitas, enquanto 54% possuem pelo menos 1.000. Esses valores indicam que a participação externa está presente em grande parte dos projetos analisados.

Entretanto, existe uma diferença bastante significativa entre a média e a mediana. Enquanto a média foi de 7.302,54 PRs, a mediana foi de apenas 1.253,50 PRs. Essa diferença, juntamente com o desvio padrão de 14.112,05 PRs, indica uma distribuição bastante assimétrica.

Essa assimetria é explicada pela existência de alguns repositórios com volumes extremamente elevados de contribuições. O maior valor observado foi de 73.425 Pull Requests aceitas, enquanto 19% dos projetos possuem pelo menos 10.000 PRs.

Por esse motivo, a mediana representa melhor o comportamento típico da amostra do que a média. Ainda assim, a grande quantidade de repositórios com centenas ou milhares de Pull Requests aceitas fornece evidências de uma participação externa significativa.

## RQ03. Sistemas populares lançam releases com frequência?

Métrica: total de releases.

**Hipótese.** A gente esperava que sim. A ideia era que projeto popular costuma ser projeto maduro, com muita gente usando, e que por isso precisaria versionar as entregas de forma explícita. A previsão era achar quase todo mundo com um número alto de releases e pouquíssimos repositórios zerados.

**O que os dados mostram.**

| | valor |
|---|---|
| mediana | 15 |
| média | 133,8 |
| 1º quartil | 0 |
| 3º quartil | 167,25 |
| com zero releases | 41 de 100 |

Por faixa: 41 repositórios com 0 releases, 5 entre 1 e 9, 13 entre 10 e 49, 20 entre 50 e 199, e 21 com 200 ou mais.

**Discussão.** A hipótese caiu pela metade. Olhando só a mediana de 15 parece que ela se confirmou, mas esse número esconde o principal: a distribuição tem dois picos. O primeiro quartil é zero, ou seja, 41% da amostra nunca publicou uma release, enquanto 21% passam de 200. Quase não existe meio termo, só 5 repositórios estão na faixa de 1 a 9.

Isso não é uma população com frequências diferentes de release. São dois grupos separados: quem usa release como parte do processo e quem simplesmente não usa o recurso.

Cruzando com a linguagem primária dá pra ver o que separa os dois. Entre os 13 repositórios sem linguagem primária, 85% têm zero releases. Entre os 87 com linguagem, esse número cai pra 34%. Repositório sem linguagem no topo do ranking é lista curada, coletânea de links, material de estudo, coisa que não é software executável e onde release não faz sentido. Então a resposta da RQ03 muda dependendo de como a amostra é segmentada: se contar só software de verdade, a proporção de zerados cai pra um terço.

Uma ressalva de medição. A API corta o `releases.totalCount` em 1000, e 4 repositórios da amostra bateram exatamente nesse valor, o que foi conferido na mão na aba Releases de cada um. Então a média de 133,8 é um piso e não uma estimativa, e o máximo não quer dizer nada. A mediana continua confiável porque está longe do teto. Os casos afetados estão marcados na coluna `releases_no_teto`.

## RQ04. Sistemas populares são atualizados com frequência?

Métrica: tempo até a última atualização.

Usamos o `pushedAt`, que é a data do último push de código. O `updatedAt` foi descartado porque ele muda com qualquer alteração de metadado, até quando alguém dá uma estrela, e isso inflaria a atividade. Os dois campos foram coletados, o `updatedAt` ficou só como controle.

**Hipótese.** Esperávamos que sim, mas com ressalva. A previsão era achar a maioria ativa e uma parcela relevante de projeto popular parado, aquele que juntou estrela no passado e foi abandonado. O chute era algo entre 20% e 30% da amostra sem atualização há mais de um ano.

**O que os dados mostram.**

| | dias desde o último push | dias desde o último commit |
|---|---|---|
| mediana | 0 | 1 |
| 3º quartil | 15 | 17 |
| máximo | 779 | 1128 |

Por janela de tempo: 57 repositórios receberam push no mesmo dia da coleta, 70 na última semana, 83 no último mês, 87 nos últimos três meses. Só 4 estão parados há mais de um ano. Nenhum repositório da amostra está arquivado.

A mediana de commits é 4.871 e a mediana do período de desenvolvimento é de 8 anos.

**Discussão.** A hipótese se confirmou, e mais forte do que a gente imaginava. Mediana de zero dias significa que mais da metade da amostra recebeu código no próprio dia em que rodamos a coleta. Setenta por cento receberam na última semana.

A ressalva não se sustentou. Esperávamos de 20% a 30% de projetos parados e achamos 4%. O fato de nenhum repositório estar arquivado reforça isso.

Dá pra ler que popularidade e manutenção ativa quase coincidem nessa amostra. Projeto popular não é só mantido, é mantido todo dia. Uma explicação possível, que dá pra testar na base completa, é que ficar no topo do ranking de estrelas exige atividade contínua: projeto abandonado vai perdendo posição pra projeto novo e acaba saindo da amostra.

Juntando com a mediana de 8 anos de desenvolvimento, o retrato é de sistema velho e ativo ao mesmo tempo, o que conversa direto com a RQ01 e vale retomar na RQ07.

Uma limitação aqui: o início do período usa a data de criação do repositório e não a do primeiro commit, que a API não entrega numa requisição só. Em repositório que teve o histórico importado de outro sistema de controle de versão, esse período fica menor do que o real.

## RQ05. Sistemas populares são escritos nas linguagens mais populares?

Métrica: linguagem primária de cada repositório.

**Fonte e hipótese.** Foi usado o [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/). A fonte classifica como mais populares TypeScript, Python, JavaScript, Java, C#, PHP, Shell, C++, HCL e Go. A expectativa era que a maior parte dos repositórios mais estrelados usasse uma dessas linguagens, embora listas curadas e materiais de documentação pudessem não ter linguagem primária.

**O que os dados mostram.** A configuração era para 100 repositórios, mas a API retornou erro 502 na quarta página; por isso esta análise usa os 75 repositórios válidos que foram persistidos nas três primeiras páginas. Desses 75, 50 (66,7%) têm uma linguagem do top 10 do Octoverse e 25 (33,3%) não têm.

| linguagem primária | repositórios | percentual |
|---|---:|---:|
| Python | 20 | 26,7% |
| TypeScript | 14 | 18,7% |
| Sem linguagem identificada | 11 | 14,7% |
| JavaScript | 7 | 9,3% |
| Shell | 4 | 5,3% |
| Go | 3 | 4,0% |
| C++ | 1 | 1,3% |
| Java | 1 | 1,3% |
| Outras linguagens | 14 | 18,7% |

As linguagens populares mais frequentes são Python, TypeScript e JavaScript: juntas, aparecem em 41 dos 75 repositórios (54,7%). A categoria `Sem linguagem identificada` não foi descartada; ela reúne repositórios para os quais a API não informou `primaryLanguage`.

**Discussão.** A hipótese se confirmou para a maior parte da amostra: aproximadamente dois terços dos repositórios usam linguagens populares conforme a mesma plataforma de onde a amostra foi coletada. Mas o resultado não significa que popularidade dependa apenas da linguagem. Os 11 repositórios sem linguagem e parte das 14 ocorrências de outras linguagens incluem projetos de documentação, listas e materiais que não são necessariamente aplicações com código executável. Na coleta de 1.000 repositórios, essa categoria deve continuar separada, porque removê-la artificialmente aumentaria o percentual de linguagens populares.

## RQ06. Sistemas populares possuem um alto percentual de issues fechadas?

Métrica: razão entre issues fechadas e total de issues.

**Hipótese.** Esperávamos um percentual alto de Issues fechadas. Projetos populares recebem muitos relatos e pedidos, mas também tendem a ter mais mantenedores e colaboradores para classificar, resolver ou encerrar Issues antigas.

**O que os dados mostram.** Também nesta RQ foram usados os 75 repositórios persistidos antes da falha 502 na quarta página. Nove deles não possuem Issues abertas nem fechadas e, portanto, não entram no cálculo do percentual para evitar divisão por zero. Nos 66 repositórios com Issues, os resultados foram:

| | percentual de Issues fechadas |
|---|---:|
| mediana | 92,6% |
| média | 81,8% |
| 1º quartil | 74,1% |
| 3º quartil | 97,1% |
| mínimo | 13,3% |
| máximo | 100,0% |

Por faixa: 1 repositório está entre 0% e 24,9%, 6 entre 25% e 49,9%, 10 entre 50% e 74,9%, 46 entre 75% e 99,9%, e 3 chegaram a 100%. Assim, 49 dos 66 repositórios com Issues (74,2%) têm pelo menos 75% de fechamento; 36 (54,5%) têm pelo menos 90%.

**Discussão.** A hipótese se confirmou com folga. A mediana de 92,6% mostra que o repositório típico da amostra fecha a maior parte das Issues que recebe. A média menor que a mediana (81,8%) revela alguns casos com percentuais baixos puxando o resultado para baixo, mas eles são minoria: apenas 7 dos 66 repositórios com Issues ficam abaixo de 50%. Os nove repositórios sem Issues devem continuar reportados separadamente; ausência de Issues não é evidência de 0% nem de 100% de fechamento.

## RQ07. Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?

Métrica: resultados das RQ02, RQ03 e RQ04 divididos por linguagem.

Uma coisa que já apareceu na RQ03 e serve de ponto de partida: a falta de linguagem primária tem forte relação com a falta de releases, 85% contra 34%. Então "sem linguagem" precisa ser tratada como categoria própria na hora de segmentar, e não descartada.

*A fazer, grupo, depois que as RQ02, RQ03 e RQ04 estiverem prontas.*

## Limitações

Os números são de uma amostra piloto de 100 repositórios. A coleta oficial de 1.000 vem na Sprint 2 e pode mudar as distribuições.

A API limita o `releases.totalCount` em 1000, o que subestima média e máximo da RQ03.

A data do primeiro commit não é obtida pela API numa requisição só, então o período de desenvolvimento usa a data de criação do repositório como aproximação.

Os dados são um retrato do momento da coleta. O número de estrelas muda o tempo todo e a composição da amostra pode ser diferente numa coleta futura.
