import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def line_for_signal(item):
    return (
        f"- {item['symbol']}：**{item['signal']}** | 分数 {item['score']:.2f} | "
        f"置信度 {item['confidence']:.2f} | 风险 {item['risk_level']}\n"
        f"  - 理由：{'；'.join(item.get('reasons', []))}\n"
        f"  - 变化：{item.get('change_vs_last', item.get('delta_vs_last', '无'))}\n"
        f"  - 数据质量：{item.get('data_quality_gate', {}).get('quality_score', 'NA')}"
    )


def pick_snapshot():
    real_path = DATA / "market_snapshot.tushare.json"
    sample_path = DATA / "market_snapshot.sample.json"
    if real_path.exists():
        return load_json(real_path), str(real_path.name)
    return load_json(sample_path), str(sample_path.name)


def main():
    snapshot, snapshot_source = pick_snapshot()
    report = load_json(DATA / "signal_report.generated.json", {"signals": [], "global_risk_state": "normal"})
    advice_actions = load_json(OUT / "advice_actions.json", {"items": []})
    portfolio_risk = load_json(OUT / "portfolio_risk_report.json", {"risk_state": "normal", "violations": []})

    ts = snapshot.get("timestamp") or report.get("timestamp") or datetime.now().isoformat()
    leaders = "、".join(snapshot.get("sector", {}).get("leaders", [])) or "暂无"
    laggards = "、".join(snapshot.get("sector", {}).get("laggards", [])) or "暂无"

    body = []
    body.append("# 低频量化日报")
    body.append(f"\n数据时间：{ts}\n")

    body.append("## 1. 市场概览")
    body.append(f"- 市场数据源：{snapshot_source}")
    body.append(f"- 强势行业：{leaders}")
    body.append(f"- 弱势行业：{laggards}")
    body.append(f"- 数据新鲜度(秒)：{snapshot.get('data_freshness_sec', 'NA')}")
    body.append(f"- 数据质量分：{snapshot.get('snapshot_quality_score', 'NA')}")
    sh = snapshot.get('source_health', {}) or {}
    body.append("- 数据源健康：")
    body.append(f"  - quote: {sh.get('quote', 'unknown')}")
    body.append(f"  - news: {sh.get('news', 'unknown')}")
    body.append(f"  - fundamental: {sh.get('fundamental', 'unknown')}")

    index_map = snapshot.get("index", {})
    if index_map:
        body.append("- 指数概览：")
        for code, v in index_map.items():
            if isinstance(v, dict) and "change_pct" in v:
                body.append(f"  - {v.get('name', code)}({code})：{v.get('change_pct')}%")

    body.append("\n## 2. 重点信号")
    items = advice_actions.get("items") or report.get("signals", [])
    if not items:
        body.append("- 数据不足，不建议操作")
    else:
        for s in items:
            body.append(line_for_signal(s))

    body.append("\n## 3. 股票池建议")
    for s in items:
        if s.get("suppressed"):
            body.append(f"- {s['symbol']}：结论重复，24小时内抑制推送")
        else:
            body.append(f"- {s['symbol']}：建议 {s['signal']}（{s.get('change_vs_last', '无变更信息')}）")

    body.append("\n## 4. 风险提示")
    body.append(f"- 全局风险状态：**{report.get('global_risk_state', 'normal')}**")
    body.append(f"- 组合风险状态：**{portfolio_risk.get('risk_state', 'normal')}**")
    if portfolio_risk.get("violations"):
        body.append(f"- 约束触发：{', '.join(portfolio_risk['violations'])}")
    else:
        body.append("- 组合约束未触发")

    body.append("\n## 5. 操作建议（观察/持有/减仓/增持）")
    if snapshot.get("snapshot_quality_score", 0) < 60:
        body.append("- 数据质量不足：仅观察，不执行增持建议")
    else:
        body.append("- 优先执行风控，再考虑增持动作")

    out = OUT / "daily_report.generated.md"
    out.write_text("\n".join(body), encoding="utf-8")
    print(f"generated: {out}")


if __name__ == "__main__":
    main()
