import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def line_for_signal(item):
    return (
        f"- {item['symbol']}：**{item['signal']}** | 分数 {item['score']:.2f} | "
        f"置信度 {item['confidence']:.2f} | 风险 {item['risk_level']}\n"
        f"  - 理由：{'；'.join(item.get('reasons', []))}\n"
        f"  - 变化：{item.get('delta_vs_last', '无')}"
    )


def pick_snapshot():
    real_path = DATA / "market_snapshot.tushare.json"
    sample_path = DATA / "market_snapshot.sample.json"
    if real_path.exists():
        return load_json(real_path), str(real_path.name)
    return load_json(sample_path), str(sample_path.name)


def main():
    snapshot, snapshot_source = pick_snapshot()
    report = load_json(DATA / "signal_report.sample.json")

    ts = snapshot.get("timestamp") or report.get("timestamp") or datetime.now().isoformat()
    leaders = "、".join(snapshot.get("sector", {}).get("leaders", [])) or "暂无"
    laggards = "、".join(snapshot.get("sector", {}).get("laggards", [])) or "暂无"

    body = []
    body.append("# 低频量化日报")
    body.append(f"\n数据时间：{ts}\n")

    body.append("## 1. 市场概览")
    body.append(f"- 数据源：{snapshot_source}")
    body.append(f"- 强势行业：{leaders}")
    body.append(f"- 弱势行业：{laggards}")

    index_map = snapshot.get("index", {})
    if index_map:
        body.append("- 指数概览：")
        for code, v in index_map.items():
            if isinstance(v, dict) and "change_pct" in v:
                body.append(f"  - {v.get('name', code)}({code})：{v.get('change_pct')}%")

    body.append("\n## 2. 重点信号")
    signals = report.get("signals", [])
    if not signals:
        body.append("- 数据不足，不建议操作")
    else:
        for s in signals:
            body.append(line_for_signal(s))

    body.append("\n## 3. 风险提示")
    grs = report.get("global_risk_state", "normal")
    body.append(f"- 当前全局风险状态：**{grs}**")
    body.append("- 如无显著变化，维持观察，避免过度交易")

    body.append("\n## 4. 操作建议")
    body.append("- 优先执行风险控制，再考虑增持动作")
    body.append("- 单票仓位、行业暴露、组合回撤遵循 config/portfolio.yaml")

    out = OUT / "daily_report.generated.md"
    out.write_text("\n".join(body), encoding="utf-8")
    print(f"generated: {out}")


if __name__ == "__main__":
    main()
