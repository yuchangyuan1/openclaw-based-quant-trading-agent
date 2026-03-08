$ErrorActionPreference = 'Stop'

$env:TUSHARE_TOKEN = [Environment]::GetEnvironmentVariable('TUSHARE_TOKEN','User')
if (-not $env:TUSHARE_TOKEN) {
  throw 'TUSHARE_TOKEN not found in User env.'
}

Write-Host '[1/5] Building market snapshot from Tushare...'
.\.venv-tushare\Scripts\python scripts\build_market_snapshot_from_tushare.py

Write-Host '[2/5] Building signal report from snapshot...'
.\.venv-tushare\Scripts\python scripts\build_signal_report_from_snapshot.py

Write-Host '[3/5] Building portfolio risk report...'
.\.venv-tushare\Scripts\python scripts\build_portfolio_risk_report.py

Write-Host '[4/5] Updating advice history and dedup states...'
.\.venv-tushare\Scripts\python scripts\update_advice_history.py

Write-Host '[5/6] Generating daily report markdown...'
.\.venv-tushare\Scripts\python scripts\generate_daily_report.py

Write-Host '[6/8] Finalizing push state...'
.\.venv-tushare\Scripts\python scripts\finalize_push_state.py

Write-Host '[7/8] Pushing daily report to Feishu...'
.\.venv-tushare\Scripts\python scripts\push_daily_to_feishu.py

Write-Host '[8/8] Consuming retry queue...'
.\.venv-tushare\Scripts\python scripts\consume_retry_queue.py

Write-Host 'Done. Outputs:'
Write-Host ' - outputs\daily_report.generated.md'
Write-Host ' - outputs\portfolio_risk_report.json'
Write-Host ' - outputs\advice_actions.json'
Write-Host ' - state\push_job_state.json'