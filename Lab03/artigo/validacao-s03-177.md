# Conferência dos resultados RQ05 e RQ06 — #177

Revisão de 22/10/2026, na branch `feat/conclusao-validacao-500`, a partir
da `main` `63f3933`. A entrega publicada `44a42b2` da #172 foi integrada
como dependência, pois ainda não estava na `main` no início desta revisão.

## Evidências incorporadas

- [RQ05](../analise/tabelas/rq05_spearman.csv): pares principais e sensibilidade,
  rho, p bilateral assintótico, p por permutação e n para CFR(a)/(b).
- [Figura RQ05](../analise/figuras/rq05_df_cfr_spearman.png), com frequência
  em log, sem transformar a CFR ou mudar os pares usados no teste.
- [Cortes RQ06](../analise/tabelas/rq06_cortes.csv): três fatores em quartis,
  com 125 projetos por grupo antes da exclusão de métricas ausentes.
- [Globais com Holm](../analise/tabelas/rq06_holm_globais.csv): todos os 18
  testes e ε²=H/(n−1), incluindo os não rejeitados.
- [Pares com Holm](../analise/tabelas/rq06_holm_pares.csv): todos os 108
  contrastes e deltas; 27 passam pelo par e pelo global corrigidos. O artigo
  detalha os sete contrastes Q1–Q4 desse conjunto, com sinal e magnitude.

A família de Holm global tem 18 hipóteses; a de pares, 108. Não são os 48
pós-testes inicialmente selecionados por p bruto. Mantêm-se sete globais
após correção, frente a oito nominais. Spearman é reportado sem ajuste;
suas duas variantes não fazem parte dessas famílias da RQ06.

## Reprodução e integridade

Os notebooks #170, #171 e #172 foram reexecutados integralmente em kernel
Python 3.14.3, lendo o CSV final e gravando em pastas temporárias. **Todos
os CSVs produzidos são idênticos, byte a byte, aos publicados.** As saídas
oficiais e os notebooks versionados foram preservados. Os comandos e as
variáveis de saída estão documentados em [analise/README.md](../analise/README.md).

O CSV final não foi alterado. A recuperação independente dos pacotes de
releases e compare confirmou os valores de CFR(b) dos 500: 498 estimáveis
e dois nulos, zero divergências a 1e-12. Isso permite usar as tabelas
existentes sem recalcular ou substituir os resultados por uma base diferente.

A suíte dos arquivos de teste oficiais aprovou **1.169 testes e ignorou dois**,
com **94,80% de cobertura**, acima dos 80% da CI. Duas cópias locais alheias
à entrega (`comparacao_rq06 2.py` e seu teste) ficaram fora dessa medição;
foram preservadas, sem staging. Não se afirma execução da CI remota.

O artigo completo compilou **com sucesso** no compilador nativo do editor,
com raiz `Lab03` e documento principal `artigo/main.tex`. A raiz contém
as figuras em `analise/figuras`; compilar com acesso limitado apenas a
`artigo` não permite carregar essas imagens. Não houve exportação ou
sincronização do Overleaf. A confirmação de compilação não equivale a uma
nova inspeção visual de todas as páginas do PDF.

## Alcance das alterações

Resultados, método dos testes e discussão foram atualizados com as fontes
acima. Resumos e conclusão, que ainda descreviam o piloto de 82 projetos,
foram alinhados à amostra final. As hipóteses originais foram preservadas;
a referência antiga do README à hipótese por idade foi corrigida para
corresponder ao texto registrado (tipo de projeto). Idade é fator adicional,
e não se afirma que o tipo foi comparado entre os 500.

A RQ07 permanece em entrega própria. Os limites de proxies, censura,
completude, origem da amostra-ouro e independência da rotulagem continuam
explícitos. Nenhuma issue foi fechada automaticamente.
