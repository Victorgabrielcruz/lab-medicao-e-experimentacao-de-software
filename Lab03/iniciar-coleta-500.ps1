$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$Host.UI.RawUI.WindowTitle = 'Lab03 | Coleta 500 | 3 sessoes'
Write-Host 'Lab03: coleta e processamento com tres tokens. Meta: 500 elegiveis.'
Write-Host 'Quedas de rede serao retomadas automaticamente. Ctrl+C interrompe a coleta.'
& (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -u -m pipeline.coleta_paralela
Write-Host "Coleta encerrada com codigo $LASTEXITCODE. Consulte data/raw/amostra-final-500/coleta-tres-sessoes.log."
