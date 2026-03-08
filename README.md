# OpenClaw 低频量化交易咨询 Agent（A 股）

这是一个基于 **OpenClaw** 的低频量化投研项目，用于把“市场数据抓取 → 信号生成 → 中文建议 → 日报输出”串成可复用流程。

> 定位：**投资决策支持系统**（recommendation only），不是自动交易系统。

---

## 1. 项目功能概览

本项目当前已实现：

- ✅ 从 Tushare 拉取股票池与指数快照（`market_snapshot`）
- ✅ 基于规则生成低频信号报告（`signal_report`）
- ✅ 自动生成中文日报 Markdown
- ✅ 关键策略参数配置化（无需改代码即可调参）
- ✅ ClawHub 第三方 skills 隔离安装与审计记录

核心工作流：

```text
config/*.yaml
   ↓
Tushare snapshot builder
   ↓
signal report builder
   ↓
daily report generator
   ↓
outputs/daily_report.generated.md
```

---

## 2. 设计原则

来自 `SOUL.md` / `IDENTITY.md`：

- 可解释优先于复杂
- 风险控制优先于收益冲动
- 没有数据就不下结论
- 没有显著变化就不重复打扰
- 不直接执行交易、不承诺收益

---

## 3. 项目结构（当前）

```text
.
├─ config/
│  ├─ portfolio.yaml                # 市场/指数/股票池/仓位约束
│  ├─ signal_rules.yaml             # 信号阈值、风险阈值、理由模板
│  └─ notify_rules.yaml             # 推送与降噪规则
├─ data/
│  ├─ market_snapshot.tushare.json  # 实时拉取生成
│  ├─ signal_report.generated.json  # 实时信号生成
│  └─ *.sample.json                 # 样例数据
├─ outputs/
│  ├─ daily_report.generated.md     # 最终日报
│  └─ feishu_payload.sample.json    # 飞书推送 dry-run 样例
├─ schemas/
│  └─ signal_report.schema.json     # 信号报告结构约束
├─ scripts/
│  ├─ build_market_snapshot_from_tushare.py
│  ├─ build_signal_report_from_snapshot.py
│  ├─ generate_daily_report.py
│  └─ run_daily_pipeline.ps1        # 一键流水线入口
├─ skills/
│  ├─ README.md                     # skills 规划与检索结果
│  ├─ tushare-finance/              # 已隔离安装（含审计）
│  └─ akshare-finance/              # 已隔离安装（含审计）
├─ examples/
├─ AGENTS.md
├─ HEARTBEAT.md
├─ IDENTITY.md
├─ SOUL.md
├─ USER.md
└─ README.md
```

---

## 4. 快速开始

### 4.1 前置要求

- Windows + PowerShell
- Python 3.11+（当前环境可用）
- OpenClaw 已配置
- Tushare 账号与可用 Token

### 4.2 配置 TUSHARE_TOKEN

PowerShell：

```powershell
setx TUSHARE_TOKEN "你的_tushare_token"
```

> 重新打开终端后生效。当前会话临时生效可用：
> `$env:TUSHARE_TOKEN="你的_tushare_token"`

### 4.3 安装依赖（隔离环境）

项目已使用 `.venv-tushare`。如需重装：

```powershell
python -m venv .venv-tushare
.\.venv-tushare\Scripts\python -m pip install -r skills\tushare-finance\requirements.txt
```

### 4.4 一键运行日报流水线

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_daily_pipeline.ps1
```

运行成功后查看：

- `data/market_snapshot.tushare.json`
- `data/signal_report.generated.json`
- `outputs/daily_report.generated.md`

---

## 5. 如何调参（只改配置，不改代码）

### 5.1 改股票池与指数

编辑 `config/portfolio.yaml`：

- `indexes`: 日报中的指数集合
- `watchlist`: 信号生成覆盖的股票池
- `portfolio_constraints`: 仓位/行业暴露/回撤约束

### 5.2 改信号规则

编辑 `config/signal_rules.yaml`：

- `thresholds`: increase / hold / observe / reduce 划分
- `risk_change_pct`: 低/中/高风险阈值
- `model_params.default_confidence`: 默认置信度
- `global_risk_thresholds`: normal/cautious/defensive 切换规则
- `reason_templates`: 信号理由模板文案

---

## 6. 关键脚本说明

- `build_market_snapshot_from_tushare.py`
  - 从 `portfolio.yaml` 读取市场、指数、股票池
  - 拉取行情并生成 `market_snapshot.tushare.json`

- `build_signal_report_from_snapshot.py`
  - 读取 snapshot 与 `signal_rules.yaml`
  - 生成 `signal_report.generated.json`

- `generate_daily_report.py`
  - 合并 snapshot + signal
  - 输出中文结构化日报 markdown

- `run_daily_pipeline.ps1`
  - 串联以上三步，一键执行

---

## 7. 第三方 Skill 使用策略（安全）

本项目对第三方 skills 采用“先隔离、后验收”的策略：

- `skills/tushare-finance/ISOLATION_AUDIT.md`
- `skills/akshare-finance/ISOLATION_AUDIT.md`

原则：
- 不直接把未知 skill 接入主流程
- 先做静态检查、依赖隔离、最小联通测试
- 再决定是否进入生产链路

---

## 8. 当前边界与后续计划

### 当前边界
- 仅输出建议，不执行交易
- 指数接口权限受 Tushare 账号权限影响（脚本已做降级处理）
- 信号模型仍是可解释的简化规则版（适合先跑通）

### 后续计划
- [ ] 加入更多因子（波动、回撤、估值、财报质量）
- [ ] 增加历史建议对比（delta_vs_last 真实化）
- [ ] 接入飞书正式推送（当前已有 dry-run payload）
- [ ] 周报自动复盘与参数迭代

---

## 9. 免责声明

本项目仅用于投研与决策辅助，不构成任何投资承诺或收益保证。投资有风险，决策需谨慎。