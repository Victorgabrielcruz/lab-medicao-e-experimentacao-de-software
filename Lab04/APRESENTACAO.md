# Roteiro da apresentação oral do Lab04

Use o próprio dashboard durante a apresentação. Os títulos abaixo seguem as 15 perguntas da seção 5 do enunciado.

| Tempo acumulado | Quem fala | Conteúdo |
|---|---|---|
| 0:00–0:10 | Victor | Abrir na seção 1 e apresentar o par de testes. |
| 0:10–2:10 | Victor | Perguntas 1–5. |
| 2:10–2:20 | Equipe | Passar a fala e posicionar o G2. |
| 2:20–4:20 | Matheus | Perguntas 6–10. |
| 4:20–4:30 | Equipe | Passar a fala e posicionar a análise da Q3. |
| 4:30–6:30 | Jonatha | Perguntas 11–15. |
| 6:30–6:40 | Jonatha | Encerrar. |

Cada integrante fica com cinco perguntas. A meta é de cerca de 24 segundos por resposta, com 20 segundos de margem até o limite de 7 minutos.

## Victor · Perguntas 1–5

### 1. Cenário e hipóteses · Seção 1

Investigamos se o workflow de testes do pytest falha em mais de 5% das execuções de CI. A hipótese nula, H₀, fixa a taxa em 5%. A alternativa, H₁, diz que a taxa está acima desse teto.

### 2. Direção do teste · Seção 1

O teste é unicaudal à direita porque queremos detectar um aumento acima de 5%. Uma contagem alta de falhas favorece a hipótese alternativa. Uma taxa abaixo da meta não gera o alerta que estamos investigando.

### 3. Coleta e forma dos dados · Seção 2, G1

Inspecionamos 300 execuções consecutivas do workflow `test` do pytest, na `main`, disparadas por push. Excluímos 57 cancelamentos. Das 243 válidas, 10 falharam. O G1 tem duas categorias, sucesso e falha, com forte concentração em sucessos. A ordem temporal revelou uma sequência de três falhas.

### 4. Parâmetros da simulação · Seções 1 e 2

O resultado binário motivou o modelo de Bernoulli. Usamos as 243 execuções válidas como tamanho de referência e a autocorrelação de lag 1, de aproximadamente 0,27, para calibrar as rajadas. Sob H₀, a taxa da simulação é a meta de 5%. A taxa observada foi 4,12%.

### 5. O que os testes comparam · Seção 3

Os dois comparam a proporção de builds que falharam com 5%. O Z padroniza a diferença usando o erro padrão sob H₀ e usa a aproximação normal. O binomial exato calcula, sob H₀, a chance de observar pelo menos o número de falhas da amostra.

## Matheus · Perguntas 6–10

### 6. Distribuições e regiões de rejeição · Seção 3, G2

O G2 mostra a normal padrão como aproximação para o Z e as probabilidades discretas da contagem binomial, exibida como proporção. As regiões de rejeição ficam à direita porque contagens grandes favorecem H₁. Para 243 builds, o binomial exato começa a rejeitar em 19 falhas.

### 7. Interpretação do p-valor · Seção 3, G2

No exemplo de 17 falhas, os p-valores são 7,67% e 10,40%. Eles medem, sob H₀ e os pressupostos de cada teste, a probabilidade de um resultado pelo menos tão alto quanto o observado. A probabilidade de H₀ ser verdadeira não é estimada pelo p-valor.

### 8. Erros tipo I e II · Seções 4 e 5

Erro tipo I é disparar um alerta quando a taxa está na meta. Erro tipo II é deixar passar uma taxa acima dela. Neste cenário, priorizamos evitar alertas falsos que poderiam acionar uma investigação desnecessária. Se falhas não detectadas tiverem custo maior, o erro tipo II ganha peso.

### 9. Calibração do erro tipo I · Seção 4, G3

Com builds independentes, o Z foi liberal, com 6,55%, e o binomial exato foi conservador, com 3,96%. A aproximação normal leva o Z a rejeitar a partir de 18 falhas. O binomial só rejeita a partir de 19, por causa da contagem discreta.

### 10. Poder por tamanho de efeito · Seção 5, G4

O Z teve maior proporção de rejeições em todos os efeitos positivos simulados. Com builds independentes e efeito de quatro pontos, o poder foi de 83,40% contra 76,73%. Em dez pontos, os dois chegaram perto de 100%. O Z também teve mais falsos positivos.

## Jonatha · Perguntas 11–15

### 11. Violações de pressupostos · Seção 5, Q3, e G3

Simulamos amostra pequena e rajadas. Com 20 builds, esperamos uma falha sob H₀, o que prejudica a aproximação normal do Z. Em rajadas, a dependência entre builds aumenta a variância da contagem. Os dois testes passam de 5% de falsos positivos.

### 12. Efeito de reduzir α para 1% · Seções 4 e 5, G3 e G4

No G3, a linha nominal iria para 1% e as taxas de falsos positivos poderiam cair. No G4, o corte mais rígido também reduziria ou manteria o poder em cada ponto. Na simulação independente com efeito de quatro pontos, o poder caiu para 60,31% no Z e 51,70% no exato.

### 13. Expectativa e resultado · Seções 1, 4 e 5

O binomial ficou conservador sob independência, sobretudo com amostra pequena, como esperávamos. O Z detectou mais aumentos, mas também passou de 5% de falsos positivos, inclusive com 243 builds independentes. Nas rajadas, a dependência deixou os dois testes liberais.

### 14. Aplicação aos dados reais · Seção 6

Os dois testes mantiveram H₀ sem rejeição. Observamos 10 falhas em 243 builds, cerca de 0,88 ponto percentual abaixo da meta. A diferença equivale a pouco menos de uma falha por 100 execuções. Seu impacto depende do volume de builds e do custo de cada falha.

### 15. Recomendação e limitação · Seções 5, 6 e 7

Com builds independentes, recomendamos o binomial exato para priorizar o controle de falsos positivos. Com amostra grande e boa calibração sob H₀, poderíamos considerar o Z. Se houver rajadas, é preciso considerar a dependência. A principal limitação é ter uma única série de CI, com poucas falhas para estimar essa dependência.

## Conferência da pergunta 12

Os valores de 1% foram recalculados com `simular_configuracao` usando as mesmas configurações, índices, semente 42 e 10.000 repetições por configuração. A tabela mostra a mudança nas taxas estimadas da situação independente com 243 builds. Os gráficos atuais usam α de 5%.

| Medida | Z a 5% | Z a 1% | Binomial a 5% | Binomial a 1% |
|---|---:|---:|---:|---:|
| Erro tipo I, efeito zero (G3) | 6,55% | 1,18% | 3,96% | 0,66% |
| Poder, efeito de +4 p.p. (G4) | 83,40% | 60,31% | 76,73% | 51,70% |
