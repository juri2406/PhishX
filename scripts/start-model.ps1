param([int]$Port = 8000, [ValidateSet('revised-run06','uci-run03')][string]$ModelRun = 'revised-run06')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$modelPath = Join-Path $projectRoot "artifacts\$ModelRun\classical.joblib"
if (-not (Test-Path -LiteralPath $modelPath)) {
    throw 'Missing trained model: copy classical.joblib from the Person 1 handoff into the selected artifacts directory.'
}
$hashes = @{ 'revised-run06' = 'a5a68744712975f0f5809dd6f13825eeb47dc4251153f3f65eadc2120727d3ed'; 'uci-run03' = '2b59557ed0a23220bd69e0f2775ad934d20fa1587ff71fe2decb750fb2ff8ac7' }
$expectedHash = $hashes[$ModelRun]
if ((Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedHash) {
    throw 'This launcher expects the verified selected model. Review the handoff before using another artifact.'
}
$env:PHISHX_MODE = 'model'
$env:PHISHX_PROVIDER = 'ml.integration:create_provider'
$env:PHISHX_MODEL_PATH = $modelPath
& '.\.venv\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port $Port
