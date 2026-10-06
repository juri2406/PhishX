param([switch]$Preview)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
if (-not (Test-Path -LiteralPath 'node_modules\vite\bin\vite.js')) {
    throw 'Install frontend dependencies using README.md first.'
}
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if ($nodeCommand) {
    $nodeExecutable = $nodeCommand.Source
} else {
    $nodeCandidates = @(
        (Join-Path $env:ProgramFiles 'nodejs\node.exe'),
        (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
    )
    $nodeExecutable = $nodeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $nodeExecutable) {
    throw 'Node.js was not found. Install Node.js 22.12 or newer, reopen PowerShell, and retry.'
}
if ($Preview) {
    if (-not (Test-Path -LiteralPath 'dist\index.html')) {
        throw 'Build the frontend using npm run build or pnpm run build first.'
    }
    & $nodeExecutable 'node_modules/vite/bin/vite.js' preview --host 127.0.0.1 --port 5173 --configLoader native
} else {
    & $nodeExecutable 'node_modules/vite/bin/vite.js' --host 127.0.0.1 --configLoader native
}

