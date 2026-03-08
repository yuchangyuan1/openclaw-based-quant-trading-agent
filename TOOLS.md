可用工具：

## market_data
用途：
- 拉取指数、股票、行业板块、财务指标、公告、新闻
输入：
- 市场、代码、时间范围、股票池
标准输出：
- `market_snapshot.json`
- 必填字段：`timestamp`、`market`、`symbols`、`index`、`sector`、`news`

## quant_analysis
用途：
- 计算趋势、动量、估值、波动、回撤、财报质量、风险暴露
输入：
- `market_snapshot.json`、策略参数、股票池
标准输出：
- `signal_report.json`
- 必填字段：`timestamp`、`symbol`、`signal`、`score`、`confidence`、`risk_level`、`reasons`

## feishu_bot
用途：
- 将结构化分析结果推送到飞书群/私聊
输入：
- 标题、摘要、正文、Markdown内容、风险级别
标准输出：
- 推送状态、message_id、发送时间

使用约束：
- 数据必须标注时间
- 无法获取新数据时，不得编造
- 推送前先生成摘要，再生成详细内容
- 同一结论重复时优先去重，减少噪音提醒

失败降级策略：
- 数据源失败：仅推送“系统状态 + 风险提示”，不输出交易建议
- 信号计算失败：保留市场摘要并明确“信号暂不可用”
- 推送失败：记录重试状态并在下个周期补发摘要