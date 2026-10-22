# RQ07 — Mudança de categoria e kappa ponderado (#174)

## Verificação de impedimentos

Em 21/10/2026, a #173 já produz três combinações para os mesmos 500 IDs,
com classes por métrica, classe geral, disponibilidade e indicadores de
qualidade. Existem 468 pares completos C1×C2 e 467 para os demais pares.
Portanto não há impedimento de dados ou de implementação para calcular a
sensibilidade. A #162 está encerrada, com relatório publicado parcial de
146/300 releases. A conferência das previsões finais locais contra o consenso
alcançou 296/300, com quatro indeterminadas, conforme o
[registro de suporte](evidencias/rq07-validacao-final-162.json).
Os pares que incluem C3 mantêm essa limitação; os quatro casos não recebem
previsões negativas nem são apresentados como validação integral.

C1 é a referência da main (#169): lead time (b) e CFR(a). C2 altera somente
o lead time para (a), e C3 altera somente CFR para (b), em relação a C1.

## Método

A análise principal usa casos com quatro métricas em ambas as combinações;
o denominador é informado por par. Mudança é qualquer classe diferente:
`100 * quantidade_de_mudanças / pares_elegíveis`. Não se usa 500 como
denominador quando há exclusões. As matrizes de transição, por métrica e
classe geral, usam a ordem fixa Low, Medium, High, Elite.

O kappa de Cohen ponderado usa pesos quadráticos de discordância
`d(i,j) = ((i-j)/3)^2`, para posições 0 a 3. Seja `O` a média dos pesos
nos pares observados e `E` a soma dos pesos multiplicados pelas proporções
marginais independentes das duas combinações. Então `kappa = 1 - O/E`.
Também se reporta peso linear `abs(i-j)/3` como análise de sensibilidade.
Sem pares ou com `E=0`, kappa é nulo, com motivo explícito. Não é kappa de
Fleiss de rotuladores, e não depende da ordem alfabética das categorias.

Quatro coortes são registradas, sem imputação:

- `completos_por_par`: quatro métricas disponíveis nas duas combinações.
- `completos_nas_tres`: mesma população completa para os três pares.
- `notas_disponiveis`: inclui notas gerais parciais permitidas pelo protocolo;
  cada métrica individual exige apenas o valor pareado dessa dimensão.
- `sem_alertas`: casos completos no par, sem coleta incompleta nem cálculo parcial.

## Resultados e robustez

| Par | Pares completos | Mudaram | Mudança | Kappa quadrático |
|---|---:|---:|---:|---:|
| C1×C2 | 468 | 68 | 14,53% | 0,8411 |
| C1×C3 | 467 | 179 | 38,33% | 0,5635 |
| C2×C3 | 467 | 197 | 42,18% | 0,4494 |

Na população comum de 467, C1×C2 passa a 14,56% e kappa 0,8394;
os outros dois pares são idênticos à análise principal. Assim, a maior
sensibilidade ao CFR não decorre somente da diferença de um caso entre
os denominadores. Excluindo alertas, as mudanças são 14,29%, 37,23% e
41,29%, com kappas 0,8367, 0,5648 e 0,4451, respectivamente.
Incluindo notas parciais nos 500, as mudanças são 16%, 37,4% e 41,6%.

A sensibilidade persiste nas verificações de disponibilidade e qualidade:
nas combinações escolhidas, trocar CFR altera mais classes gerais que
trocar apenas lead time. O kappa próximo de 0,84 para lead time ainda
acompanha dezenas de trocas de classe, por isso não substitui o percentual.
O procedimento de agregação por mediana pode ocultar diferenças individuais;
as comparações por métrica e matrizes estão nos arquivos de resultados.
Estes achados não validam CFR(b), não comprovam desempenho de produção e
não cobrem pré-releases/tags. A escrita dos resultados no artigo é a #178.

## Reprodução e validação

A partir de `Lab03`, sem token ou consultas externas:

```powershell
.venv/Scripts/python.exe -m pipeline.rq07_robustez
.venv/Scripts/python.exe -m pytest tests/test_rq07.py tests/test_rq07_robustez.py tests/test_classificacao.py tests/test_classes_dora.py
```

O comando reproduz primeiro a #173 a partir do CSV e seu manifesto;
grava `analise/rq07/robustez.csv`, `robustez.json` e `robustez.md`.
São 60 comparações: três pares, cinco dimensões e quatro coortes.
O JSON inclui matrizes, motivos de kappa não estimável e hashes do dataset
e das classificações. A saída não muda o dataset nem as rotulagens humanas.

Validação: 90 testes aprovados, incluindo concordância perfeita e inversa,
ausências, categorias constantes, identidade por ID, coortes, reprodução
byte a byte e comparação numérica independente com o kappa ponderado do
`statsmodels` para pesos quadráticos e lineares.
