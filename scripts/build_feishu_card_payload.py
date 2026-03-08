import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
TEMPLATE = ROOT / "templates" / "feishu_daily_card.json"


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    snapshot = load_json(DATA / "market_snapshot.tushare.json", {})
    advice = load_json(OUT / "advice_actions.json", {"items": []})
    risk = load_json(OUT / "portfolio_risk_report.json", {"risk_state": "normal", "violations": []})

    ts = snapshot.get("timestamp") or datetime.now().astimezone().isoformat(timespec="seconds")
    sh = snapshot.get("source_health", {}) or {}

    market_overview = "\n".join([
        "### 1) 市场概览",
        f"- 数据新鲜度: {snapshot.get('data_freshness_sec', 'NA')} 秒",
        f"- 数据质量分: {snapshot.get('snapshot_quality_score', 'NA')}",
        f"- quote/news/fundamental: {sh.get('quote','unknown')}/{sh.get('news','unknown')}/{sh.get('fundamental','unknown')}"
    ])

    items = advice.get("items", [])
    if items:
        lines = ["### 2) 重点信号"]
        for i in items[:8]:
            lines.append(f"- {i['symbol']}: **{i['signal']}** | 分数 {i['score']:.2f} | 风险 {i['risk_level']}")
        key_signals = "\n".join(lines)
    else:
        key_signals = "### 2) 重点信号\n- 暂无"

    risk_alerts = "\n".join([
        "### 3) 风险提示",
        f"- 全局风险: {load_json(DATA / 'signal_report.generated.json', {}).get('global_risk_state', 'normal')}",
        f"- 组合风险: {risk.get('risk_state', 'normal')}",
        f"- 约束触发: {', '.join(risk.get('violations', [])) if risk.get('violations') else '无'}"
    ])

    actions = "\n".join([
        "### 4) 操作建议",
        "- 数据质量不足时仅观察，不执行增持建议",
        "- 同结论24小时去重，降低噪音"
    ])

    card = load_json(TEMPLATE)
    raw = json.dumps(card, ensure_ascii=False)
    raw = raw.replace("{{title}}", "低频量化日报（卡片版）")
    raw = raw.replace("{{timestamp}}", ts)
    raw = raw.replace("{{market_overview}}", market_overview.replace('"', '\\"'))
    raw = raw.replace("{{key_signals}}", key_signals.replace('"', '\\"'))
    raw = raw.replace("{{risk_alerts}}", risk_alerts.replace('"', '\\"'))
    raw = raw.replace("{{actions}}", actions.replace('"', '\\"'))

    out_path = OUT / "feishu_card_payload.generated.json"
    out_path.write_text(raw, encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
