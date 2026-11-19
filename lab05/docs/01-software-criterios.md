# O software: SQLite

O **SQLite** é uma biblioteca em C que implementa um banco de dados SQL completo,
transacional e sem servidor: o banco inteiro fica em um único arquivo e o motor roda
dentro do processo da aplicação. Por isso, ele vem embutido em sistemas operacionais,
navegadores, celulares e linguagens de programação, em vez de ser instalado como um
serviço à parte.

O experimento usa o SQLite exatamente como as aplicações Python o usam em produção:
pelo módulo `sqlite3` da biblioteca padrão, que inclui o SQLite em todas as
distribuições desde o Python 2.5.

Todas as fontes abaixo foram acessadas em **17/11/2026**.

## Os três critérios

| Critério | Evidência | Fonte |
|---|---|---|
| **Real** | Software de uso geral, mantido pelos autores originais e com site, documentação e histórico de versões públicos. É de **domínio público** e não exige licença | [sqlite.org](https://www.sqlite.org/index.html) · [Copyright](https://www.sqlite.org/copyright.html) |
| **Em operação** | Versão atual **3.54.1, de 16/10/2026**, com releases regulares ao longo de 2026. O projeto assume o compromisso de suporte de longo prazo **até 2050** | [sqlite.org](https://www.sqlite.org/index.html) · [Chronology](https://www.sqlite.org/chronology.html) · [Long-term support](https://www.sqlite.org/lts.html) |
| **Alto impacto** | Estimativa de **mais de 1 trilhão de bancos SQLite em uso ativo**. Ele está em todo Android, iPhone e Mac, em toda instalação do Windows 10/11 e nos navegadores Firefox, Chrome e Safari. É usado por **42,1%** dos respondentes do Stack Overflow Developer Survey 2026, atrás apenas do PostgreSQL | [Most deployed](https://www.sqlite.org/mostdeployed.html) · [Stack Overflow Survey 2026](https://survey.stackoverflow.co/2026/technology) |

## Quem usa

A página oficial de usuários conhecidos cita, entre outros:

| Organização | Uso declarado |
|---|---|
| Google | Android e navegador Chrome |
| Apple | Aplicativos nativos do macOS e do iOS |
| Microsoft | Componente central do Windows 10 |
| Mozilla | Armazenamento de metadados do Firefox e do Thunderbird |
| Airbus | Software de voo da família A350 XWB |
| Bosch | Sistemas multimídia de automóveis (GM, Nissan, Suzuki) |
| Dropbox | Armazenamento local do cliente |
| Library of Congress | Formato recomendado para preservação de conteúdo digital |

Fonte: [Well-Known Users of SQLite](https://www.sqlite.org/famous.html).

## Leitura crítica dos números

- O "trilhão de bancos" é uma **estimativa dos próprios autores**: mais de 4 bilhões de
  smartphones, cada um com centenas de arquivos SQLite. A página afirma que números
  exatos são difíceis de obter. Usamos o número como ordem de grandeza, não como medida.
- O percentual do Stack Overflow mede **desenvolvedores que declaram usar** o SQLite,
  não instalações. A amostra é de respondentes voluntários da pesquisa.
- A lista de usuários conhecidos é **declarada pelo projeto** e não é exaustiva.

## Versão usada no experimento

O experimento mede o SQLite **embutido no Python** que executa a coleta. A versão exata é
registrada a cada execução em `data/ambiente.json` (campo `sqlite_version`).

| Ambiente | Python | SQLite embutido | Release do SQLite |
|---|---|---|---|
| Instalador oficial do python.org (Windows) | 3.12.10 | 3.49.1 | 18/02/2025 |
| Build da Astral (python-build-standalone) | 3.12.14 | 3.53.1 | 05/05/2026 |

As versões estáveis mais recentes são as 3.53.x e 3.54.x. Por isso, a coleta deve usar a
build com o SQLite mais atual disponível, e a versão efetivamente usada entra nas
ameaças à validade externa: os modos `journal_mode` e `synchronous` existem com o mesmo
significado em todas essas versões, mas otimizações internas podem mudar os tempos
absolutos.
