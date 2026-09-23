# Guia operacional do ambiente e dos trials

Este é o procedimento obrigatório da S01-08. Execute os comandos no PowerShell,
a partir da raiz do repositório. Não inicie um trial oficial enquanto o
ambiente, o tratamento e a combinação participante/kata não estiverem válidos.

## 1. Pré-requisitos

- Windows com `winget` disponível;
- acesso às contas necessárias para VS Code e Codex CLI;
- clone limpo sem `reference-solutions/K01` a `K06` na máquina participante;
- identificação anonimizada correta: P01, P02 ou P03.

As versões normativas estão em `data/metadata/protocol.json` e são verificadas
automaticamente. Não aceite atualização automática durante a janela de coleta.

## 2. Instalação e verificação a partir do zero

Na primeira preparação da máquina, abra PowerShell e execute, trocando P01 pela
identificação correta:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01 -InstallSystemTools
```

O parâmetro `-InstallSystemTools` instala as versões congeladas de uv, Node.js,
VS Code e Codex CLI, instala as extensões Python/Pylance de baseline, cria `.venv`, sincroniza
`requirements.lock` e executa a validação. Se as ferramentas de sistema já
estiverem instaladas nas versões corretas, omita o parâmetro:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01
```

Para somente reverificar uma máquina já preparada:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01 -VerifyOnly
```

O comando deve terminar sem erro e registrar a máquina em
`data/metadata/environment.json`. Ele também executa:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe scripts\generate_allocation.py --check
```

Cada participante executa o setup na própria máquina. A S01-08 só está
operacionalmente validada quando P01, P02 e P03 possuem registros reais e o
campo `status` do JSON é `verified`. Um registro existente não é substituído
sem `--replace`; qualquer troca de máquina ou versão deve ser registrada como
desvio antes da substituição.

## 3. Conferência do clone participante

Antes da primeira coleta, confirme:

```powershell
Test-Path reference-solutions\K01
git status --short
```

O primeiro comando deve retornar `False`. O segundo não deve apresentar
alterações desconhecidas. As referências ficam apenas com o custodiante.

## 4. Kata de treinamento

A kata de treinamento é “Decodificação por repetição” e não reutiliza nenhum
problema de K01–K06. Prepare uma cópia fora do esqueleto versionado:

```powershell
$trainingDir = "data\training\P01"
New-Item -ItemType Directory -Path $trainingDir
Copy-Item -Recurse training-kata\src "$trainingDir\src"
$env:KATA_SRC_DIR = (Resolve-Path "$trainingDir\src")
.venv\Scripts\python.exe -m pytest training-kata\tests -q
Remove-Item Env:KATA_SRC_DIR
```

O esqueleto deve falhar inicialmente com `NotImplementedError`. O participante
implementa `data/training/P01/src/solution.py`, aprende a executar os testes e
repete o fluxo de tratamento/cronômetro. Os dados permanecem em
`data/training/` e nunca recebem `trial_id` oficial.

## 5. Preparação de um trial oficial

O custodiante consulta a próxima linha de `allocation.csv` e revela somente
essa linha. Para o exemplo P01/K01/ai:

```powershell
.venv\Scripts\python.exe scripts\prepare_trial.py P01 K01 ai
```

O comando valida a combinação contra a alocação congelada e cria:

```text
trials/P01-K01-ai/
|-- README.md
|-- src/solution.py
`-- trial-config.json
```

Se for necessário limpar uma tentativa de preparação antes de iniciar o
cronômetro:

```powershell
.venv\Scripts\python.exe scripts\prepare_trial.py P01 K01 ai --restore
```

`--restore` elimina resíduos somente do diretório exato daquele trial. O
comando é recusado se `data/raw/trials/P01-K01-ai/` já existir; após o início
da coleta, nada pode ser restaurado ou sobrescrito.

## 6. Verificação do tratamento

Desde 15/09/2026 (`protocol-decisions.md`, Seção 3), qualquer extensão do
VS Code é permitida — só as de IA generativa continuam proibidas. Feche o
Codex CLI e qualquer chatbot ou autocomplete generativo antes de verificar.

Tratamento IA:

```powershell
.venv\Scripts\python.exe scripts\verify_treatment.py ai --trial-dir trials\P01-K01-ai
```

O Codex CLI 0.154.0 deve estar disponível. Extensões de IA generativa
(Copilot, Copilot Chat, Tabnine, Codeium, Continue ou equivalente) causam
falha; qualquer outra extensão é aceita.

Tratamento Manual:

```powershell
.venv\Scripts\python.exe scripts\verify_treatment.py manual --trial-dir trials\P01-K01-manual --confirm-manual-no-ai
```

Antes de usar `--confirm-manual-no-ai`, feche o Codex e confirme visualmente
que nenhum chat, autocomplete generativo ou outro assistente está disponível.
O script confere extensões e processos observáveis e registra a declaração.

Uma verificação aprovada cria `treatment-verification.json` dentro do trial.
Não inicie o cronômetro sem esse arquivo com `status: passed`.

## 7. Execução cronometrada

Use outro terminal já verificado e inicie o coletor apontando para a cópia do
trial:

```powershell
.venv\Scripts\python.exe scripts\run_trial.py P01 K01 ai --src trials\P01-K01-ai\src
```

O coletor verifica a suíte a cada cinco segundos. Ele encerra na primeira
execução totalmente verde ou aos 2.100 segundos. Não interrompa o processo,
exceto por incidente real. O resultado fica em:

```text
data/raw/trials/P01-K01-ai/
|-- final_junit.xml
`-- trial.json
```

