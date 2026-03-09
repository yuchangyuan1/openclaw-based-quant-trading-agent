$ErrorActionPreference = 'Stop'

$env:TUSHARE_TOKEN = [Environment]::GetEnvironmentVariable('TUSHARE_TOKEN','User')
if (-not $env:TUSHARE_TOKEN) {
  throw 'TUSHARE_TOKEN not found in User env.'
}

Write-Host '[1/4] Evaluating signal quality...'
.\.venv-tushare\Scripts\python scripts\evaluate_signal_quality.py

Write-Host '[2/4] Running baseline backtest...'
.\.venv-tushare\Scripts\python scripts\backtest_ma_baseline.py

Write-Host '[3/4] Generating weekly report...'
.\.venv-tushare\Scripts\python scripts\generate_weekly_report.py

Write-Host '[4/4] Proposing threshold calibration (dry-run)...'
.\.venv-tushare\Scripts\python scripts\calibrate_signal_thresholds.py

Write-Host 'Done. Outputs:'
Write-Host ' - outputs\signal_eval_report.json'
Write-Host ' - outputs\backtest_baseline_report.json'
Write-Host ' - outputs\weekly_report.generated.md'
Write-Host ' - state\parameter_change_log.jsonl'
