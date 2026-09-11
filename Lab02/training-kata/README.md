# Kata de treinamento — Decodificação por repetição

Exercício curto reservado à familiarização com ambiente, testes, cronômetro e
regras dos tratamentos. Ele não pertence à amostra K01–K06 e seus resultados
devem ser gravados em `data/training/`, nunca no dataset oficial.

## Problema

Uma mensagem compactada é representada por uma lista de blocos
`(texto, repeticoes)`. Expanda os blocos na ordem recebida, repetindo cada
texto a quantidade indicada.

Implemente:

```python
def expandir_mensagem(blocos: list[tuple[str, int]]) -> str:
```

Regras:

- a lista vazia resulta em uma string vazia;
- `texto` deve ser uma string não vazia;
- `repeticoes` deve ser um inteiro entre 0 e 20, inclusive;
- repetição zero não acrescenta conteúdo;
- bloco inválido deve lançar `ValueError`;
- valores booleanos não são quantidades válidas, embora `bool` derive de
  `int` em Python.

Exemplos:

```python
expandir_mensagem([("ab", 2), ("!", 3)]) == "abab!!!"
expandir_mensagem([("x", 0), ("fim", 1)]) == "fim"
```

O problema exercita leitura de contrato, edição, casos de borda e execução do
pytest, mas não reutiliza docas, compartimentos, remessas, credenciais,
sensores ou roteiros das katas experimentais.
