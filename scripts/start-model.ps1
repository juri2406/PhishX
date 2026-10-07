param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$modelPath = Join-Path $projectRoot 'artifacts\uci-run03\classical.joblib'
if (-not (Test-Path -LiteralPath $modelPath)) {
    throw 'Missing trained model: copy classical.joblib from the Person 1 handoff into artifacts/uci-run03.'
}
$expectedHash = '2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7'
if ((Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'This launcher expects the verified uci-run03 model. Review the handoff before using another artifact.'
}
$env:PHISHX_MODE = 'model'
$env:PHISHX_PROVIDER = 'ml.integration:create_provider'
$env:PHISHX_MODEL_PATH = $modelPath
& '.\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
