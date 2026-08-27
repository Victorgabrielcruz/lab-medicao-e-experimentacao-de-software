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

> Esta seção usa a **amostra oficial de 1.000 repositórios**
> (`repos_rq07_consolidated_2026-08-20T222207Z.csv`), diferente das seções acima,
> que ainda estão na amostra piloto de 100. Ver a nota em Limitações.

Os repositórios foram separados em três grupos: os que usam uma das dez linguagens
do Octoverse 2025, os que usam outra linguagem, e os que não têm linguagem primária.
O terceiro grupo é mantido separado de propósito, porque descartá-lo inflaria
artificialmente o resultado dos outros dois.

**Hipótese.** A previsão do grupo era que sim, nas três frentes. A ideia era que
linguagem popular significa comunidade grande, e comunidade grande significa mais
gente abrindo pull request, mais pressão por versionamento e manutenção mais
frequente.

**O que os dados mostram.**

| grupo | repositórios | PRs aceitas | releases | dias desde o push |
|---|---|---|---|---|
| linguagem popular | 702 | 1000 | 62 | 1 |
| outra linguagem | 211 | 670 | 30 | 3 |
| sem linguagem | 87 | 129 | 0 | 178 |

Comparando apenas os 913 repositórios que têm linguagem, com teste de Mann-Whitney e
tamanho de efeito por correlação rank-biserial:

| métrica | p-valor | efeito | leitura |
|---|---|---|---|
| PRs aceitas | 0,045 | 0,091 | desprezível |
| releases | < 0,0001 | 0,204 | pequeno |
| dias desde o push | 0,144 | -0,063 | não significativo |
| issues fechadas | 0,002 | 0,142 | pequeno |

Para efeito de contraste, popular contra sem linguagem em releases dá p = 4,8e-29 e
efeito 0,727, que é um efeito grande.

Por linguagem, entre as que têm ao menos 20 repositórios:

| linguagem | n | PRs aceitas | releases | dias desde o push | no top 10 |
|---|---|---|---|---|---|
| Python | 227 | 560 | 20 | 2 | sim |
| TypeScript | 173 | 1979 | 133 | 0 | sim |
| JavaScript | 111 | 617 | 37 | 6 | sim |
| Go | 77 | 1958 | 142 | 0 | sim |
| Rust | 58 | 2354 | 96 | 0 | **não** |
| C++ | 41 | 1159 | 46 | 0 | sim |
| Java | 41 | 945 | 55 | 2 | sim |
| Jupyter Notebook | 24 | 78 | 0 | 23 | não |
| C | 21 | 294 | 46 | 0 | não |
| Shell | 20 | 390 | 10 | 15 | sim |

**Discussão.** A hipótese se confirma em parte, e a parte que não se confirma é a mais
interessante.

Releases é a única frente com diferença consistente: 62 contra 30, com p abaixo de
0,0001. Mas o tamanho de efeito é 0,204, ou seja, pequeno. Existe diferença real,
só que ela explica pouco da variação entre os repositórios.

Pull requests aceitas fica no limite. O p-valor de 0,045 passaria por significativo
num teste isolado, mas o efeito de 0,091 é desprezível. Com 913 repositórios,
diferença pequena vira estatisticamente detectável sem ser praticamente relevante.
Reportar só o p-valor aqui daria uma impressão errada de força.

**Frequência de atualização não difere.** O p-valor de 0,144 não permite afirmar
diferença entre os grupos. As medianas de 1 e 3 dias são praticamente o mesmo
comportamento. Essa parte da hipótese foi refutada.

O que realmente separa os grupos não é linguagem popular contra linguagem menos
popular, é ter ou não ter linguagem. O grupo sem linguagem tem mediana de zero
releases, 85% deles nunca publicaram nenhuma, e 32% estão parados há mais de um ano
contra 9% do grupo popular. O efeito de 0,727 nessa comparação é várias vezes maior
que o de 0,204 entre popular e não popular. Traduzindo: a diferença que a RQ07
detecta é majoritariamente a diferença entre software e material que não é software,
e não um efeito da linguagem escolhida.

**Resultados inesperados.**

Rust não está no top 10 do Octoverse e mesmo assim lidera em pull requests aceitas,
com mediana de 2.354, acima de qualquer linguagem popular da tabela. Tem também 96
releases e mediana de zero dias desde o último push. C fica fora do ranking e tem 46
releases, mais que JavaScript e Python.

Dentro do próprio grupo popular a dispersão é enorme: Go tem mediana de 142 releases
e Shell tem 10, uma diferença de mais de 14 vezes. Python, a linguagem mais frequente
da amostra com 227 repositórios, tem mediana de 20 releases, abaixo de Rust, C++ e
Java.

Isso indica que "linguagem popular" não é uma categoria homogênea para efeito de
prática de engenharia. O ranking do Octoverse mede número de contribuidores na
plataforma, que é uma medida de adoção, não de como os projetos daquela linguagem são
mantidos.

**Resposta.** Sistemas escritos em linguagens mais populares lançam mais releases, com
diferença estatisticamente significativa mas de efeito pequeno, e recebem mais pull
requests aceitas, com diferença no limite da significância e efeito desprezível. Não
são atualizados com mais frequência: nessa métrica os grupos são equivalentes. A
diferença observada entre os grupos é explicada principalmente pela presença de
repositórios sem linguagem primária, que não são software, e não pela escolha da
linguagem em si.

## Limitações

As seções RQ01 a RQ06 ainda usam a amostra piloto de 100 repositórios, e a RQ05 usa
75, porque a coleta daquela execução parou na quarta página. A seção RQ07 já usa a
amostra oficial de 1.000. **Antes da entrega final, as seis primeiras precisam ser
recalculadas sobre a base de 1.000**, senão o relatório mistura duas amostras
diferentes.

O ranking de linguagens do Octoverse mede número de contribuidores na plataforma, que
é adoção, não prática de engenharia. Isso limita o quanto a RQ07 pode concluir: a
divisão entre popular e não popular agrupa linguagens com comportamentos bem
diferentes entre si.

A RQ07 mostra associação, não causa. Linguagem está confundida com tipo de projeto,
já que certas linguagens concentram certos tipos de software, e não é possível separar
os dois efeitos com os dados coletados.

A amostra são os 1.000 repositórios mais estrelados, o que não representa o GitHub em
geral. As conclusões valem para o topo do ranking de popularidade.

A API limita o `releases.totalCount` em 1000, o que subestima média e máximo da RQ03.

A data do primeiro commit não é obtida pela API numa requisição só, então o período de desenvolvimento usa a data de criação do repositório como aproximação.

Os dados são um retrato do momento da coleta. O número de estrelas muda o tempo todo e a composição da amostra pode ser diferente numa coleta futura.
