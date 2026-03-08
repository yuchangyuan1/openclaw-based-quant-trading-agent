import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = ROOT / "config"

DEFAULT_RULES = {
    "weights": {
        "trend": 0.25,
        "momentum": 0.20,
        "valuation": 0.15,
        "volatility": 0.15,
        "drawdown": 0.15,
        "earnings_quality": 0.10,
    },
    "thresholds": {"buy_watch": 0.70, "hold": 0.55, "reduce": 0.40},
    "risk_change_pct": {"low": 1.5, "medium": 3.0},
    "model_params": {"default_confidence": 0.62},
    "global_risk_thresholds": {"cautious_high_risk_count": 1, "defensive_high_risk_count": 2},
}


def load_json(p: Path):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_signal_rules(path: Path):
    rules = {
        "weights": DEFAULT_RULES["weights"].copy(),
        "thresholds": DEFAULT_RULES["thresholds"].copy(),
        "risk_change_pct": DEFAULT_RULES["risk_change_pct"].copy(),
        "model_params": DEFAULT_RULES["model_params"].copy(),
        "global_risk_thresholds": DEFAULT_RULES["global_risk_thresholds"].copy(),
    }

    if not path.exists():
        return rules

    current = None
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line in ("weights:", "thresholds:", "risk_change_pct:", "model_params:", "global_risk_thresholds:"):
                current = line[:-1]
                continue
            if line.endswith(":"):
                current = None
                continue
            if current and ":" in line:
                k, v = [x.strip() for x in line.split(":", 1)]
                try:
                    rules[current][k] = float(v)
                except ValueError:
                    pass

    return rules


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def normalize_ret(ret: float, lo=-0.08, hi=0.08) -> float:
    x = (ret - lo) / (hi - lo)
    return clamp01(x)


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


def risk_level_from_vol_change(change_pct: float, volatility20: float, risk_cfg: dict) -> str:
    abs_chg = abs(change_pct)
    low_cutoff = float(risk_cfg.get("low", 1.5))
    medium_cutoff = float(risk_cfg.get("medium", 3.0))

    if volatility20 > 0.04 or abs_chg >= medium_cutoff:
        return "high"
    if volatility20 > 0.025 or abs_chg >= low_cutoff:
        return "medium"
    return "low"


def main():
    snap_path = DATA / "market_snapshot.tushare.json"
    if not snap_path.exists():
        raise SystemExit("market_snapshot.tushare.json missing. run snapshot builder first")

    rules = load_signal_rules(CFG / "signal_rules.yaml")
    snap = load_json(snap_path)

    ts = snap.get("timestamp") or datetime.now().isoformat(timespec="seconds")
    quality_score = float(snap.get("snapshot_quality_score", 0))
    data_quality_passed = quality_score >= 60

    w = rules["weights"]
    signals = []
    high_risk_count = 0

    for s in snap.get("symbols", []):
        symbol = s.get("symbol")
        change_pct = float(s.get("change_pct", 0.0))
        fi = s.get("factor_inputs", {}) or {}

        trend = normalize_ret(float(fi.get("ret_20d", 0.0)))
        momentum = normalize_ret(float(fi.get("ret_5d", 0.0)))
        volatility = clamp01(1 - (float(fi.get("volatility_20d", 0.0)) / 0.06))
        drawdown = clamp01(0.55 + float(fi.get("ret_20d", 0.0)) * 2)
        valuation = 0.5  # 待接入 daily_basic PE/PB
        earnings_quality = 0.5  # 待接入财报因子

        score = (
            w.get("trend", 0.25) * trend
            + w.get("momentum", 0.20) * momentum
            + w.get("valuation", 0.15) * valuation
            + w.get("volatility", 0.15) * volatility
            + w.get("drawdown", 0.15) * drawdown
            + w.get("earnings_quality", 0.10) * earnings_quality
        )
        score = round(clamp01(score), 4)

        signal = signal_from_score(score, rules["thresholds"])
        risk_level = risk_level_from_vol_change(change_pct, float(fi.get("volatility_20d", 0.0)), rules["risk_change_pct"])
        if risk_level == "high":
            high_risk_count += 1

        reasons = [
            f"20日趋势收益率={fi.get('ret_20d', 0.0):.2%}",
            f"5日动量收益率={fi.get('ret_5d', 0.0):.2%}",
            f"20日波动率={fi.get('volatility_20d', 0.0):.2%}",
            f"量比(5日/基准)={fi.get('volume_ratio_5d', 1.0):.2f}",
            "估值/财报因子当前为占位分，后续接入Tushare财务接口增强",
        ]

        if not data_quality_passed and signal == "increase":
            signal = "observe"
            reasons.append("数据质量闸门未通过：增持信号降级为观察")

        signals.append(
            {
                "symbol": symbol,
                "signal": signal,
                "score": score,
                "confidence": float(rules["model_params"].get("default_confidence", 0.62)),
                "risk_level": risk_level,
                "reasons": reasons,
                "delta_vs_last": "待与 advice_history 对比",
                "evidence": {
                    "trend": round(trend, 3),
                    "momentum": round(momentum, 3),
                    "valuation": round(valuation, 3),
                    "volatility": round(volatility, 3),
                },
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
