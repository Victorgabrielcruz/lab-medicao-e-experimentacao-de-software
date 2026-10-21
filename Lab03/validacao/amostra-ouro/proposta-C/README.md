# Proposta de preenchimento C — revisão da #158

Esta pasta contém **sugestões de análise**. Não é uma
rotulagem humana independente e não conclui a #158. Na preparação desta
proposta, as duas planilhas oficiais estavam em branco. Posteriormente, o
responsável declarou ter conferido os 60 projetos e 249 releases e solicitou
a transferência: os valores conferidos estão nos arquivos oficiais, enquanto
os 51 casos não decididos continuam vazios. Os arquivos desta pasta preservam
a proposta original e não devem entrar como rótulos
de consenso, referência de avaliação ou observações independentes no Kappa.

## Material preparado

- `proposta_C_repositorios.csv`: 60 sugestões de tipo de projeto e de uso das
  releases como entregas, todas com observações. São hipóteses baseadas nas
  descrições públicas cacheadas e nas notas de releases. O responsável informou
  sua conferência antes da transferência para os arquivos oficiais.
- `proposta_C_releases.csv`: mesmas 300 releases do sorteio oficial, com 207
  sugestões `sim`, 42 `nao` e 51 células de julgamento vazias por evidência
  insuficiente. Todas têm observações; as sugestões `sim` incluem um trecho
  das notas que motivou a interpretação.
- `evidencias.json`: origem, hashes, decisões propostas e fontes textuais.
- `validacao.json`: contagens, IDs únicos, colunas fixas e hashes dos CSVs na
  preparação da proposta, quando os oficiais ainda estavam em branco. A
  transferência posterior está documentada em
  [158-transferencia-c.json](../../../docs/evidencias/158-transferencia-c.json).

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

Os 60 projetos e os 249 rótulos conferidos foram transferidos para os arquivos
oficiais, com referência ao apoio desta proposta nas observações. Os CSVs desta
pasta não mudaram: mantêm a versão que o responsável informou ter conferido.

Falta julgar os 51 casos em branco, a partir das notas externas/changelog ou
compare, e validar os 300 rótulos completos. Até isso ocorrer, o resultado é
parcial e as ausências não podem ser tratadas como `nao`. O protocolo de
independência entre integrantes e a declaração de ferramentas de apoio
continuam aplicáveis; a revisão informada não foi apresentada como cega.
Nenhuma issue foi fechada por esta transferência.
