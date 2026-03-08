import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = ROOT / "config"


def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def score_from_change(change_pct: float) -> float:
    # map roughly [-5%, +5%] -> [0,1]
    x = max(-5.0, min(5.0, change_pct))
    return round((x + 5.0) / 10.0, 4)


def signal_from_score(score: float) -> str:
    if score >= 0.7:
        return "increase"
    if score >= 0.55:
        return "hold"
    if score >= 0.4:
        return "observe"
    return "reduce"


def risk_level(change_pct: float) -> str:
    a = abs(change_pct)
    if a < 1.5:
        return "low"
    if a < 3.0:
        return "medium"
    return "high"


def main():
    snap_path = DATA / "market_snapshot.tushare.json"
    if not snap_path.exists():
        raise SystemExit("market_snapshot.tushare.json missing. run snapshot builder first")

    snap = load_json(snap_path)
    ts = snap.get("timestamp") or datetime.now().isoformat(timespec="seconds")

    signals = []
    high_risk_count = 0

    for s in snap.get("symbols", []):
        symbol = s.get("symbol")
        chg = float(s.get("change_pct", 0.0))
        sc = score_from_change(chg)
        sig = signal_from_score(sc)
        rl = risk_level(chg)
        if rl == "high":
            high_risk_count += 1

        reasons = [
            f"当日涨跌幅 {chg}%",
            "基于日频简化打分模型",
            "需结合后续财报/波动因子二次确认",
        ]

        signals.append(
            {
                "symbol": symbol,
                "signal": sig,
                "score": sc,
                "confidence": 0.62,
                "risk_level": rl,
                "reasons": reasons,
                "delta_vs_last": "首次自动生成，后续将对比历史建议",
            }
        )

    global_risk_state = "normal"
    if high_risk_count >= 2:
        global_risk_state = "defensive"
    elif high_risk_count >= 1:
        global_risk_state = "cautious"

    out = {
        "timestamp": ts,
        "market": snap.get("market", "CN-A"),
        "global_risk_state": global_risk_state,
        "signals": signals,
    }

    out_path = DATA / "signal_report.generated.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
