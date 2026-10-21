# Replicação do pipeline do grupo parceiro — FIN-01 (#180)

Execução do pipeline de mineração de métricas DORA do grupo de Matheus, Pedro e
Murilo seguindo **apenas o README** do Lab03 deles, com 30 repositórios.

- Repositório: <https://github.com/matheustitton/lab-medicao-experimentacao-6-periodo>,
  pasta `lab03-metricas-dora`, commit `9ba34433f7b0243d1bcca9d130f2dd58b67ed841`.
- Ambiente: Windows 11, Git Bash, Python 3.13.6, venv novo com o
  `requirements.txt` deles (pandas 3.0.6, PyYAML 6.0.3, requests 2.34.2,
  scikit-learn 1.9.1, statsmodels 0.15.0).
- Janela do `config.yaml` sem alteração: 2025-10-01 a 2026-09-30, igual à nossa.
- Token: `GITHUB_TOKEN` de uma conta própria, via `gh auth token`.

## Comandos executados

A partir de `lab03-metricas-dora`:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
GITHUB_TOKEN="$(gh auth token)" .venv/Scripts/python -m pipeline --config config.yaml --limite 30
```

A execução foi interrompida pelo replicador às 18h45 (3/30 incluídos) e
retomada às 19h40 com o mesmo comando. A retomada funcionou como o README
descreve: a busca não foi repetida e a coleta continuou do estado salvo.
O comando terminou com código 0 às 20h38. Tempo efetivo de execução: cerca de
77 minutos (19 antes da pausa e 58 depois), dos quais 5 na busca de candidatos.

## Resultado

- 30 repositórios incluídos, 28 deles presentes no dataset publicado pelo grupo
  (237 linhas). `itchio/itch` e `n00bcodr/Jellyfin-Enhanced` não aparecem lá.
- Funil: 8.505 candidatos; 185 avaliados (58 sem Actions, 88 com releases
  insuficientes, 9 com runs insuficientes) e 30 incluídos.
- Arquivos desta pasta: `dataset_dora.csv` (30 linhas, 37 colunas),
  `funil_selecao.md`, `dicionario_dados.csv` e o log completo
  `execucao-30.log`, com as duas execuções.

## Problemas encontrados

| # | Comando | Mensagem ou sintoma | Contorno |
|---|---|---|---|
| 1 | `source .venv/bin/activate` | `bash: .venv/bin/activate: No such file or directory` | No Windows o venv cria `.venv/Scripts/`; usamos `.venv/Scripts/python` diretamente. O README também usa `export`, que não existe no PowerShell. |
| 2 | `python -m pipeline --config config.yaml --limite 30` | O log fica vários minutos sem nenhuma linha durante a coleta de repositórios grandes; o maior intervalo foi de 17 minutos (20h07 a 20h25). Parece travado. | Conferir se o processo está ativo e se `data/cache.sqlite` continua sendo gravado. |
| 3 | (README) | O README não informa o tempo esperado nem o consumo de API da execução. | — |
| 4 | `python -m pipeline ...` | A tabela do funil passa de 8.505 candidatos para 127 que usam GitHub Actions, sem uma linha de avaliados. Os 8.320 candidatos não processados aparecem como se tivessem sido descartados; os motivos somam 155 (185 avaliados − 30 incluídos). | Ler os motivos de descarte para reconstruir a etapa de avaliados. |
| 5 | `python -m pipeline ...` | No console do Windows, o funil impresso mostra `≥ 5 releases na janela` e `Reposit�rios`. O `funil_selecao.md` gravado está correto. | Cosmético; usar o arquivo gravado. |
| 6 | `python -m pipeline ...` | A execução sobrescreve `data/saida/dataset_dora.csv` e `data/saida/funil_selecao.md`, que estão versionados no repositório deles; o README não avisa. | Copiar `data/saida/` antes de rodar, para comparar com os resultados publicados. |

Itens para a comparação (#181): o dataset publicado tem 237 repositórios,
abaixo do mínimo de 300 e do `alvo_amostra: 350` do `config.yaml`; e dois dos
30 repositórios replicados não estão nele, embora a ordem dos candidatos use
semente fixa (`semente: 42`).
