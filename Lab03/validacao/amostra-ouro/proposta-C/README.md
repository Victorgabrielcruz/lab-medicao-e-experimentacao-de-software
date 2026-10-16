# Proposta de preenchimento C — revisão da #158

Esta pasta contém **sugestões de análise assistida por IA (Codex)**. Não é uma
rotulagem humana independente e não conclui a #158. As duas planilhas oficiais
`../rotulador_C_repositorios.csv` e `../rotulador_C_releases.csv` permanecem
intactas e em branco. Os arquivos desta pasta não devem entrar como rótulos
de consenso, referência de avaliação ou observações independentes no Kappa.

## Material preparado

- `proposta_C_repositorios.csv`: 60 sugestões de tipo de projeto e de uso das
  releases como entregas, todas com observações. São hipóteses baseadas nas
  descrições públicas cacheadas e nas notas de releases; o README de cada
  projeto ainda precisa ser conferido pelo responsável.
- `proposta_C_releases.csv`: mesmas 300 releases do sorteio oficial, com 207
  sugestões `sim`, 42 `nao` e 51 células de julgamento vazias por evidência
  insuficiente. Todas têm observações; as sugestões `sim` incluem um trecho
  das notas que motivou a interpretação.
- `evidencias.json`: origem, hashes, decisões propostas e fontes textuais.
- `validacao.json`: contagens, IDs únicos, colunas fixas e hashes dos CSVs.

O sorteio é o oficial da #155: 60 repositórios, cinco releases por repositório,
`random_state=42`, população encerrada de 255 IDs. Janela:
`[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`.

## Como foi feita a proposta

A análise usou somente o manifesto oficial, as planilhas C em branco, as
descrições de repositórios presentes no cache local e os textos das releases
da consolidação encerrada. Não houve nova coleta ou chamada de API. As
planilhas A/B e os resultados ou código da heurística CFR(b) não foram usados.
Buscas de trechos nas notas serviram à navegação da leitura; os rótulos não
foram calculados a partir de patch SemVer, contagem de palavras ou da #161.

Seguiu-se o [livro de códigos](../LIVRO-CODIGOS.md): procurar evidência de
correção de defeito, distinguindo alterações de conteúdo, funcionalidades,
desempenho, refatorações e dependências. `nao` significa que nenhuma correção
foi identificada nas notas examinadas, não que todos os commits do compare
tenham sido verificados. Um compare remoto não foi consultado. Notas vazias,
remissões a changelog externo e alterações ambíguas ficam pendentes.

Descrições de projetos não substituem README e documentação. Categorias
híbridas e o caráter de software ou conteúdo das releases exigem confirmação.
As datas escritas nas notas podem diferir de `published_at`; o sorteio usa o
último campo, conforme o protocolo. Os IDs e as releases sorteadas não foram
alterados para resolver essas diferenças.

## Próxima etapa da #158

O responsável deve fazer o julgamento de cada projeto e release conforme
o protocolo e registrar seus rótulos nos arquivos oficiais, com observações
nos casos necessários. As 51 pendências precisam de leitura das notas
externas/compare ou devem continuar explicitamente pendentes. Aceitar os
valores da proposta em lote não comprova julgamento independente.

O livro de códigos requer declarar ferramentas de apoio nas observações ou
na metodologia #165. O uso destas sugestões deve ser registrado como análise
assistida; não pode ser apresentado como rotulagem humana cega. A validação
final precisa conferir 60 tipos, 60 avaliações de entregas e 300 rótulos de
releases, sem ausências, duplicatas ou alterações de IDs/links. Somente então
cabe solicitar o aceite da #158. Nenhuma issue foi fechada por esta proposta.
