# Rotulagem independente C — #158

## Situação da população e dependência

A extração foi encerrada por instrução humana em 15/10/2026, às 18:09:11 UTC,
com **255 repositórios elegíveis** entre 561 candidatos avaliados. A meta
anterior de 500 e o marco de 300 não impedem trabalhar com essa população
encerrada. A decisão local é `data/processed/sprint02-agentes/encerramento-amostra.json`;
o snapshot é `data/raw/amostra-encerrada-255-20261015T180911Z/`.

Esta preparação aguarda o **sorteio oficial da #155**. Não foi encontrado
`amostra_ouro.json` em `Lab03/validacao/` ou `Lab03/data/processed/` na verificação
registrada na [evidência](evidencias/158-preparacao-c.json). Não há planilhas C
publicadas ou rótulos preenchidos por esta entrega. A consolidação offline da
população e o sorteio oficial são etapas distintas.

## Receber o instrumento oficial

O protocolo existente em [pipeline/amostra_ouro.py](../pipeline/amostra_ouro.py)
usa 60 repositórios, 5 releases por repositório e `random_state=42`, sem reposição.
A #155 deve aplicar esse protocolo à população encerrada de 255, preservando
seu manifesto oficial. A #158 não executa um segundo sorteio.

Antes de preparar ou reutilizar C, conferir no manifesto:

- `total_populacao=255` e `populacao_sha256` correspondente aos IDs completos
  da população encerrada, ordenados numericamente e serializados por
  `json.dumps(ids)` antes do SHA-256, conforme o gerador existente;
- janela `[2025-10-01T00:00:00Z, 2026-10-01T00:00:00Z)`,
  `random_state=42` e `incluir_prereleases=false`;
- 60 `repo_id` distintos pertencentes à população e 5 releases distintas
  por repositório, totalizando 300 pares `(repo_id, release_id)`;
- nomes, IDs, datas, tags e links coerentes com o manifesto e as entradas
  locais consolidadas; releases estáveis, publicadas na janela e sem drafts;
- hashes das entradas e do manifesto iguais antes e depois da leitura.

Reutilizar somente `rotulador_C_repositorios.csv` e
`rotulador_C_releases.csv` vinculados ao sorteio oficial. Se C ainda não existir,
preparar apenas C a partir dos IDs oficiais, sem sortear novamente e sem usar
`--sobrescrever`. O gerador geral cria também A/B: ele não deve ser chamado
pela #158 para contornar a dependência. Preservar qualquer preenchimento já
existente; divergências de identidade exigem revisão, nunca substituição silenciosa.

## Preenchimento pelo responsável C

Trabalhar individualmente, sem consultar planilhas A/B, avaliações dos demais
integrantes ou resultados da heurística CFR(b). O agente não substitui o
julgamento do responsável. Usar o material já disponível e os links de apoio
para leitura humana; esta entrega não autoriza nova extração por API.

Na planilha de repositórios, manter `repo_id`, `full_name`, `repositorio_url`
e `releases_url`. Preencher:

| Campo | Orientação |
|---|---|
| `tipo_projeto` | Descrever a função principal com evidência do README/documentação. Usar o catálogo do instrumento oficial, quando fornecido; não converter dúvidas em uma classe arbitrária. Registrar casos híbridos ou categoria indefinida em observações. |
| `releases_sao_entregas_reais` | Julgar se as releases representam versões/entregas do software estudado. Distinguir publicação de conteúdo ou marcação administrativa quando a evidência permitir. Registrar a justificativa. |
| `observacoes` | Registrar evidência consultada, justificativa, limitações e dúvidas. Não copiar o julgamento de outro rotulador. |

Na planilha de releases, manter `repo_id`, `full_name`, `release_id`, `tag_name`,
`nome`, `published_at`, `release_url` e `compare_url`. Preencher:

| Campo | Orientação |
|---|---|
| `corretiva` | Julgar se a release inclui correção de defeito, usando as notas e o compare. Não inferir apenas por número de versão, palavra-chave ou resultado automático. Documentar o raciocínio em releases mistas ou ambíguas. |
| `observacoes` | Registrar trechos/referências de evidência e incertezas. Um compare ausente pode ocorrer para a primeira release elegível e não significa ausência de correções. |

Nos campos de decisão binária, seguir a codificação do instrumento oficial;
na ausência de uma codificação definida, usar `sim` e `nao` de forma consistente,
sem transformar célula vazia em `nao`. Quando a evidência for insuficiente,
deixar a decisão pendente e explicar nas observações. Não forçar consenso
antes da conclusão independente. A taxonomia de `tipo_projeto`, se ainda não
fixada pela #155, precisa ser confirmada no instrumento antes da validação final.

Salvar os CSVs preservando UTF-8 com BOM, cabeçalhos, IDs e links. Editar
somente colunas de julgamento e observações. Guardar uma cópia da versão
recebida e registrar hashes antes e depois do preenchimento, sem apagar a original.

## Validação depois do preenchimento

Conferir igualdade exata dos conjuntos de IDs com o sorteio oficial, sem IDs
extras, omissões ou duplicatas. Exigir 60 classificações de `tipo_projeto`,
60 decisões de `releases_sao_entregas_reais` e 300 decisões de `corretiva`,
com exatamente 5 releases de cada repositório. Verificar também que as colunas
fixas não foram alteradas e que os valores pertencem ao catálogo/codificação
acordado. Células vazias, dúvidas sem decisão e valores inválidos continuam
pendências explícitas; não são negativos e não contam como julgamento completo.

Somente após receber e validar os rótulos independentes é possível demonstrar
a entrega da #158. A preparação documental não conclui a issue. Enquanto o
sorteio oficial estiver ausente, o acompanhamento permanece ativo e silencioso;
quando faltar apenas o preenchimento humano, informar uma vez e pausar em
`aguardando_rotulagem_humana`, preservando os arquivos para retomada autorizada.
A CFR(b) continua pendente da #161 e de sua validação, sem valores fabricados.
