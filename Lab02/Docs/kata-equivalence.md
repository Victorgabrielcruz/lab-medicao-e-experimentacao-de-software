# Equivalência das katas experimentais

**Task:** S01-03 — Formar e validar os pares de dificuldade  
**Data da avaliação:** 10/09/2026  
**Método:** inspeção independente substitutiva prevista na Seção 7.4 de
`methodology.md`

## 1. Método de avaliação

Como não foi disponibilizado um piloto externo nesta etapa, os pares foram
avaliados antes da alocação por critérios observáveis e reproduzíveis:

- quantidade de regras operacionais no enunciado;
- estruturas e estado necessários para resolver o problema;
- quantidade de testes de aceitação e casos além do exemplo;
- SLOC da solução de referência, medido pelo Radon 6.0.1;
- complexidade ciclomática média e máxima;
- faixa de tempo estimada durante a seleção das katas.

As seis soluções passaram em 33 de 33 testes. As métricas foram coletadas pelo
pipeline da S01-06 e estão preservadas em
`data/metadata/static-metrics-sanity.json`. A matriz completa e legível por
máquina está em `data/metadata/kata-equivalence.csv`.

## 2. Matriz objetiva

| Bloco | Kata | Regras | Testes | Casos além do exemplo | SLOC | CC média | CC máxima | Tempo estimado |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| B1 | K01 | 6 | 6 | 5 | 24 | 5,0 | 9 | 20–30 min |
| B1 | K02 | 7 | 5 | 4 | 26 | 7,0 | 7 | 15–25 min |
| B2 | K03 | 7 | 6 | 5 | 22 | 7,0 | 7 | 15–25 min |
| B2 | K04 | 8 | 6 | 5 | 30 | 7,0 | 7 | 20–30 min |
| B3 | K05 | 8 | 5 | 4 | 22 | 8,0 | 8 | 15–25 min |
| B3 | K06 | 6 | 5 | 4 | 30 | 10,0 | 10 | 15–25 min |

Todas as katas usam dados em memória, estado separado por identificador e uma
única função pública principal. As referências têm entre 22 e 30 SLOC, de 5 a
6 testes e complexidade máxima entre 7 e 10. Nenhuma diferença observada
indica uma classe distinta de dificuldade ou incompatibilidade com o limite de
35 minutos.

## 3. Pares validados

### B1 — K01 e K02

As duas exigem processar coleções pequenas e manter separação por recurso.
K01 possui comparação de intervalos e CC máxima dois pontos maior; K02 possui
uma regra operacional adicional e dois SLOC a mais. As faixas de tempo se
sobrepõem entre 20 e 25 minutos. O par foi considerado equivalente.

### B2 — K03 e K04

As duas implementam máquinas de estado sobre eventos intercalados, têm seis
testes e CC máxima 7. K04 possui oito SLOC e uma regra a mais por incluir
expiração temporal; sua faixa estimada começa cinco minutos acima. A diferença
é residual e não altera a classe de dificuldade.

### B3 — K05 e K06

As duas acompanham progresso independente em sequências intercaladas e têm
cinco testes e a mesma faixa de 15–25 minutos. K06 possui oito SLOC a mais e CC
máxima 10; K05 compensa parcialmente com regras de limiar, reinício e bloqueio
de alertas repetidos. O par foi considerado equivalente, com K06 ligeiramente
mais complexa estruturalmente.

## 4. Limitações

- A equivalência foi baseada em inspeção e soluções de referência, não em
  tempos observados de um piloto humano externo.
- LOC e complexidade descrevem uma implementação correta possível, mas não
  todas as estratégias que os participantes podem escolher.
- Os pares não são idênticos: K01 enfatiza intervalos, K04 acrescenta tempo e
  K06 apresentou a maior CC máxima.
- Com apenas três participantes, diferenças residuais podem influenciar os
  resultados; por isso cada bloco será usado com os dois tratamentos e a
  alocação deverá ser contrabalanceada.

## 5. Custódia das soluções de referência

Os arquivos `reference-solutions/KXX/solution.py` permanecem somente na
máquina do responsável pela preparação e são ignorados pelo Git. O repositório
compartilhado contém apenas hashes SHA-256 e resultados de validação, que não
revelam as implementações.

Antes dos trials, cada participante deve trabalhar em um clone limpo do
repositório compartilhado. O responsável pela preparação deverá confirmar que
`git ls-files "reference-solutions/**/*.py"` não retorna arquivos e que o clone
do participante não contém implementações de referência. A publicação das
soluções só poderá ocorrer depois do encerramento dos 18 trials.

## 6. Conclusão

Ficam validados e congelados os pares **B1 = K01/K02**, **B2 = K03/K04** e
**B3 = K05/K06**. As diferenças residuais estão documentadas e devem ser
consideradas na interpretação dos resultados.
