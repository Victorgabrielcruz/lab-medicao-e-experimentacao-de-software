[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('P01', 'P02', 'P03')]
    [string]$Participant,
    [switch]$InstallSystemTools,
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot

function Assert-ExactVersion {
    param([string]$Name, [string]$Actual, [string]$Expected)
    if ($Actual -notmatch [regex]::Escape($Expected)) {
        throw "$Name incompatível: esperado $Expected; saída encontrada: $Actual"
    }
}

if ($InstallSystemTools) {
    if ($VerifyOnly) {
        throw 'Use -InstallSystemTools e -VerifyOnly em execuções separadas.'
    }
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'winget é necessário para instalar as ferramentas de sistema.'
    }
    winget install --exact --id astral-sh.uv --version 0.12.10 --accept-package-agreements --accept-source-agreements
    winget install --exact --id OpenJS.NodeJS --version 24.19.0 --accept-package-agreements --accept-source-agreements
    winget install --exact --id Microsoft.VisualStudioCode --version 1.137.0 --accept-package-agreements --accept-source-agreements
    npm install --global '@openai/codex@0.154.0'
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw 'uv não encontrado. Execute novamente com -InstallSystemTools ou instale uv 0.12.10.'
}
Assert-ExactVersion 'uv' (& uv --version) '0.12.10'

if (-not $VerifyOnly) {
    uv python install 3.12.14
    uv venv --python 3.12.14 --clear .venv
    uv pip sync --python .venv\Scripts\python.exe requirements.lock
    npm ci --ignore-scripts
    code --install-extension ms-python.python --force
    code --install-extension ms-python.vscode-pylance --force
}

$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Ambiente virtual ausente: $pythonExe"
}

if ($VerifyOnly) {
    & $pythonExe scripts\verify_environment.py $Participant
} else {
    & $pythonExe scripts\verify_environment.py $Participant --record
}
if ($LASTEXITCODE -ne 0) { throw 'A verificação do ambiente falhou.' }
& $pythonExe -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw 'A suíte da infraestrutura falhou.' }
& $pythonExe scripts\generate_allocation.py --check
if ($LASTEXITCODE -ne 0) { throw 'A auditoria da alocação falhou.' }

Write-Output "Ambiente da S01-08 preparado e verificado para $Participant."
