$ErrorActionPreference = 'Stop'

$env:TUSHARE_TOKEN = [Environment]::GetEnvironmentVariable('TUSHARE_TOKEN','User')
if (-not $env:TUSHARE_TOKEN) {
  throw 'TUSHARE_TOKEN not found in User env.'
}

Write-Host '[1/9] Building market snapshot from Tushare...'
.\.venv-tushare\Scripts\python scripts\build_market_snapshot_from_tushare.py

Write-Host '[2/9] Building signal report from snapshot...'
.\.venv-tushare\Scripts\python scripts\build_signal_report_from_snapshot.py

Write-Host '[3/9] Building portfolio risk report...'
.\.venv-tushare\Scripts\python scripts\build_portfolio_risk_report.py

Write-Host '[4/9] Updating advice history and dedup states...'
.\.venv-tushare\Scripts\python scripts\update_advice_history.py

Write-Host '[5/9] Generating daily report markdown...'
.\.venv-tushare\Scripts\python scripts\generate_daily_report.py

Write-Host '[6/9] Building Feishu card payload...'
.\.venv-tushare\Scripts\python scripts\build_feishu_card_payload.py

Write-Host '[7/9] Finalizing push state...'
.\.venv-tushare\Scripts\python scripts\finalize_push_state.py

Write-Host '[8/9] Probing fundamental data source health...'
try {
  .\.venv-tushare\Scripts\python scripts\fundamental_probe.py
} catch {
  Write-Warning 'fundamental_probe failed (non-blocking for main report).'
}

Write-Host '[9/9] Checking consecutive fundamental error alert...'
try {
  .\.venv-tushare\Scripts\python scripts\check_fundamental_alert.py
} catch {
  Write-Warning 'check_fundamental_alert failed (non-blocking).'
}

Write-Host 'Done. Outputs:'
Write-Host ' - outputs\daily_report.generated.md'
Write-Host ' - outputs\feishu_card_payload.generated.json'
Write-Host ' - outputs\portfolio_risk_report.json'
Write-Host ' - outputs\advice_actions.json'
Write-Host ' - state\push_job_state.json'
Write-Host ' - push delivery: handled by OpenClaw Feishu channel (App ID/App Secret), default format = card'