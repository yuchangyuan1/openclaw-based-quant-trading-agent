记住以下长期信息：
- 重点跟踪股票池
- 每只股票最近一次建议、日期、理由、置信度
- 用户偏好的市场与风险偏好
- 已触发过的重大风险提醒
- 当前全局风险状态（正常/谨慎/防守）
- 每个标的最近一次建议变更原因（change_vs_last）
- 最近一次成功推送时间（日报/周报）

建议维护的结构化记忆字段：
- `symbol -> last_action / last_date / reason / confidence / change_vs_last`
- `global_risk_state`
- `user_preference_version`
- `push_status -> daily_last_success / weekly_last_success`

不要长期记住：
- 临时行情波动
- 未确认的小道消息
- 无来源的传闻
- 原始逐条新闻正文（仅保留已验证结论）
