param([switch]$Preview)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
if (-not (Test-Path -LiteralPath 'node_modules\vite\bin\vite.js')) {
    throw 'Install frontend dependencies using README.md first.'
}
if ($Preview) {
    if (-not (Test-Path -LiteralPath 'dist\index.html')) {
        throw 'Build the frontend using npm run build or pnpm run build first.'
    }
    & node 'node_modules/vite/bin/vite.js' preview --host 127.0.0.1 --port 5173 --configLoader native
} else {
    & node 'node_modules/vite/bin/vite.js' --host 127.0.0.1 --configLoader native
}
