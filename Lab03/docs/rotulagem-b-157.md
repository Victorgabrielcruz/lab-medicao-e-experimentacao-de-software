# Rotulagem B — #157

**Atualização em 20/10/2026:** planilhas preenchidas, com 12 novas decisões
assistidas por IA ainda sujeitas à confirmação humana. O commit `b09ec05`
registra que a revisão manual do conjunto anterior ocorreu em outra branch,
conforme informado pelo responsável. Esse registro foi preservado e não se
estende automaticamente à complementação atual.

## Arquivos e cobertura

- [Repositórios B](../validacao/amostra-ouro/rotulador_B_repositorios.csv):
  60 classificações de tipo de projeto e 60 decisões sobre entregas reais.
- [Releases B](../validacao/amostra-ouro/rotulador_B_releases.csv):
  mesmos 300 pares oficiais, cinco releases por repositório; 251 decisões
  `sim` e 49 `nao`, sem células de julgamento vazias.
- [Evidências e pendências](evidencias/157-rotulagem-b.json): origem,
  hashes, contagens e justificativas/fontes das 12 decisões complementadas.

Cada uma das 12 células antes vazias recebeu uma decisão fundamentada:
11 `sim` e um `nao`. Ausências não foram convertidas automaticamente em
negativas. As 288 decisões anteriores e os 60 julgamentos de projeto foram
preservados. Os campos de
identidade, datas, tags, URLs, cabeçalhos, ordem e UTF-8 com BOM foram
preservados. O sorteio e as planilhas A/C não foram alterados.

## Integração com a base de 500

A `main` foi atualizada até `6bc226a` e integrada nesta branch. A
[decisão da retomada](decisao-retomada-500.md#amostra-ouro-155) determina
manter a amostra-ouro sorteada sobre os primeiros 255 elegíveis, sem novo
sorteio. O manifesto da amostra continua idêntico, com `random_state=42`;
os seus 60 repositórios estão entre os 500 IDs publicados.

A seleção dos 500 está concluída, mas os compares finais ainda estão
parciais no snapshot. Isso não impede esta rotulagem: foram preservadas as
notas congeladas do snapshot de 255 e consultadas fontes públicas específicas
para os itens pendentes, sem retomar os coletores nem extrair todo o cache.

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

Na complementação, Bevy, Julia, UI UX Pro Max, Unsloth e Hindsight tiveram
seus diffs/código examinados; Sway teve a causa do revert conferida nas issues
referidas pela PR. Para ClickHouse foi localizado o changelog cujo cabeçalho
nomeia exatamente `v26.4.1.1141-stable`, em vez de atribuir alterações do
compare entre séries diferentes. Jan, Meteor, Moby e Hermes foram julgados
pelas notas completas disponíveis no snapshot. As fontes adicionais têm
URL, tamanho e SHA-256 registrados na evidência; as notas são vinculadas aos
checkpoints já verificados e ao hash do texto UTF-8 usado na revisão.

O único `nao` novo é Meteor 3.0: suas notas descrevem a migração para APIs
assíncronas e mudanças incompatíveis, sem defeito identificado. Esse
julgamento tem a limitação de não haver compare oficial para a primeira
release elegível. Unsloth `Windows-ARM64` foi marcado `sim` pelo commit da
tag que corrige a ordem de GPUs CUDA; isso não demonstra que os binários
ARM64 executem esse caminho. Ambos os limites estão registrados por item.

As decisões se baseiam na leitura de notas, trechos relevantes
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

## Limitações

Não foram consultados os julgamentos de A/C nem gerados rótulos de consenso.
O preenchimento inicial (`b6bb8fc`) e a complementação atual tiveram apoio
de IA/Codex. Este chat já conhece a heurística da #161; portanto, o apoio de
IA não é cego e não deve ser relatado como avaliador humano independente.
As 12 observações novas identificam explicitamente esse apoio e a revisão
humana pendente. O preenchimento das 300 linhas não comprova, sozinho, o
critério de independência da #157.

O responsável informou que C será preenchido pelo grupo em conjunto.
Esse procedimento deve ser declarado: uma decisão conjunta não representa
um terceiro julgamento independente para o kappa de Fleiss. Não se deve
relatar concordância entre três avaliadores independentes com base nesse
desenho.

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

## Pendências deste conjunto

1. Confirmar ou corrigir humanamente as 12 decisões complementadas, listadas
   na evidência, registrando autoria, data e alterações. Não declarar esta
   complementação como revisão humana já concluída.
2. Alinhar o livro de códigos ao enunciado e documentar o desenho real de
   avaliação e o preenchimento conjunto de C.
3. Preservar as avaliações antes de produzir o consenso. Não calcular nem
   reportar Fleiss, precisão, recall ou F1 como já obtidos nesta entrega.

Commits desta rotulagem devem referenciar `(#157)`. Eventuais mudanças no
artigo da #165 devem ficar em commit separado. Não há decisões vazias em B;
permanecem a confirmação humana da complementação e os alinhamentos do
protocolo entre o grupo antes do uso como amostra-ouro independente.
