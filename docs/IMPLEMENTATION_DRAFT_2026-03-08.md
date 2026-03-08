# OpenClaw Quant Advisor 完整草案（文件级）

## 1. 新增 Schema
- `schemas/market_snapshot.schema.json`
- `schemas/signal_report.schema.json`
- `schemas/signal_eval_report.schema.json`
- `schemas/portfolio_risk_report.schema.json`
- `schemas/advice_record.schema.json`

## 2. 新增脚本
- `scripts/build_portfolio_risk_report.py`
- `scripts/update_advice_history.py`
- `scripts/evaluate_signal_quality.py`
- `scripts/missed_run_recovery.py`

## 3. 已改造脚本
- `scripts/build_market_snapshot_from_tushare.py`
  - 加入：`data_freshness_sec/source_health/missing_fields/snapshot_quality_score`
- `scripts/build_signal_report_from_snapshot.py`
  - 加入：`evidence/data_quality_gate`
  - 数据质量闸门失败时，增持降级为观察
- `scripts/generate_daily_report.py`
  - 输出结构固定为 5 段
  - 写入 `change_vs_last/source_health/quality_score`
- `scripts/run_daily_pipeline.ps1`
  - 统一执行 5 步流水线

## 4. 状态与模板
- `state/advice_history.jsonl`（运行时自动创建并追加）
- `state/push_job_state.json`
- `templates/feishu_daily.md`
- `templates/feishu_weekly.md`
- `templates/feishu_alert.md`

## 5. 新输出文件
- `outputs/portfolio_risk_report.json`
- `outputs/advice_actions.json`
- `outputs/signal_eval_report.json`（周度）
- `outputs/missed_run_recovery.json`

## 6. 运行顺序（日报）
1. `build_market_snapshot_from_tushare.py`
2. `build_signal_report_from_snapshot.py`
3. `build_portfolio_risk_report.py`
4. `update_advice_history.py`
5. `generate_daily_report.py`

## 7. 周度补充
- 每周六：`evaluate_signal_quality.py`

## 8. 云迁移建议（后续）
- 将 `scripts/run_daily_pipeline.ps1` 对应为 Linux `cron` 任务
- 开机自启 + 状态文件持久化 + `missed_run_recovery.py` 补偿
