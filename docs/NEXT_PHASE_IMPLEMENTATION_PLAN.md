# 后续项目实施计划表（V3，已更新）

## 一、项目目标（保持不变）
在保留 **Tushare 主链路** 前提下，引入 **Akshare 回退 + 置信度联动 + 数据源稳定性治理**，提升系统可用性、解释性与风控一致性。

---

## 二、现状评估（2026-03-09）

### 已具备能力
- 主流水线已可运行：抓数 → 信号 → 风控 → 建议 → 日报/卡片 → 推送状态落盘
- `snapshot_quality_score` 闸门已生效，低质量时可降级增持建议
- 财务因子已实现 Tushare 优先、Akshare 回退
- 建议去重与 change_vs_last 链路已建立

### 核心缺口
1. 缺少“逐接口探针”与稳定性量化（成功率/时延/错误分布）
2. 周报尚未系统呈现“数据源稳定性趋势”
3. 置信度联动已实现，但缺少回灌校准（根据周评估调阈值）
4. 缺少统一“实施—验证—回滚”清单，影响迭代节奏

---

## 三、阶段实施

## P0（当天可交付）
### 目标
把“可用率、回退率、质量闸门状态”变成可观测指标，并出现在日常输出。

### 任务
1. 日报展示财务因子可用率 + Akshare回退占比（已在 `generate_daily_report.py`）
2. 卡片端同步展示数据源健康摘要（已在 `build_feishu_card_payload.py`）
3. 建立参考调研文档（新增）

### 产物
- `docs/OPEN_SOURCE_RESEARCH_2026-03-09.md`
- `outputs/daily_report.generated.md`（运行后）
- `outputs/feishu_card_payload.generated.json`（运行后）

---

## P1（1~2天）
### 目标
建立基础“数据源稳定性治理”能力。

### 任务
1. 新增 `scripts/fundamental_probe.py`（逐接口可用性/时延探针）
2. 交易日收盘后追加执行 probe，生成 `outputs/fundamental_probe_report.json`
3. 周报纳入“fundamental health 周统计”
4. 若连续 N 天 health=error，触发系统状态提醒（先落地本地状态，后接消息通道）

### 产物
- `scripts/fundamental_probe.py`（已新增）
- `outputs/fundamental_probe_report.json`（运行后）

---

## P2（3~7天）
### 目标
从“静态规则”升级到“可校准规则”，形成轻闭环。

### 任务
1. 建立阈值/置信度校准脚本（基于 `signal_eval_report.json`）
2. 引入参数变更审计（记录何时、为何调了阈值）
3. 预留回测接口（可选 QSTrader 或轻量自研）用于周度 sanity-check
4. 已新增 MA 交叉基线回测脚本，先用于策略健康检查（非生产信号）

### 产物
- `scripts/calibrate_signal_thresholds.py`（待建）
- `state/parameter_change_log.jsonl`（待建）
- `scripts/backtest_ma_baseline.py`（已新增）
- `outputs/backtest_baseline_report.json`（运行后生成）

---

## 四、验收标准

### 数据可用性
- 财务因子可用率较当前基线显著提升
- 回退比例可解释且可追踪（日报/周报可见）

### 风险一致性
- `snapshot_quality_score < 60` 时，系统不输出增持建议
- 连续探针失败可触发系统告警/降级文案

### 可运维性
- 每日输出可快速定位：是数据问题、信号问题，还是推送问题
- 关键脚本失败后有明确降级路径

---

## 五、执行建议（本周）
1. 先跑通 `fundamental_probe.py`，确认输出结构稳定
2. 把 probe 结果写进周报模板
3. 再做“阈值校准”与“参数变更审计”

> 原则维持：可解释优先、风控优先、数据不足不下结论。