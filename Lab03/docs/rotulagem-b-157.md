# Rascunho da rotulagem B assistida por IA — #157

**Estado em 15/10/2026: em andamento, pendente de revisão humana.**
O responsável solicitou preencher B com apoio de IA e finalizar com as
evidências disponíveis para continuar a revisão posteriormente. Este commit
preserva esse rascunho; não comprova a conclusão da rotulagem independente
humana exigida pela #157.

## Arquivos e cobertura

- [Repositórios B](../validacao/amostra-ouro/rotulador_B_repositorios.csv):
  60 sugestões de tipo de projeto e 60 decisões sobre entregas reais.
- [Releases B](../validacao/amostra-ouro/rotulador_B_releases.csv):
  mesmos 300 pares oficiais, cinco releases por repositório; 288 sugestões
  `sim`/`nao` e 12 decisões vazias, com justificativa da pendência.
- [Evidências e pendências](evidencias/157-rotulagem-b-ia.json): origem,
  hashes, contagens e lista dos 12 itens para revisão prioritária.

Todas as observações identificam **IA/Codex**, rascunho e revisão humana
pendente. Nenhuma célula vazia foi transformada em `nao`. Os campos de
identidade, datas, tags, URLs, cabeçalhos, ordem e UTF-8 com BOM foram
preservados. O sorteio e as planilhas A/C não foram alterados.

## Fontes e procedimento

Foram usadas as notas das cinco releases sorteadas de cada projeto, extraídas
dos checkpoints do snapshot publicado em `entregas/dados-brutos-255/`.
As partes do pacote e os 60 checkpoints utilizados tiveram seus SHA-256
conferidos contra o manifesto publicado. A extração de apoio ocorreu em
diretório temporário, sem alterar o snapshot e sem retomar coletores/API.

Os READMEs públicos atuais foram consultados para identificar a função
principal dos projetos. Para code-server foi usada a descrição oficial
no GitHub; o README de Next.js aponta ao arquivo em `packages/next/`.
Changelogs e diffs públicos foram examinados nos casos em que as notas
apenas remetiam a fontes externas. URLs e hashes das fontes baixadas
constam da evidência. Respostas HTML a pedidos de patch não foram tratadas
como lista de commits válida.

As decisões foram escritas pela IA após leitura de notas, trechos relevantes
e, em alguns casos, mensagens/diffs de commits. A seleção de trechos serviu
como apoio à leitura; não foi executado o classificador da #161. Isso não
equivale a inspeção exaustiva de todos os commits das 300 releases.
`nao` indica que não foi identificado defeito nas evidências examinadas;
não demonstra ausência de correções em commits não examinados.

O catálogo e a definição de corretiva seguem o livro de códigos da #155:
**pelo menos uma correção de defeito**, inclusive em releases mistas.
Atualizar dependências ou documentação, isoladamente, não bastou para `sim`.
Essa definição difere do enunciado e do protocolo da #165, que se referem
ao **objetivo principal** de corrigir um defeito recente. A divergência
precisa ser alinhada e reportada antes de usar o conjunto na validação final.
Nenhuma regra comum foi alterada unilateralmente nesta entrega.

## Limitações e independência

O mesmo chat implementou a heurística da #161. Assim, mesmo sem consultar
suas previsões durante este preenchimento, estas sugestões **não são uma
avaliação cega nem um terceiro avaliador humano**. Não foram consultados
os julgamentos de A/C nem gerados rótulos de consenso.

O responsável informou que C será preenchido pelo grupo em conjunto.
Esse procedimento deve ser declarado: uma decisão conjunta não representa
um terceiro julgamento independente para o kappa de Fleiss. Não se deve
relatar concordância entre três avaliadores independentes com base nesse
desenho. Rever sugestões de IA depois também não cria cegueira retroativa.

Os READMEs consultados refletem o estado atual, não necessariamente o fim
da janela. Há projetos híbridos que exigem revisão de categoria, releases
de subpacotes e tags com nomes beta/alpha no instrumento oficial. Os itens
foram preservados conforme a amostra recebida, sem reclassificar a seleção
pelo texto da tag. Algumas notas declaram publicação incompleta ou versão
inutilizável; o julgamento de entrega real aqui é por repositório, e esses
casos de release precisam ser examinados na revisão final.

Compares entre séries de versão diferentes podem incluir mudanças anteriores
ao lançamento analisado. Em especial, conferir a atribuição das correções
nos backports ClickHouse. O registro de uma correção nessas fontes não
comprova que ela seja recente ou o objetivo principal do lançamento.

## Continuação da revisão

1. Revisar os 12 itens sem decisão, listados na evidência, e completar apenas
   quando houver evidência suficiente.
2. Revisar também as 288 sugestões preenchidas e os 60 projetos; registrar
   autoria humana, data, evidências e alterações, sem apagar o histórico de IA.
3. Alinhar o livro de códigos ao enunciado e documentar o desenho real de
   avaliação e o preenchimento conjunto de C.
4. Preservar as avaliações antes de produzir o consenso. Não calcular nem
   reportar Fleiss, precisão, recall ou F1 como já obtidos nesta entrega.

Commits desta rotulagem devem referenciar `(#157)`. Eventuais mudanças no
artigo da #165 devem ficar em commit separado. Este rascunho não fecha a
issue nem demonstra atendimento integral de seus critérios de aceite.
