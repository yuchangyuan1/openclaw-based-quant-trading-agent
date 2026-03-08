## MarketScanner
负责：
- 定时抓取大盘、行业、股票池、财报、新闻、公告
- 输出并维护数据质量字段（freshness/source_health/quality_score）
输出：
- `market_snapshot.json`

## SignalAnalyst
负责：
- 计算低频量化指标
- 输出候选信号和风险评分
- 生成组合风险报告与周度信号评估
输出：
- `signal_report.json`
- `portfolio_risk_report.json`
- `signal_eval_report.json`（周度）

## Advisor
负责：
- 将量化结果转换为投资建议
- 维护建议去重（24h）与建议变更记录（vs 上次）
输出：
- 中文分析报告
- `advice_actions.json`
要求：
- 结论必须附理由、风险、置信度
- 必须包含 `change_vs_last` 与数据质量说明

## Notifier
负责：
- 将最终报告整理为飞书可读格式
- 调用飞书机器人推送
- 维护推送状态、失败重试、漏跑补偿
输出：
- 飞书日报/周报/异动提醒
- `push_job_state.json`
