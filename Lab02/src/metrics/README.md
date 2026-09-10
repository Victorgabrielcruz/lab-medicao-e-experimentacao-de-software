# Coleta de métricas estáticas

O módulo `static_metrics.py` executa as ferramentas congeladas no protocolo e
consolida os resultados da RQ3. Ele aceita somente arquivos Python de produção
e rejeita automaticamente testes, dependências, código gerado, artefatos de
build e arquivos de configuração.

Cada coleta gera um diretório exclusivo em `data/raw/metrics/<trial_id>/` com:

- `radon-cc.json`: complexidade por função ou método;
- `radon-raw.json`: LOC por arquivo;
- `radon-mi.json`: índice de manutenibilidade por arquivo;
- `jscpd/jscpd-report.json`: relatório original de duplicação;
- `metrics.json`: consolidação por trial;
- `jscpd-stdout.txt`: registro operacional da execução.

Uma coleta existente nunca é sobrescrita. O campo `loc` consolidado representa
SLOC do Radon. O MI consolidado é a média aritmética dos valores por arquivo.
Quando nenhuma função ou método for detectado, os agregados de complexidade
ficam `null` e `missing` fica verdadeiro.
