# Renomeações durante a coleta final — #151

A coleta parou em 14/10/2026 às 19h09 (Brasília), com 347 candidatos
avaliados e 160 elegíveis. A fonte identificava `pathwaycom/llm-app`, mas
os metadados retornados pela API informavam `pathwaycom/serviette`.
Ambos tinham o ID `668195240`. A validação exigia ID e nome iguais e
interrompia a execução repetidamente.

A integração aceita mudança de nome ou organização somente quando o ID
numérico coincide. Mantém `full_name` da fonte em todas as etapas para
preservar a consistência dos joins, da seleção e dos checkpoints; registra
`full_name_atual` nos metadados e `renomeacao` no checkpoint, além de um
aviso no log. As consultas continuam pelo caminho da fonte, cujo retorno
de metadados já demonstrou o redirecionamento nesta ocorrência.

IDs diferentes continuam sendo rejeitados, agora com identificação do
repositório e dos IDs esperado/recebido no erro. Não se altera a fonte,
a janela, os critérios de inclusão ou os checkpoints anteriores.
O GitHub ainda pode remover redirecionamentos; falhas de acesso continuam
seguindo o tratamento de HTTP existente.

A validação cobre renomeação e transferência de organização, pipeline
completo com fontes sintéticas, retomada sem API e sem reescrever o
checkpoint, preservação da fonte e rejeição de ID diferente.


Validação em 15/10/2026: **78 testes passaram** em `tests/test_integrado.py`.
Comando reproduzível no ambiente com as dependências instaladas:

```powershell
python -m pytest tests/test_integrado.py -q
```

A correção foi preparada em `feat/correcao-renomeacao-151`. Sua publicação
não altera os coletores atuais: para ativá-la, o supervisor local precisa
usar o Lab03 deste checkout e registrar o commit correto, retomando a mesma
fonte, configuração e pasta de checkpoints.
