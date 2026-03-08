# Skills 规划清单（项目 case）

优先级 P0（先做）：
1. a-share-data-skill
   - A 股行情/指数/行业/公告抓取
   - 输出 market_snapshot.json

2. signal-engine-skill
   - 趋势/动量/估值/波动/回撤/财报质量评分
   - 输出 signal_report.json

3. risk-guard-skill
   - 风险分级、回撤与暴露约束
   - 输出风险状态 normal/cautious/defensive

4. advisor-cn-skill
   - 结构化中文建议（理由/风险/置信度/变化）

5. feishu-report-skill
   - 盘前/收盘/周报/异动推送

优先级 P1（第二阶段）：
6. backtest-eval-skill
   - 周度评估策略稳定性与命中率

7. signal-drift-monitor-skill
   - 监控信号漂移与阈值失效

建议来源：
- clawhub 搜索关键词：A股、quant、feishu、scheduler、risk
- 若无可用现成技能，按以上 7 个模块自建最小版本

---

## ClawHub 首轮检索结果（2026-03-07）

已找到可候选技能（按适配度排序）：

1) `StanleyChanH/tushare-finance`
- 用途：A 股/港股/美股、财务、宏观数据（Tushare）
- 适配：★★★★★（最贴近 CN-A 低频量化）
- 注意：需 Tushare Token

2) `BenAngel65/akshare-finance`
- 用途：AKShare 多市场数据抓取
- 适配：★★★★☆
- 注意：需验证字段稳定性和更新频率

3) `mbpz/akshare-stock`
- 用途：A 股量化数据分析
- 适配：★★★★☆
- 注意：下载量较低，建议先沙盒验收

4) `THIRTYFANG/stock-monitor-skill`
- 用途：股票监控预警（均线/RSI/异动）
- 适配：★★★☆☆
- 注意：偏监控告警，需与我们的风控规则对齐

5) `ajanraj/yahoo-finance`
- 用途：通用行情与基本面
- 适配：★★★☆☆
- 注意：A 股覆盖与口径需额外验证

不建议直接作为核心数据源：
- 拼写/来源不稳定的腾讯抓取类技能（多个重复变体）
- 付费调用型（如按次扣费）

下一步执行建议：
- P0 安装并验收：`tushare-finance`、`akshare-finance`
- P1 候选：`stock-monitor-skill`
- 其余模块（advisor/risk/feishu-report）优先自建项目内 skills，确保可解释与可控