Uma interrupção inesperada gera `incident.json`. Não apague o diretório nem
repita o trial sem decisão e desvio documentados.

## 8. Teste funcional e métricas finais

Confira novamente a suíte sobre o código preservado:

```powershell
.venv\Scripts\python.exe scripts\run_tests.py K01 --src trials\P01-K01-ai\src
```

Depois colete as métricas estruturais:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py P01-K01-ai --source trials\P01-K01-ai\src
```

As saídas ficam em `data/raw/metrics/P01-K01-ai/`. Os dois coletores recusam
sobrescrita. Não altere dados brutos manualmente.

## 9. Checklist de encerramento

Antes de liberar a próxima linha da alocação, confirme:

- `trial-config.json` corresponde ao participante, kata e tratamento;
- `treatment-verification.json` possui `status: passed`;
- o código final permanece em `trials/<trial_id>/src`;
- `trial.json` ou `incident.json` foi preservado;
- `final_junit.xml` existe quando a suíte foi executada;
- `data/raw/metrics/<trial_id>/metrics.json` existe;
- Issue e commit usam o mesmo `trial_id`;
- eventual desvio foi registrado em `Docs/protocol-decisions.md`.

Erros de código são resultados experimentais. Falta de ferramenta, versão
divergente, restauração indevida ou tratamento incorreto são incidentes de
infraestrutura e devem interromper o início do trial.

## 10. Dashboard e figuras das RQs

Depois de gerar `data/processed/trials.csv` e a análise consolidada, execute da
pasta `Lab02`:

```powershell
.venv\Scripts\python.exe scripts\validate_dataset.py
.venv\Scripts\python.exe scripts\run_analysis.py
.venv\Scripts\python.exe scripts\generate_dashboard.py
```

Instale previamente `requirements-analysis.txt` na `.venv` (Matplotlib). O
comando do dashboard recarrega `trials.csv` e executa novamente a validação da
Seção 13. Se houver erro crítico, interrompe antes de criar as figuras. Use
`--dataset` e `--output` para outros caminhos; o dataset informado também será
validado contra as fontes oficiais. A ordem e os deslocamentos dos pontos são
fixos, portanto a geração é reproduzível.

Abra `reports/figures/dashboard/index.html` no navegador. A página reúne:

- visão geral com os 18 trials identificados;
- RQ1: tempo individual e nove comparações pareadas por participante/bloco;
- RQ2: taxa de sucesso dos testes e conclusão de cada trial;
- RQ3: complexidade ciclomática média, duplicação e LOC, incluindo pares com
  medições disponíveis.

Cada figura possui título, eixos, unidade, legenda e fonte, e pode ser baixada
como PNG ou SVG. `trial-points.csv` contém os 18 registros usados nos gráficos;
`paired-points.csv` contém valores de IA e Manual por participante, bloco e
métrica. O marcador X indica censura. Medições estruturais ausentes não são
convertidas em zero; o gráfico informa quantas faltam em cada tratamento.
Pontos com o mesmo valor recebem deslocamentos horizontais fixos. Os pares de
três participantes são descritivos e não devem ser lidos como nove participantes
independentes.

## 11. Visualização web com Streamlit

Na pasta `Lab02`, instale as dependências e inicie o servidor local:

```powershell
uv pip install --python .venv/Scripts/python.exe -r requirements-analysis.txt
.venv\Scripts\python.exe -m streamlit run src/dashboard/app.py --server.address 127.0.0.1
```

Abra o endereço local mostrado pelo Streamlit (`http://127.0.0.1:8501`).
O aplicativo lê e revalida `data/processed/trials.csv` antes de exibir dados;
se a validação encontrar erro crítico, nenhuma visualização é apresentada.
Os filtros de participante e bloco mantêm IA e Manual lado a lado. As abas
mostram visão geral, tempo individual e pareado, taxa de sucesso e conclusão,
e complexidade, duplicação e LOC. Cada ponto tem detalhes ao passar o cursor;
censura usa marcador distinto, e métricas ausentes permanecem ausentes.

Na aba **Dados e exportação**, baixe os CSVs filtrados ou gere um ZIP com as
figuras PNG/SVG e os dados do filtro atual. Esse pacote é recriado a partir do
dataset validado, sem reutilizar figuras antigas. O comando
`scripts/generate_dashboard.py` permanece disponível para produzir os arquivos
estáticos em `reports/figures/dashboard/` sem iniciar o servidor.
