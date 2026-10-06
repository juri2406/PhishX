param([ValidateSet("fixture", "model")][string]$Mode = "fixture")
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Create .venv and install backend requirements using README.md first.'
}
$env:PHISHX_MODE = $Mode
& '.\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
