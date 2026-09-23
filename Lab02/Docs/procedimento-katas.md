# Procedimento completo de execução dos katas (tratamento Manual e tratamento IA)

Documento de referência do experimento "Medição e Experimentação de Software"
(Lab02, sprint S02). Descreve, passo a passo, como cada participante prepara
o ambiente e executa um trial — nos dois tratamentos — do jeito que foi
efetivamente seguido na coleta. Todos os comandos abaixo rodam no PowerShell,
a partir da raiz do repositório.

## 0. Contexto rápido

- Cada participante (P01, P02, P03) resolve 6 katas (K01–K06), 3 no
  tratamento **Manual** (sem nenhum assistente de IA) e 3 no tratamento
  **IA** (com assistente de IA autorizado), numa ordem contrabalanceada
  definida antecipadamente em `allocation.csv`.
- Um trial só é iniciado depois que **ambiente**, **tratamento** e a
  **combinação participante/kata/tratamento** estiverem validados. Nada é
  espontâneo — cada etapa grava evidência em disco.
- Erros de código são resultado experimental válido. Falta de ferramenta,
  versão divergente, restauração indevida ou tratamento mal verificado são
  **incidentes de infraestrutura** e devem interromper o início do trial.

## 1. Ambiente congelado (versões obrigatórias)

Estas versões ficam fixas para os três participantes e são conferidas
automaticamente antes da coleta:

| Componente | Versão | Finalidade |
|---|---:|---|
| Python | 3.12.14 | Runtime das katas e dos scripts de coleta |
| pytest | 9.1.1 | Execução dos testes de aceitação |
| Radon | 6.0.1 | Complexidade ciclomática, LOC e manutenibilidade |
| JSCPD | 5.2.0 | Detecção de duplicação de código |
| Node.js | 24.19.0 | Runtime do JSCPD e do assistente de IA em terminal |
| npm | 11.17.0 | Instalação das ferramentas Node.js |
| uv | 0.12.10 | Gerenciamento do runtime e das dependências Python |

**Assistente de IA do tratamento IA:** Codex CLI 0.154.0 (modelo
`gpt-5.3-codex`), via terminal integrado do VS Code, sem autocomplete inline
em editor — **exceto para o participante P01**, que usa Claude Code 2.1.273
(modelo `claude-sonnet-5`) em vez do Codex CLI, por não ter acesso a este
último. Essa exceção está registrada e não deve ser confundida com liberdade
de escolha: os scripts de verificação já sabem, por participante, qual
assistente é o autorizado.

**IDE:** Visual Studio Code, com `ms-python.python` e
`ms-python.vscode-pylance` sempre habilitadas. Qualquer outra extensão
(temas, linters, outras linguagens, Docker etc.) é permitida. A única
restrição real é: **nenhuma extensão de IA generativa** (GitHub Copilot,
Copilot Chat, Tabnine, Codeium, Continue ou equivalente), em nenhum dos dois
tratamentos — isso vale mesmo no tratamento IA, porque ali o único
assistente autorizado é a CLI (Codex ou Claude Code) rodando no terminal,
nunca uma extensão do editor.

## 2. Instalação e verificação da máquina

Primeira preparação da máquina:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01 -InstallSystemTools
```

Isso instala as versões congeladas de uv, Node.js, VS Code e Codex CLI, as
extensões Python de base, cria o `.venv`, sincroniza `requirements.lock` e
valida tudo. Se as ferramentas já estiverem na versão certa:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01
```

Para só reverificar uma máquina já preparada:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 -Participant P01 -VerifyOnly
```

O comando precisa terminar sem erro e registrar a máquina em
`data/metadata/environment.json` com `status: verified`. Ele também roda:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe scripts\generate_allocation.py --check
```

Cada participante roda o setup na própria máquina; um registro existente não
é substituído sem `--replace`.

## 3. Conferência do clone antes de coletar

```powershell
Test-Path reference-solutions\K01
git status --short
```

O primeiro comando deve dar `False` (as soluções de referência ficam só com
o custodiante do experimento, nunca no clone de quem está resolvendo a
kata). O segundo não deve mostrar nenhuma alteração inesperada.

## 4. Kata de treinamento (antes de qualquer trial oficial)

Serve para o participante praticar o fluxo completo (cronômetro, ambiente,
regras dos dois tratamentos) numa kata que não é usada na coleta real
("Decodificação por repetição").

```powershell
$trainingDir = "data\training\P01"
New-Item -ItemType Directory -Path $trainingDir
Copy-Item -Recurse training-kata\src "$trainingDir\src"
$env:KATA_SRC_DIR = (Resolve-Path "$trainingDir\src")
.venv\Scripts\python.exe -m pytest training-kata\tests -q
Remove-Item Env:KATA_SRC_DIR
```

O esqueleto começa falhando com `NotImplementedError`. Os dados da kata de
treinamento ficam em `data/training/` e **nunca** recebem `trial_id` oficial
— não entram no dataset.

## 5. Preparar um trial oficial

O custodiante revela apenas a próxima linha de `allocation.csv`. Exemplo
para P01/K01/tratamento IA:

