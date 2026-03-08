$ErrorActionPreference = 'Stop'

$env:TUSHARE_TOKEN = [Environment]::GetEnvironmentVariable('TUSHARE_TOKEN','User')
if (-not $env:TUSHARE_TOKEN) {
  throw 'TUSHARE_TOKEN not found in User env.'
}

Write-Host '[1/2] Building market snapshot from Tushare...'
.\.venv-tushare\Scripts\python scripts\build_market_snapshot_from_tushare.py

Write-Host '[2/2] Generating daily report markdown...'
python scripts\generate_daily_report.py

Write-Host 'Done. Output: outputs\daily_report.generated.md'