#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

python scripts/build_market_snapshot_from_tushare.py
python scripts/build_signal_report_from_snapshot.py
python scripts/build_portfolio_risk_report.py
python scripts/update_advice_history.py
python scripts/generate_daily_report.py
python scripts/build_feishu_card_payload.py
python scripts/finalize_push_state.py

echo "pipeline done: $(date -Iseconds)"