```powershell
.venv\Scripts\python.exe scripts\prepare_trial.py P01 K01 ai
```

Isso valida a combinação contra a alocação congelada e cria uma cópia limpa
do esqueleto da kata em:

```text
trials/P01-K01-ai/
|-- README.md
|-- src/solution.py
`-- trial-config.json
```

Se precisar limpar uma preparação antes do cronômetro começar:

```powershell
.venv\Scripts\python.exe scripts\prepare_trial.py P01 K01 ai --restore
```

`--restore` só limpa o diretório daquele trial específico. **Depois que a
coleta (`data/raw/trials/<trial_id>/`) existir, nada pode ser restaurado ou
sobrescrito** — o comando é recusado.

## 6. Verificar o tratamento antes de iniciar o cronômetro

Feche o assistente de IA (Codex CLI / Claude Code) e qualquer chatbot ou
autocomplete generativo antes de verificar.

**Tratamento IA:**

```powershell
.venv\Scripts\python.exe scripts\verify_treatment.py ai --trial-dir trials\P01-K01-ai
```

O script já sabe, pelo `participant_id` gravado em `trial-config.json`, se o
assistente esperado é Codex CLI (P02, P03) ou Claude Code (P01), e confere a
versão instalada. Qualquer extensão de IA generativa no editor causa falha.

**Tratamento Manual:**

```powershell
.venv\Scripts\python.exe scripts\verify_treatment.py manual --trial-dir trials\P01-K01-manual --confirm-manual-no-ai
```

Antes de usar `--confirm-manual-no-ai`, feche o assistente de IA e confirme
visualmente que nenhum chat, autocomplete generativo ou outro assistente
está disponível. O script confere extensões e processos em execução, e
registra essa declaração como evidência.

Em ambos os casos, uma verificação aprovada cria
`trials/<trial_id>/treatment-verification.json` com `status: "passed"`.
**Não inicie o cronômetro sem esse arquivo.**

## 7. Executar o trial cronometrado

```powershell
.venv\Scripts\python.exe scripts\run_trial.py P01 K01 ai --src trials\P01-K01-ai\src
```

(troque `ai` por `manual` e o caminho conforme o trial). O coletor roda a
suíte de aceitação a cada 5 segundos, em segundo plano, enquanto o
participante continua editando e testando livremente. Ele encerra:

- na primeira execução totalmente verde (todos os testes passando), ou
- em 2.100 segundos (35 minutos), o que vier primeiro.

Não interrompa o processo, exceto por incidente real (nesse caso ele grava
`incident.json` em vez do resultado). O resultado fica em:

```text
data/raw/trials/P01-K01-ai/
|-- final_junit.xml
`-- trial.json
```

**Importante:** o código final deve estar salvo com folga antes do prazo
fechar — um salvamento de última hora, nos segundos finais, pode não ser
capturado corretamente pela verificação final do coletor.

## 8. Teste funcional final e métricas

Confirme a suíte sobre o código preservado:

```powershell
.venv\Scripts\python.exe scripts\run_tests.py K01 --src trials\P01-K01-ai\src
```

Colete as métricas estruturais:

```powershell
.venv\Scripts\python.exe scripts\collect_static_metrics.py P01-K01-ai --source trials\P01-K01-ai\src
```

As saídas ficam em `data/raw/metrics/P01-K01-ai/`. Nenhum dos dois
coletores sobrescreve uma coleta existente. **Dados brutos nunca são
editados manualmente** — qualquer inconsistência descoberta depois vira uma
nota documentada à parte, não uma edição do arquivo original.

## 9. Checklist de encerramento de um trial

Antes de liberar a próxima linha da alocação, confirme:

- [ ] `trial-config.json` corresponde ao participante, kata e tratamento certos;
- [ ] `treatment-verification.json` existe com `status: "passed"`;
- [ ] o código final está preservado em `trials/<trial_id>/src`;
- [ ] `trial.json` (ou `incident.json`, se houve incidente) foi gravado;
- [ ] `final_junit.xml` existe, se a suíte chegou a rodar;
- [ ] `data/raw/metrics/<trial_id>/metrics.json` existe;
- [ ] issue e commit referenciam o mesmo `trial_id`;
- [ ] qualquer desvio do protocolo foi registrado antes de seguir para o próximo trial.

## 10. Regras gerais sobre desvios de protocolo

- Qualquer mudança em relação ao que está congelado (versões, assistente,
  extensões, prazos) precisa ser registrada, com data, motivo e quem
  decidiu, **antes** de continuar os trials.
- Um trial cujo processo de coleta foi invalidado (ex.: assistente resolveu
  sozinho, sem interação do participante) é arquivado com a evidência bruta
  intacta e uma nova tentativa oficial é preparada do zero.
- Um trial cuja implementação está correta mas cujo *registro* tem um
  problema de instrumentação (ex.: bug de timing no coletor) não é
  necessariamente refeito — refazer só faz sentido se não comprometer a
  validade do dado (por exemplo, se o participante já sabe a resposta,
  refazer mediria memorização, não capacidade de resolver a kata do zero).
  Nesses casos, a evidência bruta também não é editada; documenta-se a
  leitura correta separadamente.
