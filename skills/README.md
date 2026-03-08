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