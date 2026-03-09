# OpenClaw 低频量化交易咨询 Agent（A 股）

本项目基于 OpenClaw，实现 A 股低频量化投研流水线：
**数据抓取 → 多因子打分 → 风控约束 → 建议生成 → 飞书推送（卡片）**。

> 定位：投资决策支持系统（recommendation only），不自动下单。

---

## 1. 当前能力

- ✅ Tushare 市场数据抓取（股票池/指数/基础财务）
- ✅ 多因子信号模型：趋势、动量、估值、波动、回撤、财报质量
- ✅ 数据质量闸门（freshness/source_health/quality_score）
- ✅ 组合风险约束（单票/行业/回撤）
- ✅ 24h 建议去重 + 建议变更追踪
- ✅ 日报/周报产出
- ✅ OpenClaw Feishu 通道推送（App ID/App Secret，默认卡片）
- ✅ 财务数据源探针（fundamental_probe，可用性/时延报告）

---

## 2. 主流水线（交易日 15:30）

`run_daily_pipeline.ps1`：

1. `build_market_snapshot_from_tushare.py`
2. `build_signal_report_from_snapshot.py`
3. `build_portfolio_risk_report.py`
4. `update_advice_history.py`
5. `generate_daily_report.py`
6. `build_feishu_card_payload.py`
7. `finalize_push_state.py`
8. 由 OpenClaw Feishu 通道发送

---

## 3. 目录结构（关键）

```text
config/      # 参数配置（股票池、阈值、推送规则）
data/        # 运行时快照与信号数据
outputs/     # 报告与卡片payload
schemas/     # JSON结构约束
scripts/     # 核心流水线脚本
state/       # 推送状态、建议历史
templates/   # 飞书日报/周报/卡片模板
docs/        # 实施文档与执行说明
```

---

## 4. 环境变量

```powershell
setx TUSHARE_TOKEN "你的token"
```

飞书推送不需要 webhook，使用 OpenClaw 已连接的 Feishu 应用（App ID/App Secret）。

---

## 5. 运行命令

### 日报流水线
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_daily_pipeline.ps1
```

### 周度评估
```powershell
.\.venv-tushare\Scripts\python scripts\evaluate_signal_quality.py
```

### 周流水线（一键）
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_weekly_pipeline.ps1
```

### 基线回测（MA 交叉）
```powershell
.\.venv-tushare\Scripts\python scripts\backtest_ma_baseline.py
```
输出：`outputs/backtest_baseline_report.json`

### 建议解释查询（交互入口）
```powershell
.\.venv-tushare\Scripts\python scripts\explain_advice.py --symbol 600519.SH
```
不带 `--symbol` 时输出全部当前建议解释。

### 漏跑补偿检查
```powershell
.\.venv-tushare\Scripts\python scripts\missed_run_recovery.py
```

### 财务数据源探针
```powershell
.\.venv-tushare\Scripts\python scripts\fundamental_probe.py
```

### 连续异常告警检查（N=3）
```powershell
.\.venv-tushare\Scripts\python scripts\check_fundamental_alert.py
```

---

## 6. 关键输出

- `data/market_snapshot.tushare.json`
- `data/signal_report.generated.json`
- `outputs/portfolio_risk_report.json`
- `outputs/advice_actions.json`
- `outputs/daily_report.generated.md`
- `outputs/feishu_card_payload.generated.json`
- `outputs/signal_eval_report.json`
- `state/push_job_state.json`

---

## 7. 治理配置文件

- `SOUL.md`
- `AGENTS.md`
- `USER.md`
- `HEARTBEAT.md`
- `MEMORY.md`

---

## 8. 版本控制策略

`.gitignore` 默认忽略运行时数据与产物，仅保留必要状态骨架文件。

---

## 9. 后续路线图

- [ ] 云端常驻部署（cron/systemd）
- [ ] 周报自动推送串联
- [ ] 多源财务数据回退（Tushare→Akshare）
- [ ] 置信度校准与策略回测闭环

---

## 10. 免责声明

仅用于投研与辅助决策，不构成投资建议。投资有风险，决策需谨慎。
