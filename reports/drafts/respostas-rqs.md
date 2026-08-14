# Respostas das questões de pesquisa

Laboratório 01, disciplina de Laboratório de Experimentação de Software.

Os números abaixo vêm de uma amostra piloto de 100 repositórios, coletada em 2026-08-13 com o filtro `stars:>10000 sort:stars-desc` pela API GraphQL do GitHub. A amostra oficial de 1.000 repositórios será coletada na Sprint 2, então os resultados aqui valem como indício e podem mudar. Os dados brutos estão em `data/raw/repos_raw_2026-08-13T225359Z.csv`.

As hipóteses foram escritas como previsão para a base de 1.000, antes dessa coleta maior acontecer.

## RQ01. Sistemas populares são maduros/antigos?

Métrica: idade do repositório, a partir da data de criação.

*A fazer, Víctor.*

## RQ02. Sistemas populares recebem muita contribuição externa?

Métrica: total de pull requests aceitas.

*A fazer, Víctor.*

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

O grupo ainda precisa definir e citar a fonte usada pra "linguagens mais populares", que pode ser TIOBE, GitHut ou o Octoverse do GitHub. A mesma fonte tem que valer pro laboratório inteiro.

*A fazer, Matheus.*

## RQ06. Sistemas populares possuem um alto percentual de issues fechadas?

Métrica: razão entre issues fechadas e total de issues.

*A fazer, Matheus.*

## RQ07. Sistemas escritos em linguagens mais populares recebem mais contribuição externa, lançam mais releases e são atualizados com mais frequência?

Métrica: resultados das RQ02, RQ03 e RQ04 divididos por linguagem.

Uma coisa que já apareceu na RQ03 e serve de ponto de partida: a falta de linguagem primária tem forte relação com a falta de releases, 85% contra 34%. Então "sem linguagem" precisa ser tratada como categoria própria na hora de segmentar, e não descartada.

*A fazer, grupo, depois que as RQ02, RQ03 e RQ04 estiverem prontas.*

## Limitações

Os números são de uma amostra piloto de 100 repositórios. A coleta oficial de 1.000 vem na Sprint 2 e pode mudar as distribuições.

A API limita o `releases.totalCount` em 1000, o que subestima média e máximo da RQ03.

A data do primeiro commit não é obtida pela API numa requisição só, então o período de desenvolvimento usa a data de criação do repositório como aproximação.

Os dados são um retrato do momento da coleta. O número de estrelas muda o tempo todo e a composição da amostra pode ser diferente numa coleta futura.
