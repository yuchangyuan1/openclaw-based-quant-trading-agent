# OpenClaw 低频量化交易咨询 Agent（A 股）

这是一个基于 **OpenClaw** 的低频量化投研项目，把“数据抓取 → 信号分析 → 风控约束 → 建议生成 → 飞书推送”串成可持续运行流程。

> 定位：**投资决策支持系统（recommendation only）**，不自动下单。

---

## 1. 当前能力（已落地）

- ✅ Tushare 数据抓取（股票池 + 指数）
- ✅ 数据质量闸门：`freshness/source_health/quality_score`
- ✅ 信号生成（含 `evidence` 与 `data_quality_gate`）
- ✅ 组合风险报告（单票/行业/回撤约束）
- ✅ 建议去重（24h 同结论同理由抑制）
- ✅ 建议变更记录（`change_vs_last`）
- ✅ 日报生成（5段结构）
- ✅ 飞书自动推送（webhook）
- ✅ 推送失败重试队列与补偿机制
- ✅ 周度信号评估报告

---

## 2. 核心流程（当前主流水线）

`run_daily_pipeline.ps1` 现为 8 步：

1. `build_market_snapshot_from_tushare.py`
2. `build_signal_report_from_snapshot.py`
3. `build_portfolio_risk_report.py`
4. `update_advice_history.py`
5. `generate_daily_report.py`
6. `finalize_push_state.py`
7. `push_daily_to_feishu.py`
8. `consume_retry_queue.py`

---

## 3. 项目结构（关键目录）

```text
.
├─ config/
│  ├─ portfolio.yaml
│  ├─ signal_rules.yaml
│  └─ notify_rules.yaml
├─ data/                              # 运行时数据（默认不入库）
├─ outputs/                           # 运行产物（默认不入库）
├─ state/
│  ├─ push_job_state.json             # 推送状态（保留）
│  └─ advice_history.jsonl            # 建议历史（默认不入库）
├─ schemas/
│  ├─ market_snapshot.schema.json
│  ├─ signal_report.schema.json
│  ├─ portfolio_risk_report.schema.json
│  ├─ signal_eval_report.schema.json
│  └─ advice_record.schema.json
├─ scripts/
│  ├─ build_market_snapshot_from_tushare.py
│  ├─ build_signal_report_from_snapshot.py
│  ├─ build_portfolio_risk_report.py
│  ├─ update_advice_history.py
│  ├─ evaluate_signal_quality.py
│  ├─ generate_daily_report.py
│  ├─ finalize_push_state.py
│  ├─ push_daily_to_feishu.py
│  ├─ consume_retry_queue.py
│  ├─ missed_run_recovery.py
│  └─ run_daily_pipeline.ps1
├─ templates/
│  ├─ feishu_daily.md
│  ├─ feishu_weekly.md
│  └─ feishu_alert.md
├─ docs/
│  ├─ IMPLEMENTATION_DRAFT_2026-03-08.md
│  ├─ CONTEXT_ARCHIVE_2026-03-08.md
│  └─ NEXT_STEPS_EXECUTION.md
└─ README.md
```

---

## 4. 环境变量

### 必需

```powershell
setx TUSHARE_TOKEN "你的_tushare_token"
```

### 飞书推送（二选一）

```powershell
setx FEISHU_WEBHOOK_URL "你的飞书机器人webhook"
# 或
setx FEISHU_BOT_WEBHOOK "你的飞书机器人webhook"
```

> 未配置 webhook 时，系统不会中断，但会把任务放入 `retry_queue`。

---

## 5. 运行方式

### 日报流水线

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_daily_pipeline.ps1
```

### 周度评估

```powershell
.\.venv-tushare\Scripts\python scripts\evaluate_signal_quality.py
```

### 漏跑补偿检查（重启后）

```powershell
.\.venv-tushare\Scripts\python scripts\missed_run_recovery.py
```

---

## 6. 输出文件说明

- `data/market_snapshot.tushare.json`：市场快照（含质量字段）
- `data/signal_report.generated.json`：信号与风险结果
- `outputs/portfolio_risk_report.json`：组合约束检查结果
- `outputs/advice_actions.json`：去重后的建议动作
- `outputs/daily_report.generated.md`：日报内容
- `outputs/signal_eval_report.json`：周度评估
- `state/push_job_state.json`：推送状态与重试队列

---

## 7. 配置与治理文件（已更新）

以下 OpenClaw 配置文件已对齐当前实现：

- `SOUL.md`
- `AGENTS.md`
- `USER.md`
- `HEARTBEAT.md`
- `MEMORY.md`

---

## 8. 版本控制策略

已加入 `.gitignore`：

- 默认忽略运行产物：`data/*.json`, `outputs/*.json`, `outputs/*.md`, `state/*.jsonl`
- 保留必要骨架：`state/push_job_state.json`

---

## 9. 后续计划

- [ ] 云端常驻部署（cron/systemd）
- [ ] 周报自动推送串联
- [ ] 更真实的收益/回撤评估与置信度校准
- [ ] source health 的多源路由与回退优化

---

## 10. 免责声明

本项目仅用于投研与决策辅助，不构成投资建议或收益承诺。投资有风险，决策需谨慎。
