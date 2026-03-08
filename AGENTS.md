## MarketScanner
负责：
- 定时抓取大盘、行业、股票池、新闻、公告
- 获取行情因子输入（ret_1d/5d/20d、volatility_20d、volume_ratio_5d）
- 获取财务因子输入（PE/PB、ROE、毛利率、资产负债率）
- 输出并维护数据质量字段（freshness/source_health/quality_score）
输出：
- `market_snapshot.json`

## SignalAnalyst
负责：
- 计算低频量化多因子评分（趋势/动量/估值/波动/回撤/财报质量）
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
- 将最终报告整理为飞书可读格式（默认卡片）
- 通过 OpenClaw Feishu 通道推送（App ID/App Secret）
- 维护推送状态与漏跑补偿
输出：
- 飞书日报/周报/异动提醒
- `push_job_state.json`
