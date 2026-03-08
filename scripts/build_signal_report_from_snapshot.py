import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = ROOT / "config"

DEFAULT_RULES = {
    "thresholds": {"buy_watch": 0.70, "hold": 0.55, "reduce": 0.40},
    "risk_change_pct": {"low": 1.5, "medium": 3.0},
    "model_params": {"default_confidence": 0.62},
    "global_risk_thresholds": {"cautious_high_risk_count": 1, "defensive_high_risk_count": 2},
    "reason_templates": {
        "price_change": "当日涨跌幅 {change_pct}%",
        "model_note": "阈值规则：buy_watch={buy_watch}, hold={hold}, reduce={reduce}",
        "caution_note": "需结合后续财报/波动因子二次确认",
    },
}


def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_signal_rules(path: Path):
    rules = {
        "thresholds": DEFAULT_RULES["thresholds"].copy(),
        "risk_change_pct": DEFAULT_RULES["risk_change_pct"].copy(),
        "model_params": DEFAULT_RULES["model_params"].copy(),
        "global_risk_thresholds": DEFAULT_RULES["global_risk_thresholds"].copy(),
        "reason_templates": DEFAULT_RULES["reason_templates"].copy(),
    }

    if not path.exists():
        return rules

    current = None
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            if line in ("thresholds:", "risk_change_pct:", "model_params:", "global_risk_thresholds:", "reason_templates:"):
                current = line[:-1]
                continue

            if line.endswith(":"):
                current = None
                continue

            if current and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                if current == "reason_templates":
                    rules[current][k] = v.strip('"').strip("'")
                else:
                    try:
                        rules[current][k] = float(v)
                    except ValueError:
                        pass

    return rules


def score_from_change(change_pct: float) -> float:
    x = max(-5.0, min(5.0, change_pct))
    return round((x + 5.0) / 10.0, 4)


def signal_from_score(score: float, thresholds: dict) -> str:
    buy_watch = float(thresholds.get("buy_watch", 0.70))
    hold = float(thresholds.get("hold", 0.55))
    reduce = float(thresholds.get("reduce", 0.40))

    if score >= buy_watch:
        return "increase"
    if score >= hold:
        return "hold"
    if score >= reduce:
        return "observe"
    return "reduce"


def risk_level(change_pct: float, risk_cfg: dict) -> str:
    a = abs(change_pct)
    low_cutoff = float(risk_cfg.get("low", 1.5))
    medium_cutoff = float(risk_cfg.get("medium", 3.0))
    if a < low_cutoff:
        return "low"
    if a < medium_cutoff:
        return "medium"
    return "high"


def evidence_from_change(change_pct: float):
    base = score_from_change(change_pct)
    return {
        "trend": round(base, 3),
        "momentum": round(max(0.0, min(1.0, base + 0.05)), 3),
        "valuation": 0.5,
        "volatility": round(max(0.0, min(1.0, abs(change_pct) / 5)), 3),
    }


def main():
    snap_path = DATA / "market_snapshot.tushare.json"
    if not snap_path.exists():
        raise SystemExit("market_snapshot.tushare.json missing. run snapshot builder first")

    rules = load_signal_rules(CFG / "signal_rules.yaml")
    snap = load_json(snap_path)

    ts = snap.get("timestamp") or datetime.now().isoformat(timespec="seconds")
    quality_score = float(snap.get("snapshot_quality_score", 0))
    data_quality_passed = quality_score >= 60

    signals = []
    high_risk_count = 0

    for s in snap.get("symbols", []):
        symbol = s.get("symbol")
        chg = float(s.get("change_pct", 0.0))
        sc = score_from_change(chg)
        sig = signal_from_score(sc, rules["thresholds"])
        rl = risk_level(chg, rules["risk_change_pct"])
        if rl == "high":
            high_risk_count += 1

        rt = rules["reason_templates"]
        reasons = [
            rt.get("price_change", "当日涨跌幅 {change_pct}%").format(change_pct=chg),
            rt.get("model_note", "阈值规则：buy_watch={buy_watch}, hold={hold}, reduce={reduce}").format(
                buy_watch=rules["thresholds"].get("buy_watch"),
                hold=rules["thresholds"].get("hold"),
                reduce=rules["thresholds"].get("reduce"),
            ),
            rt.get("caution_note", "需结合后续财报/波动因子二次确认"),
        ]

        if not data_quality_passed and sig == "increase":
            sig = "observe"
            reasons.append("数据质量闸门未通过：降级为观察")

        signals.append(
            {
                "symbol": symbol,
                "signal": sig,
                "score": sc,
                "confidence": float(rules["model_params"].get("default_confidence", 0.62)),
                "risk_level": rl,
                "reasons": reasons,
                "delta_vs_last": "待与 advice_history 对比",
                "evidence": evidence_from_change(chg),
                "data_quality_gate": {"passed": data_quality_passed, "quality_score": quality_score},
            }
        )

    gr = rules["global_risk_thresholds"]
    defensive_n = int(gr.get("defensive_high_risk_count", 2))
    cautious_n = int(gr.get("cautious_high_risk_count", 1))

    global_risk_state = "normal"
    if high_risk_count >= defensive_n:
        global_risk_state = "defensive"
    elif high_risk_count >= cautious_n:
        global_risk_state = "cautious"

    out = {
        "timestamp": ts,
        "market": snap.get("market", "CN-A"),
        "global_risk_state": global_risk_state,
        "signals": signals,
    }

    out_path = DATA / "signal_report.generated.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated: {out_path}")


if __name__ == "__main__":
    main()
