# Conclusão das pendências com as fontes finais dos 500

Revisão de 22/10/2026, branch `feat/conclusao-validacao-500`, criada a partir
da `main` atualizada em `63f3933`. Escopo: entregas anteriores que dependiam
dos detalhes finais por release, e seu relato no artigo. A #172 já publicada
na branch anterior foi integrada como dependência dos resultados da #177.

| Issue | Entrega nesta revisão | Limite preservado |
|---|---|---|
| #161 | CFR(b) completo e comprimido: 500 projetos, 34.255 releases; 498 valores estimáveis, dois nulos; agregados iguais ao CSV final. | Regra v1 preservada; 95 classificações indeterminadas no universo completo. |
| #162 | Avaliação contra o consenso em 296/300 pares; precisão, recall, F1 e matriz publicados; 150 das 154 antigas lacunas resolvidas. | Quatro primeiras releases sem predecessora não recebem previsão artificial. |
| #163 | Histórico atualizado e decisão de manter v1 sem refinar: F1=0,933078; pior conclusão binária das quatro lacunas daria 0,925996. | Limites condicionais não são F1 observado nas 300 nem validação independente. |
| #165 | Amostra, instrumento aplicado, Fleiss, consenso, avaliação e procedimento real reportados. | Independência e cronologia das três rotulagens não inteiramente comprovadas; definição humana mais ampla que objetivo principal corretivo. |
| #177 | Resultados RQ05/RQ06 com rho/p/n, dispersão, Holm e tamanhos de efeito, a partir das #170–172. | Idade é fator adicional; tipo de projeto não foi testado para os 500. RQ07 tem entrega própria. |

A execução dos **500** foi concluída sem novas consultas à API. Isso não
significa rotular manualmente suas 34.255 releases: o consenso oficial cobre
300 pares de 60 projetos, sorteados sobre os 255 primeiros elegíveis.
Não se alterou esse sorteio, as seis planilhas, decisões humanas, códigos
ou resultados históricos. Os limites do procedimento humano não podem ser
corrigidos retrospectivamente por uma execução de software.

## Verificação

- Partes e arquivos utilizados dos pacotes conferidos por tamanho/SHA-256.
- Restauração real do CFR(b) comprimido com hash idêntico ao original.
- Reavaliação a partir do arquivo restaurado: mesmos resultados e pares.
- Kappa e consenso reproduzidos integralmente em pastas temporárias.
- Três notebooks executados em kernel novo: todos os CSVs idênticos.
- 1.169 testes passaram, dois foram ignorados; cobertura 94,80% dos módulos
  do projeto, preservando e excluindo as cópias locais alheias com sufixo ` 2.py`.
- Artigo completo compilado no editor nativo, com raiz `Lab03`.

Os comandos de reprodução e os hashes estão no
[relatório final da #162](../validacao/avaliacao-heuristica/final-500/README.md).
A conferência do artigo está em [#165](../artigo/validacao-s02-165.md) e
[#177](../artigo/validacao-s03-177.md). Nenhuma issue foi encerrada e nenhuma
PR nova foi criada automaticamente.
