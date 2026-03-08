定时任务：

## 每个交易日 08:30
执行：
- 拉取隔夜全球市场信息
- 拉取重点股票池最新新闻与公告
- 生成盘前观察（不触发交易建议）

## 每个交易日 15:30
执行（主流水线）：
1. `build_market_snapshot_from_tushare.py`
2. `build_signal_report_from_snapshot.py`
3. `build_portfolio_risk_report.py`
4. `update_advice_history.py`
5. `generate_daily_report.py`
6. 推送飞书日报

失败降级：
- 任一步失败，输出“系统状态 + 风险提示”，不输出交易建议
- 更新 `state/push_job_state.json` 并进入重试队列

## 每周六 10:00
执行：
- `evaluate_signal_quality.py`
- 汇总本周收益、回撤、信号变化
- 生成周报并推送飞书

## 启动补偿任务（开机或服务重启后）
执行：
- `missed_run_recovery.py`
- 若检测到漏跑，补发摘要并标注“补发”

事件触发任务（非定时）：
- 指数或组合波动超过阈值：触发风险快报
- 单标的触发回撤阈值：触发减仓/观察建议
- 出现重大财报/公告风险关键词：触发异动提醒
- 数据源连续失败：触发系统状态告警
