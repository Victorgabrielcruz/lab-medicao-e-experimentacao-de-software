# Cronômetro e coletor de trials

O módulo `trial_collector.py` implementa o cronômetro padronizado descrito em
`Docs/methodology.md`, Seção 10.4. Ele roda a suíte de aceitação da kata em
segundo plano, em intervalos regulares, até o primeiro dos dois eventos de
encerramento:

- todos os testes passam (sucesso); ou
- o limite de **2.100 segundos** (35 minutos) é atingido (censura).

A lógica é separada em duas camadas:

- `run_trial`: cronômetro puro, sem tocar em disco. Recebe a suíte a
  executar e os relógios (`monotonic`/`sleep`/`wall_clock`) como funções
  injetáveis, o que permite testar sucesso, censura e falha inesperada sem
  esperar tempo real.
- `collect_trial`: orquestração real. Executa `pytest` via subprocesso com
  relatório JUnit, grava a saída bruta final e o registro consolidado em
  `data/raw/trials/<trial_id>/`.

Cada coleta gera:

- `final_junit.xml`: saída bruta da verificação final da suíte, executada
  uma última vez após o encerramento (Seção 10.4, item 3);
- `trial.json`: registro consolidado do trial — horários de início e fim com
  fuso, duração em segundos, `completed`/`censored`, totais de testes e o
  log de cada checagem do cronômetro (`attempts`).

O `trial_id` é gerado a partir de `participante-kata-tratamento`
(`build_trial_id`), a mesma combinação que já identifica um trial de forma
única na metodologia (Seção 2.1) — não há necessidade de um identificador
independente.

Uma coleta existente nunca é sobrescrita: se o diretório do trial já existe
— inclusive por um incidente anterior —, uma nova chamada falha em vez de
apagar o registro. Um encerramento inesperado (falha ao executar a suíte ou
interrupção manual) preserva um `incident.json` com mensagem clara em vez do
`trial.json`, para que a decisão de repetir o trial (Seção 10.5) seja
tomada por uma pessoa, não automaticamente.
