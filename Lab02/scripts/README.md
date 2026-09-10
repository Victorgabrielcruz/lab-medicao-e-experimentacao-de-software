# Scripts

Pontos de entrada previstos:

- preparação e restauração do ambiente;
- geração da alocação contrabalanceada;
- execução cronometrada de trials;
- execução padronizada dos testes;
- coleta de métricas estáticas;
- construção e validação do dataset;
- análise estatística e geração do dashboard.

Os scripts devem apenas orquestrar regras implementadas e testadas em `src/` sempre que a lógica ultrapassar uma operação simples.

## `run_tests.py` (S01-04)

Execução padronizada dos testes de aceitação de uma kata:

```bash
python scripts/run_tests.py K01
```

Por padrão testa `katas/K01/src/`. Para validar a suíte contra a solução de
referência (uso interno da equipe, nunca durante um trial):

```bash
python scripts/run_tests.py K01 --src reference-solutions/K01
```

Gera um relatório JUnit XML em `.reports/<KATA>_junit.xml` (ignorado pelo
git) e imprime total de testes, quantos passaram e quantos falharam. Roda
sempre uma kata por vez, em processo isolado — não colete testes de várias
katas no mesmo comando `pytest`, porque todas usam o nome de módulo
`solution` e um processo só resolveria o primeiro que importar.
