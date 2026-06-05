#!/usr/bin/env pwsh
# One-command launch smoke test for demos and social recordings.
# Usage: .\scripts\launch-smoke.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "`n=== LoRA-JIT Launch Smoke Test ===" -ForegroundColor Cyan
Write-Host "Repo: https://github.com/Anandb71/LoRA-jit`n"

Write-Host "[1/3] Running tests..." -ForegroundColor Yellow
python -m pytest tests/ -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[2/3] Benchmark compare..." -ForegroundColor Yellow
python scripts/run-benchmark.py examples/sample-trace.json --compare

Write-Host "`n[3/3] JIT paging demo (daemon must be running in another terminal)..." -ForegroundColor Yellow
Write-Host "  python scripts/run-daemon.py" -ForegroundColor DarkGray
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2
    Write-Host "  Daemon: OK" -ForegroundColor Green

    $route1 = Invoke-RestMethod -Uri "http://127.0.0.1:8765/jit/route" -Method Post -ContentType "application/json" `
        -Body '{"session_id":"launch","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":1,"cursor_line":0,"cursor_column":10,"full_text":"SELECT id FROM teams WHERE"}'
    Write-Host "  Route 1 paging: $($route1.paging_status)" -ForegroundColor Green

    $route2 = Invoke-RestMethod -Uri "http://127.0.0.1:8765/jit/route" -Method Post -ContentType "application/json" `
        -Body '{"session_id":"launch","event_type":"cursor","file_path":"query.sql","language_id":"sql","sequence_id":2,"cursor_line":0,"cursor_column":10,"full_text":"SELECT count FROM orders WHERE"}'
    Write-Host "  Route 2 paging: $($route2.paging_status)" -ForegroundColor Green
} catch {
    Write-Host "  Daemon not running — skip live demo (start with: python scripts/run-daemon.py)" -ForegroundColor DarkYellow
}

Write-Host "`n=== Ready to share ===" -ForegroundColor Cyan
Write-Host "  https://github.com/Anandb71/LoRA-jit"
Write-Host "  Copy posts from docs/SOCIAL.md`n"
