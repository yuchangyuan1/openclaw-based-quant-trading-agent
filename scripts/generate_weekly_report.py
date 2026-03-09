import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
STATE = ROOT / "state"
TEMPLATE = ROOT / "templates" / "feishu_weekly.md"


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def parse_jsonl(path: Path):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def main():
    now = datetime.now().astimezone()
    week_range = now.strftime("%G-W%V")

    sig_eval = load_json(OUT / "signal_eval_report.json", {}) or {}
    bt = load_json(OUT / "backtest_baseline_report.json", {}) or {}
    probe = load_json(OUT / "fundamental_probe_report.json", {}) or {}
    alert = load_json(STATE / "fundamental_alert_state.json", {}) or {}

    summary = sig_eval.get("summary", {})
    weekly_summary = "\n".join([
        f"- 样本数: {summary.get('samples', 'NA')}",
        f"- 代理胜率: {summary.get('win_rate', 'NA')}",
        f"- 代理回撤: {summary.get('max_drawdown', 'NA')}",
        f"- 代理T+5收益: {summary.get('avg_return_t5', 'NA')}",
    ])

    bt_sum = (bt.get("summary") or {})
    signal_eval = "\n".join([
        f"- 回测基线: {(bt.get('strategy') or {}).get('name', 'N/A')}",
        f"- 覆盖标的数: {bt_sum.get('symbols', 'NA')}",
        f"- 平均总收益: {bt_sum.get('avg_total_return', 'NA')}",
        f"- 最差最大回撤: {bt_sum.get('worst_max_drawdown', 'NA')}",
    ])

    risk_changes = "\n".join([
        f"- Fundamental 探针健康: {probe.get('health', 'unknown')} (success_rate={probe.get('success_rate', 'NA')})",
        f"- 探针平均延迟: {(probe.get('summary') or {}).get('avg_latency_ms', 'NA')} ms",
        f"- 连续异常告警: {alert.get('alert', False)}",
        f"- 告警说明: {alert.get('message', 'N/A')}",
    ])

    next_week_actions = "\n".join([
        "- 若数据质量分 < 60，继续仅输出观察/风控结论",
        "- 若连续3次 fundamental=error，优先排查 Tushare 权限与回退链路",
        "- 基于周评估考虑小步调参（记录到 parameter_change_log）",
    ])

    tpl = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else "# {{title}}\n{{weekly_summary}}"
    txt = tpl.replace("{{title}}", "低频量化周报")
    txt = txt.replace("{{week_range}}", week_range)
    txt = txt.replace("{{weekly_summary}}", weekly_summary)
    txt = txt.replace("{{signal_eval}}", signal_eval)
    txt = txt.replace("{{risk_changes}}", risk_changes)
    txt = txt.replace("{{next_week_actions}}", next_week_actions)

    OUT.mkdir(parents=True, exist_ok=True)
    out_path = OUT / "weekly_report.generated.md"
    out_path.write_text(txt, encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
